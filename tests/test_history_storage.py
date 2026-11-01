"""History cleanup uses temporary simulated jobs only."""
import asyncio
import base64
import io
import json
from pathlib import Path
import tempfile
import unittest
import uuid
from unittest.mock import patch, Mock
from aiohttp.test_utils import make_mocked_request
from web.serve import Studio
from PIL import Image
from printing.service import PrintService
from printing.images import UserError
from printing import history


class HistoryStorage(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.core=PrintService(self.tmp.name,True);self.addCleanup(lambda:[h.close() for h in self.core._locks])
        self.owner={'id':'one','files':set()};self.other={'id':'two','files':set()}
        output=io.BytesIO();Image.new('RGB',(1040,1040),'#4c81ac').save(output,'JPEG')
        self.page={'media':5009,'base64':base64.b64encode(output.getvalue()).decode()}
    async def job(self,session=None,phase='done'):
        session=session or self.owner
        request={'requestId':str(uuid.uuid4()),'pages':[self.page]}
        await self.core.submit(session,request);job=self.core.jobs[-1];job['phase']=phase;self.core.save()
        return job,request
    async def clear(self,**values):
        return await self.core.history_cleanup(self.owner,dict(confirmed=True,**values))

    async def test_cleanup_keeps_identity_and_rejects_reprint(self):
        job,request=await self.job();path=self.core.data/job['file'];size=path.stat().st_size
        result,removed=await self.clear()
        self.assertEqual(result['bytes'],size);self.assertFalse(path.exists());self.assertIn(job['file'],removed)
        public=self.core.public(job);self.assertNotIn('file',public);self.assertFalse(public['canReprint'])
        self.assertTrue((await self.core.submit(self.owner,request))['duplicate']);self.assertEqual(len(self.core.jobs),1)
        with self.assertRaises(UserError):await self.core.reprint(self.owner,{'token':job['token'],'confirmed':True,'requestId':str(uuid.uuid4())})
        self.assertEqual(json.loads((self.core.data/'jobs.json').read_text())[0]['requestId'],request['requestId'])

    async def test_all_pages_and_overcoat_deleted_together(self):
        await self.core.submit(self.owner,{'requestId':str(uuid.uuid4()),'pages':[self.page,self.page]})
        job=self.core.jobs[-1];job['phase']='done'
        for page in job['pages']:
            page['ocFile']='prints/'+str(uuid.uuid4())+'.oc'
            (self.core.data/page['ocFile']).write_bytes(b'overcoat')
        names=history.references(job);expected=sum((self.core.data/n).stat().st_size for n in names)
        result,_=await self.clear()
        self.assertEqual(result['files'],4);self.assertEqual(result['bytes'],expected)
        self.assertTrue(all(not (self.core.data/n).exists() for n in names))

    async def test_other_owner_active_uncertain_and_current_draft_survive(self):
        records=[]
        for owner,phase in [(self.other,'done'),(self.owner,'queued'),(self.owner,'uncertain'),(self.owner,'done')]:
            job,_=await self.job(owner,phase);records.append(job)
        result,_=await self.clear(keepFiles=['/private/'+records[-1]['file']])
        self.assertEqual(result['bytes'],0)
        self.assertTrue(all((self.core.data/j['file']).exists() for j in records))

    async def test_shared_references_protect_whole_batch(self):
        old,_=await self.job();other,_=await self.job(self.other)
        second='prints/'+str(uuid.uuid4())+'.oc';(self.core.data/second).write_bytes(b'coat')
        old['pages'][0]['ocFile']=second;other['pages'][0]['ocFile']=second
        result,_=await self.clear();self.assertEqual(result['bytes'],0)
        self.assertFalse(old.get('filesCleared'));self.assertTrue((self.core.data/old['file']).exists())

    async def test_failed_save_deletes_nothing(self):
        job,_=await self.job()
        with patch.object(self.core,'save',side_effect=OSError('disk full')):
            with self.assertRaises(OSError):await self.clear()
        self.assertFalse(job.get('filesCleared'));self.assertTrue((self.core.data/job['file']).exists())

    async def test_failed_unlink_is_persisted_and_retryable(self):
        job,_=await self.job();name=job['file']
        with patch.object(Path,'unlink',side_effect=PermissionError):
            result,_=await self.clear()
        self.assertEqual(result['files'],0);self.assertEqual(result['pending'],1)
        self.assertEqual(job['cleanupPending'],[name]);self.assertFalse(self.core.public(job)['canReprint'])
        result,_=await self.clear();self.assertEqual(result['files'],1);self.assertEqual(job['cleanupPending'],[])

    async def test_reprint_preparation_blocks_cleanup(self):
        job,_=await self.job();entered=asyncio.Event();release=asyncio.Event()
        original=self.core.submit
        async def slow(*args,**kwargs):entered.set();await release.wait();return await original(*args,**kwargs)
        with patch.object(self.core,'submit',slow):
            reprint=asyncio.create_task(self.core.reprint(self.owner,{'token':job['token'],'confirmed':True,'requestId':str(uuid.uuid4())}))
            await entered.wait();cleanup=asyncio.create_task(self.clear());await asyncio.sleep(.01)
            self.assertFalse(cleanup.done());self.assertTrue((self.core.data/job['file']).exists())
            release.set();await reprint;await cleanup
        self.assertTrue((self.core.data/self.core.jobs[-1]['file']).exists())

    async def test_device_busy_and_unconfirmed_refused(self):
        job,_=await self.job()
        async with self.core.io_lock:
            with self.assertRaises(UserError):await self.clear()
        with self.assertRaises(UserError):await self.core.history_cleanup(self.owner,{})
        self.assertTrue((self.core.data/job['file']).exists())

    async def test_invalid_path_and_symlink_never_deleted(self):
        job,_=await self.job();outside=self.core.data/'source.jpg';outside.write_bytes(b'private source')
        job['pages'][0]['file']='../source.jpg'
        await self.clear();self.assertTrue(outside.exists())
        job['pages'][0]['file']=job['file'];target=self.core.data/job['file'];target.unlink()
        try:target.symlink_to(outside)
        except OSError:self.skipTest('Symlinks unavailable')
        await self.clear();self.assertTrue(outside.exists());self.assertTrue(target.is_symlink())

    async def test_api_revokes_all_owner_sessions_and_persistent_access(self):
        job,_=await self.job();name='/private/'+job['file']
        studio=Studio(core=self.core)
        studio.sessions={'a':dict(id='one',files={name}), 'b':dict(id='one',files={name}), 'c':dict(id='two',files={'/private/photos/kept.jpg'})}
        studio.owners={'one':dict(id='one',files=[name]), 'two':dict(id='two',files=['/private/photos/kept.jpg'])}
        transport=Mock();transport.get_extra_info.side_effect=lambda key:('127.0.0.1',8635) if key=='sockname' else ('192.168.1.10',123)
        request=make_mocked_request('POST','/api/history/clear',headers={'Host':'127.0.0.1:8635','Origin':'http://127.0.0.1:8635','Cookie':'liuying=a'},transport=transport)
        request._read_bytes=b'{"confirmed":true,"keepFiles":[]}'
        response=await studio.handle(request)
        self.assertEqual(response.status,200)
        self.assertEqual(studio.sessions['a']['files'],set());self.assertEqual(studio.sessions['b']['files'],set())
        stored=json.loads((self.core.data/'web-owners.json').read_text())
        self.assertEqual(stored['one']['files'],[]);self.assertEqual(stored['two']['files'],['/private/photos/kept.jpg'])

    async def test_restart_keeps_cleanup_marker_and_duplicate_identity(self):
        job,request=await self.job()
        with patch.object(Path,'unlink',side_effect=PermissionError):await self.clear()
        for handle in self.core._locks:handle.close()
        restored=PrintService(self.tmp.name,True)
        try:
            self.assertFalse(restored.public(restored.jobs[0])['canReprint'])
            self.assertTrue((await restored.submit(self.owner,request))['duplicate'])
            result,_=await restored.history_cleanup(self.owner,{'confirmed':True})
            self.assertEqual(result['files'],1);self.assertEqual(len(restored.jobs),1)
        finally:
            for handle in restored._locks:handle.close()


if __name__=='__main__':unittest.main()
