"""Run independent Web and AirPrint adapters on one print service."""
import argparse,asyncio,os,re,signal,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from aiohttp import web
from printing.service import PrintService

async def run(args):
    core=PrintService(args.data,args.simulate,os.environ.get('MIJIA_BLUETOOTH_ADDRESS'))
    runners=[];bonjour=None
    await core.start(None)
    try:
        if args.entry in ('web','both'):
            from web.serve import Studio,app
            studio=Studio(core=core);runner=web.AppRunner(app(studio),access_log=None);runners.append(runner)
            await runner.setup();await web.TCPSite(runner,'0.0.0.0' if args.lan else '127.0.0.1',args.web_port).start()
            print('配对码：'+studio.code,flush=True)
            print(f'Web: http://127.0.0.1:{args.web_port}',flush=True)
        if args.entry in ('airprint','both'):
            from airprint.adapter import AirPrint,app
            from airprint.capabilities import URF
            from airprint.documents import FORMATS
            await core.status()
            adapter=AirPrint(core,f'ipp://{args.hostname}:{args.ipp_port}/ipp/print',paper=args.paper)
            runner=web.AppRunner(app(adapter,args.allow_network),access_log=None);runners.append(runner)
            await runner.setup();await web.TCPSite(runner,'0.0.0.0' if args.lan else '127.0.0.1',args.ipp_port).start()
            print(f'AirPrint: {adapter.uri}',flush=True)
            if args.announce:
                bonjour=await asyncio.create_subprocess_exec('/usr/bin/dns-sd','-R','Liuying Photo Printer','_ipp._tcp,_universal','local.',str(args.ipp_port),'txtvers=1','qtotal=1','rp=ipp/print','ty=Liuying Photo Printer','product=(Mijia Instant Photo Printer 2)','Color=T','Duplex=F','kind=photo','priority=50','pdl='+','.join(FORMATS),'URF='+b','.join(URF).decode(),'UUID='+adapter.identity.removeprefix('urn:uuid:'),stdout=asyncio.subprocess.DEVNULL,stderr=asyncio.subprocess.DEVNULL)
                await asyncio.sleep(.2)
                if bonjour.returncode is not None:raise RuntimeError('Bonjour registration failed')
        if args.simulate:print('模拟模式：不会连接打印机或实际打印。',flush=True)
        stopped=asyncio.Event();loop=asyncio.get_running_loop()
        for sig in (signal.SIGINT,signal.SIGTERM):loop.add_signal_handler(sig,stopped.set)
        await stopped.wait()
    finally:
        if bonjour and bonjour.returncode is None:bonjour.terminate();await bonjour.wait()
        for runner in reversed(runners):await runner.cleanup()
        await core.stop(None)

def main():
    p=argparse.ArgumentParser();p.add_argument('--entry',choices=('web','airprint','both'),default='both');p.add_argument('--simulate',action='store_true');p.add_argument('--lan',action='store_true');p.add_argument('--announce',action='store_true');p.add_argument('--allow-network',action='append',default=[]);p.add_argument('--hostname',default='localhost');p.add_argument('--web-port',type=int,default=8635);p.add_argument('--ipp-port',type=int,default=8636);p.add_argument('--paper',choices=('auto','six','square','splice'),default='auto');p.add_argument('--data',type=Path,default=Path.home()/'Library/Application Support/LiuyingStudio');args=p.parse_args()
    if not args.simulate and not os.environ.get('MIJIA_BLUETOOTH_ADDRESS'):p.error('设置 MIJIA_BLUETOOTH_ADDRESS，或使用 --simulate')
    if args.lan and args.entry!='web' and (not args.allow_network or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,62}\.local',args.hostname)):p.error('局域网 AirPrint 需要 --hostname 主机名.local 和 --allow-network 网段')
    if args.announce and (not args.lan or args.simulate or args.entry=='web'):p.error('Bonjour 只用于显式开启局域网的真实 AirPrint 服务')
    asyncio.run(run(args))
if __name__=='__main__':main()
