#!/usr/bin/env python3
"""Download pinned build dependencies."""
import hashlib,json,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent
URLS={
 'deps/onnxruntime-android-1.23.2.aar':'https://repo.maven.apache.org/maven2/com/microsoft/onnxruntime/onnxruntime-android/1.23.2/onnxruntime-android-1.23.2.aar',
 'assets/models/u2netp.onnx':'https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx',
}
for name,checksum in json.loads((ROOT/'deps/checksums.json').read_text()).items():
 path=ROOT/name
 if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()==checksum:continue
 path.parent.mkdir(parents=True,exist_ok=True)
 with urllib.request.urlopen(URLS[name],timeout=120) as response:data=response.read()
 if hashlib.sha256(data).hexdigest()!=checksum:raise RuntimeError('Checksum mismatch: '+name)
 temporary=path.with_suffix('.download');temporary.write_bytes(data);temporary.replace(path)
 print('Ready:',name)
