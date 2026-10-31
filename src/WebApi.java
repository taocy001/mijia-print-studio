package local.liuying.studio;
import android.content.Context;
import android.graphics.*;
import java.io.*;
import java.nio.*;
import java.nio.file.Files;
import java.util.*;
import org.json.*;

final class WebApi implements LocalHttp.Handler {
 private final Context context;final WebSessions sessions=new WebSessions();private final Object imageLock=new Object();
 WebApi(Context c){context=c;}
 static String mime(String path){return path.endsWith(".js")?"application/javascript":path.endsWith(".css")?"text/css":path.endsWith(".svg")?"image/svg+xml":path.endsWith(".ttf")?"font/ttf":path.endsWith(".jpg")?"image/jpeg":"text/html; charset=utf-8";}
 private LocalHttp.Response json(int status,JSONObject object){return LocalHttp.Response.text(status,"application/json; charset=utf-8",object.toString());}
 private static byte[] bytes(InputStream in)throws IOException{try(InputStream source=in;ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] b=new byte[8192];int n;while((n=source.read(b))!=-1)out.write(b,0,n);return out.toByteArray();}}
 public LocalHttp.Response handle(LocalHttp.Request r)throws Exception{
  if(r.path.equals("/api/pair")&&r.method.equals("POST")){
   String code=r.text().replaceFirst("^code=","");String token=sessions.pair(code);
   if(token==null)return LocalHttp.Response.text(403,"text/html; charset=utf-8",pairPage("配对码不正确或请求过多，请稍后重试"));
   LocalHttp.Response out=LocalHttp.Response.text(303,"text/plain","");out.headers.put("Location","/");out.headers.put("Set-Cookie","liuying="+token+"; HttpOnly; SameSite=Strict; Path=/");return out;
  }
  WebSessions.Session s=sessions.find(r.headers.get("cookie"));
  if(s==null){if(r.path.equals("/")&&r.method.equals("GET"))return LocalHttp.Response.text(200,"text/html; charset=utf-8",pairPage("输入手机 App 中显示的配对码"));return json(401,new JSONObject().put("error","请重新配对"));}
  if(r.method.equals("GET")){
   if(r.path.equals("/api/sharing")){JSONObject state=SharingService.sharingState();state.remove("code");state.put("current","http://"+r.host).put("host","android");return json(200,state);}
   if(r.path.equals("/api/state")){JSONObject state=PrintJobs.state(context,s.id);if(SharingService.sharingState().optBoolean("paused")&&"queued".equals(state.getJSONObject("job").optString("phase")))state.getJSONObject("job").put("message","共享队列已暂停，请在手机上检查");synchronized(s){JSONObject job=state.optJSONObject("job");if(job!=null&&job.has("file"))s.files.add("/private/"+job.getString("file"));JSONArray history=state.optJSONArray("history");if(history!=null)for(int i=0;i<history.length();i++)s.files.add("/private/"+history.getJSONObject(i).getString("file"));}return json(200,state);}
   if(r.path.equals("/session.js"))return LocalHttp.Response.text(200,"application/javascript","window.STUDIO_DRAFT_KEY="+JSONObject.quote("liuying-draft-"+s.id)+";");
   if(r.path.startsWith("/private/")){
    synchronized(s){if(!s.files.contains(r.path))return json(404,new JSONObject().put("error","照片不存在"));}
    return new LocalHttp.Response(200,"image/jpeg",Files.readAllBytes(new File(context.getFilesDir(),r.path.substring(9)).toPath()));
   }
   String name=r.path.equals("/")?"index.html":r.path.substring(1);if(!AssetPolicy.allows(name))return json(404,new JSONObject().put("error","页面不存在"));
   return new LocalHttp.Response(200,mime(name),bytes(context.getAssets().open(name)));
  }
  try{
   if(r.path.equals("/api/upload"))return json(200,upload(s,r.body));
   JSONObject data=new JSONObject(r.text());
   if(r.path.equals("/api/print")){
    if(!SharingService.accepting())throw new IOException("共享服务已停止");
    return json(200,PrintJobs.submit(context,s.id,data.getString("requestId"),data.getJSONArray("pages").toString()));
   }
   if(r.path.equals("/api/cancel")){PrintJobs.cancel(context,s.id);return json(200,new JSONObject().put("ok",true));}
   if(r.path.equals("/api/connect")){SharingService.checkPrinter();return json(200,new JSONObject().put("ok",true));}
   if(r.path.equals("/api/release")){PrinterStatus.release(context);return json(200,new JSONObject().put("ok",true));}
   if(r.path.equals("/api/airprint-layout")){PrinterStatus.layout(data.getBoolean("splice"));return json(200,new JSONObject().put("ok",true));}
   if(r.path.equals("/api/reconcile")){SharingService.reconcile(s.id);return json(200,new JSONObject().put("ok",true));}
   if(r.path.equals("/api/cutout")){
    String src=data.getString("source");synchronized(s){if(!s.files.contains(src))throw new IOException("照片不存在");}
    JSONObject variants;synchronized(imageLock){variants=PortraitCutout.process(context,src);}synchronized(s){for(String k:new String[]{"white","blue","red"})s.files.add(variants.getString(k));}
    return json(200,new JSONObject().put("images",variants));
   }
   return json(404,new JSONObject().put("error","接口不存在"));
  }catch(Exception|OutOfMemoryError e){return json(409,new JSONObject().put("error",e instanceof IOException?e.getMessage():"操作未完成，请检查照片或打印状态"));}
 }
 private JSONObject upload(WebSessions.Session session,byte[] data)throws Exception{
  synchronized(imageLock){synchronized(session){if(session.files.size()>=60||session.bytes+data.length>120L*1024*1024)throw new IOException("本次共享照片已达上限，请停止共享后重新开启");}
   Bitmap bitmap=ImageDecoder.decodeBitmap(ImageDecoder.createSource(ByteBuffer.wrap(data)),(decoder,info,src)->{decoder.setAllocator(ImageDecoder.ALLOCATOR_SOFTWARE);int w=info.getSize().getWidth(),h=info.getSize().getHeight();double scale=Math.min(1,2400.0/Math.max(w,h));decoder.setTargetSize(Math.max(1,(int)(w*scale)),Math.max(1,(int)(h*scale)));});
   String name="photos/"+UUID.randomUUID()+".jpg";File file=new File(context.getFilesDir(),name);file.getParentFile().mkdirs();try{try(FileOutputStream out=new FileOutputStream(file)){if(!bitmap.compress(Bitmap.CompressFormat.JPEG,97,out))throw new IOException("照片转换失败");}String src="/private/"+name;synchronized(session){session.files.add(src);session.bytes+=data.length;}return new JSONObject().put("src",src).put("width",bitmap.getWidth()).put("height",bitmap.getHeight());}finally{bitmap.recycle();}
  }
 }
 private static String pairPage(String message){return "<!doctype html><html lang='zh-CN'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>留影工坊</title><style>:root{color-scheme:light dark;font:16px system-ui}body{max-width:360px;margin:18vh auto;padding:24px}input,button{box-sizing:border-box;width:100%;padding:16px;margin:12px 0;border-radius:12px;font:inherit}button{background:#d5ba76;color:#222;border:0}p{line-height:1.7}</style><h1>留影工坊</h1><p>"+message+"</p><form method='post' action='/api/pair'><input name='code' inputmode='numeric' pattern='[0-9]{6}' maxlength='6' required autocomplete='off' placeholder='6 位配对码' aria-label='配对码'><button>连接</button></form></html>";}
}
