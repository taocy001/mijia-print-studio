"""Small OS boundaries for desktop locks and transport launch."""
import errno
import os
import sys


def user_id():
    return os.getuid() if hasattr(os, 'getuid') else 'user'


def open_lock(path):
    flags = os.O_CREAT | os.O_RDWR | getattr(os, 'O_NOFOLLOW', 0)
    return os.fdopen(os.open(path, flags, 0o600), 'a+b')


def lock_exclusive(handle):
    if sys.platform == 'win32':
        import msvcrt
        handle.seek(0)
        try:
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as error:
            if error.errno in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
                raise BlockingIOError('Print service or Bluetooth device is in use') from error
            raise
    else:
        import fcntl
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)


def transport_command(helper):
    return [sys.executable, '-u', str(helper)] if sys.platform == 'win32' else [str(helper)]


def sync_directory(path):
    if sys.platform == 'win32':
        return
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
