package local.liuying.studio;
import android.app.Instrumentation;
import android.content.*;
import android.content.pm.ProviderInfo;
import android.graphics.*;
import android.net.Uri;
import android.os.*;
import android.provider.OpenableColumns;
import java.io.*;
import java.nio.file.*;
import java.util.UUID;
import org.json.*;

public final class CaptureInstrument extends Instrumentation {
 private int checks;
 private void check(boolean yes,String message){checks++;if(!yes)throw new AssertionError(message);}
 private static void remove(File file)throws Exception{if(Files.isSymbolicLink(file.toPath())){Files.delete(file.toPath());return;}if(file.isDirectory()){File[] children=file.listFiles();if(children!=null)for(File child:children)remove(child);}Files.deleteIfExists(file.toPath());}
 @Override public void onCreate(Bundle args){super.onCreate(args);start();}
 @Override public void onStart(){Bundle result=new Bundle();File root=new File(getTargetContext().getCacheDir(),"capture-test-"+System.nanoTime());root.mkdirs();Context context=new ContextWrapper(getTargetContext()){
  @Override public File getFilesDir(){File f=new File(root,"files");f.mkdirs();return f;}
  @Override public File getCacheDir(){File f=new File(root,"cache");f.mkdirs();return f;}
 };
 try{
  boolean rejected=false;try{CameraCapture.begin(context,0);}catch(IOException expected){rejected=true;}check(rejected&&!CameraCapture.read(context).has("id"),"No space cannot begin capture");
  JSONObject pending=CameraCapture.begin(context,6);String id=pending.getString("id");File output=CaptureProvider.output(context,id);check(output.exists()&&output.length()==0,"Full-resolution output prepared");
  rejected=false;try{CameraCapture.begin(context,5);}catch(IOException expected){rejected=true;}check(rejected,"Concurrent capture rejected");check(CameraCapture.read(context).getString("id").equals(id),"Pending capture survives helper reconstruction");
  CaptureProvider provider=new CaptureProvider();ProviderInfo info=new ProviderInfo();info.authority=CaptureProvider.AUTHORITY;info.exported=false;info.grantUriPermissions=true;provider.attachInfo(context,info);Uri uri=CaptureProvider.uri(id);
  check(provider.getType(uri).equals("image/jpeg"),"Provider MIME type");try(android.database.Cursor cursor=provider.query(uri,null,null,null,null)){check(cursor.moveToFirst()&&cursor.getString(cursor.getColumnIndexOrThrow(OpenableColumns.DISPLAY_NAME)).equals(id+".jpg"),"Provider exposes only fixed filename");}
  for(String path:new String[]{"../photos/a.jpg","/etc/passwd",id+".jpg/child","%2e%2e%2f"+id+".jpg",id+".jpg?other=1",id+".jpg#fragment","bad.jpg"}){rejected=false;try{CaptureProvider.resolve(context,Uri.parse("content://"+CaptureProvider.AUTHORITY+"/"+path));}catch(IOException expected){rejected=true;}check(rejected,"Reject malformed URI "+path);}
  rejected=false;try{provider.openFile(uri,"wa");}catch(FileNotFoundException expected){rejected=true;}check(rejected,"Append mode rejected");
  try(OutputStream stream=new ParcelFileDescriptor.AutoCloseOutputStream(provider.openFile(uri,"wt"))){stream.write(new byte[]{1,2,3,4});stream.flush();}
  CameraCapture.receive(context,false,null);JSONObject ready=CameraCapture.finish(context);check(ready.getJSONObject("finished").optBoolean("cancelled")&&!output.exists(),"Cancelled result deletes temporary output");check(ready.getJSONArray("photos").length()==0,"Cancelled result imports nothing");CameraCapture.acknowledge(context,"wrong");check(CameraCapture.read(context).has("id"),"Wrong acknowledgement ignored");CameraCapture.acknowledge(context,id);check(!CameraCapture.read(context).has("id"),"Acknowledgement clears journal");
  pending=CameraCapture.begin(context,1);id=pending.getString("id");output=CaptureProvider.output(context,id);Files.write(output.toPath(),new byte[]{1,2,3,4,5});CameraCapture.receive(context,true,null);ready=CameraCapture.finish(context);check(ready.getJSONObject("finished").has("error")&&!output.exists(),"Corrupt capture reports error and cleans file");CameraCapture.acknowledge(context,id);
  pending=CameraCapture.begin(context,1);id=pending.getString("id");CameraCapture.receive(context,false,"无法打开相机");ready=CameraCapture.finish(context);check(ready.getJSONObject("finished").getString("error").equals("无法打开相机"),"Launch failure durable until acknowledged");CameraCapture.acknowledge(context,id);
  pending=CameraCapture.begin(context,1);id=pending.getString("id");output=CaptureProvider.output(context,id);Bitmap bitmap=Bitmap.createBitmap(3000,1500,Bitmap.Config.ARGB_8888);bitmap.eraseColor(Color.rgb(15,110,200));try(FileOutputStream stream=new FileOutputStream(output)){bitmap.compress(Bitmap.CompressFormat.JPEG,95,stream);}bitmap.recycle();
  CameraCapture.receive(context,true,null);check(CameraCapture.read(context).getString("stage").equals("received"),"Result receipt persisted before decoding");ready=CameraCapture.finish(context);JSONObject photo=ready.getJSONArray("photos").getJSONObject(0);check(photo.getInt("width")==2400&&photo.getInt("height")==1200,"Full-resolution capture resized proportionally");check(photo.getString("captureId").equals(id)&&photo.getString("src").equals("/private/photos/"+id+".jpg"),"Stable source and capture identity");check(!output.exists(),"Successful capture removes camera temporary file");
  check(CameraCapture.finish(context).toString().equals(ready.toString()),"Unacknowledged result redelivers without reimport");File imported=new File(context.getFilesDir(),"photos/"+id+".jpg");long length=imported.length();CameraCapture.acknowledge(context,id);check(imported.exists()&&imported.length()==length&&!CameraCapture.read(context).has("id"),"Acknowledgement preserves imported photo");
  pending=CameraCapture.begin(context,1);id=pending.getString("id");CameraCapture.recover(context,true);check(CameraCapture.read(context).getString("stage").equals("waiting"),"Restored activity preserves pending camera result");CameraCapture.recover(context,false);ready=CameraCapture.finish(context);check(ready.getJSONObject("finished").optBoolean("cancelled"),"Cold restart cancels unreturned capture instead of guessing success");CameraCapture.acknowledge(context,id);
  String linkId=UUID.randomUUID().toString();File link=CaptureProvider.output(context,linkId);Files.createSymbolicLink(link.toPath(),imported.toPath());rejected=false;try{CaptureProvider.resolve(context,CaptureProvider.uri(linkId));}catch(IOException expected){rejected=true;}check(rejected&&imported.exists(),"Symlink output rejected without touching source");
  result.putString("result","PASS: capture "+checks+" checks; synthetic files only, no camera launched");
 }catch(Throwable error){result.putString("error",android.util.Log.getStackTraceString(error));}finally{try{remove(root);}catch(Exception ignored){}}finish(result.containsKey("error")?1:-1,result);}
}
