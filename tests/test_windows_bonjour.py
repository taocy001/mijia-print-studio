import asyncio
import unittest
from types import SimpleNamespace
from desktop.windows_bonjour import WindowsBonjour, _IPP, _UNIVERSAL


class Info:
    def __init__(self, type_, name, **values):
        self.type, self.name = type_, name
        self.__dict__.update(values)


class Responder:
    def __init__(self, owner, interfaces):
        self.owner, self.interfaces = owner, interfaces
        self.registrations, self.closed, self.close_failures = [], False, 0

    async def async_register_service(self, info, **options):
        self.registrations.append((info, options))
        if self.owner.rename and info.type == _IPP:
            info.name = "Printer-2." + _IPP
        if self.owner.fail_register:
            raise OSError("Network unavailable")
        async def completion():
            self.owner.started.set()
            if self.owner.gate:
                await self.owner.gate.wait()
        return asyncio.create_task(completion())

    async def async_close(self):
        if self.close_failures:
            self.close_failures -= 1
            raise OSError("Goodbye failed")
        self.closed = True


class Factory:
    def __init__(self):
        self.items, self.rename, self.fail_register = [], False, False
        self.started, self.gate = asyncio.Event(), None

    def __call__(self, *, interfaces):
        responder = Responder(self, interfaces)
        self.items.append(responder)
        return responder


class WindowsBonjourTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.ready, self.media, self.now = False, 5012, 10
        core = SimpleNamespace(airprint_ready=lambda: self.ready, available_media=lambda: self.media,
                               airprint_splice=False)
        self.adapter = SimpleNamespace(core=core, identity="urn:uuid:1234", uri="ipp://liuying-1234.local:8637/ipp/print")
        self.factory = Factory()
        self.service = WindowsBonjour(self.adapter, "Printer", 8637, "192.0.2.20", factory=self.factory,
                                      info_factory=Info, clock=lambda: self.now)

    async def asyncTearDown(self):
        await self.service.close()

    async def test_readiness_subtype_and_recovery(self):
        await self.service.update()
        self.assertFalse(self.factory.items)
        self.ready = True
        await asyncio.gather(self.service.update(), self.service.update())
        self.assertEqual(len(self.factory.items), 2)
        primary, subtype = self.factory.items
        first, options = primary.registrations[0]
        second, sub_options = subtype.registrations[0]
        self.assertEqual(first.type, _IPP)
        self.assertEqual(second.type, _UNIVERSAL)
        self.assertEqual(second.name, first.name)
        self.assertTrue(options["allow_name_change"])
        self.assertTrue(sub_options["cooperating_responders"])
        self.assertEqual(first.server, "liuying-1234.local.")
        self.assertEqual(first.parsed_addresses, ["192.0.2.20"])
        self.assertEqual(primary.interfaces, ["192.0.2.20"])
        self.assertEqual(first.properties["media-size"], "5012")
        self.assertEqual(first.properties["UUID"], "1234")
        self.assertIn("image/urf", first.properties["pdl"])
        self.assertTrue(self.service.advertised)
        self.ready = False
        await self.service.update()
        self.assertTrue(primary.closed and subtype.closed)
        self.assertFalse(self.service.advertised)
        self.ready = True
        await self.service.update()
        self.assertEqual(len(self.factory.items), 4)

    async def test_paper_format_and_collision(self):
        self.factory.rename = self.ready = True
        await self.service.update()
        self.assertEqual(self.factory.items[1].registrations[0][0].name, "Printer-2." + _IPP)
        self.adapter.core.airprint_splice = True
        await self.service.update()
        info = self.factory.items[-1].registrations[0][0]
        self.assertEqual(info.properties["media-size"], "5014")
        self.assertEqual(info.properties["pdl"], "image/jpeg,application/pdf")
        self.assertTrue(all(r.closed for r in self.factory.items[:2]))
        self.media = 5009
        await self.service.update()
        self.assertEqual(self.factory.items[-1].registrations[0][0].properties["media-size"], "5009")
        self.media = 0
        await self.service.update()
        self.assertFalse(self.service.advertised)

    async def test_failed_withdrawal_retained_and_retried(self):
        self.ready = True
        await self.service.update()
        self.factory.items[1].close_failures = 1
        self.ready = False
        await self.service.update()
        self.assertTrue(self.service.advertised)
        self.assertEqual(len(self.service._responders), 1)
        self.ready = True
        await self.service.update()
        self.assertEqual(len(self.factory.items), 2)
        self.now += 5
        await self.service.update()
        self.assertTrue(self.factory.items[1].closed)
        self.assertEqual(len(self.factory.items), 4)

    async def test_shutdown_retries_without_losing_registration(self):
        self.ready = True
        await self.service.update()
        self.factory.items[1].close_failures = 1
        await self.service.close()
        self.assertTrue(all(r.closed for r in self.factory.items))
        self.assertFalse(self.service.advertised)
        await self.service.update()
        self.assertEqual(len(self.factory.items), 2)

    async def test_shutdown_persistent_error_is_reported(self):
        self.ready = True
        await self.service.update()
        self.factory.items[1].close_failures = 3
        with self.assertRaisesRegex(RuntimeError, "withdrawal"):
            await self.service.close()
        self.assertTrue(self.service.advertised)
        await self.service.close()
        self.assertFalse(self.service.advertised)

    async def test_registration_error_backoff(self):
        self.ready = self.factory.fail_register = True
        await self.service.update()
        self.assertTrue(self.factory.items[0].closed)
        self.assertFalse(self.service.advertised)
        self.factory.fail_register = False
        await self.service.update()
        self.assertEqual(len(self.factory.items), 1)
        self.now += 5
        await self.service.update()
        self.assertTrue(self.service.advertised)

    async def test_cancel_inflight_closes_without_late_announcement(self):
        self.ready = True
        self.factory.gate = asyncio.Event()
        task = asyncio.create_task(self.service.update())
        await self.factory.started.wait()
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertTrue(all(r.closed for r in self.factory.items))
        self.assertFalse(self.service.advertised)
        self.assertFalse(self.service._announcements)

    async def test_availability_changed_during_registration(self):
        self.ready = True
        self.factory.gate = asyncio.Event()
        task = asyncio.create_task(self.service.update())
        await self.factory.started.wait()
        self.ready = False
        self.factory.gate.set()
        await task
        self.assertFalse(self.service.advertised)
        self.assertEqual(len(self.factory.items), 1)
        self.assertTrue(self.factory.items[0].closed)

    async def test_invalid_addresses_and_uri(self):
        for address in ("127.0.0.1", "0.0.0.0", "224.0.0.1", "::1", "255.255.255.255"):
            with self.assertRaises(ValueError):
                WindowsBonjour(self.adapter, "Printer", 8637, address, factory=self.factory, info_factory=Info)
        self.adapter.uri = "ipp://192.0.2.20:8637/ipp/print"
        with self.assertRaises(ValueError):
            WindowsBonjour(self.adapter, "Printer", 8637, "192.0.2.20", factory=self.factory, info_factory=Info)

    async def test_real_service_info_without_network(self):
        try:
            from zeroconf import ServiceInfo
        except ImportError:
            self.skipTest("Optional Windows dependency not installed")
        self.service.info_factory = ServiceInfo
        self.ready = True
        await self.service.update()
        primary = self.factory.items[0].registrations[0][0]
        subtype = self.factory.items[1].registrations[0][0]
        self.assertEqual(primary.dns_pointer().alias, subtype.dns_pointer().alias)
        self.assertEqual(subtype.dns_pointer().name, _UNIVERSAL)
        self.assertEqual(primary.dns_service().server, "liuying-1234.local.")
        self.assertEqual(primary.parsed_addresses(), ["192.0.2.20"])


if __name__ == "__main__":
    unittest.main()
