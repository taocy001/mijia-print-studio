"""Face detection, crop geometry and document boundaries; no printer access."""
import io
import math
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image
from printing.faces import MODEL, crop_plan, detect_faces, frame_photo
from airprint import offline, documents

ROOT = Path(__file__).resolve().parents[1]


class CropGeometry(unittest.TestCase):
    def test_no_face_keeps_center(self):
        self.assertEqual(crop_plan(2000, 1000, (1040, 1040), []), {'scaling': 'fill', 'centering': (.5, .5)})

    def test_edge_face_moves_only_as_far_as_needed(self):
        plan = crop_plan(2000, 1000, (1040, 1040), [[.8, .25, .9, .45]])
        self.assertEqual(plan['scaling'], 'fill')
        self.assertAlmostEqual(plan['centering'][0], .84)
        self.assertEqual(plan['centering'][1], .5)

    def test_high_face_in_splice_keeps_head(self):
        plan = crop_plan(1000, 2000, (1216, 912), [[.3, .05, .5, .15]])
        self.assertEqual(plan['scaling'], 'fill')
        self.assertAlmostEqual(plan['centering'][1], 0)

    def test_distant_group_fits_everyone(self):
        plan = crop_plan(2000, 1000, (1040, 1040), [[.05, .2, .15, .4], [.85, .2, .95, .4]])
        self.assertEqual(plan['scaling'], 'fit')

    def test_centered_face_does_not_recompose(self):
        self.assertEqual(crop_plan(2000, 1000, (1040, 1040), [[.4, .3, .6, .5]])['centering'], (.5, .5))

    def test_invalid_boxes_ignored(self):
        self.assertEqual(crop_plan(2000, 1000, (1040, 1040), [[math.nan, 0, 1, 1], [.5, .1, .2, .4], [2, 2, 3, 3]])['centering'], (.5, .5))

    def test_fit_and_manual_crop_do_not_run_detection(self):
        im = Image.new('RGB', (200, 100), 'red')
        with patch('printing.faces.detect_faces', side_effect=AssertionError('must not detect')):
            self.assertEqual(frame_photo(im, (100, 100), scaling='fit').getpixel((50, 0)), (255, 255, 255))
            self.assertEqual(frame_photo(im, (100, 100), centering=(0, .5)).size, (100, 100))

    def test_model_failure_falls_back(self):
        with patch('printing.faces._session', side_effect=RuntimeError('model failure')):
            self.assertEqual(detect_faces(Image.new('RGB', (10, 10))), [])

    def test_shape_and_margins_all_papers(self):
        for target in ((1040, 1040), (1216, 1824), (1216, 912)):
            for width, height in ((2000, 1000), (1000, 2000), (1000, 1000)):
                box = [.75, .1, .9, .3]
                plan = crop_plan(width, height, target, [box])
                if plan['scaling'] == 'fit':
                    continue
                cw = min(1, height/width*target[0]/target[1])
                ch = min(1, width/height*target[1]/target[0])
                left, top = (1-cw)*plan['centering'][0], (1-ch)*plan['centering'][1]
                self.assertLessEqual(left, .72+1e-6)
                self.assertGreaterEqual(left+cw, .93-1e-6)
                self.assertLessEqual(top, 1e-6)
                self.assertGreaterEqual(top+ch, .34-1e-6)


class AirPrintBoundary(unittest.TestCase):
    def test_jpeg_enables_detection(self):
        out = io.BytesIO()
        Image.new('RGB', (400, 200), 'blue').save(out, 'JPEG')
        with patch('printing.faces.detect_faces', return_value=[]) as detect:
            self.assertEqual(offline.prepare_jpeg(out.getvalue()).size, (1216, 1824))
            detect.assert_called_once()

    def test_plain_pdf_and_raster_never_detect(self):
        pixels = Image.new('RGB', (20, 30), 'blue').tobytes()
        with patch.object(documents, '_render_lib'), patch.object(documents, '_native_render', return_value=(pixels, 20, 30)), patch.object(documents, '_pdf_is_photo', return_value=False), patch('printing.faces.detect_faces', side_effect=AssertionError('document cropped')):
            for mime in ('application/pdf', 'image/urf', 'image/pwg-raster'):
                self.assertEqual(documents.prepare_document(b'document', mime).size, (1216, 1824))

    def test_photo_pdf_detects(self):
        pixels = Image.new('RGB', (20, 30), 'blue').tobytes()
        with patch.object(documents, '_render_lib'), patch.object(documents, '_native_render', return_value=(pixels, 20, 30)), patch.object(documents, '_pdf_is_photo', return_value=True), patch('printing.faces.detect_faces', return_value=[]) as detect:
            documents.prepare_document(b'photo pdf', 'application/pdf')
            detect.assert_called_once()

    def test_splice_handles_each_photo_independently(self):
        a = Image.new('RGB', (400, 200), 'red')
        b = Image.new('RGB', (400, 200), 'blue')
        group = [[.02, .2, .1, .4], [.9, .2, .98, .4]]
        with patch('printing.faces.detect_faces', side_effect=[[], group]) as detect:
            result = offline.compose_splice([a, b])
            self.assertEqual(detect.call_count, 2)
        with Image.open(io.BytesIO(result.jpeg)) as image:
            self.assertLess(image.getpixel((600, 5))[1], 10)
            self.assertTrue(all(v > 245 for v in image.getpixel((600, 917))))
            self.assertGreater(image.getpixel((600, 1400))[2], 240)

    def test_splice_plain_document_preserves_entire_page(self):
        im = Image.new('RGB', (200, 400), 'blue')
        im.info['studio_photo'] = False
        with patch('printing.faces.detect_faces', side_effect=AssertionError('document cropped')):
            result = offline.compose_splice([im])
        with Image.open(io.BytesIO(result.jpeg)) as image:
            self.assertTrue(all(v > 245 for v in image.getpixel((5, 450))))


@unittest.skipUnless(MODEL.is_file(), 'run fetch_deps.py to verify actual inference')
class RealDetector(unittest.TestCase):
    def portrait(self):
        with Image.open(ROOT/'tests/fixtures/faces/astronaut.jpg') as image:
            return image.convert('RGB')

    def test_blank_has_no_faces(self):
        self.assertEqual(detect_faces(Image.new('RGB', (800, 600), 'gray')), [])

    def test_real_face_bounds(self):
        faces = detect_faces(self.portrait())
        self.assertEqual(len(faces), 1)
        left, top, right, bottom = faces[0]
        self.assertTrue(.32 < left < .38 and .10 < top < .15 and .50 < right < .56 and .31 < bottom < .37, faces)

    def test_real_edge_and_group_photos(self):
        face = self.portrait()
        edge = Image.new('RGB', (1200, 600), '#aaaaaa')
        edge.paste(face, (688, 30))
        found = detect_faces(edge)
        self.assertEqual(len(found), 1)
        self.assertGreater(crop_plan(*edge.size, (1040, 1040), found)['centering'][0], .6)
        group = Image.new('RGB', (1500, 600), '#aaaaaa')
        group.paste(face, (0, 30)); group.paste(face, (988, 30))
        found = detect_faces(group)
        self.assertEqual(len(found), 2)
        self.assertEqual(crop_plan(*group.size, (1040, 1040), found)['scaling'], 'fit')


if __name__ == '__main__':
    unittest.main()
