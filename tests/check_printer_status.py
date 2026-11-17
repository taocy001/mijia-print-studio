"""Run Android status scheduling against local fakes; no Bluetooth or device IO."""
from pathlib import Path
import subprocess,tempfile,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from build import JDK
sources={
 'android/content/Context.java': 'package android.content; public class Context {}',
 'org/json/JSONObject.java': """package org.json;import java.util.*;public class JSONObject extends HashMap<String,Object>{public JSONObject put(String k,Object v){super.put(k,v);return this;}public boolean has(String k){return containsKey(k);}public String optString(String k){return String.valueOf(getOrDefault(k,""));}public int optInt(String k){return optInt(k,0);}public int optInt(String k,int d){return get(k) instanceof Number?((Number)get(k)).intValue():d;}public long optLong(String k){return get(k) instanceof Number?((Number)get(k)).longValue():0;}public boolean optBoolean(String k){return Boolean.TRUE.equals(get(k));}public JSONArray optJSONArray(String k){return get(k) instanceof JSONArray?(JSONArray)get(k):null;}}""",
 'org/json/JSONArray.java': 'package org.json;import java.util.*;public class JSONArray extends ArrayList<JSONObject>{public int length(){return size();}public JSONObject getJSONObject(int i){return get(i);}}',
 'local/liuying/studio/StatusTest.java': r'''package local.liuying.studio;
import android.content.Context;import org.json.*;
class Store{static final Object LOCK=new Object();static volatile boolean busy;static String message="";static JSONObject device=new JSONObject(),job=new JSONObject();static JSONObject read(Context c,String f){return job;}static void write(Context c,String f,JSONObject j){job=j;}static void archive(Context c,JSONObject j){}static boolean terminal(JSONObject j){return "done".equals(j.optString("phase"))||"cancelled".equals(j.optString("phase"));}}
class PrintJobs{static int finished;static void finish(Context c,JSONObject j){finished++;}static JSONArray jobs=new JSONArray();static JSONArray records(Context c){return jobs;}}
class SharingService{static int updates;static int resumes;static void resumeQueue(){resumes++;}static void refreshAdvertisement(){updates++;}}
class Printer implements AutoCloseable{static int opened,closed;static boolean fail;static int jobState=5;static int jobCalls;JSONObject job(int id){jobCalls++;return new JSONObject().put("job-id",id).put("job-state",jobState);}Printer(Context c){opened++;if(!Store.busy)throw new AssertionError("Probe must own busy");PrinterStatus.refresh(c,true);}JSONObject status()throws Exception{if(fail)throw new java.io.IOException("Synthetic offline");return new JSONObject().put("connected",true).put("media",5012).put("checkedAt",System.currentTimeMillis()).put("state","30").put("ribbon",10);}public void close(){closed++;}}
class Thread{static int failure;final Runnable work;Thread(Runnable r,String name){work=r;}void start(){if(failure==1)throw new IllegalStateException("Synthetic start failure");if(failure==2)throw new OutOfMemoryError("Synthetic start failure");work.run();}}
public class StatusTest{
 static int checks;static final Context context=new Context();static void check(boolean v,String message){checks++;if(!v)throw new AssertionError(message);}
 static void elapsed()throws Exception{java.lang.reflect.Field field=PrinterStatus.class.getDeclaredField("lastAttempt");field.setAccessible(true);field.setLong(null,System.currentTimeMillis()-61000);}
 public static void main(String[]args)throws Exception{
  check(!PrinterStatus.released,"New process permits automatic checks");
  PrinterStatus.refresh(context,false);check(Printer.opened==1&&Printer.closed==1&&!Store.busy,"Initial auto probe closes and releases");check(PrinterStatus.ready(context,false),"Fresh status usable without manual detection");
  PrinterStatus.refresh(context,false);check(Printer.opened==1,"Foreground ticks throttle before 60 seconds");elapsed();PrinterStatus.refresh(context,false);check(Printer.opened==2,"Periodic refresh after interval");
  PrinterStatus.release(context);elapsed();PrinterStatus.refresh(context,false);check(PrinterStatus.released&&Printer.opened==2,"Explicit pause prevents automatic reconnect");PrinterStatus.refresh(context,true);check(!PrinterStatus.released&&Printer.opened==3,"Manual detection resumes");PrinterStatus.refresh(context,true);check(Printer.opened==4,"Manual detection bypasses throttle");
  Store.busy=true;elapsed();PrinterStatus.refresh(context,false);PrinterStatus.refresh(context,true);check(Printer.opened==4&&Store.busy,"Busy probe cannot steal print lock");Store.busy=false;
  Store.job=new JSONObject().put("token","synthetic").put("phase","uncertain");elapsed();PrinterStatus.refresh(context,false);PrinterStatus.refresh(context,true);check(Printer.opened==6&&!Store.busy,"Unresolved print permits read-only probes");check(!PrinterStatus.ready(context,false),"Unresolved job still blocks printing and AirPrint");
  Store.job.put("phase","done");elapsed();PrinterStatus.refresh(context,false);check(Printer.opened==7,"Completed history allows auto probe");Store.job=new JSONObject();
  Printer.fail=true;elapsed();PrinterStatus.refresh(context,false);check(Printer.opened==8&&Printer.closed==8&&!Store.busy&&PrinterStatus.media()==0,"Offline check closes and invalidates");Printer.fail=false;
  for(int failure:new int[]{1,2}){Thread.failure=failure;elapsed();PrinterStatus.refresh(context,false);check(!Store.busy&&PrinterStatus.media()==0&&Store.message.contains("启动检测"),"Thread start failure releases busy");Thread.failure=0;PrinterStatus.refresh(context,true);check(PrinterStatus.media()==5012&&!Store.busy,"Retry after start failure");}
  Store.job=new JSONObject().put("token","auto").put("phase","held").put("jobId",123);Printer.jobState=5;
  PrinterStatus.refresh(context,true);check(Store.job.optString("phase").equals("held"),"Held original remains unresolved");
  Printer.jobState=9;PrinterStatus.refresh(context,true);check(Store.job.optString("phase").equals("done")&&PrintJobs.finished==1&&SharingService.resumes==1,"Original completion unlocks without print");
  Store.job=new JSONObject().put("token","partial").put("phase","uncertain").put("jobId",124);JSONArray pending=new JSONArray();pending.add(new JSONObject());Store.job.put("remaining",pending);
  PrinterStatus.refresh(context,true);check(Store.job.optBoolean("batchStopped")&&Store.job.optJSONArray("remaining").length()==1,"Unsent remainder retained and stopped");
  for(int state:new int[]{7,8}){Store.job=new JSONObject().put("token","terminal").put("phase","uncertain").put("jobId",125);Printer.jobState=state;PrinterStatus.refresh(context,true);check(Store.job.optString("phase").equals(state==7?"aborted":"cancelled"),"Explicit terminal state unlocks");}
  int calls=Printer.jobCalls;Store.job=new JSONObject().put("token","missing").put("phase","blocked");PrinterStatus.refresh(context,true);check(Printer.jobCalls==calls,"No job ID never guesses from idle");
  check(SharingService.updates>0,"Status changes refresh advertisement");System.out.println("PASS: "+checks+" status checks; startup, throttle, periodic/manual, pause, busy/unresolved, failures and resource release; no Bluetooth");
 }
}'''
}
with tempfile.TemporaryDirectory(prefix='printer-status-') as directory:
 root=Path(directory)
 for name,source in sources.items():
  path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(source)
 classes=root/'classes';classes.mkdir()
 subprocess.run([str(JDK/'bin/javac'),'-d',str(classes),str(ROOT/'src/PrinterStatus.java'),str(ROOT/'src/JobRecovery.java'),str(ROOT/'src/PrinterAlerts.java'),*[str(root/name) for name in sources]],check=True)
 subprocess.run([str(JDK/'bin/java'),'-cp',str(classes),'local.liuying.studio.StatusTest'],check=True)
