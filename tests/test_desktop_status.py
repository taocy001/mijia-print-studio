"""Read-only status recovery; no Bluetooth hardware."""
import asyncio,tempfile,threading,unittest,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from printing.service import PrintService
from printing.images import UserError
from airprint.adapter import AirPrint

class StatusTests(unittest.IsolatedAsyncioTestCase):
 async def asyncSetUp(self):
  self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
  self.core=PrintService(self.folder.name,True);await self.core.start(None);self.addAsyncCleanup(self.core.stop,None);self.core.simulate=False
 def printer(self):
  class Fake:
   def get_prop(self,*names):return ['30','::0',{'media-size':5009},{'ribbon-info':[1,0,-1]}]
   def close(self):pass
  return Fake()
 async def test_failure_clears_connected_and_next_check_recovers(self):
  self.core.device={'connected':True,'media':5012}
  with patch.object(self.core,'printer',side_effect=TimeoutError()):
   with self.assertRaises(UserError):await self.core.status()
  self.assertFalse(self.core.device['connected'])
  adapter=AirPrint(self.core,'ipp://localhost:1/ipp/print')
  self.assertFalse(any(a.name=='media-ready' for a in adapter.printer_attributes()))
  with patch.object(self.core,'printer',return_value=self.printer()):await self.core.status()
  self.assertTrue(self.core.device['connected']);self.assertEqual(self.core.device['media'],5009)
  self.assertEqual([a.value for a in adapter.printer_attributes() if a.name=='media-ready'],[b'custom_square_3x3in'])
 async def test_busy_device_is_not_probed(self):
  async with self.core.io_lock:
   with patch.object(self.core,'printer',side_effect=AssertionError('must not connect')):await self.core.status()
 async def test_cancel_waits_for_thread_before_releasing_device(self):
  entered=threading.Event();finish=threading.Event();printer=self.printer();original=printer.get_prop
  def read(*args):entered.set();finish.wait(3);return original(*args)
  printer.get_prop=read
  with patch.object(self.core,'printer',return_value=printer):
   task=asyncio.create_task(self.core.status())
   try:
    await asyncio.to_thread(entered.wait,1);task.cancel();await asyncio.sleep(.02)
    self.assertTrue(self.core.io_lock.locked());self.assertFalse(task.done())
   finally:finish.set()
   with self.assertRaises(asyncio.CancelledError):await task
   self.assertFalse(self.core.io_lock.locked())
 async def test_status_handshake_has_bounded_retry(self):
  from printing.bluetooth_printer import BluetoothPrinter
  with patch('printing.bluetooth_printer.BluetoothClient') as client:
   client.return_value.address='00:00:00:00:00:00'
   printer=BluetoothPrinter('00:00:00:00:00:00','unused',1,Path(self.folder.name),status_only=True)
   client.return_value.open.assert_called_once_with(lock_timeout=0,attempts=2);printer.close()
if __name__=='__main__':unittest.main()
