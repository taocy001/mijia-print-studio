#!/usr/bin/env python3
"""Download pinned build dependencies."""
import hashlib,json,os,tempfile,urllib.request
from printing.platform import open_lock,lock_exclusive
from pathlib import Path
ROOT=Path(__file__).resolve().parent
URLS={
 'assets/models/face_detection_yunet_2023mar.onnx':'https://media.githubusercontent.com/media/opencv/opencv_zoo/f12e12798e8314f7c074a6656816c048dcc95b7a/models/face_detection_yunet/face_detection_yunet_2023mar.onnx',
 'deps/onnxruntime-android-1.23.2.aar':'https://repo.maven.apache.org/maven2/com/microsoft/onnxruntime/onnxruntime-android/1.23.2/onnxruntime-android-1.23.2.aar',
 'assets/models/u2netp.onnx':'https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx',
}
for name,checksum in json.loads((ROOT/'deps/checksums.json').read_text()).items():
 path=ROOT/name
 if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()==checksum:continue
 path.parent.mkdir(parents=True,exist_ok=True)
 locks=ROOT/'build/dependency-locks';locks.mkdir(parents=True,exist_ok=True)
 with open_lock(locks/(path.name+'.lock')) as lock:
  lock_exclusive(lock)
  with urllib.request.urlopen(URLS[name],timeout=120) as response:data=response.read()
  if hashlib.sha256(data).hexdigest()!=checksum:raise RuntimeError('Checksum mismatch: '+name)
  fd,temporary=tempfile.mkstemp(prefix='.'+path.name+'-',suffix='.download',dir=path.parent)
  try:
   with os.fdopen(fd,'wb') as output:output.write(data);output.flush();os.fsync(output.fileno())
   os.replace(temporary,path)
  finally:Path(temporary).unlink(missing_ok=True)
 print('Ready:',name)
