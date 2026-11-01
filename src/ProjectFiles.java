package local.liuying.studio;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.ImageDecoder;
import android.net.Uri;
import android.util.Base64;
import java.io.*;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.util.UUID;
import org.json.JSONObject;

final class ProjectFiles {
    static final int MAX_PROJECT=32*1024*1024,MAX_IMAGE=8*1024*1024;
    static byte[] projectBytes(String json)throws IOException{
        if(json==null||json.isEmpty()||json.length()>MAX_PROJECT)throw new IOException("作品包不能超过 32 MB");
        byte[] bytes=json.getBytes(StandardCharsets.UTF_8);
        if(bytes.length>MAX_PROJECT)throw new IOException("作品包不能超过 32 MB");
        return bytes;
    }
    static void write(Context context,Uri uri,byte[] bytes)throws IOException{
        if(uri==null||!"content".equals(uri.getScheme())||bytes.length>MAX_PROJECT)throw new IOException("保存位置无效");
        try(OutputStream output=context.getContentResolver().openOutputStream(uri,"wt")){
            if(output==null)throw new IOException("无法打开保存位置");
            output.write(bytes);output.flush();
        }
    }
    private static final class ImageData {
        final byte[] bytes;final int width,height;
        ImageData(byte[] bytes,int width,int height){this.bytes=bytes;this.width=width;this.height=height;}
    }
    static byte[] imageBytes(String encoded)throws Exception{return validatedImage(encoded).bytes;}
    private static ImageData validatedImage(String encoded)throws Exception{
        if(encoded==null||encoded.length()>((MAX_IMAGE+2)/3)*4)throw new IOException("作品照片不能超过 8 MB");
        byte[] jpeg=Base64.decode(encoded,Base64.NO_WRAP);
        if(jpeg.length<4||jpeg.length>MAX_IMAGE||(jpeg[0]&255)!=255||(jpeg[1]&255)!=216
                ||(jpeg[jpeg.length-2]&255)!=255||(jpeg[jpeg.length-1]&255)!=217)throw new IOException("作品照片必须是完整 JPEG");
        Bitmap bitmap=ImageDecoder.decodeBitmap(ImageDecoder.createSource(ByteBuffer.wrap(jpeg)),(decoder,info,source)->{
            int width=info.getSize().getWidth(),height=info.getSize().getHeight();
            if(!"image/jpeg".equals(info.getMimeType())||!sizeAllowed(width,height))throw new IllegalArgumentException("作品照片尺寸无效");
            decoder.setAllocator(ImageDecoder.ALLOCATOR_SOFTWARE);
            decoder.setOnPartialImageListener(error->false);
        });
        int width=bitmap.getWidth(),height=bitmap.getHeight();bitmap.recycle();
        if(!sizeAllowed(width,height))throw new IOException("作品照片尺寸无效");
        return new ImageData(jpeg,width,height);
    }
    static JSONObject importImage(Context context,String encoded)throws Exception{
        ImageData image=validatedImage(encoded);byte[] jpeg=image.bytes;int width=image.width,height=image.height;
        File directory=new File(context.getFilesDir(),"photos");
        if(!directory.isDirectory()&&!directory.mkdirs())throw new IOException("无法保存作品照片");
        String name=UUID.randomUUID()+".jpg";File file=new File(directory,name);boolean saved=false;
        try{
            try(FileOutputStream output=new FileOutputStream(file)){output.write(jpeg);output.getFD().sync();}
            JSONObject result=new JSONObject().put("src","/private/photos/"+name).put("width",width).put("height",height);
            saved=true;return result;
        }finally{if(!saved)file.delete();}
    }
    static boolean sizeAllowed(int width,int height){return width>0&&height>0&&width<=8192&&height<=8192&&(long)width*height<=24000000;}
}
