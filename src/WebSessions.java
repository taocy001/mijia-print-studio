package local.liuying.studio;
import java.security.*;
import java.util.*;
final class WebSessions {
 static final class Session {final String id=UUID.randomUUID().toString();final Set<String> files=new HashSet<>();long bytes;}
 private final Map<String,Session> sessions=new HashMap<>();
 final String code=String.format(Locale.ROOT,"%06d",new SecureRandom().nextInt(1000000));
 private int failures;private long blockedUntil;
 synchronized String pair(String input){
  if(System.currentTimeMillis()<blockedUntil||sessions.size()>=12)return null;
  if(!MessageDigest.isEqual(code.getBytes(java.nio.charset.StandardCharsets.US_ASCII),input.getBytes(java.nio.charset.StandardCharsets.US_ASCII))){if(++failures>=5){blockedUntil=System.currentTimeMillis()+60000;failures=0;}return null;}
  failures=0;String token=UUID.randomUUID().toString()+UUID.randomUUID();sessions.put(token,new Session());return token;
 }
 synchronized Session find(String cookie){if(cookie==null)return null;for(String part:cookie.split(";")){String p=part.trim();if(p.startsWith("liuying="))return sessions.get(p.substring(8));}return null;}
 synchronized void clear(){sessions.clear();}
}
