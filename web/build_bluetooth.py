"""Build the macOS Bluetooth helper. Requires Xcode command-line tools."""
import plistlib
import subprocess
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
app = root / 'build/desktop-bluetooth.app'
(app / 'Contents/MacOS').mkdir(parents=True, exist_ok=True)
(app / 'Contents/Info.plist').write_bytes(plistlib.dumps(dict(
    CFBundleExecutable='transport', CFBundleIdentifier='local.liuying.bluetooth',
    CFBundleName='Liuying Bluetooth', CFBundlePackageType='APPL', CFBundleVersion='1',
    NSBluetoothAlwaysUsageDescription='Connect to the photo printer to send photos over Bluetooth.')))
with tempfile.TemporaryDirectory(prefix='mijia-swift-') as cache:
    subprocess.run(['xcrun', 'swiftc', '-module-cache-path', cache,
                    str(root / 'web/native/bluetooth_transport.swift'), '-o',
                    str(app / 'Contents/MacOS/transport'), '-framework', 'IOBluetooth'], check=True)
subprocess.run(['codesign', '--force', '--sign', '-', str(app)], check=True)
