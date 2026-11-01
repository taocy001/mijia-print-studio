"""Shared editor output on desktop/mobile viewports; synthetic inputs, no printing."""
import base64
import mimetypes
from pathlib import Path
from urllib.parse import urlparse
import unittest
from playwright.sync_api import sync_playwright
from test_output_contract import chart, decoded, encoded, quadrants
from printing.images import page_files

ROOT = Path(__file__).resolve().parents[1]
check = unittest.TestCase()


def setup(page, media, orientation='portrait', count=1, size=(600, 900), fit='cover'):
    source = base64.b64encode(encoded(chart(size), 'PNG')).decode()
    page.evaluate('''async ({source,media,orientation,count,fit})=>{
      closeSheet();state={...defaults,media,orientation,sixLayout:media,photos:[],active:0,copies:2};
      for(let i=0;i<count;i++){
        const p={src:'data:image/png;base64,'+source,fit,border:0,filter:'none',turn:0,zoom:1,x:0,y:0,
          sharpen:i%3,coatTexture:'',overlays:[]};await loadPhoto(p);state.photos.push(p);
      }
      native.device={connected:true,media:media===5014?5012:media,checkedAt:Date.now()};
    }''', dict(source=source, media=media, orientation=orientation, count=count, fit=fit))


def output(page):
    before = page.evaluate('JSON.stringify(state)')
    pages = page.evaluate('preparePrintPages()')
    check.assertEqual(page.evaluate('JSON.stringify(state)'), before, 'Export changed editor state')
    for item in pages:
        jpeg, coat = page_files(item)
        check.assertEqual(jpeg, base64.b64decode(item['base64']))
        check.assertLessEqual(len(jpeg), 1048576)
        check.assertEqual(item['copies'], 2)
        check.assertEqual(bool(coat), bool(item['ocMask']))
    return pages


with sync_playwright() as runtime:
    browser = runtime.chromium.launch()
    for width, height in [(1440, 1000), (390, 844), (844, 390)]:
        page = browser.new_page(viewport=dict(width=width, height=height))
        errors, blocked = [], []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.add_init_script("window.Studio={state:()=>'{\"permission\":true,\"device\":{},\"history\":[]}',printBatch:()=>{throw Error('Printing forbidden')}}")
        def route(request):
            name = urlparse(request.request.url).path
            if request.request.method != 'GET' or name.startswith('/api/'):
                blocked.append(name); request.abort(); return
            file = ROOT/'assets'/(name.lstrip('/') or 'index.html')
            if file.is_file():
                request.fulfill(body=file.read_bytes(), content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
            else:
                request.fulfill(status=404, body='Missing')
        page.route('**/*', route)
        page.goto('https://studio.test/')
        page.wait_for_function('window.LayerEditor&&window.TemplateStudio&&window.StudioExtras')
        page.evaluate('LayerEditor.ready')
        for media, orientation, size, order in [(5012, 'portrait', (600, 900), [0, 1, 2, 3]),
                (5012, 'landscape', (900, 600), [2, 0, 3, 1]),
                (5009, 'portrait', (600, 600), [3, 2, 1, 0])]:
            setup(page, media, orientation, size=size)
            pages = output(page)
            check.assertEqual(len(pages), 1)
            image = decoded(pages[0]['base64'])
            check.assertEqual(image.size, (1040, 1040) if media==5009 else (1216, 1824))
            quadrants(check, image, order)
            check.assertIsNone(pages[0]['ocMask'])

        # Three sources: first sheet keeps order; the odd final source repeats.
        setup(page, 5014, count=3, size=(800, 600))
        page.evaluate('''async()=>{for(const [i,color] of ['#dc2832','#1eb446','#2846dc'].entries()){
          const c=document.createElement('canvas');c.width=800;c.height=600;
          c.getContext('2d').fillStyle=color;c.getContext('2d').fillRect(0,0,800,600);
          state.photos[i].src=c.toDataURL();await loadPhoto(state.photos[i]);}state.active=1;}''')
        pages = output(page)
        check.assertEqual(len(pages), 2)
        for item, colors in zip(pages, [[(220, 40, 50), (30, 180, 70)], [(40, 70, 220)]*2]):
            image = decoded(item['base64'])
            for y, expected in zip([456, 1368], colors):
                check.assertLessEqual(max(abs(a-b) for a,b in zip(image.getpixel((608,y)), expected)), 12)

        # Contain preserves white side margins; cover fills them.
        for fit in ['contain', 'cover']:
            setup(page, 5012, size=(400, 1200), fit=fit)
            image = decoded(output(page)[0]['base64'])
            pixel = image.getpixel((60, 450))
            check.assertEqual(min(pixel)>245, fit=='contain', (fit, pixel))

        # Hidden text changes only OC, visible text changes only its own JPEG.
        setup(page, 5012, count=2)
        baseline = output(page)
        page.evaluate("state.photos[0].overlays=[{id:'contract',kind:'text',text:'TEST',font:'sans',color:'#ffffff',sizePct:16,fx:.5,fy:.5,angle:0,hidden:true}];state.active=1")
        hidden = output(page)
        check.assertEqual([p['base64'] for p in hidden], [p['base64'] for p in baseline])
        check.assertIsNone(hidden[1]['ocMask'])
        mask = decoded(hidden[0]['ocMask'])
        check.assertIsNotNone(mask.getbbox())
        check.assertEqual(mask.getpixel((10,10)), (0,0,0))
        page.evaluate('state.photos[0].overlays[0].hidden=false')
        visible = output(page)
        check.assertNotEqual(visible[0]['base64'], baseline[0]['base64'])
        check.assertEqual(visible[1]['base64'], baseline[1]['base64'])
        check.assertTrue(all(p['ocMask'] is None for p in visible))
        check.assertEqual([p['sharpen'] for p in visible], [0,1])
        page.evaluate("state.photos[0].overlays=[];state.photos[0].filter='sepia'")
        toned = output(page)
        check.assertNotEqual(toned[0]['base64'], baseline[0]['base64'])
        check.assertEqual(toned[1]['base64'], baseline[1]['base64'])
        page.evaluate("state.photos[0].filter='none';state.photos[0].overlays=[{id:'emoji',kind:'emoji',text:'😀',sizePct:18,fx:.5,fy:.5,hidden:true}]")
        emoji = output(page)
        check.assertEqual([p['base64'] for p in emoji], [p['base64'] for p in baseline])
        check.assertIsNotNone(decoded(emoji[0]['ocMask']).getbbox())
        check.assertIsNone(emoji[1]['ocMask'])
        check.assertFalse(errors, errors)
        check.assertFalse(blocked, blocked)
        page.close()
    browser.close()
print('PASS: desktop/mobile output pixels, rotation, splice order, fit, hidden layers and payloads; no printing')
