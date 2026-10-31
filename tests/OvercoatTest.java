package local.liuying.studio;
import android.graphics.Bitmap;
import android.graphics.Color;
import java.io.ByteArrayOutputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.zip.Inflater;
public final class OvercoatTest {
 public static void main(String[] args)throws Exception{
  for(int media:new int[]{5009,5012,5014}){
  int width=media==5009?1040:1216,height=media==5009?1040:1824;
  Bitmap bitmap=Bitmap.createBitmap(width,height,Bitmap.Config.ARGB_8888);bitmap.eraseColor(Color.BLACK);bitmap.setPixel(300,400,Color.WHITE);
  ByteArrayOutputStream png=new ByteArrayOutputStream();bitmap.compress(Bitmap.CompressFormat.PNG,100,png);bitmap.recycle();
  byte[] oc=Overcoat.encode(png.toByteArray(),100,media);
  ByteBuffer header=ByteBuffer.wrap(oc).order(ByteOrder.BIG_ENDIAN);header.position(12);
  if(header.getInt()!=width||header.getInt()!=height||header.getInt()!=oc.length-32||header.getInt()!=1)throw new AssertionError("header");
  Inflater decoder=new Inflater(true);decoder.setInput(oc,32,oc.length-32);byte[] data=new byte[width*height];int count=decoder.inflate(data);
  if(!decoder.finished()||count!=data.length)throw new AssertionError("deflate");decoder.end();
  for(int i=0;i<data.length;i++)if((data[i]&255)!=(i==400*width+300?255:0))throw new AssertionError("mask pixel");
  boolean rejected=false;try{Overcoat.encode(new byte[]{1,2,3},100);}catch(Exception e){rejected=true;}
  if(!rejected)throw new AssertionError("invalid input accepted");
  }
  System.out.println("Overcoat header, raw deflate, all mask pixels and invalid input passed");
 }
}
