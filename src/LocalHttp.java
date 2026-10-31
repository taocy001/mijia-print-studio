package local.liuying.studio;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.*;

final class LocalHttp implements AutoCloseable {
 interface Handler {
  Response handle(Request request)throws Exception;
  default void receiveFailure(Request partial,Exception error){}
 }
 static final class Request {
  String method,path,host,origin,peer;Map<String,String> headers=new HashMap<>();byte[] body=new byte[0];
  boolean ippValidated;
  String text(){return new String(body,StandardCharsets.UTF_8);}
 }
 static final class Response {
  int status;String type;byte[] body;Map<String,String> headers=new LinkedHashMap<>();List<String> cookies=new ArrayList<>();
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
 private void read(Socket s,Request r)throws Exception{
  r.peer=s.getInetAddress().getHostAddress();
  if(ipp&&!s.getInetAddress().isLoopbackAddress()&&!s.getInetAddress().isSiteLocalAddress()&&!s.getInetAddress().isLinkLocalAddress()&&!(s.getInetAddress() instanceof Inet6Address&&(s.getInetAddress().getAddress()[0]&0xfe)==0xfc))throw new IOException("Local network required");
  InputStream in=new BufferedInputStream(s.getInputStream());String[] first=line(in,2048).split(" ");
  if(first.length!=3)throw new IOException("Invalid request line");
  boolean legacy=ipp&&first[2].equals("HTTP/1.0");if(!first[2].equals("HTTP/1.1")&&!legacy)throw new IOException("Unsupported HTTP version");
  r.method=first[0];if(!r.method.equals("GET")&&!r.method.equals("POST"))throw new IOException("Unsupported HTTP method");
  if(!first[1].startsWith("/")||first[1].startsWith("//"))throw new IOException("Invalid request target");
  r.path=first[1].split("\\?",2)[0];if(r.path.contains("%")||r.path.contains("..")||r.path.contains("\\"))throw new IOException("Invalid request target");
  int size=0;for(int i=0;;i++){String h=line(in,8192);size+=h.length();if(size>16384||i>60)throw new IOException("Headers too large");if(h.isEmpty())break;int colon=h.indexOf(':');if(colon<1)throw new IOException("Malformed headers");String k=h.substring(0,colon).toLowerCase(Locale.ROOT),v=h.substring(colon+1).trim();if(!k.matches("[!#$%&'*+.^_`|~0-9a-z-]+"))throw new IOException("Invalid header name");if(r.headers.put(k,v)!=null)throw new IOException("Duplicate header");}
  r.host=r.headers.get("host");r.origin=r.headers.get("origin");String expected=s.getLocalAddress().getHostAddress()+":"+port();
  if(ipp){if(!r.method.equals("POST")||!r.path.equals("/ipp/print")||r.origin!=null||!"application/ipp".equalsIgnoreCase(r.headers.get("content-type")))throw new IOException("IPP required");if(r.host==null||!r.host.matches("(?:[A-Za-z0-9.\\-]+|\\[[0-9A-Fa-f:%]+\\])(?::[0-9]+)?"))throw new IOException("Invalid host");r.ippValidated=true;}
  if(!ipp&&!expected.equals(r.host)&&!(s.getLocalAddress().isLoopbackAddress()&&("localhost:"+port()).equals(r.host)))throw new IOException("Invalid host");
  if(!ipp&&r.method.equals("POST")&&!Objects.equals(r.origin,"http://"+r.host))throw new IOException("Invalid origin");
  if((!ipp||legacy)&&(r.headers.containsKey("transfer-encoding")||r.headers.containsKey("expect")))throw new IOException("Unsupported transfer option");
  int max=ipp?32*1024*1024:r.path.equals("/api/upload")?25*1024*1024:r.path.equals("/api/print")?18000000:4096;
  String transfer=r.headers.get("transfer-encoding");if(transfer!=null&&(!ipp||!transfer.equalsIgnoreCase("chunked")||r.headers.containsKey("content-length")))throw new IOException("Invalid transfer encoding");
  String length=r.headers.getOrDefault("content-length","0");if(!length.matches("[0-9]{1,10}"))throw new IOException("Invalid content length");long declared=Long.parseLong(length);if(declared>max||r.method.equals("GET")&&declared!=0)throw new IOException("Body too large");int len=(int)declared;
  if(r.headers.containsKey("expect")){if(!"100-continue".equalsIgnoreCase(r.headers.get("expect")))throw new IOException("Unsupported expectation");s.getOutputStream().write("HTTP/1.1 100 Continue\r\n\r\n".getBytes(StandardCharsets.US_ASCII));s.getOutputStream().flush();}
  ByteArrayOutputStream body=new ByteArrayOutputStream();
  try{
   if(transfer!=null){while(true){String value=line(in,64).split(";",2)[0];if(!value.matches("[0-9a-fA-F]{1,8}"))throw new IOException("Invalid chunk size");long count=Long.parseLong(value,16);if(count>max-body.size())throw new IOException("Body too large");int n=(int)count;if(n==0){if(!line(in,2).isEmpty())throw new IOException("Unsupported chunk trailers");break;}copy(in,body,n);if(!line(in,2).isEmpty())throw new IOException("Malformed chunk delimiter");}}
   else copy(in,body,len);
  }finally{r.body=body.toByteArray();}
 }
 private static void copy(InputStream in,ByteArrayOutputStream out,int count)throws IOException{
  byte[] buffer=new byte[Math.min(8192,Math.max(1,count))];while(count>0){int read=in.read(buffer,0,Math.min(buffer.length,count));if(read<0)throw new EOFException("Incomplete request body");out.write(buffer,0,read);count-=read;}
 }
 private void serve(Socket socket){
  try(Socket s=socket){Response response;Request request=new Request();boolean received=false;try{read(s,request);received=true;response=handler.handle(request);}catch(Exception e){
    if(!received&&request.ippValidated&&!listener.isClosed())try{handler.receiveFailure(request,e);}catch(Exception ignored){}
    response=Response.text(400,"text/plain; charset=utf-8","请求无效");
   }
   OutputStream out=s.getOutputStream();StringBuilder h=new StringBuilder("HTTP/1.1 "+response.status+" "+(response.status==200?"OK":response.status==303?"See Other":"Error")+"\r\nContent-Type: "+response.type+"\r\nContent-Length: "+response.body.length+"\r\nConnection: close\r\nCache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\nReferrer-Policy: same-origin\r\nX-Frame-Options: DENY\r\nContent-Security-Policy: default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; form-action 'self'; object-src 'none'\r\n");
   for(Map.Entry<String,String> e:response.headers.entrySet())h.append(e.getKey()).append(": ").append(e.getValue()).append("\r\n");for(String cookie:response.cookies)h.append("Set-Cookie: ").append(cookie).append("\r\n");out.write(h.append("\r\n").toString().getBytes(StandardCharsets.US_ASCII));out.write(response.body);out.flush();
  }catch(IOException ignored){}finally{sockets.remove(socket);}
 }
 public void close(){try{listener.close();}catch(IOException ignored){}workers.shutdownNow();for(Socket s:sockets)try{s.close();}catch(IOException ignored){}sockets.clear();}
}
