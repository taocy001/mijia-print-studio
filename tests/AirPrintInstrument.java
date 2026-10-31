package local.liuying.studio;
import android.app.Instrumentation;
import android.content.*;
import android.graphics.*;
import android.graphics.pdf.PdfDocument;
import android.os.Bundle;
import android.util.Base64;
import java.io.*;
import java.nio.file.Files;
import java.util.*;
import org.json.*;
public class AirPrintInstrument extends Instrumentation {
 static void check(boolean b,String why){if(!b)throw new AssertionError(why);}
 @Override public void onCreate(Bundle args){super.onCreate(args);start();}
 private Context isolated;
 private byte[] image()throws Exception{Bitmap b=Bitmap.createBitmap(300,450,Bitmap.Config.ARGB_8888);Canvas c=new Canvas(b);c.drawColor(Color.BLUE);Paint p=new Paint();p.setColor(Color.RED);c.drawRect(0,0,300,225,p);ByteArrayOutputStream out=new ByteArrayOutputStream();b.compress(Bitmap.CompressFormat.JPEG,95,out);b.recycle();return out.toByteArray();}
 private IppWire.Message request(int op,int id,byte[] document,String mime)throws Exception{IppWire.Message m=new IppWire.Message();m.code=op;m.id=id;m.document=document;m.attrs.add(IppWire.text(1,0x47,"attributes-charset","utf-8"));m.attrs.add(IppWire.text(1,0x48,"attributes-natural-language","en"));if(mime!=null)m.attrs.add(IppWire.text(1,0x49,"document-format",mime));return m;}
 private IppWire.Message call(PhoneAirPrint api,IppWire.Message m,String peer)throws Exception{LocalHttp.Request r=new LocalHttp.Request();r.method="POST";r.path="/ipp/print";r.host="127.0.0.1:8637";r.peer=peer;r.body=IppWire.encode(m);return IppWire.decode(api.handle(r).body);}
 private void device(int media)throws Exception{Store.device=new JSONObject().put("connected",true).put("media",media).put("checkedAt",System.currentTimeMillis());PrinterStatus.released=false;}
 @Override public void onStart(){Bundle result=new Bundle();JSONObject old=Store.device;boolean released=PrinterStatus.released,splice=PrinterStatus.splice;File folder=new File(getTargetContext().getCacheDir(),"ipp-test-"+UUID.randomUUID());folder.mkdirs();
  try{
   check(!Store.busy,"Busy printer");JSONObject job=Store.read(getTargetContext(),"job.json");check(!job.has("token")||Store.terminal(job),"Unfinished job");
   isolated=new ContextWrapper(getTargetContext()){@Override public File getFilesDir(){return folder;}@Override public File getCacheDir(){return folder;}};
   PhoneAirPrint api=new PhoneAirPrint(isolated);device(5009);
   IppWire.Message caps=call(api,request(11,1,new byte[0],null),"127.0.0.1");check(caps.text("media-ready","").contains("square"),"Detected square");
   IppWire.Message print=request(2,2,image(),"image/jpeg"),accepted=call(api,print,"127.0.0.1");check(accepted.code==0,"JPEG admission");check(call(api,print,"127.0.0.1").number("job-id",0)==accepted.number("job-id",-1),"Retry dedupe");check(PrintJobs.records(isolated).length()==1,"No duplicate queued");
   IppWire.Message cancel=request(8,3,new byte[0],null);cancel.attrs.add(IppWire.integer(1,0x21,"job-id",accepted.number("job-id",0)));check(call(api,cancel,"192.168.1.99").code==0x406,"Client isolation");check(call(api,cancel,"127.0.0.1").number("job-state",0)==7,"Cancel queued");
   IppWire.Message create=call(api,request(5,4,new byte[0],"image/jpeg"),"127.0.0.1"),send=request(6,5,image(),"image/jpeg");send.attrs.add(IppWire.integer(1,0x21,"job-id",create.number("job-id",0)));send.attrs.add(new IppWire.Attr(1,0x22,"last-document",new byte[]{1}));check(call(api,send,"127.0.0.1").code==0,"Create and send");check(call(api,send,"127.0.0.1").code==0&&PrintJobs.records(isolated).length()==2,"Send retry");
   IppWire.Message bad=request(2,6,image(),"image/jpeg");bad.attrs.add(IppWire.text(2,0x44,"media","na_index-4x6_4x6in"));check(call(api,bad,"127.0.0.1").code==0x40b,"Wrong paper rejected");
   PrinterStatus.released=true;check(call(api,request(2,7,image(),"image/jpeg"),"127.0.0.1").code==0x507,"Released rejects print");device(5012);PrinterStatus.splice=true;
   ByteArrayOutputStream pdfBytes=new ByteArrayOutputStream();PdfDocument pdf=new PdfDocument();try{for(int i=0;i<2;i++){PdfDocument.Page p=pdf.startPage(new PdfDocument.PageInfo.Builder(300,450,i+1).create());p.getCanvas().drawColor(i==0?Color.RED:Color.BLUE);pdf.finishPage(p);}pdf.writeTo(pdfBytes);}finally{pdf.close();}
   JSONArray pages=AirPrintPages.render(isolated,pdfBytes.toByteArray(),"application/pdf",5014,"fit",0);check(pages.length()==1,"PDF pair splice");byte[] bytes=Base64.decode(pages.getJSONObject(0).getString("base64"),Base64.DEFAULT);Bitmap bitmap=BitmapFactory.decodeByteArray(bytes,0,bytes.length);check(bitmap.getWidth()==1216&&bitmap.getHeight()==1824,"Splice size");check(Color.red(bitmap.getPixel(608,456))>240&&Color.blue(bitmap.getPixel(608,1368))>240,"Splice page order");bitmap.recycle();
   for(String ext:new String[]{"urf","pwg"}){byte[] data=Files.readAllBytes(new File("/data/local/tmp/liuying-one-page."+ext).toPath());JSONArray raster=AirPrintPages.render(isolated,data,ext.equals("urf")?"image/urf":"image/pwg-raster",5009,"fill",0);byte[] jpg=Base64.decode(raster.getJSONObject(0).getString("base64"),Base64.DEFAULT);Bitmap b=BitmapFactory.decodeByteArray(jpg,0,jpg.length);check(b.getWidth()==1040&&Color.blue(b.getPixel(520,200))>240,"Square rotation "+ext);b.recycle();}
   PrinterStatus.splice=false;device(5012);JSONArray webPages=AirPrintPages.render(isolated,image(),"image/jpeg",5012,"fill",0);PrintJobs.submit(isolated,"browser-test","browser-request-0001",webPages.toString());
   PrintJobs.cancelWaiting(isolated,false);JSONArray queue=PrintJobs.records(isolated);check(queue.getJSONObject(queue.length()-1).getString("phase").equals("cancelled"),"Web stop cancels Web queue");check(queue.getJSONObject(1).getString("phase").equals("queued"),"Web stop preserves AirPrint queue");PrintJobs.cancelWaiting(isolated,true);check(PrintJobs.records(isolated).getJSONObject(1).getString("phase").equals("cancelled"),"AirPrint stop cancels own queue");
   Store.device.put("checkedAt",System.currentTimeMillis()-151000);check(PrinterStatus.media()==0,"Expired paper unavailable");
   check(!Store.read(isolated,"job.json").has("token"),"No physical printing promoted");
   result.putString("stream","PASS: Android IPP square detection, JPEG, PDF splice, URF/PWG, rotation, create/send, duplicate requests, isolation, cancellation, release and paper rejection; no Bluetooth calls");finish(-1,result);
  }catch(Throwable e){result.putString("stream",android.util.Log.getStackTraceString(e));finish(0,result);}
  finally{Store.device=old;PrinterStatus.released=released;PrinterStatus.splice=splice;delete(folder);}
 }
 private static void delete(File f){File[] files=f.listFiles();if(files!=null)for(File p:files)delete(p);f.delete();}
}
