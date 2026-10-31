package local.liuying.studio;
import android.app.Instrumentation;
import android.content.*;
import android.graphics.*;
import android.os.Bundle;
import android.util.Base64;
import java.io.*;
import org.json.*;

public final class WebJobsInstrument extends Instrumentation {
 static void check(boolean b,String m){if(!b)throw new AssertionError(m);}
 @Override public void onCreate(Bundle args){super.onCreate(args);start();}
 @Override public void onStart(){Bundle out=new Bundle();File dir=new File(getTargetContext().getCacheDir(),"queue-test-"+System.nanoTime());dir.mkdirs();Context ctx=new ContextWrapper(getTargetContext()){@Override public File getFilesDir(){return dir;}};
  try{
   Bitmap image=Bitmap.createBitmap(1040,1040,Bitmap.Config.ARGB_8888);image.eraseColor(Color.BLUE);ByteArrayOutputStream jpeg=new ByteArrayOutputStream();image.compress(Bitmap.CompressFormat.JPEG,92,jpeg);image.recycle();
   JSONObject page=new JSONObject().put("media",5009).put("base64",Base64.encodeToString(jpeg.toByteArray(),Base64.NO_WRAP));String payload=new JSONArray().put(page).toString();
   PrintJobs.submit(ctx,"alice","request-0000000001",payload);PrintJobs.submit(ctx,"alice","request-0000000001",payload);check(PrintJobs.records(ctx).length()==1,"Duplicate submission");
   boolean rejected=false;try{PrintJobs.submit(ctx,"alice","request-0000000001",new JSONArray().put(new JSONObject(page.toString()).put("copies",2)).toString());}catch(IOException e){rejected=true;}check(rejected,"Changed payload with same key");
   PrintJobs.submit(ctx,"bob","request-0000000002",payload);check(PrintJobs.state(ctx,"alice").getJSONObject("job").getString("message").contains("1"),"First queue position");check(PrintJobs.state(ctx,"bob").getJSONObject("job").getString("message").contains("2"),"Second queue position");
   check(PrintJobs.promote(ctx),"Promote first");check(!PrintJobs.promote(ctx),"No overlapping promotion");check(!PrintJobs.state(ctx,"bob").getJSONObject("job").getString("token").equals(Store.read(ctx,"job.json").getString("token")),"Private job separation");
   PrintJobs.cancel(ctx,"bob");check(!Store.terminal(Store.read(ctx,"job.json")),"Cannot cancel another owner");PrintJobs.cancel(ctx,"alice");check(Store.terminal(Store.read(ctx,"job.json")),"Cancel own prepared job");check(!PrintJobs.promote(ctx),"Cancelled queued job stays cancelled");
   int before=new File(dir,"prints").list().length;rejected=false;try{PrintJobs.submit(ctx,"alice","request-0000000003",new JSONArray().put(page).put(new JSONObject().put("media",123)).toString());}catch(Exception e){rejected=true;}check(rejected,"Invalid second page rejected");check(new File(dir,"prints").list().length==before,"Partial validation files cleaned");
   PrintJobs.submit(ctx,"alice","request-0000000004",payload);PrintJobs.cancelWaiting(ctx);check(!PrintJobs.promote(ctx),"Stopping sharing cancels waiting jobs");
   out.putString("stream","PASS: Android JPEG validation, duplicate requests, owner isolation, queue ordering, cancellation and rollback; no Bluetooth calls\n");finish(-1,out);
  }catch(Throwable e){out.putString("stream",e.toString()+"\n");finish(0,out);}finally{erase(dir);}
 }
 static void erase(File f){File[] children=f.listFiles();if(children!=null)for(File c:children)erase(c);f.delete();}
}
