"""Shared durable queue and exclusive desktop printer ownership."""
import asyncio,fcntl,hashlib,json,os,re,tempfile,threading,time,uuid
from pathlib import Path
from .images import page_files,UserError
ROOT=Path(__file__).resolve().parents[1]

def atomic(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(dir=path.parent,prefix='.write-')
    try:
        with os.fdopen(fd,'w') as out:json.dump(value,out);out.flush();os.fsync(out.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)

class PrintService:
    def __init__(self,data,simulate=False,address=None):
        self.data=Path(data);self.data.mkdir(parents=True,exist_ok=True,mode=0o700);self.simulate=simulate;self.address=address
        self.device={};self.queue=asyncio.Queue();self.io_lock=asyncio.Lock();self.lock=asyncio.Lock();self.paused=False;self.cancel_flags={};self.device_printer=None
        self._locks=[]
        self._acquire(self.data/'service.lock')
        if not simulate:
            identity=hashlib.sha256(re.sub('[^0-9a-f]','',str(address).lower()).encode()).hexdigest()[:24]
            self._acquire(Path(tempfile.gettempdir())/f'liuying-service-{os.getuid()}-{identity}.lock')
        try:self.jobs=json.loads((self.data/'jobs.json').read_text())
        except FileNotFoundError:self.jobs=[]
        for job in self.jobs:
            if job['phase']=='queued':job.update(phase='cancelled',message='服务已重启，未开始的任务已取消')
            elif job['phase'] not in ('done','cancelled','rejected','aborted'):job.update(phase='uncertain',message='上次结果未知，请在服务端检查');self.paused=True
        self.save()
    def _acquire(self,path):
        handle=open(path,'a+')
        try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            handle.close()
            for held in self._locks:held.close()
            raise RuntimeError('打印服务已运行；请在同一服务中启用 Web 和 AirPrint') from None
        self._locks.append(handle)
    def save(self):atomic(self.data/'jobs.json',self.jobs)
    def printer(self,status=False):
        from .bluetooth_printer import BluetoothPrinter
        return BluetoothPrinter(self.address,ROOT/'build/desktop-bluetooth.app/Contents/MacOS/transport',os.environ.get('MIJIA_RFCOMM_CHANNEL','1'),self.data/'bluetooth-state',status_only=status)
    def connection(self,status=False):
        if self.device_printer is None:self.device_printer=self.printer(status)
        return self.device_printer
    def disconnect(self):
        printer,self.device_printer=self.device_printer,None
        if printer is not None:printer.close()
    async def start(self,app):
        self.worker=asyncio.create_task(self.work())
        self.monitor=asyncio.create_task(self.monitor_status()) if not self.simulate else None
    async def monitor_status(self):
        failures=0
        while True:
            if not self.io_lock.locked():
                try:await self.status();failures=0
                except Exception:failures=min(failures+1,4)
            await asyncio.sleep(min(120,15*2**(failures-1)) if failures else 60)
    async def stop(self,app):
        if getattr(self,'monitor',None):
            self.monitor.cancel()
            try:await self.monitor
            except asyncio.CancelledError:pass
        for job in self.jobs:
            if job['phase']=='queued':job.update(phase='cancelled',message='服务停止，尚未开始的任务已取消')
        self.save()
        async with self.io_lock:await asyncio.to_thread(self.disconnect)
        self.worker.cancel()
        try:await self.worker
        except asyncio.CancelledError:pass
        for held in self._locks:held.close()
        self._locks=[]
    async def work(self):
        while True:
            job=await self.queue.get()
            while self.paused:await asyncio.sleep(.3)
            if job['phase']!='queued':continue
            async with self.io_lock:
                if job['phase']!='queued':continue
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
        printer=self.connection()
        try:
            for page in job['pages']:
                if cancel.is_set():return 'cancelled'
                files=[(self.data/page['file']).read_bytes()]
                if page.get('ocFile'):files.insert(0,(self.data/page['ocFile']).read_bytes())
                if not printer.print_photo(files,copies=page['copies'],sharpen=page['sharpen'],media_size=page['media'],log=lambda _:None,on_cancel=cancel.is_set):return 'cancelled' if printer.last_state==8 else 'aborted'
            return 'done'
        except Exception:
            self.disconnect();raise
    async def status(self):
        if self.simulate:self.device={'connected':True,'state':'30','alert':'::0','ribbon':-1,'media':5012,'checkedAt':int(time.time()*1000)};return
        if self.io_lock.locked():return
        async with self.io_lock:
            def read():
                p=self.connection(True)
                try:
                    v=p.get_prop('printer-state','printer-state-alerts','media-size','ribbon-info');return dict(connected=True,state=str(v[0]),alert=v[1],media=v[2]['media-size'],ribbon=v[3].get('ribbon-info',[0,0,-1])[2],checkedAt=int(time.time()*1000))
                except Exception:
                    self.disconnect();raise
            task=asyncio.create_task(asyncio.to_thread(read))
            try:self.device=await asyncio.shield(task)
            except asyncio.CancelledError:
                try:await task
                except Exception:pass
                raise
            except Exception as error:
                self.device={**self.device,'connected':False,'checkedAt':int(time.time()*1000),'error':'蓝牙暂不可用，稍后自动重连'}
                raise UserError(self.device['error']) from error
    def public(self,job):return {k:v for k,v in job.items() if k in ('token','phase','message','progress','file','media','copies','title','orientation','createdAt','batchCount','batchIndex','jobId')}
    async def submit(self,session,body):
        key=body['requestId'];pages=body['pages']
        if not isinstance(key,str) or not re.fullmatch('[A-Za-z0-9-]{16,80}',key) or not isinstance(pages,list) or not 1<=len(pages)<=6:raise UserError('打印参数无效')
        digest=hashlib.sha256(json.dumps(pages,sort_keys=True).encode()).hexdigest()
        async with self.lock:
            for job in self.jobs:
                if job['owner']==session['id'] and job['requestId']==key:
                    if job['digest']!=digest:raise UserError('请求内容已变化，请重新预览')
                    return {'ok':True,'duplicate':True,'simulated':self.simulate,'token':job['token']}
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
                self.cancel_flags[job['token']]=threading.Event();await self.queue.put(job);return {'ok':True,'simulated':self.simulate,'token':job['token']}
            except Exception:
                if job is not None and job in self.jobs:self.jobs.remove(job)
                for file in files:file.unlink(missing_ok=True)
                raise
    async def cancel(self,session):
        for job in self.jobs:
            if job['owner']==session['id']:
                if job['phase']=='queued':job.update(phase='cancelled',message='已取消等待任务')
                elif job['phase']=='printing':self.cancel_flags[job['token']].set()
                elif job['phase']=='uncertain':raise UserError('结果未知，请在服务端检查；不会重新发送')
        self.save();return {'ok':True}
    async def reconcile(self,session):
        if self.simulate:return {'ok':True}
        own=next((j for j in self.jobs if j['owner']==session['id'] and j['phase']=='uncertain'),None)
        if own is None:return {'ok':True}
        def reconcile():
            printer=self.connection(True)
            try:
                if not printer.intent.exists():raise UserError('未发现待确认记录，请在打印机端核对结果')
                record=json.loads(printer.intent.read_text());identifier=record.get('job')
                if type(identifier)!=int or identifier<=0:raise UserError('未取得任务编号，请在服务端核对，不能自动重印')
                records=printer.client.rpc('get-job-info',{'job-id':identifier});found=[v for v in records if v.get('job-id')==identifier]
                if len(found)!=1:raise UserError('未能确认原任务，请继续保留记录')
                phase={9:'done',8:'cancelled',7:'aborted'}.get(found[0].get('job-state'),'uncertain')
                if phase!='uncertain':printer.intent.unlink()
                return phase,identifier
            except Exception:
                self.disconnect();raise
        async with self.io_lock:phase,identifier=await asyncio.to_thread(reconcile)
        own.update(phase=phase,jobId=identifier,message='已确认原任务结束' if phase!='uncertain' else '原任务仍未结束，请检查打印机')
        self.paused=any(j['phase']=='uncertain' for j in self.jobs);self.save();return {'ok':True}
