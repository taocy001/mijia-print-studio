package local.liuying.studio;
import android.app.Instrumentation;
import android.content.*;
import android.os.Bundle;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import org.json.*;
public final class WebSessionsInstrument extends Instrumentation {
 static void check(boolean value,String text){if(!value)throw new AssertionError(text);}
 static LocalHttp.Response call(WebApi api,String method,String path,String cookie,String body)throws Exception{LocalHttp.Request r=new LocalHttp.Request();r.method=method;r.path=path;r.host="127.0.0.1";if(cookie!=null)r.headers.put("cookie",cookie);r.body=body.getBytes(StandardCharsets.UTF_8);return api.handle(r);}
 static String pair(WebApi api,String old)throws Exception{LocalHttp.Response r=call(api,"POST","/api/pair",old,"code="+api.sessions.code);check(r.status==303,"Pair accepted");check(r.headers.get("Set-Cookie").contains("Max-Age=31536000")&&r.cookies.get(0).contains("Max-Age=31536000"),"Both cookies last one year");return r.headers.get("Set-Cookie").split(";")[0]+"; "+r.cookies.get(0).split(";")[0];}
 static String ownerOnly(String cookie){return cookie.substring(cookie.indexOf("liuying-owner="));}
 @Override public void onCreate(Bundle args){super.onCreate(args);start();}
 @Override public void onStart(){Bundle result=new Bundle();File dir=new File(getTargetContext().getCacheDir(),"web-session-test-"+System.nanoTime());dir.mkdirs();Context ctx=new ContextWrapper(getTargetContext()){@Override public File getFilesDir(){return dir;}};
  try{
   WebApi api=new WebApi(ctx);String alice=pair(api,null);WebSessions.Session session=api.sessions.find(alice);String id=session.id;
   File photo=new File(dir,"photos/a.jpg"),printed=new File(dir,"prints/a.jpg");photo.getParentFile().mkdirs();printed.getParentFile().mkdirs();Files.write(photo.toPath(),new byte[]{1,2,3});Files.write(printed.toPath(),new byte[]{4,5,6});session.files.add("/private/photos/a.jpg");api.sessions.remember(session);
   Store.write(ctx,"history.json",new JSONObject().put("items",new JSONArray().put(new JSONObject().put("owner",id).put("token","past").put("phase","aborted").put("file","prints/a.jpg"))));
   Store.write(ctx,"web-queue.json",new JSONObject().put("items",new JSONArray().put(new JSONObject().put("owner",id).put("token","held").put("phase","uncertain"))));String queue=PrintJobs.records(ctx).toString();
   api.sessions.clear();check(call(api,"GET","/private/photos/a.jpg",alice,"").status==200,"Stop preserves paired browser");
   WebApi restarted=new WebApi(ctx);check(call(restarted,"GET","/private/prints/a.jpg",alice,"").status==200,"History grant restored before state fetch");check(call(restarted,"GET","/api/state",alice,"").status==200,"Session persists across restart");check(call(restarted,"GET","/private/photos/a.jpg",ownerOnly(alice),"").status==401,"Owner cookie alone cannot read");
   String restored=alice;check(id.equals(restarted.sessions.find(restored).id),"Owner restored without fresh pairing");check(call(restarted,"GET","/private/photos/a.jpg",restored,"").status==200,"Uploaded photo grant restored");
   check(call(restarted,"GET","/private/prints/a.jpg",restored,"").status==200,"History grant restored before editor draft loads");
   JSONObject state=new JSONObject(new String(call(restarted,"GET","/api/state",restored,"").body,StandardCharsets.UTF_8));check(state.getJSONArray("history").length()==1,"Own history restored");check(call(restarted,"GET","/private/prints/a.jpg",restored,"").status==200,"Durable print history restores grant without post-submit metadata save");
   String bob=pair(restarted,null);check(call(restarted,"GET","/private/photos/a.jpg",bob,"").status==404&&call(restarted,"GET","/private/prints/a.jpg",bob,"").status==404,"Other browser cannot read photos or history images");
   check(new JSONObject(new String(call(restarted,"GET","/api/state",bob,"").body,StandardCharsets.UTF_8)).getJSONArray("history").length()==0,"Other owner history isolated");check(queue.equals(PrintJobs.records(ctx).toString()),"Pairing and recovery never requeue or replay jobs");
   check(call(restarted,"GET","/api/sharing",null,"").status==401,"Unpaired cannot see pairing code");
   JSONObject sharing=new JSONObject(new String(call(restarted,"GET","/api/sharing",restored,"").body,StandardCharsets.UTF_8));check(sharing.getString("code").equals(restarted.sessions.code)&&!sharing.getBoolean("canManagePairing"),"Paired browser sees current code without management permission");
   check(call(restarted,"POST","/api/pairing/reset",restored,"{}").status==404,"No remote reset endpoint");
   String previous=restarted.sessions.code;restarted.sessions.revokeAll();check(!previous.equals(restarted.sessions.code),"Reset rotates code");check(call(restarted,"GET","/api/sharing",restored,"").status==401&&call(restarted,"GET","/api/state",bob,"").status==401,"All browser credentials revoked");
   WebApi afterReset=new WebApi(ctx);check(call(afterReset,"GET","/api/state",restored,"").status==401,"Revocation survives restart");String pairedAgain=pair(afterReset,alice);check(afterReset.sessions.find(pairedAgain).id.equals(id),"Explicit re-pair recovers owner history");check(call(afterReset,"GET","/private/prints/a.jpg",pairedAgain,"").status==200,"History survives reset");
   result.putString("stream","PASS: Android durable pairing, private-file/history isolation, native-only reset and no job replay; isolated files, no printing\n");finish(-1,result);
  }catch(Throwable error){result.putString("stream",error.toString()+"\n");finish(0,result);}finally{erase(dir);}
 }
 static void erase(File file){File[] children=file.listFiles();if(children!=null)for(File child:children)erase(child);file.delete();}
}
