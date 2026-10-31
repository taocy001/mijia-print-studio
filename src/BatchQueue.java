package local.liuying.studio;
import org.json.*;

/** Advances only confirmed, uninterrupted batches. Caller atomically persists before submitting. */
final class BatchQueue {
    static JSONObject next(JSONObject completed,boolean allow)throws JSONException{
        if(!allow||!"done".equals(completed.optString("phase")))return null;
        JSONArray remaining=completed.optJSONArray("remaining");if(remaining==null||remaining.length()==0)return null;
        JSONObject next=new JSONObject(remaining.getJSONObject(0).toString());
        if(!"prepared".equals(next.optString("phase"))||next.has("jobId")
            ||!completed.optString("batchId").equals(next.optString("batchId"))
            ||next.optInt("batchIndex")!=completed.optInt("batchIndex")+1
            ||next.optInt("batchCount")!=completed.optInt("batchCount"))throw new JSONException("待打印队列记录不一致，已停止后续照片");
        JSONArray rest=new JSONArray();for(int i=1;i<remaining.length();i++)rest.put(remaining.get(i));
        next.put("remaining",rest);return next;
    }
}
