package local.liuying.studio;
import java.io.*;
import java.nio.*;
import java.nio.file.*;
import java.util.*;
public final class UploadStreamTest {
 static void check(boolean value,String message){if(!value)throw new AssertionError(message);}
 static byte[] receive(byte[] data)throws Exception{
  byte[] key="0123456789ABCDEF".getBytes("US-ASCII");int total=(data.length+987)/988;ByteArrayOutputStream out=new ByteArrayOutputStream();
  for(int i=0;i<total;i++){
   Wire.Frame frame=new Wire.Frame(Wire.uploadFrame(key,145,data,i,7+i));check(frame.total==total&&frame.number==i+1,"Single continuous frame numbering");
   byte[] plain=Wire.crypt(key,frame.body,false);check(ByteBuffer.wrap(plain).order(ByteOrder.LITTLE_ENDIAN).getInt()==145,"Job id retained");
   int end=plain.length;if(i==total-1)while(end>4&&plain[end-1]==0)end--;else check(end==992,"Full packets have no AES padding");
   out.write(plain,4,end-4);
  }return out.toByteArray();
 }
 public static void main(String[] args)throws Exception{
  for(int media:new int[]{5009,5012})for(int length:new int[]{32,988,989,1976,2893})for(int tail:new int[]{1,4,16}){
   byte[] coat=new byte[length];new Random(length+tail).nextBytes(coat);Arrays.fill(coat,Math.max(32,length-tail),length,(byte)0);
   ByteBuffer.wrap(coat).order(ByteOrder.BIG_ENDIAN).position(12).putInt(media==5009?1040:1216).putInt(media==5009?1040:1824).putInt(length-32);
   if(length>200)Arrays.fill(coat,64,200,(byte)0);
   byte[] jpeg=new byte[364649];new Random(9).nextBytes(jpeg);jpeg[0]=(byte)255;jpeg[1]=(byte)216;jpeg[jpeg.length-2]=(byte)255;jpeg[jpeg.length-1]=(byte)217;
   byte[] joined=Wire.jobData(coat,jpeg);check(joined.length==coat.length+jpeg.length,"Declared file size is sum");check(Arrays.equals(receive(joined),joined),"OC zeros retained at boundaries and inside");
   check(Wire.jobData(null,jpeg)==jpeg&&Arrays.equals(receive(jpeg),jpeg),"JPEG-only unchanged");
  }
  if(args.length==2){byte[] coat=Files.readAllBytes(Paths.get(args[0])),jpeg=Files.readAllBytes(Paths.get(args[1]));byte[] joined=Wire.jobData(coat,jpeg);check(Arrays.equals(joined,receive(joined)),"Failed job exact bytes preserved by merged upload");check(receive(coat).length<coat.length,"Old separate OC stream reproduces trailing-zero loss");}
  System.out.println("PASS: continuous OC/JPEG frames, square/six-inch headers, zero suffix and boundary cases; no device calls");
 }
}
