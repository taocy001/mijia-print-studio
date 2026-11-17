"""Automatic status reconciliation never uploads, recreates or resumes a print."""
import json
from unittest.mock import patch
from test_queue_recovery import Queue

class AutomaticRecovery(Queue):
 async def test_auto_last_page_unlocks_and_preserves_original_failure(self):
  self.job['pages']=self.job['pages'][:2];await self.run_job()
  failure=self.job['originalFailure'];await self.core.status()
  self.assertEqual(self.job['phase'],'done');self.assertFalse(self.core.paused)
  self.assertEqual(self.printer.calls,2);self.assertEqual(self.job['originalFailure'],failure)
  self.assertFalse(self.printer.intent.exists());self.assertTrue(self.core.device['connected'])
 async def test_auto_mid_batch_stops_remaining(self):
  await self.run_job();await self.core.status()
  self.assertEqual(self.job['phase'],'cancelled');self.assertEqual(self.job['completedPages'],2)
  self.assertNotIn('phase',self.job['pages'][2]);self.assertEqual(self.printer.calls,2)
 async def test_auto_nonterminal_or_missing_keeps_record(self):
  for result in [[{'job-id':2,'job-state':5}],[],[{'job-id':999,'job-state':9}],{'error-code':8005}]:
   with self.subTest(result=result):
    self.job.update(phase='uncertain',jobId=2,mayHavePrinted=True,message='original 5416');self.core.paused=True
    self.printer.intent.write_text('{"job":2}')
    with patch.object(self.printer,'rpc',return_value=result):await self.core.status()
    self.assertEqual(self.job['phase'],'uncertain');self.assertTrue(self.core.paused)
    self.assertEqual(self.job['message'],'original 5416');self.assertTrue(self.printer.intent.exists())
    self.assertTrue(self.core.device['connected']);self.assertEqual(self.printer.calls,0)
 async def test_auto_no_id_and_intent_conflict_never_queries(self):
  self.job.update(phase='uncertain',mayHavePrinted=True);self.core.paused=True
  with patch.object(self.printer,'rpc') as rpc:await self.core.status();rpc.assert_not_called()
  self.job['jobId']=2;self.printer.intent.write_text('{"job":3}')
  with patch.object(self.printer,'rpc') as rpc:await self.core.status();rpc.assert_not_called()
  self.assertTrue(self.core.paused)
 async def test_auto_terminal_cancel_or_abort_unlocks(self):
  for state,phase in [(7,'aborted'),(8,'cancelled')]:
   self.job.update(phase='uncertain',jobId=2,mayHavePrinted=True);self.core.paused=True
   self.printer.intent.write_text('{"job":2}')
   with patch.object(self.printer,'rpc',return_value=[{'job-id':2,'job-state':state}]):await self.core.status()
   self.assertEqual(self.job['phase'],phase);self.assertFalse(self.core.paused);self.assertEqual(self.printer.calls,0)
 async def test_auto_released_or_busy_does_not_probe(self):
  self.job.update(phase='uncertain',jobId=2);self.core.released=True
  with patch.object(self.printer,'rpc') as rpc:await self.core.status();rpc.assert_not_called()
  self.core.released=False
  async with self.core.io_lock:
   with patch.object(self.printer,'rpc') as rpc:await self.core.status();rpc.assert_not_called()
