package local.liuying.studio;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.util.zip.Deflater;

/** The same ocpattern1 mask format as the Web USB backend. */
final class Overcoat {
    static byte[] encode(byte[] png,int threshold)throws IOException{return encode(png,threshold,5012);}
    static byte[] encode(byte[] png,int threshold,int media)throws IOException{
        if(media!=5009&&media!=5012&&media!=5014)throw new IOException("相纸类型不支持");
        int width=media==5009?1040:1216,height=media==5009?1040:1824;
        if(png.length>1048576||threshold<60||threshold>140)throw new IOException("覆膜数据无效");
        BitmapFactory.Options bounds=new BitmapFactory.Options();bounds.inJustDecodeBounds=true;
        BitmapFactory.decodeByteArray(png,0,png.length,bounds);
        if(bounds.outWidth!=width||bounds.outHeight!=height)throw new IOException("覆膜尺寸不正确");
        Bitmap mask=BitmapFactory.decodeByteArray(png,0,png.length);
        if(mask==null)throw new IOException("无法读取覆膜图层");
        byte[] raw=new byte[width*height];int[] row=new int[width];
        try{for(int y=0;y<height;y++){
            mask.getPixels(row,0,width,0,y,width,1);
            for(int x=0;x<width;x++)raw[y*width+x]=(byte)(((row[x]>>>16)&255)>=100?255:0);
        }}finally{mask.recycle();}
        Deflater deflater=new Deflater(6,true);ByteArrayOutputStream compressed=new ByteArrayOutputStream();
        try{deflater.setInput(raw);deflater.finish();byte[] chunk=new byte[8192];
            while(!deflater.finished()){int n=deflater.deflate(chunk);compressed.write(chunk,0,n);}
        }finally{deflater.end();}
        byte[] data=compressed.toByteArray();ByteBuffer out=ByteBuffer.allocate(32+data.length).order(ByteOrder.BIG_ENDIAN);
        out.put("ocpattern1\0\0".getBytes(StandardCharsets.US_ASCII)).putInt(width).putInt(height).putInt(data.length).putInt(1);
        out.put((byte)(threshold+60)).put((byte)(threshold-20)).putShort((short)0).put(data);return out.array();
    }
}
