"""Preserve portrait editor space when rotating with the text drawer open."""
from pathlib import Path
from urllib.parse import urlparse
import mimetypes
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORTRAIT = {'width': 390, 'height': 700}
LANDSCAPE = {'width': 844, 'height': 390}
GEOMETRY = """() => ({
 dock: document.querySelector('.dock').getBoundingClientRect().height,
 cached: parseFloat(document.documentElement.style.getPropertyValue('--browser-dock-height')),
 app: document.querySelector('.app').getBoundingClientRect().height,
 workspace: document.querySelector('.workspace').getBoundingClientRect().height,
 editing: document.body.classList.contains('layer-editing'),
 landscape: document.body.classList.contains('landscape')
})"""

with sync_playwright() as p:
 browser = p.chromium.launch()
 for native in (False, True):
  for initial_portrait in (False, True):
   page = browser.new_page(viewport=PORTRAIT if initial_portrait else LANDSCAPE)
   errors = []
   page.on('pageerror', lambda e: errors.append(str(e)))
   if native:
    page.add_init_script("window.Studio={landscape:()=>innerWidth>innerHeight,state:()=>'{\"device\":{},\"history\":[]}'}")
   def route(r):
    assert r.request.method == 'GET', 'Layout test must not print'
    url = urlparse(r.request.url)
    assert url.hostname == 'studio.test', url.hostname
    if url.path == '/api/state':
     r.fulfill(json={'device': {}, 'history': []}); return
    file = ROOT / 'assets' / (url.path.lstrip('/') or 'index.html')
    if file.is_file():
     r.fulfill(body=file.read_bytes(), content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
    else:
     r.fulfill(status=404, body='Missing')
   page.route('**/*', route)
   page.goto('https://studio.test/')
   page.wait_for_function('window.CropEditor && window.LayerEditor')
   page.evaluate('LayerEditor.ready')
   page.evaluate("""async()=>{poll=()=>{};closeSheet();
    const photo={src:'/sample.svg',turn:0,zoom:1,x:0,y:0,fit:'cover',filter:'none',overlays:[]};
    await loadPhoto(photo);state={...defaults,photos:[photo],active:0};render();} """)
   page.wait_for_timeout(150)
   baseline = page.evaluate(GEOMETRY) if initial_portrait else None
   page.set_viewport_size(LANDSCAPE)
   page.wait_for_timeout(150)
   page.locator('#addTextQuick').click()
   page.locator('#layerText').fill('Synthetic rotation test')
   page.wait_for_timeout(150)
   landscape = page.evaluate(GEOMETRY)
   assert landscape['editing'] and landscape['landscape'], landscape
   assert abs(landscape['cached'] - LANDSCAPE['height']) <= 1, landscape
   page.set_viewport_size(PORTRAIT)
   page.wait_for_timeout(150)
   hidden = page.evaluate(GEOMETRY)
   assert hidden['editing'] and not hidden['landscape'] and hidden['dock'] == 0, hidden
   assert 50 <= hidden['cached'] <= 80, hidden
   assert hidden['app'] >= 620 and hidden['workspace'] >= 490, hidden
   assert abs(hidden['app'] + hidden['cached'] - PORTRAIT['height']) <= 1, hidden
   if baseline:
    assert abs(hidden['cached'] - baseline['cached']) <= 1, (baseline, hidden)
    assert abs(hidden['workspace'] - baseline['workspace']) <= 1, (baseline, hidden)
   page.locator('#closeSheet').click()
   page.wait_for_timeout(150)
   restored = page.evaluate(GEOMETRY)
   assert not restored['editing'] and 50 <= restored['dock'] <= 80, restored
   assert abs(restored['dock'] - restored['cached']) <= 1, restored
   assert abs(restored['app'] - hidden['app']) <= 2, (hidden, restored)
   assert abs(restored['workspace'] - hidden['workspace']) <= 2, (hidden, restored)
   assert not errors, errors
   page.close()
 browser.close()
print('PASS: native/web hidden dock rotation, cached/default portrait height and editor close; no printing')
