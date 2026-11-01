"""Windows setup window, separate from the shared photo editor."""
import argparse
import base64
import ipaddress
import json
import os
from pathlib import Path
import queue
import re
import socket
import subprocess
import sys
import tempfile
import threading
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
DEFAULTS = dict(printer='', lan=False, address='', network='', web_port=8635, ipp_port=8636, simulate=False)


def data_directory():
    return Path(os.environ.get('LOCALAPPDATA', str(Path.home()/'AppData/Local')))/'MijiaPrintStudio'


def validate(settings):
    value = {key: settings.get(key, default) for key, default in DEFAULTS.items()}
    for key in ('lan', 'simulate'):
        if type(value[key]) is not bool: raise ValueError('共享和模拟选项无效')
    for key in ('printer', 'address', 'network'):
        if not isinstance(value[key], str): raise ValueError('配置格式无效')
        value[key] = value[key].strip()
    for key in ('web_port', 'ipp_port'):
        if type(value[key]) is not int or not 1 <= value[key] <= 65535: raise ValueError('端口必须为 1–65535')
    if value['web_port'] == value['ipp_port']: raise ValueError('Web 与 AirPrint 需要不同端口')
    if not value['simulate'] and not re.fullmatch(r'(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}', value['printer']):
        raise ValueError('请选择已配对的打印机，或填写蓝牙地址')
    if value['lan']:
        try:
            address = ipaddress.IPv4Address(value['address'])
            network = ipaddress.ip_network(value['network'], strict=False)
            if network.version != 4 or address not in network or network.prefixlen < 8: raise ValueError()
            private = [ipaddress.ip_network(cidr) for cidr in ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16')]
            if not any(network.subnet_of(cidr) for cidr in private): raise ValueError()
        except ValueError: raise ValueError('请填写本机局域网 IPv4 和包含该地址的私有可信网段') from None
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            try: probe.bind((str(address), 0))
            except OSError: raise ValueError('所填局域网地址不属于本机，或无法绑定') from None
        value['network'] = str(network)
    return value


def load_settings(path):
    if not path.exists(): return dict(DEFAULTS)
    try:
        raw = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(raw, dict): raise ValueError()
        values={key:raw.get(key,default) for key,default in DEFAULTS.items()}
        if any(type(values[key]) is not type(default) for key,default in DEFAULTS.items()):raise ValueError()
        return values
    except (OSError, ValueError): raise ValueError('无法读取已有配置；文件未被覆盖，请检查 launcher.json') from None


def save_settings(path, value):
    value = validate(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.launcher-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as output:
            json.dump(value, output, ensure_ascii=False); output.flush(); os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def command(settings, data):
    value = validate(settings)
    args = [sys.executable, '-u', str(ROOT/'desktop/windows_host.py'), '--data', str(data),
            '--web-port', str(value['web_port']), '--ipp-port', str(value['ipp_port'])]
    if value['simulate']: args.append('--simulate')
    if value['lan']:
        args += ['--lan', '--address', value['address'], '--allow-network', value['network']]
        if not value['simulate']: args.append('--announce')
    env = dict(os.environ, PYTHONUTF8='1')
    env.pop('MIJIA_BLUETOOTH_ADDRESS', None)
    env.pop('MIJIA_RFCOMM_CHANNEL', None)
    if not value['simulate']: env['MIJIA_BLUETOOTH_ADDRESS'] = value['printer']
    return args, env


def paired_printers():
    source = r'''
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new()
@(Get-PnpDevice -ErrorAction Stop | Where-Object {$_.Class -eq 'Bluetooth' -and $_.InstanceId -match '^BTHENUM\\DEV_([0-9A-F]{12})\\' -and $_.FriendlyName -match '(?i)print|打印|照片|mijia'} | ForEach-Object {
 $null=$_.InstanceId -match '^BTHENUM\\DEV_([0-9A-F]{12})\\'
 @{name=$_.FriendlyName;address=([regex]::Matches($Matches[1],'.{2}').Value -join ':')}
}) | ConvertTo-Json -Compress
'''
    encoded = base64.b64encode(source.encode('utf-16-le')).decode()
    result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-EncodedCommand', encoded], capture_output=True, timeout=20)
    if result.returncode: raise RuntimeError('无法读取配对设备，请在 Windows 蓝牙设置中检查')
    raw = result.stdout.decode('utf-8-sig').strip()
    rows = json.loads(raw) if raw else []
    from desktop.windows_check import bluetooth
    candidates=rows if isinstance(rows,list) else [rows]
    return [row for row in candidates if re.fullmatch(r'(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}',row.get('address','')) and bluetooth(row['address'])['paired'] is True]


class Service:
    def __init__(self):
        self.process = None
        self.events = queue.Queue()
        self.ready = False
        self.stopping = False
        self.settings = None

    def start(self, settings, data):
        if self.process is not None: raise RuntimeError('本窗口的服务尚未结束')
        args, env = command(settings, data)
        self.ready = False; self.stopping = False; self.settings = validate(settings)
        self.process = subprocess.Popen(args, cwd=ROOT, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', bufsize=1,
                                        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        process = self.process
        def output():
            try:
                for line in process.stdout: self.events.put(('line', line.rstrip()))
            finally:
                process.stdout.close(); code = process.wait()
                self.events.put(('exit', (process, code)))
        threading.Thread(target=output, daemon=True).start()

    def stop(self):
        if self.process is None or self.stopping: return
        self.stopping = True
        try: self.process.stdin.write('STOP\n'); self.process.stdin.flush()
        except (OSError, ValueError): pass

    def receive(self):
        items = []
        while True:
            try: kind, value = self.events.get_nowait()
            except queue.Empty: break
            if kind == 'line' and value == 'STUDIO_READY': self.ready = True
            if kind == 'exit':
                process, code = value
                if process is self.process:
                    process.stdin.close(); self.process = None; self.ready = False; self.stopping = False
                value = code
            items.append((kind, value))
        return items


class Window:
    def __init__(self, root, data):
        import tkinter as tk
        from tkinter import ttk, messagebox
        self.root, self.data, self.messages = root, data, messagebox
        self.service = Service(); self.closing = False; self.results = queue.Queue(); self.devices = {}
        root.title('留影工坊 · Windows'); root.minsize(600, 570)
        panel = ttk.Frame(root, padding=24); panel.pack(fill='both', expand=True); panel.columnconfigure(1, weight=1)
        ttk.Label(panel, text='留影工坊', font=('Segoe UI', 20, 'bold')).grid(row=0, column=0, columnspan=3, sticky='w', pady=(0,18))
        self.config_error = False
        try: settings = load_settings(data/'launcher.json')
        except ValueError as error: settings = dict(DEFAULTS); self.config_error = True; messagebox.showerror('配置未读取', str(error))
        self.values = {key: tk.BooleanVar(value=settings[key]) if isinstance(default, bool) else tk.StringVar(value=settings[key]) for key, default in DEFAULTS.items()}
        ttk.Label(panel, text='打印机').grid(row=1, column=0, sticky='w')
        self.printers = ttk.Combobox(panel, state='readonly'); self.printers.grid(row=1, column=1, sticky='ew', padx=12)
        self.printers.bind('<<ComboboxSelected>>', lambda _: self.values['printer'].set(self.devices[self.printers.get()]))
        ttk.Button(panel, text='读取已配对设备', command=self.discover).grid(row=1, column=2)
        ttk.Label(panel, text='蓝牙地址').grid(row=2, column=0, sticky='w', pady=10)
        ttk.Entry(panel, textvariable=self.values['printer']).grid(row=2, column=1, columnspan=2, sticky='ew', padx=(12,0))
        ttk.Checkbutton(panel, text='允许局域网通过 Web / AirPrint 使用', variable=self.values['lan'], command=self.network_fields).grid(row=3, column=0, columnspan=3, sticky='w', pady=8)
        self.network_widgets=[]
        for row,key,label in [(4,'address','本机 IPv4'),(5,'network','可信网段')]:
            ttk.Label(panel,text=label).grid(row=row,column=0,sticky='w',pady=6)
            entry=ttk.Entry(panel,textvariable=self.values[key]);entry.grid(row=row,column=1,columnspan=2,sticky='ew',padx=(12,0));self.network_widgets.append(entry)
        ports=ttk.Frame(panel);ports.grid(row=6,column=0,columnspan=3,sticky='w',pady=10)
        for key,label in [('web_port','Web 端口'),('ipp_port','AirPrint 端口')]:
            ttk.Label(ports,text=label).pack(side='left',padx=(0,8));ttk.Entry(ports,textvariable=self.values[key],width=7).pack(side='left',padx=(0,20))
        ttk.Checkbutton(panel,text='模拟模式（不连接打印机、不出纸）',variable=self.values['simulate']).grid(row=7,column=0,columnspan=3,sticky='w',pady=6)
        buttons=ttk.Frame(panel);buttons.grid(row=8,column=0,columnspan=3,sticky='ew',pady=12)
        self.start_button=ttk.Button(buttons,text='保存并启动',command=self.start);self.start_button.pack(side='left')
        self.stop_button=ttk.Button(buttons,text='停止服务',command=self.stop,state='disabled');self.stop_button.pack(side='left',padx=8)
        self.open_button=ttk.Button(buttons,text='打开编辑器',command=self.open_editor,state='disabled');self.open_button.pack(side='left')
        self.check_button=ttk.Button(buttons,text='自检',command=self.check);self.check_button.pack(side='right')
        self.status=tk.StringVar(value='未启动');ttk.Label(panel,textvariable=self.status,wraplength=540).grid(row=9,column=0,columnspan=3,sticky='w',pady=4)
        self.address=tk.StringVar();ttk.Entry(panel,textvariable=self.address,state='readonly').grid(row=10,column=0,columnspan=3,sticky='ew',pady=4)
        self.pair=tk.StringVar();ttk.Label(panel,textvariable=self.pair).grid(row=11,column=0,columnspan=3,sticky='w')
        self.log=tk.Text(panel,height=6,width=65,wrap='word',state='disabled',font=('Segoe UI',10));self.log.grid(row=12,column=0,columnspan=3,sticky='nsew',pady=(10,0));panel.rowconfigure(12,weight=1)
        self.network_fields();root.protocol('WM_DELETE_WINDOW',self.close);root.after(100,self.poll)
        if self.config_error:self.start_button.configure(state='disabled')

    def network_fields(self):
        for widget in self.network_widgets:widget.configure(state='normal' if self.values['lan'].get() else 'disabled')

    def settings(self):
        values={key:item.get() for key,item in self.values.items()}
        try:
            for key in ('web_port','ipp_port'):values[key]=int(values[key])
        except ValueError:raise ValueError('端口必须为数字') from None
        return validate(values)

    def background(self, function, callback):
        def work():
            try:self.results.put((callback,function(),None))
            except Exception as error:self.results.put((callback,None,str(error)))
        threading.Thread(target=work,daemon=True).start()

    def discover(self):
        def done(rows,error):
            if error:self.messages.showerror('读取设备',error);return
            self.devices={str(row['name'])+' ('+row['address']+')':row['address'] for row in rows}
            self.printers.configure(values=list(self.devices))
            if not rows:self.status.set('未找到已配对的打印机；请先在 Windows 蓝牙设置中配对')
            elif len(rows)==1:self.printers.current(0);self.values['printer'].set(rows[0]['address'])
        self.background(paired_printers,done)

    def check(self):
        self.check_button.configure(state='disabled')
        address=self.values['printer'].get();ports=[self.values[key].get() for key in ('web_port','ipp_port')]
        def inspect():
            result=subprocess.run([sys.executable,str(ROOT/'desktop/windows_check.py'),'--json','--web-port',ports[0],'--ipp-port',ports[1]],env=dict(os.environ,PYTHONUTF8='1',MIJIA_BLUETOOTH_ADDRESS=address),capture_output=True,timeout=35)
            try:return json.loads(result.stdout.decode('utf-8'))
            except ValueError:raise ValueError('自检未能完成，请核对端口输入和 Python 安装') from None
        def done(result,error):
            self.check_button.configure(state='normal')
            if error:self.messages.showerror('自检',error);return
            self.append('\n'.join('['+c['status']+'] '+c['message'] for c in result['checks']))
        self.background(inspect,done)

    def append(self,text):
        self.log.configure(state='normal');self.log.insert('end',text+'\n')
        if int(self.log.index('end-1c').split('.')[0])>150:self.log.delete('1.0','50.0')
        self.log.see('end');self.log.configure(state='disabled')

    def start(self):
        try:
            settings=self.settings();save_settings(self.data/'launcher.json',settings);self.service.start(settings,self.data)
        except Exception as error:self.messages.showerror('未启动',str(error));return
        self.start_button.configure(state='disabled');self.stop_button.configure(state='normal');self.open_button.configure(state='disabled')
        self.pair.set('');self.address.set('');self.status.set('正在启动模拟服务…' if settings['simulate'] else '正在启动服务…')

    def stop(self):
        self.service.stop();self.stop_button.configure(state='disabled');self.open_button.configure(state='disabled');self.status.set('正在停止；等待当前任务结束，未开始的任务将取消')

    def open_editor(self):
        if self.service.ready and not self.service.stopping:webbrowser.open('http://127.0.0.1:'+str(self.service.settings['web_port']))

    def close(self):
        if self.service.process is None:self.root.destroy();return
        self.closing=True;self.stop()

    def poll(self):
        for kind,value in self.service.receive():
            if kind=='line':
                if value=='STUDIO_READY':
                    if not self.service.stopping:
                        settings=self.service.settings;self.status.set('模拟服务已启动 · 不会打印' if settings['simulate'] else '服务已启动；设备状态可在编辑器中查看')
                        self.address.set('http://'+(settings['address'] if settings['lan'] else '127.0.0.1')+':'+str(settings['web_port']));self.open_button.configure(state='normal')
                elif value.startswith('配对码：'):self.pair.set(value)
                else:self.append(value)
            elif kind=='exit':
                self.start_button.configure(state='normal');self.stop_button.configure(state='disabled');self.open_button.configure(state='disabled');self.pair.set('');self.address.set('')
                self.status.set('服务已停止' if value==0 else '启动或运行失败，请查看下方信息')
                if self.closing:self.root.destroy();return
        while True:
            try:callback,result,error=self.results.get_nowait()
            except queue.Empty:break
            callback(result,error)
        self.root.after(100,self.poll)


def main():
    if sys.platform!='win32':raise SystemExit('This launcher requires native Windows')
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--data',type=Path,default=data_directory());args=parser.parse_args()
    import tkinter as tk
    sys.path.insert(0,str(ROOT))
    from printing.platform import open_lock,lock_exclusive
    args.data.mkdir(parents=True,exist_ok=True)
    with open_lock(args.data/'launcher.lock') as lock:
        try:lock_exclusive(lock)
        except BlockingIOError:raise SystemExit('Launcher already open for this data directory') from None
        root=tk.Tk();Window(root,args.data);root.mainloop()


if __name__=='__main__':main()
