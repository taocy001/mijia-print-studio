package local.liuying.studio;
import android.content.Context;
import org.json.*;
final class PrinterStatus {
 static volatile boolean released=true;
 static volatile boolean splice=false;
 private static long lastAttempt;
 static int media(){JSONObject d=Store.device;int tray=d.optInt("media");return d.optBoolean("connected")&&System.currentTimeMillis()-d.optLong("checkedAt")<150000&&(tray==5009||tray==5012)?tray:0;}
 static void refresh(Context context,boolean manual){
  synchronized(Store.LOCK){
   if(manual)released=false;
   if(released||Store.busy||!manual&&System.currentTimeMillis()-lastAttempt<60000)return;
   JSONObject job=Store.read(context,"job.json");if(job.has("token")&&!Store.terminal(job))return;
   lastAttempt=System.currentTimeMillis();Store.busy=true;
  }
  new Thread(()->{try(Printer printer=new Printer(context)){Store.device=printer.status();Store.message="蓝牙已连接";}
   catch(Exception e){Store.device=new JSONObject();Store.message="连接失败，请在另一台设备上释放蓝牙后重试";}
   finally{Store.busy=false;}},"liuying-status").start();
 }
 static void release(Context context)throws Exception{
  synchronized(Store.LOCK){JSONObject j=Store.read(context,"job.json");if(Store.busy||j.has("token")&&!Store.terminal(j))throw new java.io.IOException("请等待当前任务结束");
   JSONArray jobs=PrintJobs.records(context);for(int i=0;i<jobs.length();i++)if("queued".equals(jobs.getJSONObject(i).optString("phase")))throw new java.io.IOException("请先处理等待中的任务");
   released=true;Store.device=new JSONObject().put("connected",false).put("released",true);Store.message="蓝牙已释放";
  }
 }
 static void layout(boolean value)throws Exception{if(media()!=5012)throw new java.io.IOException("检测到六寸纸盒后才能设置拼接");splice=value;}
}
