"""Stable anonymous display labels; independent of IPP endpoint identities."""
import json
import re
import sys
import uuid
from pathlib import Path
from .platform import open_lock, lock_exclusive
from .service import atomic


def sharing_name(data, requested=None):
    data=Path(data);data.mkdir(parents=True,exist_ok=True)
    with open_lock(data/'sharing-name.lock') as lock:
        lock_exclusive(lock)
        path=data/'sharing-name.json'
        try:identifier=str(uuid.UUID(str(json.loads(path.read_text())['id'])))
        except (FileNotFoundError,ValueError,KeyError,TypeError):
            identifier=str(uuid.uuid4());atomic(path,{'id':identifier})
    platform='Mac' if sys.platform=='darwin' else 'Windows' if sys.platform=='win32' else '电脑'
    prefix=requested if requested and requested!='Liuying Photo Printer' else '留影工坊 · '+platform
    prefix=re.sub(r'[.\\\x00-\x1f\x7f]','-',prefix).strip()
    prefix=prefix.encode('utf-8')[:32].decode('utf-8','ignore').strip() or '留影工坊'
    return prefix+' · '+identifier.replace('-','')[:8].upper()
