package local.liuying.studio;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
public final class LocalHttpTest {
 static String request(int port,String data)throws Exception{try(Socket s=new Socket("127.0.0.1",port)){s.setSoTimeout(3000);s.getOutputStream().write(data.getBytes(StandardCharsets.US_ASCII));s.shutdownOutput();return new String(s.getInputStream().readAllBytes(),StandardCharsets.UTF_8);}}
 static void check(boolean v,String m){if(!v)throw new AssertionError(m);}
 public static void main(String[] args)throws Exception{
  try(LocalHttp h=new LocalHttp(false,0,r->LocalHttp.Response.text(200,"text/plain",r.path))){int p=h.port();String host="127.0.0.1:"+p;
   check(request(p,"GET / HTTP/1.1\r\nHost: "+host+"\r\n\r\n").startsWith("HTTP/1.1 200"),"GET");
   check(request(p,"POST /api/pair HTTP/1.1\r\nHost: "+host+"\r\nOrigin: http://"+host+"\r\nContent-Length: 6\r\n\r\n123456").startsWith("HTTP/1.1 200"),"POST");
   for(String extra:new String[]{"Host: evil.example\r\n","Host: "+host+"\r\nOrigin: http://evil.example\r\n","Host: "+host+"\r\nOrigin: http://"+host+"\r\nContent-Length: 99999999\r\n","Host: "+host+"\r\nOrigin: http://"+host+"\r\nTransfer-Encoding: chunked\r\n","Host: "+host+"\r\nHost: "+host+"\r\n"})check(request(p,"POST /api/pair HTTP/1.1\r\n"+extra+"\r\n").startsWith("HTTP/1.1 400"),extra);
   check(request(p,"GET /%2e%2e/key HTTP/1.1\r\nHost: "+host+"\r\n\r\n").startsWith("HTTP/1.1 400"),"Traversal");
  }
  try(LocalHttp h=new LocalHttp(false,0,r->LocalHttp.Response.text(200,"text/plain",r.text()),true)){int p=h.port();String head="POST /ipp/print HTTP/1.1\r\nHost: printer.local:"+p+"\r\nContent-Type: application/ipp\r\n";
   check(request(p,head+"Transfer-Encoding: chunked\r\n\r\n3\r\nabc\r\n2\r\nde\r\n0\r\n\r\n").endsWith("abcde"),"IPP chunks");
   String expect=request(p,head+"Expect: 100-continue\r\nContent-Length: 3\r\n\r\nabc");check(expect.startsWith("HTTP/1.1 100 Continue")&&expect.endsWith("abc"),"IPP continue");
   check(request(p,head+"Origin: http://printer.local\r\nContent-Length: 0\r\n\r\n").startsWith("HTTP/1.1 400"),"IPP browser rejected");
   check(request(p,head+"Transfer-Encoding: chunked\r\nContent-Length: 0\r\n\r\n").startsWith("HTTP/1.1 400"),"IPP ambiguous length rejected");
  }
  WebSessions sessions=new WebSessions();String token=sessions.pair(sessions.code);check(token!=null,"Pair");check(sessions.find("liuying="+token)!=null,"Cookie");check(sessions.find("liuying=wrong")==null,"Wrong cookie");String other=sessions.pair(sessions.code);check(!sessions.find("liuying="+token).id.equals(sessions.find("liuying="+other).id),"Session isolation");sessions.clear();check(sessions.find("liuying="+token)==null,"Revocation");for(int i=0;i<5;i++)sessions.pair("bad");check(sessions.pair(sessions.code)==null,"Pair rate limit");
  System.out.println("PASS: real HTTP requests, Host/Origin checks, request limits, traversal rejection, pairing and revocation");
 }
}
