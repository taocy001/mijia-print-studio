package local.liuying.studio;
import android.app.*;
import android.content.*;
import android.os.*;
import java.net.*;
import java.util.*;
import org.json.*;

public final class SharingService extends PrintService {
 private static volatile SharingService instance;
 private LocalHttp http;private WebApi api;private boolean lan;private volatile boolean closing,running,paused;
 private final Handler main=new Handler(Looper.getMainLooper());
 static boolean accepting(){SharingService s=instance;return s!=null&&!s.closing&&s.http!=null;}
 static JSONObject sharingState(){
  JSONObject out=new JSONObject();try{SharingService s=instance;out.put("running",accepting());if(s==null)return out;out.put("paused",s.paused).put("lan",s.lan);if(s.http==null)return out;out.put("code",s.api.sessions.code).put("local","http://127.0.0.1:"+s.http.port());JSONArray addresses=new JSONArray();
   if(s.lan)for(NetworkInterface n:Collections.list(NetworkInterface.getNetworkInterfaces()))if(n.isUp()&&!n.isLoopback())for(InetAddress a:Collections.list(n.getInetAddresses()))if(a instanceof Inet4Address&&a.isSiteLocalAddress())addresses.put("http://"+a.getHostAddress()+":"+s.http.port());out.put("addresses",addresses);
  }catch(Exception ignored){}return out;
 }
 @Override protected int notificationId(){return 2;}
 @Override protected Notification notice(String text){
  PendingIntent open=PendingIntent.getActivity(this,0,new Intent(this,MainActivity.class),PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
  PendingIntent stop=PendingIntent.getService(this,2,new Intent(this,SharingService.class).setAction("stop"),PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
  return new Notification.Builder(this,"print").setSmallIcon(R.drawable.icon).setContentTitle("留影工坊 · 共享打印").setContentText(text).setContentIntent(open).setOngoing(true).addAction(new Notification.Action.Builder(null,"停止共享",stop).build()).build();
 }
 @Override public int onStartCommand(Intent intent,int flags,int startId){
  getSystemService(NotificationManager.class).createNotificationChannel(new NotificationChannel("print","照片打印",NotificationManager.IMPORTANCE_LOW));
  startForeground(2,notice("共享打印服务运行中"));
  if(intent==null){stopSelf();return START_NOT_STICKY;}
  if("stop".equals(intent.getAction())){closeSharing();return START_NOT_STICKY;}
  if(http!=null)return START_NOT_STICKY;
  try{lan=intent.getBooleanExtra("lan",false);PrintJobs.cancelWaiting(this);PrintJobs.persist(this,new JSONArray());api=new WebApi(this);http=new LocalHttp(lan,8634,api);instance=this;main.post(pump);}
  catch(Exception e){Store.message="共享服务启动失败，请检查端口或权限";stopForeground(STOP_FOREGROUND_REMOVE);stopSelf();}
  return START_NOT_STICKY;
 }
 private final Runnable pump=new Runnable(){public void run(){if(closing)return;try{synchronized(Store.LOCK){if(!running&&!paused&&PrintJobs.promote(SharingService.this)){running=true;execute("print");}}}catch(Exception e){paused=true;Store.message="共享队列已暂停，请在手机上检查";}main.postDelayed(this,700);}};
 @Override protected void finished(){main.post(()->{running=false;JSONObject job=Store.read(this,"job.json");if(!"done".equals(job.optString("phase"))&&!"cancelled".equals(job.optString("phase")))paused=true;if(closing){stopForeground(STOP_FOREGROUND_REMOVE);stopSelf();}else getSystemService(NotificationManager.class).notify(2,notice(paused?"共享队列已暂停，请检查任务":"共享打印服务运行中"));});}
 static void resumeQueue(){SharingService s=instance;if(s!=null)s.main.post(()->{if(!Store.busy){JSONObject j=Store.read(s,"job.json");if(!j.has("token")||Store.terminal(j))s.paused=false;}});}
 static void checkPrinter(){SharingService s=instance;if(s==null)return;s.main.post(()->{
  synchronized(Store.LOCK){JSONObject j=Store.read(s,"job.json");if(Store.busy||j.has("token")&&!Store.terminal(j))return;Store.busy=true;}
  new Thread(()->{try(Printer p=new Printer(s)){Store.device=p.status();Store.message="蓝牙已连接";}catch(Exception e){Store.message="连接失败，请在手机上检查打印机";}finally{Store.busy=false;}},"liuying-web-status").start();
 });}
 static void reconcile(String owner)throws Exception{SharingService s=instance;if(s==null)throw new java.io.IOException("共享服务未开启");s.main.post(()->{synchronized(Store.LOCK){JSONObject j=Store.read(s,"job.json");if(!Store.busy&&!s.running&&owner.equals(j.optString("owner"))&&j.has("jobId")&&!Store.terminal(j)){s.running=true;s.execute("reconcile");}}});}
 static void stopSharing(){SharingService s=instance;if(s!=null)s.main.post(s::closeSharing);}
 private void closeSharing(){closing=true;try{PrintJobs.cancelWaiting(this);}catch(Exception ignored){}main.removeCallbacks(pump);if(http!=null){http.close();http=null;}if(api!=null)api.sessions.clear();if(!running){stopForeground(STOP_FOREGROUND_REMOVE);stopSelf();}}
 @Override public void onDestroy(){main.removeCallbacksAndMessages(null);if(http!=null)http.close();if(api!=null)api.sessions.clear();if(instance==this)instance=null;super.onDestroy();}
}
