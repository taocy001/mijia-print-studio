"""Read-only Windows readiness checks; never opens a printer connection."""
import argparse
import base64
import ctypes
import importlib.util
import json
import os
from pathlib import Path
import re
import socket
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
DEPENDENCIES = {'aiohttp': 'aiohttp', 'Pillow': 'PIL', 'numpy': 'numpy',
                'pycryptodome': 'Crypto', 'pypdf': 'pypdf', 'pypdfium2': 'pypdfium2',
                'zeroconf': 'zeroconf', 'pi-heif': 'pi_heif', 'onnxruntime': 'onnxruntime'}
ADDRESS = re.compile(r'(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}')


def bluetooth(address):
    from ctypes import wintypes as w
    class RadioParams(ctypes.Structure):
        _fields_ = [('size', w.DWORD)]
    class SystemTime(ctypes.Structure):
        _fields_ = [('values', w.WORD * 8)]
    class Device(ctypes.Structure):
        _fields_ = [('size', w.DWORD), ('address', ctypes.c_ulonglong), ('class_', w.ULONG),
                    ('connected', w.BOOL), ('remembered', w.BOOL), ('authenticated', w.BOOL),
                    ('seen', SystemTime), ('used', SystemTime), ('name', w.WCHAR * 248)]
    api = ctypes.WinDLL('bthprops.cpl', use_last_error=True)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    api.BluetoothFindFirstRadio.argtypes = [ctypes.POINTER(RadioParams), ctypes.POINTER(w.HANDLE)]
    api.BluetoothFindFirstRadio.restype = w.HANDLE
    api.BluetoothFindNextRadio.argtypes = [w.HANDLE, ctypes.POINTER(w.HANDLE)]
    api.BluetoothFindNextRadio.restype = w.BOOL
    api.BluetoothFindRadioClose.argtypes = [w.HANDLE]
    api.BluetoothGetDeviceInfo.argtypes = [w.HANDLE, ctypes.POINTER(Device)]
    api.BluetoothGetDeviceInfo.restype = w.DWORD
    kernel.CloseHandle.argtypes = [w.HANDLE]
    params = RadioParams(ctypes.sizeof(RadioParams)); radio = w.HANDLE()
    finder = api.BluetoothFindFirstRadio(ctypes.byref(params), ctypes.byref(radio))
    if not finder:
        error = ctypes.get_last_error()
        if error == 259:
            return {'radios': 0, 'paired': False}
        raise OSError(error, 'Radio enumeration failed')
    count, paired, unknown = 0, False, False
    try:
        while True:
            try:
                count += 1
                if address:
                    device = Device(); device.size = ctypes.sizeof(Device)
                    device.address = int(address.replace(':', ''), 16)
                    code = api.BluetoothGetDeviceInfo(radio, ctypes.byref(device))
                    if code == 0: paired |= bool(device.authenticated)
                    elif code not in (2, 1168): unknown = True
            finally:
                kernel.CloseHandle(radio)
            if not api.BluetoothFindNextRadio(finder, ctypes.byref(radio)):
                if ctypes.get_last_error() != 259: unknown = True
                break
    finally:
        api.BluetoothFindRadioClose(finder)
    return {'radios': count, 'paired': True if paired else None if unknown else False}


def disabled_adapter():
    source = r'''
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new()
$disabled=$false;$parentDisabled=$false
$devices=@(Get-PnpDevice -ErrorAction Stop | Where-Object {$_.Class -eq 'Bluetooth' -and $_.InstanceId -match '^(USB|PCI)\\'})
foreach ($device in $devices) {
 $id=$device.InstanceId
 for ($level=0;$level -lt 6 -and $id;$level++) {
  $properties=Get-PnpDeviceProperty -InstanceId $id -KeyName DEVPKEY_Device_ProblemCode,DEVPKEY_Device_Parent -ErrorAction Stop
  $code=($properties | Where-Object {$_.KeyName -eq 'DEVPKEY_Device_ProblemCode'}).Data
  if ($code -eq 22) {if ($level -eq 0) {$disabled=$true} else {$parentDisabled=$true}}
  $id=($properties | Where-Object {$_.KeyName -eq 'DEVPKEY_Device_Parent'}).Data
 }
}
@{disabled=$disabled;parentDisabled=$parentDisabled} | ConvertTo-Json -Compress
'''
    command = base64.b64encode(source.encode('utf-16-le')).decode()
    result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-EncodedCommand', command],
                            capture_output=True, timeout=20)
    if result.returncode: raise OSError('Device inspection failed')
    return json.loads(result.stdout.decode('utf-8-sig'))


def port_free(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        if hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        probe.bind(('0.0.0.0', port))


def report(address=None, ports=(8635, 8636)):
    checks = []
    def add(name, status, message): checks.append(dict(check=name, status=status, message=message))
    native = sys.platform == 'win32'
    add('runtime', 'ok' if native and sys.version_info >= (3, 12) and struct.calcsize('P') == 8 else 'error',
        '需要原生 Windows、Python 3.12+、64 位；WSL 不能作为蓝牙后端。' if not native or sys.version_info < (3, 12) or struct.calcsize('P') != 8 else '原生 Windows 64 位 Python 可用。')
    missing = []
    for name, module in DEPENDENCIES.items():
        try: found = importlib.util.find_spec(module)
        except (ImportError, ValueError): found = None
        if found is None: missing.append(name)
    add('dependencies', 'error' if missing else 'ok', '缺少依赖：'+', '.join(missing) if missing else '依赖文件齐全；此项不验证驱动或动态库加载。')
    valid = bool(ADDRESS.fullmatch(address or ''))
    add('address', 'ok' if valid else 'error', '已配置目标地址。' if valid else '请设置 MIJIA_BLUETOOTH_ADDRESS 为已配对打印机的蓝牙地址。')
    if native:
        add('rfcomm', 'ok' if hasattr(socket, 'AF_BLUETOOTH') else 'error', '经典蓝牙套接字可用。' if hasattr(socket, 'AF_BLUETOOTH') else '当前 Python 不支持经典蓝牙套接字。')
        try:
            state = bluetooth(address if valid else None)
            add('adapter', 'ok' if state['radios'] else 'error', '已识别本机蓝牙适配器；不代表打印机已连接。' if state['radios'] else '未识别到可用的本机蓝牙适配器。')
            if state['radios'] and valid:
                paired = state['paired']
                add('pairing', 'ok' if paired else 'unknown' if paired is None else 'error', '目标打印机已配对。' if paired else '未能读取配对状态。' if paired is None else '目标打印机未配对，请在 Windows 蓝牙设置中配对。')
            if not state['radios']:
                try:
                    disabled = disabled_adapter()
                    if disabled['disabled'] or disabled['parentDisabled']:
                        add('disabled-device', 'error', '蓝牙适配器或其父设备被禁用，请在设备管理器检查；自检不会更改设备。')
                except (OSError, ValueError, subprocess.TimeoutExpired):
                    add('disabled-device', 'unknown', '未能检查设备禁用状态，请在设备管理器核对。')
        except (OSError, AttributeError):
            add('adapter', 'unknown', '未能查询本机蓝牙状态；请检查系统权限和驱动。')
    if len(set(ports)) != len(ports):
        add('ports', 'error', 'Web 与 AirPrint 需要不同端口。')
    for port in ports:
        if type(port) is not int or not 1 <= port <= 65535:
            add('port', 'error', '端口必须为 1–65535。'); continue
        try:
            port_free(port); add('port-'+str(port), 'ok', '端口可绑定；不代表防火墙已允许局域网访问。')
        except OSError:
            add('port-'+str(port), 'error', '端口被占用或无法绑定；若服务已启动，不要重复启动。')
    for name, filename in [('face-model', 'face_detection_yunet_2023mar.onnx'), ('cutout-model', 'u2netp.onnx')]:
        present = (ROOT/'assets/models'/filename).is_file()
        add(name, 'ok' if present else 'warning', '模型文件存在。' if present else '可选模型未安装：运行 python fetch_deps.py；普通照片仍可打印。')
    return {'ready': not any(c['status'] in ('error', 'unknown') for c in checks), 'checks': checks,
            'note': '只读自检，不连接打印机、不打印；通过不等于已验证出纸。'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--web-port', type=int, default=8635)
    parser.add_argument('--ipp-port', type=int, default=8636)
    args = parser.parse_args(argv)
    result = report(os.environ.get('MIJIA_BLUETOOTH_ADDRESS'), (args.web_port, args.ipp_port))
    if args.json: print(json.dumps(result, ensure_ascii=False))
    else:
        for item in result['checks']: print(f"[{item['status']}] {item['check']}: {item['message']}")
        print(result['note'])
    return 0 if result['ready'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
