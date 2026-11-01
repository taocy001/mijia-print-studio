import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"web"))
"""Offline tests for the Bluetooth wire protocol; never contact a printer."""
import json
import queue
import struct
import unittest
from unittest.mock import patch
from bluetooth_client import BluetoothClient, crypt, frame


class BluetoothTests(unittest.TestCase):
    def client(self):
        p = BluetoothClient('00:00:00:00:00:00', '/unused')
        p.buffer = bytearray()
        p.lines = queue.Queue()
        p.seq = 4
        p.key = b'0123456789ABCDEF'
        return p

    def test_frame_and_checksum(self):
        raw = frame(3, 6, 3, 4, b'hello')
        self.assertEqual(raw[:3], b'\x7e\x64\0')
        self.assertEqual(raw[-2], sum(raw[1:-2]) % 256)
        self.assertEqual(raw[-1], 126)

    def test_frame_too_large(self):
        with self.assertRaises(ValueError): frame(3, 6, 3, 4, bytes(1024))

    def test_fragmented_receive(self):
        p = self.client()
        raw = frame(3, 7, 3, 4, b'answer')
        for part in (raw[:2], raw[2:21], raw[21:]):
            p.lines.put('DATA ' + part.hex())
        self.assertEqual(p.receive(3, 7), b'answer')

    def test_bad_checksum(self):
        p = self.client()
        raw = bytearray(frame(3, 7, 3, 4, b'answer'))
        raw[-2] ^= 1
        p.buffer = raw
        with self.assertRaisesRegex(ValueError, 'checksum'): p.receive(3, 7)

    def test_multi_part_rpc_rejected(self):
        p = self.client()
        p.buffer.extend(frame(3, 7, 3, 4, b'answer', 2, 1))
        with self.assertRaisesRegex(ValueError, 'segmented'): p.receive(3, 7)

    def test_upload_boundaries(self):
        p = self.client()
        sent = []
        p.send = sent.append
        data = bytes(range(256)) * 8
        with patch('bluetooth_client.time.sleep'): p.upload(42, data)
        self.assertEqual(len(sent), 3)
        chunks = []
        for index, raw in enumerate(sent, 1):
            self.assertEqual(struct.unpack('<HH', raw[14:18]), (3, index))
            plain = crypt(p.key, raw[20:-2], False)
            self.assertEqual(struct.unpack('<I', plain[:4])[0], 42)
            count = min(988, len(data) - len(chunks)*988)
            chunks.append(plain[4:4+count])
        self.assertEqual(b''.join(chunks), data)

    def test_rpc_matches_id(self):
        p = self.client()
        p.send = lambda raw: None
        p.receive = lambda ch, op: crypt(p.key, json.dumps({'id': 99, 'result': {}}).encode())
        with self.assertRaisesRegex(ValueError, 'mismatched'): p.rpc('get_prop', [])

    def test_failed_upload_not_retried(self):
        p = self.client()
        attempts = []
        def fail(raw):
            attempts.append(raw)
            raise IOError('disconnected')
        p.send = fail
        with self.assertRaises(IOError): p.upload(42, b'photo')
        self.assertEqual(len(attempts), 1)

    def test_address_and_channel_validation(self):
        with self.assertRaises(ValueError): BluetoothClient('', '/unused')
        with self.assertRaises(ValueError): BluetoothClient('00:00:00:00:00:00', '/unused', 31)

import io
import tempfile
from pathlib import Path
from PIL import Image
from bluetooth_printer import BluetoothPrinter


class WebBluetoothTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.printer = object.__new__(BluetoothPrinter)
        self.printer.intent = Path(self.tmp.name) / 'intent.json'
        self.calls = []
        self.printer.client = self
        self.state = 9
        self.fail_upload = False
        out = io.BytesIO()
        Image.new('RGB', (1216, 1824), 'gray').save(out, 'JPEG')
        self.photo = out.getvalue()

    def rpc(self, method, params):
        self.calls.append((method, params))
        if method == 'get_prop': return ['::0', {'media-size': 5012}]
        if method == 'get-job-id-list': return {'job-id-list': ''}
        if method == 'print-job': return {'job-id': 42}
        if method == 'get-job-info': return [{'job-id': 42, 'job-state': self.state}]
        raise AssertionError(method)

    def upload(self, job, data, progress=None):
        self.assertEqual(job, 42)
        if self.fail_upload: raise IOError('disconnected')
        if progress:progress(len(data),len(data))

    def test_live_progress_is_separate_from_lifecycle(self):
        states=[];samples=[]
        self.assertTrue(self.printer.print_photo([self.photo],log=lambda _:None,on_state=states.append,on_progress=samples.append))
        self.assertEqual([s['phase'] for s in states],['creating','uploading','done'])
        self.assertEqual(samples[0]['stage'],'transfer')
        self.assertEqual(samples[0]['sentBytes'],samples[0]['totalBytes'])
        self.assertEqual(samples[-1]['device']['job-state'],9)
        self.assertNotIn('phase',samples[-1])
        self.assertEqual(sum(method=='print-job' for method,_ in self.calls),1)

    def test_completed_job_clears_intent(self):
        self.assertTrue(self.printer.print_photo([self.photo], log=lambda _: None))
        self.assertFalse(self.printer.intent.exists())
        create = next(params for method, params in self.calls if method == 'print-job')
        self.assertEqual(create['channel'], 576)

    def test_disconnected_job_blocks_next_print(self):
        self.fail_upload = True
        with self.assertRaises(IOError): self.printer.print_photo([self.photo])
        self.assertTrue(self.printer.intent.exists())
        with self.assertRaises(RuntimeError): self.printer.print_photo([self.photo])
        self.assertEqual(len([c for c in self.calls if c[0] == 'print-job']), 1)

    def test_canceled_is_not_success(self):
        self.state = 7
        self.assertFalse(self.printer.print_photo([self.photo], log=lambda _: None))

    def test_cancel_does_not_create_another_job(self):
        original=self.rpc
        def rpc(method,params):
            if method=='cancel-job':
                self.calls.append((method,params));self.state=8;return {}
            return original(method,params)
        self.rpc=rpc
        self.assertFalse(self.printer.print_photo([self.photo],log=lambda _:None,on_cancel=lambda:True))
        self.assertEqual(sum(m=='print-job' for m,_ in self.calls),1)
        self.assertEqual(sum(m=='cancel-job' for m,_ in self.calls),1)
        self.assertFalse(self.printer.intent.exists())

    def test_reject_texture_before_creation(self):
        with self.assertRaises(ValueError): self.printer.print_photo([b'coat', self.photo])
        self.assertEqual(self.calls, [])

    def test_aborted_transfer_retains_safe_diagnostics(self):
        original=self.rpc;states=[]
        def rpc(method,params):
            if method=='get-job-info':return [{'job-id':42,'job-state':7,'transfer-status':3,'file-size':367542,'transfer-size':367541,'print-page':0,'print-time':0,'file':'private photo','person':'private'}]
            return original(method,params)
        self.rpc=rpc
        self.assertFalse(self.printer.print_photo([self.photo],log=lambda _:None,on_state=states.append))
        self.assertEqual(self.printer.last_state,7);self.assertEqual(self.printer.last_info['transfer-size'],367541)
        self.assertNotIn('file',self.printer.last_info);self.assertNotIn('person',self.printer.last_info)
        self.assertEqual(states[-1]['phase'],'aborted');self.assertIn('缺少 1 字节',states[-1]['message'])
        self.assertFalse(self.printer.intent.exists())
        from bluetooth_printer import terminal_message
        self.assertEqual(terminal_message({**self.printer.last_info,'job-state':9}),'打印完成')
        self.assertEqual(terminal_message({**self.printer.last_info,'job-state':8}),'任务已取消')

class MediaValidationTests(unittest.TestCase):
 def test_unsupported_paper_is_reported_before_mask_or_device_commands(self):
  printer=object.__new__(BluetoothPrinter)
  with self.assertRaisesRegex(ValueError,'当前检测到纸型 9999'):
   printer.print_photo([b'invalid mask',b'invalid image'],media_size=9999)
 def test_bad_copies_does_not_report_wrong_paper(self):
  printer=object.__new__(BluetoothPrinter)
  with self.assertRaisesRegex(ValueError,'份数'):
   printer.print_photo([b'image'],copies=0)

class SquareBluetoothTests(WebBluetoothTests):
    def setUp(self):
        super().setUp()
        out = io.BytesIO()
        Image.new('RGB', (1040, 1040), 'red').save(out, 'JPEG')
        self.square = out.getvalue()
        self.uploaded = []

    def test_square_with_hidden_coat(self):
        import struct, zlib
        self.printer.get_prop = lambda *args: ['::0', {'media-size': 5009}]
        self.printer.client.upload = lambda job, data: self.uploaded.append(data)
        encoder = zlib.compressobj(wbits=-15)
        packed = encoder.compress(bytes(1040*1040)) + encoder.flush()
        coat = b'ocpattern1\0\0' + struct.pack('>IIII',1040,1040,len(packed),1) + bytes(4) + packed
        self.assertTrue(self.printer.print_photo([coat,self.square], media_size=5009, log=lambda _:None))
        create = next(p for m,p in self.calls if m=='print-job')
        self.assertEqual(create['media-size'],5009)
        self.assertEqual(create['file-size'],len(coat)+len(self.square))
        self.assertEqual(self.uploaded,[coat+self.square])

    def test_square_rejects_six_inch_image(self):
        with self.assertRaisesRegex(ValueError,'1040'):
            self.printer.print_photo([self.photo],media_size=5009)
        self.assertEqual(self.calls,[])

    def test_square_rejects_wrong_tray(self):
        with self.assertRaises(RuntimeError):
            self.printer.print_photo([self.square],media_size=5009)
        self.assertFalse(self.printer.intent.exists())
        self.assertFalse(any(m=='print-job' for m,p in self.calls))

class CombinedStreamTests(unittest.TestCase):
    """Model final-fragment zero unpadding; full fragments remain binary intact."""
    def wire(self,parts):
        client=BluetoothTests().client();frames=[];client.send=frames.append
        with patch('bluetooth_client.time.sleep'):
            for part in parts:client.upload(42,part)
        received=[]
        for frame_data in frames:
            total,number=struct.unpack('<HH',frame_data[14:18]);plain=crypt(client.key,frame_data[20:-2],False)
            self.assertEqual(struct.unpack('<I',plain[:4])[0],42)
            payload=plain[4:]
            if number==total:payload=payload.rstrip(b'\0')
            received.append(payload)
        return b''.join(received),frames
    def coat(self):
        import random,zlib
        for seed in range(40):
            rng=random.Random(seed);raw=bytes(255 if rng.random()>.8 else 0 for _ in range(4000))+bytes(1040*1040-4000)
            encoder=zlib.compressobj(6,zlib.DEFLATED,-15);packed=encoder.compress(raw)+encoder.flush()
            if packed.endswith(b'\0'):break
        self.assertTrue(packed.endswith(b'\0'))
        return b'ocpattern1\0\0'+struct.pack('>IIIIBBH',1040,1040,len(packed),1,183,103,0)+packed,raw
    def test_final_fragment_model_reproduces_loss_and_preserves_combined_stream(self):
        import zlib
        coat,raw=self.coat();photo=io.BytesIO();Image.new('RGB',(1040,1040),'red').save(photo,'JPEG');jpeg=photo.getvalue()
        legacy,_=self.wire([coat,jpeg]);self.assertEqual(len(legacy),len(coat)+len(jpeg)-(len(coat)-len(coat.rstrip(b'\0'))))
        received,frames=self.wire([coat+jpeg]);self.assertEqual(received,coat+jpeg)
        self.assertEqual([struct.unpack('<HH',f[14:18]) for f in frames],[(len(frames),i+1) for i in range(len(frames))])
        self.assertEqual(zlib.decompress(received[32:len(coat)],-15),raw)
        self.assertEqual(received[len(coat):],jpeg)
    def test_combined_stream_over_one_megabyte_preserves_full_chunk_zero_tails(self):
        data=(b'abcd'+bytes(984))*1100+b'\xff\xd9'
        self.assertGreater(len(data),1048576)
        received,_=self.wire([data]);self.assertEqual(received,data)
        client=BluetoothTests().client();client.send=lambda _:self.fail('must reject before sending')
        with self.assertRaises(ValueError):client.upload(42,bytes(2097153))
