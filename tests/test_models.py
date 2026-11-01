"""Model management with a local fixture server; never loads a printer."""
import asyncio
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch, Mock
from aiohttp import web
from aiohttp.test_utils import TestServer, make_mocked_request
from printing import models
from printing.platform import open_lock, lock_exclusive
from web.serve import Studio


class Models(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name);(self.root/'deps').mkdir()
        self.data = b'pinned-model-test-content'
        (self.root/'deps/checksums.json').write_text(json.dumps({'assets/models/test.onnx':hashlib.sha256(self.data).hexdigest()}))
        self.hits=0;self.mode='ok';self.entered=asyncio.Event()
        async def download(request):
            self.hits+=1;self.entered.set()
            if self.mode=='slow':await asyncio.sleep(.3)
            if self.mode=='bad':return web.Response(body=b'wrong checksum')
            if self.mode=='large':return web.Response(body=b'x'*129)
            if self.mode=='chunked':
                response=web.StreamResponse();await response.prepare(request)
                await response.write(b'x'*129);await response.write_eof();return response
            if self.mode=='http':raise web.HTTPServiceUnavailable()
            return web.Response(body=self.data)
        app=web.Application();app.router.add_get('/model',download)
        self.server=TestServer(app);await self.server.start_server();self.addAsyncCleanup(self.server.close)
        self.catalog=patch.dict(models.MODELS,{'test':('Test','test.onnx',str(self.server.make_url('/model')),128)},clear=True)
        self.catalog.start();self.addCleanup(self.catalog.stop)
        self.store=models.ModelStore(self.root);self.addAsyncCleanup(self.store.close)

    async def finish(self):
        await self.store.tasks['test']
        return (await self.store.status())['models'][0]

    async def test_missing_download_verified_and_duplicate(self):
        self.assertEqual((await self.store.status())['models'][0]['state'],'missing')
        self.store.start('test');first=self.store.tasks['test'];self.store.start('test')
        self.assertIs(self.store.tasks['test'],first)
        self.assertEqual((await self.finish())['state'],'verified')
        self.assertEqual(self.store.path('test').read_bytes(),self.data)
        self.store.start('test');await self.finish();self.assertEqual(self.hits,1)

    async def test_failed_download_preserves_file_and_can_retry(self):
        path=self.store.path('test');path.parent.mkdir(parents=True);path.write_bytes(b'existing invalid file')
        for mode in ['bad','large','chunked','http']:
            self.mode=mode;self.store.start('test')
            self.assertEqual((await self.finish())['state'],'failed',mode)
            self.assertEqual(path.read_bytes(),b'existing invalid file')
            self.assertFalse(list(path.parent.glob('.*.download')))
        self.mode='ok';self.store.start('test');self.assertEqual((await self.finish())['state'],'verified')

    async def test_cancel_cleans_temporary_and_preserves_old(self):
        path=self.store.path('test');path.parent.mkdir(parents=True);path.write_bytes(b'old')
        self.mode='slow';self.store.start('test');await self.entered.wait();await self.store.close()
        self.assertEqual(path.read_bytes(),b'old');self.assertFalse(list(path.parent.glob('.*.download')))
        with self.assertRaises(ValueError):self.store.start('test')

    async def test_timeout_and_unknown_identifier(self):
        with self.assertRaises(ValueError):self.store.start('../other')
        with patch('aiohttp.ClientSession.get',side_effect=asyncio.TimeoutError):
            self.store.start('test');self.assertEqual((await self.finish())['state'],'failed')
        self.assertFalse(list(self.store.path('test').parent.glob('.*.download')))

    async def test_external_download_lock(self):
        path=self.store.path('test');path.parent.mkdir(parents=True)
        locks=self.root/'build/dependency-locks';locks.mkdir(parents=True)
        with open_lock(locks/(path.name+'.lock')) as lock:
            lock_exclusive(lock);self.store.start('test')
            self.assertEqual((await self.finish())['state'],'failed')
        self.assertEqual(self.hits,0)

    async def test_runtime_failure_is_separate_from_verified_file(self):
        self.store.start('test');await self.finish()
        with patch.object(models.importlib,'import_module',side_effect=ImportError):
            status=await self.store.status()
        self.assertFalse(status['runtime']);self.assertEqual(status['models'][0]['state'],'verified')

    def request(self, path, peer='127.0.0.1', method='GET', paired=True, origin=None):
        transport=Mock()
        transport.get_extra_info.side_effect=lambda key:('127.0.0.1',8635) if key=='sockname' else (peer,1234)
        headers={'Host':'127.0.0.1:8635','Origin':origin or 'http://127.0.0.1:8635','X-Forwarded-For':'127.0.0.1'}
        if paired:headers['Cookie']='liuying=test'
        req=make_mocked_request(method,path,headers=headers,transport=transport)
        req._read_bytes=b'{"id":"test"}'
        return req

    async def test_state_advertises_capabilities_without_admin_privilege(self):
        core=SimpleNamespace(data=self.root,simulate=True,jobs=[],public=lambda job:job,airprint_splice=False,device={})
        studio=Studio(core=core);studio.sessions['test']={'id':'test'}
        response=await studio.handle(self.request('/api/state',peer='192.168.1.2'))
        value=json.loads(response.text)
        self.assertEqual(value['capabilities'],{'models':True,'historyStorage':True})
        self.assertFalse(value['canManageQueue'])

    async def test_api_auth_origin_and_host_only_download(self):
        studio=Studio(core=SimpleNamespace(data=self.root,simulate=True));studio.models=self.store
        studio.sessions['test']={'id':'test'}
        response=await studio.handle(self.request('/api/models',paired=False));self.assertEqual(response.status,401)
        response=await studio.handle(self.request('/api/models',peer='192.168.1.2'))
        self.assertFalse(json.loads(response.text)['canManage'])
        with self.assertRaises(web.HTTPForbidden):
            await studio.handle(self.request('/api/admin/models',peer='192.168.1.2',method='POST'))
        with self.assertRaises(web.HTTPForbidden):
            await studio.handle(self.request('/api/admin/models',method='POST',origin='http://untrusted.test'))
        self.assertEqual(self.hits,0)
        response=await studio.handle(self.request('/api/admin/models',method='POST'))
        self.assertEqual(response.status,202);await self.finish();self.assertEqual(self.hits,1)


if __name__=='__main__':unittest.main()
