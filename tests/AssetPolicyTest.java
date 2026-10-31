package local.liuying.studio;
import java.nio.file.*;
public class AssetPolicyTest {
 public static void main(String[] args)throws Exception{
  Path assets=Paths.get(args[0]);String html=new String(Files.readAllBytes(assets.resolve("index.html")),"UTF-8");
  java.util.regex.Matcher scripts=java.util.regex.Pattern.compile("<script src=\"([^\"]+)\"").matcher(html);
  while(scripts.find())check(assets,scripts.group(1));
  for(String dir:new String[]{"emoji"})try(java.util.stream.Stream<Path> files=Files.list(assets.resolve(dir))){files.forEach(p->{try{check(assets,dir+"/"+p.getFileName());}catch(Exception e){throw new RuntimeException(e);}});}
  for(String path:new String[]{"templates/old.png","name-labels/old.png","card-art/old.jpg","../app.js","card-art/../../private.jpg","unknown.js","name-labels/x.html"})if(AssetPolicy.allows(path))throw new AssertionError(path);
  System.out.println("Native asset policy: all entry scripts and creative images accepted; invalid paths rejected");
 }
 static void check(Path root,String name)throws Exception{if(!AssetPolicy.allows(name)||!Files.isRegularFile(root.resolve(name)))throw new AssertionError(name);}
}
