"""Synthetic offline fixtures; never initialize a transport or printer."""
import importlib.util
import io
import struct
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject,NameObject
from airprint import documents
from airprint import windows_documents as windows
from airprint.offline import Unsupported,compose_splice

FIXTURES=Path(__file__).parent/'fixtures/airprint'


def pdf(colors=('1 0 0',),width=288,height=216):
    writer=PdfWriter()
    for color in colors:
        page=writer.add_blank_page(width=width,height=height)
        stream=DecodedStreamObject();stream.set_data(f'{color} rg 0 0 {width} {height} re f'.encode())
        page[NameObject('/Contents')]=writer._add_object(stream)
    output=io.BytesIO();writer.write(output);return output.getvalue()


def urf(width,height,channels=3):
    header=bytearray(44);header[:8]=b'UNIRAST\0';struct.pack_into('>I',header,8,1);header[12]=channels*8;header[13]=1 if channels==3 else 0
    struct.pack_into('>II',header,24,width,height);return bytes(header)


class RasterTests(unittest.TestCase):
    def test_real_cups_fixtures(self):
        for extension,mime in (('urf','image/urf'),('pwg','image/pwg-raster')):
            for name,size in (('one-page',(1200,1800)),('landscape',(1800,1200))):
                image=windows.raster_image((FIXTURES/f'{name}.{extension}').read_bytes(),mime)
                self.assertEqual(image.size,size);self.assertEqual(image.getpixel((0,0)),(255,0,0));self.assertEqual(image.getpixel((size[0]-1,size[1]-1)),(0,0,255))
            with self.assertRaises(Unsupported):windows.raster_image((FIXTURES/f'two-pages.{extension}').read_bytes(),mime)
    def test_literal_repeated_rows_gray_and_white_fill(self):
        image=windows.raster_image(urf(3,2)+bytes([1,254,255,0,0,0,255,0,0,0,255]),'image/urf')
        self.assertEqual(list(image.getdata()),[(255,0,0),(0,255,0),(0,0,255)]*2)
        gray=windows.raster_image(urf(4,1,1)+bytes([0,1,42,128]),'image/urf')
        self.assertEqual(list(gray.getdata()),[(42,42,42)]*2+[(255,255,255)]*2)
    def test_dimensions_truncation_and_bad_runs_are_rejected(self):
        for data in (urf(10001,1),urf(5000,5000),urf(0,1),urf(1,1)+b'\x01\x80',urf(1,1)+b'\x00\x01\x00\x00\x00',urf(2,1)+b'\x00\xff\x01',urf(1,1)+b'\x00\x80extra',b'UNIRAST'):
            with self.subTest(size=len(data)),self.assertRaises(Unsupported):windows.raster_image(data,'image/urf')
        with patch.object(windows,'MAX_INPUT',10),self.assertRaises(Unsupported):windows.raster_image(urf(1,1),'image/urf')
    def test_unsupported_pwg_header_is_rejected(self):
        original=(FIXTURES/'one-page.pwg').read_bytes()
        for offset,value in ((388,16),(392,32),(396,1),(400,1),(404,6),(276,1)):
            data=bytearray(original);struct.pack_into('>I',data,offset,value)
            with self.subTest(offset=offset),self.assertRaises(Unsupported):windows.raster_image(bytes(data),'image/pwg-raster')
    def test_windows_dispatch_never_loads_mac_library(self):
        data=(FIXTURES/'one-page.urf').read_bytes()
        with patch.object(documents.sys,'platform','win32'),patch.object(documents,'_render_lib',side_effect=AssertionError('Mac renderer called')):
            result=documents.prepare_document(data,'image/urf')
        self.assertEqual(result.size,(1216,1824))
    @unittest.skipUnless(sys.platform=='darwin' and Path('build/libmijia_render.dylib').exists(),'Mac comparison fixture')
    def test_raster_matches_existing_native_decoder(self):
        for extension,mime in (('urf','image/urf'),('pwg','image/pwg-raster')):
            data=(FIXTURES/f'one-page.{extension}').read_bytes();rgb,w,h=documents._native_render(documents._render_lib(),data,mime)
            self.assertEqual(windows.raster_image(data,mime).tobytes(),rgb)


@unittest.skipUnless(importlib.util.find_spec('pypdfium2'),'Optional Windows PDFium dependency not installed')
class PdfTests(unittest.TestCase):
    def test_real_pdfium_page_order_and_splice(self):
        images=windows.pdf_page_images(pdf(('1 0 0','0 0 1')),6)
        self.assertEqual([im.size for im in images],[(2400,1800)]*2)
        self.assertFalse(any(im.info['studio_photo'] for im in images))
        result=compose_splice(images,scaling='fill');image=Image.open(io.BytesIO(result.jpeg))
        self.assertEqual(image.size,(1216,1824));self.assertGreater(image.getpixel((608,456))[0],240);self.assertGreater(image.getpixel((608,1368))[2],240)
    def test_six_pages_and_invalid_documents(self):
        self.assertEqual(len(windows.pdf_page_images(pdf(('0 1 0',)*6),6)),6)
        for data,limit in ((pdf(('0 0 0',)*7),6),(pdf(('0 0 0',)*2),1),(b'not pdf',6),(pdf(width=14401),6)):
            with self.assertRaises(Unsupported):windows.pdf_page_images(data,limit)
        with self.assertRaises(Unsupported):windows.pdf_page_images(pdf(),7)
    def test_document_lifetime_and_serialized_rendering(self):
        with ThreadPoolExecutor(2) as pool:
            images=list(pool.map(lambda _:windows.pdf_page_images(pdf(),1)[0],range(2)))
        for image in images:self.assertEqual(image.getpixel((100,100)),(255,0,0))
    def test_win32_route_keeps_pdf_document_fit(self):
        import pypdfium2
        with patch.object(documents.sys,'platform','win32'),patch.object(documents,'_render_lib',side_effect=AssertionError('Mac renderer called')):
            images=documents.pdf_page_images(pdf(('1 0 0','0 0 1')),6)
            result=documents.prepare_document(pdf(), 'application/pdf',scaling='fill')
        self.assertEqual(len(images),2);image=Image.open(io.BytesIO(result.jpeg));self.assertEqual(result.size,(1216,1824))
        self.assertEqual(image.getpixel((0,0)),(255,255,255))
    def test_mac_dispatch_remains_native(self):
        with patch.object(documents.sys,'platform','darwin'),patch.object(documents,'_render_lib',side_effect=RuntimeError('native branch')):
            with self.assertRaisesRegex(RuntimeError,'native branch'):documents.pdf_page_images(pdf())
            with self.assertRaisesRegex(RuntimeError,'native branch'):documents.prepare_document(pdf(),'application/pdf')

if __name__=='__main__':unittest.main()
