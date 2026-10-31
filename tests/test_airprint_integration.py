"""Offline integration tests. All jobs use synthetic documents and simulation."""
import asyncio,base64,io,json,os,struct,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PIL import Image
from aiohttp import ClientSession,CookieJar,web
from printing.service import PrintService
from airprint.adapter import AirPrint,app as ipp_app
from airprint.offline import Attribute as A,Message,encode_ipp,decode_ipp
from airprint.capabilities import integer
from web.serve import Studio,app as web_app
ROOT=Path(__file__).resolve().parents[1]

def photo(size=(320,480)):
    out=io.BytesIO();Image.new('RGB',size,'#da9370').save(out,'JPEG');return out.getvalue()
def request(op=2,identifier=1,document=b'',attrs=()):
    return encode_ipp(Message((2,0),op,identifier,(A(1,0x47,'attributes-charset',b'utf-8'),A(1,0x48,'attributes-natural-language',b'en'))+tuple(attrs),document))
def page():return {'media':5012,'base64':base64.b64encode(photo((1216,1824))).decode()}

class Integration(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.core=PrintService(self.tmp.name,True)
        self.adapter=AirPrint(self.core,'ipp://localhost:8636/ipp/print')
        await self.core.start(None);self.addAsyncCleanup(self.core.stop,None)
    async def call(self,raw,owner='client'):
        return decode_ipp(await self.adapter.handle(raw,owner))
    async def wait_done(self,count):
        for _ in range(100):
            if len(self.core.jobs)==count and all(j['phase']=='done' for j in self.core.jobs):return
            await asyncio.sleep(.03)
        self.fail(str([(j['phase'],j['owner']) for j in self.core.jobs]))
    async def test_both_http_entries_share_fifo_and_isolate_web_sessions(self):
        studio=Studio(core=self.core);runners=[];urls=[]
        for app in (web_app(studio),ipp_app(self.adapter)):
            runner=web.AppRunner(app);await runner.setup();runners.append(runner);self.addAsyncCleanup(runner.cleanup)
            site=web.TCPSite(runner,'127.0.0.1',0);await site.start()
            urls.append('http://127.0.0.1:'+str(site._server.sockets[0].getsockname()[1]))
        w,i=urls
        async with ClientSession(cookie_jar=CookieJar(unsafe=True)) as client:
            response=await client.post(w+'/api/pair',data={'code':studio.code},headers={'Origin':w});self.assertEqual(response.status,200)
            await self.core.io_lock.acquire()
            responses=await asyncio.gather(client.post(w+'/api/print',json={'requestId':'web-test-request-0001','pages':[page()]},headers={'Origin':w}),client.post(i+'/ipp/print',data=request(document=photo()),headers={'Content-Type':'application/ipp'}))
            self.assertTrue((await responses[0].json())['ok']);self.assertEqual(decode_ipp(await responses[1].read()).code,0)
            self.assertEqual(len(self.core.jobs),2);self.assertIs(studio.core,self.adapter.core)
            state=await (await client.get(w+'/api/state')).json();self.assertNotIn('airprint-',json.dumps(state))
            self.core.io_lock.release();await self.wait_done(2)
            self.assertEqual(self.core.jobs[0]['phase'],'done')
    async def test_web_controls_airprint_layout_and_bluetooth_release(self):
        studio=Studio(core=self.core);runner=web.AppRunner(web_app(studio));await runner.setup();self.addAsyncCleanup(runner.cleanup)
        site=web.TCPSite(runner,'127.0.0.1',0);await site.start();url='http://127.0.0.1:'+str(site._server.sockets[0].getsockname()[1])
        async with ClientSession(cookie_jar=CookieJar(unsafe=True),headers={'Origin':url}) as client:
            await client.post(url+'/api/pair',data={'code':studio.code})
            response=await client.post(url+'/api/airprint-layout',json={'splice':True});self.assertEqual(response.status,200)
            self.assertEqual(self.adapter.media,5014)
            self.assertTrue((await (await client.get(url+'/api/state')).json())['airprintSplice'])
            self.core.device['media']=5009;self.assertEqual(self.adapter.media,5009)
            self.assertEqual((await client.post(url+'/api/airprint-layout',json={'splice':False})).status,409)
            self.assertEqual((await client.post(url+'/api/release',json={})).status,200)
            self.assertTrue(self.core.released)
            response=await client.post(url+'/api/print',json={'requestId':'released-test-request','pages':[page()]});self.assertEqual(response.status,409)
            self.assertEqual(self.core.jobs,[])
            self.assertEqual((await client.post(url+'/api/connect',json={})).status,200);self.assertFalse(self.core.released)
    async def test_retry_cancel_and_other_client(self):
        self.core.paused=True
        # A paused queue advertises unavailable, but can retain already admitted work.
        self.core.paused=False
        raw=request(document=photo());response=await self.call(raw);self.assertEqual(response.code,0)
        self.assertEqual((await self.call(raw)).values('job-id'),response.values('job-id'));self.assertEqual(len(self.core.jobs),1)
        attrs=[A(1,0x21,'job-id',response.values('job-id')[0])]
        self.assertEqual((await self.call(request(9,2,attrs=attrs),'other')).code,0x0406)
        await self.wait_done(1)
        self.assertEqual((await self.call(request(8,3,attrs=attrs))).code,0x0404)
    async def test_create_send_cancel_and_duplicate(self):
        created=await self.call(request(5));self.assertEqual(created.code,0)
        attrs=[A(1,0x21,'job-id',created.values('job-id')[0]),A(1,0x22,'last-document',b'\x01')]
        raw=request(6,2,photo(),attrs)
        self.assertEqual((await self.call(raw)).code,0);self.assertEqual((await self.call(raw)).code,0);self.assertEqual(len(self.core.jobs),1)
        created=await self.call(request(5,3));jid=created.values('job-id')[0]
        self.assertEqual((await self.call(request(8,4,attrs=[A(1,0x21,'job-id',jid)]))).values('job-state'),[integer(7)])
        self.assertEqual((await self.call(request(6,5,photo(),[A(1,0x21,'job-id',jid),A(1,0x22,'last-document',b'\x01')]))).code,0x0404)
    async def test_invalid_input_does_not_enqueue(self):
        bad=await self.call(request(document=b'not an image'));self.assertNotEqual(bad.code,0);self.assertEqual(self.core.jobs,[])
        self.assertNotEqual((await self.call(request(2,2,photo(),[A(2,0x21,'copies',integer(2))]))).code,0)
    async def test_second_service_rejected_before_loading_jobs(self):
        before=(Path(self.tmp.name)/'jobs.json').read_bytes()
        with self.assertRaisesRegex(RuntimeError,'打印服务已运行'):PrintService(self.tmp.name,True)
        self.assertEqual((Path(self.tmp.name)/'jobs.json').read_bytes(),before)
    async def test_renderer_formats_and_all_papers(self):
        for paper,media,size in [('six',5012,(1216,1824)),('square',5009,(1040,1040)),('splice',5014,(1216,1824))]:
            self.core.airprint_splice=paper=='splice'
            async def status(media=media):self.core.device={'connected':True,'media':5012 if media==5014 else media}
            self.core.status=status
            await status()
            result=await self.call(request(2,media,photo((640,320))))
            self.assertEqual(result.code,0,result.values('status-message'))
            job=self.core.jobs[-1];self.assertEqual(job['media'],media)
            with Image.open(self.core.data/job['file']) as image:self.assertEqual(image.size,size)
        self.core.airprint_splice=False
        async def status():self.core.device={'connected':True,'media':5012}
        self.core.status=status
        await status()
        for index,mime in enumerate(('image/urf','image/pwg-raster')):
            suffix='urf' if mime=='image/urf' else 'pwg'
            for shape in ('one-page','landscape'):
                data=(ROOT/f'tests/fixtures/airprint/{shape}.{suffix}').read_bytes()
                result=await self.call(request(2,100+index,data,[A(1,0x49,'document-format',mime.encode())]))
                self.assertEqual(result.code,0,result.values('status-message'))
            data=(ROOT/f'tests/fixtures/airprint/two-pages.{suffix}').read_bytes()
            self.assertNotEqual((await self.call(request(2,110+index,data,[A(1,0x49,'document-format',mime.encode())]))).code,0)
    async def test_restart_never_replays_incomplete_job(self):
        self.core.paused=True
        await self.core.submit({'id':'web','files':set()},{'requestId':'restart-test-0000001','pages':[page()]})
        self.core.jobs[0]['phase']='printing';self.core.save()
        await self.core.stop(None)
        recovered=PrintService(self.tmp.name,True)
        try:
            self.assertTrue(recovered.paused);self.assertEqual(recovered.jobs[0]['phase'],'uncertain');self.assertTrue(recovered.queue.empty())
        finally:
            for handle in recovered._locks:handle.close()
    async def test_cancel_while_waiting_for_device_never_sends(self):
        import time
        sent=[]
        def send(job):sent.append(job['owner']);time.sleep(.02);return 'done'
        self.core.simulate=False
        with patch.object(self.core,'send',side_effect=send),patch.object(self.core,'printer',side_effect=AssertionError('no hardware')):
            await self.core.io_lock.acquire()
            try:
                for owner in ('cancel-me','keep-me'):
                    await self.core.submit({'id':owner,'files':set()},{'requestId':'cancel-race-request-001','pages':[page()]})
                await asyncio.sleep(.02)
                await self.core.cancel({'id':'cancel-me'})
            finally:self.core.io_lock.release()
            for _ in range(100):
                if self.core.jobs[-1]['phase']=='done':break
                await asyncio.sleep(.01)
            self.assertEqual(sent,['keep-me']);self.assertEqual(self.core.jobs[0]['phase'],'cancelled')
    async def test_get_jobs_has_separate_groups(self):
        await self.call(request(5,1));await self.call(request(5,2))
        result=await self.adapter.handle(request(10,3),'client')
        parsed=decode_ipp(result)
        self.assertEqual(len(parsed.values('job-id')),2)
        self.assertEqual(result.count(b'\x02\x21\x00\x06job-id'),2)
    async def test_oversize_pdf_rejected_without_partial_batch(self):
        out=io.BytesIO();im=Image.new('RGB',(20,30),'blue');im.save(out,'PDF',save_all=True,append_images=[im]*6)
        result=await self.call(request(2,90,out.getvalue(),[A(1,0x49,'document-format',b'application/pdf')]))
        self.assertNotEqual(result.code,0);self.assertEqual(self.core.jobs,[])
    async def test_pdf_batch(self):
        out=io.BytesIO();im=Image.new('RGB',(200,300),'blue');im.save(out,'PDF',save_all=True,append_images=[Image.new('RGB',(300,200),'orange')])
        data=out.getvalue();attrs=[A(1,0x49,'document-format',b'application/pdf')]
        result=await self.call(request(2,90,data,attrs));self.assertEqual(result.code,0,result.values('status-message'));self.assertEqual(len(self.core.jobs[-1]['pages']),2)
        self.core.airprint_splice=True;result=await self.call(request(2,91,data,attrs));self.assertEqual(result.code,0,result.values('status-message'));self.assertEqual(len(self.core.jobs[-1]['pages']),1)

if __name__=='__main__':unittest.main()
