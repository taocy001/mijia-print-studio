"""Advertise only a recently verified, usable AirPrint endpoint."""
import asyncio
import logging
import time
from airprint.capabilities import URF
from airprint.documents import FORMATS

_log=logging.getLogger(__name__)

class Bonjour:
    def __init__(self,adapter,name,port,spawn=None):
        self.adapter,self.name,self.port=adapter,name,port
        self.spawn=spawn or asyncio.create_subprocess_exec
        self.process=None;self.signature=None;self.retry_at=0
    def desired(self):
        core=self.adapter.core
        if not core.airprint_ready():return None
        media=core.available_media()
        if media not in (5009,5012):return None
        media=5014 if media==5012 and core.airprint_splice else media
        formats=tuple(f for f in FORMATS if media!=5014 or f in ('image/jpeg','application/pdf'))
        return media,formats
    async def close(self):
        process,self.process=self.process,None;self.signature=None
        if process is not None and process.returncode is None:
            try:process.terminate()
            except ProcessLookupError:return
            try:await asyncio.wait_for(process.wait(),3)
            except asyncio.TimeoutError:
                process.kill();await process.wait()
    async def update(self):
        desired=self.desired()
        if self.process is not None and self.process.returncode is not None:
            self.process=None;self.signature=None;self.retry_at=time.monotonic()+5
        if desired==self.signature:return
        await self.close()
        if desired is None or time.monotonic()<self.retry_at:return
        media,formats=desired
        note={5009:'3 inch square',5012:'6 inch photo',5014:'Two 4 inch photos'}[media]
        try:
            start=asyncio.create_task(self.spawn('/usr/bin/dns-sd','-R',self.name,'_ipp._tcp,_universal','local.',str(self.port),
                'txtvers=1','qtotal=1','rp=ipp/print','ty='+self.name,'product=(Mijia Instant Photo Printer 2)',
                'Color=T','Duplex=F','kind=photo','priority=50','pdl='+','.join(formats),
                'URF='+b','.join(URF).decode(),'UUID='+self.adapter.identity.removeprefix('urn:uuid:'),'note='+note,
                stdout=asyncio.subprocess.DEVNULL,stderr=asyncio.subprocess.DEVNULL))
            try:self.process=await asyncio.shield(start)
            except asyncio.CancelledError:
                try:self.process=await start
                except OSError:pass
                await self.close();raise
            self.signature=desired
        except OSError:
            self.retry_at=time.monotonic()+5;_log.warning('AirPrint announcement unavailable; retrying')
    async def run(self):
        try:
            while True:
                await self.update();await asyncio.sleep(1)
        finally:await self.close()
