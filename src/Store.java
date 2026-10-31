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
        JSONObject job=read(c,"job.json");
        return new JSONObject().put("airprintSplice",PrinterStatus.splice).put("busy",busy).put("message",message).put("device",device).put("job",job)
            .put("unresolved",job.has("token")&&!terminal(job)).put("history",read(c,"history.json").optJSONArray("items"));
    }
    static void archive(Context c,JSONObject job)throws Exception{
        synchronized(LOCK){JSONObject history=read(c,"history.json");JSONArray old=history.optJSONArray("items"),next=new JSONArray();
            next.put(new JSONObject(job.toString()));
            if(old!=null)for(int i=0;i<old.length()&&next.length()<20;i++)if(!old.getJSONObject(i).optString("token").equals(job.optString("token")))next.put(old.get(i));
            history.put("items",next);write(c,"history.json",history);}
    }
}
