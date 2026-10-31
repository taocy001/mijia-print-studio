package local.liuying.studio;
import android.content.Context;
import android.graphics.BitmapFactory;
import android.util.Base64;
import java.io.*;
import java.util.*;
import java.security.MessageDigest;
import org.json.*;

final class PrintJobs {
 static String digest(String value)throws Exception{byte[] bytes=MessageDigest.getInstance("SHA-256").digest(value.getBytes("UTF-8"));StringBuilder b=new StringBuilder();for(byte v:bytes)b.append(String.format(Locale.ROOT,"%02x",v&255));return b.toString();}
 static JSONArray records(Context c){JSONArray a=Store.read(c,"web-queue.json").optJSONArray("items");return a==null?new JSONArray():a;}
 static void persist(Context c,JSONArray a)throws Exception{Store.write(c,"web-queue.json",new JSONObject().put("items",a));}
 static JSONObject submit(Context context,String owner,String requestId,String payload)throws Exception{
  synchronized(Store.LOCK){
   if(!requestId.matches("[a-zA-Z0-9-]{16,80}")||payload.length()>18000000)throw new IOException("打印请求无效");
   JSONArray all=records(context);String hash=digest(payload);int pending=0;
   for(int i=0;i<all.length();i++){JSONObject r=all.getJSONObject(i);if(owner.equals(r.optString("owner"))&&requestId.equals(r.optString("requestId"))){if(!hash.equals(r.optString("digest")))throw new IOException("请求内容已变化，请重新预览");return new JSONObject().put("ok",true).put("duplicate",true);}
    if("queued".equals(r.optString("phase")))pending++;}
   if(pending>=12||all.length()>=128)throw new IOException("共享队列已满，请在手机上处理后重试");
   JSONObject first=prepare(context,owner,requestId,payload);first.put("phase","queued").put("message","已加入打印队列").put("digest",hash);all.put(first);persist(context,all);
   return new JSONObject().put("ok",true);
  }
 }
 static JSONObject prepare(Context context,String owner,String requestId,String payload)throws Exception{
  List<File> created=new ArrayList<>();try{
                    JSONArray pages=new JSONArray(payload),jobs=new JSONArray();
                    if(pages.length()<1||pages.length()>6)throw new IOException("每次最多打印 6 张相纸");
                    String batch=UUID.randomUUID().toString();new File(context.getFilesDir(),"prints").mkdirs();
                    for(int i=0;i<pages.length();i++){
                        JSONObject options=pages.getJSONObject(i);int media=options.getInt("media");
                        if(media!=5009&&media!=5012&&media!=5014)throw new IOException("相纸类型不支持");
                        String base64=options.getString("base64");if(base64.length()>1500000)throw new IOException("照片过大");
                        byte[] bytes=Base64.decode(base64,Base64.DEFAULT);
                        BitmapFactory.Options bounds=new BitmapFactory.Options();bounds.inJustDecodeBounds=true;BitmapFactory.decodeByteArray(bytes,0,bytes.length,bounds);
                        if(bytes.length>1048576||bytes.length<4||bytes[0]!=(byte)255||bytes[1]!=(byte)216||bounds.outWidth!=(media==5009?1040:1216)||bounds.outHeight!=(media==5009?1040:1824))throw new IOException("输出照片尺寸或格式不正确");
                        int copies=options.optInt("copies",1);if(copies<1||copies>10)throw new IOException("每个作品最多 10 份");
                        int sharpen=options.optInt("sharpen",0);if(sharpen<0||sharpen>2)throw new IOException("锐度参数无效");
                        byte[] coat=null;
                        if(!options.isNull("ocMask")&&options.has("ocMask")){
                            String encoded=options.getString("ocMask");if(encoded.length()>1500000)throw new IOException("覆膜数据过大");
                            coat=Overcoat.encode(Base64.decode(encoded,Base64.DEFAULT),options.optInt("threshold",100),media);
                        }
                        String token=UUID.randomUUID().toString(),file="prints/"+token+".jpg";
                        created.add(new File(context.getFilesDir(),file));
                    try(FileOutputStream out=new FileOutputStream(new File(context.getFilesDir(),file))){out.write(bytes);out.getFD().sync();}
                        String coatFile="";
                        if(coat!=null){coatFile="prints/"+token+".oc";created.add(new File(context.getFilesDir(),coatFile));try(FileOutputStream out=new FileOutputStream(new File(context.getFilesDir(),coatFile))){out.write(coat);out.getFD().sync();}}
                        jobs.put(new JSONObject().put("copies",copies).put("ocFile",coatFile).put("ocBytes",coat==null?0:coat.length).put("sharpen",sharpen).put("token",token).put("file",file).put("media",media).put("phase","prepared")
                            .put("title",options.optString("title","照片")).put("orientation",options.optString("orientation","portrait"))
                            .put("owner",owner).put("requestId",requestId).put("batchId",batch).put("batchIndex",i+1).put("batchCount",pages.length())
                            .put("createdAt",System.currentTimeMillis()).put("bytes",bytes.length).put("message","准备打印…").put("progress",0));
                    }
                    JSONObject first=jobs.getJSONObject(0);JSONArray remaining=new JSONArray();for(int i=1;i<jobs.length();i++)remaining.put(jobs.get(i));first.put("remaining",remaining);

  return first;
  }catch(Exception e){for(File f:created)f.delete();throw e;}
 }
 static boolean promote(Context c)throws Exception{
  synchronized(Store.LOCK){if(Store.busy)return false;JSONObject old=Store.read(c,"job.json");if(old.has("token")&&!Store.terminal(old))return false;
   JSONArray all=records(c);for(int i=0;i<all.length();i++){JSONObject record=all.getJSONObject(i);if(!"queued".equals(record.optString("phase")))continue;
    JSONObject job=new JSONObject(record.toString());job.put("phase","prepared").put("message","准备打印…");Store.write(c,"job.json",job);record.put("phase","active");persist(c,all);return true;
   }return false;
  }
 }
 static JSONObject state(Context c,String owner)throws Exception{
  synchronized(Store.LOCK){JSONObject current=Store.read(c,"job.json"),own=new JSONObject();JSONArray all=records(c),history=new JSONArray();int position=0;
   if(owner.equals(current.optString("owner")))own=current;
   for(int i=0;i<all.length();i++){JSONObject record=all.getJSONObject(i);if("queued".equals(record.optString("phase"))){position++;if(owner.equals(record.optString("owner"))&&(!own.has("token")||Store.terminal(own))){own=new JSONObject(record.toString());own.put("message","等待打印 · 队列第 "+position+" 个");}}}
   JSONArray stored=Store.read(c,"history.json").optJSONArray("items");if(stored!=null)for(int i=0;i<stored.length();i++)if(owner.equals(stored.getJSONObject(i).optString("owner")))history.put(publicJob(stored.getJSONObject(i)));
   boolean unresolved=own.has("token")&&!Store.terminal(own);return new JSONObject().put("permission",true).put("busy",Store.busy&&owner.equals(current.optString("owner"))&&!Store.terminal(current)).put("unresolved",unresolved).put("job",publicJob(own)).put("history",history).put("device",publicDevice()).put("message",own.optString("message",Store.message));
  }
 }
 private static JSONObject publicDevice()throws Exception{JSONObject out=new JSONObject();for(String key:new String[]{"connected","name","state","alert","media","ribbon","checkedAt"})if(Store.device.has(key))out.put(key,Store.device.get(key));return out;}
 private static JSONObject publicJob(JSONObject job)throws Exception{JSONObject out=new JSONObject();for(String key:new String[]{"token","phase","message","progress","file","title","media","orientation","createdAt","copies","batchIndex","batchCount","jobId"})if(job.has(key))out.put(key,job.get(key));return out;}
 static void cancelWaiting(Context c)throws Exception{synchronized(Store.LOCK){JSONArray all=records(c);for(int i=0;i<all.length();i++){JSONObject r=all.getJSONObject(i);if("queued".equals(r.optString("phase")))r.put("phase","cancelled").put("message","共享已停止，尚未打印的任务已取消");}persist(c,all);}}
 static void cancel(Context c,String owner)throws Exception{
  synchronized(Store.LOCK){JSONArray all=records(c);for(int i=0;i<all.length();i++){JSONObject r=all.getJSONObject(i);if(owner.equals(r.optString("owner"))&&"queued".equals(r.optString("phase")))r.put("phase","cancelled");}persist(c,all);
   JSONObject current=Store.read(c,"job.json");if(owner.equals(current.optString("owner"))&&!Store.terminal(current)){if(Store.busy)Store.cancel=true;else if("prepared".equals(current.optString("phase"))){current.put("phase","cancelled");Store.write(c,"job.json",current);}else throw new IOException("请在手机上检查当前任务");}
  }
 }
}
