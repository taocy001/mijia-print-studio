package local.liuying.studio;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.*;
import java.util.*;
final class WebSessions {
 static final long COOKIE_MAX_AGE=31536000L;
 private static final int MAX_SESSIONS=12;
 static final class Session {
  final String id,ownerKey;final Set<String> files=new HashSet<>();long bytes;int uploads;
  Session(String id,String key,Collection<String> saved){this.id=id;ownerKey=key;files.addAll(saved);}
 }
 static final class Pair {final String token,owner;Pair(String token,String owner){this.token=token;this.owner=owner;}}
 private final Map<String,Session> sessions=new HashMap<>();private final Properties owners=new Properties(),pairings=new Properties();private final File file,pairingFile;
 volatile String code=newCode();
 private int failures;private long blockedUntil;
 WebSessions(){file=pairingFile=null;}
 WebSessions(File directory)throws IOException{
  file=new File(directory,"web-owners.properties");pairingFile=new File(directory,"web-pairings.properties");
  if(file.isFile())try(InputStream input=new FileInputStream(file)){owners.load(input);}
  if(pairingFile.isFile())try(InputStream input=new FileInputStream(pairingFile)){pairings.load(input);}
 }
 private static String newCode(){return String.format(Locale.ROOT,"%06d",new SecureRandom().nextInt(1000000));}
 private static String random(){byte[] bytes=new byte[48];new SecureRandom().nextBytes(bytes);return Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);}
 private static String hash(String value){try{byte[] bytes=MessageDigest.getInstance("SHA-256").digest(value.getBytes(StandardCharsets.US_ASCII));StringBuilder out=new StringBuilder();for(byte b:bytes)out.append(String.format(Locale.ROOT,"%02x",b&255));return out.toString();}catch(NoSuchAlgorithmException e){throw new AssertionError(e);}}
 private static String cookie(String header,String name){if(header!=null)for(String part:header.split(";")){String p=part.trim();if(p.startsWith(name+"="))return p.substring(name.length()+1);}return "";}
 private static String authorizedOwner(String value,long now){
  if(value==null)return null;String[] parts=value.split(" ");if(parts.length!=2||!parts[0].matches("[a-f0-9]{64}"))return null;
  try{return Long.parseLong(parts[1])>now?parts[0]:null;}catch(NumberFormatException e){return null;}
 }
 private Properties validPairings(){Properties valid=new Properties();long now=System.currentTimeMillis();for(String key:pairings.stringPropertyNames())if(key.matches("[a-f0-9]{64}")&&authorizedOwner(pairings.getProperty(key),now)!=null)valid.setProperty(key,pairings.getProperty(key));return valid;}
 private static void write(File destination,Properties data)throws IOException{
  if(destination==null)return;Path temporary=Files.createTempFile(destination.getParentFile().toPath(),".web-sessions-",".tmp");
  try{try(FileOutputStream output=new FileOutputStream(temporary.toFile())){data.store(output,null);output.getFD().sync();}
   try{Files.move(temporary,destination.toPath(),StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);}catch(AtomicMoveNotSupportedException e){Files.move(temporary,destination.toPath(),StandardCopyOption.REPLACE_EXISTING);}
  }finally{Files.deleteIfExists(temporary);}
 }
 private void savePairings(Properties next)throws IOException{Set<String> removed=new HashSet<>(pairings.stringPropertyNames());removed.removeAll(next.stringPropertyNames());write(pairingFile,next);pairings.clear();pairings.putAll(next);sessions.entrySet().removeIf(entry->removed.contains(hash(entry.getKey())));}
 private Session restore(String key){String id=owners.getProperty("id."+key);if(id==null)return null;Set<String> files=new HashSet<>();for(String path:owners.getProperty("files."+key,"").split("\n"))if(!path.isEmpty())files.add(path);return new Session(id,key,files);}
 synchronized String pair(String input)throws IOException{Pair pair=pair(input,null);return pair==null?null:pair.token;}
 synchronized Pair pair(String input,String cookies)throws IOException{
  if(System.currentTimeMillis()<blockedUntil)return null;
  if(input==null||!MessageDigest.isEqual(code.getBytes(StandardCharsets.US_ASCII),input.getBytes(StandardCharsets.US_ASCII))){if(++failures>=5){blockedUntil=System.currentTimeMillis()+60000;failures=0;}return null;}
  failures=0;String owner=cookie(cookies,"liuying-owner");if(!owner.matches("[A-Za-z0-9_-]{64}"))owner=random();String key=hash(owner);
  Properties next=validPairings();next.entrySet().removeIf(entry->key.equals(authorizedOwner((String)entry.getValue(),System.currentTimeMillis())));if(next.size()>=MAX_SESSIONS)return null;
  Session session=restore(key);if(session==null)session=new Session(UUID.randomUUID().toString(),key,Collections.emptySet());
  // Re-pairing does not reset a browser's current upload quota.
  for(Session active:sessions.values())if(active.ownerKey.equals(key)){session=active;break;}
  remember(session);String token=random();next.setProperty(hash(token),key+" "+(System.currentTimeMillis()+COOKIE_MAX_AGE*1000));savePairings(next);sessions.put(token,session);return new Pair(token,owner);
 }
 synchronized void remember(Session session)throws IOException{
  Properties next=new Properties();next.putAll(owners);next.setProperty("id."+session.ownerKey,session.id);Set<String> files=new TreeSet<>();for(String path:owners.getProperty("files."+session.ownerKey,"").split("\n"))if(!path.isEmpty())files.add(path);
  synchronized(session){files.addAll(session.files);}next.setProperty("files."+session.ownerKey,String.join("\n",files));write(file,next);owners.clear();owners.putAll(next);
  synchronized(session){session.files.addAll(files);}for(Session active:sessions.values())if(active.ownerKey.equals(session.ownerKey))synchronized(active){active.files.addAll(files);}
 }
 synchronized Session find(String cookies)throws IOException{
  String token=cookie(cookies,"liuying");if(!token.matches("[A-Za-z0-9_-]{64}"))return null;String key=hash(token),stored=pairings.getProperty(key);Session session=sessions.get(token);
  if(stored==null&&session!=null){Properties next=validPairings();if(next.size()>=MAX_SESSIONS)return null;next.setProperty(key,session.ownerKey+" "+(System.currentTimeMillis()+COOKIE_MAX_AGE*1000));savePairings(next);}
  String owner=authorizedOwner(pairings.getProperty(key),System.currentTimeMillis());if(owner==null){sessions.remove(token);return null;}
  if(session==null){session=restore(owner);if(session==null)return null;sessions.put(token,session);}
  return session;
 }
 synchronized String persistentCookie(String cookies){String token=cookie(cookies,"liuying");if(!token.matches("[A-Za-z0-9_-]{64}"))return null;String stored=pairings.getProperty(hash(token));long now=System.currentTimeMillis();if(authorizedOwner(stored,now)==null)return null;long seconds=(Long.parseLong(stored.split(" ")[1])-now)/1000;return "liuying="+token+"; Max-Age="+seconds+"; HttpOnly; SameSite=Lax; Path=/";}
 synchronized void clear(){sessions.clear();}
 synchronized void revokeAll()throws IOException{savePairings(new Properties());sessions.clear();String previous=code;do{code=newCode();}while(code.equals(previous));failures=0;blockedUntil=0;}
}
