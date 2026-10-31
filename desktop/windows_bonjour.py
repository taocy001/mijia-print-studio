"""Windows-only AirPrint discovery via python-zeroconf."""
import asyncio
import inspect
import ipaddress
import logging
import re
import time
from urllib.parse import urlparse

from airprint.capabilities import URF
from desktop.bonjour import Bonjour

_log = logging.getLogger(__name__)
_IPP = "_ipp._tcp.local."
_UNIVERSAL = "_universal._sub." + _IPP


class WindowsBonjour:
    desired = Bonjour.desired

    def __init__(self, adapter, name, port, address, *, factory=None, info_factory=None, clock=time.monotonic):
        ip = ipaddress.IPv4Address(address)
        if ip.is_unspecified or ip.is_multicast or ip.is_loopback or ip.is_reserved:
            raise ValueError("AirPrint requires a LAN interface IPv4 address")
        server = urlparse(adapter.uri).hostname or ""
        if not re.fullmatch(r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.local\.?", server):
            raise ValueError("AirPrint URI must use the advertised .local hostname")
        if not 1 <= port <= 65535:
            raise ValueError("Invalid AirPrint port")
        if factory is None or info_factory is None:
            from zeroconf import IPVersion, ServiceInfo
            from zeroconf.asyncio import AsyncZeroconf
            factory = factory or (lambda **kw: AsyncZeroconf(ip_version=IPVersion.V4Only, **kw))
            info_factory = info_factory or ServiceInfo
        self.adapter, self.name, self.port = adapter, name, port
        self.address, self.server = str(ip), server.rstrip(".") + "."
        label = re.sub(r"[.\\\x00-\x1f]", "-", name).strip() or "Mijia Print"
        self.instance = label.encode("utf-8")[:48].decode("utf-8", "ignore") + "." + _IPP
        self.factory, self.info_factory, self.clock = factory, info_factory, clock
        self.signature = None
        self.retry_at = 0
        self._responders, self._announcements = [], set()
        self._lock, self._closed = asyncio.Lock(), False

    @property
    def advertised(self):
        return any(item[1] for item in self._responders)

    async def _register(self, responder, info, **options):
        # The API returns a second awaitable for the actual announcement packets.
        completion = await responder[0].async_register_service(info, **options)
        responder[1] = True
        if inspect.isawaitable(completion):
            task = asyncio.ensure_future(completion)
            self._announcements.add(task)
            try:
                await task
            finally:
                self._announcements.discard(task)

    async def _withdraw(self):
        self.signature = None
        for task in self._announcements:
            task.cancel()
        if self._announcements:
            await asyncio.gather(*self._announcements, return_exceptions=True)
        self._announcements.clear()
        remaining = []
        for responder in reversed(self._responders):
            try:
                # async_close sends goodbyes before closing the multicast sockets.
                await asyncio.wait_for(responder[0].async_close(), 5)
            except Exception:
                remaining.append(responder)
                _log.warning("AirPrint withdrawal incomplete; retrying")
        self._responders = list(reversed(remaining))
        return not remaining

    async def close(self):
        self._closed = True
        async with self._lock:
            for attempt in range(3):
                if await self._withdraw():
                    return
                if attempt < 2:
                    await asyncio.sleep(.1)
            raise RuntimeError("AirPrint withdrawal did not complete")

    def _info(self, type_, name, desired):
        media, formats = desired
        note = {5009: "3 inch square", 5012: "6 inch photo", 5014: "Two 4 inch photos"}[media]
        properties = {
            "txtvers": "1", "qtotal": "1", "rp": "ipp/print", "ty": self.name,
            "product": "(Mijia Instant Photo Printer 2)", "Color": "T", "Duplex": "F",
            "kind": "photo", "priority": "50", "pdl": ",".join(formats),
            "URF": b",".join(URF).decode(), "UUID": self.adapter.identity.removeprefix("urn:uuid:"),
            "note": note, "media-size": str(media),
        }
        return self.info_factory(type_, name, server=self.server, port=self.port,
                                 parsed_addresses=[self.address], properties=properties,
                                 host_ttl=120, other_ttl=120)

    async def update(self):
        async with self._lock:
            if self._closed:
                return
            desired = self.desired()
            if desired == self.signature and not (desired is None and self._responders):
                return
            if self.clock() < self.retry_at:
                return
            if not await self._withdraw():
                self.retry_at = self.clock() + 5
                return
            if desired is None:
                return
            try:
                primary = [self.factory(interfaces=[self.address]), False]
                self._responders.append(primary)
                info = self._info(_IPP, self.instance, desired)
                await self._register(primary, info, allow_name_change=True)
                self.instance = info.name
                if self.desired() != desired:
                    await self._withdraw()
                    return
                # One registry cannot hold two PTR types with the same SRV name.
                # The subtype responder reuses the primary's conflict-checked name.
                subtype = [self.factory(interfaces=[self.address]), False]
                self._responders.append(subtype)
                await self._register(subtype, self._info(_UNIVERSAL, info.name, desired),
                                     cooperating_responders=True)
                if self.desired() != desired:
                    await self._withdraw()
                    return
                self.signature = desired
                self.retry_at = 0
            except asyncio.CancelledError:
                await self._withdraw()
                raise
            except Exception:
                await self._withdraw()
                self.retry_at = self.clock() + 5
                _log.warning("AirPrint announcement unavailable; retrying")

    async def run(self):
        try:
            while True:
                await self.update()
                await asyncio.sleep(1)
        finally:
            await self.close()
