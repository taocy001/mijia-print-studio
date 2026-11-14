"""Cross-language catalog and combined-code parity; offline, no printer IO."""
import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from printing.errors import CATALOG,code,describe
from build import JDK
out=ROOT/'build/error-tests';out.mkdir(parents=True,exist_ok=True)
subprocess.run([str(JDK/'bin/javac'),'-encoding','UTF-8','-d',str(out),str(ROOT/'src/PrinterAlerts.java'),str(ROOT/'tests/PrinterErrorCatalogTest.java')],check=True)
java=subprocess.check_output([str(JDK/'bin/java'),'-cp',str(out),'local.liuying.studio.PrinterErrorCatalogTest'],text=True)
assert dict(line.split('\t',1) for line in java.splitlines())=={k:code(k) for k in CATALOG}
script="const fs=require('fs'),vm=require('vm');global.window={};vm.runInThisContext(fs.readFileSync('assets/printer-errors.js','utf8'));console.log(JSON.stringify("+json.dumps(list(CATALOG)+['::5402%9008:5402','::0','::9999'])+".map(k=>window.PrinterErrors.describe(k))));"
js=json.loads(subprocess.check_output(['node','-e',script],cwd=ROOT,text=True))
assert js==[describe(k) for k in list(CATALOG)+['::5402%9008:5402','::0','::9999']]
print('PASS: 28 codes plus compound, zero and unknown cases agree across Python, Java and browser JavaScript')
