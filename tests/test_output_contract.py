"""Synthetic output contracts; no service, transport or printer is started."""
import base64
import io
import json
from pathlib import Path
import struct
import subprocess
import sys
import unittest
import zlib
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from printing.images import page_files

ROOT = Path(__file__).resolve().parents[1]
COLORS = [(220, 40, 50), (30, 180, 70), (40, 70, 220), (235, 190, 30)]


def chart(size):
    image = Image.new('RGB', size)
    draw = ImageDraw.Draw(image)
    w, h = size
    for color, box in zip(COLORS, [(0, 0, w//2-1, h//2-1), (w//2, 0, w-1, h//2-1),
                                   (0, h//2, w//2-1, h-1), (w//2, h//2, w-1, h-1)]):
        draw.rectangle(box, fill=color)
    return image


def encoded(image, fmt='JPEG'):
    out = io.BytesIO()
    image.save(out, fmt)
    return out.getvalue()


def decoded(value):
    return Image.open(io.BytesIO(base64.b64decode(value))).convert('RGB')


def quadrants(test, image, order):
    w, h = image.size
    for (x, y), index in zip([(w//4, h//4), (3*w//4, h//4), (w//4, 3*h//4), (3*w//4, 3*h//4)], order):
        actual = image.getpixel((x, y))
        test.assertLessEqual(max(abs(a-b) for a, b in zip(actual, COLORS[index])), 12, (actual, COLORS[index]))


class OutputContract(unittest.TestCase):
    def test_web_payload_is_lossless_and_mask_uses_red_threshold(self):
        for media, size in [(5009, (1040, 1040)), (5012, (1216, 1824)), (5014, (1216, 1824))]:
            jpeg = encoded(chart(size))
            # Green/blue must not affect the red-channel threshold of 100.
            row = [(99, 255, 255), (100, 0, 0), (101, 0, 0), (0, 255, 255)]
            mask = Image.new('RGB', size)
            mask.putdata((row * ((size[0]*size[1]+3)//4))[:size[0]*size[1]])
            expected = bytes([0, 255, 255, 0]) * (size[0]*size[1]//4)
            for threshold in [60, 100, 140]:
                with self.subTest(media=media, threshold=threshold):
                    page = dict(media=media, base64=base64.b64encode(jpeg).decode(),
                                ocMask=base64.b64encode(encoded(mask, 'PNG')).decode(), threshold=threshold)
                    actual, coat = page_files(page)
                    self.assertEqual(actual, jpeg)
                    self.assertEqual(coat[:12], b'ocpattern1\0\0')
                    self.assertEqual(struct.unpack('>IIIIBBH', coat[12:32]), (*size, len(coat)-32, 1, threshold+60, threshold-20, 0))
                    self.assertEqual(zlib.decompress(coat[32:], -15), expected)
            self.assertEqual(page_files(dict(media=media, base64=page['base64'])), (jpeg, None))

    def worker_pages(self, data, media, mime='image/jpeg', **options):
        args = dict(media=media, mime=mime, scaling='fill', **options)
        result = subprocess.run([sys.executable, str(ROOT/'airprint/render_worker.py')],
                                input=json.dumps(args).encode()+b'\n'+data,
                                capture_output=True, check=True, timeout=35)
        pages = json.loads(result.stdout)
        self.assertTrue(all(p['media']==media for p in pages))
        return [decoded(p['base64']) for p in pages]

    def worker(self, size, media, **options):
        images = self.worker_pages(encoded(chart(size)), media, **options)
        self.assertEqual(len(images), 1)
        return images[0]

    def test_airprint_worker_orientation_and_square_compensation(self):
        for size, media, orientation, order in [((600, 900), 5012, 3, [0, 1, 2, 3]),
                ((900, 600), 5012, 4, [1, 3, 0, 2]), ((600, 600), 5009, 3, [3, 2, 1, 0])]:
            with self.subTest(media=media, orientation=orientation):
                image = self.worker(size, media, orientation=orientation)
                self.assertEqual(image.size, (1040, 1040) if media==5009 else (1216, 1824))
                quadrants(self, image, order)

    def test_airprint_single_photo_splice_duplicates_without_turning(self):
        image = self.worker((800, 600), 5014)
        self.assertEqual(image.size, (1216, 1824))
        for top in [0, 912]:
            quadrants(self, image.crop((0, top, 1216, top+912)), [0, 1, 2, 3])

    @unittest.skipUnless(sys.platform=='win32' or (sys.platform=='darwin' and (ROOT/'build/libmijia_render.dylib').is_file()), 'Native PDF renderer required')
    def test_airprint_pdf_page_order_fit_and_odd_splice(self):
        from pypdf import PdfWriter
        from pypdf.generic import DecodedStreamObject, NameObject
        writer = PdfWriter()
        for color in ['1 0 0', '0 1 0', '0 0 1']:
            page = writer.add_blank_page(width=288, height=216)
            stream = DecodedStreamObject()
            stream.set_data(f'{color} rg 0 0 288 216 re f'.encode())
            page[NameObject('/Contents')] = writer._add_object(stream)
        buffer = io.BytesIO()
        writer.write(buffer)
        for media, centers in [(5012, [[(255,0,0)],[(0,255,0)],[(0,0,255)]]),
                               (5014, [[(255,0,0),(0,255,0)],[(0,0,255),(0,0,255)]])]:
            with self.subTest(media=media):
                images = self.worker_pages(buffer.getvalue(), media, 'application/pdf', orientation=3)
                self.assertEqual(len(images), len(centers))
                for image, colors in zip(images, centers):
                    self.assertEqual(image.size, (1216,1824))
                    for y, expected in zip([912] if media==5012 else [456,1368], colors):
                        self.assertLessEqual(max(abs(a-b) for a,b in zip(image.getpixel((608,y)),expected)),12)
                    if media==5012:
                        self.assertEqual(image.getpixel((608,30)), (255,255,255), 'PDF must fit, not crop')


if __name__ == '__main__':
    unittest.main()
