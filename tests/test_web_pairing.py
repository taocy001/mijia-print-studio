"""Browser grants survive restart without exposing another browser's files."""
import hashlib,json,tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from aiohttp import DummyCookieJar
from aiohttp.test_utils import TestClient,TestServer
from web.serve import Studio,app
from web.pairing import Pairings,LIFETIME

class Pairing(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        await self.start()
    async def start(self):
        self.studio=Studio(self.tmp.name,True)
        self.client=TestClient(TestServer(app(self.studio)),cookie_jar=DummyCookieJar())
        await self.client.start_server();self.origin=str(self.client.make_url('/')).rstrip('/')
    async def asyncTearDown(self):await self.client.close()
    def headers(self,pair=None):return {'Origin':self.origin,**({'Cookie':f'liuying={pair[0]}; liuying-owner={pair[1]}'} if pair else {})}
    async def pair(self,owner=None):
        headers={'Origin':self.origin}
        if owner:headers['Cookie']='liuying-owner='+owner
        r=await self.client.post('/api/pair',data={'code':self.studio.code},headers=headers,allow_redirects=False)
        self.assertEqual(r.status,303)
        cookie=r.cookies['liuying'];self.assertEqual(cookie['max-age'],str(LIFETIME));self.assertTrue(cookie['httponly']);self.assertEqual(cookie['samesite'],'Strict');self.assertEqual(cookie['path'],'/')
        return cookie.value,r.cookies['liuying-owner'].value
    async def test_restart_keeps_grants_files_and_separate_identities(self):
        a,b=await self.pair(),await self.pair();sa=self.studio.session(a[0]);sb=self.studio.session(b[0])
        self.assertNotEqual(sa['id'],sb['id']);identity=sa['id']
        file=self.studio.data/'photos/a.jpg';file.parent.mkdir();file.write_bytes(b'synthetic')
        sa['files'].add('/private/photos/a.jpg');sa['uploads']=60;sa['bytes']=120*1024*1024;self.studio.remember(sa)
        saved=self.studio.pairings.path.read_text();self.assertNotIn(a[0],saved);self.assertNotIn(a[1],saved)
        await self.client.close();await self.start()
        r=await self.client.get('/api/sharing',headers=self.headers(a));value=await r.json();self.assertEqual(r.status,200);self.assertEqual(value['code'],self.studio.code)
        self.assertEqual(self.studio.session(a[0])['id'],identity);self.assertEqual(self.studio.session(a[0])['uploads'],0)
        self.assertEqual((await self.client.get('/private/photos/a.jpg',headers=self.headers(a))).status,200)
        self.assertEqual((await self.client.get('/private/photos/a.jpg',headers=self.headers(b))).status,404)
        mixed=(a[0],b[1]);await self.client.get('/api/state',headers=self.headers(mixed));self.assertEqual(self.studio.session(a[0])['id'],identity)
    async def test_unauthorized_expired_and_owner_only_cannot_read_code(self):
        a=await self.pair()
        for cookie in ['', 'liuying-owner='+a[1], 'liuying=invalid', 'liuying='+hashlib.sha256(a[0].encode()).hexdigest()]:
            r=await self.client.get('/api/sharing',headers={'Cookie':cookie});self.assertEqual(r.status,401);self.assertNotIn(self.studio.code,await r.text())
        key=hashlib.sha256(a[0].encode()).hexdigest();self.studio.pairings.records[key]['expires']=int(time.time())-1
        self.assertEqual((await self.client.get('/api/sharing',headers=self.headers(a))).status,401)
    async def test_reset_is_host_only_rotates_code_and_preserves_owner(self):
        a,b=await self.pair(),await self.pair();identity=self.studio.session(b[0])['id'];old_code=self.studio.code
        with patch('web.serve.ipaddress.ip_address',return_value=SimpleNamespace(is_loopback=False)):
            r=await self.client.get('/api/sharing',headers=self.headers(b));value=await r.json();self.assertEqual(value['code'],old_code);self.assertFalse(value['canManagePairing'])
            r=await self.client.post('/api/admin/pairing/reset',json={},headers=self.headers(b));self.assertEqual(r.status,403)
        r=await self.client.post('/api/admin/pairing/reset',json={},headers=self.headers(a));self.assertEqual(r.status,200);self.assertNotEqual(old_code,self.studio.code)
        self.assertEqual((await self.client.get('/api/sharing',headers=self.headers(a))).status,200)
        self.assertEqual((await self.client.get('/api/sharing',headers=self.headers(b))).status,401)
        r=await self.client.post('/api/pair',data={'code':old_code},headers=self.headers(b),allow_redirects=False);self.assertEqual(r.status,403)
        again=await self.pair(b[1]);self.assertEqual(self.studio.session(again[0])['id'],identity)
    async def test_failed_write_does_not_grant_or_reset(self):
        a=await self.pair();old_code=self.studio.code;records=dict(self.studio.pairings.records)
        with patch('web.pairing.atomic',side_effect=OSError('disk full')):
            r=await self.client.post('/api/pair',data={'code':old_code},headers={'Origin':self.origin},allow_redirects=False);self.assertEqual(r.status,409);self.assertNotIn('liuying',r.cookies)
            r=await self.client.post('/api/admin/pairing/reset',json={},headers=self.headers(a));self.assertEqual(r.status,409)
        self.assertEqual(records,self.studio.pairings.records);self.assertEqual(old_code,self.studio.code);self.assertIsNotNone(self.studio.session(a[0]))
    async def test_repair_same_browser_replaces_old_token_and_limit_expires(self):
        a=await self.pair();again=await self.pair(a[1]);self.assertIsNone(self.studio.session(a[0]));self.assertEqual(len(self.studio.pairings.live()),1)
        for _ in range(11):await self.pair()
        self.assertFalse(self.studio.pairings.available('0'*64));await self.pair(again[1])
        for record in self.studio.pairings.records.values():record['expires']=0
        self.assertTrue(self.studio.pairings.available('0'*64));await self.pair();self.assertEqual(len(self.studio.pairings.live()),1)
    async def test_corrupt_grant_file_does_not_authorize_owners(self):
        await self.pair();self.studio.pairings.path.write_text('[]')
        with self.assertRaises(ValueError):Pairings(Path(self.tmp.name))

if __name__=='__main__':unittest.main()
