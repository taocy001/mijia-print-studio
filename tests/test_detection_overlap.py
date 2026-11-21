"""Manual desktop detection must report the result of the current device read."""
import asyncio
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from printing.bluetooth_client import BluetoothClient
from printing.images import UserError
from printing.service import PrintService


class DetectionTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.core = PrintService(folder.name, simulate=True)
        await self.core.start(None)
        self.addAsyncCleanup(self.core.stop, None)
        self.core.simulate = False

    async def overlap(self, fail):
        entered = threading.Event()
        finish = threading.Event()
        def read(*_):
            entered.set()
            if not finish.wait(4):
                raise AssertionError('Read was not released')
            if fail:
                raise OSError('unavailable')
            return ['30', '::0', {'media-size': 5012}, {'ribbon-info': [1, 0, 12]}]

        printer = Mock()
        printer.get_prop.side_effect = read
        with patch.object(self.core, 'printer', return_value=printer) as factory:
            first = asyncio.create_task(self.core.status())
            try:
                self.assertTrue(await asyncio.to_thread(entered.wait, 2))
                second = asyncio.create_task(self.core.connect())
                await asyncio.sleep(0)
                self.assertFalse(second.done())
            finally:
                finish.set()
            results = await asyncio.gather(first, second, return_exceptions=True)
            factory.assert_called_once()
            printer.get_prop.assert_called_once()
            self.assertIsNone(self.core._status_result)
            return results

    async def test_join_success(self):
        self.assertEqual(await self.overlap(False), [None, None])

    async def test_join_failure(self):
        with self.assertLogs('printing.service', level='WARNING') as captured:
            results = await self.overlap(True)
        self.assertTrue(all(isinstance(result, UserError) for result in results))
        self.assertEqual(str(results[0]), str(results[1]))
        self.assertRegex(' '.join(captured.output), r'at_ms=\d+ phase=read status error=OSError')

    async def test_cancelled_waiter_does_not_cancel_device_read(self):
        result = asyncio.get_running_loop().create_future()
        self.core._status_result = result
        waiter = asyncio.create_task(self.core.connect())
        await asyncio.sleep(0)
        waiter.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await waiter
        self.assertFalse(result.done())
        result.set_result(None)
        self.core._status_result = None

    async def test_other_device_work_is_reported_as_busy(self):
        async with self.core.io_lock:
            with self.assertRaises(UserError):
                await self.core.connect()

    async def test_handshake_phase_survives_setup_cleanup(self):
        client = BluetoothClient('00:00:00:00:00:00', 'unused')
        def fail():
            client.phase = 'handshake confirmation'
            raise ValueError('private payload')
        with patch.object(client, 'connect', side_effect=fail), patch.object(self.core, 'printer', side_effect=lambda *args: client.open(attempts=1)):
            with self.assertLogs('printing.service', level='WARNING') as captured, self.assertRaises(UserError):
                await self.core.connect()
        lines = ' '.join(captured.output)
        self.assertIn('phase=handshake confirmation error=ValueError', lines)
        self.assertNotIn('private payload', lines)
