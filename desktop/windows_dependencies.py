"""Install only this checkout's pinned dependencies while its default service is stopped."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from printing.platform import open_lock, lock_exclusive

ROOT = Path(__file__).resolve().parents[1]
IMPORTS = 'import aiohttp,PIL,numpy,Crypto,pypdf,pypdfium2,zeroconf,pi_heif,onnxruntime,tkinter'


def prepare(root=ROOT, data=None, run=subprocess.run):
    data = data or Path(os.environ['LOCALAPPDATA'])/'MijiaPrintStudio'
    stamp = root/'build/windows-requirements.txt'
    digest = hashlib.sha256(b'\0'.join((root/name).read_bytes() for name in ('desktop/requirements-windows.txt','web/requirements.txt'))).hexdigest()
    if stamp.is_file() and stamp.read_text().strip() == digest:
        if run([sys.executable, '-c', IMPORTS], capture_output=True).returncode == 0: return
    data.mkdir(parents=True, exist_ok=True)
    with open_lock(data/'launcher.lock') as launcher, open_lock(data/'service.lock') as service:
        try: lock_exclusive(launcher); lock_exclusive(service)
        except BlockingIOError: raise RuntimeError('Close the launcher and stop the service before updating dependencies.') from None
        for args in (['-m','ensurepip'], ['-m','pip','install','--disable-pip-version-check','-r',str(root/'desktop/requirements-windows.txt')], ['-c',IMPORTS]):
            result = run([sys.executable,*args], cwd=root)
            if result.returncode: raise RuntimeError('Dependency setup failed; no service was started. Run setup again to retry.')
        stamp.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix='.windows-setup-',dir=stamp.parent)
        try:
            with os.fdopen(fd,'w') as output: output.write(digest+'\n'); output.flush(); os.fsync(output.fileno())
            os.replace(name,stamp)
        finally:
            if os.path.exists(name):os.unlink(name)


if __name__ == '__main__':
    if sys.platform != 'win32': raise SystemExit('Native Windows Python is required')
    prepare()
