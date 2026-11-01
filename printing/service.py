"""Shared durable queue and exclusive desktop printer ownership."""
import asyncio,hashlib,json,logging,os,re,tempfile,threading,time,uuid,sys
from pathlib import Path
from .images import page_files,UserError
from .platform import open_lock,lock_exclusive,user_id
ROOT=Path(__file__).resolve().parents[1]
_log=logging.getLogger(__name__)

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
        self.released=False;self.airprint_splice=False;self.device={};self.queue=asyncio.Queue();self.io_lock=asyncio.Lock();self.lock=asyncio.Lock();self.paused=False;self.cancel_flags={};self.device_printer=None;self._active_job=None;self._batch_verified=False
        self._locks=[];self._save_lock=threading.RLock()
        self._acquire(self.data/'service.lock')
        if not simulate:
            identity=hashlib.sha256(re.sub('[^0-9a-f]','',str(address).lower()).encode()).hexdigest()[:24]
            self._acquire(Path(tempfile.gettempdir())/f'liuying-service-{user_id()}-{identity}.lock')
        try:self.jobs=json.loads((self.data/'jobs.json').read_text())
        except FileNotFoundError:self.jobs=[]
        for job in self.jobs:
            if job['phase']=='queued':job.update(phase='cancelled',message='服务已重启，未开始的任务已取消')
            elif job['phase'] not in ('done','cancelled','rejected','aborted'):
                if job.get('mayHavePrinted') is False:
                    complete=sum(p.get('phase')=='done' for p in job.get('pages',[]))
                    job.update(phase='done' if complete and complete==len(job['pages']) else 'cancelled' if complete else 'rejected',completedPages=complete,message='服务重启；已确认页保留，其余未发送')
                else:job.update(phase='uncertain',message='上次结果未知，请在服务端检查');self.paused=True
        self.save()
    def _acquire(self,path):
        handle=open_lock(path)
        try:lock_exclusive(handle)
        except BlockingIOError:
            handle.close()
            for held in self._locks:held.close()
            raise RuntimeError('打印服务已运行；请在同一服务中启用 Web 和 AirPrint') from None
        self._locks.append(handle)
    def save(self):
        with self._save_lock:atomic(self.data/'jobs.json',json.loads(json.dumps(self.jobs)))
    def printer(self,status=False):
        from .bluetooth_printer import BluetoothPrinter
        helper=ROOT/'printing/windows_transport.py' if sys.platform=='win32' else ROOT/'build/desktop-bluetooth.app/Contents/MacOS/transport'
        return BluetoothPrinter(self.address,helper,os.environ.get('MIJIA_RFCOMM_CHANNEL','1'),self.data/'bluetooth-state',status_only=status)
    def connection(self,status=False):
        if self.device_printer is None:self.device_printer=self.printer(status)
        return self.device_printer
    def disconnect(self):
        printer,self.device_printer=self.device_printer,None
        if printer is None:return True
        try:printer.close();return True
        except Exception as error:
            self._unavailable();_log.warning('Bluetooth close failed (%s)',type(error).__name__);return False
    def available_media(self,now_ms=None):
        # connected is a recent successful probe, not a retained RFCOMM channel.
        d=self.device;media=d.get('media',0)
        if self.released or not d.get('connected') or media not in (5009,5012):return 0
        age=(int(time.time()*1000) if now_ms is None else now_ms)-d.get('checkedAt',0)
        active=self._active_job is not None and self._batch_verified
        return media if active or 0<=age<=150000 else 0
    def airprint_ready(self):
        active=self._active_job is not None and self._batch_verified
        return bool(self.available_media() and not self.paused and not any(j['phase']=='uncertain' for j in self.jobs)
                    and self.device.get('alert')=='::0' and self.device.get('ribbon',-1)!=0
                    and (active or str(self.device.get('state')) in ('20','30')))
    @staticmethod
    def _read_device(printer):
        v=printer.get_prop('printer-state','printer-state-alerts','media-size','ribbon-info')
        return dict(connected=True,state=str(v[0]),alert=v[1],media=v[2]['media-size'],ribbon=v[3].get('ribbon-info',[0,0,-1])[2],checkedAt=int(time.time()*1000))
    def _unavailable(self):
        self.device={**self.device,'connected':False,'checkedAt':int(time.time()*1000),'error':'蓝牙暂不可用，稍后自动重连'}
    @staticmethod
    async def _device_call(function,*args):
        task=asyncio.create_task(asyncio.to_thread(function,*args))
        try:return await asyncio.shield(task)
        except asyncio.CancelledError:
            try:await task
            except Exception:pass
            raise
    async def start(self,app):
        if self.simulate:await self.status()
        self.worker=asyncio.create_task(self.work())
        self.monitor=asyncio.create_task(self.monitor_status()) if not self.simulate else None
    async def monitor_status(self):
        failures=0
        while True:
            if not self.released and not self.io_lock.locked():
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
                job.update(phase='printing',message='正在连接打印机',progress=0,mayHavePrinted=False);self.save();self._active_job=job;self._batch_verified=False
                try:
                    if self.simulate:await asyncio.sleep(.05);phase='done'
                    else:phase=await self._device_call(self.send,job)
                    job.update(phase=phase,message='模拟完成（未打印）' if self.simulate else '打印完成' if phase=='done' else job.get('terminalMessage','任务已停止'),progress=100 if phase=='done' else 0)
                    self.paused=any(j['phase']=='uncertain' for j in self.jobs)
                except Exception:
                    uncertain=bool(job.get('mayHavePrinted'))
                    complete=sum(p.get('phase')=='done' for p in job.get('pages',[]))
                    phase='uncertain' if uncertain else 'done' if complete==len(job['pages']) else 'cancelled' if complete else 'rejected'
                    job.update(phase=phase,completedPages=complete,message='打印结果待核对；不会自动重印' if uncertain else '打印完成' if phase=='done' else '剩余页面未发送，请检查连接、相纸或耗材' if complete else '尚未发送：请检查连接、相纸或耗材后重新提交')
                    self.paused=any(j['phase']=='uncertain' for j in self.jobs)
                finally:self._active_job=None;self._batch_verified=False
                if job['phase']!='done' and job.get('completedPages'):
                    job['message']=f"已确认 {job['completedPages']}/{len(job['pages'])} 页；"+job['message']
                self.save()
    def send(self,job):
        cancel=self.cancel_flags[job['token']]
        if cancel.is_set():return 'cancelled'
        printer=None;confirmed=False
        try:
            printer=self.connection();self.device=self._read_device(printer);self._batch_verified=str(self.device.get('state')) in ('20','30')
            for index,page in enumerate(job['pages']):
                if cancel.is_set():confirmed=True;return 'cancelled'
                job.update(batchIndex=index+1,currentPage=index,mayHavePrinted=False)
                for key in ('jobId','terminalInfo','terminalMessage','telemetry'):job.pop(key,None)
                page['phase']='prepared';self.save()
                files=[(self.data/page['file']).read_bytes()]
                if page.get('ocFile'):files.insert(0,(self.data/page['ocFile']).read_bytes())
                def progress(record):
                    page['phase']=record['phase'];job['mayHavePrinted']=record['phase'] in ('creating','uploading')
                    if record.get('job'):page['jobId']=record['job'];job['jobId']=record['job']
                    if 'info' in record:page['terminalInfo']=record['info'];job['terminalInfo']=record['info']
                    if record.get('message'):job['terminalMessage']=record['message']
                    job['completedPages']=sum(p.get('phase')=='done' for p in job['pages']);self.save()
                def telemetry(record):
                    job['telemetry']={**job.get('telemetry',{}),**record}
                    if record.get('stage')=='transfer':
                        job['progress']=min(100,record['sentBytes']*100//max(1,record['totalBytes']))
                        job['message']=f"正在发送照片 · {job['progress']}%"
                    else:job.update(progress=-1,message='照片已发送，等待打印机完成')
                    self.save()
                try:ok=printer.print_photo(files,copies=page['copies'],sharpen=page['sharpen'],media_size=page['media'],log=lambda _:None,on_cancel=cancel.is_set,on_state=progress,on_progress=telemetry)
                except Exception:
                    job['mayHavePrinted']=printer.intent.exists() or page.get('phase')=='uploading'
                    self.save();raise
                page['phase']='done' if ok else 'cancelled' if printer.last_state==8 else 'aborted'
                job['mayHavePrinted']=False;job['completedPages']=sum(p.get('phase')=='done' for p in job['pages']);self.save()
                if not ok:confirmed=True;return page['phase']
            confirmed=True;return 'done'
        finally:
            if confirmed and printer is not None:
                try:self.device=self._read_device(printer)
                except Exception:self._unavailable()
            else:self._unavailable()
            self._batch_verified=False;self.disconnect()
    async def release(self):
        async with self.lock:
            if self.io_lock.locked() or any(j['phase'] not in ('done','cancelled','aborted','rejected') for j in self.jobs):raise UserError('请等待打印或状态读取结束，再释放蓝牙')
            self.released=True
            async with self.io_lock:await asyncio.to_thread(self.disconnect)
            self.device={**self.device,'connected':False,'released':True,'checkedAt':int(time.time()*1000)}
    async def connect(self):
        self.released=False
        self.device={**self.device,'released':False}
        await self.status()
    async def status(self):
        if self.released:return
        if self.simulate:self.device={'connected':True,'state':'30','alert':'::0','ribbon':-1,'media':5012,'checkedAt':int(time.time()*1000)};return
        if self.io_lock.locked():return
        async with self.io_lock:
            def read():
                try:value=self._read_device(self.connection(True))
                finally:closed=self.disconnect()
                if not closed:raise OSError('Bluetooth channel did not close cleanly')
                return value
            try:self.device=await self._device_call(read)
            except Exception as error:
                self._unavailable()
                raise UserError(self.device['error']) from error
    def public(self,job):
        result={k:v for k,v in job.items() if k in ('token','phase','message','progress','file','media','copies','title','orientation','createdAt','batchCount','batchIndex','jobId','completedPages','terminalInfo','telemetry')}
        index=job.get('currentPage',0)
        pages=job.get('pages',[])
        if type(index) is int and 0<=index<len(pages):
            result['previewPage']={k:pages[index][k] for k in ('file','media','orientation') if k in pages[index]}
        result['canReprint']=job.get('phase')=='done' and bool(job.get('pages'))
        if result['canReprint']:result['reprintPages']=[{k:p[k] for k in ('copies','media') if k in p} for p in job['pages']]
        return result
    async def submit(self,session,body,*,prepared_files=None):
        key=body['requestId'];pages=body['pages']
        if not isinstance(key,str) or not re.fullmatch('[A-Za-z0-9-]{16,80}',key) or not isinstance(pages,list) or not 1<=len(pages)<=6:raise UserError('打印参数无效')
        digest=hashlib.sha256(json.dumps(pages,sort_keys=True).encode()).hexdigest()
        async with self.lock:
            if self.released:raise UserError('蓝牙已释放，请先连接此设备')
            for job in self.jobs:
                if job['owner']==session['id'] and job.get('requestId')==key:
                    if job['digest']!=digest:raise UserError('请求内容已变化，请重新预览')
                    return {'ok':True,'duplicate':True,'simulated':self.simulate,'token':job['token']}
            if sum(j['phase']=='queued' for j in self.jobs)>=12:raise UserError('队列已满')
            prepared=prepared_files if prepared_files is not None else await asyncio.to_thread(lambda:[page_files(page) for page in pages]);saved=[];files=[];job=None
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
    async def reprint(self,session,body):
        if body.get('confirmed') is not True:raise UserError('请确认按原参数重新打印')
        source=next((j for j in self.jobs if j['owner']==session['id'] and j.get('token')==body.get('token')),None)
        if source is None or source['phase']!='done' or not source.get('pages'):raise UserError('只能重印本人的已完成作品')
        def load():
            pages=[];prepared=[]
            for original in source['pages']:
                def read(name,suffix):
                    path=(self.data/name).resolve()
                    if not name.startswith('prints/') or path.parent!=(self.data/'prints').resolve() or path.suffix!=suffix:raise UserError('历史作品文件无效')
                    if suffix=='.jpg' and '/private/'+name not in session['files']:raise UserError('无权读取该作品')
                    return path.read_bytes()
                jpeg=read(original['file'],'.jpg');coat=read(original['ocFile'],'.oc') if original.get('ocFile') else None
                page={k:original[k] for k in ('media','copies','sharpen','title','orientation') if k in original}
                page.update(sourceToken=source['token'],contentHash=hashlib.sha256(jpeg+(coat or b'')).hexdigest())
                pages.append(page);prepared.append((jpeg,coat))
            return pages,prepared
        pages,prepared=await asyncio.to_thread(load)
        return await self.submit(session,{'requestId':body['requestId'],'pages':pages},prepared_files=prepared)
    async def cancel(self,session):
        for job in self.jobs:
            if job['owner']==session['id']:
                if job['phase']=='queued':job.update(phase='cancelled',message='已取消等待任务')
                elif job['phase']=='printing':self.cancel_flags[job['token']].set()
                elif job['phase']=='uncertain':raise UserError('结果未知，请在服务端检查；不会重新发送')
        self.save();return {'ok':True}
    def _target(self,session,token=None,admin=False):
        if admin and (not isinstance(token,str) or not token):raise UserError('请选择需要核对的任务')
        return next((j for j in self.jobs if (admin or j['owner']==session['id']) and (token is None or j.get('token')==token) and j['phase']=='uncertain'),None)
    def _finish_page(self,job,phase,identifier=None):
        pages=job.get('pages',[]);index=job.get('currentPage',job.get('batchIndex',1)-1)
        if pages:
            if not 0<=index<len(pages):raise UserError('任务页码异常，请现场核对')
            pages[index]['phase']=phase
            if identifier:pages[index]['jobId']=identifier
            job['completedPages']=sum(p.get('phase')=='done' for p in pages)
            if phase=='done' and job['completedPages']!=len(pages):phase='cancelled'
        job.update(phase=phase,mayHavePrinted=phase=='uncertain',progress=100 if phase=='done' else 0)
        if identifier:job['jobId']=identifier
        job['message']=('原任务仍未结束，请检查打印机' if phase=='uncertain' else
            f"已确认完成 {job.get('completedPages',0)}/{len(pages)} 页；其余未发送，不会自动续打" if pages and phase=='cancelled' else job.get('terminalMessage','已确认原任务结束'))
        self.paused=any(j['phase']=='uncertain' for j in self.jobs);self.save()
    async def reconcile(self,session,token=None,admin=False):
        if self.simulate:return {'ok':True}
        own=self._target(session,token,admin)
        if own is None:return {'ok':True}
        def reconcile():
            try:
                printer=self.connection(True)
                record=json.loads(printer.intent.read_text()) if printer.intent.exists() else {}
                identifier=own.get('jobId') or record.get('job')
                if record.get('job') and own.get('jobId') and record['job']!=own['jobId']:raise UserError('待确认记录不匹配，请现场核对')
                if type(identifier)!=int or identifier<=0:raise UserError('未取得任务编号，请在服务端核对，不能自动重印')
                records=printer.client.rpc('get-job-info',{'job-id':identifier});found=[v for v in records if v.get('job-id')==identifier]
                if len(found)!=1:raise UserError('未能确认原任务，请继续保留记录')
                phase={9:'done',8:'cancelled',7:'aborted'}.get(found[0].get('job-state'),'uncertain')
                from .bluetooth_printer import terminal_info,terminal_message
                own['terminalInfo']=terminal_info(found[0]);own['terminalMessage']=terminal_message(own['terminalInfo'])
                own['jobId']=identifier;self.save()
                if phase!='uncertain':printer.intent.unlink(missing_ok=True)
                self._finish_page(own,phase,identifier)
                try:self.device=self._read_device(printer)
                except Exception:self._unavailable()
            except Exception:
                self._unavailable();raise
            finally:self.disconnect()
        async with self.io_lock:await self._device_call(reconcile)
        return {'ok':True}
    async def resolve(self,session,token,confirmed=False,admin=False):
        if confirmed is not True:raise UserError('请先现场检查打印机和已输出相纸')
        if self.io_lock.locked() or self._active_job is not None:raise UserError('请等待正在执行的操作结束')
        async with self.io_lock:
            own=self._target(session,token,admin)
            if own is None:raise UserError('未找到待核对任务')
            # Keep evidence, never upload or resume the remaining batch.
            def clear():
                key=hashlib.sha256(str(self.address).replace('-',':').upper().encode()).hexdigest()[:24]
                path=self.data/'bluetooth-state'/(key+'.json')
                if path.is_file():
                    try:record=json.loads(path.read_text())
                    except json.JSONDecodeError:record={}
                    if not isinstance(record,dict):record={}
                    if own.get('jobId') and record.get('job') and own['jobId']!=record['job']:raise UserError('记录不匹配，请继续保留')
                    path.rename(path.with_suffix('.resolved-'+str(int(time.time()*1000))))
            await asyncio.to_thread(clear)
            own.update(phase='cancelled',mayHavePrinted=False,message='已现场核对并结束记录；未发送的页面不会续打')
            self.paused=any(j['phase']=='uncertain' for j in self.jobs);self.save()
        return {'ok':True}
