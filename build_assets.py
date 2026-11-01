"""Stage only declared editor assets and required notices for Android."""
import json
import shutil
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath

NOTICES = (
    'licenses/Project-MIT.txt', 'licenses/THIRD_PARTY.md',
    'licenses/Bluetooth-MIT.txt', 'licenses/Calendar-Holidays-MIT.txt',
    'licenses/Calendar-Lunar-MIT.txt', 'licenses/QR-Code-MIT.txt',
    'licenses/Twemoji-CC-BY-4.0.txt', 'models/SOURCES.txt',
    'models/ONNXRuntime-LICENSE.txt', 'models/ONNXRuntime-ThirdPartyNotices.txt',
    'models/U2Net-LICENSE.txt', 'models/YuNet-MIT.txt', 'models/rembg-LICENSE.txt',
)


def local_path(value):
    if not isinstance(value, str) or not value or '\\' in value:
        raise ValueError('Invalid asset path')
    path = PurePosixPath(value)
    if path.is_absolute() or '..' in path.parts or str(path) != value or ':' in value or '?' in value or '#' in value:
        raise ValueError('Invalid asset path: '+value)
    return value


class EntryAssets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'script' and 'src' in attrs:
            self.paths.add(local_path(attrs['src']))
        if tag == 'link' and attrs.get('rel') in ('stylesheet', 'icon', 'apple-touch-icon'):
            href=attrs.get('href')
            self.paths.add(local_path(href[1:] if isinstance(href,str) and href.startswith('/') and not href.startswith('//') else href))


def declared_assets(root):
    assets = root/'assets'
    entry = EntryAssets()
    entry.feed((assets/'index.html').read_text())
    names = {'index.html', 'sample.svg', 'provenance.json', *NOTICES, *entry.paths}
    for item in json.loads((assets/'provenance.json').read_text()):
        path = local_path(item['path'])
        if path.startswith('assets/'):
            names.add(path[len('assets/'):])
    for path in json.loads((root/'deps/checksums.json').read_text()):
        local_path(path)
        if path.startswith('assets/models/') and path.endswith('.onnx'):
            names.add(path[len('assets/'):])
    return names


def stage_assets(root, destination):
    root, destination = Path(root), Path(destination)
    assets = root/'assets'
    if assets.is_symlink() or destination.is_symlink() or assets.resolve() == destination.resolve() or assets.resolve() in destination.resolve().parents or destination.resolve() in root.resolve().parents or destination.resolve() == root.resolve():
        raise ValueError('Invalid asset staging directory')
    actual = set()
    for path in assets.rglob('*'):
        if path.is_symlink():
            raise ValueError('Symlink in assets: '+path.relative_to(assets).as_posix())
        if path.is_file():
            actual.add(path.relative_to(assets).as_posix())
    expected = declared_assets(root)
    if actual != expected:
        extra, missing = sorted(actual-expected), sorted(expected-actual)
        raise ValueError('Asset manifest mismatch; unexpected: '+', '.join(extra)+'; missing: '+', '.join(missing))
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    for name in sorted(expected):
        target = destination/name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(assets/name, target)
    return destination
