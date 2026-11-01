package local.liuying.studio;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
public final class WebSessionsTest {
 static void check(boolean value,String text){if(!value)throw new AssertionError(text);}
 static String auth(WebSessions.Pair pair){return "liuying="+pair.token+"; liuying-owner="+pair.owner;}
 static Properties read(Path path)throws Exception{Properties data=new Properties();try(InputStream in=Files.newInputStream(path)){data.load(in);}return data;}
 static void write(Path path,Properties data)throws Exception{try(OutputStream out=Files.newOutputStream(path)){data.store(out,null);}}
 public static void main(String[] args)throws Exception{
  Path root=Files.createTempDirectory("web-sessions-");
  try{
   WebSessions first=new WebSessions(root.toFile());WebSessions.Pair alice=first.pair(first.code,null);WebSessions.Session a=first.find(auth(alice));
   a.files.add("/private/photos/a.jpg");first.remember(a);String id=a.id;
   WebSessions.Pair bob=first.pair(first.code,null);WebSessions.Session b=first.find(auth(bob));check(!id.equals(b.id)&&b.files.isEmpty(),"Browser separation");
   check(first.find("liuying-owner="+alice.owner)==null,"Owner cookie is not authentication");
   check(first.find("liuying=invalid; liuying-owner="+alice.owner)==null,"Invalid session cannot use owner identity");
   check(first.find("liuying="+alice.token+"; liuying-owner="+bob.owner).id.equals(id),"Authentication record owns the identity, not owner cookie");
   check(first.pair("not-a-code","liuying-owner="+alice.owner)==null,"Owner cookie never bypasses pairing");
   String disk=Files.readString(root.resolve("web-owners.properties"))+Files.readString(root.resolve("web-pairings.properties"));
   check(!disk.contains(alice.owner)&&!disk.contains(alice.token)&&!disk.contains(bob.token),"Raw secrets never stored");
   check(WebSessions.COOKIE_MAX_AGE==31536000L,"Pairing lifetime is one year");
   WebSessions.Pair again=first.pair(first.code,auth(alice));WebSessions.Session a2=first.find(auth(again));check(id.equals(a2.id),"Re-pair keeps owner");check(first.find(auth(alice))==null,"Re-pair invalidates the previous token");
   a2.files.add("/private/photos/new.jpg");first.remember(a2);a.files.add("/private/cutouts/old-tab.jpg");first.remember(a);
   check(a.files.contains("/private/photos/new.jpg")&&a2.files.contains("/private/cutouts/old-tab.jpg"),"Concurrent grants merged");
   a.bytes=1000;a.uploads=2;first.clear();check(first.find(auth(again)).id.equals(id),"Stopping service preserves paired authorization");
   WebSessions restarted=new WebSessions(root.toFile());WebSessions.Session restored=restarted.find(auth(again));
   check(id.equals(restored.id)&&restored.files.size()==3,"Restart restores owned files without pairing");check(restored.bytes==0&&restored.uploads==0,"Restart resets per-run upload quota");
   check(restarted.find(auth(bob)).files.isEmpty(),"Other browser cannot recover Alice files");
   String oldCode=restarted.code;restarted.revokeAll();check(!oldCode.equals(restarted.code),"Revocation rotates pairing code");
   check(restarted.find(auth(alice))==null&&restarted.find(auth(bob))==null,"Revocation removes every browser");
   check(new WebSessions(root.toFile()).find(auth(alice))==null,"Revocation survives restart");
   check(restarted.pair(oldCode,auth(alice))==null,"Old code cannot pair after reset");
   WebSessions.Pair recovered=restarted.pair(restarted.code,auth(alice));check(restarted.find(auth(recovered)).id.equals(id),"New pairing retains owner history after revocation");
   // Legacy owner records alone do not grant access after a process restart.
   Files.delete(root.resolve("web-pairings.properties"));WebSessions legacy=new WebSessions(root.toFile());check(legacy.find(auth(recovered))==null,"Legacy owners are not trusted");
   WebSessions.Pair current=legacy.pair(legacy.code,auth(alice));
   java.lang.reflect.Field field=WebSessions.class.getDeclaredField("pairings");field.setAccessible(true);((Properties)field.get(legacy)).clear();Files.delete(root.resolve("web-pairings.properties"));
   check(legacy.find(auth(current))!=null,"Existing valid memory session upgrades on first use");
   check(new WebSessions(root.toFile()).find(auth(current))!=null,"Upgraded session is durable");check(legacy.persistentCookie(auth(current)).contains("Max-Age=")&&legacy.persistentCookie("liuying-owner="+current.owner)==null,"Only authenticated cookie gets lifetime upgrade");
   Properties records=read(root.resolve("web-pairings.properties"));for(String key:records.stringPropertyNames()){String[] parts=records.getProperty(key).split(" ");long expiry=Long.parseLong(parts[1]);check(Math.abs(expiry-System.currentTimeMillis()-WebSessions.COOKIE_MAX_AGE*1000)<10000,"Explicit absolute expiry");records.setProperty(key,parts[0]+" 1");}write(root.resolve("web-pairings.properties"),records);
   WebSessions expired=new WebSessions(root.toFile());check(expired.find(auth(current))==null,"Expired token rejected");
   List<WebSessions.Pair> paired=new ArrayList<>();for(int i=0;i<12;i++){WebSessions.Pair pair=expired.pair(expired.code,null);check(pair!=null,"Expired records do not consume slots");paired.add(pair);}
   check(expired.pair(expired.code,null)==null,"Twelve persistent sessions maximum");WebSessions.Pair oldPair=paired.get(0);WebSessions.Session quota=expired.find(auth(oldPair));quota.uploads=9;quota.bytes=1234;WebSessions.Pair renewed=expired.pair(expired.code,auth(oldPair));check(renewed!=null&&expired.find(auth(oldPair))==null,"Same owner replaces token even at session capacity");check(expired.find(auth(renewed)).uploads==9&&expired.find(auth(renewed)).bytes==1234,"Re-pair retains per-process upload quota");paired.set(0,renewed);
   WebSessions capped=new WebSessions(root.toFile());check(capped.pair(capped.code,null)==null,"Restart does not bypass session limit");
   // A failed revocation must leave both active sessions and the code intact.
   Path authFile=root.resolve("web-pairings.properties"),saved=root.resolve("pairings-backup");Files.move(authFile,saved);Files.createDirectory(authFile);Files.writeString(authFile.resolve("block"),"block");String before=expired.code;
   boolean failed=false;try{expired.revokeAll();}catch(IOException expected){failed=true;}check(failed&&before.equals(expired.code)&&expired.find(auth(paired.get(0)))!=null,"Failed persistence keeps authorization and code");
   Files.delete(authFile.resolve("block"));Files.delete(authFile);Files.move(saved,authFile);expired.revokeAll();
   for(int i=0;i<5;i++)expired.pair("bad");check(expired.pair(expired.code,null)==null,"Pairing code rate limit retained");
   try(LocalHttp http=new LocalHttp(false,0,r->{LocalHttp.Response response=LocalHttp.Response.text(303,"text/plain","");response.headers.put("Set-Cookie","liuying=session; HttpOnly; SameSite=Strict; Path=/");response.cookies.add("liuying-owner=owner; HttpOnly; SameSite=Strict; Path=/");return response;})){
    try(Socket socket=new Socket("127.0.0.1",http.port())){socket.setSoTimeout(3000);socket.getOutputStream().write(("GET / HTTP/1.1\r\nHost: 127.0.0.1:"+http.port()+"\r\n\r\n").getBytes(StandardCharsets.US_ASCII));String response=new String(socket.getInputStream().readAllBytes(),StandardCharsets.US_ASCII);check(response.split("Set-Cookie:",-1).length==3,"Two separate Set-Cookie headers");}
   }
   System.out.println("PASS: durable hashed pairing, expiry, legacy migration, owner isolation, quotas, atomic revocation, code rotation and rate limit; no printing");
  }finally{try(java.util.stream.Stream<Path> files=Files.walk(root)){files.sorted(Comparator.reverseOrder()).forEach(p->{try{Files.delete(p);}catch(IOException e){throw new UncheckedIOException(e);}});}}
 }
}
