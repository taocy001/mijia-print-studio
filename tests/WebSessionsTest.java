package local.liuying.studio;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
public final class WebSessionsTest {
 static void check(boolean value,String text){if(!value)throw new AssertionError(text);}
 static String auth(WebSessions.Pair pair){return "liuying="+pair.token+"; liuying-owner="+pair.owner;}
 public static void main(String[] args)throws Exception{
  Path root=Files.createTempDirectory("web-sessions-");
  try{
   WebSessions first=new WebSessions(root.toFile());WebSessions.Pair alice=first.pair(first.code,null);WebSessions.Session a=first.find(auth(alice));
   a.files.add("/private/photos/a.jpg");first.remember(a);String id=a.id;
   WebSessions.Pair bob=first.pair(first.code,null);WebSessions.Session b=first.find(auth(bob));check(!id.equals(b.id)&&b.files.isEmpty(),"Browser separation");
   check(first.find("liuying-owner="+alice.owner)==null,"Owner cookie is not authentication");
   check(first.pair("not-a-code","liuying-owner="+alice.owner)==null,"Owner cookie never bypasses pairing");
   check(!new String(Files.readAllBytes(root.resolve("web-owners.properties")),StandardCharsets.ISO_8859_1).contains(alice.owner),"Raw owner secret not stored");
   WebSessions.Pair again=first.pair(first.code,auth(alice));WebSessions.Session a2=first.find(auth(again));check(id.equals(a2.id),"Re-pair keeps owner");
   a2.files.add("/private/photos/new.jpg");first.remember(a2);a.files.add("/private/cutouts/old-tab.jpg");first.remember(a);
   check(a.files.contains("/private/photos/new.jpg")&&a2.files.contains("/private/cutouts/old-tab.jpg"),"Concurrent grants merged");
   first.clear();check(first.find(auth(alice))==null&&first.find(auth(again))==null,"Stop revokes all sessions");
   WebSessions restarted=new WebSessions(root.toFile());check(restarted.find(auth(again))==null,"Restart requires new pairing");
   WebSessions.Pair recovered=restarted.pair(restarted.code,auth(alice));WebSessions.Session restored=restarted.find(auth(recovered));
   check(id.equals(restored.id)&&restored.files.size()==3,"Restart restores all owned files");check(restored.bytes==0&&restored.uploads==0,"History does not consume upload quota");
   WebSessions.Pair fresh=restarted.pair(restarted.code,"liuying-owner="+String.join("",Collections.nCopies(64,"A")));check(!id.equals(restarted.find(auth(fresh)).id),"Invented owner cookie cannot choose existing identity");
   WebSessions.Pair bobAgain=restarted.pair(restarted.code,auth(bob));check(restarted.find(auth(bobAgain)).files.isEmpty(),"Other browser cannot recover Alice files");
   try(LocalHttp http=new LocalHttp(false,0,r->{LocalHttp.Response response=LocalHttp.Response.text(303,"text/plain","");response.headers.put("Set-Cookie","liuying=session; HttpOnly; SameSite=Strict; Path=/");response.cookies.add("liuying-owner=owner; HttpOnly; SameSite=Strict; Path=/");return response;})){
    try(Socket socket=new Socket("127.0.0.1",http.port())){socket.setSoTimeout(3000);socket.getOutputStream().write(("GET / HTTP/1.1\r\nHost: 127.0.0.1:"+http.port()+"\r\n\r\n").getBytes(StandardCharsets.US_ASCII));String response=new String(socket.getInputStream().readAllBytes(),StandardCharsets.US_ASCII);check(response.split("Set-Cookie:",-1).length==3,"Two separate Set-Cookie headers");}
   }
   System.out.println("PASS: persistent owner, re-pair authentication, restart/stop revocation, browser isolation, concurrent grants and two-cookie HTTP response; no printing");
  }finally{try(java.util.stream.Stream<Path> files=Files.walk(root)){files.sorted(Comparator.reverseOrder()).forEach(p->{try{Files.delete(p);}catch(IOException e){throw new UncheckedIOException(e);}});}}
 }
}
