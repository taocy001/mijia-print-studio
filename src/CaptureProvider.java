package local.liuying.studio;
import android.content.*;
import android.database.*;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.provider.OpenableColumns;
import java.io.*;
import java.nio.file.Files;

public final class CaptureProvider extends ContentProvider {
 static final String AUTHORITY="local.liuying.studio.capture";
 static File output(Context c,String id)throws IOException{
  if(id==null||!id.matches("[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"))throw new FileNotFoundException("Invalid capture");
  File cache=c.getCacheDir().getCanonicalFile(),root=new File(cache,"capture"),file=new File(root,id+".jpg");
  if(Files.isSymbolicLink(root.toPath())||Files.isSymbolicLink(file.toPath())||!root.equals(root.getCanonicalFile())||!root.equals(file.getCanonicalFile().getParentFile()))throw new FileNotFoundException("Invalid capture path");return file;
 }
 static Uri uri(String id){return Uri.parse("content://"+AUTHORITY+"/"+id+".jpg");}
 static File resolve(Context c,Uri uri)throws IOException{
  if(uri==null||!"content".equals(uri.getScheme())||!AUTHORITY.equals(uri.getAuthority())||uri.getQuery()!=null||uri.getFragment()!=null||uri.getPathSegments().size()!=1)throw new FileNotFoundException("Invalid capture URI");
  String name=uri.getLastPathSegment();if(name==null||!name.endsWith(".jpg")||!uri.getEncodedPath().equals("/"+name))throw new FileNotFoundException("Invalid capture name");return output(c,name.substring(0,name.length()-4));
 }
 @Override public boolean onCreate(){return true;}
 @Override public String getType(Uri uri){try{resolve(getContext(),uri);return "image/jpeg";}catch(IOException error){throw new IllegalArgumentException("Invalid capture URI");}}
 @Override public Cursor query(Uri uri,String[] projection,String selection,String[] args,String order){
  if(selection!=null||args!=null||order!=null)throw new IllegalArgumentException("Unsupported query");
  try{File file=resolve(getContext(),uri);if(!file.isFile())throw new FileNotFoundException();String[] columns=projection==null?new String[]{OpenableColumns.DISPLAY_NAME,OpenableColumns.SIZE}:projection;Object[] values=new Object[columns.length];for(int i=0;i<columns.length;i++){if(OpenableColumns.DISPLAY_NAME.equals(columns[i]))values[i]=file.getName();else if(OpenableColumns.SIZE.equals(columns[i]))values[i]=file.length();else throw new IllegalArgumentException("Unsupported column");}MatrixCursor cursor=new MatrixCursor(columns,1);cursor.addRow(values);return cursor;}catch(IOException error){throw new IllegalArgumentException("Invalid capture URI");}
 }
 @Override public ParcelFileDescriptor openFile(Uri uri,String mode)throws FileNotFoundException{
  try{File file=resolve(getContext(),uri);if(!file.isFile())throw new FileNotFoundException("Missing capture");int flags;
   if("r".equals(mode))flags=ParcelFileDescriptor.MODE_READ_ONLY;
   else if("w".equals(mode)||"wt".equals(mode))flags=ParcelFileDescriptor.MODE_WRITE_ONLY|ParcelFileDescriptor.MODE_TRUNCATE;
   else if("rw".equals(mode))flags=ParcelFileDescriptor.MODE_READ_WRITE;
   else if("rwt".equals(mode))flags=ParcelFileDescriptor.MODE_READ_WRITE|ParcelFileDescriptor.MODE_TRUNCATE;
   else throw new FileNotFoundException("Unsupported capture mode");return ParcelFileDescriptor.open(file,flags);
  }catch(IOException error){throw new FileNotFoundException("Invalid capture file");}
 }
 @Override public Uri insert(Uri uri,ContentValues values){throw new UnsupportedOperationException();}
 @Override public int update(Uri uri,ContentValues values,String selection,String[] args){throw new UnsupportedOperationException();}
 @Override public int delete(Uri uri,String selection,String[] args){throw new UnsupportedOperationException();}
}
