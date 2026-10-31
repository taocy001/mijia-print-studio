"""Desktop printing over Bluetooth. Never replay an unresolved print intent."""
import hashlib
import io
import json
import os
import time
import struct
import zlib
from PIL import Image
from .bluetooth_client import BluetoothClient


class BluetoothPrinter:
    @staticmethod
    def validate_media(media_size):
        if media_size not in (5009, 5012, 5014):
            name = f'纸型 {media_size}'
            raise ValueError(f'当前检测到{name}；此蓝牙驱动尚未支持，支持 3 寸方形背胶、6 寸相纸和 4 寸拼接相纸')

    def __init__(self, address, helper, channel, state_dir, *, status_only=False):
        self.client = BluetoothClient(address, helper, channel)
        state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        key = hashlib.sha256(self.client.address.encode()).hexdigest()[:24]
        self.intent = state_dir / (key + '.json')
        self.client.open(lock_timeout=0 if status_only else 5, attempts=2)

    def close(self):
        self.client.close()

    def rpc(self, method, params, extra=None, timeout=10):
        if method == 'print-job':
            raise ValueError('Use print_photo to preserve the print intent')
        return {'result': self.client.rpc(method, params)}

    def get_prop(self, *names):
        return self.client.rpc('get_prop', list(names))

    def get_media_size(self):
        return self.get_prop('media-size')[0]['media-size']

    def _record(self, record, *, create=False):
        flags = os.O_WRONLY | os.O_CREAT | (os.O_EXCL if create else os.O_TRUNC)
        with os.fdopen(os.open(self.intent, flags, 0o600), 'w') as f:
            json.dump(record, f)
            f.flush()
            os.fsync(f.fileno())
        fd = os.open(self.intent.parent, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    def print_photo(self, files, copies=1, sharpen=0, media_size=5012,
                    log=print, on_lower_quality=None, on_cancel=None):
        self.validate_media(media_size)
        expected_width, expected_height = (1040, 1040) if media_size == 5009 else (1216, 1824)
        if type(copies) is not int or copies < 1:
            raise ValueError('打印份数必须是正整数')
        files = list(files)
        if len(files) not in (1, 2):
            raise ValueError('需要一张 JPEG，可附带一份覆膜图层')
        coat = files[0] if len(files) == 2 else None
        if coat is not None:
            if len(coat) < 32 or len(coat) > 1048576 or coat[:12] != b'ocpattern1\0\0':
                raise ValueError('覆膜文件格式不正确')
            width, height, size, version = struct.unpack('>IIII', coat[12:28])
            if (width, height, size, version) != (expected_width, expected_height, len(coat)-32, 1):
                raise ValueError('覆膜文件尺寸不正确')
            decoder = zlib.decompressobj(-15)
            mask = decoder.decompress(coat[32:], expected_width*expected_height+1)
            if len(mask) != expected_width*expected_height or not decoder.eof or decoder.unused_data:
                raise ValueError('覆膜文件内容不完整')
        data = files[-1]
        with Image.open(io.BytesIO(data)) as im:
            if im.format != 'JPEG' or im.size != (expected_width, expected_height):
                raise ValueError(f'当前相纸需要 {expected_width}×{expected_height} JPEG')
            im.load()
            if len(data) > 1048576:
                for quality in (90, 85, 80):
                    out = io.BytesIO()
                    im.convert('RGB').save(out, 'JPEG', quality=quality, optimize=True)
                    data = out.getvalue()
                    if len(data) <= 1048576:
                        break
        if len(data) > 1048576:
            raise ValueError('照片超过蓝牙大小限制，请降低画质后重试')
        if self.intent.exists():
            raise RuntimeError('上次蓝牙打印结果未确认，请先核对打印机和 bluetooth-state 中的任务记录；不会自动重印')
        status = self.get_prop('printer-state-alerts', 'media-size')
        jobs = self.client.rpc('get-job-id-list', {})
        if status[0] != '::0' or status[1].get('media-size') != (5012 if media_size == 5014 else media_size) or jobs.get('job-id-list') not in ('', []):
            raise RuntimeError('请检查相纸、耗材和打印机队列')
        record = {'phase': 'creating'}
        self._record(record, create=True)
        result = self.client.rpc('print-job', {
            'copies': copies, 'file-size': len(data)+(len(coat) if coat else 0), 'job-type': 0, 'file-type': 'jpg',
            'media-size': media_size, 'channel': 576, 'sharpenmode': sharpen,
        })
        job = result.get('job-id', result.get('job_id'))
        if result.get('error-code', 0) != 0 or type(job) is not int or job <= 0:
            raise RuntimeError('蓝牙任务未确认；保留记录，不自动重试')
        record.update(phase='uploading', job=job)
        self._record(record)
        if coat is not None:
            self.client.upload(job, coat)
        self.client.upload(job, data)
        log('传输完成，等待打印机确认打印结果…')
        cancel_sent=False
        for _ in range(150):
            if on_cancel and on_cancel() and not cancel_sent:
                self.client.rpc("cancel-job", {"job-id":job});cancel_sent=True
            infos = self.client.rpc('get-job-info', {'job-id': job})
            matches = [i for i in infos if i.get('job-id') == job]
            if len(matches) != 1:
                raise RuntimeError('打印状态未确认；保留记录，不自动重试')
            info = matches[0]
            state = info.get('job-state')
            if state in (7, 8, 9):
                self.last_state=state
                self.intent.unlink()
                log('打印完成' if state == 9 else '打印已中止')
                return state == 9
            time.sleep(2)
        raise TimeoutError('打印结果未确认；保留记录，不自动重试')
