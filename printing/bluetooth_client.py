"""Mac RFCOMM + independently verified Syrup protocol. No automatic print retries."""
import fcntl, hashlib, json, logging, os, queue, re, secrets, struct, subprocess, tempfile, threading, time
from pathlib import Path
from Crypto.Cipher import AES
from PIL import Image

def frame(ch,op,enc,seq,body,total=0,number=0):
    if len(body) > 1023: raise ValueError('Bluetooth frame too large')
    h=struct.pack('<3sBBBIIHHH',b'\x7e\x64\0',ch,op,enc,seq,seq,total,number,len(body)+0x1400+(0x2000 if total>1 else 0))
    return h+body+bytes([sum((h+body)[1:])%256,0x7e])

def crypt(key,data,encrypt=True):
    if encrypt:data+=b'\0'*((-len(data))%16)
    c=AES.new(key,AES.MODE_ECB)
    return c.encrypt(data) if encrypt else c.decrypt(data)

class BluetoothClient:
    def __init__(self, address, helper, channel=None):
        if not re.fullmatch(r"(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}", address or ""):
            raise ValueError("Set a valid printer Bluetooth address")
        if channel is not None and not 1 <= int(channel) <= 30:
            raise ValueError("RFCOMM channel must be 1..30")
        self.address = address.replace('-', ':').upper()
        self.helper = str(helper)
        self.channel = 1 if channel is None else int(channel)
        self.lock = None
        self.p = None
        self.phase = 'not connected'
        self.transport_info = ''

    def open(self, *, lock_timeout=0, attempts=2):
        try:
            digest = hashlib.sha256(self.address.encode()).hexdigest()[:24]
            path = Path(tempfile.gettempdir()) / f"mijia-bt-{os.getuid()}-{digest}.lock"
            self.lock = os.fdopen(os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600), 'a')
            deadline = time.monotonic() + max(0, lock_timeout)
            while True:
                try:
                    fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        raise BlockingIOError('Bluetooth device is in use by another process') from None
                    time.sleep(.1)
            # Only transport setup and authentication are retried. No RPC or photo is replayed.
            for attempt in range(max(1, min(2, attempts))):
                try:
                    return self.connect()
                except OSError:
                    self._close_transport()
                    if attempt + 1 >= max(1, min(2, attempts)):
                        raise
                    logging.getLogger(__name__).warning('Bluetooth reconnect before job creation: phase=%s channel=%s', self.phase, self.channel)
                    time.sleep(.3)
        except Exception:
            self.close()
            raise

    def __enter__(self):
        return self.open()

    def connect(self):
        self.phase = 'connection'
        self.transport_info = ''
        env = dict(os.environ, MIJIA_BLUETOOTH_ADDRESS=self.address)
        env.pop("MIJIA_RFCOMM_CHANNEL", None)
        if self.channel is not None: env["MIJIA_RFCOMM_CHANNEL"] = str(self.channel)
        self.p=subprocess.Popen([self.helper],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,bufsize=1)
        self.lines=queue.Queue();self.buffer=bytearray();self.seq=4
        process, lines = self.p, self.lines
        def read():
            for line in process.stdout:lines.put(line.strip())
            lines.put('ERROR transport exited')
        threading.Thread(target=read,daemon=True).start()
        deadline=time.monotonic()+30
        while True:
            line=self.line(deadline)
            if line.startswith('READY'):break
            if time.monotonic() >= deadline: raise TimeoutError('Bluetooth connection timeout')
        self.phase = 'handshake hello'
        self.send(frame(255,16,3,2,b'hello'))
        body=self.receive(255,17)
        if len(body)!=36:raise ValueError('unexpected DH hello')
        g,p,ra=[int(x.rstrip(b'\0'),16) for x in (body[:4],body[4:20],body[20:])]
        if not(1<g<p and 1<ra<p and p.bit_length()<=64):raise ValueError('invalid DH values')
        b=secrets.randbelow(p-4)+3
        self.key=format(pow(ra,b,p),'X').encode().ljust(16,b'\0')
        public=format(pow(g,b,p),'016X').encode()
        self.phase = 'handshake confirmation'
        self.send(frame(255,18,3,3,public+crypt(self.key,body[4:20])))
        if self.receive(255,19).rstrip(b'\0').lower()!=b'ok':raise ValueError('DH rejected')
        self.phase = 'ready'
        return self
    def diagnostic(self, message):
        return f'{message} [phase={self.phase}; channel={self.channel}; {self.transport_info}]'
    def line(self,deadline):
        if time.monotonic() >= deadline: raise TimeoutError(self.diagnostic('Bluetooth response timeout'))
        try:line=self.lines.get(timeout=max(.01,deadline-time.monotonic()))
        except queue.Empty:raise TimeoutError(self.diagnostic('Bluetooth response timeout'))
        if line.startswith('INFO '):self.transport_info=line[5:]
        if line.startswith('ERROR'):raise IOError(self.diagnostic(line))
        if line.startswith('DATA '):self.buffer.extend(bytes.fromhex(line[5:]))
        return line
    def send(self,data):
        self.p.stdin.write(data.hex()+'\n');self.p.stdin.flush()
        deadline=time.monotonic()+15
        while self.line(deadline)!='SENT':pass
    def receive(self,ch,op):
        deadline=time.monotonic()+15
        while True:
            if len(self.buffer)>=20:
                if self.buffer[:3]!=b'\x7e\x64\0':raise ValueError('bad frame header')
                n=(int.from_bytes(self.buffer[18:20],'little')&1023)+22
                if len(self.buffer)>=n:
                    raw=bytes(self.buffer[:n]);del self.buffer[:n]
                    if raw[-1]!=126 or sum(raw[1:-2])%256!=raw[-2]:raise ValueError('bad checksum')
                    if raw[3]==ch and raw[4]==op:
                        if int.from_bytes(raw[14:16],'little')>1:raise ValueError('segmented RPC unsupported')
                        return raw[20:-2]
                    continue
            self.line(deadline)
    def rpc(self,method,params):
        self.phase = 'rpc ' + method
        seq=self.seq;self.seq+=1
        req=dict(id=seq,method=method,params=params)
        if method=='get-job-info':req['isNewSpec']=1
        self.send(frame(3,6,3,seq,crypt(self.key,json.dumps(req,separators=(',',':')).encode())))
        answer=json.loads(crypt(self.key,self.receive(3,7),False).rstrip(b'\0'))
        if answer.get('id')!=seq or 'error' in answer:raise ValueError('Bluetooth RPC rejected or mismatched')
        return answer['result']
    def upload(self,job,data):
        self.phase = 'photo upload'
        if not data or len(data) > 1048576: raise ValueError('JPEG must be 1..1048576 bytes')
        total=(len(data)+987)//988
        for i,offset in enumerate(range(0,len(data),988),1):
            self.send(frame(4,6,2,self.seq,crypt(self.key,struct.pack('<I',job)+data[offset:offset+988]),total,i));self.seq+=1
            if i%3==0:time.sleep(.015)
    def _close_transport(self):
        if self.p is not None:
            try:
                self.p.stdin.write('CLOSE\n'); self.p.stdin.flush(); self.p.wait(timeout=3)
            except Exception:
                self.p.kill(); self.p.wait()
            finally:
                self.p.stdin.close(); self.p.stdout.close(); self.p = None

    def close(self):
        self._close_transport()
        if self.lock is not None:
            self.lock.close(); self.lock = None

    def __exit__(self, *args):
        self.close()
