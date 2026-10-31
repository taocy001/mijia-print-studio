package local.liuying.studio;
import android.content.Context;
import android.graphics.*;
import ai.onnxruntime.*;
import java.io.*;
import java.nio.FloatBuffer;
import java.nio.file.Files;
import java.security.MessageDigest;
import java.util.*;
import org.json.JSONObject;
/** Offline U2NetP segmentation. Original imported photos are never overwritten. */
final class PortraitCutout {
 static synchronized JSONObject process(Context context,String source)throws Exception{
  if(source==null||!source.matches("/private/(photos|prints)/[A-Za-z0-9-]+\\.jpg"))throw new IOException("请选择已导入的照片");
  File file=new File(context.getFilesDir(),source.substring(9));
  if(!file.getCanonicalPath().startsWith(context.getFilesDir().getCanonicalPath()+"/")||!file.isFile())throw new IOException("原照片不存在，请重新导入");
  byte[] digest=MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(file.toPath()));StringBuilder key=new StringBuilder("u2netp-v1-");for(byte b:digest)key.append(String.format(Locale.ROOT,"%02x",b&255));
  String[] colors={"white","blue","red"};int[] backgrounds={0xffffffff,0xff438edb,0xffff0000};
  File directory=new File(context.getFilesDir(),"cutouts");if(!directory.isDirectory()&&!directory.mkdirs())throw new IOException("无法保存抠图结果");
  JSONObject images=new JSONObject();boolean cached=true;for(String color:colors){String name=key+"-"+color+".jpg";cached&=new File(directory,name).isFile();images.put(color,"/private/cutouts/"+name);}
  if(cached)return images;
  BitmapFactory.Options bounds=new BitmapFactory.Options();bounds.inJustDecodeBounds=true;BitmapFactory.decodeFile(file.getPath(),bounds);
  if(bounds.outWidth<1||bounds.outHeight<1||bounds.outWidth>2400||bounds.outHeight>2400)throw new IOException("照片尺寸无效，请重新导入");
  Bitmap original=BitmapFactory.decodeFile(file.getPath());if(original==null)throw new IOException("无法读取照片");
  Bitmap small=null,mask=null,fullMask=null,output=null;
  try{
   small=Bitmap.createScaledBitmap(original,320,320,true);int[] pixels=new int[320*320];small.getPixels(pixels,0,320,0,0,320,320);
   OrtEnvironment env=OrtEnvironment.getEnvironment();byte[] model;try(InputStream in=context.getAssets().open("models/u2netp.onnx")){ByteArrayOutputStream bytes=new ByteArrayOutputStream();byte[] chunk=new byte[8192];int count;while((count=in.read(chunk))!=-1)bytes.write(chunk,0,count);model=bytes.toByteArray();}
   int[] alpha;
   try(OrtSession.SessionOptions options=new OrtSession.SessionOptions()){
    options.setIntraOpNumThreads(2);options.setInterOpNumThreads(1);
    try(OrtSession session=env.createSession(model,options);OnnxTensor input=OnnxTensor.createTensor(env,FloatBuffer.wrap(CutoutMath.input(pixels)),new long[]{1,3,320,320});OrtSession.Result result=session.run(Collections.singletonMap(session.getInputNames().iterator().next(),input),Collections.singleton("1959"))){
     float[] prediction=new float[320*320];((OnnxTensor)result.get(0)).getFloatBuffer().get(prediction);alpha=CutoutMath.mask(prediction);
    }
   }
   mask=Bitmap.createBitmap(alpha,320,320,Bitmap.Config.ARGB_8888);fullMask=Bitmap.createScaledBitmap(mask,original.getWidth(),original.getHeight(),true);
   int w=original.getWidth(),h=original.getHeight();output=Bitmap.createBitmap(w,h,Bitmap.Config.ARGB_8888);int[] row=new int[w],m=new int[w];
   for(int c=0;c<colors.length;c++){
    for(int y=0;y<h;y++){original.getPixels(row,0,w,0,y,w,1);fullMask.getPixels(m,0,w,0,y,w,1);for(int x=0;x<w;x++)row[x]=CutoutMath.blend(row[x],m[x],backgrounds[c]);output.setPixels(row,0,w,0,y,w,1);}
    File target=new File(directory,key+"-"+colors[c]+".jpg"),temp=File.createTempFile("cutout-",".tmp",directory);
    try{try(FileOutputStream out=new FileOutputStream(temp)){if(!output.compress(Bitmap.CompressFormat.JPEG,97,out))throw new IOException("保存失败");}if(!temp.renameTo(target))throw new IOException("保存失败");}finally{temp.delete();}
   }
   return images;
  }finally{if(small!=null&&small!=original)small.recycle();if(fullMask!=null&&fullMask!=mask)fullMask.recycle();if(mask!=null)mask.recycle();if(output!=null)output.recycle();original.recycle();}
 }
}
