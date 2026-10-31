"""Windows adapter tests use synthetic data and never connect to Bluetooth."""
import errno
import io
import importlib.util
import json
import os
import queue
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import Mock,patch
from printing import platform as host
from printing.windows_transport import connect,serve
from desktop.windows import arguments
from printing.service import PrintService

class TransportTests(unittest.TestCase):
    def test_connect_timeout_and_failure_close(self):
        sock=Mock();factory=Mock(return_value=sock)
        self.assertIs(connect('00:11:22:33:44:55',1,factory),sock)
        sock.connect.assert_called_once_with(('00:11:22:33:44:55',1))
        self.assertEqual(sock.settimeout.call_args_list[0].args,(30,))
        self.assertEqual(sock.settimeout.call_args_list[1].args,(15,))
        sock.connect.side_effect=TimeoutError('offline')
        with self.assertRaises(TimeoutError):connect('00:11:22:33:44:55',1,factory)
        sock.close.assert_called_once()
    def test_invalid_configuration_never_opens_socket(self):
        factory=Mock()
        for address,channel in [('',1),('00:11:22:33:44:55',0),('00:11:22:33:44:55',31)]:
            with self.assertRaises(ValueError):connect(address,channel,factory)
        factory.assert_not_called()
    def test_bidirectional_bytes_and_clean_close(self):
        received=threading.Event()
        class Output(io.StringIO):
            def write(self,value):
                result=super().write(value)
                if value.startswith('DATA '):received.set()
                return result
        class Input(io.StringIO):
            def readline(self,size=-1):
                value=super().readline(size)
                if value=='CLOSE\n' and not received.wait(2):raise TimeoutError('Missing received bytes')
                return value
        left,right=socket.socketpair();output=Output();source=Input('00017eff\nCLOSE\n')
        right.sendall(bytes([0,126,255]));serve(left,source,output)
        self.assertEqual(right.recv(10),bytes([0,1,126,255]));right.close()
        lines=output.getvalue().splitlines();self.assertEqual(lines[0],'READY');self.assertIn('SENT',lines)
        self.assertIn('DATA 007eff',lines);self.assertEqual(left.fileno(),-1)
    def test_invalid_or_failed_write_has_no_success_ack(self):
        for value in ['zz\n','00'*1046+'\n','0\n']:
            sock=Mock();sock.recv.return_value=b'';out=io.StringIO()
            with self.assertRaises(ValueError):serve(sock,io.StringIO(value),out)
            sock.sendall.assert_not_called();self.assertNotIn('SENT',out.getvalue());sock.close.assert_called_once()
        sock=Mock();sock.recv.return_value=b'';sock.sendall.side_effect=OSError('lost');out=io.StringIO()
        with self.assertRaises(OSError):serve(sock,io.StringIO('abcd\n'),out)
        self.assertNotIn('SENT',out.getvalue());sock.sendall.assert_called_once()
    def test_transport_platform_selection(self):
        with patch.object(host.sys,'platform','win32'):
            self.assertEqual(host.transport_command('helper.py'),[sys.executable,'-u','helper.py'])
        with patch.object(host.sys,'platform','darwin'):
            self.assertEqual(host.transport_command('/helper'),['/helper'])

class LockTests(unittest.TestCase):
    def test_lock_release_in_another_process(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'lock';held=host.open_lock(path);host.lock_exclusive(held)
            source="from pathlib import Path; from printing.platform import open_lock,lock_exclusive; import sys; h=open_lock(Path(sys.argv[1])); lock_exclusive(h); print('LOCKED')"
            blocked=subprocess.run([sys.executable,'-c',source,str(path)],capture_output=True,text=True)
            self.assertNotEqual(blocked.returncode,0);held.close()
            released=subprocess.run([sys.executable,'-c',source,str(path)],capture_output=True,text=True)
            self.assertEqual(released.returncode,0,released.stderr);self.assertIn('LOCKED',released.stdout)
    def test_windows_lock_conflict_is_normalized(self):
        crt=Mock();crt.LK_NBLCK=2;crt.locking.side_effect=PermissionError(errno.EACCES,'busy');handle=Mock()
        with patch.dict(sys.modules,msvcrt=crt),patch.object(host.sys,'platform','win32'):
            with self.assertRaises(BlockingIOError):host.lock_exclusive(handle)
        handle.seek.assert_called_once_with(0)

class EntryTests(unittest.TestCase):
    def test_simulation_defaults_and_lan_requirements(self):
        args=arguments(['--simulate']);self.assertEqual(args.entry,'both');self.assertEqual(args.hostname,'localhost')
        with self.assertRaises(SystemExit):arguments(['--simulate','--announce'])
        with self.assertRaises(SystemExit):arguments(['--simulate','--lan'])
        with self.assertRaises(SystemExit):arguments(['--simulate','--web-port','8636'])
    def test_simulated_queue_has_no_transport(self):
        with tempfile.TemporaryDirectory() as tmp:
            core=PrintService(tmp,True)
            self.assertIsNone(core.device_printer)
            with self.assertRaises(RuntimeError):PrintService(tmp,True)
            for lock in core._locks:lock.close()

class ImageTests(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec('pi_heif'), 'Windows HEIC dependency not installed')
    def test_synthetic_heic_decode(self):
        from printing.images import decode
        data=(Path(__file__).parent/'fixtures/airprint/synthetic.heic').read_bytes()
        with patch('printing.images.sys.platform','win32'):
            image=decode(data)
        self.assertEqual(image.size,(96,64))
        red=image.getpixel((20,15));blue=image.getpixel((20,48))
        self.assertGreater(red[0],200);self.assertLess(red[2],40)
        self.assertGreater(blue[2],200);self.assertLess(blue[0],40)

if __name__=='__main__':unittest.main()
