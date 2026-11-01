package local.liuying.studio;
import android.content.Context;
import android.graphics.*;
import android.util.AtomicFile;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.UUID;
import org.json.*;

final class CameraCapture {
 static final Object LOCK=new Object();
 private static AtomicFile journal(Context c){return new AtomicFile(new File(c.getFilesDir(),"capture.json"));}
 static JSONObject read(Context c)throws Exception{synchronized(LOCK){File file=new File(c.getFilesDir(),"capture.json");if(!file.exists()&&!new File(file+".bak").exists())return new JSONObject();byte[] bytes=journal(c).readFully();if(bytes.length>65536)throw new IOException("拍摄记录无效");return new JSONObject(new String(bytes,StandardCharsets.UTF_8));}}
 private static void write(Context c,JSONObject value)throws Exception{AtomicFile atomic=journal(c);FileOutputStream out=null;try{out=atomic.startWrite();out.write(value.toString().getBytes(StandardCharsets.UTF_8));atomic.finishWrite(out);}catch(Exception error){if(out!=null)atomic.failWrite(out);throw error;}}
 static void recover(Context c,boolean restored)throws Exception{synchronized(LOCK){if(!restored&&"waiting".equals(read(c).optString("stage")))receive(c,false,null);}}
 static JSONObject begin(Context c,int remaining)throws Exception{synchronized(LOCK){
  if(remaining<1||remaining>6)throw new IOException("最多保留 6 张照片，请先腾出位置");if(read(c).has("id"))throw new IOException("请先完成当前拍摄或接收拍摄结果");
  String id=UUID.randomUUID().toString();File file=CaptureProvider.output(c,id);if(!file.getParentFile().isDirectory()&&!file.getParentFile().mkdirs())throw new IOException("无法准备拍摄文件");if(!file.createNewFile())throw new IOException("无法准备拍摄文件");
  JSONObject pending=new JSONObject().put("id",id).put("stage","waiting");try{write(c,pending);}catch(Exception error){file.delete();throw error;}return pending;
 }}
 static void receive(Context c,boolean success,String error)throws Exception{synchronized(LOCK){JSONObject pending=read(c);if(!"waiting".equals(pending.optString("stage")))return;pending.put("stage","received").put("success",success);if(error!=null)pending.put("error",error);write(c,pending);}}
 static JSONObject finish(Context c)throws Exception{synchronized(LOCK){JSONObject pending=read(c);if(!"received".equals(pending.optString("stage")))return pending;
  String id=pending.getString("id");File source=CaptureProvider.output(c,id);JSONArray photos=new JSONArray();JSONObject finished=new JSONObject().put("id",id);File output=null;boolean imported=false;
  try{
   if(pending.has("error"))finished.put("error",pending.getString("error"));
   else if(!pending.optBoolean("success"))finished.put("cancelled",true);
   else{
    if(!source.isFile()||source.length()<4||source.length()>64L*1024*1024)throw new IOException("拍摄照片缺失或过大，请重试");
    Bitmap bitmap=ImageDecoder.decodeBitmap(ImageDecoder.createSource(source),(decoder,info,image)->{
     int w=info.getSize().getWidth(),h=info.getSize().getHeight();if(w<1||h<1||w>20000||h>20000||(long)w*h>100000000)throw new IllegalArgumentException("照片尺寸过大");decoder.setAllocator(ImageDecoder.ALLOCATOR_SOFTWARE);decoder.setOnPartialImageListener(error->false);double scale=Math.min(1,2400.0/Math.max(w,h));decoder.setTargetSize(Math.max(1,(int)(w*scale)),Math.max(1,(int)(h*scale)));
    });
    try{File root=new File(c.getFilesDir(),"photos");if(!root.isDirectory()&&!root.mkdirs())throw new IOException("无法保存拍摄照片");output=new File(root,id+".jpg");if(Files.isSymbolicLink(root.toPath())||Files.isSymbolicLink(output.toPath())||!root.getCanonicalFile().equals(output.getCanonicalFile().getParentFile()))throw new IOException("照片保存位置无效");
     AtomicFile atomic=new AtomicFile(output);FileOutputStream stream=null;try{stream=atomic.startWrite();if(!bitmap.compress(Bitmap.CompressFormat.JPEG,97,stream))throw new IOException("照片保存失败");atomic.finishWrite(stream);}catch(Exception error){if(stream!=null)atomic.failWrite(stream);throw error;}
     photos.put(new JSONObject().put("src","/private/photos/"+id+".jpg").put("captureId",id).put("width",bitmap.getWidth()).put("height",bitmap.getHeight()).put("faces",FaceDetector.json(FaceDetector.detect(c,bitmap))));imported=true;
    }finally{bitmap.recycle();}
   }
  }catch(Exception|OutOfMemoryError error){finished.put("error","拍摄照片未能读取，请重新拍摄");if(output!=null&&!imported)new AtomicFile(output).delete();}
  pending=new JSONObject().put("id",id).put("stage","ready").put("photos",photos).put("finished",finished);write(c,pending);Files.deleteIfExists(source.toPath());return pending;
 }}
 static void acknowledge(Context c,String id)throws Exception{synchronized(LOCK){JSONObject pending=read(c);if("ready".equals(pending.optString("stage"))&&pending.optString("id").equals(id)){Files.deleteIfExists(CaptureProvider.output(c,id).toPath());journal(c).delete();}}}
}
