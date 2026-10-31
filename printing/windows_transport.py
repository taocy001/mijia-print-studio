"""Windows RFCOMM byte transport; protocol and print decisions stay in the parent."""
import os
import re
import socket
import sys
import threading


def connect(address, channel, factory=None):
    if not re.fullmatch(r'(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}', address or ''):
        raise ValueError('Invalid Bluetooth address')
    if type(channel) is not int or not 1 <= channel <= 30:
        raise ValueError('RFCOMM channel must be 1..30')
    if factory is None and not hasattr(socket, 'AF_BLUETOOTH'):
        raise OSError('Windows CPython with Bluetooth socket support is required')
    sock = (factory or socket.socket)(getattr(socket, 'AF_BLUETOOTH', 32), socket.SOCK_STREAM,
                                      getattr(socket, 'BTPROTO_RFCOMM', 3))
    try:
        sock.settimeout(30)
        sock.connect((address, channel))
        sock.settimeout(15)
        return sock
    except BaseException:
        sock.close()
        raise


def serve(sock, source, output):
    lock = threading.Lock()
    stopped = threading.Event()
    def emit(value):
        with lock:
            output.write(value + '\n')
            output.flush()
    def receive():
        try:
            while not stopped.is_set():
                try:
                    data = sock.recv(4096)
                except socket.timeout:
                    continue
                if not data:
                    if not stopped.is_set():
                        emit('ERROR Bluetooth disconnected')
                    break
                emit('DATA ' + data.hex())
        except OSError:
            if not stopped.is_set():
                emit('ERROR Bluetooth receive failed')
    reader = threading.Thread(target=receive, daemon=True)
    emit('READY')
    reader.start()
    try:
        while True:
            line = source.readline(4096)
            if not line or line.strip() == 'CLOSE':
                break
            if not line.endswith('\n') or len(line) > 2091:
                raise ValueError('Invalid transport frame')
            value = line.strip()
            if not value or len(value) % 2 or not re.fullmatch('[0-9a-fA-F]+', value):
                raise ValueError('Invalid transport frame')
            sock.sendall(bytes.fromhex(value))
            emit('SENT')
    finally:
        stopped.set()
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        sock.close()
        reader.join(timeout=1)


def main():
    try:
        if sys.platform != 'win32':
            raise OSError('This Bluetooth transport requires Windows')
        address = os.environ.get('MIJIA_BLUETOOTH_ADDRESS', '')
        channel = int(os.environ.get('MIJIA_RFCOMM_CHANNEL', '1'))
        serve(connect(address, channel), sys.stdin, sys.stdout)
    except Exception as error:
        print('ERROR ' + type(error).__name__ + ': Bluetooth transport unavailable; check pairing and adapter', flush=True)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
