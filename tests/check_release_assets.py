from pathlib import Path
import hashlib,json,re,xml.etree.ElementTree as ET
root=Path(__file__).resolve().parents[1];assets=root/'assets'
for name in ['templates','name-labels','card-art']:
 assert not (assets/name).exists(),name
for item in json.loads((assets/'provenance.json').read_text()):
 file=root/item['path'];assert file.is_file(),file
 assert hashlib.sha256(file.read_bytes()).hexdigest()==item['sha256'],file
for file in (assets/'emoji').glob('*.svg'):
 tree=ET.fromstring(file.read_text())
 for e in tree.iter():
  assert e.tag.split('}')[-1] not in ['script','foreignObject','image'],file
  assert not any(k.startswith('on') or 'href' in k for k in e.attrib),file
catalog=json.loads((assets/'emoji-catalog.js').read_text().split('=',1)[1].rstrip(';\n'))
assert {v['code']+'.svg' for group in catalog.values() for v in group}=={p.name for p in (assets/'emoji').glob('*.svg')}
for name in ['Project-MIT.txt','THIRD_PARTY.md','Twemoji-CC-BY-4.0.txt','Calendar-Lunar-MIT.txt','Calendar-Holidays-MIT.txt','Bluetooth-MIT.txt']:
 assert (assets/'licenses'/name).is_file(),name
assert (assets/'licenses/Project-MIT.txt').read_bytes()==(root/'LICENSE').read_bytes()
assert (assets/'licenses/THIRD_PARTY.md').read_bytes()==(root/'THIRD_PARTY.md').read_bytes()
for p in [*assets.glob('*.js'),*root.glob('src/*.java'),root/'AndroidManifest.xml']:
 s=p.read_text();assert not re.search(r'/Users/|local\.tao\.|syrup_6|portrait-Size6Inch|wide-.*_ota|(?:[A-F0-9]{2}:){5}[A-F0-9]{2}',s),p
print('PASS: provenance hashes, SVG safety, complete emoji catalog, bundled licenses, removed legacy assets and personal identifiers')
