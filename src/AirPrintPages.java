package local.liuying.studio;
import android.content.Context;
import android.graphics.*;
import android.graphics.pdf.PdfRenderer;
import android.os.ParcelFileDescriptor;
import android.util.Base64;
import java.io.*;
import java.nio.ByteBuffer;
import java.util.*;
import org.json.*;
final class AirPrintPages {
 static final String[] FORMATS={"image/jpeg","application/pdf","image/urf","image/pwg-raster"};
 static JSONArray render(Context context,byte[] data,String mime,int media,String scaling,int orientation)throws Exception{
  if(data.length==0||data.length>32*1024*1024)throw new IOException("Invalid document size");
  List<Bitmap> images=new ArrayList<>();JSONArray result=new JSONArray();
  try{
   if(mime.equals("application/pdf")){
    File file=File.createTempFile("ipp-",".pdf",context.getCacheDir());try{
     try(FileOutputStream out=new FileOutputStream(file)){out.write(data);}
     try(ParcelFileDescriptor fd=ParcelFileDescriptor.open(file,ParcelFileDescriptor.MODE_READ_ONLY);PdfRenderer pdf=new PdfRenderer(fd)){
      if(pdf.getPageCount()<1||pdf.getPageCount()>6)throw new IOException("At most six PDF pages");
      for(int i=0;i<pdf.getPageCount();i++)try(PdfRenderer.Page page=pdf.openPage(i)){
       double factor=Math.min(2400.0/page.getWidth(),2400.0/page.getHeight());Bitmap b=Bitmap.createBitmap(Math.max(1,(int)(page.getWidth()*factor)),Math.max(1,(int)(page.getHeight()*factor)),Bitmap.Config.ARGB_8888);images.add(b);b.eraseColor(Color.WHITE);page.render(b,null,null,PdfRenderer.Page.RENDER_MODE_FOR_PRINT);
      }
     }
    }finally{file.delete();}
   }else if(mime.equals("image/jpeg")){
    if(data.length<2||data[0]!=(byte)255||data[1]!=(byte)216)throw new IOException("JPEG required");
    Bitmap b=ImageDecoder.decodeBitmap(ImageDecoder.createSource(ByteBuffer.wrap(data)),(decoder,info,source)->{decoder.setAllocator(ImageDecoder.ALLOCATOR_SOFTWARE);int w=info.getSize().getWidth(),h=info.getSize().getHeight();double scale=Math.min(1,2400.0/Math.max(w,h));decoder.setTargetSize(Math.max(1,(int)(w*scale)),Math.max(1,(int)(h*scale)));decoder.setTargetColorSpace(ColorSpace.get(ColorSpace.Named.SRGB));});images.add(b);
   }else if(mime.equals("image/urf")||mime.equals("image/pwg-raster")){
    if(media==5014)throw new IOException("Splice supports JPEG and PDF only");RasterImage r=RasterImage.decode(data,mime);images.add(Bitmap.createBitmap(r.pixels,r.width,r.height,Bitmap.Config.ARGB_8888));
   }else throw new IOException("Unsupported document format");
   for(int i=0;i<images.size();i+=media==5014?2:1){
    int w=media==5009?1040:1216,h=media==5009?1040:1824;Bitmap out=Bitmap.createBitmap(w,h,Bitmap.Config.ARGB_8888);out.eraseColor(Color.WHITE);
    try{Canvas canvas=new Canvas(out);if(media==5009)canvas.rotate(180,w/2f,h/2f);
     if(media==5014){draw(canvas,images.get(i),0,0,w,h/2f,scaling);draw(canvas,images.get(Math.min(i+1,images.size()-1)),0,h/2f,w,h/2f,scaling);}
     else{Bitmap image=images.get(i);boolean landscape=orientation==4||orientation==5||orientation==0&&media!=5009&&image.getWidth()>image.getHeight();if(orientation==5||orientation==6)canvas.rotate(180,w/2f,h/2f);if(landscape){canvas.translate(0,h);canvas.rotate(-90);draw(canvas,image,0,0,h,w,scaling);}else draw(canvas,image,0,0,w,h,scaling);}
     byte[] encoded=null;for(int quality=97;quality>=60;quality-=3){ByteArrayOutputStream buffer=new ByteArrayOutputStream();out.compress(Bitmap.CompressFormat.JPEG,quality,buffer);encoded=buffer.toByteArray();if(encoded.length<=524288)break;}if(encoded.length>524288)throw new IOException("Image exceeds output limit");
     result.put(new JSONObject().put("media",media).put("copies",1).put("sharpen",0).put("title","AirPrint").put("base64",Base64.encodeToString(encoded,Base64.NO_WRAP)));
    }finally{out.recycle();}
   }return result;
  }finally{for(Bitmap b:images)b.recycle();}
 }
 private static void draw(Canvas c,Bitmap b,float x,float y,float w,float h,String fit){float scale=fit.equals("fit")?Math.min(w/b.getWidth(),h/b.getHeight()):Math.max(w/b.getWidth(),h/b.getHeight());float bw=b.getWidth()*scale,bh=b.getHeight()*scale;c.save();c.clipRect(x,y,x+w,y+h);c.drawBitmap(b,null,new RectF(x+(w-bw)/2,y+(h-bh)/2,x+(w+bw)/2,y+(h+bh)/2),new Paint(Paint.ANTI_ALIAS_FLAG|Paint.FILTER_BITMAP_FLAG));c.restore();}
}
