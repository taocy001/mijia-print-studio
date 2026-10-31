"""Bounded document conversion; no device access."""
import sys,json,resource,base64,io
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from airprint import offline
from airprint.documents import prepare_document,pdf_page_images
from PIL import Image
resource.setrlimit(resource.RLIMIT_CPU,(20,20))
args=json.loads(sys.stdin.buffer.readline(4096))
data=sys.stdin.buffer.read(32*1024*1024+1)
if len(data)>32*1024*1024:raise ValueError('document too large')
media=args['media'];mime=args['mime'];scaling=args['scaling'];orientation=args.get('orientation')
if media==5009:offline.CANVAS=(1040,1040)
images=None;pdfs=None
if mime=='application/pdf':
    from pypdf import PdfReader,PdfWriter
    reader=PdfReader(io.BytesIO(data))
    if reader.is_encrypted or not 1<=len(reader.pages)<=6:raise ValueError('PDF must contain 1 to 6 unencrypted pages')
    if media==5014:images=pdf_page_images(data,6)
    else:
        pdfs=[]
        for page in reader.pages:
            writer=PdfWriter();writer.add_page(page);buffer=io.BytesIO();writer.write(buffer);pdfs.append(buffer.getvalue())
elif media==5014:
    if mime=='image/jpeg':images=[offline.load_jpeg_pil(data)]
    else:raise ValueError('splice requires JPEG or PDF')
if media==5014:
    output=[offline.compose_splice(images[i:i+2],scaling=scaling) for i in range(0,len(images),2)]
elif pdfs is not None:
    output=[prepare_document(pdf,mime,scaling=scaling,orientation=orientation) for pdf in pdfs]
else:output=[prepare_document(data,mime,scaling=scaling,orientation=orientation)]
if media==5009:output=[offline.rotate180_pi(im) for im in output]
print(json.dumps([{'media':media,'copies':1,'sharpen':0,'base64':base64.b64encode(im.jpeg).decode()} for im in output]))
