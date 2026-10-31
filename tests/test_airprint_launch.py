"""Launch only simulated services on temporary ports."""
import socket,subprocess,sys,tempfile,time,unittest,urllib.request
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from airprint.offline import Message,encode_ipp,decode_ipp
ROOT=Path(__file__).resolve().parents[1]

def port():
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));return sock.getsockname()[1]

class Launch(unittest.TestCase):
    def check_entry(self,entry):
        with tempfile.TemporaryDirectory() as folder:
            ipp,web=port(),port()
            args=[sys.executable,str(ROOT/'desktop/serve.py'),'--simulate','--entry',entry,'--data',folder,'--ipp-port',str(ipp),'--web-port',str(web)]
            process=subprocess.Popen(args,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
            try:
                raw=encode_ipp(Message((2,0),11,1,()))
                target=urllib.request.Request(f'http://127.0.0.1:{ipp}/ipp/print',data=raw,headers={'Content-Type':'application/ipp'})
                for _ in range(100):
                    try:
                        with urllib.request.urlopen(target,timeout=.2) as response:self.assertEqual(decode_ipp(response.read()).code,0)
                        break
                    except OSError:
                        if process.poll() is not None:self.fail(process.stderr.read())
                        time.sleep(.05)
                else:self.fail('simulated service did not start')
                if entry=='both':
                    with urllib.request.urlopen(f'http://127.0.0.1:{web}',timeout=1) as response:self.assertEqual(response.status,200)
                else:
                    with self.assertRaises(OSError):urllib.request.urlopen(f'http://127.0.0.1:{web}',timeout=.2)
                duplicate=subprocess.run(args,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True,timeout=5)
                self.assertNotEqual(duplicate.returncode,0);self.assertIn('打印服务已运行',duplicate.stderr)
            finally:
                process.terminate()
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:process.kill();process.wait();self.fail('service failed to stop')
                error=process.stderr.read();process.stderr.close()
            self.assertEqual(process.returncode,0,error)
    def test_airprint_without_web(self):self.check_entry('airprint')
    def test_combined_service(self):self.check_entry('both')
if __name__=='__main__':unittest.main()
