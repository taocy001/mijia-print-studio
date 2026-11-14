"""User-facing errors for the verified syrup catalog; unknown codes stay visible."""
import json,re
from pathlib import Path
CATALOG=json.loads(Path(__file__).with_name('printer_errors.json').read_text())['codes']
def code(value):
    c='' if value is None else str(value).strip()
    if not c or c=='0':return ''
    row=CATALOG.get(c)
    if row:return f"{row['title']}（{c}）。{row['action']}"
    safe=re.sub(r'[^0-9A-Za-z_-]','_',c)[:80]
    return f'未识别的打印机错误（{safe}）。请检查设备提示并保留错误码；不要重复提交未确认的任务。'
def describe(value):
    return '；'.join(dict.fromkeys(code(v) for v in re.split(r'[:%,;\s]+',str(value or '')) if v and v!='0'))
def rewrite(value):
    message=re.sub(r'打印机告警[（(]([0-9A-Za-z_-]+)[）)]',lambda m:code(m[1]),str(value or ''))
    return re.sub(r'打印机拒绝任务[：:]\s*(\d+)\b',lambda m:'打印机拒绝任务：'+code(m[1]),message)
class PrinterResponseError(ValueError):
    def __init__(self,value):
        self.code=value
        super().__init__('打印机请求未完成：'+(code(value) or '返回了未识别的错误，请检查设备状态'))
