"""Render web icons from the Android launcher vector."""
from pathlib import Path
import xml.etree.ElementTree as ET
from playwright.sync_api import sync_playwright

root=Path(__file__).resolve().parents[1]
android='{http://schemas.android.com/apk/res/android}'
vector=ET.parse(root/'res/drawable/icon.xml').getroot()
svg=ET.Element('svg',xmlns='http://www.w3.org/2000/svg',viewBox=f"0 0 {vector.get(android+'viewportWidth')} {vector.get(android+'viewportHeight')}")
for path in vector:
    ET.SubElement(svg,'path',d=path.get(android+'pathData'),fill=path.get(android+'fillColor'),opacity=path.get(android+'fillAlpha','1'))
with sync_playwright() as p:
    browser=p.chromium.launch()
    for size,name in [(180,'apple-touch-icon.png'),(32,'favicon.png')]:
        page=browser.new_page(viewport={'width':size,'height':size},device_scale_factor=1)
        page.set_content('<style>html,body{margin:0;width:100%;height:100%}svg{display:block;width:100%;height:100%}</style>'+ET.tostring(svg,encoding='unicode'))
        page.locator('svg').screenshot(path=str(root/'assets'/name))
        page.close()
    browser.close()
