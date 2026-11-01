package local.liuying.studio;
import android.content.Context;
import android.util.AtomicFile;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import org.json.*;

final class Store {
    static final Object LOCK=new Object();
    static volatile boolean busy=false;
    static volatile boolean cancel=false;
    static volatile String message="点击连接打印机";
    static volatile JSONObject device=new JSONObject();
    static JSONObject read(Context c,String name){
        synchronized(LOCK){try{return new JSONObject(new String(new AtomicFile(new File(c.getFilesDir(),name)).readFully(),StandardCharsets.UTF_8));}
            catch(Exception e){return new JSONObject();}}
    }
    static void write(Context c,String name,JSONObject value)throws Exception{
        synchronized(LOCK){AtomicFile file=new AtomicFile(new File(c.getFilesDir(),name));FileOutputStream f=null;
            try{f=file.startWrite();f.write(value.toString().getBytes(StandardCharsets.UTF_8));file.finishWrite(f);}
            catch(Exception e){if(f!=null)file.failWrite(f);throw e;}}
    }
    static boolean terminal(JSONObject job){String s=job.optString("phase");return s.equals("done")||s.equals("cancelled")||s.equals("aborted")||s.equals("rejected");}
    static JSONObject state(Context c)throws Exception{
        JSONObject job=HistoryStorage.publicJob(read(c,"job.json"));JSONArray history=read(c,"history.json").optJSONArray("items"),visible=new JSONArray();
        if(history!=null)for(int i=0;i<history.length();i++)visible.put(HistoryStorage.publicJob(history.getJSONObject(i)));
        return new JSONObject().put("airprintSplice",PrinterStatus.splice).put("busy",busy).put("message",message).put("device",device).put("job",job)
            .put("unresolved",job.has("token")&&!terminal(job)).put("history",visible).put("failure",HistoryStorage.publicJob(read(c,"failure.json")));
    }
    static void batchFailure(Context c,JSONObject job)throws Exception{
        job.put("batchStopped",true);
        failure(c,"batch-"+job.optString("batchId",job.optString("token")),job.optString("owner"),"batch","本张照片已完成，后续照片准备失败，未继续发送。请检查打印记录后再处理剩余照片");
        try{write(c,"job.json",job);}catch(Exception e){android.util.Log.w("LiuyingPrint","Batch stop state could not be saved");}
    }
    static void recover(Context c)throws Exception{
        synchronized(LOCK){JSONObject job=read(c,"job.json");String phase=job.optString("phase");
            if(!busy&&job.has("token")&&(phase.equals("creating")||phase.equals("uploading")||phase.equals("printing"))){
                job.put("phase","uncertain").put("message","上次打印期间 App 已中断，请检查原任务与出纸结果；不会自动重印");write(c,"job.json",job);archive(c,job);messageFailure(c,job);PrintJobs.finish(c,job);
            }
        }
    }
    static void failure(Context c,String token,String owner,String stage,String message)throws Exception{
        JSONObject failure=new JSONObject().put("token",token).put("owner",owner).put("phase","rejected").put("title",owner.equals("local")?"照片打印":"AirPrint 打印")
            .put("stage",stage).put("message",message).put("createdAt",System.currentTimeMillis()).put("media",PrinterStatus.media());
        messageFailure(c,failure);archive(c,failure);
    }
    static void messageFailure(Context c,JSONObject job)throws Exception{Store.message=job.optString("message");write(c,"failure.json",job);}
    static void archive(Context c,JSONObject job)throws Exception{
        synchronized(LOCK){JSONObject history=read(c,"history.json");JSONArray old=history.optJSONArray("items"),next=new JSONArray();
            JSONObject copy=new JSONObject(job.toString());
            if(old!=null)for(int i=0;i<old.length();i++){JSONObject prior=old.getJSONObject(i);if(prior.optString("token").equals(job.optString("token"))&&prior.optBoolean("filesCleared"))copy.put("filesCleared",true).put("cleanupPending",prior.optBoolean("cleanupPending"));}
            next.put(copy);
            if(old!=null)for(int i=0;i<old.length()&&next.length()<20;i++)if(!old.getJSONObject(i).optString("token").equals(job.optString("token")))next.put(old.get(i));
            history.put("items",next);write(c,"history.json",history);}
    }
}
