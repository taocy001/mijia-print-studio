import json,unittest
from unittest.mock import patch
from printing.errors import CATALOG,code,describe,rewrite,PrinterResponseError
from printing.bluetooth_client import BluetoothClient,crypt
from printing.bluetooth_printer import terminal_message
class Errors(unittest.TestCase):
 def test_official_catalog_complete(self):
  expected='SYSTEM_OTHER JOB_OTHER 8004 8005 8006 8007 8008 8009 8011 8013 8208 8209 8210 5304 5306 5402 5403 5414 5416 8101 8102 8103 8104 8199 9006 9007 9008 9009'.split()
  self.assertEqual(set(CATALOG),set(expected))
  for c in expected:
   self.assertIn('（'+c+'）',code(c));self.assertTrue(CATALOG[c]['action']);self.assertTrue(CATALOG[c]['name'])
 def test_supply_is_not_paper_or_ribbon(self):
  text=describe('::9008');self.assertIn('Type-C 供电不足',text);self.assertNotIn('缺纸',text);self.assertNotIn('色带耗尽',text)
 def test_multiple_codes_and_no_alarm(self):
  self.assertEqual(describe('::0'),'');self.assertEqual(describe(None),'');self.assertEqual(describe('::5402%9008:5402'),code('5402')+'；'+code('9008'))
 def test_unknown_safe_and_honest(self):
  self.assertIn('未识别',code('9999'));self.assertIn('9999',code('9999'));self.assertNotIn('<',code('<script>'))
 def test_historical_failures_are_explained(self):
  self.assertIn('Type-C 供电不足',rewrite('打印机告警（9008)。照片尚未提交'))
  self.assertIn('正忙',rewrite('打印机拒绝任务：8011'))
  self.assertEqual(rewrite('打印完成'),'打印完成')
 def test_rpc_error_retains_code(self):
  p=object.__new__(BluetoothClient);p.seq=4;p.key=b'0123456789ABCDEF'
  with patch.object(p,'send'),patch.object(p,'receive',return_value=crypt(p.key,json.dumps({'id':4,'error':{'code':8011}}).encode())):
   with self.assertRaises(PrinterResponseError) as err:p.rpc('get_prop',[])
  self.assertEqual(err.exception.code,8011);self.assertIn('正忙',str(err.exception))
 def test_terminal_code_explained(self):
  self.assertIn('供电不足',terminal_message({'job-state':7,'error-code':9008}))
if __name__=='__main__':unittest.main()

class ApiErrors(unittest.IsolatedAsyncioTestCase):
 async def test_api_retains_printer_error(self):
  from web.serve import responses
  async def handler(request):raise PrinterResponseError(9008)
  response=await responses(None,handler)
  self.assertEqual(response.status,409);self.assertIn('Type-C 供电不足',json.loads(response.text)['error'])
