"""IPP entrypoint backed by the shared print service."""
import asyncio,base64,hashlib,ipaddress,json,struct,sys,time,uuid
from pathlib import Path
from aiohttp import web
from printing.images import UserError
from printing.service import atomic
from .capabilities import Capabilities,IppFailure,integer
from .offline import Attribute as A,Message,Unsupported,decode_ipp,encode_ipp

STATES={'receiving':4,'rendering':4,'queued':3,'printing':5,'uncertain':6,'done':9,'cancelled':7,'aborted':8,'rejected':8}
TERMINAL=('done','cancelled','aborted','rejected')

class AirPrint(Capabilities):
    def __init__(self,core,uri,*,paper='auto'):
        self.core,self.uri,self.paper=core,uri,paper
        self.identity='urn:uuid:'+str(uuid.uuid5(uuid.NAMESPACE_URL,uri))
        self.started=time.monotonic();self.gate=asyncio.Lock()
        self.path=core.data/'airprint.json'
        try:self.rows=json.loads(self.path.read_text())
        except FileNotFoundError:self.rows=[]
        for row in self.rows:
            if not self.job(row) and row['phase'] not in TERMINAL:
                row.update(phase='aborted',message='Service restarted; not replayed')
        self.save()
    @property
    def media(self):
        if self.paper!='auto':return {'square':5009,'six':5012,'splice':5014}[self.paper]
        return self.core.device.get('media',5012)
    def save(self):atomic(self.path,self.rows)
    def job(self,row):return next((j for j in self.core.jobs if j['requestId']==row['key'] and j['owner']==row['owner']),None)
    def phase(self,row):return (self.job(row) or row)['phase']
    def attributes(self,row):
        phase=self.phase(row);state=STATES[phase]
        reasons={9:b'job-completed-successfully',7:b'job-canceled-by-user',8:b'aborted-by-system',6:b'job-stopped',4:b'job-incoming'}
        return [A(2,0x21,'job-id',integer(row['id'])),A(2,0x45,'job-uri',f"{self.uri}/jobs/{row['id']}".encode()),A(2,0x23,'job-state',integer(state)),A(2,0x44,'job-state-reasons',reasons.get(state,b'none')),A(2,0x41,'job-state-message',(self.job(row) or row).get('message',phase).encode()[:255])]
    def find(self,req,owner):
        identifier=self._one(req,'job-id')
        uri=self._one(req,'job-uri')
        if identifier is not None:
            if len(identifier)!=4:raise IppFailure(0x0400,'invalid job id')
            identifier=struct.unpack('>i',identifier)[0]
        elif uri:
            prefix=(self.uri+'/jobs/').encode()
            if not uri.startswith(prefix):raise IppFailure(0x0406,'job not found')
            identifier=int(uri[len(prefix):])
        row=next((r for r in self.rows if r['id']==identifier and r['client']==owner),None)
        if row is None:raise IppFailure(0x0406,'job not found')
        return row
    def create(self,req,key,client):
        if sum(self.phase(r) not in TERMINAL for r in self.rows)>=12:raise IppFailure(0x0507,'queue full')
        row=dict(id=max((r['id'] for r in self.rows),default=0)+1,key=key,client=client,owner='airprint-'+str(uuid.uuid4()),phase='receiving',created=time.time(),attrs=base64.b64encode(encode_ipp(Message(req.version,req.code,req.request_id,req.attributes))).decode())
        self.rows.append(row);self.save();return row
    async def render(self,req,row):
        mime,scaling,_=self._validate(req)
        orientation=self._one(req,'orientation-requested')
        args=dict(mime=mime,scaling=scaling,media=self.media,orientation=struct.unpack('>i',orientation)[0] if orientation else None)
        process=await asyncio.create_subprocess_exec(sys.executable,str(Path(__file__).with_name('render_worker.py')),stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.DEVNULL)
        try:
            output,_=await asyncio.wait_for(process.communicate(json.dumps(args).encode()+b'\n'+req.document),30)
            if process.returncode:raise IppFailure(0x040b,'document renderer rejected input')
            pages=json.loads(output)
            await self.core.submit({'id':row['owner'],'files':set()},{'requestId':row['key'],'pages':pages})
            row['phase']='queued';self.save()
        finally:
            if process.returncode is None:process.kill();await process.wait()
    async def handle(self,raw,client):
        req=decode_ipp(raw)
        opattrs=[A(1,0x47,'attributes-charset',b'utf-8'),A(1,0x48,'attributes-natural-language',b'en')]
        attrs=[];status=0
        try:
            if req.version not in ((1,1),(2,0)):raise IppFailure(0x0503,'unsupported IPP version')
            for row in self.rows:
                if row['phase']=='receiving' and time.time()-row['created']>300:row.update(phase='aborted',message='Document timeout');self.save()
            if req.code==11:attrs=self.printer_attributes()
            elif req.code==4:self._validate(req)
            elif req.code in (2,5,6):
                async with self.gate:
                    key=hashlib.sha256(client.encode()+raw).hexdigest()
                    if req.code==6:
                        row=self.find(req,client)
                        if row.get('documentKey')==key and self.phase(row)!='receiving':return encode_ipp(Message(req.version,0,req.request_id,opattrs+self.attributes(row)))
                        if self.phase(row)!='receiving':raise IppFailure(0x0404,'document already supplied or task closed')
                        if self._one(req,'last-document')!=b'\x01':raise IppFailure(0x040b,'one final document required')
                        saved=decode_ipp(base64.b64decode(row['attrs']));names={a.name for a in req.attributes}
                        req=Message(req.version,req.code,req.request_id,tuple(a for a in saved.attributes if a.name not in names)+req.attributes,req.document)
                    else:
                        row=next((r for r in self.rows if r['key']==key),None)
                        if row:return encode_ipp(Message(req.version,0,req.request_id,opattrs+self.attributes(row)))
                        self._validate(req)
                        if self.core.paused or not (self.core.simulate or self.core.device.get('connected')):raise IppFailure(0x0507,'printer paused; inspect unresolved job')
                        row=self.create(req,key,client)
                    if req.code!=5:
                        if not req.document:raise IppFailure(0x0400,'empty document')
                        row.update(phase='rendering',documentKey=key);self.save()
                        try:
                            if self.paper=='auto' and not self.core.io_lock.locked():await self.core.status()
                            if self.media not in (5009,5012,5014):raise IppFailure(0x040b,'unsupported loaded paper')
                            await self.render(req,row)
                        except Exception:
                            if not self.job(row):row.update(phase='aborted',message='Document preparation failed');self.save()
                            raise
                    attrs=self.attributes(row)
            elif req.code in (8,9):
                row=self.find(req,client)
                if req.code==8:
                    if self.phase(row) in TERMINAL:raise IppFailure(0x0404,'job already ended')
                    if self.phase(row)=='rendering':raise IppFailure(0x0507,'document processing; retry cancellation')
                    await self.core.cancel({'id':row['owner']})
                    row['phase']='cancelled';self.save()
                attrs=self.attributes(row)
            elif req.code==10:
                which=self._one(req,'which-jobs',b'not-completed')
                if which not in (b'not-completed',b'completed',b'all'):raise IppFailure(0x040b,'unsupported job selection')
                for row in self.rows:
                    if row['client']!=client:continue
                    if which==b'not-completed' and self.phase(row) in TERMINAL:continue
                    if which==b'completed' and self.phase(row) not in TERMINAL:continue
                    attrs+=[A(2,0,'',b'')]+self.attributes(row)
            else:raise IppFailure(0x0501,'operation not supported')
        except IppFailure as error:status=error.status;attrs=[A(1,0x41,'status-message',error.message.encode())]
        except (ValueError,KeyError,TypeError,Unsupported,struct.error):status=0x0400;attrs=[A(1,0x41,'status-message',b'invalid request or document')]
        except Exception:status=0x0502;attrs=[A(1,0x41,'status-message',b'print service unavailable; do not resubmit automatically')]
        return encode_ipp(Message(req.version,status,req.request_id,opattrs+attrs))

def app(adapter,allowed_networks=()):
    networks=[ipaddress.ip_network(n) for n in allowed_networks]
    slots=asyncio.Semaphore(4)
    async def post(request):
        try:peer=ipaddress.ip_address(request.remote)
        except ValueError:raise web.HTTPForbidden()
        if not peer.is_loopback and not any(peer in network for network in networks):raise web.HTTPForbidden()
        if request.content_type!='application/ipp':raise web.HTTPUnsupportedMediaType()
        if slots.locked():raise web.HTTPServiceUnavailable()
        async with slots:
            try:
                raw=await asyncio.wait_for(request.read(),15)
                response=await adapter.handle(raw,hashlib.sha256(str(peer).encode()).hexdigest())
            except (Unsupported,asyncio.TimeoutError):raise web.HTTPBadRequest()
        return web.Response(body=response,content_type='application/ipp')
    server=web.Application(client_max_size=32*1024*1024)
    server.router.add_post('/ipp/print',post);server.router.add_post('/ipp/print/',post);server.router.add_post('/ipp/print/jobs/{job_id}',post)
    return server
