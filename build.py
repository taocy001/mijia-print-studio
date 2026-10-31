#!/usr/bin/env python3
"""Build the Android app with the local SDK."""
import os
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile
ROOT=Path(__file__).resolve().parent
SDK=Path(os.environ.get('ANDROID_HOME',str(Path.home()/'Library/Android/sdk')))
JDK=Path(os.environ.get('JAVA_HOME','/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home'))
TOOLS=SDK/'build-tools/37.0.0'
ANDROID=SDK/'platforms/android-36/android.jar'
BUILD=ROOT/'build'
def run(*cmd):
    subprocess.run(list(map(str,cmd)),check=True,env={**os.environ,'JAVA_HOME':str(JDK)})
def main():
    for name in ('classes','dex','generated'):(BUILD/name).mkdir(parents=True,exist_ok=True)
    for name,checksum in json.loads((ROOT/'deps/checksums.json').read_text()).items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=checksum:raise RuntimeError('Dependency checksum mismatch: '+name)
    runtime=BUILD/'onnxruntime';runtime.mkdir(exist_ok=True)
    with zipfile.ZipFile(ROOT/'deps/onnxruntime-android-1.23.2.aar') as archive:
        archive.extract('classes.jar',runtime)
        for name in archive.namelist():
            if name.startswith('jni/') and name.endswith('.so'):archive.extract(name,runtime)
    runtime_jar=runtime/'classes.jar'
    run(TOOLS/'aapt2','compile','--dir',ROOT/'res','-o',BUILD/'resources.zip')
    run(TOOLS/'aapt2','link','-I',ANDROID,'--manifest',ROOT/'AndroidManifest.xml','-A',ROOT/'assets','--java',BUILD/'generated','-o',BUILD/'unsigned.apk',BUILD/'resources.zip')
    run(JDK/'bin/javac','-source','8','-target','8','-classpath',str(ANDROID)+os.pathsep+str(runtime_jar),'-d',BUILD/'classes',*sorted((ROOT/'src').glob('*.java')),*sorted((BUILD/'generated').rglob('*.java')))
    run(TOOLS/'d8','--lib',ANDROID,'--min-api','31','--output',BUILD/'dex',*sorted((BUILD/'classes').rglob('*.class')),runtime_jar)
    with zipfile.ZipFile(BUILD/'unsigned.apk','a') as z:
        for dex in (BUILD/'dex').glob('*.dex'):z.write(dex,dex.name)
        for library in (runtime/'jni').rglob('*.so'):z.write(library,'lib/'+str(library.relative_to(runtime/'jni')),compress_type=zipfile.ZIP_DEFLATED)
    run(TOOLS/'zipalign','-f','4',BUILD/'unsigned.apk',BUILD/'aligned.apk')
    key=BUILD/'debug.keystore'
    if not key.exists():run(JDK/'bin/keytool','-genkeypair','-keystore',key,'-storepass','android','-keypass','android','-alias','androiddebugkey','-keyalg','RSA','-keysize','2048','-validity','3650','-dname','CN=Liuying Local App')
    run(TOOLS/'apksigner','sign','--ks',key,'--ks-pass','pass:android','--out',BUILD/'liuying-studio.apk',BUILD/'aligned.apk')
    run(TOOLS/'apksigner','verify',BUILD/'liuying-studio.apk')
    print(BUILD/'liuying-studio.apk')
if __name__=='__main__':main()
