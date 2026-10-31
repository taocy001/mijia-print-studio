"""Serve the shared editor with an independent desktop backend."""
import argparse,asyncio,json,os,re,secrets,time,uuid
from pathlib import Path
from aiohttp import web
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from printing.images import decode,cutout,UserError
from printing.service import PrintService

ROOT=Path(__file__).resolve().parents[1]
HEADERS={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'same-origin','X-Frame-Options':'DENY','Content-Security-Policy':"default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; form-action 'self'; object-src 'none'"}

class Studio:
    def __init__(self,data=None,simulate=False,address=None,*,core=None):
        self.core=core or PrintService(data,simulate,address)
        self.owns_core=core is None
        self.data=self.core.data;self.simulate=self.core.simulate
        self.code=f'{secrets.randbelow(1000000):06}';self.sessions={};self.failures=0;self.blocked_until=0
    async def start(self,app):
        if self.owns_core:await self.core.start(app)
    async def stop(self,app):
        if self.owns_core:await self.core.stop(app)
    async def handle(self,r):
        if r.method not in ('GET','POST'):raise web.HTTPMethodNotAllowed(r.method,['GET','POST'])
        address,port=r.transport.get_extra_info('sockname')[:2];allowed={f'{address}:{port}'}
        if address=='127.0.0.1':allowed.add(f'localhost:{port}')
        if r.host not in allowed or r.method=='POST' and r.headers.get('Origin')!='http://'+r.host:raise web.HTTPForbidden()
        if r.path=='/api/pair' and r.method=='POST':
            if (r.content_length or 0)>4096:raise web.HTTPRequestEntityTooLarge(max_size=4096,actual_size=r.content_length)
            code=(await r.post()).get('code','')
            if time.monotonic()<self.blocked_until or len(self.sessions)>=12 or not code.isascii() or not secrets.compare_digest(code,self.code):
                self.failures+=1
                if self.failures>=5:self.blocked_until=time.monotonic()+60;self.failures=0
                return web.Response(text=self.pair_page('配对码不正确或请求过多，请稍后重试'),content_type='text/html',status=403)
            self.failures=0;token=secrets.token_urlsafe(48);self.sessions[token]={'id':str(uuid.uuid4()),'files':set(),'bytes':0}
            response=web.HTTPSeeOther('/');response.set_cookie('liuying',token,httponly=True,samesite='Strict');return response
        session=self.sessions.get(r.cookies.get('liuying'))
        if not session:
            if r.path=='/' and r.method=='GET':return web.Response(text=self.pair_page('输入服务端显示的配对码'),content_type='text/html')
            return web.json_response({'error':'请重新配对'},status=401)
        if r.method=='GET':
            if r.path=='/api/state':
                own=[j for j in self.core.jobs if j['owner']==session['id']];waiting=[j for j in own if j['phase'] in ('queued','printing','uncertain')];job=waiting[0] if waiting else own[-1] if own else {};public=self.core.public(job)
                if job.get('phase')=='queued' and self.core.paused:public['message']='共享队列已暂停，请在服务端检查'
                return web.json_response(dict(permission=True,host='desktop',simulation=self.simulate,busy=job.get('phase')=='printing',unresolved=bool(waiting),job=public,history=[self.core.public(j) for j in reversed(own) if j['phase']=='done'][:20],device=self.core.device,message=public.get('message','电脑共享服务已连接')))
            if r.path=='/session.js':return web.Response(text='window.STUDIO_DRAFT_KEY='+json.dumps('liuying-draft-'+session['id'])+';',content_type='application/javascript')
            if r.path.startswith('/private/'):
                if r.path not in session['files']:raise web.HTTPNotFound()
                return web.FileResponse(self.data/r.path[9:])
            name=r.path.lstrip('/') or 'index.html';path=ROOT/'assets'/name
            if not (re.fullmatch(r'[a-z0-9-]+\.(js|css|html)',name) or name=='sample.svg' or re.fullmatch(r'emoji/[a-f0-9-]+\.svg',name) or name in ('fonts/MaShanZheng-Regular.ttf','fonts/ZCOOLKuaiLe-Regular.ttf')) or not path.is_file():raise web.HTTPNotFound()
            return web.FileResponse(path)
        if r.path=='/api/upload':
            data=await r.read()
            if session['bytes']+len(data)>120*1024*1024 or len(session['files'])>=60:raise UserError('照片已达本次会话上限')
            async with self.core.io_lock:image=await asyncio.to_thread(decode,data)
            name='photos/'+str(uuid.uuid4())+'.jpg';path=self.data/name;path.parent.mkdir(exist_ok=True);await asyncio.to_thread(image.save,path,'JPEG',quality=97);src='/private/'+name;session['files'].add(src);session['bytes']+=len(data)
            return web.json_response(dict(src=src,width=image.width,height=image.height))
        if (r.content_length or 0)>(18000000 if r.path=='/api/print' else 4096):raise web.HTTPRequestEntityTooLarge(max_size=18000000,actual_size=r.content_length)
        raw=await r.read()
        if len(raw)>(18000000 if r.path=='/api/print' else 4096):raise UserError('请求过大')
        body=json.loads(raw)
        if r.path=='/api/print':return web.json_response(await self.core.submit(session,body))
        if r.path=='/api/cutout':
            source=body['source']
            if source not in session['files'] or not source.startswith(('/private/photos/','/private/prints/')):raise UserError('照片不存在')
            async with self.core.io_lock:outputs=await asyncio.to_thread(cutout,self.data/source[9:],self.data/'cutouts',ROOT/'assets/models/u2netp.onnx')
            result={c:'/private/cutouts/'+p.name for c,p in outputs.items()};session['files'].update(result.values());return web.json_response({'images':result})
        if r.path=='/api/connect':await self.core.status();return web.json_response({'ok':True})
        if r.path=='/api/cancel':return web.json_response(await self.core.cancel(session))
        if r.path=='/api/reconcile':return web.json_response(await self.core.reconcile(session))
        raise web.HTTPNotFound()
    def pair_page(self,message):return f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>留影工坊</title><style>:root{{color-scheme:light dark;font:16px system-ui}}body{{max-width:360px;margin:18vh auto;padding:24px}}input,button{{box-sizing:border-box;width:100%;padding:16px;margin:12px 0;border-radius:12px;font:inherit}}button{{background:#d5ba76;color:#222;border:0}}</style><h1>留影工坊</h1><p>{message}</p><form method="post" action="/api/pair"><input name="code" inputmode="numeric" pattern="[0-9]{{6}}" maxlength="6" required placeholder="6 位配对码"><button>连接</button></form></html>'''

@web.middleware
async def responses(request,handler):
    try:response=await handler(request)
    except web.HTTPException as error:response=error
    except UserError as error:response=web.json_response({'error':str(error)},status=409)
    except (ValueError,KeyError,TypeError):response=web.json_response({'error':'请求无效，请检查图片和参数'},status=409)
    except Exception:response=web.json_response({'error':'操作未完成，请检查服务端和设备状态'},status=409)
    response.headers.update(HEADERS);return response

def app(studio):
    server=web.Application(client_max_size=25*1024*1024,middlewares=[responses]);server.router.add_route('*','/{path:.*}',studio.handle);server.on_startup.append(studio.start);server.on_cleanup.append(studio.stop);return server

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--lan',action='store_true');parser.add_argument('--port',type=int,default=8635);parser.add_argument('--simulate',action='store_true');parser.add_argument('--data',type=Path,default=Path.home()/'Library/Application Support/LiuyingStudio');args=parser.parse_args()
    address=os.environ.get('MIJIA_BLUETOOTH_ADDRESS')
    if not args.simulate and not address:parser.error('请设置 MIJIA_BLUETOOTH_ADDRESS；仅测试网页可使用 --simulate')
    studio=Studio(args.data,args.simulate,address);print('配对码：'+studio.code,flush=True)
    if args.simulate:print('模拟模式：不会连接打印机或实际打印。',flush=True)
    web.run_app(app(studio),host='0.0.0.0' if args.lan else '127.0.0.1',port=args.port,access_log=None)
if __name__=='__main__':main()
