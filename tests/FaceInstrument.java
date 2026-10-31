package local.liuying.studio;
import android.app.Instrumentation;
import android.graphics.*;
import android.os.Bundle;
import java.util.*;
public class FaceInstrument extends Instrumentation {
 private String photo;
 @Override public void onCreate(Bundle args){super.onCreate(args);photo=args.getString("photo");start();}
 static void check(boolean value,String why){if(!value)throw new AssertionError(why);}
 @Override public void onStart(){Bundle result=new Bundle();Bitmap source=null,out=null,face=null;try{
  source=Bitmap.createBitmap(2000,1000,Bitmap.Config.ARGB_8888);source.eraseColor(Color.BLUE);Paint paint=new Paint();paint.setColor(Color.RED);new Canvas(source).drawRect(60,0,340,1000,paint);
  long start=System.nanoTime();check(FaceDetector.detectStrict(getTargetContext(),source).isEmpty(),"False detection on solid color");long ms=(System.nanoTime()-start)/1000000;
  out=Bitmap.createBitmap(1040,1040,Bitmap.Config.ARGB_8888);out.eraseColor(Color.WHITE);AirPrintPages.draw(new Canvas(out),source,0,0,1040,1040,"fill",Arrays.asList(new float[]{.05f,.3f,.15f,.5f}));check(Color.red(out.getPixel(100,520))>240,"Off-center face content lost");check(Color.blue(out.getPixel(900,520))>240,"Fill image missing");
  out.eraseColor(Color.WHITE);AirPrintPages.draw(new Canvas(out),source,0,0,1040,1040,"fill",Arrays.asList(new float[]{.05f,.3f,.15f,.5f},new float[]{.85f,.3f,.95f,.5f}));check(out.getPixel(520,20)==Color.WHITE,"Group must fit with margin");check(Color.red(out.getPixel(70,520))>240,"Group cropped left face");
  out.eraseColor(Color.WHITE);AirPrintPages.draw(new Canvas(out),source,0,0,1040,1040,"fill",Collections.emptyList());check(Color.blue(out.getPixel(100,520))>240,"No-face fallback changed");
  int count=0;if(photo!=null){face=BitmapFactory.decodeFile(photo);check(face!=null,"Face fixture unavailable");start=System.nanoTime();List<float[]> boxes=FaceDetector.detectStrict(getTargetContext(),face);long warm=(System.nanoTime()-start)/1000000;count=boxes.size();check(count==1,"Expected one known face");float[] box=boxes.get(0);check(box[0]>.30&&box[0]<.40&&box[1]>.09&&box[1]<.16&&box[2]>.49&&box[2]<.56&&box[3]>.30&&box[3]<.38,"Known face bounds differ");result.putLong("face_ms",warm);result.putString("boxes",FaceDetector.json(boxes).toString());}
  result.putString("stream","PASS: ONNX inference "+ms+" ms, face fixture count="+count+", off-center face preservation, group fit, no-face fallback; no Bluetooth calls");finish(-1,result);
 }catch(Throwable e){result.putString("stream",android.util.Log.getStackTraceString(e));finish(0,result);}finally{if(source!=null)source.recycle();if(out!=null)out.recycle();if(face!=null)face.recycle();}}
}
