"""Per-operation Bluetooth lifetimes and live discovery; no hardware."""
import asyncio,json,tempfile,threading,time,unittest,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from printing.service import PrintService
from printing.images import UserError
from desktop.bonjour import Bonjour

class FakePrinter:
    def __init__(self,path):
        self.closed=0;self.sent=[];self.intent=Path(path)/'intent.json';self.client=self;self.last_state=9
    def close(self):self.closed+=1
    def get_prop(self,*names):return ['30','::0',{'media-size':5009},{'ribbon-info':[1,0,20]}]
    def print_photo(self,files,**kwargs):self.sent.append(files);return True
    def rpc(self,method,params):
        assert method=='get-job-info'
        return [{'job-id':params['job-id'],'job-state':9}]

class Lifecycle(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.core=PrintService(self.folder.name,True);await self.core.start(None);self.addAsyncCleanup(self.core.stop,None);self.core.simulate=False
        self.printer=FakePrinter(self.folder.name)
        self.enterContext(patch.object(self.core,'printer',return_value=self.printer))
    def batch(self):
        (self.core.data/'test.jpg').write_bytes(b'synthetic')
        job={'token':'test','phase':'printing','pages':[{'file':'test.jpg','copies':1,'sharpen':0,'media':5009}]*2}
        self.core.cancel_flags['test']=threading.Event();return job
    async def test_batch_keeps_one_channel_until_all_pages_complete(self):
        job=self.batch();self.core._active_job=job
        original=self.printer.print_photo
        def page(*args,**kwargs):
            self.assertEqual(self.printer.closed,0)
            self.core.device['checkedAt']-=300000
            self.assertTrue(self.core.airprint_ready())
            return original(*args,**kwargs)
        with patch.object(self.printer,'print_photo',side_effect=page):self.assertEqual(self.core.send(job),'done')
        self.assertEqual(len(self.printer.sent),2);self.assertEqual(self.printer.closed,1);self.assertIsNone(self.core.device_printer)
        self.assertFalse(self.core._batch_verified);self.assertTrue(self.core.airprint_ready())
    async def test_send_failure_closes_without_replaying(self):
        job=self.batch()
        def fail(*args,**kwargs):self.printer.intent.write_text('{"phase":"uploading","job":17}');raise OSError('lost connection')
        with patch.object(self.printer,'print_photo',side_effect=fail) as send:
            with self.assertRaises(OSError):self.core.send(job)
        self.assertEqual(send.call_count,1);self.assertEqual(self.printer.closed,1);self.assertTrue(self.printer.intent.exists())
        self.assertIsNone(self.core.device_printer);self.assertFalse(self.core.airprint_ready())
    async def test_close_failure_preserves_confirmed_print(self):
        with patch.object(self.printer,'close',side_effect=OSError('cleanup failed')):
            self.assertEqual(self.core.send(self.batch()),'done')
        self.assertFalse(self.core.airprint_ready());self.assertIsNone(self.core.device_printer)
    async def test_close_failure_preserves_original_upload_error(self):
        with patch.object(self.printer,'print_photo',side_effect=TimeoutError('upload failed')),patch.object(self.printer,'close',side_effect=OSError('cleanup failed')):
            with self.assertRaisesRegex(TimeoutError,'upload failed'):self.core.send(self.batch())
        self.assertFalse(self.core.airprint_ready())
    async def test_close_failure_preserves_confirmed_reconcile(self):
        self.printer.intent.write_text('{"job":17}');self.core.jobs=[{'owner':'test','phase':'uncertain'}]
        with patch.object(self.printer,'close',side_effect=OSError('cleanup failed')):
            await self.core.reconcile({'id':'test'})
        self.assertEqual(self.core.jobs[0]['phase'],'done');self.assertFalse(self.printer.intent.exists());self.assertFalse(self.core.airprint_ready())
    async def test_successful_probe_with_failed_close_is_unavailable(self):
        with patch.object(self.printer,'close',side_effect=OSError('cleanup failed')):
            with self.assertRaises(UserError):await self.core.status()
        self.assertFalse(self.core.device.get('connected'));self.assertFalse(self.core.airprint_ready())
    async def test_cancel_after_page_closes_batch(self):
        job=self.batch()
        def done(*args,**kwargs):self.core.cancel_flags['test'].set();return True
        with patch.object(self.printer,'print_photo',side_effect=done) as send:self.assertEqual(self.core.send(job),'cancelled')
        self.assertEqual(send.call_count,1);self.assertEqual(self.printer.closed,1)
    async def test_terminal_abort_closes_batch(self):
        job=self.batch();self.printer.last_state=7
        with patch.object(self.printer,'print_photo',return_value=False):self.assertEqual(self.core.send(job),'aborted')
        self.assertEqual(self.printer.closed,1)
    async def test_confirmed_print_is_not_made_uncertain_by_status_failure(self):
        job=self.batch()
        with patch.object(self.printer,'get_prop',side_effect=[['30','::0',{'media-size':5009},{'ribbon-info':[1,0,20]}],OSError('status unavailable')]):
            self.assertEqual(self.core.send(job),'done')
        self.assertEqual(self.printer.closed,1);self.assertFalse(self.core.airprint_ready())
    async def test_reconcile_success_closes_and_never_prints(self):
        self.printer.intent.write_text('{"job":17}');self.core.jobs=[{'owner':'test','phase':'uncertain'}]
        await self.core.reconcile({'id':'test'})
        self.assertEqual(self.core.jobs[0]['phase'],'done');self.assertEqual(self.printer.closed,1);self.assertEqual(self.printer.sent,[])
        self.assertIsNone(self.core.device_printer)
    async def test_reconcile_failure_closes_and_preserves_intent(self):
        self.printer.intent.write_text('{"job":17}');self.core.jobs=[{'owner':'test','phase':'uncertain'}]
        with patch.object(self.printer,'rpc',side_effect=OSError('lost connection')):
            with self.assertRaises(OSError):await self.core.reconcile({'id':'test'})
        self.assertTrue(self.printer.intent.exists());self.assertEqual(self.printer.closed,1);self.assertEqual(self.printer.sent,[])
        self.assertFalse(self.core.airprint_ready())
    async def test_cancelled_reconcile_keeps_lock_until_channel_closes(self):
        self.printer.intent.write_text('{"job":17}');self.core.jobs=[{'owner':'test','phase':'uncertain'}]
        entered=threading.Event();finish=threading.Event();original=self.printer.rpc
        def wait(*args):entered.set();finish.wait(3);return original(*args)
        with patch.object(self.printer,'rpc',side_effect=wait):
            task=asyncio.create_task(self.core.reconcile({'id':'test'}))
            try:
                await asyncio.to_thread(entered.wait,1);task.cancel();await asyncio.sleep(.02)
                self.assertTrue(self.core.io_lock.locked());self.assertFalse(task.done());self.assertEqual(self.printer.closed,0)
            finally:finish.set()
            with self.assertRaises(asyncio.CancelledError):await task
        self.assertFalse(self.core.io_lock.locked());self.assertEqual(self.printer.closed,1);self.assertEqual(self.printer.sent,[])
    async def test_freshness_and_real_paper_required(self):
        now=int(time.time()*1000);self.core.device={'connected':True,'media':5009,'state':'30','alert':'::0','checkedAt':now}
        self.assertEqual(self.core.available_media(now+150000),5009);self.assertEqual(self.core.available_media(now+150001),0)
        self.core.device['checkedAt']=now-150001
        async with self.core.io_lock:self.assertFalse(self.core.airprint_ready())
        self.core.device.update(checkedAt=now,media=9999);self.assertEqual(self.core.available_media(),0)
        self.core.device.update(media=5009,connected=False);self.assertFalse(self.core.airprint_ready())
    async def test_alert_release_and_uncertain_withdraw_readiness(self):
        await self.core.status();self.assertTrue(self.core.airprint_ready())
        self.core.device['alert']='::5402';self.assertFalse(self.core.airprint_ready())
        self.core.device['alert']='::0';self.core.device['ribbon']=0;self.assertFalse(self.core.airprint_ready())
        self.core.device['ribbon']=20;self.core.device['state']='10';self.assertFalse(self.core.airprint_ready())
        for state in ('20','30'):
            self.core.device['state']=state;self.assertTrue(self.core.airprint_ready())
        for state in ('10','40','50','60'):
            self.core.device['state']=state;self.assertFalse(self.core.airprint_ready())
        self.core.device['state']='30';self.core.jobs=[{'phase':'uncertain'}];self.assertFalse(self.core.airprint_ready())
        self.core.jobs=[];await self.core.release();self.assertFalse(self.core.airprint_ready())

class FakeProcess:
    def __init__(self):self.returncode=None;self.terminated=False
    def terminate(self):self.terminated=True;self.returncode=0
    async def wait(self):return self.returncode

class Discovery(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.core=PrintService(self.folder.name,True);await self.core.start(None);self.addAsyncCleanup(self.core.stop,None)
        self.calls=[];self.processes=[]
        async def spawn(*args,**kwargs):self.calls.append(args);p=FakeProcess();self.processes.append(p);return p
        adapter=type('Adapter',(),{'core':self.core,'identity':'urn:uuid:00000000-0000-0000-0000-000000000001'})()
        self.publisher=Bonjour(adapter,'Test Printer',1234,spawn);self.addAsyncCleanup(self.publisher.close)
    async def test_unknown_disconnected_and_stale_do_not_advertise(self):
        for change in ({'media':9999},{'media':5012,'connected':False},{'connected':True,'checkedAt':0}):
            self.core.device.update(change);await self.publisher.update();self.assertEqual(self.calls,[])
    async def test_ready_registers_and_failure_or_release_withdraws(self):
        await self.publisher.update();self.assertEqual(len(self.calls),1)
        await self.publisher.update();self.assertEqual(len(self.calls),1)
        self.core.device['connected']=False;await self.publisher.update();self.assertTrue(self.processes[0].terminated)
        await self.core.status();await self.publisher.update();self.assertEqual(len(self.calls),2)
        await self.core.release();await self.publisher.update();self.assertTrue(self.processes[1].terminated)
    async def test_physical_paper_and_splice_republish_capabilities(self):
        await self.publisher.update();self.core.device['media']=5009;await self.publisher.update()
        self.assertEqual(len(self.calls),2);self.assertTrue(self.processes[0].terminated)
        self.core.airprint_splice=True;await self.publisher.update();self.assertEqual(len(self.calls),2)
        self.core.device['media']=5012;await self.publisher.update();self.assertEqual(len(self.calls),3)
        pdl=next(a for a in self.calls[-1] if a.startswith('pdl='));self.assertEqual(pdl,'pdl=image/jpeg,application/pdf')
    async def test_active_verified_batch_does_not_flicker_after_ttl(self):
        await self.publisher.update();self.core._active_job={'phase':'printing'};self.core._batch_verified=True
        self.core.device['checkedAt']=0;await self.publisher.update();self.assertEqual(len(self.calls),1);self.assertFalse(self.processes[0].terminated)
        self.core._batch_verified=False;self.core._active_job=None;self.core.paused=True
        await self.publisher.update();self.assertTrue(self.processes[0].terminated)
    async def test_unresolved_results_remove_advertisement(self):
        await self.publisher.update();self.core.jobs=[{'phase':'uncertain'}]
        await self.publisher.update();self.assertTrue(self.processes[0].terminated)
    async def test_cancel_during_registration_closes_late_process(self):
        entered=asyncio.Event();finish=asyncio.Event();process=FakeProcess()
        async def delayed(*args,**kwargs):entered.set();await finish.wait();return process
        self.publisher.spawn=delayed;task=asyncio.create_task(self.publisher.update())
        await entered.wait();task.cancel();await asyncio.sleep(0)
        self.assertFalse(task.done());finish.set()
        with self.assertRaises(asyncio.CancelledError):await task
        self.assertTrue(process.terminated);self.assertIsNone(self.publisher.process)
    async def test_failed_process_is_not_restarted_in_tight_loop(self):
        await self.publisher.update();self.processes[0].returncode=1
        await self.publisher.update();await self.publisher.update();self.assertEqual(len(self.calls),1)
        self.publisher.retry_at=0;await self.publisher.update();self.assertEqual(len(self.calls),2)

if __name__=='__main__':unittest.main()
