package local.liuying.studio;
import android.content.Context;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.json.*;

final class HistoryStorage {
 private static final String NAME="prints/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\\.(jpg|oc)";
 private static final String[] STORES={"history.json","web-queue.json","job.json","failure.json"};
 private static final class Entry {
  final JSONObject value;final String group;final boolean closed;
  Entry(JSONObject value,boolean inherited){this.value=value;group=group(value);closed=Store.terminal(value)||(inherited&&value.optString("phase").equals("prepared"));}
 }
 private static String group(JSONObject j){return j.optString("owner")+"\n"+(j.optString("batchId").isEmpty()?j.optString("token"):j.optString("batchId"));}
 private static JSONObject read(Context c,String name)throws Exception{
  File f=new File(c.getFilesDir(),name);
  if(!f.exists()&&!new File(f+".bak").exists()&&!new File(f+".new").exists())return new JSONObject();
  File backup=new File(f+".bak"),source=backup.exists()?backup:f;
  if(Files.isSymbolicLink(source.toPath())||!source.isFile()||source.length()>8*1024*1024)throw new IOException("历史索引无法安全读取");
  return new JSONObject(new String(Files.readAllBytes(source.toPath()),StandardCharsets.UTF_8));
 }
 private static File file(Context c,String name)throws IOException{
  if(!name.matches(NAME))throw new IOException("历史文件名无效");
  File base=c.getFilesDir().getCanonicalFile(),root=new File(base,"prints"),f=new File(base,name);
  if(Files.isSymbolicLink(root.toPath())||Files.isSymbolicLink(f.toPath())||!root.equals(root.getCanonicalFile())||!root.equals(f.getCanonicalFile().getParentFile()))throw new IOException("历史文件路径无效");
  if(Files.exists(f.toPath(),LinkOption.NOFOLLOW_LINKS)&&!Files.isRegularFile(f.toPath(),LinkOption.NOFOLLOW_LINKS))throw new IOException("历史文件类型无效");return f;
 }
 private static List<String> paths(JSONObject j){List<String> result=new ArrayList<>();for(String key:new String[]{"file","ocFile"})if(!j.optString(key).isEmpty())result.add(j.optString(key));return result;}
 private static void collect(JSONObject j,boolean inherited,List<Entry> out,int depth)throws Exception{
  if(depth>6||out.size()>1000)throw new IOException("历史记录过多或结构无效");
  Entry entry=new Entry(j,inherited);if(j.has("token")||!paths(j).isEmpty())out.add(entry);
  if(j.has("remaining")){JSONArray a=j.getJSONArray("remaining");for(int i=0;i<a.length();i++)collect(a.getJSONObject(i),entry.closed,out,depth+1);}
 }
 private static final class Plan {
  final Map<String,JSONObject> stores=new LinkedHashMap<>();final List<Entry> entries=new ArrayList<>();
  final Set<String> groups=new HashSet<>();final Map<String,File> files=new LinkedHashMap<>();int jobs;long bytes;
 }
 private static Plan plan(Context c,String owner,JSONArray keep)throws Exception{
  if(owner==null||owner.isEmpty())throw new IOException("缺少历史记录身份");
  Set<String> protectedFiles=new HashSet<>();if(keep!=null){if(keep.length()>100)throw new IOException("编辑引用过多");for(int i=0;i<keep.length();i++){String name=keep.getString(i);if(name.startsWith("/private/"))name=name.substring(9);protectedFiles.add(name);}}
  Plan p=new Plan();for(String name:STORES){JSONObject doc=read(c,name);p.stores.put(name,doc);if(name.equals("history.json")||name.equals("web-queue.json")){if(doc.length()>0&&!doc.has("items"))throw new IOException("历史索引不完整");if(doc.has("items")){JSONArray a=doc.getJSONArray("items");for(int i=0;i<a.length();i++)collect(a.getJSONObject(i),false,p.entries,0);}}else collect(doc,false,p.entries,0);}
  JSONArray history=p.stores.get("history.json").optJSONArray("items");if(history!=null)for(int i=0;i<history.length();i++){JSONObject j=history.getJSONObject(i);if(owner.equals(j.optString("owner"))&&Store.terminal(j)&&(!j.optBoolean("filesCleared")||j.optBoolean("cleanupPending"))&&!paths(j).isEmpty())p.groups.add(group(j));}
  Set<String> blocked=new HashSet<>();Map<String,Set<String>> users=new HashMap<>();Map<String,Map<Integer,String>> indices=new HashMap<>();Map<String,Integer> counts=new HashMap<>();
  for(Entry e:p.entries){JSONObject j=e.value;if(!owner.equals(j.optString("owner"))||!e.closed||j.optString("token").isEmpty())blocked.add(e.group);
   int count=j.optInt("batchCount",1),index=j.optInt("batchIndex",1);Integer prior=counts.put(e.group,count);Map<Integer,String> slots=indices.computeIfAbsent(e.group,k->new HashMap<>());String old=slots.put(index,j.optString("token"));
   if(count<1||count>6||index<1||index>count||(prior!=null&&prior!=count)||(old!=null&&!old.equals(j.optString("token"))))blocked.add(e.group);
   for(String name:paths(j)){users.computeIfAbsent(name,k->new HashSet<>()).add(e.group);try{file(c,name);}catch(IOException error){blocked.add(e.group);}if(protectedFiles.contains(name))blocked.add(e.group);}
  }
  for(String group:p.groups)if(indices.getOrDefault(group,Collections.emptyMap()).size()!=counts.getOrDefault(group,0))blocked.add(group);
  boolean changed;do{changed=false;for(Set<String> groups:users.values()){boolean protect=false;for(String group:groups)if(!p.groups.contains(group)||blocked.contains(group))protect=true;if(protect)for(String group:groups)if(blocked.add(group))changed=true;}}while(changed);
  p.groups.removeAll(blocked);Set<String> tokens=new HashSet<>();for(Entry e:p.entries)if(p.groups.contains(e.group)){tokens.add(e.value.optString("token"));for(String name:paths(e.value))p.files.put(name,file(c,name));}
  p.jobs=tokens.size();for(File f:p.files.values())p.bytes+=f.length();return p;
 }
 private static JSONObject result(Plan p)throws Exception{return new JSONObject().put("eligibleBytes",p.bytes).put("eligibleFiles",p.files.size()).put("eligibleJobs",p.jobs).put("bytes",p.bytes).put("files",p.files.size()).put("jobs",p.jobs).put("busy",Store.busy);}
 static JSONObject summary(Context c,String owner,JSONArray keep)throws Exception{synchronized(Store.LOCK){Plan p=plan(c,owner,keep);if(Store.busy){p.files.clear();p.bytes=0;p.jobs=0;}return result(p);}}
 static JSONObject clear(Context c,String owner,JSONArray keep)throws Exception{
  synchronized(Store.LOCK){if(Store.busy)throw new IOException("请等待当前打印结束再清理");Plan p=plan(c,owner,keep);JSONObject result=result(p);
   if(p.groups.isEmpty())return result.put("deletedFiles",0).put("deletedBytes",0).put("pendingFiles",0).put("clearedPaths",new JSONArray()).put("bytes",0).put("files",0).put("pending",0);
   for(Entry e:p.entries)if(p.groups.contains(e.group))e.value.put("filesCleared",true).put("cleanupPending",true);
   // Every durable copy is marked before any file is removed. Partial saves are retryable.
   for(Map.Entry<String,JSONObject> doc:p.stores.entrySet())Store.write(c,doc.getKey(),doc.getValue());
   int deleted=0,pending=0;long bytes=0;JSONArray cleared=new JSONArray();Set<String> failed=new HashSet<>();
   for(Map.Entry<String,File> entry:p.files.entrySet())try{File f=file(c,entry.getKey());long size=f.length();if(Files.deleteIfExists(f.toPath())){deleted++;bytes+=size;}cleared.put("/private/"+entry.getKey());}catch(IOException error){pending++;failed.add(entry.getKey());}
   for(Entry e:p.entries)if(p.groups.contains(e.group)){boolean retry=false;for(Entry member:p.entries)if(member.group.equals(e.group))for(String name:paths(member.value))if(failed.contains(name))retry=true;e.value.put("cleanupPending",retry);}
   // If final bookkeeping fails, the previous pending markers still allow retry.
   for(Map.Entry<String,JSONObject> doc:p.stores.entrySet())Store.write(c,doc.getKey(),doc.getValue());
   return result.put("deletedFiles",deleted).put("deletedBytes",bytes).put("pendingFiles",pending).put("clearedPaths",cleared).put("bytes",bytes).put("files",deleted).put("pending",pending);
  }
 }
 static JSONObject publicJob(JSONObject job)throws Exception{
  JSONObject out=new JSONObject(job.toString());if(out.optBoolean("filesCleared")){for(String key:new String[]{"file","ocFile","remaining","reprintPages"})out.remove(key);out.put("canReprint",false);}return out;
 }
}
