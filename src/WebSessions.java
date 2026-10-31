package local.liuying.studio;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.*;
import java.util.*;
final class WebSessions {
 static final class Session {
  final String id,ownerKey;final Set<String> files=new HashSet<>();long bytes;int uploads;
  Session(String id,String key,Collection<String> saved){this.id=id;ownerKey=key;files.addAll(saved);}
 }
 static final class Pair {final String token,owner;Pair(String token,String owner){this.token=token;this.owner=owner;}}
 private final Map<String,Session> sessions=new HashMap<>();private final Properties owners=new Properties();private final File file;
 final String code=String.format(Locale.ROOT,"%06d",new SecureRandom().nextInt(1000000));
 private int failures;private long blockedUntil;
 WebSessions(){file=null;}
 WebSessions(File directory)throws IOException{
  file=new File(directory,"web-owners.properties");if(file.isFile())try(InputStream input=new FileInputStream(file)){owners.load(input);}
 }
 private static String random(){byte[] bytes=new byte[48];new SecureRandom().nextBytes(bytes);return Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);}
 private static String hash(String value){try{byte[] bytes=MessageDigest.getInstance("SHA-256").digest(value.getBytes(StandardCharsets.US_ASCII));StringBuilder out=new StringBuilder();for(byte b:bytes)out.append(String.format(Locale.ROOT,"%02x",b&255));return out.toString();}catch(NoSuchAlgorithmException e){throw new AssertionError(e);}}
 private static String cookie(String header,String name){if(header!=null)for(String part:header.split(";")){String p=part.trim();if(p.startsWith(name+"="))return p.substring(name.length()+1);}return "";}
 synchronized String pair(String input)throws IOException{Pair pair=pair(input,null);return pair==null?null:pair.token;}
 synchronized Pair pair(String input,String cookies)throws IOException{
  if(System.currentTimeMillis()<blockedUntil||sessions.size()>=12)return null;
  if(!MessageDigest.isEqual(code.getBytes(StandardCharsets.US_ASCII),input.getBytes(StandardCharsets.US_ASCII))){if(++failures>=5){blockedUntil=System.currentTimeMillis()+60000;failures=0;}return null;}
  failures=0;String owner=cookie(cookies,"liuying-owner");if(!owner.matches("[A-Za-z0-9_-]{64}"))owner=random();String key=hash(owner);
  String id=owners.getProperty("id."+key);if(id==null)id=UUID.randomUUID().toString();
  Set<String> files=new HashSet<>();for(String path:owners.getProperty("files."+key,"").split("\n"))if(!path.isEmpty())files.add(path);
  Session session=new Session(id,key,files);remember(session);String token=random();sessions.put(token,session);return new Pair(token,owner);
 }
 synchronized void remember(Session session)throws IOException{
  owners.setProperty("id."+session.ownerKey,session.id);Set<String> files=new TreeSet<>();for(String path:owners.getProperty("files."+session.ownerKey,"").split("\n"))if(!path.isEmpty())files.add(path);
  synchronized(session){files.addAll(session.files);session.files.addAll(files);}owners.setProperty("files."+session.ownerKey,String.join("\n",files));
  for(Session active:sessions.values())if(active.ownerKey.equals(session.ownerKey))synchronized(active){active.files.addAll(files);}
  if(file==null)return;
  Path temporary=Files.createTempFile(file.getParentFile().toPath(),".web-owners-",".tmp");
  try{try(FileOutputStream output=new FileOutputStream(temporary.toFile())){owners.store(output,null);output.getFD().sync();}
   try{Files.move(temporary,file.toPath(),StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);}catch(AtomicMoveNotSupportedException e){Files.move(temporary,file.toPath(),StandardCopyOption.REPLACE_EXISTING);}
  }finally{Files.deleteIfExists(temporary);}
 }
 synchronized Session find(String cookies){return sessions.get(cookie(cookies,"liuying"));}
 synchronized void clear(){sessions.clear();}
}
