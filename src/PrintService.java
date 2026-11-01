package local.liuying.studio;
import android.app.*;
import android.content.*;
import android.os.*;
import android.graphics.BitmapFactory;
import java.io.*;
import java.nio.file.Files;
import org.json.*;

public class PrintService extends Service {
    private JSONObject job;
    private boolean stopBatch=false;
    protected boolean batchFailed=false;
    private PowerManager.WakeLock wake;
    @Override public IBinder onBind(Intent intent){return null;}
    protected Notification notice(String text){
        Intent open=new Intent(this,MainActivity.class);
        PendingIntent pending=PendingIntent.getActivity(this,0,open,PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
        return new Notification.Builder(this,"print").setSmallIcon(R.drawable.icon).setContentTitle("留影工坊")
            .setContentText(text).setContentIntent(pending).setOngoing(Store.busy).build();
    }
    private void update(String phase,String message,int progress)throws Exception{
        job.put("phase",phase).put("message",message).put("progress",progress).put("updatedAt",System.currentTimeMillis());
        if(job.optInt("batchCount",1)>1){message="第 "+job.optInt("batchIndex",1)+" / "+job.optInt("batchCount",1)+" 个作品 · "+message;job.put("message",message);}
        Store.message=message;Store.write(this,"job.json",job);
        if(Store.terminal(job)||phase.equals("blocked")||phase.equals("uncertain")||phase.equals("held"))Store.archive(this,job);
        if(phase.equals("rejected")||phase.equals("aborted")||phase.equals("blocked")||phase.equals("uncertain")||phase.equals("held"))Store.messageFailure(this,job);
        getSystemService(NotificationManager.class).notify(notificationId(),notice(message));
    }
    @Override public int onStartCommand(Intent intent,int flags,int startId){
        NotificationManager manager=getSystemService(NotificationManager.class);
        manager.createNotificationChannel(new NotificationChannel("print","照片打印",NotificationManager.IMPORTANCE_LOW));
        startForeground(1,notice("正在连接打印机…"));
        if(intent==null){stopSelf();return START_NOT_STICKY;}
        execute(intent.getStringExtra("action"));return START_NOT_STICKY;
    }
    protected int notificationId(){return 1;}
    protected void finished(){stopForeground(STOP_FOREGROUND_REMOVE);stopSelf();}
    protected void execute(String action){

        if("cancel".equals(action)&&Store.busy){Store.cancel=true;return;}
        synchronized(Store.LOCK){if(Store.busy){return;}Store.busy=true;PrinterStatus.runningSession=true;PrinterStatus.verifiedSession=false;Store.cancel=false;stopBatch=false;batchFailed=false;job=null;}
        wake=getSystemService(PowerManager.class).newWakeLock(PowerManager.PARTIAL_WAKE_LOCK,"liuying:print");wake.acquire(600000);
        new Thread(()->{
            try(Printer printer=new Printer(this)){
                job=Store.read(this,"job.json");
                if(!job.has("token"))throw new IOException("没有待处理任务");
                Store.device=printer.status();PrinterStatus.verifiedSession=true;
                if("print".equals(action))startPrint(printer);
                else if("cancel".equals(action)){
                    int id=job.optInt("jobId",0);if(id<=0)throw new IOException("未取得任务编号，不能自动取消。请在米家中检查任务。");
                    printer.rpc("cancel-job",new JSONObject().put("job-id",id));monitor(printer);
                }else monitor(printer);
                // Advance only after a confirmed completion in this uninterrupted print run.
                while(true){
                    JSONObject next=BatchQueue.next(job,"print".equals(action)&&!stopBatch&&!Store.cancel);
                    if(next==null)break;
                    Store.write(this,"job.json",next);job=next;
                    Store.device=printer.status();startPrint(printer);
                }
            }catch(Exception e){
                PrinterStatus.invalidate();
                try{if(job==null)job=Store.read(this,"job.json");
                    if("done".equals(job.optString("phase"))&&job.optJSONArray("remaining")!=null&&job.getJSONArray("remaining").length()>0){stopBatch=true;batchFailed=true;Store.batchFailure(this,job);}
                    else if(!Store.terminal(job)){
                        boolean untouched="prepared".equals(job.optString("phase"));
                        update(untouched?"rejected":job.has("jobId")?"uncertain":"blocked",
                            untouched?"尚未提交打印："+friendly(e):"操作未完成："+friendly(e)+"。请检查任务，不要重复打印。",job.optInt("progress",0));}}
                catch(Exception ignored){}android.util.Log.e("LiuyingPrint","Print failed",e);
            }finally{
                try{if(job!=null&&job.has("token"))PrintJobs.finish(this,job);}catch(Exception e){android.util.Log.e("LiuyingPrint","Queue state could not be saved",e);}
                synchronized(Store.LOCK){PrinterStatus.verifiedSession=false;PrinterStatus.runningSession=false;Store.busy=false;Store.cancel=false;}
                SharingService.refreshAdvertisement();
                if(wake!=null&&wake.isHeld())wake.release();finished();
            }
        },"liuying-print").start();
    }
    private static String friendly(Exception e){String text=e.getMessage();return text==null||text.matches("(?s)[\\x00-\\x7F]*")?"蓝牙通讯中断或连接超时，请检查打印机电源和连接":text;}
    private void startPrint(Printer printer)throws Exception{
        if(!"prepared".equals(job.optString("phase")))throw new IOException("任务已经提交，禁止重复创建");
        byte[] jpeg=Files.readAllBytes(new File(getFilesDir(),job.getString("file")).toPath());
        int media=job.getInt("media");BitmapFactory.Options b=new BitmapFactory.Options();b.inJustDecodeBounds=true;BitmapFactory.decodeByteArray(jpeg,0,jpeg.length,b);
        if(jpeg.length>1048576||jpeg.length<4||b.outWidth!=(media==5009?1040:1216)||b.outHeight!=(media==5009?1040:1824))throw new IOException("照片尺寸不正确");
        int tray=Store.device.optInt("media");
        if(tray!=(media==5014?5012:media)){update("rejected","纸盒与选择的相纸不一致，请核对后重试",0);return;}
        String alert=PrinterAlerts.describe(Store.device.optString("alert"));if(!alert.isEmpty()){update("rejected",alert+"。照片尚未提交",0);return;}
        if(Store.device.optInt("ribbon",-1)==0){update("rejected","色带已耗尽，请更换色带。照片尚未提交",0);return;}
        JSONObject queue=printer.rpc("get-job-id-list",new JSONObject()).getJSONObject("result");
        if(!"".equals(queue.getString("job-id-list"))){update("rejected","打印机还有任务，请等待完成",0);return;}
        byte[] coat=job.optString("ocFile").isEmpty()?null:Files.readAllBytes(new File(getFilesDir(),job.getString("ocFile")).toPath());
        if(coat!=null&&(coat.length!=job.optInt("ocBytes")||coat.length<32||coat.length>1048576))throw new IOException("覆膜文件不完整");
        byte[] data=Wire.jobData(coat,jpeg);int totalBytes=data.length;
        update("creating","正在创建打印任务…",0);
        JSONObject answer=printer.rpc("print-job",new JSONObject().put("copies",job.optInt("copies",1)).put("file-size",totalBytes).put("job-type",0)
            .put("file-type","jpg").put("media-size",media).put("channel",576).put("sharpenmode",job.optInt("sharpen",0)));
        job.put("createResponse",answer);Store.write(this,"job.json",job);
        JSONObject result=answer.optJSONObject("result");
        if(result!=null&&result.optInt("error-code",0)!=0){update("rejected","打印机拒绝任务："+result.optInt("error-code"),0);return;}
        int id=result==null?0:result.optInt("job-id",result.optInt("job_id",0));
        if(id<=0)throw new IOException("创建结果无法确认");
        job.put("jobId",id);update("uploading","正在传送照片…",0);
        JSONObject before=printer.job(id);job.put("lastInfo",before);Store.write(this,"job.json",job);
        if(before.optInt("job-state",-1)!=1||before.optInt("transfer-size",-1)!=0)throw new IOException("打印任务不是待接收状态");
        printer.upload(id,data,p->update("uploading","正在传送照片"+(coat==null?"":"与覆膜")+" · "+p+"%",p));
        update("printing","照片已发送，等待打印机完成",-1);monitor(printer);
    }
    static String transferFailure(JSONObject info){
        long expected=info.optLong("file-size",-1),received=info.optLong("transfer-size",-1);
        return info.optInt("transfer-status",-1)==3&&expected>0&&received>=0&&received<expected?"照片传输不完整（缺少 "+(expected-received)+" 字节），打印机已中止；未自动重试":"";
    }
    private String printerFailure(Printer printer,String fallback){
        try{Store.device=printer.status();String alert=PrinterAlerts.describe(Store.device.optString("alert"));if(!alert.isEmpty())return alert;if(Store.device.optInt("ribbon",-1)==0)return "色带已耗尽，请更换色带";}catch(Exception ignored){}
        return fallback;
    }
    private void monitor(Printer printer)throws Exception{
        int id=job.optInt("jobId",0);if(id<=0)throw new IOException("创建结果未知，请在米家中检查打印队列");
        for(int n=0;n<150;n++){
            if(Store.cancel){stopBatch=true;printer.rpc("cancel-job",new JSONObject().put("job-id",id));Store.cancel=false;}
            JSONObject info=printer.job(id);job.put("lastInfo",info);
            JSONObject snapshot=new JSONObject();for(String key:new String[]{"job-state","job-sub-state","transfer-size","file-size","print-time","printing-page-number"}){Object value=info.opt(key);if(value instanceof Number)snapshot.put(key,value);}
            job.put("telemetry",new JSONObject().put("stage","waiting").put("sampleAt",System.currentTimeMillis()).put("device",snapshot));
            int state=info.optInt("job-state",-1);
            if(state==9){update("done","打印完成，留住这一刻。",100);Store.archive(this,job);return;}
            if(state==7||state==8){update(state==8?"cancelled":"aborted",state==8?"任务已取消":transferFailure(info).isEmpty()?printerFailure(printer,"打印机已中止任务"):transferFailure(info),0);Store.archive(this,job);return;}
            if(state==5){Store.device=printer.status();update("held","打印暂停 · "+printerFailure(printer,"请检查相纸、色带或卡纸"),-1);return;}
            if(state<0)throw new IOException("无法识别任务状态");
            update("printing",state==1?"已传送，等待打印机确认数据…":"正在打印 · 请勿抽拉相纸",-1);Thread.sleep(2000);
        }
        throw new IOException("等待打印结果超时");
    }
}
