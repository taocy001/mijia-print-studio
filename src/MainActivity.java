package local.liuying.studio;
import android.Manifest;
import android.app.*;
import android.bluetooth.BluetoothAdapter;
import android.content.*;
import android.content.pm.PackageManager;
import android.graphics.*;
import android.net.Uri;
import android.os.*;
import android.provider.Settings;
import android.provider.MediaStore;
import android.util.Base64;
import android.view.*;
import android.webkit.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.*;
import org.json.*;

public final class MainActivity extends Activity {
    private static final String HOST="studio.local";
    private WebView web;
    private final Handler main=new Handler(Looper.getMainLooper());
    private final java.util.concurrent.atomic.AtomicBoolean cutting=new java.util.concurrent.atomic.AtomicBoolean();
    private boolean picking,sharingLan;
    private int pickLimit=6;
    @Override public void onCreate(Bundle saved){
        super.onCreate(saved);
        updateSystemTheme();
        web=new WebView(this);updateSystemTheme();
        android.widget.FrameLayout root=new android.widget.FrameLayout(this);root.setBackgroundColor((getResources().getConfiguration().uiMode & android.content.res.Configuration.UI_MODE_NIGHT_MASK)==android.content.res.Configuration.UI_MODE_NIGHT_YES?Color.rgb(17,18,20):Color.rgb(245,245,247));
        root.addView(web,new android.widget.FrameLayout.LayoutParams(-1,-1));
        root.setOnApplyWindowInsetsListener((v,insets)->{android.graphics.Insets system=insets.getInsets(WindowInsets.Type.systemBars()|WindowInsets.Type.displayCutout());v.setPadding(system.left,system.top,system.right,Math.max(system.bottom,insets.getInsets(WindowInsets.Type.ime()).bottom));return WindowInsets.CONSUMED;});
        setContentView(root);
        WebSettings settings=web.getSettings();settings.setJavaScriptEnabled(true);settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);settings.setAllowContentAccess(false);settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setSupportMultipleWindows(false);settings.setTextZoom(100);
        web.addJavascriptInterface(new Bridge(),"Studio");
        web.setWebViewClient(new WebViewClient(){
            @Override public boolean shouldOverrideUrlLoading(WebView v,WebResourceRequest r){return true;}
            @Override public WebResourceResponse shouldInterceptRequest(WebView v,WebResourceRequest request){
                Uri uri=request.getUrl();String path=uri.getPath();
                try{
                    if(!HOST.equals(uri.getHost())||!"https".equals(uri.getScheme())||path==null||path.contains(".."))throw new IOException();
                    InputStream input;String mime;
                    if(path.startsWith("/private/")){
                        File root=getFilesDir(),file=new File(root,path.substring(9));
                        if(!file.getCanonicalPath().startsWith(root.getCanonicalPath()+"/")||!file.getName().endsWith(".jpg"))throw new IOException();
                        input=new FileInputStream(file);mime="image/jpeg";
                    }else{
                        String name=path.equals("/")?"index.html":path.substring(1);
                        if(!AssetPolicy.allows(name))throw new IOException();
                        input=getAssets().open(name);mime=name.endsWith(".jpg")?"image/jpeg":name.endsWith(".png")?"image/png":name.endsWith(".js")?"application/javascript":name.endsWith(".css")?"text/css":name.endsWith(".svg")?"image/svg+xml":name.endsWith(".ttf")?"font/ttf":"text/html";
                    }
                    Map<String,String> headers=new HashMap<>();headers.put("Cache-Control","no-store");headers.put("X-Content-Type-Options","nosniff");
                    headers.put("Content-Security-Policy","default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; object-src 'none'; frame-src 'none'");
                    return new WebResourceResponse(mime,"UTF-8",200,"OK",headers,input);
                }catch(Exception e){return new WebResourceResponse("text/plain","UTF-8",404,"Not Found",Collections.emptyMap(),new ByteArrayInputStream(new byte[0]));}
            }
        });
        web.setWebChromeClient(new WebChromeClient(){@Override public boolean onConsoleMessage(ConsoleMessage m){android.util.Log.d("LiuyingUI",m.message()+" @"+m.lineNumber());return true;}});
        web.loadUrl("https://"+HOST+"/");
    }
    private void updateSystemTheme(){
        boolean dark=(getResources().getConfiguration().uiMode & android.content.res.Configuration.UI_MODE_NIGHT_MASK)==android.content.res.Configuration.UI_MODE_NIGHT_YES;
        int color=dark?Color.rgb(17,18,20):Color.rgb(245,245,247);
        getWindow().setStatusBarColor(color);getWindow().setNavigationBarColor(color);
        getWindow().getDecorView().setSystemUiVisibility(dark?0:View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR|View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);
        if(web!=null)web.setBackgroundColor(color);
    }
    private void event(String type,Object value){main.post(()->{if(web!=null)try{web.evaluateJavascript("window.nativeEvent&&window.nativeEvent("+new JSONObject().put("type",type).put("value",value)+")",null);}catch(Exception ignored){}});}
    private boolean granted(){return checkSelfPermission(Manifest.permission.BLUETOOTH_CONNECT)==PackageManager.PERMISSION_GRANTED&&checkSelfPermission(Manifest.permission.BLUETOOTH_SCAN)==PackageManager.PERMISSION_GRANTED;}
    private void check(){
        if(!granted()){requestPermissions(new String[]{Manifest.permission.BLUETOOTH_CONNECT,Manifest.permission.BLUETOOTH_SCAN},7);return;}
        synchronized(Store.LOCK){if(Store.busy)return;JSONObject job=Store.read(this,"job.json");if(job.has("token")&&!Store.terminal(job)){event("toast","请先在打印进度中处理当前任务");return;}Store.busy=true;Store.message="正在连接打印机…";}
        new Thread(()->{try(Printer printer=new Printer(this)){Store.device=printer.status();Store.message="蓝牙已连接";}
            catch(Exception e){Store.device=new JSONObject();Store.message="连接失败，请确认打印机开机，且米家未占用蓝牙";event("toast",Store.message);android.util.Log.w("LiuyingPrint","Status",e);}
            finally{Store.busy=false;}},"liuying-status").start();
    }
    @Override public void onRequestPermissionsResult(int request,String[] permissions,int[] results){super.onRequestPermissionsResult(request,permissions,results);if(request==9&&granted())startSharingService();if(request==7){if(granted())check();else event("toast","需要附近设备权限才能连接打印机");}}
    private void startSharingService(){
        if(Build.VERSION.SDK_INT>=33&&checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED)requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},8);
        try{startForegroundService(new Intent(this,SharingService.class).putExtra("lan",sharingLan));}catch(RuntimeException e){event("toast","请解锁手机并保持 App 在前台，再开启共享");}
    }
    private void service(String action){
        if(!granted()){event("toast","请先连接打印机并允许附近设备权限");return;}
        if(Build.VERSION.SDK_INT>=33&&checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED)
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},8);
        try{startForegroundService(new Intent(this,PrintService.class).putExtra("action",action));}catch(RuntimeException e){event("toast","任务尚未启动，请回到 App 检查打印进度");}
    }
    @Override public void onConfigurationChanged(android.content.res.Configuration configuration){
        super.onConfigurationChanged(configuration);
        updateSystemTheme();
        if(web!=null)web.post(()->web.evaluateJavascript("window.updateEditorOrientation&&window.updateEditorOrientation()",null));
    }
    private final class Bridge {
        @JavascriptInterface public String sharingState(){return SharingService.sharingState().toString();}
        @JavascriptInterface public void startSharing(boolean lan){main.post(()->{sharingLan=lan;if(!granted()){requestPermissions(new String[]{Manifest.permission.BLUETOOTH_CONNECT,Manifest.permission.BLUETOOTH_SCAN},9);return;}startSharingService();});}
        @JavascriptInterface public void stopSharing(){SharingService.stopSharing();}
        @JavascriptInterface public void resumeSharing(){SharingService.resumeQueue();}
        @JavascriptInterface public boolean landscape(){return getResources().getConfiguration().orientation==android.content.res.Configuration.ORIENTATION_LANDSCAPE;}

        @JavascriptInterface public String state(){try{return Store.state(MainActivity.this).put("permission",granted()).toString();}catch(Exception e){return "{}";}}
        @JavascriptInterface public void connect(){main.post(()->check());}
        @JavascriptInterface public void bluetoothSettings(){main.post(()->startActivity(new Intent(Settings.ACTION_BLUETOOTH_SETTINGS)));}
        @JavascriptInterface public void pick(int remaining){main.post(()->{
            if(picking)return;
            if(remaining<1){event("toast","最多选择 6 张照片");return;}
            pickLimit=Math.min(6,remaining);picking=true;
            if(Build.VERSION.SDK_INT>=33){
                Intent picker=new Intent(MediaStore.ACTION_PICK_IMAGES).setType("image/*");
                if(pickLimit>1)picker.putExtra(MediaStore.EXTRA_PICK_IMAGES_MAX,Math.min(pickLimit,MediaStore.getPickImagesMaxLimit()));
                try{startActivityForResult(picker,10);return;}catch(ActivityNotFoundException ignored){}
            }
            Intent intent=new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("image/*").addCategory(Intent.CATEGORY_OPENABLE).putExtra(Intent.EXTRA_ALLOW_MULTIPLE,pickLimit>1);
            try{startActivityForResult(intent,10);event("toast","长按照片可多选，本次最多选择 "+pickLimit+" 张");}
            catch(Exception e){picking=false;event("toast","无法打开照片选择器");}
        });}
        @JavascriptInterface public String cutout(String source){
            if(!cutting.compareAndSet(false,true))return "{\"error\":\"正在处理另一张照片，请稍候\"}";
            new Thread(()->{
                try{JSONObject images=PortraitCutout.process(MainActivity.this,source);event("cutout",new JSONObject().put("source",source).put("images",images));}
                catch(Exception|OutOfMemoryError e){try{event("cutoutError",new JSONObject().put("source",source).put("message","抠图未完成，请使用清晰的人像照片重试"));}catch(Exception ignored){}}
                finally{cutting.set(false);}
            },"liuying-cutout").start();return "{\"ok\":true}";
        }
        @JavascriptInterface public void pickTexture(){main.post(()->{
            if(picking)return;picking=true;
            Intent intent=new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("image/*").addCategory(Intent.CATEGORY_OPENABLE);
            try{startActivityForResult(intent,11);}catch(Exception e){picking=false;event("toast","无法打开图片选择器");}
        });}
        @JavascriptInterface public String print(String base64,String settings){
            try{JSONObject page=new JSONObject(settings).put("base64",base64);return printBatch(new JSONArray().put(page).toString());}
            catch(Exception e){return "{\"error\":\"无法读取打印参数\"}";}
        }
        @JavascriptInterface public String printBatch(String payload){
            try{
                if(!granted())throw new IOException("请先连接打印机");
                synchronized(Store.LOCK){
                    JSONObject previous=Store.read(MainActivity.this,"job.json");
                    if(Store.busy||(previous.has("token")&&!Store.terminal(previous)))throw new IOException("请先处理当前打印任务");
                    if(payload.length()>18000000)throw new IOException("照片数据过大");
                    JSONObject first=PrintJobs.prepare(MainActivity.this,"local",UUID.randomUUID().toString(),payload);
                    Store.write(MainActivity.this,"job.json",first);
                    main.post(()->service("print"));return new JSONObject().put("ok",true).toString();
                }
            }catch(Exception e){try{return new JSONObject().put("error",e.getMessage()).toString();}catch(Exception ignored){return "{}";}}
        }
        @JavascriptInterface public void reconcile(){main.post(()->{if(!Store.busy)service("reconcile");});}
        @JavascriptInterface public void cancel(){main.post(()->{
            new AlertDialog.Builder(MainActivity.this).setTitle("取消当前打印任务？").setMessage("已开始的机械打印可能无法立即停止。")
                .setNegativeButton("继续打印",null).setPositiveButton("取消任务",(d,w)->{if(Store.busy)Store.cancel=true;else service("cancel");}).show();
        });}
        @JavascriptInterface public void discardPrepared(){
            synchronized(Store.LOCK){JSONObject job=Store.read(MainActivity.this,"job.json");if(!Store.busy&&"prepared".equals(job.optString("phase")))try{job.put("phase","cancelled");job.put("message","已取消尚未提交的任务");Store.write(MainActivity.this,"job.json",job);}catch(Exception ignored){}}
        }
        @JavascriptInterface public void resolveUnknown(){main.post(()->{
            JSONObject current=Store.read(MainActivity.this,"job.json");
            if(Store.busy||current.has("jobId")||!current.has("token")||Store.terminal(current))return;
            new AlertDialog.Builder(MainActivity.this).setTitle("结束结果未知的记录？")
                .setMessage("请先确认打印机已停止，并检查是否已经出纸。这里只归档本次记录，不会重新打印，也不会取消打印机里的任务。")
                .setNegativeButton("继续检查",null).setPositiveButton("已检查，结束记录",(d,w)->{
                    synchronized(Store.LOCK){JSONObject latest=Store.read(MainActivity.this,"job.json");
                        if(Store.busy||!current.optString("token").equals(latest.optString("token"))||latest.has("jobId"))return;
                        try{latest.put("phase","aborted").put("message","手动结束结果未知的记录，未重新打印");Store.write(MainActivity.this,"job.json",latest);Store.archive(MainActivity.this,latest);}
                        catch(Exception e){event("toast","记录更新失败，请重试");}}
                }).show();
        });}
    }
    @Override protected void onActivityResult(int request,int result,Intent data){
        super.onActivityResult(request,result,data);if(request!=10&&request!=11)return;picking=false;
        if(result!=RESULT_OK||data==null)return;
        int limit=request==11?1:pickLimit;
        if(data.getClipData()!=null&&data.getClipData().getItemCount()>limit){event("toast","本次最多选择 "+limit+" 张照片，请重新选择");return;}
        ArrayList<Uri> uris=new ArrayList<>();if(data.getClipData()!=null){for(int i=0;i<data.getClipData().getItemCount();i++)uris.add(data.getClipData().getItemAt(i).getUri());}else if(data.getData()!=null)uris.add(data.getData());
        event("loading",true);
        new Thread(()->{
            JSONArray imported=new JSONArray();
            try{new File(getFilesDir(),"photos").mkdirs();
                for(Uri uri:uris){
                    Bitmap bitmap=ImageDecoder.decodeBitmap(ImageDecoder.createSource(getContentResolver(),uri),(decoder,info,source)->{
                        decoder.setAllocator(ImageDecoder.ALLOCATOR_SOFTWARE);int w=info.getSize().getWidth(),h=info.getSize().getHeight();
                        double scale=Math.min(1,2400.0/Math.max(w,h));decoder.setTargetSize(Math.max(1,(int)(w*scale)),Math.max(1,(int)(h*scale)));
                    });
                    String name="photos/"+UUID.randomUUID()+".jpg";
                    try(FileOutputStream out=new FileOutputStream(new File(getFilesDir(),name))){bitmap.compress(Bitmap.CompressFormat.JPEG,97,out);}
                    imported.put(new JSONObject().put("src","/private/"+name).put("width",bitmap.getWidth()).put("height",bitmap.getHeight()));bitmap.recycle();
                }
            }catch(Exception e){event("toast","有照片未能读取，请尝试其他图片");android.util.Log.w("LiuyingUI","Import",e);}
            finally{event(request==11?"texture":"photos",imported);event("loading",false);}
        },"liuying-import").start();
    }
    @Override public void onBackPressed(){web.evaluateJavascript("window.goBack?window.goBack():false",value->{if(!"true".equals(value))super.onBackPressed();});}
    @Override protected void onDestroy(){if(web!=null){web.removeJavascriptInterface("Studio");web.destroy();web=null;}super.onDestroy();}
}
