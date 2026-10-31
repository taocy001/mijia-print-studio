"""Run isolated queue and browser-session tests. Never prints."""
from pathlib import Path
import os,subprocess,sys,shutil
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from build import JDK,SDK,TOOLS,ANDROID
out=root/'build/queue-tests';out.mkdir(parents=True,exist_ok=True)
def run(*args):return subprocess.run([str(a) for a in args],check=True,env={**os.environ,'JAVA_HOME':str(JDK)})
instruments=['WebJobsInstrument','WebSessionsInstrument']
manifest=out/'AndroidManifest.xml';manifest.write_text('<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="local.liuying.studio.tests"><uses-sdk android:minSdkVersion="31" android:targetSdkVersion="36"/><application android:label="留影测试" android:debuggable="true"/>'+''.join(f'<instrumentation android:name="local.liuying.studio.{name}" android:targetPackage="local.liuying.studio"/>' for name in instruments)+'</manifest>')
classes=out/'classes';dex=out/'dex'
for directory in (classes,dex):shutil.rmtree(directory,ignore_errors=True);directory.mkdir()
run(JDK/'bin/javac','-source','8','-target','8','-cp',str(ANDROID)+os.pathsep+str(root/'build/classes'),'-d',classes,*(root/'tests'/f'{name}.java' for name in instruments))
run(TOOLS/'d8','--lib',ANDROID,'--min-api','31','--output',dex,*classes.rglob('*.class'))
run(TOOLS/'aapt2','link','-I',ANDROID,'--manifest',manifest,'-o',out/'unsigned.apk')
import zipfile
with zipfile.ZipFile(out/'unsigned.apk','a') as z:z.write(dex/'classes.dex','classes.dex')
run(TOOLS/'zipalign','-f','4',out/'unsigned.apk',out/'aligned.apk')
run(TOOLS/'apksigner','sign','--ks',root/'build/debug.keystore','--ks-pass','pass:android','--out',out/'tests.apk',out/'aligned.apk')
adb=SDK/'platform-tools/adb'
services=subprocess.check_output([str(adb),'shell','dumpsys','activity','services','local.liuying.studio'],text=True)
if 'isForeground=true' in services:raise SystemExit('Stop sharing and finish printing before device tests')
run(adb,'install','--no-incremental','-r',out/'tests.apk')
for name in instruments:
 result=subprocess.run([str(adb),'shell','am','instrument','-r','-w','local.liuying.studio.tests/local.liuying.studio.'+name],capture_output=True,text=True)
 print(result.stdout);print(result.stderr)
 if result.returncode or 'PASS:' not in result.stdout or 'INSTRUMENTATION_CODE: -1' not in result.stdout:raise SystemExit(name+' failed')
