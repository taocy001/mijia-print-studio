package local.liuying.studio;
import android.content.Context;
import org.json.*;
final class PrinterStatus {
 static volatile boolean released=false;
 static volatile boolean splice=false;
 static volatile boolean verifiedSession,runningSession;
 private static long lastAttempt;
 static int media(){JSONObject d=Store.device;int tray=d.optInt("media");return d.optBoolean("connected")&&System.currentTimeMillis()-d.optLong("checkedAt")<150000&&(tray==5009||tray==5012)?tray:0;}
 static boolean active(Context context){
  if(!Store.busy||!verifiedSession)return false;JSONObject job=Store.read(context,"job.json");String phase=job.optString("phase");
  if(job.optBoolean("batchStopped"))return false;
  return phase.equals("prepared")||phase.equals("creating")||phase.equals("uploading")||phase.equals("printing")||phase.equals("done")&&job.optJSONArray("remaining")!=null&&job.optJSONArray("remaining").length()>0;
 }
 static int media(Context context){JSONObject d=Store.device;int tray=d.optInt("media");return d.optBoolean("connected")&&(active(context)||System.currentTimeMillis()-d.optLong("checkedAt")<150000)&&(tray==5009||tray==5012)?tray:0;}
 static boolean idle(String state){return state.equals("20")||state.equals("30");}
 static boolean ready(Context context,boolean paused){
  if(released||paused||media(context)==0||Store.device.optInt("ribbon",-1)==0||!active(context)&&!idle(Store.device.optString("state")))return false;String alert=Store.device.optString("alert");if(!alert.isEmpty()&&!alert.equals("::0"))return false;
  JSONObject job=Store.read(context,"job.json");return !job.has("token")||Store.terminal(job)||active(context)||Store.busy&&runningSession&&job.optString("phase").equals("prepared");
 }
 static void invalidate(){verifiedSession=false;Store.device=new JSONObject();SharingService.refreshAdvertisement();}
 static void refresh(Context context,boolean manual){
  synchronized(Store.LOCK){
   if(manual)released=false;
   JSONObject waiting=Store.read(context,"job.json");long interval=JobRecovery.recoverable(waiting.optString("phase"))&&waiting.optInt("jobId")>0?15000:60000;
   if(released||Store.busy||!manual&&System.currentTimeMillis()-lastAttempt<interval)return;
   // Read-only status is safe while an earlier job awaits reconciliation.
   lastAttempt=System.currentTimeMillis();Store.busy=true;Store.message="正在检测打印机";
  }
  try{new Thread(()->{boolean recovered=false;try(Printer printer=new Printer(context)){Store.device=printer.status();Store.message="蓝牙可用 · 按需连接";try{recovered=reconcile(context,printer);}catch(Exception ignored){/* Original outcome stays unresolved; never retry the print. */}}
   catch(Exception e){invalidate();String detail=e.getMessage();Store.message=detail!=null&&detail.matches("(?s).*[\\u4e00-\\u9fff].*")?detail:"蓝牙暂不可用，请检查打印机电源、距离或其他设备连接";try{Store.device.put("error",Store.message);}catch(Exception ignored){}}
   finally{Store.busy=false;if(recovered)SharingService.resumeQueue();SharingService.refreshAdvertisement();}},"liuying-status").start();}
  catch(RuntimeException|OutOfMemoryError error){try{invalidate();Store.message="暂时无法启动检测，请稍后重试";}finally{Store.busy=false;SharingService.refreshAdvertisement();}}
 }
 static boolean reconcile(Context context,Printer printer)throws Exception{
  JSONObject job=Store.read(context,"job.json");int id=job.optInt("jobId");
  if(!job.has("token")||!JobRecovery.recoverable(job.optString("phase"))||id<=0)return false;
  JSONObject info=printer.job(id);String phase=JobRecovery.terminalPhase(info.optInt("job-state",-1));
  if(!phase.isEmpty()&&info.optInt("job-id",-1)==id){synchronized(Store.LOCK){
   JSONObject current=Store.read(context,"job.json");
   if(!current.optString("token").equals(job.optString("token"))||current.optInt("jobId")!=id||!JobRecovery.recoverable(current.optString("phase")))return false;
   JSONArray remaining=current.optJSONArray("remaining");boolean stopped=remaining!=null&&remaining.length()>0;
   String message=phase.equals("done")?(stopped?"已自动确认本张完成；后续照片未发送":"已自动确认打印完成"):phase.equals("cancelled")?"已自动确认原任务取消，未自动重印":"已自动确认原任务中止，未自动重印";
   current.put("lastInfo",info).put("phase",phase).put("message",message).put("progress",phase.equals("done")?100:0).put("updatedAt",System.currentTimeMillis());
   if(stopped)current.put("batchStopped",true);
   Store.write(context,"job.json",current);Store.archive(context,current);PrintJobs.finish(context,current);Store.message=message;return true;
  }}return false;
 }
 static void release(Context context)throws Exception{
  synchronized(Store.LOCK){JSONObject j=Store.read(context,"job.json");if(Store.busy||j.has("token")&&!Store.terminal(j))throw new java.io.IOException("请等待当前任务结束");
   JSONArray jobs=PrintJobs.records(context);for(int i=0;i<jobs.length();i++)if("queued".equals(jobs.getJSONObject(i).optString("phase")))throw new java.io.IOException("请先处理等待中的任务");
   released=true;Store.device=new JSONObject().put("connected",false).put("released",true);Store.message="蓝牙已释放";
  }
  SharingService.refreshAdvertisement();
 }
 static void layout(boolean value)throws Exception{if(media()!=5012)throw new java.io.IOException("检测到六寸纸盒后才能设置拼接");splice=value;SharingService.refreshAdvertisement();}
}
