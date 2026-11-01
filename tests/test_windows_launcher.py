"""Launcher lifecycle and installer checks use simulated services only."""
import asyncio
import contextlib
import io
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from desktop import windows_launcher as launcher, windows_dependencies as installer
from printing.platform import open_lock,lock_exclusive


def free_port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]


class Settings(unittest.TestCase):
    def test_local_defaults_require_explicit_printer(self):
        with self.assertRaises(ValueError):launcher.validate(launcher.DEFAULTS)
        args,env=launcher.command(dict(launcher.DEFAULTS,simulate=True),Path('folder with spaces'))
        self.assertNotIn('--lan',args);self.assertNotIn('--announce',args)
        self.assertIn('--simulate',args);self.assertNotIn('MIJIA_BLUETOOTH_ADDRESS',env)
        self.assertIn('folder with spaces',args)

    def test_invalid_settings(self):
        for extra in [dict(lan='false'),dict(web_port=True),dict(web_port=0),dict(ipp_port=8635),dict(printer=['bad']),dict(lan=True,address='127.0.0.1',network='0.0.0.0/0')]:
            with self.subTest(extra=extra),self.assertRaises(ValueError):launcher.validate(dict(launcher.DEFAULTS,simulate=True,**extra))

    def test_lan_requires_local_private_address_and_containing_network(self):
        with patch.object(launcher.socket,'socket'):
            settings=launcher.validate(dict(launcher.DEFAULTS,simulate=True,lan=True,address='192.168.20.5',network='192.168.20.0/24'))
            args,_=launcher.command(settings,Path('data'))
            self.assertIn('--lan',args);self.assertNotIn('--announce',args)
            with self.assertRaises(ValueError):launcher.validate(dict(settings,network='192.168.21.0/24'))
            with self.assertRaises(ValueError):launcher.validate(dict(settings,network='::/0'))

    def test_config_atomic_and_no_pair_code(self):
        with tempfile.TemporaryDirectory(prefix='studio 空格 ') as folder:
            path=Path(folder)/'launcher.json';value=dict(launcher.DEFAULTS,simulate=True,pair_code='not saved')
            launcher.save_settings(path,value);self.assertEqual(launcher.load_settings(path),dict(launcher.DEFAULTS,simulate=True))
            before=path.read_bytes()
            with self.assertRaises(ValueError):launcher.save_settings(path,dict(value,web_port=-1))
            self.assertEqual(path.read_bytes(),before)
            path.write_text('{bad')
            with self.assertRaises(ValueError):launcher.load_settings(path)
            self.assertEqual(path.read_text(),'{bad')
            for raw in [{'lan':'invalid'},{'simulate':0},{'web_port':True},{'printer':[]}]:
                path.write_text(json.dumps(raw))
                with self.assertRaises(ValueError):launcher.load_settings(path)
                self.assertEqual(json.loads(path.read_text()),raw)


class Installation(unittest.TestCase):
    def fixture(self,folder):
        root=Path(folder)/'项目 folder';(root/'desktop').mkdir(parents=True);(root/'web').mkdir()
        (root/'desktop/requirements-windows.txt').write_text('pinned-windows\n');(root/'web/requirements.txt').write_text('pinned-core\n')
        return root,Path(folder)/'user data'

    def test_failure_does_not_mark_installed_and_retry_succeeds(self):
        with tempfile.TemporaryDirectory() as folder:
            root,data=self.fixture(folder);calls=[]
            def fail(args,**kw):calls.append(args);return SimpleNamespace(returncode=1 if 'pip' in args else 0)
            with self.assertRaises(RuntimeError):installer.prepare(root,data,fail)
            self.assertFalse((root/'build/windows-requirements.txt').exists())
            def success(args,**kw):calls.append(args);return SimpleNamespace(returncode=0)
            installer.prepare(root,data,success);self.assertTrue((root/'build/windows-requirements.txt').exists())
            calls.clear();installer.prepare(root,data,success)
            self.assertEqual(len(calls),1);self.assertNotIn('pip',calls[0])
            self.assertFalse(any('windows_host' in str(c) for c in calls))

    def test_running_service_prevents_dependency_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            root,data=self.fixture(folder);data.mkdir()
            with open_lock(data/'service.lock') as held:
                lock_exclusive(held)
                with patch.object(installer.subprocess,'run') as run:
                    with self.assertRaises(RuntimeError):installer.prepare(root,data,run)
                    run.assert_not_called()


class Lifecycle(unittest.TestCase):
    def wait(self,service,condition):
        events=[]
        for _ in range(150):
            events+=service.receive()
            if condition():return events
            time.sleep(.05)
        self.fail('Timed out waiting for launcher lifecycle: '+repr(events[-4:]))

    def test_ready_stop_duplicate_and_restart(self):
        with tempfile.TemporaryDirectory(prefix='studio 空格 ') as folder:
            data=Path(folder);settings=dict(launcher.DEFAULTS,simulate=True,web_port=free_port(),ipp_port=free_port())
            service=launcher.Service();other=launcher.Service()
            try:
                service.start(settings,data);self.wait(service,lambda:service.ready)
                other.start(settings,data);events=self.wait(other,lambda:other.process is None)
                self.assertTrue(any(kind=='exit' and value!=0 for kind,value in events));self.assertTrue(service.ready)
                service.stop();self.wait(service,lambda:service.process is None)
                self.assertFalse(service.ready)
                jobs=json.loads((data/'jobs.json').read_text());self.assertEqual(jobs,[])
                service.start(settings,data);self.wait(service,lambda:service.ready)
                service.stop();self.wait(service,lambda:service.process is None)
            finally:
                for item in (service,other):
                    item.stop()
                    if item.process:self.wait(item,lambda:item.process is None)

    def test_parent_pipe_eof_stops_without_console_signal(self):
        with tempfile.TemporaryDirectory() as folder:
            service=launcher.Service();settings=dict(launcher.DEFAULTS,simulate=True,web_port=free_port(),ipp_port=free_port())
            service.start(settings,Path(folder));self.wait(service,lambda:service.ready)
            service.process.stdin.close();self.wait(service,lambda:service.process is None)


@unittest.skipUnless(sys.platform=='win32','Native Windows GUI and sharing modes')
class NativeWindows(unittest.TestCase):
    def test_runtime_lease_blocks_installer_for_custom_data(self):
        from desktop.windows_runtime import lease
        import base64,subprocess
        path=launcher.ROOT/'build/windows-install.lock'
        source="$p='"+str(path).replace("'","''")+"';try{$h=[IO.File]::Open($p,'OpenOrCreate','ReadWrite','None');$h.Dispose();exit 0}catch{exit 3}"
        args=['powershell.exe','-NoProfile','-EncodedCommand',base64.b64encode(source.encode('utf-16-le')).decode()]
        with lease():self.assertEqual(subprocess.run(args,capture_output=True,timeout=10).returncode,3)
        self.assertEqual(subprocess.run(args,capture_output=True,timeout=10).returncode,0)

    def test_native_window_starts_and_closes_simulation(self):
        import tkinter as tk
        with tempfile.TemporaryDirectory(prefix='studio GUI ') as folder:
            root=tk.Tk();root.withdraw();window=launcher.Window(root,Path(folder))
            window.values['simulate'].set(True)
            window.values['web_port'].set(str(free_port()));window.values['ipp_port'].set(str(free_port()))
            window.start()
            try:
                for _ in range(150):
                    root.update()
                    if window.service.ready:break
                    time.sleep(.05)
                self.assertTrue(window.service.ready)
                self.assertEqual(str(window.open_button['state']),'normal')
                self.assertIn('模拟',window.status.get())
            finally:
                window.close()
                for _ in range(150):
                    if window.service.process is None:break
                    root.update();time.sleep(.05)
                self.assertIsNone(window.service.process)



class Graceful(unittest.IsolatedAsyncioTestCase):
    async def test_stop_waits_for_inflight_device_operation(self):
        from desktop.serve import run
        from printing.service import PrintService
        with tempfile.TemporaryDirectory() as folder:
            core=PrintService(folder,True);original=core.start
            async def start(app):await original(app);await core.io_lock.acquire()
            core.start=start
            event=asyncio.Event();ready=asyncio.Event()
            args=SimpleNamespace(data=Path(folder),simulate=True,entry='web',lan=False,web_port=free_port())
            with patch('desktop.serve.PrintService',return_value=core),contextlib.redirect_stdout(io.StringIO()):
                task=asyncio.create_task(run(args,stop_event=event,on_ready=ready.set))
                await asyncio.wait_for(ready.wait(),3);event.set();await asyncio.sleep(.1)
                self.assertFalse(task.done())
                core.io_lock.release();await asyncio.wait_for(task,3)
            self.assertEqual(core.jobs,[])


if __name__=='__main__':unittest.main()
