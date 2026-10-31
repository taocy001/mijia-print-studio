package local.liuying.studio;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.*;
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
  BlockingQueue<LocalHttp.Request> failures=new LinkedBlockingQueue<>();BlockingQueue<Exception> errors=new LinkedBlockingQueue<>();
  LocalHttp.Handler handler=new LocalHttp.Handler(){public LocalHttp.Response handle(LocalHttp.Request r){return LocalHttp.Response.text(200,"text/plain",r.text());}public void receiveFailure(LocalHttp.Request r,Exception e){failures.add(r);errors.add(e);}};
  try(LocalHttp h=new LocalHttp(false,0,handler,true)){int p=h.port();String head="POST /ipp/print HTTP/1.1\r\nHost: printer.local:"+p+"\r\nContent-Type: application/ipp\r\n";
   check(request(p,head+"Transfer-Encoding: chunked\r\n\r\n3;ext=value\r\nabc\r\n2\r\nde\r\n0\r\n\r\n").endsWith("abcde"),"IPP chunks");
   try(Socket socket=new Socket("127.0.0.1",p)){socket.setSoTimeout(3000);socket.getOutputStream().write((head+"Expect: 100-continue\r\nContent-Length: 3\r\n\r\n").getBytes(StandardCharsets.US_ASCII));byte[] reply=socket.getInputStream().readNBytes(25);check(new String(reply,StandardCharsets.US_ASCII).equals("HTTP/1.1 100 Continue\r\n\r\n"),"Continue before sending body");socket.getOutputStream().write("abc".getBytes(StandardCharsets.US_ASCII));check(new String(socket.getInputStream().readAllBytes(),StandardCharsets.UTF_8).endsWith("abc"),"Continue completed");}
   check(request(p,head.replace("HTTP/1.1","HTTP/1.0")+"Content-Length: 3\r\n\r\nabc").endsWith("abc"),"IPP HTTP 1.0 framed request");
   for(String value:new String[]{head+"Origin: http://printer.local\r\nContent-Length: 0\r\n\r\n",head.replace("application/ipp","text/plain")+"\r\n",head.replace("POST /ipp/print","GET /ipp/print")+"\r\n",head.replace("/ipp/print","/random")+"\r\n","garbage\r\n\r\n"})check(request(p,value).startsWith("HTTP/1.1 400"),"Non-IPP request rejected");
   check(failures.isEmpty(),"Random requests are not print failures");
   check(request(p,head+"Content-Length: 8\r\n\r\nabc").startsWith("HTTP/1.1 400"),"Truncated length rejected");LocalHttp.Request partial=failures.poll(2,TimeUnit.SECONDS);check(partial!=null&&partial.text().equals("abc")&&partial.path.equals("/ipp/print")&&partial.method.equals("POST"),"Partial body retained");check(errors.poll() instanceof EOFException,"Truncation cause retained");
   check(request(p,head+"Transfer-Encoding: chunked\r\n\r\n3\r\nabc\r\n4\r\nde").startsWith("HTTP/1.1 400"),"Truncated chunk rejected");check(failures.poll(2,TimeUnit.SECONDS).text().equals("abcde"),"Partial chunks retained");check(errors.poll() instanceof EOFException,"Chunk truncation cause");
   for(String extra:new String[]{"Transfer-Encoding: chunked\r\nContent-Length: 0\r\n\r\n","Content-Length: 9999999999\r\n\r\n","Content-Length: private-value\r\n\r\n","Expect: private-value\r\n\r\n","Transfer-Encoding: chunked\r\n\r\nprivate-value\r\n"}){check(request(p,head+extra).startsWith("HTTP/1.1 400"),"Invalid framing rejected");check(failures.poll(2,TimeUnit.SECONDS)!=null,"Framing failure reported");Exception error=errors.poll();check(error!=null&&!String.valueOf(error.getMessage()).contains("private-value"),"Diagnostic excludes raw input");}
   try(Socket socket=new Socket("127.0.0.1",p)){socket.setSoTimeout(20000);socket.getOutputStream().write((head+"Content-Length: 4\r\n\r\nab").getBytes(StandardCharsets.US_ASCII));check(new String(socket.getInputStream().readAllBytes(),StandardCharsets.UTF_8).startsWith("HTTP/1.1 400"),"Read timeout response");check(failures.poll(2,TimeUnit.SECONDS).text().equals("ab"),"Timeout retains partial body");check(errors.poll() instanceof SocketTimeoutException,"Read timeout reported");}
   check(failures.isEmpty()&&errors.isEmpty(),"One callback per failure");
  }
  WebSessions sessions=new WebSessions();String token=sessions.pair(sessions.code);check(token!=null,"Pair");check(sessions.find("liuying="+token)!=null,"Cookie");check(sessions.find("liuying=wrong")==null,"Wrong cookie");String other=sessions.pair(sessions.code);check(!sessions.find("liuying="+token).id.equals(sessions.find("liuying="+other).id),"Session isolation");sessions.clear();check(sessions.find("liuying="+token)==null,"Revocation");for(int i=0;i<5;i++)sessions.pair("bad");check(sessions.pair(sessions.code)==null,"Pair rate limit");
  System.out.println("PASS: HTTP/IPP framing, Expect handshake, partial-body diagnostics, timeout, HTTP 1.0 compatibility, request isolation, pairing and revocation");
 }
}
