"""Pinned desktop model downloads; no inference or device access."""
import asyncio
import hashlib
import importlib
import json
import os
from pathlib import Path
import tempfile
from printing.platform import open_lock, lock_exclusive

ROOT = Path(__file__).resolve().parents[1]
MODELS = {
    'face': ('人脸辅助裁切', 'face_detection_yunet_2023mar.onnx', 'https://media.githubusercontent.com/media/opencv/opencv_zoo/f12e12798e8314f7c074a6656816c048dcc95b7a/models/face_detection_yunet/face_detection_yunet_2023mar.onnx', 1024*1024),
    'cutout': ('证件照抠图换底', 'u2netp.onnx', 'https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx', 8*1024*1024),
}


class ModelStore:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.checksums = json.loads((self.root/'deps/checksums.json').read_text())
        self.tasks, self.progress, self.cache = {}, {}, {}
        self.closed = False

    def path(self, key):
        return self.root/'assets/models'/MODELS[key][1]

    def inspect(self, key):
        path = self.path(key)
        try:
            stat = path.stat()
            signature = (stat.st_mtime_ns, stat.st_size, stat.st_ctime_ns)
            if self.cache.get(key, (None,))[0] == signature:
                return self.cache[key][1]
            valid = stat.st_size <= MODELS[key][3] and hashlib.sha256(path.read_bytes()).hexdigest() == self.checksums['assets/models/'+path.name]
            status = 'verified' if valid else 'invalid'
            self.cache[key] = (signature, status)
            return status
        except FileNotFoundError:
            return 'missing'
        except OSError:
            return 'unreadable'

    async def status(self):
        def inspect():
            try:
                importlib.import_module('onnxruntime')
                runtime = True
            except Exception:
                runtime = False
            return runtime, {key:self.inspect(key) for key in MODELS}
        runtime, files = await asyncio.to_thread(inspect)
        return dict(runtime=runtime, models=[dict(id=key, name=spec[0], fileState=files[key],
                    **self.progress.get(key, {'state':files[key], 'bytes':0})) for key,spec in MODELS.items()])

    def start(self, key):
        if self.closed or key not in MODELS:
            raise ValueError('模型参数无效')
        if key not in self.tasks or self.tasks[key].done():
            self.progress[key] = dict(state='downloading', bytes=0)
            self.tasks[key] = asyncio.create_task(self.download(key))

    async def download(self, key):
        import aiohttp
        path, temporary = self.path(key), None
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            locks=self.root/'build/dependency-locks';locks.mkdir(parents=True,exist_ok=True)
            with open_lock(locks/(path.name+'.lock')) as lock:
                lock_exclusive(lock)
                if await asyncio.to_thread(self.inspect, key) == 'verified':
                    self.progress.pop(key, None)
                    return
                descriptor, temporary = tempfile.mkstemp(prefix='.'+path.name+'-', suffix='.download', dir=path.parent)
                digest, count = hashlib.sha256(), 0
                timeout = aiohttp.ClientTimeout(total=180, sock_read=30)
                async with aiohttp.ClientSession(timeout=timeout) as client:
                    async with client.get(MODELS[key][2]) as response:
                        response.raise_for_status()
                        if response.content_length and response.content_length>MODELS[key][3]:
                            raise ValueError('模型文件超过大小限制')
                        with os.fdopen(descriptor, 'wb') as output:
                            descriptor = None
                            async for chunk in response.content.iter_chunked(65536):
                                count += len(chunk)
                                if count>MODELS[key][3]:raise ValueError('模型文件超过大小限制')
                                output.write(chunk);digest.update(chunk)
                                self.progress[key] = dict(state='downloading', bytes=count)
                            output.flush();os.fsync(output.fileno())
                if digest.hexdigest()!=self.checksums['assets/models/'+path.name]:
                    raise ValueError('模型校验失败，请重试')
                os.replace(temporary, path)
                self.cache.pop(key, None);self.progress.pop(key, None)
        except asyncio.CancelledError:
            self.progress.pop(key, None)
            raise
        except BlockingIOError:
            self.progress[key] = dict(state='failed', bytes=0, error='另一个进程正在下载，请稍后重试')
        except Exception as error:
            message = str(error) if isinstance(error, ValueError) else '下载未完成，请检查网络或目录权限后重试'
            self.progress[key] = dict(state='failed', bytes=0, error=message)
        finally:
            if 'descriptor' in locals() and descriptor is not None:os.close(descriptor)
            if temporary is not None:Path(temporary).unlink(missing_ok=True)

    async def close(self):
        self.closed = True
        for task in self.tasks.values():task.cancel()
        await asyncio.gather(*self.tasks.values(), return_exceptions=True)
