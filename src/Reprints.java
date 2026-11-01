package local.liuying.studio;
import android.content.Context;
import android.graphics.BitmapFactory;
import java.io.*;
import java.nio.file.Files;
import java.util.*;
import org.json.*;

final class Reprints {
 private static File file(Context c,String name,String suffix)throws IOException{
  if(!name.matches("prints/[a-zA-Z0-9-]+"+java.util.regex.Pattern.quote(suffix)))throw new IOException("历史作品文件无效");
  File root=new File(c.getFilesDir(),"prints").getCanonicalFile(),f=new File(c.getFilesDir(),name).getCanonicalFile();
  if(!root.equals(f.getParentFile())||!f.isFile()||f.length()<4||f.length()>1048576)throw new IOException("历史作品文件已缺失或不完整");return f;
 }
 static JSONArray pages(Context c,String owner,String token)throws Exception{
  JSONArray history=Store.read(c,"history.json").optJSONArray("items");JSONObject source=null;
  if(history!=null)for(int i=0;i<history.length();i++){JSONObject j=history.getJSONObject(i);if(token.equals(j.optString("token"))&&owner.equals(j.optString("owner")))source=j;}
  if(source==null||(!source.optString("phase").equals("done")||source.optBoolean("filesCleared")))throw new IOException("只能重印本人的已完成作品");
  int count=source.optInt("batchCount",1);if(count<1||count>6)throw new IOException("历史批次无效");
  JSONObject[] ordered=new JSONObject[count];String batch=source.optString("batchId");
  for(int i=0;i<history.length();i++){JSONObject j=history.getJSONObject(i);if(!owner.equals(j.optString("owner"))||!(batch.isEmpty()?token.equals(j.optString("token")):batch.equals(j.optString("batchId"))))continue;
   int index=j.optInt("batchIndex",1)-1;if(index<0||index>=count||ordered[index]!=null||j.optInt("batchCount",1)!=count||!j.optString("phase").equals("done")||j.optBoolean("batchStopped")||j.optBoolean("filesCleared"))throw new IOException("该批次尚未全部完成");ordered[index]=j;
  }
  JSONArray pages=new JSONArray();for(JSONObject j:ordered){if(j==null)throw new IOException("历史批次不完整，无法原样重印");file(c,j.optString("file"),".jpg");if(!j.optString("ocFile").isEmpty())file(c,j.optString("ocFile"),".oc");pages.put(j);}return pages;
 }
 static JSONObject decorate(Context c,String owner,JSONObject job)throws Exception{
  job.put("canReprint",false);job.remove("reprintPages");try{JSONArray pages=pages(c,owner,job.optString("token")),summary=new JSONArray();for(int i=0;i<pages.length();i++){JSONObject p=pages.getJSONObject(i);summary.put(new JSONObject().put("copies",p.optInt("copies",1)).put("media",p.getInt("media")));}job.put("canReprint",true).put("reprintPages",summary);}catch(Exception ignored){}return job;
 }
 static JSONObject submit(Context c,String owner,String token,String requestId,boolean confirmed,boolean local)throws Exception{
  synchronized(Store.LOCK){
   if(!confirmed)throw new IOException("请确认按原参数重新打印");if(!requestId.matches("[a-zA-Z0-9-]{16,80}"))throw new IOException("打印请求无效");
   JSONArray queue=PrintJobs.compact(c);for(int i=0;i<queue.length();i++){JSONObject j=queue.getJSONObject(i);if(owner.equals(j.optString("owner"))&&requestId.equals(j.optString("requestId"))){if(!token.equals(j.optString("reprintSource")))throw new IOException("请求已用于其他作品");return new JSONObject().put("ok",true).put("duplicate",true).put("startable",local&&j.optString("phase").equals("queued")&&JobRetention.pending(queue)==1);}}
   if(PrinterStatus.released)throw new IOException("蓝牙已释放，请先连接手机");if(JobRetention.pending(queue)>=12)throw new IOException("共享队列已满，请处理后重试");
   JSONObject current=Store.read(c,"job.json");if(local&&(JobRetention.pending(queue)>0||Store.busy||current.has("token")&&!Store.terminal(current)))throw new IOException("请先处理当前打印任务");
   JSONArray originals=pages(c,owner,token),jobs=new JSONArray();String batch=UUID.randomUUID().toString();
   for(int i=0;i<originals.length();i++){JSONObject old=originals.getJSONObject(i);byte[] jpeg=Files.readAllBytes(file(c,old.getString("file"),".jpg").toPath());int media=old.getInt("media"),copies=old.optInt("copies",1),sharpen=old.optInt("sharpen",0);
    if((media!=5009&&media!=5012&&media!=5014)||copies<1||copies>10||sharpen<0||sharpen>2||jpeg.length!=old.optInt("bytes",jpeg.length)||jpeg[0]!=(byte)255||jpeg[1]!=(byte)216)throw new IOException("历史打印参数或照片无效");
    BitmapFactory.Options bounds=new BitmapFactory.Options();bounds.inJustDecodeBounds=true;BitmapFactory.decodeByteArray(jpeg,0,jpeg.length,bounds);if(bounds.outWidth!=(media==5009?1040:1216)||bounds.outHeight!=(media==5009?1040:1824))throw new IOException("历史照片尺寸无效");
    if(!old.optString("ocFile").isEmpty()){byte[] coat=Files.readAllBytes(file(c,old.getString("ocFile"),".oc").toPath());if(coat.length<32||coat.length!=old.optInt("ocBytes"))throw new IOException("历史覆膜文件不完整");}
    JSONObject job=new JSONObject();for(String key:new String[]{"file","bytes","ocFile","ocBytes","media","copies","sharpen","title","orientation"})if(old.has(key))job.put(key,old.get(key));
    job.put("token",UUID.randomUUID().toString()).put("owner",owner).put("requestId",requestId).put("reprintSource",token).put("batchId",batch).put("batchIndex",i+1).put("batchCount",originals.length()).put("createdAt",System.currentTimeMillis()).put("phase","prepared").put("message","准备打印…").put("progress",0);jobs.put(job);
   }
   JSONObject first=jobs.getJSONObject(0);JSONArray remaining=new JSONArray();for(int i=1;i<jobs.length();i++)remaining.put(jobs.getJSONObject(i));first.put("remaining",remaining).put("phase","queued").put("message","已加入打印队列");queue.put(first);PrintJobs.persist(c,queue);return new JSONObject().put("ok",true).put("startable",local);
  }
 }
}
