"""Image preparation shared by the desktop HTTP endpoints."""
import base64,hashlib,io,struct,subprocess,sys,tempfile,zlib
from pathlib import Path
from PIL import Image,ImageOps

class UserError(ValueError):pass

def decode(data):
    try:
        image=Image.open(io.BytesIO(data));image.load()
    except Exception:
        if sys.platform!='darwin' or len(data)<12 or data[4:8]!=b'ftyp':raise UserError('无法读取照片') from None
        with tempfile.TemporaryDirectory(prefix='liuying-image-') as folder:
            src=Path(folder)/'input.heic';dst=Path(folder)/'output.png';src.write_bytes(data)
            subprocess.run(['/usr/bin/sips','-s','format','png',str(src),'--out',str(dst)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=30)
            image=Image.open(dst);image.load()
    image=ImageOps.exif_transpose(image).convert('RGB');image.thumbnail((2400,2400));return image

def page_files(page):
    media=page.get('media');size=(1040,1040) if media==5009 else (1216,1824)
    if type(media)!=int or media not in (5009,5012,5014):raise UserError('相纸类型不支持')
    copies=page.get('copies',1);sharp=page.get('sharpen',0)
    if type(copies)!=int or not 1<=copies<=10 or type(sharp)!=int or not 0<=sharp<=2:raise UserError('打印参数无效')
    def read(value):
        if not isinstance(value,str) or len(value)>1500000:raise UserError('图片过大')
        data=base64.b64decode(value,validate=True)
        if len(data)>1048576:raise UserError('图片过大')
        return data
    jpeg=read(page['base64'])
    with Image.open(io.BytesIO(jpeg)) as image:
        if image.format!='JPEG' or image.size!=size:raise UserError('打印图片尺寸或格式不正确')
        image.verify()
    coat=None
    if page.get('ocMask'):
        threshold=page.get('threshold',100)
        if type(threshold)!=int or not 60<=threshold<=140:raise UserError('覆膜参数无效')
        with Image.open(io.BytesIO(read(page['ocMask']))) as image:
            if image.size!=size:raise UserError('覆膜尺寸不正确')
            red=image.convert('RGB').getchannel('R');raw=red.point(lambda x:255 if x>=100 else 0).tobytes()
        compressor=zlib.compressobj(6,zlib.DEFLATED,-15);packed=compressor.compress(raw)+compressor.flush()
        coat=b'ocpattern1\0\0'+struct.pack('>IIIIBBH',*size,len(packed),1,threshold+60,threshold-20,0)+packed
    return jpeg,coat

def cutout(source,directory,model):
    import numpy as np
    import onnxruntime as ort
    if not model.is_file():raise UserError('请先下载离线模型：python3 fetch_deps.py')
    data=source.read_bytes();key='u2netp-v1-'+hashlib.sha256(data).hexdigest();outputs={c:directory/(key+'-'+c+'.jpg') for c in ['white','blue','red']}
    if all(p.is_file() for p in outputs.values()):return outputs
    photo=Image.open(io.BytesIO(data)).convert('RGB');small=np.asarray(photo.resize((320,320),Image.Resampling.BILINEAR),dtype=np.float32)
    value=small/max(float(small.max()),1);value=(value-np.array([.485,.456,.406],np.float32))/np.array([.229,.224,.225],np.float32)
    session=ort.InferenceSession(str(model),providers=['CPUExecutionProvider']);mask=session.run(['1959'],{session.get_inputs()[0].name:value.transpose(2,0,1)[None]})[0].squeeze()
    low,high=float(mask.min()),float(mask.max())
    if not np.isfinite(mask).all() or high-low<1e-6:raise UserError('未识别出清晰主体，请换一张照片')
    alpha=Image.fromarray(np.rint((mask-low)/(high-low)*255).astype('uint8')).resize(photo.size,Image.Resampling.BILINEAR);directory.mkdir(parents=True,exist_ok=True)
    for name,color in [('white','#ffffff'),('blue','#438edb'),('red','#ff0000')]:Image.composite(photo,Image.new('RGB',photo.size,color),alpha).save(outputs[name],'JPEG',quality=97)
    return outputs
