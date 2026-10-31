import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"web"))
"""Offline recovery and device-lock tests; never access a physical printer."""
import importlib.util
import os
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch,Mock
from bluetooth_client import BluetoothClient

ADDRESS='00:00:00:00:00:00'

class RecoveryTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.enterContext(patch('bluetooth_client.tempfile.gettempdir',return_value=self.tmp.name))
 def client(self):return BluetoothClient(ADDRESS,'/unused')
 def test_handshake_retry_keeps_lock_and_never_sends_rpc(self):
  p=self.client();other=self.client();attempts=[]
  def connect():
   with self.assertRaises(BlockingIOError):other.open(attempts=1)
   attempts.append(1)
   if len(attempts)==1:raise TimeoutError('hello')
   return p
  with patch.object(p,'connect',side_effect=connect),patch.object(p,'rpc',side_effect=AssertionError('no job')),patch('bluetooth_client.time.sleep'):
   try:self.assertIs(p.open(),p);self.assertEqual(len(attempts),2)
   finally:p.close()
  with patch.object(other,'connect',return_value=other):other.open();other.close()
 def test_recovery_is_bounded_and_invalid_handshake_not_retried(self):
  for error,count in [(TimeoutError('unavailable'),2),(ValueError('invalid DH'),1)]:
   p=self.client()
   with patch.object(p,'connect',side_effect=error) as connect,patch('bluetooth_client.time.sleep'):
    with self.assertRaises(type(error)):p.open()
    self.assertEqual(connect.call_count,count);self.assertIsNone(p.lock)
 def test_status_connection_can_disable_retry(self):
  p=self.client()
  with patch.object(p,'connect',side_effect=TimeoutError()) as connect:
   with self.assertRaises(TimeoutError):p.open(attempts=1)
   self.assertEqual(connect.call_count,1)
 def test_rpc_timeout_is_not_replayed_and_names_phase(self):
  p=self.client();p.seq=4;p.key=b'0123456789ABCDEF';p.buffer=bytearray();p.lines=queue.Queue()
  with patch.object(p,'send') as send,patch.object(p.lines,'get',side_effect=queue.Empty):
   with self.assertRaisesRegex(TimeoutError,'phase=rpc get_prop; channel=1'):p.rpc('get_prop',[])
   self.assertEqual(send.call_count,1)
 def test_separate_process_lock_and_crash_release(self):
  source="from bluetooth_client import BluetoothClient; import time; p=BluetoothClient('00:00:00:00:00:00','/unused'); p.connect=lambda:p; p.open(); print('LOCKED',flush=True); time.sleep(30)"
  child=subprocess.Popen([sys.executable,'-u','-c',source],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=dict(os.environ,TMPDIR=self.tmp.name,PYTHONPATH=str(Path(__file__).resolve().parents[1]/"web")),cwd=Path(__file__).parent)
  try:
   self.assertEqual(child.stdout.readline().strip(),'LOCKED')
   p=self.client()
   with patch.object(p,'connect',return_value=p) as connect:
    with self.assertRaises(BlockingIOError):p.open(lock_timeout=.1)
    connect.assert_not_called()
    child.kill();child.wait(timeout=5)
    p.open();p.close()
  finally:
   if child.poll() is None:child.kill();child.wait()
   child.stdout.close();child.stderr.close()
 def test_close_failure_releases_local_lock(self):
  first=self.client();second=self.client()
  with patch.object(first,'connect',return_value=first):first.open()
  with patch.object(first,'_close_transport',side_effect=OSError('helper cleanup')):
   with self.assertRaises(OSError):first.close()
  self.assertIsNone(first.lock)
  with patch.object(second,'connect',return_value=second):second.open();second.close()
 def test_cleanup_closes_both_streams_after_timeout_and_close_error(self):
  client=self.client();process=Mock();client.p=process;process.poll.return_value=None
  process.wait.side_effect=[subprocess.TimeoutExpired('helper',3),0];process.stdin.close.side_effect=OSError('pipe cleanup')
  with self.assertRaisesRegex(OSError,'pipe cleanup'):client.close()
  process.kill.assert_called_once();process.stdout.close.assert_called_once();self.assertIsNone(client.p)
 def test_context_cleanup_does_not_replace_operation_error(self):
  client=self.client()
  with patch.object(client,'close',side_effect=OSError('cleanup')):
   self.assertIsNone(client.__exit__(TimeoutError,TimeoutError('upload'),None))
 def test_open_failure_keeps_original_error_if_cleanup_also_fails(self):
  client=self.client()
  with patch.object(client,'connect',side_effect=ValueError('handshake')),patch.object(client,'_close_transport',side_effect=OSError('cleanup')):
   with self.assertRaisesRegex(ValueError,'handshake'):client.open()
  self.assertIsNone(client.lock)
 def test_address_separators_share_lock(self):
  a=self.client();b=BluetoothClient('00-00-00-00-00-00','/unused')
  with patch.object(a,'connect',return_value=a):a.open()
  try:
   with self.assertRaises(BlockingIOError):b.open()
  finally:a.close();b.close()

if __name__=='__main__':unittest.main()
