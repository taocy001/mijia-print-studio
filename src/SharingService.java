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
 private PhoneAirPrint ippApi;private LocalHttp http,ipp;private NsdManager.RegistrationListener registration;private volatile String airprintName="留影工坊 · 手机",airprintError="";private WebApi api;private volatile boolean closing,running,paused;
 private final Handler main=new Handler(Looper.getMainLooper());
 static boolean accepting(){SharingService s=instance;return s!=null&&!s.closing&&s.http!=null;}
 static JSONObject sharingState(){
  JSONObject out=new JSONObject();try{SharingService s=instance;out.put("running",accepting());if(s==null)return out;out.put("airprint",s.ipp!=null).put("airprintName",s.airprintName).put("airprintError",s.airprintError).put("paused",s.paused).put("lan",true);if(s.http==null)return out;out.put("code",s.api.sessions.code);JSONArray addresses=new JSONArray();
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
   if(instance==null){PrintJobs.cancelWaiting(this);instance=this;main.post(pump);}
   if("airprint".equals(intent.getAction())){if(ipp==null){ippApi=new PhoneAirPrint(this);ipp=new LocalHttp(true,8637,ippApi,true);announce();}}
   else if(http==null){api=new WebApi(this);http=new LocalHttp(true,8634,api);}
  }catch(Exception e){Store.message="共享服务启动失败，请检查端口或权限";if(http==null&&ipp==null){stopForeground(STOP_FOREGROUND_REMOVE);stopSelf();}}
  return START_NOT_STICKY;
 }
 private final Runnable pump=new Runnable(){public void run(){if(closing)return;PrinterStatus.refresh(SharingService.this,false);try{synchronized(Store.LOCK){if(!running&&!paused&&PrintJobs.promote(SharingService.this)){running=true;execute("print");}}}catch(Exception e){paused=true;Store.message="共享队列已暂停，请在手机上检查";}main.postDelayed(this,700);}};
 @Override protected void finished(){main.post(()->{running=false;JSONObject job=Store.read(this,"job.json");if(!"done".equals(job.optString("phase"))&&!"cancelled".equals(job.optString("phase")))paused=true;if(closing){stopForeground(STOP_FOREGROUND_REMOVE);stopSelf();}else getSystemService(NotificationManager.class).notify(2,notice(paused?"共享队列已暂停，请检查任务":"共享打印服务运行中"));});}
 static void resumeQueue(){SharingService s=instance;if(s!=null)s.main.post(()->{if(!Store.busy){JSONObject j=Store.read(s,"job.json");if(!j.has("token")||Store.terminal(j))s.paused=false;}});}
 static void checkPrinter(){SharingService s=instance;if(s!=null)PrinterStatus.refresh(s,true);}
 static void reconcile(String owner)throws Exception{SharingService s=instance;if(s==null)throw new java.io.IOException("共享服务未开启");s.main.post(()->{synchronized(Store.LOCK){JSONObject j=Store.read(s,"job.json");if(!Store.busy&&!s.running&&owner.equals(j.optString("owner"))&&j.has("jobId")&&!Store.terminal(j)){s.running=true;s.execute("reconcile");}}});}
 static void stopSharing(){SharingService s=instance;if(s!=null)s.main.post(()->{if(s.ipp==null)s.closeSharing();else{if(s.http!=null){s.http.close();s.http=null;}try{PrintJobs.cancelWaiting(s,false);}catch(Exception ignored){}if(s.api!=null)s.api.sessions.clear();}});}
 static void stopAirPrint(){SharingService s=instance;if(s!=null)s.main.post(()->{s.closeAirPrint();try{PrintJobs.cancelWaiting(s,true);}catch(Exception ignored){}if(s.http==null)s.closeSharing();});}
 static String printerUuid(Context c){android.content.SharedPreferences p=c.getSharedPreferences("printer",0);String id=p.getString("uuid",null);if(id==null){id="urn:uuid:"+UUID.randomUUID();p.edit().putString("uuid",id).apply();}return id;}
 static String printerName(Context c){SharingService s=instance;return s!=null&&s.ipp!=null?s.airprintName:defaultPrinterName(c);}
 private static String defaultPrinterName(Context c){return "留影工坊 · 手机 " + printerUuid(c).substring(9,15).toUpperCase(Locale.ROOT);}
 private void announce(){
  airprintName=defaultPrinterName(this);
  NsdServiceInfo info=new NsdServiceInfo();info.setServiceName(airprintName);info.setServiceType("_ipp._tcp");info.setPort(8637);if(Build.VERSION.SDK_INT>=35)info.setSubtypes(Collections.singleton("_universal"));
  String[][] attrs={{"txtvers","1"},{"qtotal","1"},{"rp","ipp/print"},{"ty","Liuying Photo Printer"},{"product","(Liuying Photo Printer)"},{"Color","T"},{"Duplex","F"},{"kind","photo"},{"priority","50"},{"pdl",String.join(",",AirPrintPages.FORMATS)},{"URF","V1.4,CP1,W8,SRGB24,RS300,DM1"},{"UUID",printerUuid(this).substring(9)}};
  for(String[] attr:attrs)info.setAttribute(attr[0],attr[1]);
  registration=new NsdManager.RegistrationListener(){public void onServiceRegistered(NsdServiceInfo s){airprintName=s.getServiceName();airprintError="";}public void onRegistrationFailed(NsdServiceInfo s,int code){airprintError="打印机广播失败，请重新开启 AirPrint";}public void onServiceUnregistered(NsdServiceInfo s){}public void onUnregistrationFailed(NsdServiceInfo s,int code){}};
  getSystemService(NsdManager.class).registerService(info,NsdManager.PROTOCOL_DNS_SD,registration);
 }
 private void closeAirPrint(){if(ippApi!=null){ippApi.close();ippApi=null;}if(registration!=null){try{getSystemService(NsdManager.class).unregisterService(registration);}catch(Exception ignored){}registration=null;}if(ipp!=null){ipp.close();ipp=null;}}

 private void closeSharing(){closing=true;closeAirPrint();try{PrintJobs.cancelWaiting(this);}catch(Exception ignored){}main.removeCallbacks(pump);if(http!=null){http.close();http=null;}if(api!=null)api.sessions.clear();if(!running){stopForeground(STOP_FOREGROUND_REMOVE);stopSelf();}}
 @Override public void onDestroy(){closeAirPrint();main.removeCallbacksAndMessages(null);if(http!=null)http.close();if(api!=null)api.sessions.clear();if(instance==this)instance=null;super.onDestroy();}
}
