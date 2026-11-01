"""Keep the checkout's runtime open while Windows uses its dependencies."""
from pathlib import Path


def lease():
    path = Path(__file__).resolve().parents[1]/'build/windows-install.lock'
    path.parent.mkdir(parents=True, exist_ok=True)
    try: return path.open('a+b')
    except PermissionError: raise RuntimeError('Runtime setup is in progress; start the service after setup finishes.') from None
