package local.liuying.studio;
import org.json.*;
public final class BatchQueueTest {
 static int count;
 static void check(boolean v,String label){if(!v)throw new AssertionError(label);count++;}
 static JSONObject job(int i)throws Exception{return new JSONObject().put("token","page-"+i).put("batchId","batch").put("batchIndex",i).put("batchCount",6).put("phase","prepared");}
 public static void main(String[] args)throws Exception{
  JSONObject first=job(1);JSONArray pending=new JSONArray();for(int i=2;i<=6;i++)pending.put(job(i));first.put("remaining",pending);
  for(String phase:new String[]{"prepared","creating","uploading","printing","uncertain","held","cancelled","aborted","rejected"}){first.put("phase",phase);check(BatchQueue.next(first,true)==null,"Never advance "+phase);}
  first.put("phase","done");check(BatchQueue.next(first,false)==null,"Cancel or recovery cannot advance");
  JSONObject current=first;
  for(int i=2;i<=6;i++){current.put("phase","done").put("jobId",100+i);JSONObject next=BatchQueue.next(current,true);check(next.getInt("batchIndex")==i&&next.getString("token").equals("page-"+i)&&!next.has("jobId"),"Next page has distinct identity");check(next.getJSONArray("remaining").length()==6-i,"Queue shrinks once");check(BatchQueue.next(next,true)==null,"Prepared page cannot be skipped");current=next;}
  current.put("phase","done");check(BatchQueue.next(current,true)==null,"Batch ends exactly at six");
  JSONObject bad=job(2).put("jobId",99);first.put("remaining",new JSONArray().put(bad));boolean rejected=false;try{BatchQueue.next(first,true);}catch(JSONException e){rejected=true;}check(rejected,"Submitted page cannot replay");
  System.out.println("Batch queue checks passed: "+count);
 }
}
