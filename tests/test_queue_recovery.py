"""Durable page recovery and browser ownership; no physical printing."""
import asyncio,json,tempfile,threading,unittest
from pathlib import Path
from unittest.mock import patch
from aiohttp.test_utils import TestClient,TestServer
from printing.service import PrintService
from printing.images import UserError
from web.serve import Studio,app

class Printer:
    def __init__(self,root):self.intent=root/'intent.json';self.client=self;self.calls=0
    def close(self):pass
    def get_prop(self,*args):return ['30','::0',{'media-size':5012},{'ribbon-info':[0,0,20]}]
    def rpc(self,method,args):return [{'job-id':args['job-id'],'job-state':9}]
    def print_photo(self,files,**kw):
        self.calls+=1;cb=kw['on_state'];cb({'phase':'creating'})
        self.intent.write_text(json.dumps({'job':self.calls}));cb({'phase':'uploading','job':self.calls})
        if self.calls==2:raise OSError('lost response')
        self.intent.unlink();cb({'phase':'done','job':self.calls});return True

class Queue(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.core=PrintService(self.tmp.name,True);await self.core.start(None);self.addAsyncCleanup(self.core.stop,None);self.core.simulate=False
        self.printer=Printer(self.core.data);self.enterContext(patch.object(self.core,'printer',return_value=self.printer))
        (self.core.data/'p.jpg').write_bytes(b'fixture')
        self.job={'token':'batch','owner':'a','phase':'queued','pages':[dict(file='p.jpg',copies=1,sharpen=0,media=5012) for _ in range(3)]}
        self.core.jobs.append(self.job);self.core.cancel_flags['batch']=threading.Event()
    async def run_job(self):
        await self.core.queue.put(self.job)
        for _ in range(100):
            if self.job['phase'] not in ('queued','printing'):return
            await asyncio.sleep(.01)
        self.fail('worker stuck')
    async def test_progress_cannot_clear_unresolved_print_intent(self):
        def disconnected(*args, **kwargs):
            kwargs['on_state']({'phase':'creating'})
            self.printer.intent.write_text('{"job":1}')
            kwargs['on_state']({'phase':'uploading','job':1})
            kwargs['on_progress']({'stage':'transfer','sentBytes':80,'totalBytes':100,'sampleAt':1})
            self.assertEqual(self.job['progress'],80)
            kwargs['on_progress']({'stage':'waiting','device':{'job-state':2,'job-sub-state':4321},'sampleAt':2})
            self.assertTrue(self.job['mayHavePrinted'])
            self.assertEqual(self.job['phase'],'printing')
            self.assertEqual(self.job['progress'],-1)
            raise OSError('connection lost after upload')
        with patch.object(self.printer,'print_photo',side_effect=disconnected) as send:
            await self.run_job()
        self.assertEqual(send.call_count,1)
        self.assertEqual(self.job['phase'],'uncertain');self.assertTrue(self.core.paused)
        self.assertEqual(self.core.public(self.job)['telemetry']['device']['job-sub-state'],4321)
        self.assertTrue(self.printer.intent.exists())

    async def test_current_page_preview_uses_submitted_page(self):
        self.job['pages'][1].update(file='second.jpg',orientation='landscape',media=5014)
        self.job['currentPage']=1
        self.assertEqual(self.core.public(self.job)['previewPage'],{'file':'second.jpg','orientation':'landscape','media':5014})

    async def test_preflight_failure_does_not_pause(self):
        with patch.object(self.printer,'get_prop',side_effect=OSError('offline')):await self.run_job()
        self.assertEqual(self.job['phase'],'rejected');self.assertFalse(self.core.paused);self.assertEqual(self.printer.calls,0)
    async def test_mid_batch_reconcile_never_sends_remaining_page(self):
        await self.run_job()
        self.assertEqual(self.job['phase'],'uncertain');self.assertEqual(self.job['completedPages'],1);self.assertEqual(self.job['jobId'],2)
        saved=json.loads((self.core.data/'jobs.json').read_text())[0];self.assertEqual(saved['currentPage'],1)
        await self.core.reconcile({'id':'a'})
        self.assertEqual(self.job['phase'],'cancelled');self.assertEqual(self.job['completedPages'],2);self.assertFalse(self.core.paused)
        self.assertEqual(self.printer.calls,2);self.assertNotIn('phase',self.job['pages'][2])
    async def test_last_page_reconcile_can_complete_batch(self):
        self.job['pages']=self.job['pages'][:2];await self.run_job()
        await self.core.reconcile({'id':'a'})
        self.assertEqual(self.job['phase'],'done');self.assertEqual(self.job['completedPages'],2);self.assertEqual(self.printer.calls,2)
    async def test_intent_creation_failure_is_rejected(self):
        def fail(*args,**kwargs):kwargs['on_state']({'phase':'creating'});raise OSError('disk full')
        with patch.object(self.printer,'print_photo',side_effect=fail):await self.run_job()
        self.assertEqual(self.job['phase'],'rejected');self.assertFalse(self.core.paused)
    async def test_restart_never_requeues_partially_sent_batch(self):
        await self.run_job()
        with tempfile.TemporaryDirectory() as target:
            Path(target,'jobs.json').write_text((self.core.data/'jobs.json').read_text())
            recovered=PrintService(target,True)
            try:
                self.assertTrue(recovered.paused);self.assertTrue(recovered.queue.empty())
                self.assertEqual(recovered.jobs[0]['jobId'],2);self.assertEqual(recovered.jobs[0]['completedPages'],1)
            finally:
                for held in recovered._locks:held.close()
    async def test_aborted_transfer_message_reaches_public_history(self):
        from printing.bluetooth_printer import terminal_info,terminal_message
        info=terminal_info({'job-state':7,'transfer-status':3,'file-size':367542,'transfer-size':367541,'file':'private'})
        def abort(*args,**kwargs):
            self.printer.last_state=7
            kwargs['on_state']({'phase':'aborted','job':145,'info':info,'message':terminal_message(info)})
            return False
        with patch.object(self.printer,'print_photo',side_effect=abort):await self.run_job()
        public=self.core.public(self.job)
        self.assertEqual(public['phase'],'aborted');self.assertIn('缺少 1 字节',public['message']);self.assertFalse(self.core.paused)
        self.assertNotIn('file',public['terminalInfo'])
    async def test_other_owner_cannot_reconcile(self):
        await self.run_job();await self.core.reconcile({'id':'b'})
        self.assertEqual(self.job['phase'],'uncertain');self.assertTrue(self.printer.intent.exists())
    async def test_resolve_requires_explicit_confirmation_and_idle(self):
        await self.run_job()
        with self.assertRaises(UserError):await self.core.resolve({'id':'a'},'batch',1)
        async with self.core.io_lock:
            with self.assertRaises(UserError):await self.core.resolve({'id':'a'},'batch',True)
        import hashlib
        self.core.address='00:11:22:33:44:55';directory=self.core.data/'bluetooth-state';directory.mkdir()
        current=directory/(hashlib.sha256(self.core.address.encode()).hexdigest()[:24]+'.json');current.write_text('{truncated')
        other=directory/'other.json';other.write_text('{"job":3}')
        await self.core.resolve({'id':'a'},'batch',True)
        self.assertFalse(current.exists());self.assertTrue(other.exists());self.assertEqual(len(list(directory.glob('*.resolved-*'))),1)
        self.assertEqual(self.job['phase'],'cancelled');self.assertFalse(self.core.paused);self.assertEqual(self.printer.calls,2)

class Browser(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
    async def start_server(self):
        self.studio=Studio(self.tmp.name,True);self.client=TestClient(TestServer(app(self.studio)));await self.client.start_server()
        self.origin=str(self.client.make_url('/')).rstrip('/')
    async def pair(self,owner=None):
        headers={'Origin':self.origin}
        if owner:headers['Cookie']='liuying-owner='+owner
        r=await self.client.post('/api/pair',data={'code':self.studio.code},headers=headers,allow_redirects=False)
        self.assertEqual(r.status,303);return r.cookies['liuying-owner'].value
    async def test_restart_requires_pair_then_restores_owner_and_private_history(self):
        await self.start_server();owner=await self.pair();session=next(iter(self.studio.sessions.values()))
        (self.studio.data/'photos').mkdir();(self.studio.data/'photos/test.jpg').write_bytes(b'photo')
        session['files'].add('/private/photos/test.jpg');self.studio.remember(session)
        self.studio.core.jobs.append(dict(owner=session['id'],token='old',phase='rejected',file='photos/test.jpg',pages=[{'file':'photos/test.jpg','media':5009}]));self.studio.core.save()
        await self.client.close();await self.start_server()
        try:
            r=await self.client.get('/api/state',headers={'Cookie':'liuying-owner='+owner});self.assertEqual(r.status,401)
            await self.pair(owner)
            r=await self.client.get('/api/state');state=await r.json();self.assertEqual(state['history'][0]['phase'],'rejected');self.assertTrue(state['canManageQueue'])
            r=await self.client.get('/private/photos/test.jpg');self.assertEqual(r.status,200)
            r=await self.client.get('/api/admin/queue');public=(await r.json())['jobs'][0];self.assertNotIn('file',public);self.assertNotIn('previewPage',public)
            from types import SimpleNamespace
            with patch('web.serve.ipaddress.ip_address',return_value=SimpleNamespace(is_loopback=False)):
                r=await self.client.get('/api/admin/queue',headers={'X-Forwarded-For':'127.0.0.1'});self.assertEqual(r.status,403)
                r=await self.client.post('/api/admin/resolve',json={'token':'old','confirmed':True},headers={'Origin':self.origin,'X-Forwarded-For':'127.0.0.1'});self.assertEqual(r.status,403)
            self.client.session.cookie_jar.clear();await self.pair()
            r=await self.client.get('/private/photos/test.jpg');self.assertEqual(r.status,404)
        finally:await self.client.close()

class Reprint(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        import base64,io
        from PIL import Image
        from printing.images import page_files
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.core=PrintService(self.tmp.name,True)
        self.addCleanup(lambda:[held.close() for held in self.core._locks])
        photo=io.BytesIO();Image.new('RGB',(1040,1040),'green').save(photo,'JPEG')
        mask=io.BytesIO();Image.new('RGB',(1040,1040),'white').save(mask,'PNG')
        self.jpeg,self.coat=page_files(dict(base64=base64.b64encode(photo.getvalue()).decode(),ocMask=base64.b64encode(mask.getvalue()).decode(),media=5009,threshold=123))
        (self.core.data/'prints').mkdir();(self.core.data/'prints/original.jpg').write_bytes(self.jpeg);(self.core.data/'prints/original.oc').write_bytes(self.coat)
        self.page=dict(file='prints/original.jpg',ocFile='prints/original.oc',media=5009,copies=2,sharpen=2,title='姓名贴',orientation='square',phase='done')
        self.source=dict(owner='a',token='original',phase='done',pages=[self.page,dict(self.page)])
        self.core.jobs=[self.source];self.session={'id':'a','files':{'/private/prints/original.jpg'}}
        self.body=dict(token='original',requestId='exact-reprint-12345',confirmed=True)
    async def test_exact_bytes_and_parameters_and_idempotent_retry(self):
        response=await self.core.reprint(self.session,self.body);job=self.core.jobs[-1]
        self.assertEqual(job['phase'],'queued');self.assertEqual(len(job['pages']),2)
        for page in job['pages']:
            self.assertEqual((self.core.data/page['file']).read_bytes(),self.jpeg)
            self.assertEqual((self.core.data/page['ocFile']).read_bytes(),self.coat)
            for key in ('copies','media','sharpen','orientation','title'):self.assertEqual(page[key],self.page[key])
        duplicate=await self.core.reprint(self.session,self.body)
        self.assertTrue(duplicate['duplicate']);self.assertEqual(response['token'],duplicate['token']);self.assertEqual(self.core.queue.qsize(),1)
    async def test_confirmation_owner_and_file_grants_required(self):
        for session,body in [(self.session,{**self.body,'confirmed':False}),({'id':'b','files':self.session['files']},self.body),({'id':'a','files':set()},self.body)]:
            with self.assertRaises(UserError):await self.core.reprint(session,body)
        self.assertTrue(self.core.queue.empty())
    async def test_unknown_and_path_escape_are_not_reprinted(self):
        self.source['phase']='uncertain'
        with self.assertRaises(UserError):await self.core.reprint(self.session,self.body)
        self.source['phase']='done';self.page['ocFile']='../secret.oc'
        with self.assertRaises(UserError):await self.core.reprint(self.session,self.body)
        self.assertTrue(self.core.queue.empty())
    async def test_request_id_cannot_switch_original_work(self):
        await self.core.reprint(self.session,self.body)
        self.core.jobs.append({**self.source,'token':'different'})
        with self.assertRaises(UserError):await self.core.reprint(self.session,{**self.body,'token':'different'})
        self.assertEqual(self.core.queue.qsize(),1)

if __name__=='__main__':unittest.main()
