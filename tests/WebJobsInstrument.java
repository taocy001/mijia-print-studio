package local.liuying.studio;
import android.app.Instrumentation;
import android.content.*;
import android.graphics.*;
import android.os.Bundle;
import android.util.Base64;
import java.io.*;
import java.nio.file.Files;
import java.util.Arrays;
import org.json.*;

public final class WebJobsInstrument extends Instrumentation {
 static void check(boolean b,String m){if(!b)throw new AssertionError(m);}
 @Override public void onCreate(Bundle args){super.onCreate(args);start();}
 @Override public void onStart(){Bundle out=new Bundle();File dir=new File(getTargetContext().getCacheDir(),"queue-test-"+System.nanoTime());dir.mkdirs();Context ctx=new ContextWrapper(getTargetContext()){@Override public File getFilesDir(){return dir;}};
  boolean released=PrinterStatus.released;
  try{
   check(!Store.busy&&!Store.state(getTargetContext()).optBoolean("unresolved"),"Stop real jobs before isolated queue tests");PrinterStatus.released=false;
   Bitmap image=Bitmap.createBitmap(1040,1040,Bitmap.Config.ARGB_8888);image.eraseColor(Color.BLUE);ByteArrayOutputStream jpeg=new ByteArrayOutputStream();image.compress(Bitmap.CompressFormat.JPEG,92,jpeg);image.recycle();
   JSONObject page=new JSONObject().put("media",5009).put("base64",Base64.encodeToString(jpeg.toByteArray(),Base64.NO_WRAP));String payload=new JSONArray().put(page).toString();
   PrintJobs.submit(ctx,"alice","request-0000000001",payload);PrintJobs.submit(ctx,"alice","request-0000000001",payload);check(PrintJobs.records(ctx).length()==1,"Duplicate submission");
   boolean rejected=false;try{PrintJobs.submit(ctx,"alice","request-0000000001",new JSONArray().put(new JSONObject(page.toString()).put("copies",2)).toString());}catch(IOException e){rejected=true;}check(rejected,"Changed payload with same key");
   PrintJobs.submit(ctx,"bob","request-0000000002",payload);check(PrintJobs.state(ctx,"alice").getJSONObject("job").getString("message").contains("1"),"First queue position");check(PrintJobs.state(ctx,"bob").getJSONObject("job").getString("message").contains("2"),"Second queue position");
   check(PrintJobs.promote(ctx),"Promote first");check(!PrintJobs.promote(ctx),"No overlapping promotion");check(!PrintJobs.state(ctx,"bob").getJSONObject("job").getString("token").equals(Store.read(ctx,"job.json").getString("token")),"Private job separation");
   PrintJobs.cancel(ctx,"bob");check(!Store.terminal(Store.read(ctx,"job.json")),"Cannot cancel another owner");PrintJobs.cancel(ctx,"alice");check(Store.terminal(Store.read(ctx,"job.json")),"Cancel own prepared job");check(!PrintJobs.promote(ctx),"Cancelled queued job stays cancelled");
   int before=new File(dir,"prints").list().length;rejected=false;try{PrintJobs.submit(ctx,"alice","request-0000000003",new JSONArray().put(page).put(new JSONObject().put("media",123)).toString());}catch(Exception e){rejected=true;}check(rejected,"Invalid second page rejected");check(new File(dir,"prints").list().length==before,"Partial validation files cleaned");
   PrintJobs.submit(ctx,"alice","request-0000000004",payload);PrintJobs.cancelWaiting(ctx);check(!PrintJobs.promote(ctx),"Stopping sharing cancels waiting jobs");
   Bitmap mask=Bitmap.createBitmap(1040,1040,Bitmap.Config.ARGB_8888);mask.eraseColor(Color.WHITE);ByteArrayOutputStream png=new ByteArrayOutputStream();mask.compress(Bitmap.CompressFormat.PNG,100,png);mask.recycle();
   JSONObject firstOptions=new JSONObject(page.toString()).put("copies",2).put("sharpen",1).put("ocMask",Base64.encodeToString(png.toByteArray(),Base64.NO_WRAP));JSONObject secondOptions=new JSONObject(page.toString()).put("copies",3).put("sharpen",2);
   JSONObject original=PrintJobs.prepare(ctx,"alice","original-batch-0001",new JSONArray().put(firstOptions).put(secondOptions).toString());original.put("phase","done");Store.archive(ctx,original);
   check(!Reprints.decorate(ctx,"alice",new JSONObject(original.toString())).getBoolean("canReprint"),"Incomplete completed batch cannot reprint");JSONObject second=BatchQueue.next(original,true);second.put("phase","done");Store.archive(ctx,second);
   JSONArray summary=Reprints.decorate(ctx,"alice",new JSONObject(original.toString())).getJSONArray("reprintPages");check(summary.length()==2&&summary.getJSONObject(0).getInt("copies")==2&&summary.getJSONObject(1).getInt("copies")==3,"Original per-page counts exposed");
   String source=original.getString("token"),reprintId="reprint-request-0001";int count=PrintJobs.records(ctx).length();
   rejected=false;try{Reprints.submit(ctx,"alice",source,reprintId,false,false);}catch(IOException e){rejected=true;}check(rejected&&PrintJobs.records(ctx).length()==count,"Explicit confirmation required");
   rejected=false;try{Reprints.submit(ctx,"bob",source,reprintId,true,false);}catch(IOException e){rejected=true;}check(rejected&&PrintJobs.records(ctx).length()==count,"Other owner cannot reprint");
   byte[] originalJpeg=Files.readAllBytes(new File(dir,original.getString("file")).toPath()),originalCoat=Files.readAllBytes(new File(dir,original.getString("ocFile")).toPath());
   check(Reprints.submit(ctx,"alice",source,reprintId,true,false).getBoolean("ok"),"Exact batch accepted");JSONObject copy=PrintJobs.records(ctx).getJSONObject(count),copySecond=copy.getJSONArray("remaining").getJSONObject(0);
   check(!copy.getString("token").equals(source)&&!copy.getString("batchId").equals(original.getString("batchId")),"New job identity");
   for(String key:new String[]{"file","bytes","ocFile","ocBytes","media","copies","sharpen","title","orientation"}){if(original.has(key))check(original.get(key).equals(copy.get(key)),"First page unchanged: "+key);if(second.has(key))check(second.get(key).equals(copySecond.get(key)),"Second page unchanged: "+key);}
   check(Arrays.equals(originalJpeg,Files.readAllBytes(new File(dir,copy.getString("file")).toPath()))&&Arrays.equals(originalCoat,Files.readAllBytes(new File(dir,copy.getString("ocFile")).toPath())),"JPEG and compressed OC bytes identical");
   PrinterStatus.released=true;check(Reprints.submit(ctx,"alice",source,reprintId,true,false).optBoolean("duplicate")&&PrintJobs.records(ctx).length()==count+1,"Lost response retry acknowledged once even after release");PrinterStatus.released=false;
   rejected=false;try{Reprints.submit(ctx,"alice",second.getString("token"),reprintId,true,false);}catch(IOException e){rejected=true;}check(rejected,"Request ID cannot switch source");
   JSONObject local=PrintJobs.prepare(ctx,"local","local-original-0001",payload);local.put("phase","done");Store.archive(ctx,local);rejected=false;try{Reprints.submit(ctx,"local",local.getString("token"),"local-reprint-0001",true,true);}catch(IOException e){rejected=true;}check(rejected,"Local reprint cannot start a remote pending queue");PrintJobs.cancelWaiting(ctx);
   check(Reprints.submit(ctx,"local",local.getString("token"),"local-reprint-0001",true,true).getBoolean("startable"),"Local exact reprint ready for explicit service start");check(PrintJobs.state(ctx,"local").getJSONObject("job").optString("phase").equals("queued"),"Unstarted local reprint visible after rereading storage");PrintJobs.cancel(ctx,"local");
   File coatFile=new File(dir,original.getString("ocFile"));check(coatFile.delete(),"Remove isolated old coat fixture");check(!Reprints.decorate(ctx,"alice",new JSONObject(original.toString())).getBoolean("canReprint"),"Missing OC disables exact reprint");rejected=false;try{Reprints.submit(ctx,"alice",source,"missing-file-0001",true,false);}catch(IOException e){rejected=true;}check(rejected,"Missing original file rejects whole batch");
   out.putString("stream","PASS: Android JPEG validation, duplicate requests, owner isolation, queue ordering, cancellation rollback and exact history reprint ownership, confirmation, byte identity, per-page parameters, deduplication and missing-file safety; no Bluetooth calls\n");finish(-1,out);
  }catch(Throwable e){out.putString("stream",e.toString()+"\n");finish(0,out);}finally{PrinterStatus.released=released;erase(dir);}
 }
 static void erase(File f){File[] children=f.listFiles();if(children!=null)for(File c:children)erase(c);f.delete();}
}
