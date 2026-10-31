"""Offline face bounds and conservative automatic photo framing."""
import logging
import math
import threading
from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageOps

MODEL = Path(__file__).resolve().parents[1] / 'assets/models/face_detection_yunet_2023mar.onnx'
SIZE = 640
SCORE = .75
NMS = .3
_log = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _session():
    import onnxruntime as ort
    ort.disable_telemetry_events()
    options = ort.SessionOptions()
    options.intra_op_num_threads = 1
    options.inter_op_num_threads = 1
    return ort.InferenceSession(str(MODEL), sess_options=options, providers=['CPUExecutionProvider'])


def _iou(a, b):
    intersection = max(0, min(a[2], b[2])-max(a[0], b[0])) * max(0, min(a[3], b[3])-max(a[1], b[1]))
    union = (a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - intersection
    return intersection / union if union > 0 else 0


def _decode(outputs, width, height):
    import numpy as np
    candidates = []
    for stride in (8, 16, 32):
        cls = outputs[f'cls_{stride}'].reshape(-1)
        obj = outputs[f'obj_{stride}'].reshape(-1)
        boxes = outputs[f'bbox_{stride}'].reshape(-1, 4)
        scores = np.sqrt(np.clip(cls, 0, 1)*np.clip(obj, 0, 1))
        for index in np.flatnonzero(scores >= SCORE):
            index = int(index)
            dx, dy, dw, dh = map(float, boxes[index])
            if not all(math.isfinite(v) for v in (dx, dy, dw, dh)) or abs(dw) > 20 or abs(dh) > 20:
                continue
            cx = (index % (SIZE//stride) + dx) * stride
            cy = (index // (SIZE//stride) + dy) * stride
            bw, bh = math.exp(dw)*stride, math.exp(dh)*stride
            box = [max(0., (cx-bw/2)/width), max(0., (cy-bh/2)/height),
                   min(1., (cx+bw/2)/width), min(1., (cy+bh/2)/height)]
            if box[2] > box[0] and box[3] > box[1]:
                candidates.append((float(scores[index]), box))
    candidates.sort(key=lambda item: -item[0])
    kept = []
    for _, box in candidates[:1000]:
        if all(_iou(box, other) <= NMS for other in kept):
            kept.append(box)
    return kept


def detect_faces(image):
    """Return normalized xyxy bounds; detection failures never block printing."""
    try:
        import numpy as np
        import onnxruntime as ort
        scale = SIZE / max(image.size)
        width, height = max(1, int(image.width*scale+.5)), max(1, int(image.height*scale+.5))
        small = image.convert('RGB').resize((width, height), Image.Resampling.BILINEAR)
        value = np.zeros((1, 3, SIZE, SIZE), dtype=np.float32)
        value[0, :, :height, :width] = np.asarray(small, dtype=np.float32)[:, :, ::-1].transpose(2, 0, 1)
        session = _session()
        options = ort.RunOptions()
        timer = threading.Timer(2., lambda: setattr(options, 'terminate', True))
        timer.daemon = True
        timer.start()
        try:
            names = [f'{kind}_{stride}' for kind in ('cls', 'obj', 'bbox') for stride in (8, 16, 32)]
            outputs = dict(zip(names, session.run(names, {'input': value}, options)))
        finally:
            timer.cancel()
        return _decode(outputs, width, height)
    except Exception as error:
        _log.warning('Face detection unavailable (%s); using centered crop', type(error).__name__)
        return []


def crop_plan(width, height, target, faces):
    """Move a fill crop only as far as needed; use fit when heads cannot fit."""
    if width <= 0 or height <= 0 or min(target) <= 0:
        raise ValueError('Invalid photo dimensions')
    protected = []
    for face in faces:
        if len(face) != 4 or not all(math.isfinite(v) for v in face):
            continue
        left, top, right, bottom = [max(0., min(1., v)) for v in face]
        if right <= left or bottom <= top:
            continue
        fw, fh = right-left, bottom-top
        protected.append((max(0., left-fw*.2), max(0., top-fh*.5), min(1., right+fw*.2), min(1., bottom+fh*.2)))
    result = {'scaling': 'fill', 'centering': (.5, .5)}
    if not protected:
        return result
    left, top = min(b[0] for b in protected), min(b[1] for b in protected)
    right, bottom = max(b[2] for b in protected), max(b[3] for b in protected)
    cw = min(1., height/width * target[0]/target[1])
    ch = min(1., width/height * target[1]/target[0])
    if right-left > cw+1e-6 or bottom-top > ch+1e-6:
        return {'scaling': 'fit', 'centering': (.5, .5)}
    def center(low, high, length):
        overflow = 1-length
        if overflow <= 1e-9:
            return .5
        start = max(max(0., high-length), min(overflow/2, min(low, overflow)))
        return max(0., min(1., start/overflow))
    result['centering'] = (center(left, right, cw), center(top, bottom, ch))
    return result


def frame_photo(image, target, *, scaling='fill', centering=(.5, .5), face_aware=True):
    if scaling == 'fill' and face_aware and tuple(centering) == (.5, .5):
        plan = crop_plan(*image.size, target, detect_faces(image))
        scaling, centering = plan['scaling'], plan['centering']
    if scaling == 'fill':
        return ImageOps.fit(image, target, Image.Resampling.LANCZOS, centering=centering)
    inner = ImageOps.contain(image, target, Image.Resampling.LANCZOS)
    frame = Image.new('RGB', target, 'white')
    frame.paste(inner, ((target[0]-inner.width)//2, (target[1]-inner.height)//2))
    return frame
