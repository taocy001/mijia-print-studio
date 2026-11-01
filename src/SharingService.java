package local.liuying.studio;
import android.app.*;
import android.content.*;
import android.os.*;
import android.net.nsd.*;
import java.net.*;
import java.util.*;
import org.json.*;

public final class SharingService extends PrintService {
 private static volatile SharingService instance;
 private PhoneAirPrint ippApi;private LocalHttp http,ipp;private NsdManager.RegistrationListener registration;private final AirPrintAdvertisement advertisement=new AirPrintAdvertisement();private long announceRetry;private volatile String airprintName="留影工坊 · 手机",airprintError="";private WebApi api;private volatile boolean closing,running,paused;
 private final Handler main=new Handler(Looper.getMainLooper());
 static boolean accepting(){SharingService s=instance;return s!=null&&!s.closing&&s.http!=null;}
 static JSONObject sharingState(){
  JSONObject out=new JSONObject();try{SharingService s=instance;out.put("running",accepting()).put("canManagePairing",true);if(s==null)return out;out.put("airprintReady",s.ipp!=null&&PrinterStatus.ready(s,s.paused)).put("airprintAdvertised",s.advertisement.visible()).put("airprint",s.ipp!=null).put("airprintName",s.airprintName).put("airprintError",s.airprintError).put("paused",s.paused).put("lan",true);if(s.http==null)return out;out.put("code",s.api.sessions.code);JSONArray addresses=new JSONArray();
   for(NetworkInterface n:Collections.list(NetworkInterface.getNetworkInterfaces()))if(n.isUp()&&!n.isLoopback())for(InetAddress a:Collections.list(n.getInetAddresses()))if(a instanceof Inet4Address&&a.isSiteLocalAddress())addresses.put("http://"+a.getHostAddress()+":"+s.http.port());out.put("addresses",addresses);
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
  try{
   if(instance==null){Store.recover(this);PrintJobs.cancelWaiting(this);instance=this;main.post(pump);}
   if("airprint".equals(intent.getAction())){if(ipp==null){ippApi=new PhoneAirPrint(this);ipp=new LocalHttp(true,8637,ippApi,true);airprintName=defaultPrinterName(this);}PrinterStatus.refresh(this,true);syncAdvertisement();}
   else if(http==null){synchronized(SharingService.class){api=new WebApi(this);http=new LocalHttp(true,8634,api);}}
  }catch(Exception e){Store.message="共享服务启动失败，请检查端口或权限";if(http==null&&ipp==null){stopForeground(STOP_FOREGROUND_REMOVE);stopSelf();}}
  return START_NOT_STICKY;
 }
 private final Runnable pump=new Runnable(){public void run(){if(closing)return;PrinterStatus.refresh(SharingService.this,false);try{synchronized(Store.LOCK){if(!running&&!paused&&PrintJobs.promote(SharingService.this)){running=true;execute("print");}}}catch(Exception e){paused=true;Store.message="共享队列已暂停，请在手机上检查";}syncAdvertisement();main.postDelayed(this,700);}};
 @Override protected void finished(){main.post(()->{running=false;JSONObject job=Store.read(this,"job.json");if(batchFailed||job.optBoolean("batchStopped")||!"done".equals(job.optString("phase"))&&!"cancelled".equals(job.optString("phase")))paused=true;syncAdvertisement();if(closing){stopForeground(STOP_FOREGROUND_REMOVE);stopSelf();}else getSystemService(NotificationManager.class).notify(2,notice(paused?"共享队列已暂停，请检查任务":"共享打印服务运行中"));});}
 static void resumeQueue(){SharingService s=instance;if(s!=null)s.main.post(()->{if(!Store.busy){JSONObject j=Store.read(s,"job.json");if(!j.has("token")||Store.terminal(j)){s.paused=false;s.syncAdvertisement();}}});}
 static void checkPrinter(){SharingService s=instance;if(s!=null)PrinterStatus.refresh(s,true);}
 static void reconcile(String owner)throws Exception{SharingService s=instance;if(s==null)throw new java.io.IOException("共享服务未开启");s.main.post(()->{synchronized(Store.LOCK){JSONObject j=Store.read(s,"job.json");if(!Store.busy&&!s.running&&owner.equals(j.optString("owner"))&&j.has("jobId")&&!Store.terminal(j)){s.running=true;s.execute("reconcile");}}});}
 static synchronized String resetPairing(Context context){try{SharingService s=instance;WebSessions sessions=s!=null&&s.api!=null?s.api.sessions:new WebSessions(context.getFilesDir());sessions.revokeAll();return "{\"ok\":true}";}catch(Exception e){return "{\"error\":\"配对重置失败，请重试\"}";}}
 static void stopSharing(){SharingService s=instance;if(s!=null)s.main.post(()->{if(s.ipp==null)s.closeSharing();else{if(s.http!=null){s.http.close();s.http=null;}try{PrintJobs.cancelWaiting(s,false);}catch(Exception ignored){}if(s.api!=null)s.api.sessions.clear();}});}
 static void stopAirPrint(){SharingService s=instance;if(s!=null)s.main.post(()->{s.closeAirPrint();try{PrintJobs.cancelWaiting(s,true);}catch(Exception ignored){}if(s.http==null)s.closeSharing();});}
 static String printerUuid(Context c){android.content.SharedPreferences p=c.getSharedPreferences("printer",0);String id=p.getString("uuid",null);if(id==null){id="urn:uuid:"+UUID.randomUUID();p.edit().putString("uuid",id).apply();}return id;}
 static String printerName(Context c){SharingService s=instance;return s!=null&&s.ipp!=null?s.airprintName:defaultPrinterName(c);}
 private static String defaultPrinterName(Context c){return "留影工坊 · 手机 · " + printerUuid(c).substring(9,15).toUpperCase(Locale.ROOT);}
 static boolean queuePaused(){SharingService s=instance;return s!=null&&s.paused;}
 static void refreshAdvertisement(){SharingService s=instance;if(s!=null)s.main.post(s::syncAdvertisement);}
 private void syncAdvertisement(){
  boolean wanted=!closing&&ipp!=null&&PrinterStatus.ready(this,paused);
  int paper=PrinterStatus.media(this);String formats=paper==5012&&PrinterStatus.splice?"image/jpeg,application/pdf":String.join(",",AirPrintPages.FORMATS);
  advertise(advertisement.update(wanted,paper+"|"+formats,System.currentTimeMillis()>=announceRetry),formats);
 }
 private void advertise(AirPrintAdvertisement.Action action,String formats){
  if(action==AirPrintAdvertisement.Action.NONE)return;
  final int token=advertisement.token();
  if(action==AirPrintAdvertisement.Action.UNREGISTER){
   try{getSystemService(NsdManager.class).unregisterService(registration);}
   catch(IllegalArgumentException e){registration=null;advertise(advertisement.unregistered(token,true),formats);}
   catch(RuntimeException e){announceRetry=System.currentTimeMillis()+5000;advertisement.unregistered(token,false);airprintError="打印机广播撤销未完成，正在重试";main.postDelayed(this::syncAdvertisement,5000);}
   return;
  }
  formats=advertisement.key().substring(advertisement.key().indexOf('|')+1);final String announcedFormats=formats;
  NsdServiceInfo info=new NsdServiceInfo();info.setServiceName(defaultPrinterName(this));info.setServiceType("_ipp._tcp");info.setPort(8637);if(Build.VERSION.SDK_INT>=35)info.setSubtypes(Collections.singleton("_universal"));
  String[][] attrs={{"txtvers","1"},{"qtotal","1"},{"rp","ipp/print"},{"ty","Liuying Photo Printer"},{"product","(Liuying Photo Printer)"},{"Color","T"},{"Duplex","F"},{"kind","photo"},{"priority","50"},{"pdl",formats},{"URF","V1.4,CP1,W8,SRGB24,RS300,DM1"},{"UUID",printerUuid(this).substring(9)}};
  for(String[] attr:attrs)info.setAttribute(attr[0],attr[1]);
  registration=new NsdManager.RegistrationListener(){
   public void onServiceRegistered(NsdServiceInfo info){main.post(()->{if(token!=advertisement.token())return;airprintName=info.getServiceName();airprintError="";advertise(advertisement.registered(token,true),announcedFormats);syncAdvertisement();});}
   public void onRegistrationFailed(NsdServiceInfo info,int code){main.post(()->{if(token!=advertisement.token())return;registration=null;advertisement.registered(token,false);announceRetry=System.currentTimeMillis()+5000;airprintError="打印机广播失败，正在重试";});}
   public void onServiceUnregistered(NsdServiceInfo info){main.post(()->{if(token!=advertisement.token())return;registration=null;airprintError="";advertise(advertisement.unregistered(token,true),announcedFormats);syncAdvertisement();});}
   public void onUnregistrationFailed(NsdServiceInfo info,int code){main.post(()->{if(token!=advertisement.token())return;advertisement.unregistered(token,false);announceRetry=System.currentTimeMillis()+5000;airprintError="打印机广播撤销未完成，正在重试";main.postDelayed(SharingService.this::syncAdvertisement,5000);});}
  };
  try{getSystemService(NsdManager.class).registerService(info,NsdManager.PROTOCOL_DNS_SD,registration);}
  catch(RuntimeException e){registration=null;advertisement.registered(token,false);announceRetry=System.currentTimeMillis()+5000;airprintError="打印机广播失败，正在重试";}
 }
 private void closeAirPrint(){if(ippApi!=null){ippApi.close();ippApi=null;}if(ipp!=null){ipp.close();ipp=null;}syncAdvertisement();}

 private void closeSharing(){closing=true;closeAirPrint();try{PrintJobs.cancelWaiting(this);}catch(Exception ignored){}main.removeCallbacks(pump);if(http!=null){http.close();http=null;}if(api!=null)api.sessions.clear();if(!running){stopForeground(STOP_FOREGROUND_REMOVE);stopSelf();}}
 @Override public void onDestroy(){closeAirPrint();main.removeCallbacks(pump);if(http!=null)http.close();if(api!=null)api.sessions.clear();if(instance==this)instance=null;super.onDestroy();}
}
