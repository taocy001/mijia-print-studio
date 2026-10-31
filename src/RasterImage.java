package local.liuying.studio;
import java.io.*;
import java.nio.*;
import java.util.*;
final class RasterImage {
 final int width,height;final int[] pixels;
 RasterImage(int w,int h,int[] p){width=w;height=h;pixels=p;}
 static int integer(byte[] b,int offset){return ByteBuffer.wrap(b,offset,4).getInt();}
 static RasterImage decode(byte[] data,String mime)throws IOException{
  DataInputStream in=new DataInputStream(new ByteArrayInputStream(data));boolean urf=mime.equals("image/urf");int w,h,channels;
  if(urf){byte[] header=new byte[44];in.readFully(header);if(!Arrays.equals(Arrays.copyOf(header,8),new byte[]{85,78,73,82,65,83,84,0}))throw new IOException("Invalid URF");int pages=integer(header,8);if(pages<0||pages>1)throw new IOException("Single raster page required");w=integer(header,24);h=integer(header,28);channels=header[13]==1?3:header[13]==0?1:0;if(header[12]!=channels*8||header[14]>1)throw new IOException("Unsupported raster format");}
  else{byte[] header=new byte[1800];in.readFully(header);if(integer(header,0)!=0x52615332)throw new IOException("Invalid PWG");w=integer(header,376);h=integer(header,380);int space=integer(header,404);channels=space==19?3:space==18?1:0;if(integer(header,388)!=8||integer(header,392)!=channels*8||integer(header,396)!=(long)w*channels||integer(header,400)!=0||integer(header,276)!=0)throw new IOException("Unsupported raster format");}
  if(channels==0||w<1||h<1||w>10000||h>10000||(long)w*h>16000000)throw new IOException("Raster dimensions unsupported");
  int[] pixels=new int[w*h],row=new int[w];int[] color=new int[channels];
  for(int y=0;y<h;){int repeat=in.readUnsignedByte()+1;if(y+repeat>h)throw new IOException("Invalid row repeat");int x=0;
   while(x<w){int code=in.readUnsignedByte();if(code==128){Arrays.fill(row,x,w,0xffffffff);x=w;break;}int count=code<128?code+1:257-code;if(count>w-x)throw new IOException("Invalid pixel run");
    for(int n=0;n<count;n++){if(n==0||code>128)for(int c=0;c<channels;c++)color[c]=in.readUnsignedByte();int rgb=channels==1?color[0]*0x10101:(color[0]<<16)|(color[1]<<8)|color[2];row[x++]=0xff000000|rgb;}
   }
   for(int n=0;n<repeat;n++)System.arraycopy(row,0,pixels,(y+n)*w,w);y+=repeat;
  }
  if(in.available()!=0)throw new IOException("Multiple raster pages unsupported");return new RasterImage(w,h,pixels);
 }
}
