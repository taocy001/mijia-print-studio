"""Anonymous display names without changing IPP endpoint identity."""
import asyncio
import json
from pathlib import Path
import tempfile
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import patch
from printing.identity import sharing_name
from printing.service import PrintService
from airprint.adapter import AirPrint
from web.serve import Studio
from desktop.windows_bonjour import WindowsBonjour


class Identity(unittest.TestCase):
    def test_restart_and_distinct_installations(self):
        with tempfile.TemporaryDirectory() as first,tempfile.TemporaryDirectory() as second:
            one=sharing_name(first);two=sharing_name(second)
            self.assertEqual(one,sharing_name(first));self.assertNotEqual(one,two)
            value=json.loads((Path(first)/'sharing-name.json').read_text())
            self.assertEqual(set(value),{'id'});uuid.UUID(value['id'])
            self.assertNotIn(first,one)

    def test_corrupt_display_metadata_recovers(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'sharing-name.json'
            for content in ['not json','[]','{}','{"id":"invalid"}','{"id":42}']:
                path.write_text(content)
                name=sharing_name(folder)
                self.assertEqual(name,sharing_name(folder))
                uuid.UUID(json.loads(path.read_text())['id'])

    def test_normalized_utf8_prefix_preserves_suffix(self):
        with tempfile.TemporaryDirectory() as folder:
            initial=sharing_name(folder);suffix=initial.split(' · ')[-1]
            for label in ['长名字'*100,'x.y\\z\n\r\0', '   ']:
                name=sharing_name(folder,label)
                self.assertLessEqual(len(name.encode()),48);self.assertTrue(name.endswith(suffix))
                self.assertNotIn('.',name);self.assertNotIn('\\',name);self.assertNotIn('\n',name)

    def test_web_ipp_bonjour_names_match_and_uuid_stays_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            core=PrintService(folder,True)
            try:
                name=sharing_name(folder,'测试共享')
                uri='ipp://liuying-test.local:8636/ipp/print'
                adapter=AirPrint(core,uri,name=name);studio=Studio(core=core,name=name)
                service=WindowsBonjour(adapter,name,8636,'192.168.1.20',factory=lambda **kw:None,info_factory=lambda *a,**kw:None)
                values={a.name:a.value for a in adapter.printer_attributes()}
                self.assertEqual(values['printer-name'].decode(),studio.name)
                self.assertEqual(values['printer-info'].decode(),name)
                self.assertEqual(service.instance,name+'._ipp._tcp.local.')
                self.assertEqual(adapter.identity,'urn:uuid:'+str(uuid.uuid5(uuid.NAMESPACE_URL,uri)))
            finally:
                for handle in core._locks:handle.close()

    def test_defaults_use_platform_not_machine_or_account(self):
        with tempfile.TemporaryDirectory() as folder:
            for platform,label in [('darwin','Mac'),('win32','Windows')]:
                with patch('printing.identity.sys.platform',platform):
                    # Avoid using a mocked Windows lock on a non-Windows runner.
                    with patch('printing.identity.lock_exclusive'):
                        name=sharing_name(folder,'Liuying Photo Printer')
                self.assertTrue(name.startswith('留影工坊 · '+label+' · '))


class Startup(unittest.IsolatedAsyncioTestCase):
    async def test_identity_write_failure_releases_service_lock(self):
        from desktop.serve import run
        with tempfile.TemporaryDirectory() as folder:
            args=SimpleNamespace(data=Path(folder),simulate=True)
            with patch('desktop.serve.sharing_name',side_effect=PermissionError('read only')):
                with self.assertRaises(PermissionError):await run(args)
            core=PrintService(folder,True)
            for handle in core._locks:handle.close()


if __name__=='__main__':unittest.main()
