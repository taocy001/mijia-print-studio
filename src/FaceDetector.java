package local.liuying.studio;
import android.content.Context;
import android.graphics.Bitmap;
import android.util.Log;
import ai.onnxruntime.*;
import java.io.*;
import java.nio.FloatBuffer;
import java.util.*;
import org.json.*;
final class FaceDetector {
 private static OrtSession session;
 private static synchronized OrtSession session(Context context)throws Exception{
  if(session==null){
   byte[] model;try(InputStream in=context.getAssets().open("models/face_detection_yunet_2023mar.onnx");ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] chunk=new byte[8192];int count;while((count=in.read(chunk))!=-1)out.write(chunk,0,count);model=out.toByteArray();}
   try(OrtSession.SessionOptions options=new OrtSession.SessionOptions()){options.setIntraOpNumThreads(2);options.setInterOpNumThreads(1);OrtEnvironment env=OrtEnvironment.getEnvironment();env.setTelemetry(false);session=env.createSession(model,options);}
  }return session;
 }
 static List<float[]> detect(Context context,Bitmap image){
  try{return detectStrict(context,image);}catch(Exception|OutOfMemoryError error){Log.w("LiuyingFace","Face detection unavailable; using centered crop");return Collections.emptyList();}
 }
 static synchronized List<float[]> detectStrict(Context context,Bitmap image)throws Exception{
  Bitmap small=null;
  try{
   double scale=640.0/Math.max(image.getWidth(),image.getHeight());int width=Math.max(1,(int)Math.round(image.getWidth()*scale)),height=Math.max(1,(int)Math.round(image.getHeight()*scale));
   small=Bitmap.createScaledBitmap(image,width,height,true);int[] pixels=new int[width*height];small.getPixels(pixels,0,width,0,0,width,height);
   OrtSession model=session(context);OrtEnvironment env=OrtEnvironment.getEnvironment();
   try(OnnxTensor tensor=OnnxTensor.createTensor(env,FloatBuffer.wrap(FaceCropMath.input(pixels,width,height)),new long[]{1,3,640,640});OrtSession.RunOptions options=new OrtSession.RunOptions()){
    Timer timer=new Timer("liuying-face-timeout",true);boolean[] finished={false};timer.schedule(new TimerTask(){public void run(){synchronized(options){if(!finished[0])try{options.setTerminate(true);}catch(OrtException ignored){}}}},2000);
    try(OrtSession.Result output=model.run(Collections.singletonMap(model.getInputNames().iterator().next(),tensor),options)){
     Map<String,float[]> values=new HashMap<>();for(int stride:new int[]{8,16,32})for(String prefix:new String[]{"cls_","obj_","bbox_"}){String name=prefix+stride;OnnxTensor data=(OnnxTensor)output.get(name).orElseThrow(()->new IllegalStateException("Missing face output"));FloatBuffer buffer=data.getFloatBuffer();float[] result=new float[buffer.remaining()];buffer.get(result);values.put(name,result);}return FaceCropMath.decode(values,image.getWidth(),image.getHeight(),width,height);
    }finally{synchronized(options){finished[0]=true;timer.cancel();}}
   }
  }finally{if(small!=null&&small!=image)small.recycle();}
 }
 static JSONArray json(List<float[]> faces)throws JSONException{JSONArray result=new JSONArray();for(float[] face:faces){JSONArray box=new JSONArray();for(int i=0;i<4;i++)box.put(face[i]);result.put(box);}return result;}
}
