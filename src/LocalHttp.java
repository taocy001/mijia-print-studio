package local.liuying.studio;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.*;

final class LocalHttp implements AutoCloseable {
 interface Handler { Response handle(Request request)throws Exception; }
 static final class Request {
  String method,path,host,origin,peer;Map<String,String> headers;byte[] body;
  String text(){return new String(body,StandardCharsets.UTF_8);}
 }
 static final class Response {
  int status;String type;byte[] body;Map<String,String> headers=new LinkedHashMap<>();
  Response(int s,String t,byte[] b){status=s;type=t;body=b;}
  static Response text(int s,String t,String b){return new Response(s,t,b.getBytes(StandardCharsets.UTF_8));}
 }
 private final boolean ipp;
 private final ServerSocket listener;private final Handler handler;
 private final ThreadPoolExecutor workers=new ThreadPoolExecutor(4,4,0,TimeUnit.SECONDS,new ArrayBlockingQueue<>(8));
 private final Set<Socket> sockets=ConcurrentHashMap.newKeySet();
 LocalHttp(boolean lan,int port,Handler handler)throws IOException{
  this(lan,port,handler,false);
 }
 LocalHttp(boolean lan,int port,Handler handler,boolean ipp)throws IOException{
  this.ipp=ipp;this.handler=handler;listener=new ServerSocket();listener.setReuseAddress(true);listener.bind(lan&&ipp?new InetSocketAddress(port):new InetSocketAddress(lan?"0.0.0.0":"127.0.0.1",port),8);
  Thread thread=new Thread(()->{while(!listener.isClosed())try{Socket s=listener.accept();s.setSoTimeout(15000);sockets.add(s);try{workers.execute(()->serve(s));}catch(RejectedExecutionException e){sockets.remove(s);s.close();}}catch(IOException e){if(!listener.isClosed())close();}},"liuying-http");thread.setDaemon(true);thread.start();
 }
 int port(){return listener.getLocalPort();}
 private static String line(InputStream in,int max)throws IOException{
  ByteArrayOutputStream out=new ByteArrayOutputStream();int v;while((v=in.read())!=-1){if(v=='\n'){byte[] b=out.toByteArray();if(b.length==0||b[b.length-1]!='\r')throw new IOException("Malformed headers");return new String(b,0,b.length-1,StandardCharsets.US_ASCII);}if(out.size()>=max)throw new IOException("Header too large");out.write(v);}throw new EOFException();
 }
 private Request read(Socket s)throws Exception{
  InputStream in=new BufferedInputStream(s.getInputStream());String[] first=line(in,2048).split(" ");if(first.length!=3||!first[2].equals("HTTP/1.1"))throw new IOException();
  Request r=new Request();r.peer=s.getInetAddress().getHostAddress();if(ipp&&!s.getInetAddress().isLoopbackAddress()&&!s.getInetAddress().isSiteLocalAddress()&&!s.getInetAddress().isLinkLocalAddress()&&!(s.getInetAddress() instanceof Inet6Address&&(s.getInetAddress().getAddress()[0]&0xfe)==0xfc))throw new IOException("Local network required");r.method=first[0];if(!r.method.equals("GET")&&!r.method.equals("POST"))throw new IOException();
  if(!first[1].startsWith("/")||first[1].startsWith("//"))throw new IOException();
  r.path=first[1].split("\\?",2)[0];if(r.path.contains("%")||r.path.contains("..")||r.path.contains("\\"))throw new IOException();
  r.headers=new HashMap<>();int size=0;for(int i=0;;i++){String h=line(in,8192);size+=h.length();if(size>16384||i>60)throw new IOException();if(h.isEmpty())break;int colon=h.indexOf(':');if(colon<1)throw new IOException();String k=h.substring(0,colon).toLowerCase(Locale.ROOT),v=h.substring(colon+1).trim();if(r.headers.put(k,v)!=null)throw new IOException();}
  r.host=r.headers.get("host");r.origin=r.headers.get("origin");String expected=s.getLocalAddress().getHostAddress()+":"+port();
  if(ipp){if(!r.path.equals("/ipp/print")||r.origin!=null||!"application/ipp".equalsIgnoreCase(r.headers.get("content-type")))throw new IOException("IPP required");if(r.host==null||!r.host.matches("(?:[A-Za-z0-9.\\-]+|\\[[0-9A-Fa-f:%]+\\])(?::[0-9]+)?"))throw new IOException("Invalid host");}
  if(!ipp&&!expected.equals(r.host)&&!(s.getLocalAddress().isLoopbackAddress()&&("localhost:"+port()).equals(r.host)))throw new IOException("Invalid host");
  if(!ipp&&r.method.equals("POST")&&!Objects.equals(r.origin,"http://"+r.host))throw new IOException("Invalid origin");
  if(!ipp&&(r.headers.containsKey("transfer-encoding")||r.headers.containsKey("expect")))throw new IOException();
  int max=ipp?32*1024*1024:r.path.equals("/api/upload")?25*1024*1024:r.path.equals("/api/print")?18000000:4096;
  String transfer=r.headers.get("transfer-encoding");if(transfer!=null&&(!ipp||!transfer.equalsIgnoreCase("chunked")||r.headers.containsKey("content-length")))throw new IOException("Invalid transfer encoding");
  int len=Integer.parseInt(r.headers.getOrDefault("content-length","0"));if(len<0||len>max||r.method.equals("GET")&&len!=0)throw new IOException("Body too large");
  if(r.headers.containsKey("expect")){if(!"100-continue".equalsIgnoreCase(r.headers.get("expect")))throw new IOException();s.getOutputStream().write("HTTP/1.1 100 Continue\r\n\r\n".getBytes(StandardCharsets.US_ASCII));s.getOutputStream().flush();}
  if(transfer!=null){ByteArrayOutputStream body=new ByteArrayOutputStream();while(true){int n=Integer.parseInt(line(in,64).split(";",2)[0],16);if(n<0||n>max-body.size())throw new IOException("Body too large");if(n==0){if(!line(in,2).isEmpty())throw new IOException();break;}byte[] chunk=new byte[n];new DataInputStream(in).readFully(chunk);body.write(chunk);if(!line(in,2).isEmpty())throw new IOException();}r.body=body.toByteArray();}
  else{r.body=new byte[len];new DataInputStream(in).readFully(r.body);}return r;
 }
 private void serve(Socket socket){
  try(Socket s=socket){Response response;try{response=handler.handle(read(s));}catch(Exception e){response=Response.text(400,"text/plain; charset=utf-8","请求无效");}
   OutputStream out=s.getOutputStream();StringBuilder h=new StringBuilder("HTTP/1.1 "+response.status+" "+(response.status==200?"OK":response.status==303?"See Other":"Error")+"\r\nContent-Type: "+response.type+"\r\nContent-Length: "+response.body.length+"\r\nConnection: close\r\nCache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\nReferrer-Policy: same-origin\r\nX-Frame-Options: DENY\r\nContent-Security-Policy: default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; form-action 'self'; object-src 'none'\r\n");
   for(Map.Entry<String,String> e:response.headers.entrySet())h.append(e.getKey()).append(": ").append(e.getValue()).append("\r\n");out.write(h.append("\r\n").toString().getBytes(StandardCharsets.US_ASCII));out.write(response.body);out.flush();
  }catch(IOException ignored){}finally{sockets.remove(socket);}
 }
 public void close(){try{listener.close();}catch(IOException ignored){}workers.shutdownNow();for(Socket s:sockets)try{s.close();}catch(IOException ignored){}sockets.clear();}
}
