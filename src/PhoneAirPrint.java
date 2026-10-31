package local.liuying.studio;
import android.content.Context;
import android.util.Base64;
import java.io.*;
import java.util.*;
import org.json.*;
final class PhoneAirPrint implements LocalHttp.Handler {
 private volatile boolean closed;
 void close(){closed=true;}
 private final Context context;private final JSONArray rows;private final long started=System.currentTimeMillis();
 PhoneAirPrint(Context c)throws Exception{context=c;JSONArray saved=Store.read(c,"ipp-jobs.json").optJSONArray("items");rows=saved==null?new JSONArray():saved;for(int i=0;i<rows.length();i++){JSONObject r=rows.getJSONObject(i);if(r.optString("phase").equals("receiving")||r.optString("phase").equals("rendering"))r.put("phase","aborted");}save();}
 private void save()throws Exception{Store.write(context,"ipp-jobs.json",new JSONObject().put("items",rows));}
 static int media(){int tray=PrinterStatus.media();return tray==5012&&PrinterStatus.splice?5014:tray;}
 private static String mediaName(int m){return m==5009?"custom_square_3x3in":"na_index-4x6_4x6in";}
 private boolean accepting(){JSONObject job=Store.read(context,"job.json");return !closed&&!PrinterStatus.released&&media()!=0&&(!job.has("token")||Store.terminal(job)||Store.busy)&&!SharingService.sharingState().optBoolean("paused");}
 private static void text(IppWire.Message m,int tag,String name,String value){m.attrs.add(IppWire.text(4,tag,name,value));}
 private static void num(IppWire.Message m,int tag,String name,int value){m.attrs.add(IppWire.integer(4,tag,name,value));}
 private static void bool(IppWire.Message m,String name,boolean value){m.attrs.add(new IppWire.Attr(4,0x22,name,new byte[]{(byte)(value?1:0)}));}
 private static void collection(IppWire.Message m,String name,int media){
  m.attrs.add(new IppWire.Attr(4,0x34,name,new byte[0]));m.attrs.add(IppWire.text(4,0x4a,"","media-size"));m.attrs.add(new IppWire.Attr(4,0x34,"",new byte[0]));
  m.attrs.add(IppWire.text(4,0x4a,"","x-dimension"));m.attrs.add(IppWire.integer(4,0x21,"",media==5009?7620:10160));m.attrs.add(IppWire.text(4,0x4a,"","y-dimension"));m.attrs.add(IppWire.integer(4,0x21,"",media==5009?7620:15240));m.attrs.add(new IppWire.Attr(4,0x37,"",new byte[0]));
  for(String edge:new String[]{"left","right","top","bottom"}){m.attrs.add(IppWire.text(4,0x4a,"","media-"+edge+"-margin"));m.attrs.add(IppWire.integer(4,0x21,"",0));}m.attrs.add(IppWire.text(4,0x4a,"","media-type"));m.attrs.add(IppWire.text(4,0x44,"","photographic"));m.attrs.add(new IppWire.Attr(4,0x37,"",new byte[0]));
 }
 private void capabilities(IppWire.Message m,String uri){
  int paper=media();boolean ready=accepting();
  text(m,0x42,"printer-name","留影工坊 · 手机");text(m,0x41,"printer-info","留影工坊 · 手机蓝牙打印");text(m,0x41,"printer-make-and-model","Liuying Photo Printer");text(m,0x45,"printer-uri-supported",uri);text(m,0x45,"printer-uuid",SharingService.printerUuid(context));
  text(m,0x44,"uri-security-supported","none");text(m,0x44,"uri-authentication-supported","none");bool(m,"printer-is-accepting-jobs",ready);num(m,0x23,"printer-state",ready?(Store.busy?4:3):5);text(m,0x44,"printer-state-reasons",ready?"none":"paused");text(m,0x41,"printer-state-message",ready?"Ready":"Connect printer on phone");num(m,0x21,"printer-up-time",(int)((System.currentTimeMillis()-started)/1000));num(m,0x21,"queued-job-count",PrintJobs.records(context).length());
  text(m,0x47,"charset-configured","utf-8");text(m,0x47,"charset-supported","utf-8");text(m,0x48,"natural-language-configured","en");text(m,0x48,"generated-natural-language-supported","en");
  for(String v:new String[]{"1.1","2.0"})text(m,0x44,"ipp-versions-supported",v);
  for(int op:new int[]{2,4,5,6,8,9,10,11})num(m,0x23,"operations-supported",op);
  for(String f:AirPrintPages.FORMATS)if(paper!=5014||f.equals("image/jpeg")||f.equals("application/pdf"))text(m,0x49,"document-format-supported",f);
  text(m,0x49,"document-format-default","image/jpeg");text(m,0x44,"compression-supported","none");bool(m,"color-supported",true);bool(m,"multiple-document-jobs-supported",false);bool(m,"job-ids-supported",true);
  for(String k:new String[]{"sides-default","sides-supported"})text(m,0x44,k,"one-sided");
  for(String k:new String[]{"print-color-mode-default","print-color-mode-supported"})text(m,0x44,k,"color");
  num(m,0x21,"copies-default",1);m.attrs.add(new IppWire.Attr(4,0x33,"copies-supported",new byte[]{0,0,0,1,0,0,0,1}));num(m,0x23,"orientation-requested-default",3);for(int v=3;v<=6;v++)num(m,0x23,"orientation-requested-supported",v);
  text(m,0x44,"print-scaling-default","fill");text(m,0x44,"print-scaling-supported","fill");text(m,0x44,"print-scaling-supported","fit");num(m,0x23,"print-quality-default",5);num(m,0x23,"print-quality-supported",5);
  for(String k:new String[]{"printer-resolution-default","printer-resolution-supported","pwg-raster-document-resolution-supported"})m.attrs.add(new IppWire.Attr(4,0x32,k,new byte[]{0,0,1,44,0,0,1,44,3}));
  for(String v:new String[]{"srgb_8","sgray_8"})text(m,0x44,"pwg-raster-document-type-supported",v);for(String v:new String[]{"V1.4","CP1","W8","SRGB24","RS300","DM1"})text(m,0x44,"urf-supported",v);
  for(String k:new String[]{"media-default","media-supported"})text(m,0x44,k,mediaName(paper));if(ready)text(m,0x44,"media-ready",mediaName(paper));
  for(String k:new String[]{"media-type-default","media-type-supported"})text(m,0x44,k,"photographic");for(String edge:new String[]{"left","right","top","bottom"})num(m,0x21,"media-"+edge+"-margin-supported",0);
  for(String member:new String[]{"media-size","media-type","media-left-margin","media-right-margin","media-top-margin","media-bottom-margin"})text(m,0x44,"media-col-supported",member);collection(m,"media-col-default",paper);collection(m,"media-col-database",paper);
 }
 private static void require(boolean ok,int code,String why)throws IppWire.Failure{if(!ok)throw new IppWire.Failure(code,why);}
 private void validate(IppWire.Message req)throws Exception{
  int paper=media();String mime=req.text("document-format","image/jpeg");require(Arrays.asList(AirPrintPages.FORMATS).contains(mime),0x40a,"Unsupported format");require(paper!=5014||mime.equals("image/jpeg")||mime.equals("application/pdf"),0x40b,"Splice requires JPEG or PDF");
  require(req.number("copies",1)==1&&req.number("number-up",1)==1,0x40b,"One copy per job");require(req.text("media",mediaName(paper)).equals(mediaName(paper)),0x40b,"Loaded paper differs");require(Arrays.asList("fit","fill").contains(req.text("print-scaling","fill")),0x40b,"Unsupported scaling");require(req.text("sides","one-sided").equals("one-sided")&&req.text("compression","none").equals("none"),0x40b,"Unsupported option");require(req.one("page-ranges")==null,0x40b,"Page ranges unsupported");require(req.number("orientation-requested",3)>=3&&req.number("orientation-requested",3)<=6,0x40b,"Unsupported orientation");
  require(req.text("media-type","photographic").equals("photographic")&&req.text("print-color-mode","color").equals("color")&&req.text("job-hold-until","no-hold").equals("no-hold"),0x40b,"Unsupported print option");
  require(req.number("print-quality",5)==4||req.number("print-quality",5)==5,0x40b,"Unsupported quality");
  byte[] resolution=req.one("printer-resolution");require(resolution==null||Arrays.equals(resolution,new byte[]{0,0,1,44,0,0,1,44,3}),0x40b,"300 dpi raster required");
  for(String axis:new String[]{"x-image-position","y-image-position"})require(req.text(axis,"center").equals("center"),0x40b,"Centered placement required");
  int depth=0;String member="";for(IppWire.Attr a:req.attrs){if(a.tag==0x34){depth++;require(depth<=2,0x40b,"Unsupported collection");}else if(a.tag==0x37){depth--;require(depth>=0,0x400,"Malformed collection");}else if(depth>0){if(a.tag==0x4a)member=new String(a.value,"UTF-8");else if(member.equals("x-dimension")||member.equals("y-dimension")){require(a.value.length==4,0x400,"Invalid dimension");int value=java.nio.ByteBuffer.wrap(a.value).getInt();require(value==(paper==5009?7620:member.equals("x-dimension")?10160:15240),0x40b,"Loaded paper differs");}else if(member.endsWith("-margin"))require(a.value.length==4&&java.nio.ByteBuffer.wrap(a.value).getInt()==0,0x40b,"Margins unsupported");else if(member.equals("media-type"))require(new String(a.value,"UTF-8").equals("photographic"),0x40b,"Photographic media required");else throw new IppWire.Failure(0x40b,"Unsupported media member");}}
  require(depth==0,0x400,"Unclosed collection");
 }
 private JSONObject find(IppWire.Message req,String client,String uri)throws Exception{
  int id=req.number("job-id",0);if(id==0){String value=req.text("job-uri","");require(value.startsWith(uri+"/jobs/"),0x406,"Job not found");id=Integer.parseInt(value.substring((uri+"/jobs/").length()));}
  for(int i=0;i<rows.length();i++){JSONObject row=rows.getJSONObject(i);if(row.getInt("id")==id&&row.getString("client").equals(client))return row;}throw new IppWire.Failure(0x406,"Job not found");
 }
 private String phase(JSONObject row)throws Exception{String owner=row.getString("owner");JSONObject current=Store.read(context,"job.json");if(owner.equals(current.optString("owner")))return current.optString("phase");JSONArray jobs=PrintJobs.records(context);for(int i=0;i<jobs.length();i++){JSONObject j=jobs.getJSONObject(i);if(owner.equals(j.optString("owner")))return j.optString("phase").equals("active")?"aborted":j.optString("phase");}return row.getString("phase");}
 private void jobAttrs(IppWire.Message response,JSONObject row,String uri)throws Exception{response.attrs.add(new IppWire.Attr(2,0,"",new byte[0]));String phase=phase(row);int status=phase.equals("done")?9:phase.equals("cancelled")?7:phase.equals("aborted")||phase.equals("rejected")?8:phase.equals("queued")?3:phase.equals("receiving")||phase.equals("rendering")?4:phase.equals("uncertain")||phase.equals("blocked")?6:5;response.attrs.add(IppWire.integer(2,0x21,"job-id",row.getInt("id")));response.attrs.add(IppWire.text(2,0x45,"job-uri",uri+"/jobs/"+row.getInt("id")));response.attrs.add(IppWire.integer(2,0x23,"job-state",status));response.attrs.add(IppWire.text(2,0x44,"job-state-reasons",status==9?"job-completed-successfully":status==7?"job-canceled-by-user":status==8?"job-aborted-by-system":"none"));}
 public synchronized LocalHttp.Response handle(LocalHttp.Request http)throws Exception{
  if(!http.method.equals("POST")||!http.path.equals("/ipp/print"))return LocalHttp.Response.text(404,"text/plain","Not found");IppWire.Message req=IppWire.decode(http.body),response=IppWire.response(req);String uri="ipp://"+http.host+"/ipp/print",client=PrintJobs.digest(http.peer);
  try{
   require(req.version==0x101||req.version==0x200,0x503,"Unsupported IPP version");
   for(int i=0;i<rows.length();i++){JSONObject row=rows.getJSONObject(i);if(row.getString("phase").equals("receiving")&&System.currentTimeMillis()-row.getLong("created")>300000){row.put("phase","aborted");save();}}
   if(req.code==11)capabilities(response,uri);
   else if(req.code==4){validate(req);require(accepting(),0x507,"Connect printer on phone");}
   else if(req.code==2||req.code==5||req.code==6){
    String key=PrintJobs.digest(client+Base64.encodeToString(http.body,Base64.NO_WRAP));JSONObject row=null;
    if(req.code==6){row=find(req,client,uri);if(row.optString("documentKey").equals(key)&&!phase(row).equals("receiving")){jobAttrs(response,row,uri);return new LocalHttp.Response(200,"application/ipp",IppWire.encode(response));}require(phase(row).equals("receiving"),0x404,"Job is closed");require(Arrays.equals(req.one("last-document"),new byte[]{1}),0x40b,"One final document required");IppWire.Message saved=IppWire.decode(Base64.decode(row.getString("attrs"),Base64.DEFAULT));Set<String> names=new HashSet<>();for(IppWire.Attr a:req.attrs)names.add(a.name);for(IppWire.Attr a:saved.attrs)if(!names.contains(a.name))req.attrs.add(a);}
    else{for(int i=0;i<rows.length();i++)if(rows.getJSONObject(i).getString("key").equals(key))row=rows.getJSONObject(i);if(row!=null){jobAttrs(response,row,uri);return new LocalHttp.Response(200,"application/ipp",IppWire.encode(response));}}
    validate(req);require(accepting(),0x507,"Connect printer on phone");
    if(row==null){require(rows.length()<128,0x507,"Queue history full; restart sharing after clearing history");row=new JSONObject().put("id",rows.length()+1).put("client",client).put("key",key).put("owner","ipp-"+UUID.randomUUID()).put("phase","receiving").put("created",System.currentTimeMillis());byte[] document=req.document;req.document=new byte[0];row.put("attrs",Base64.encodeToString(IppWire.encode(req),Base64.NO_WRAP));req.document=document;rows.put(row);save();}
    if(req.code!=5){row.put("phase","rendering").put("documentKey",key);save();int paper=media();try{
      JSONArray pages=AirPrintPages.render(context,req.document,req.text("document-format","image/jpeg"),paper,req.text("print-scaling","fill"),req.number("orientation-requested",0));
      require(paper==media()&&accepting(),0x507,"Paper or connection changed");PrintJobs.submit(context,row.getString("owner"),key,pages.toString());row.put("phase","queued");save();
     }catch(Exception|OutOfMemoryError e){row.put("phase","aborted");save();throw new IppWire.Failure(0x40b,"Document preparation failed");}}
    jobAttrs(response,row,uri);
   }else if(req.code==8||req.code==9){JSONObject row=find(req,client,uri);if(req.code==8){require(!Arrays.asList("done","cancelled","aborted","rejected").contains(phase(row)),0x404,"Job already ended");PrintJobs.cancel(context,row.getString("owner"));row.put("phase","cancelled");save();}jobAttrs(response,row,uri);}
   else if(req.code==10){String which=req.text("which-jobs","not-completed");require(Arrays.asList("all","completed","not-completed").contains(which),0x40b,"Unsupported job selection");for(int i=0;i<rows.length();i++){JSONObject row=rows.getJSONObject(i);boolean done=Arrays.asList("done","cancelled","aborted","rejected").contains(phase(row));if(row.getString("client").equals(client)&&(which.equals("all")||done==which.equals("completed")))jobAttrs(response,row,uri);}}
   else throw new IppWire.Failure(0x501,"Unsupported operation");
  }catch(IppWire.Failure e){response.code=e.code;response.attrs=IppWire.response(req).attrs;response.attrs.add(IppWire.text(1,0x41,"status-message",e.getMessage()));}
  catch(Exception e){response.code=0x400;response.attrs=IppWire.response(req).attrs;response.attrs.add(IppWire.text(1,0x41,"status-message","Invalid request"));}
  return new LocalHttp.Response(200,"application/ipp",IppWire.encode(response));
 }
}
