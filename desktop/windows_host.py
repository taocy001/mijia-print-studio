"""Launcher-owned service; closing its input requests a graceful shutdown."""
import asyncio
from pathlib import Path
import sys
import threading
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from desktop.windows import arguments


async def serve(args):
    from desktop.serve import run
    stopped = asyncio.Event()
    loop = asyncio.get_running_loop()
    def control():
        try:
            for line in sys.stdin:
                if line.strip() == 'STOP': break
        finally:
            try: loop.call_soon_threadsafe(stopped.set)
            except RuntimeError: pass
    threading.Thread(target=control, daemon=True).start()
    await run(args, stop_event=stopped, on_ready=lambda: print('STUDIO_READY', flush=True))


if __name__ == '__main__':
    from desktop.windows_runtime import lease
    with lease():
        asyncio.run(serve(arguments()))
