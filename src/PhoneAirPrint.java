package local.liuying.studio;
import android.content.Context;
import android.util.Base64;
import java.io.*;
import java.util.*;
import org.json.*;
final class PhoneAirPrint implements LocalHttp.Handler {
 private volatile boolean closed;
 void close(){closed=true;}
 private final Context context;private JSONArray rows;private long nextId;private final long started=System.currentTimeMillis();
 PhoneAirPrint(Context c)throws Exception{
  context=c;JSONObject stored=Store.read(c,"ipp-jobs.json");JSONArray saved=stored.optJSONArray("items");rows=saved==null?new JSONArray():saved;nextId=Math.max(1,stored.optLong("nextId",1));for(int i=0;i<rows.length();i++)nextId=Math.max(nextId,rows.getJSONObject(i).optLong("id")+1);
  for(int i=0;i<rows.length();i++){JSONObject row=rows.getJSONObject(i);String phase=row.optString("phase");
   if(phase.equals("receiving")||phase.equals("rendering")){
    JSONObject queued=queued(row.optString("owner"));
    if(queued!=null)row.put("phase",queued.optString("phase")).put("message","已恢复已接收的打印任务，请查看原任务状态");
    else{row.put("phase","aborted");failure(row,"restart","共享服务重启，未完成的照片接收已中止");}
   }
  }compact();save();
 }
 private JSONObject queued(String owner)throws Exception{
  JSONArray jobs=PrintJobs.records(context);for(int i=0;i<jobs.length();i++){JSONObject job=jobs.getJSONObject(i);if(owner.equals(job.optString("owner")))return job;}return null;
 }
 private void failure(JSONObject row,String stage,String message)throws Exception{
  String token=row.optString("owner","ipp-"+UUID.randomUUID());row.put("message",message);if(Store.terminal(row)&&!row.has("completedAt"))row.put("completedAt",System.currentTimeMillis());
  Store.failure(context,token,row.optString("owner"),stage,message);
 }
 private static boolean printRequest(byte[] body,boolean incomplete){
  if(body.length<4)return incomplete;
  int version=((body[0]&255)<<8)|(body[1]&255),op=((body[2]&255)<<8)|(body[3]&255);
  return (version==0x101||version==0x200)&&(op==2||op==4||op==5||op==6);
 }
 @Override public synchronized void receiveFailure(LocalHttp.Request req,Exception e){
  if(!printRequest(req.body,true))return;
  try{Store.failure(context,"ipp-receive-"+UUID.randomUUID(),"","receiving",e instanceof java.net.SocketTimeoutException?"AirPrint 接收超时，请检查网络和原打印任务状态":"AirPrint 接收中断，请检查网络和原打印任务状态");android.util.Log.w("LiuyingAirPrint","HTTP receive failed: "+e.getClass().getSimpleName());}catch(Exception ignored){}
 }
 private static String reason(Exception e){String m=e.getMessage();if(m==null)return "AirPrint 请求未完成";if(m.startsWith("AirPrint "))return m;
  switch(m){case "Connect printer on phone":return "AirPrint 尚未提交：请先在手机连接打印机并读取相纸";case "Loaded paper differs":return "AirPrint 相纸设置与实际纸盒不一致";case "Unsupported format":return "AirPrint 照片格式不支持";case "Paper or connection changed":return "AirPrint 处理期间连接或相纸已变化，请重新检查";default:return e instanceof IppWire.Failure?"AirPrint 请求不支持："+m:"AirPrint 照片处理失败，请检查文件后重试";}
 }
 private void save()throws Exception{Store.write(context,"ipp-jobs.json",new JSONObject().put("items",rows).put("nextId",nextId));}
 private void compact()throws Exception{
  String before=rows.toString();JSONArray jobs=PrintJobs.records(context);Map<String,JSONObject> owners=new HashMap<>();for(int i=0;i<jobs.length();i++){JSONObject job=jobs.getJSONObject(i);owners.put(job.optString("owner"),job);}
  for(int i=0;i<rows.length();i++){JSONObject row=rows.getJSONObject(i),job=owners.get(row.optString("owner"));if(job!=null&&Store.terminal(job)){row.put("phase",job.optString("phase")).put("message",job.optString("message")).put("completedAt",JobRetention.time(job,System.currentTimeMillis()));}}
  JSONArray trimmed=JobRetention.compact(rows,Collections.emptySet(),System.currentTimeMillis());rows=trimmed;if(!before.equals(rows.toString()))save();
 }
 private int media(){int tray=PrinterStatus.media(context);return tray==5012&&PrinterStatus.splice?5014:tray;}
 private static String mediaName(int m){return m==5009?"custom_square_3x3in":m==5012||m==5014?"na_index-4x6_4x6in":"";}
 private boolean accepting(){return !closed&&PrinterStatus.ready(context,SharingService.queuePaused());}
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
  text(m,0x42,"printer-name",SharingService.printerName(context));text(m,0x41,"printer-info","留影工坊 · 手机 蓝牙打印");text(m,0x41,"printer-make-and-model","Liuying Photo Printer");text(m,0x45,"printer-uri-supported",uri);text(m,0x45,"printer-uuid",SharingService.printerUuid(context));
  text(m,0x44,"uri-security-supported","none");text(m,0x44,"uri-authentication-supported","none");bool(m,"printer-is-accepting-jobs",ready);num(m,0x23,"printer-state",ready?(Store.busy?4:3):5);text(m,0x44,"printer-state-reasons",ready?"none":"paused");text(m,0x41,"printer-state-message",ready?"Ready":"Connect printer on phone");num(m,0x21,"printer-up-time",(int)((System.currentTimeMillis()-started)/1000));num(m,0x21,"queued-job-count",JobRetention.pending(PrintJobs.records(context)));
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
  if(paper!=0){for(String k:new String[]{"media-default","media-supported"})text(m,0x44,k,mediaName(paper));if(ready)text(m,0x44,"media-ready",mediaName(paper));
  for(String k:new String[]{"media-type-default","media-type-supported"})text(m,0x44,k,"photographic");for(String edge:new String[]{"left","right","top","bottom"})num(m,0x21,"media-"+edge+"-margin-supported",0);
  for(String member:new String[]{"media-size","media-type","media-left-margin","media-right-margin","media-top-margin","media-bottom-margin"})text(m,0x44,"media-col-supported",member);collection(m,"media-col-default",paper);collection(m,"media-col-database",paper);}
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
 private String phase(JSONObject row)throws Exception{
  synchronized(Store.LOCK){String owner=row.getString("owner");JSONObject current=Store.read(context,"job.json"),job=queued(owner);
   if(job!=null&&Store.terminal(job))return job.optString("phase");
   if(owner.equals(current.optString("owner"))){if(current.optString("phase").equals("done")&&current.optJSONArray("remaining")!=null&&current.getJSONArray("remaining").length()>0)return Store.busy?"printing":"uncertain";return current.optString("phase");}
   String value=job==null?row.getString("phase"):job.optString("phase");return value.equals("active")?"uncertain":value;
  }
 }
 private String message(JSONObject row,String phase)throws Exception{
  JSONObject job=queued(row.getString("owner"));if(job!=null&&Store.terminal(job))return job.optString("message",phase);
  JSONObject current=Store.read(context,"job.json");if(row.getString("owner").equals(current.optString("owner"))){if(phase.equals("uncertain")&&current.optString("phase").equals("done"))return "本批后续照片未自动发送，请检查原任务";return current.optString("message",phase);}
  if(phase.equals("uncertain"))return "任务结果尚未确认，请在手机上检查，不要重复打印";
  return row.optString("message",job==null?phase:job.optString("message",phase));
 }
 private void jobAttrs(IppWire.Message response,JSONObject row,String uri)throws Exception{response.attrs.add(new IppWire.Attr(2,0,"",new byte[0]));String phase=phase(row);int status=phase.equals("done")?9:phase.equals("cancelled")?7:phase.equals("aborted")||phase.equals("rejected")?8:phase.equals("queued")?3:phase.equals("receiving")||phase.equals("rendering")?4:phase.equals("uncertain")||phase.equals("blocked")||phase.equals("held")?6:5;response.attrs.add(IppWire.text(2,0x41,"job-state-message",message(row,phase)));response.attrs.add(IppWire.integer(2,0x21,"job-id",row.getInt("id")));response.attrs.add(IppWire.text(2,0x45,"job-uri",uri+"/jobs/"+row.getInt("id")));response.attrs.add(IppWire.integer(2,0x23,"job-state",status));response.attrs.add(IppWire.text(2,0x44,"job-state-reasons",status==9?"job-completed-successfully":status==7?"job-canceled-by-user":status==8?"job-aborted-by-system":status==6?"job-stopped":"none"));}
 public synchronized LocalHttp.Response handle(LocalHttp.Request http)throws Exception{
  if(!http.method.equals("POST")||!http.path.equals("/ipp/print"))return LocalHttp.Response.text(404,"text/plain","Not found");IppWire.Message req;
  try{req=IppWire.decode(http.body);}catch(Exception e){
   if(printRequest(http.body,false))try{Store.failure(context,"ipp-invalid-"+PrintJobs.digest(Base64.encodeToString(http.body,Base64.NO_WRAP)),"","receiving","AirPrint 打印请求不完整，未能解析任务，请检查发送端");}catch(Exception ignored){}
   android.util.Log.w("LiuyingAirPrint","IPP decode failed: "+e.getClass().getSimpleName());return LocalHttp.Response.text(400,"text/plain; charset=utf-8","AirPrint 请求无效");
  }
  IppWire.Message response=IppWire.response(req);String uri="ipp://"+http.host+"/ipp/print",client=PrintJobs.digest(http.peer);JSONObject handling=null;
  try{
   require(req.version==0x101||req.version==0x200,0x503,"Unsupported IPP version");compact();
   for(int i=0;i<rows.length();i++){JSONObject row=rows.getJSONObject(i);if(row.getString("phase").equals("receiving")&&System.currentTimeMillis()-row.getLong("created")>300000){row.put("phase","aborted");failure(row,"receiving","AirPrint 接收超时，照片未发送到打印机");save();}}
   if(req.code==11)capabilities(response,uri);
   else if(req.code==4){require(accepting(),0x507,"Connect printer on phone");validate(req);}
   else if(req.code==2||req.code==5||req.code==6){
    String key=PrintJobs.digest(client+Base64.encodeToString(http.body,Base64.NO_WRAP));JSONObject row=null;
    if(req.code==6){row=find(req,client,uri);if(row.optString("documentKey").equals(key)&&!phase(row).equals("receiving")){jobAttrs(response,row,uri);return new LocalHttp.Response(200,"application/ipp",IppWire.encode(response));}require(phase(row).equals("receiving"),0x404,"Job is closed");require(Arrays.equals(req.one("last-document"),new byte[]{1}),0x40b,"One final document required");IppWire.Message saved=IppWire.decode(Base64.decode(row.getString("attrs"),Base64.DEFAULT));Set<String> names=new HashSet<>();for(IppWire.Attr a:req.attrs)names.add(a.name);for(IppWire.Attr a:saved.attrs)if(!names.contains(a.name))req.attrs.add(a);}
    else{for(int i=0;i<rows.length();i++)if(rows.getJSONObject(i).getString("key").equals(key))row=rows.getJSONObject(i);if(row!=null){jobAttrs(response,row,uri);return new LocalHttp.Response(200,"application/ipp",IppWire.encode(response));}}
    require(accepting(),0x507,"Connect printer on phone");validate(req);
    if(row==null){require(JobRetention.pending(rows)<128,0x507,"Too many unfinished jobs");require(nextId<=Integer.MAX_VALUE,0x507,"Job identifier limit reached");row=new JSONObject().put("id",nextId++).put("client",client).put("key",key).put("owner","ipp-"+UUID.randomUUID()).put("phase","receiving").put("created",System.currentTimeMillis());byte[] document=req.document;req.document=new byte[0];row.put("attrs",Base64.encodeToString(IppWire.encode(req),Base64.NO_WRAP));req.document=document;rows.put(row);save();}
    handling=row;
    if(req.code!=5){
     row.put("phase","rendering").put("documentKey",key);save();int paper=media();JSONArray pages;
     try{pages=AirPrintPages.render(context,req.document,req.text("document-format","image/jpeg"),paper,req.text("print-scaling","fill"),req.number("orientation-requested",0));require(paper==media()&&accepting(),0x507,"Paper or connection changed");}
     catch(Exception|OutOfMemoryError e){row.put("phase","aborted");failure(row,"rendering",e instanceof Exception?reason((Exception)e):"AirPrint 照片过大，处理内存不足");save();android.util.Log.w("LiuyingAirPrint","Document preparation failed: "+e.getClass().getSimpleName());throw new IppWire.Failure(0x40b,row.getString("message"));}
     try{PrintJobs.submit(context,row.getString("owner"),key,pages.toString());}
     catch(Exception|OutOfMemoryError e){
      if(queued(row.getString("owner"))==null){row.put("phase","aborted");failure(row,"queue","AirPrint 未能加入打印队列，请在手机上检查");save();throw new IppWire.Failure(0x507,row.getString("message"));}
     }
     row.put("phase","queued");
     try{save();}catch(Exception e){row.put("message","任务已接收，请查看原任务状态，不要重复打印");android.util.Log.w("LiuyingAirPrint","Accepted IPP state save failed: "+e.getClass().getSimpleName());}
    }
    jobAttrs(response,row,uri);
   }else if(req.code==8||req.code==9){JSONObject row=find(req,client,uri);if(req.code==8){require(!Arrays.asList("done","cancelled","aborted","rejected").contains(phase(row)),0x404,"Job already ended");PrintJobs.cancel(context,row.getString("owner"));row.put("phase","cancelled").put("completedAt",System.currentTimeMillis());save();}jobAttrs(response,row,uri);}
   else if(req.code==10){String which=req.text("which-jobs","not-completed");require(Arrays.asList("all","completed","not-completed").contains(which),0x40b,"Unsupported job selection");for(int i=0;i<rows.length();i++){JSONObject row=rows.getJSONObject(i);boolean done=Arrays.asList("done","cancelled","aborted","rejected").contains(phase(row));if(row.getString("client").equals(client)&&(which.equals("all")||done==which.equals("completed")))jobAttrs(response,row,uri);}}
   else throw new IppWire.Failure(0x501,"Unsupported operation");
  }catch(IppWire.Failure e){
   if((req.code==2||req.code==4||req.code==5||req.code==6)&&handling==null){Store.failure(context,"ipp-"+PrintJobs.digest(client+Base64.encodeToString(http.body,Base64.NO_WRAP)),"","validation",reason(e));}
   response.code=e.code;response.attrs=IppWire.response(req).attrs;response.attrs.add(IppWire.text(1,0x41,"status-message",reason(e)));}
  catch(Exception e){
   android.util.Log.w("LiuyingAirPrint","IPP handling failed: "+e.getClass().getSimpleName());
   boolean accepted=handling!=null&&queued(handling.optString("owner"))!=null;
   if(accepted){response=IppWire.response(req);jobAttrs(response,handling,uri);}
   else{if(printRequest(http.body,false))try{Store.failure(context,handling==null?"ipp-invalid-"+PrintJobs.digest(Base64.encodeToString(http.body,Base64.NO_WRAP)):handling.optString("owner"),handling==null?"":handling.optString("owner"),"preparation","AirPrint 任务处理失败，请在手机上检查");}catch(Exception ignored){}
    response.code=0x400;response.attrs=IppWire.response(req).attrs;response.attrs.add(IppWire.text(1,0x41,"status-message","AirPrint 任务处理失败"));}
  }
  return new LocalHttp.Response(200,"application/ipp",IppWire.encode(response));
 }
}
