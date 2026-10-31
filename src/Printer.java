package local.liuying.studio;
import android.bluetooth.*;
import android.content.Context;
import java.io.*;
import java.nio.*;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.util.UUID;
import java.util.concurrent.*;
import org.json.*;

final class Printer implements AutoCloseable {
    private String address;
    private BluetoothSocket socket;
    private byte[] key;
    private int sequence=4;
    private final ScheduledExecutorService timer=Executors.newSingleThreadScheduledExecutor();
    Printer(Context context)throws Exception{
        ScheduledFuture<?> deadline=timer.schedule(this::closeSocket,18,TimeUnit.SECONDS);
        try{
            BluetoothAdapter a=context.getSystemService(BluetoothManager.class).getAdapter();
            if(a==null||!a.isEnabled())throw new IOException("请先开启手机蓝牙");
            BluetoothDevice d=null;
            for(BluetoothDevice paired:a.getBondedDevices()){
                String name=paired.getName();
                if(name!=null&&(name.startsWith("米家桌面照片")||name.startsWith("Xiaomi Photo Printer 2"))){
                    if(d!=null)throw new IOException("检测到多台照片打印机，请在系统蓝牙中仅保留要使用的一台配对");
                    d=paired;
                }
            }
            if(d==null)throw new IOException("请先在系统蓝牙中配对米家桌面照片打印机 2");
            address=d.getAddress();
            a.cancelDiscovery();socket=d.createRfcommSocketToServiceRecord(UUID.fromString("00001101-0000-1000-8000-00805f9b34fb"));
            socket.connect();send(Wire.frame(255,16,3,2,0,0,"hello".getBytes(StandardCharsets.US_ASCII)));
            Wire.Confirm auth=Wire.confirm(receive(255,17).body,3,new SecureRandom());
            key=auth.key;send(auth.packet);
            if(!Wire.text(receive(255,19).body).equalsIgnoreCase("ok"))throw new IOException("打印机握手失败");
        }catch(Exception e){close();throw e;}finally{deadline.cancel(false);}
    }
    private void send(byte[] bytes)throws IOException{socket.getOutputStream().write(bytes);socket.getOutputStream().flush();}
    private Wire.Frame receive(int channel,int op)throws Exception{
        while(true){Wire.Frame frame=Wire.read(socket.getInputStream());if(frame.channel==channel&&frame.op==op)return frame;}
    }
    JSONObject rpc(String method,Object params)throws Exception{
        ScheduledFuture<?> deadline=timer.schedule(this::closeSocket,15,TimeUnit.SECONDS);
        try{
            int id=sequence++;
            JSONObject request=new JSONObject().put("id",id).put("method",method).put("params",params);
            if(method.equals("get-job-info"))request.put("isNewSpec",1);
            send(Wire.frame(3,6,3,id,0,0,Wire.crypt(key,request.toString().getBytes(StandardCharsets.UTF_8),true)));
            while(true){Wire.Frame frame=receive(3,7);if(frame.total>1)throw new IOException("打印机返回了暂不支持的分段状态");
                JSONObject result=new JSONObject(Wire.text(Wire.crypt(key,frame.body,false)));
                if(result.optInt("id",-1)==id)return result;}
        }finally{deadline.cancel(false);}
    }
    JSONObject status()throws Exception{
        JSONArray r=rpc("get_prop",new JSONArray(new String[]{"printer-state","printer-state-alerts","media-size","ribbon-info"})).getJSONArray("result");
        int media=r.getJSONObject(2).getInt("media-size");JSONArray ribbon=r.getJSONObject(3).optJSONArray("ribbon-info");
        return new JSONObject().put("connected",true).put("name","米家桌面照片机 2").put("address",address)
            .put("state",r.optString(0)).put("alert",r.optString(1)).put("media",media)
            .put("ribbon",ribbon==null?-1:ribbon.optInt(2,-1)).put("checkedAt",System.currentTimeMillis());
    }
    JSONObject job(int id)throws Exception{
        JSONArray result=rpc("get-job-info",new JSONObject().put("job-id",id)).getJSONArray("result");
        if(result.length()!=1||result.getJSONObject(0).optInt("job-id",-1)!=id)throw new IOException("任务状态无法确认，请检查打印机");
        return result.getJSONObject(0);
    }
    interface Progress{void update(int value)throws Exception;}
    void upload(int job,byte[] jpeg,Progress progress)throws Exception{
        ScheduledFuture<?> deadline=timer.schedule(this::closeSocket,90,TimeUnit.SECONDS);
        try{int total=(jpeg.length+987)/988;
            for(int i=0;i<total;i++){
                if(Store.cancel)throw new IOException("已请求取消传输，请检查任务状态");
                int offset=i*988,len=Math.min(988,jpeg.length-offset);
                byte[] body=ByteBuffer.allocate(4+len).order(ByteOrder.LITTLE_ENDIAN).putInt(job).put(jpeg,offset,len).array();
                socket.getOutputStream().write(Wire.frame(4,6,2,sequence++,total,i+1,Wire.crypt(key,body,true)));
                if((i+1)%3==0||i+1==total){socket.getOutputStream().flush();Thread.sleep(15);}
                if((i+1)%12==0||i+1==total)progress.update((i+1)*100/total);
            }
        }finally{deadline.cancel(false);}
    }
    private void closeSocket(){try{if(socket!=null)socket.close();}catch(Exception ignored){}}
    public void close(){closeSocket();timer.shutdownNow();}
}
