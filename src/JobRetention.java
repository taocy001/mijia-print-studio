package local.liuying.studio;
import java.util.*;
import org.json.*;
final class JobRetention {
 static final long RECENT_MS=24L*60*60*1000;
 static JSONArray compact(JSONArray rows,Set<String> protectedOwners,long now)throws JSONException{
  List<JSONObject> terminal=new ArrayList<>();for(int i=0;i<rows.length();i++){JSONObject row=rows.getJSONObject(i);if(Store.terminal(row))terminal.add(row);}
  terminal.sort((a,b)->Long.compare(time(b,now),time(a,now)));Set<JSONObject> keep=Collections.newSetFromMap(new IdentityHashMap<JSONObject,Boolean>());for(int i=0;i<Math.min(64,terminal.size());i++)keep.add(terminal.get(i));
  JSONArray result=new JSONArray();for(int i=0;i<rows.length();i++){JSONObject row=rows.getJSONObject(i);if(!Store.terminal(row)||keep.contains(row)||protectedOwners.contains(row.optString("owner"))||now-time(row,now)<RECENT_MS)result.put(row);}return result;
 }
 static long time(JSONObject row,long fallback){long value=Math.max(Math.max(row.optLong("completedAt"),row.optLong("updatedAt")),Math.max(row.optLong("createdAt"),row.optLong("created")));return value>0?value:fallback;}
 static int pending(JSONArray rows){int count=0;for(int i=0;i<rows.length();i++){JSONObject row=rows.optJSONObject(i);if(row==null||!Store.terminal(row))count++;}return count;}
}
