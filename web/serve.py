"""Serve the shared editor with an independent desktop backend."""
import argparse,asyncio,threading,hashlib,io,json,os,re,secrets,socket,tempfile,time,uuid
from pathlib import Path
from aiohttp import web
from images import decode,page_files,cutout,UserError

ROOT=Path(__file__).resolve().parents[1]
HEADERS={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'same-origin','X-Frame-Options':'DENY','Content-Security-Policy':"default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; form-action 'self'; object-src 'none'"}

def atomic(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(dir=path.parent,prefix='.write-')
    try:
        with os.fdopen(fd,'w') as out:json.dump(value,out);out.flush();os.fsync(out.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)

class Studio:
    def __init__(self,data,simulate=False,address=None):
        self.data=Path(data);self.data.mkdir(parents=True,exist_ok=True,mode=0o700);self.simulate=simulate;self.address=address
        self.code=f'{secrets.randbelow(1000000):06}';self.sessions={};self.failures=0;self.blocked_until=0;self.device={};self.queue=asyncio.Queue();self.io_lock=asyncio.Lock();self.lock=asyncio.Lock();self.paused=False;self.cancel_flags={}
        try:self.jobs=json.loads((self.data/'jobs.json').read_text())
        except FileNotFoundError:self.jobs=[]
        for job in self.jobs:
            if job['phase']=='queued':job.update(phase='cancelled',message='服务已重启，未开始的任务已取消')
            elif job['phase'] not in ('done','cancelled','rejected','aborted'):job.update(phase='uncertain',message='上次结果未知，请在服务端检查');self.paused=True
        self.save()
    def save(self):atomic(self.data/'jobs.json',self.jobs)
    def printer(self,status=False):
        from bluetooth_printer import BluetoothPrinter
        return BluetoothPrinter(self.address,ROOT/'build/desktop-bluetooth.app/Contents/MacOS/transport',os.environ.get('MIJIA_RFCOMM_CHANNEL','1'),self.data/'bluetooth-state',status_only=status)
    async def start(self,app):self.worker=asyncio.create_task(self.work())
    async def stop(self,app):
        for job in self.jobs:
            if job['phase']=='queued':job.update(phase='cancelled',message='服务停止，尚未开始的任务已取消')
        self.save();self.worker.cancel()
        try:await self.worker
        except asyncio.CancelledError:pass
    async def work(self):
        while True:
            job=await self.queue.get()
            while self.paused:await asyncio.sleep(.3)
            if job['phase']!='queued':continue
            async with self.io_lock:
                job.update(phase='printing',message='正在打印',progress=0);self.save()
                try:
                    if self.simulate:await asyncio.sleep(.05);phase='done'
                    else:phase=await asyncio.to_thread(self.send,job)
                    job.update(phase=phase,message='模拟完成（未打印）' if self.simulate else '打印完成' if phase=='done' else '任务已停止',progress=100 if phase=='done' else 0)
                    if phase=='aborted':self.paused=True
                except Exception:
                    job.update(phase='uncertain',message='打印未完成，请检查设备；不会自动重印');self.paused=True
                self.save()
    def send(self,job):
        cancel=self.cancel_flags[job['token']]
        if cancel.is_set():return 'cancelled'
        printer=self.printer()
        try:
            for page in job['pages']:
                if cancel.is_set():return 'cancelled'
                files=[(self.data/page['file']).read_bytes()]
                if page.get('ocFile'):files.insert(0,(self.data/page['ocFile']).read_bytes())
                if not printer.print_photo(files,copies=page['copies'],sharpen=page['sharpen'],media_size=page['media'],log=lambda _:None,on_cancel=cancel.is_set):return 'cancelled' if printer.last_state==8 else 'aborted'
            return 'done'
        finally:printer.close()
    async def status(self):
        if self.simulate:self.device={'connected':True,'state':'30','alert':'::0','ribbon':-1,'checkedAt':int(time.time()*1000)};return
        async with self.io_lock:
            def read():
                p=self.printer(True)
                try:
                    v=p.get_prop('printer-state','printer-state-alerts','media-size','ribbon-info');return dict(connected=True,state=str(v[0]),alert=v[1],media=v[2]['media-size'],ribbon=v[3].get('ribbon-info',[0,0,-1])[2],checkedAt=int(time.time()*1000))
                finally:p.close()
            self.device=await asyncio.to_thread(read)
    def public(self,job):return {k:v for k,v in job.items() if k in ('token','phase','message','progress','file','media','copies','title','orientation','createdAt','batchCount','batchIndex','jobId')}
    async def submit(self,session,body):
        key=body['requestId'];pages=body['pages']
        if not isinstance(key,str) or not re.fullmatch('[A-Za-z0-9-]{16,80}',key) or not isinstance(pages,list) or not 1<=len(pages)<=6:raise UserError('打印参数无效')
        digest=hashlib.sha256(json.dumps(pages,sort_keys=True).encode()).hexdigest()
        async with self.lock:
            for job in self.jobs:
                if job['owner']==session['id'] and job['requestId']==key:
                    if job['digest']!=digest:raise UserError('请求内容已变化，请重新预览')
                    return {'ok':True,'duplicate':True,'simulated':self.simulate}
            if sum(j['phase']=='queued' for j in self.jobs)>=12:raise UserError('队列已满')
            prepared=await asyncio.to_thread(lambda:[page_files(page) for page in pages]);saved=[];files=[];job=None
            try:
                for page,(jpeg,coat) in zip(pages,prepared):
                    name='prints/'+str(uuid.uuid4());target=self.data/(name+'.jpg');target.parent.mkdir(exist_ok=True);target.write_bytes(jpeg);files.append(target)
                    item={k:page[k] for k in ('media','title','orientation') if k in page};item.update(file=name+'.jpg',copies=page.get('copies',1),sharpen=page.get('sharpen',0))
                    if coat is not None:target=self.data/(name+'.oc');target.write_bytes(coat);files.append(target);item['ocFile']=name+'.oc'
                    saved.append(item)
                job={**saved[0],'owner':session['id'],'requestId':key,'digest':digest,'token':str(uuid.uuid4()),'pages':saved,'phase':'queued','message':'等待打印','progress':0,'createdAt':int(time.time()*1000),'batchCount':len(saved),'batchIndex':1};self.jobs.append(job);self.save()
                for page in saved:session['files'].add('/private/'+page['file'])
                self.cancel_flags[job['token']]=threading.Event();await self.queue.put(job);return {'ok':True,'simulated':self.simulate}
            except Exception:
                if job is not None and job in self.jobs:self.jobs.remove(job)
                for file in files:file.unlink(missing_ok=True)
                raise
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
                own=[j for j in self.jobs if j['owner']==session['id']];waiting=[j for j in own if j['phase'] in ('queued','printing','uncertain')];job=waiting[0] if waiting else own[-1] if own else {};public=self.public(job)
                if job.get('phase')=='queued' and self.paused:public['message']='共享队列已暂停，请在服务端检查'
                return web.json_response(dict(permission=True,host='desktop',simulation=self.simulate,busy=job.get('phase')=='printing',unresolved=bool(waiting),job=public,history=[self.public(j) for j in reversed(own) if j['phase']=='done'][:20],device=self.device,message=public.get('message','电脑共享服务已连接')))
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
            async with self.io_lock:image=await asyncio.to_thread(decode,data)
            name='photos/'+str(uuid.uuid4())+'.jpg';path=self.data/name;path.parent.mkdir(exist_ok=True);await asyncio.to_thread(image.save,path,'JPEG',quality=97);src='/private/'+name;session['files'].add(src);session['bytes']+=len(data)
            return web.json_response(dict(src=src,width=image.width,height=image.height))
        if (r.content_length or 0)>(18000000 if r.path=='/api/print' else 4096):raise web.HTTPRequestEntityTooLarge(max_size=18000000,actual_size=r.content_length)
        raw=await r.read()
        if len(raw)>(18000000 if r.path=='/api/print' else 4096):raise UserError('请求过大')
        body=json.loads(raw)
        if r.path=='/api/print':return web.json_response(await self.submit(session,body))
        if r.path=='/api/cutout':
            source=body['source']
            if source not in session['files'] or not source.startswith(('/private/photos/','/private/prints/')):raise UserError('照片不存在')
            async with self.io_lock:outputs=await asyncio.to_thread(cutout,self.data/source[9:],self.data/'cutouts',ROOT/'assets/models/u2netp.onnx')
            result={c:'/private/cutouts/'+p.name for c,p in outputs.items()};session['files'].update(result.values());return web.json_response({'images':result})
        if r.path=='/api/connect':await self.status();return web.json_response({'ok':True})
        if r.path=='/api/cancel':
            for job in self.jobs:
                if job['owner']==session['id']:
                    if job['phase']=='queued':job.update(phase='cancelled',message='已取消等待任务')
                    elif job['phase']=='printing':self.cancel_flags[job['token']].set()
                    elif job['phase']=='uncertain':raise UserError('结果未知，请在服务端检查；不会重新发送')
            self.save();return web.json_response({'ok':True})
        if r.path=='/api/reconcile':
            if self.simulate:return web.json_response({'ok':True})
            own=next((j for j in self.jobs if j['owner']==session['id'] and j['phase']=='uncertain'),None)
            if own is None:return web.json_response({'ok':True})
            def reconcile():
                printer=self.printer(True)
                try:
                    if not printer.intent.exists():raise UserError('未发现待确认记录，请在打印机端核对结果')
                    record=json.loads(printer.intent.read_text());identifier=record.get('job')
                    if type(identifier)!=int or identifier<=0:raise UserError('未取得任务编号，请在服务端核对，不能自动重印')
                    records=printer.client.rpc('get-job-info',{'job-id':identifier});found=[v for v in records if v.get('job-id')==identifier]
                    if len(found)!=1:raise UserError('未能确认原任务，请继续保留记录')
                    phase={9:'done',8:'cancelled',7:'aborted'}.get(found[0].get('job-state'),'uncertain')
                    if phase!='uncertain':printer.intent.unlink()
                    return phase,identifier
                finally:printer.close()
            async with self.io_lock:phase,identifier=await asyncio.to_thread(reconcile)
            own.update(phase=phase,jobId=identifier,message='已确认原任务结束' if phase!='uncertain' else '原任务仍未结束，请检查打印机')
            self.paused=any(j['phase']=='uncertain' for j in self.jobs);self.save();return web.json_response({'ok':True})
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
