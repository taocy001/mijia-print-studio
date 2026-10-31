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

    def upload(self, job, data):
        self.assertEqual(job, 42)
        if self.fail_upload: raise IOError('disconnected')

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
        self.assertEqual(self.uploaded,[coat,self.square])

    def test_square_rejects_six_inch_image(self):
        with self.assertRaisesRegex(ValueError,'1040'):
            self.printer.print_photo([self.photo],media_size=5009)
        self.assertEqual(self.calls,[])

    def test_square_rejects_wrong_tray(self):
        with self.assertRaises(RuntimeError):
            self.printer.print_photo([self.square],media_size=5009)
        self.assertFalse(self.printer.intent.exists())
        self.assertFalse(any(m=='print-job' for m,p in self.calls))
