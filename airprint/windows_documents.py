"""Bounded PDFium and raster conversion for the Windows service."""
import math
import struct
import threading
from PIL import Image
from .offline import Unsupported

MAX_INPUT=32*1024*1024
MAX_PIXELS=16000000
_PDF_LOCK=threading.RLock()


def _input(data):
    if not isinstance(data,bytes) or not 0<len(data)<=MAX_INPUT:raise Unsupported('Invalid document size')


def pdf_page_images(data,max_pages=2):
    _input(data)
    if type(max_pages) is not int or not 1<=max_pages<=6:raise Unsupported('At most six PDF pages')
    # PDFium cannot run concurrently even for different documents.
    with _PDF_LOCK:
        try:import pypdfium2 as pdfium
        except ImportError as error:raise Unsupported('Windows PDF support requires pypdfium2') from error
        try:
            with pdfium.PdfDocument(data) as document:
                if not 1<=len(document)<=max_pages:raise Unsupported('Too many PDF pages')
                images=[]
                for index in range(len(document)):
                    page=document[index]
                    try:
                        width,height=page.get_size()
                        if not all(math.isfinite(v) and 0<v<=14400 for v in (width,height)):raise Unsupported('PDF dimensions unsupported')
                        scale=math.nextafter(2400/max(width,height),0.0)
                        if min(width,height)*scale<1:raise Unsupported('PDF aspect ratio unsupported')
                        bitmap=page.render(scale=scale,fill_color=(255,255,255,255))
                        try:image=bitmap.to_pil().convert('RGB')
                        finally:bitmap.close()
                        if image.width*image.height>MAX_PIXELS:raise Unsupported('PDF dimensions unsupported')
                        image.info['studio_photo']=False
                        images.append(image)
                    finally:page.close()
                return images
        except Unsupported:raise
        except Exception as error:raise Unsupported('PDF could not be rendered') from error


def raster_image(data,mime):
    _input(data)
    def number(offset):return struct.unpack_from('>I',data,offset)[0]
    if mime=='image/urf':
        if len(data)<44 or data[:8]!=b'UNIRAST\0':raise Unsupported('Invalid URF header')
        if number(8)>1:raise Unsupported('Single raster page required')
        width,height=number(24),number(28);channels={0:1,1:3}.get(data[13],0);offset=44
        if data[12]!=channels*8 or data[14]>1:raise Unsupported('Unsupported URF encoding')
    elif mime=='image/pwg-raster':
        if len(data)<1800 or data[:4]!=b'RaS2':raise Unsupported('Invalid PWG header')
        width,height=number(376),number(380);channels={18:1,19:3}.get(number(404),0);offset=1800
        if number(388)!=8 or number(392)!=channels*8 or number(396)!=width*channels or number(400)!=0 or number(276)!=0:raise Unsupported('Unsupported PWG encoding')
    else:raise Unsupported('Unsupported raster format')
    if not channels or not 1<=width<=10000 or not 1<=height<=10000 or width*height>MAX_PIXELS:raise Unsupported('Raster dimensions unsupported')
    source=memoryview(data)
    def read(count):
        nonlocal offset
        if offset+count>len(source):raise Unsupported('Truncated raster data')
        value=source[offset:offset+count];offset+=count;return value
    output=bytearray(width*height*channels);row_size=width*channels;y=0
    while y<height:
        repeat=read(1)[0]+1
        if y+repeat>height:raise Unsupported('Invalid raster row repeat')
        row=bytearray();x=0
        while x<width:
            code=read(1)[0]
            if code==128:row.extend(b'\xff'*((width-x)*channels));break
            count=code+1 if code<128 else 257-code
            if count>width-x:raise Unsupported('Invalid raster pixel run')
            row.extend(bytes(read(channels))*count if code<128 else read(channels*count));x+=count
        for line in range(y,y+repeat):output[line*row_size:(line+1)*row_size]=row
        y+=repeat
    if offset!=len(data):raise Unsupported('Multiple raster pages unsupported')
    image=Image.frombytes('RGB' if channels==3 else 'L',(width,height),bytes(output)).convert('RGB')
    image.info['studio_photo']=False
    return image
