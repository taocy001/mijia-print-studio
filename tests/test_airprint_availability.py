"""No Bluetooth or printing: capabilities must follow measured availability."""
import tempfile,time,unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from printing.service import PrintService
from airprint.adapter import AirPrint
from airprint.capabilities import integer
from airprint.offline import Message,encode_ipp,decode_ipp
class Availability(unittest.IsolatedAsyncioTestCase):
 async def asyncSetUp(self):
  self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
  self.core=PrintService(self.folder.name,True);await self.core.start(None);self.addAsyncCleanup(self.core.stop,None)
  self.ipp=AirPrint(self.core,'ipp://localhost:8636/ipp/print')
 def attrs(self):
  values={}
  for a in self.ipp.printer_attributes():values.setdefault(a.name,[]).append(a.value)
  return values
 def device(self,media=5009):self.core.device={'connected':True,'media':media,'checkedAt':int(time.time()*1000),'alert':'::0','state':'30','ribbon':10}
 def unavailable(self):
  self.assertEqual(self.attrs()['printer-is-accepting-jobs'],[b'\x00'])
  self.assertNotIn('media-ready',self.attrs())
 async def test_unknown_and_released_do_not_guess_six_inch(self):
  for device in ({},{'connected':False,'media':5009},{'connected':True,'media':0}):
   self.core.device=device;self.unavailable()
   for key in ('media-default','media-supported','media-col-default','media-col-database'):self.assertNotIn(key,self.attrs())
  self.device();await self.core.release();self.unavailable();self.assertNotIn('media-default',self.attrs())
 async def test_stale_status_and_alerts_reject_new_jobs(self):
  self.device();self.core.simulate=False;self.core.device['checkedAt']-=151000;self.unavailable()
  self.assertNotIn('media-default',self.attrs())
  response=decode_ipp(await self.ipp.handle(encode_ipp(Message((2,0),4,1,())), 'test'))
  self.assertEqual(response.code,0x507);self.assertEqual(self.core.jobs,[])
  self.device();self.core.device['alert']='::5402';self.unavailable()
  self.core.device['alert']='::0';self.core.device['ribbon']=0;self.unavailable()
 async def test_recovery_paper_and_splice_formats(self):
  self.device();self.assertEqual(self.attrs()['media-ready'],[b'custom_square_3x3in'])
  self.device(5012);self.core.airprint_splice=True
  self.assertEqual(self.attrs()['media-ready'],[b'na_index-4x6_4x6in'])
  self.assertEqual(set(self.attrs()['document-format-supported']),{b'image/jpeg',b'application/pdf'})
  self.core.paused=True;self.unavailable();self.core.paused=False
  self.assertEqual(self.attrs()['printer-is-accepting-jobs'],[b'\x01'])
if __name__=='__main__':unittest.main()
