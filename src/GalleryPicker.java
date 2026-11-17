package local.liuying.studio;

import android.Manifest;
import android.app.*;
import android.content.*;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.graphics.*;
import android.graphics.drawable.Drawable;
import android.net.Uri;
import android.os.*;
import android.provider.MediaStore;
import android.util.*;
import android.view.*;
import android.widget.*;
import java.util.*;
import java.util.concurrent.*;

/** App-owned image grid: the camera is item zero, not an editor toolbar action. */
final class GalleryPicker extends Dialog {
    interface Listener {void photos(ArrayList<Uri> uris);void camera();void system();void closed();}
    private final Activity activity;
    private final Listener listener;
    private final int limit;
    private final Handler main=new Handler(Looper.getMainLooper());
    private final ExecutorService worker=Executors.newFixedThreadPool(2);
    private final ArrayList<Uri> photos=new ArrayList<>();
    private final LinkedHashSet<Uri> selected=new LinkedHashSet<>();
    private final Set<Uri> pending=new HashSet<>();
    private final LruCache<Uri,Bitmap> thumbnails=new LruCache<Uri,Bitmap>(8*1024*1024){@Override protected int sizeOf(Uri u,Bitmap b){return b.getAllocationByteCount();}};
    private final GridView grid;
    private final BaseAdapter adapter;
    private final Button done,system,access;
    private final TextView status;
    private final int ink,bg,tile;
    private boolean closed,loading,validating,more=true;
    private Runnable afterDismiss;
    private final Set<CancellationSignal> thumbnailSignals=ConcurrentHashMap.newKeySet();
    private int generation,offset;
    private android.os.CancellationSignal querySignal;
    private static final int PAGE=120;
    static boolean canRead(Activity a){return a.checkSelfPermission(Build.VERSION.SDK_INT>=33?Manifest.permission.READ_MEDIA_IMAGES:Manifest.permission.READ_EXTERNAL_STORAGE)==PackageManager.PERMISSION_GRANTED||(Build.VERSION.SDK_INT>=34&&a.checkSelfPermission(Manifest.permission.READ_MEDIA_VISUAL_USER_SELECTED)==PackageManager.PERMISSION_GRANTED);}
    static boolean fullAccess(Activity a){return a.checkSelfPermission(Build.VERSION.SDK_INT>=33?Manifest.permission.READ_MEDIA_IMAGES:Manifest.permission.READ_EXTERNAL_STORAGE)==PackageManager.PERMISSION_GRANTED;}
    static String[] permissions(){return Build.VERSION.SDK_INT>=34?new String[]{Manifest.permission.READ_MEDIA_IMAGES,Manifest.permission.READ_MEDIA_VISUAL_USER_SELECTED}:new String[]{Build.VERSION.SDK_INT>=33?Manifest.permission.READ_MEDIA_IMAGES:Manifest.permission.READ_EXTERNAL_STORAGE};}
    GalleryPicker(Activity a,int maximum,Listener l){
        super(a);activity=a;listener=l;limit=maximum;requestWindowFeature(Window.FEATURE_NO_TITLE);
        boolean dark=(a.getResources().getConfiguration().uiMode&android.content.res.Configuration.UI_MODE_NIGHT_MASK)==android.content.res.Configuration.UI_MODE_NIGHT_YES;
        ink=dark?Color.WHITE:Color.rgb(28,30,33);bg=dark?Color.rgb(25,26,29):Color.rgb(248,248,250);tile=dark?Color.rgb(44,46,51):Color.rgb(228,231,235);
        LinearLayout root=new LinearLayout(a);root.setOrientation(LinearLayout.VERTICAL);root.setPadding(dp(12),dp(10),dp(12),dp(10));root.setBackgroundColor(bg);
        LinearLayout header=new LinearLayout(a);header.setGravity(Gravity.CENTER_VERTICAL);
        TextView title=new TextView(a);title.setText("选择照片");title.setTextSize(20);title.setTextColor(ink);header.addView(title,new LinearLayout.LayoutParams(0,dp(48),1));
        system=button("系统相册");header.addView(system);Button cancel=button("取消");header.addView(cancel);root.addView(header);
        status=new TextView(a);status.setTextColor(ink);status.setTextSize(13);status.setPadding(0,dp(4),0,dp(8));root.addView(status);
        access=button("显示相册照片");root.addView(access,new LinearLayout.LayoutParams(-1,dp(44)));
        grid=new GridView(a);grid.setNumColumns(a.getResources().getConfiguration().screenWidthDp>=600?6:3);grid.setHorizontalSpacing(dp(4));grid.setVerticalSpacing(dp(4));grid.setStretchMode(GridView.STRETCH_COLUMN_WIDTH);grid.setClipToPadding(false);
        adapter=new BaseAdapter(){
            public int getCount(){return photos.size()+1;}public Object getItem(int p){return p==0?null:photos.get(p-1);}public long getItemId(int p){return p;}
            public View getView(int position,View old,android.view.ViewGroup parent){
                Cell cell=old instanceof Cell?(Cell)old:new Cell();Uri uri=position==0?null:photos.get(position-1);cell.uri=uri;
                cell.image.setImageDrawable(null);cell.label.setText("");cell.label.setVisibility(View.GONE);cell.setBackgroundColor(tile);
                if(uri==null){cell.image.setImageDrawable(new CameraIcon());cell.label.setText("拍照");cell.label.setVisibility(View.VISIBLE);cell.setContentDescription("拍照");cell.setAlpha(selected.isEmpty()?1f:.45f);}
                else{cell.setAlpha(1f);Bitmap cached=thumbnails.get(uri);if(cached!=null)cell.image.setImageBitmap(cached);else thumbnail(uri);int order=new ArrayList<>(selected).indexOf(uri);cell.label.setText(order>=0?String.valueOf(order+1):"○");cell.label.setVisibility(View.VISIBLE);cell.setContentDescription("照片 "+position+(order>=0?"，已选择 "+(order+1):"，未选择"));}
                cell.label.setBackgroundColor(uri==null?Color.TRANSPARENT:selected.contains(uri)?Color.rgb(166,125,36):0x66000000);cell.label.setTextColor(uri==null?ink:Color.WHITE);return cell;
            }
        };
        grid.setAdapter(adapter);root.addView(grid,new LinearLayout.LayoutParams(-1,0,1));
        done=button("添加照片");root.addView(done,new LinearLayout.LayoutParams(-1,dp(50)));setContentView(root);
        cancel.setOnClickListener(v->dismiss());system.setOnClickListener(v->finish(()->listener.system()));
        access.setOnClickListener(v->a.requestPermissions(permissions(),15));
        done.setOnClickListener(v->{if(selected.isEmpty())return;ArrayList<Uri> result=new ArrayList<>(selected);finish(()->listener.photos(result));});
        grid.setOnItemClickListener((parent,view,position,id)->{
            if(position==0){if(!selected.isEmpty()){Toast.makeText(a,"请先添加已选照片，或取消勾选后拍照",Toast.LENGTH_SHORT).show();return;}finish(()->listener.camera());return;}
            Uri uri=photos.get(position-1);if(!selected.remove(uri)){if(selected.size()>=limit){Toast.makeText(a,"本次最多选择 "+limit+" 张",Toast.LENGTH_SHORT).show();return;}selected.add(uri);}update();adapter.notifyDataSetChanged();
        });
        grid.setOnScrollListener(new AbsListView.OnScrollListener(){public void onScrollStateChanged(AbsListView v,int state){}public void onScroll(AbsListView v,int first,int visible,int total){if(visible>0&&first+visible>=total-12)loadMore();}});
        setOnDismissListener(d->{closed=true;generation++;if(querySignal!=null)querySignal.cancel();cancelThumbnails();worker.shutdownNow();thumbnails.evictAll();listener.closed();Runnable action=afterDismiss;afterDismiss=null;if(action!=null&&!activity.isFinishing()&&!activity.isDestroyed())action.run();});
    }
    private void finish(Runnable action){if(closed)return;afterDismiss=action;dismiss();}
    private void cancelThumbnails(){for(CancellationSignal signal:thumbnailSignals)signal.cancel();thumbnailSignals.clear();}
    private Button button(String text){Button b=new Button(activity);b.setText(text);b.setTextColor(ink);b.setAllCaps(false);b.setMinHeight(dp(44));return b;}
    private int dp(int n){return Math.round(n*activity.getResources().getDisplayMetrics().density);}
    @Override public void show(){super.show();Window w=getWindow();if(w!=null){w.setBackgroundDrawableResource(android.R.color.transparent);w.setGravity(Gravity.BOTTOM);w.setLayout(-1,(int)(activity.getWindowManager().getCurrentWindowMetrics().getBounds().height()*.82));}refresh();}
    void resized(){if(closed)return;grid.setNumColumns(activity.getResources().getConfiguration().screenWidthDp>=600?6:3);Window w=getWindow();if(w!=null)w.setLayout(-1,(int)(activity.getWindowManager().getCurrentWindowMetrics().getBounds().height()*.82));}
    void refresh(){if(closed)return;generation++;if(querySignal!=null)querySignal.cancel();photos.clear();if(!canRead(activity))selected.clear();cancelThumbnails();thumbnails.evictAll();pending.clear();loading=false;more=true;offset=0;validateSelection();update();adapter.notifyDataSetChanged();loadMore();}
    private void validateSelection(){
        validating=!selected.isEmpty();if(!validating)return;int token=generation;ArrayList<Uri> snapshot=new ArrayList<>(selected);
        worker.execute(()->{ArrayList<Uri> unavailable=new ArrayList<>();for(Uri uri:snapshot){try(android.content.res.AssetFileDescriptor fd=activity.getContentResolver().openAssetFileDescriptor(uri,"r")){if(fd==null)unavailable.add(uri);}catch(Exception e){unavailable.add(uri);}}
            main.post(()->{if(closed||token!=generation)return;validating=false;selected.removeAll(unavailable);update();adapter.notifyDataSetChanged();});});
    }
    private void update(){boolean read=canRead(activity),full=fullAccess(activity);status.setText(!read?"允许访问照片后，这里会显示相册；也可以直接拍照。":selected.isEmpty()?(full?"最近照片":"当前仅显示已获授权的照片")+" · 最多选 "+limit+" 张":"已选 "+selected.size()+" / "+limit+" 张");access.setVisibility(full?View.GONE:View.VISIBLE);access.setText(read?"选择更多可访问的照片":"显示相册照片");access.setEnabled(selected.isEmpty());system.setEnabled(selected.isEmpty());done.setEnabled(!selected.isEmpty()&&!validating);done.setText(selected.isEmpty()?"添加照片":"添加 "+selected.size()+" 张照片");}
    private void loadMore(){
        if(closed||loading||!more||!canRead(activity))return;loading=true;int token=generation,start=offset;android.os.CancellationSignal signal=new android.os.CancellationSignal();querySignal=signal;
        worker.execute(()->{
            ArrayList<Uri> found=new ArrayList<>();String error=null;
            try{Uri collection=MediaStore.Images.Media.getContentUri(MediaStore.VOLUME_EXTERNAL);Bundle args=new Bundle();args.putString(ContentResolver.QUERY_ARG_SQL_SORT_ORDER,MediaStore.Images.Media.DATE_ADDED+" DESC, "+MediaStore.Images.Media._ID+" DESC");args.putInt(ContentResolver.QUERY_ARG_LIMIT,PAGE);args.putInt(ContentResolver.QUERY_ARG_OFFSET,start);
                try(Cursor c=activity.getContentResolver().query(collection,new String[]{MediaStore.Images.Media._ID},args,signal)){if(c==null)throw new IllegalStateException();while(c.moveToNext())found.add(ContentUris.withAppendedId(collection,c.getLong(0)));}
            }catch(OperationCanceledException ignored){return;}catch(Exception e){error="暂时无法读取相册，可使用“系统相册”选择照片。";}
            final String message=error;main.post(()->{if(closed||token!=generation)return;loading=false;offset+=found.size();more=found.size()==PAGE;photos.addAll(found);adapter.notifyDataSetChanged();if(message!=null){more=false;status.setText(message);}else if(photos.isEmpty())status.setText("暂无可访问的照片，可以拍照或使用系统相册。");});
        });
    }
    private void thumbnail(Uri uri){
        if(closed||!pending.add(uri))return;int token=generation;CancellationSignal signal=new CancellationSignal();thumbnailSignals.add(signal);
        worker.execute(()->{Bitmap bitmap=null;try{bitmap=activity.getContentResolver().loadThumbnail(uri,new Size(256,256),signal);}catch(Exception|OutOfMemoryError ignored){}finally{thumbnailSignals.remove(signal);}final Bitmap result=bitmap;
            main.post(()->{if(closed||token!=generation){if(result!=null)result.recycle();return;}pending.remove(uri);if(result!=null){thumbnails.put(uri,result);for(int i=0;i<grid.getChildCount();i++){Cell cell=(Cell)grid.getChildAt(i);if(uri.equals(cell.uri))cell.image.setImageBitmap(result);}}});
        });
    }
    private final class Cell extends FrameLayout {
        Uri uri;final ImageView image;final TextView label;
        Cell(){super(activity);image=new ImageView(activity);image.setScaleType(ImageView.ScaleType.CENTER_CROP);addView(image,new FrameLayout.LayoutParams(-1,-1));label=new TextView(activity);label.setTextSize(15);label.setGravity(Gravity.CENTER);FrameLayout.LayoutParams lp=new FrameLayout.LayoutParams(dp(48),dp(32),Gravity.BOTTOM|Gravity.RIGHT);addView(label,lp);}
        @Override protected void onMeasure(int width,int height){super.onMeasure(width,View.MeasureSpec.makeMeasureSpec(View.MeasureSpec.getSize(width),View.MeasureSpec.EXACTLY));}
    }
    private final class CameraIcon extends Drawable {
        final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
        public void draw(Canvas c){Rect b=getBounds();float u=Math.min(b.width(),b.height()),x=b.exactCenterX(),y=b.exactCenterY()-u*.06f;paint.setColor(ink);paint.setStyle(Paint.Style.STROKE);paint.setStrokeWidth(u*.025f);c.drawRoundRect(x-u*.21f,y-u*.14f,x+u*.21f,y+u*.14f,u*.025f,u*.025f,paint);c.drawCircle(x,y,u*.08f,paint);c.drawRect(x-u*.1f,y-u*.19f,x+u*.08f,y-u*.14f,paint);}
        public void setAlpha(int a){paint.setAlpha(a);}public void setColorFilter(ColorFilter f){paint.setColorFilter(f);}public int getOpacity(){return PixelFormat.TRANSLUCENT;}
    }
}
