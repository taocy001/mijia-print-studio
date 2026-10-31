package local.liuying.studio;
import java.util.*;
final class FaceCropMath {
 static final class Plan {
  final boolean fit;final double left,top,width,height;
  Plan(boolean f,double x,double y,double w,double h){fit=f;left=x;top=y;width=w;height=h;}
 }
 static Plan plan(int width,int height,double ratio,List<float[]> faces){
  if(width<1||height<1||!Double.isFinite(ratio)||ratio<=0)throw new IllegalArgumentException("Invalid crop size");
  double cw=Math.min(width,height*ratio),ch=cw/ratio,x=(width-cw)/2,y=(height-ch)/2;
  double left=width,top=height,right=0,bottom=0;boolean found=false;
  for(float[] face:faces){
   if(face==null||face.length<4)continue;boolean finite=true;for(int i=0;i<4;i++)finite&=Float.isFinite(face[i]);if(!finite)continue;
   double l=Math.max(0,Math.min(1,face[0]))*width,t=Math.max(0,Math.min(1,face[1]))*height,r=Math.max(0,Math.min(1,face[2]))*width,b=Math.max(0,Math.min(1,face[3]))*height;
   if(r<=l||b<=t)continue;double fw=r-l,fh=b-t;
   left=Math.min(left,Math.max(0,l-fw*.2));top=Math.min(top,Math.max(0,t-fh*.5));right=Math.max(right,Math.min(width,r+fw*.2));bottom=Math.max(bottom,Math.min(height,b+fh*.2));found=true;
  }
  if(found){
   if(right-left>cw+width*1e-6||bottom-top>ch+height*1e-6)return new Plan(true,0,0,1,1);
   x=Math.max(Math.max(0,right-cw),Math.min(x,Math.min(left,width-cw)));
   y=Math.max(Math.max(0,bottom-ch),Math.min(y,Math.min(top,height-ch)));
  }
  return new Plan(false,x/width,y/height,cw/width,ch/height);
 }
 static float[] input(int[] pixels,int width,int height){
  float[] values=new float[3*640*640];
  for(int y=0;y<height;y++)for(int x=0;x<width;x++){int color=pixels[y*width+x],i=y*640+x;values[i]=color&255;values[640*640+i]=(color>>>8)&255;values[2*640*640+i]=(color>>>16)&255;}return values;
 }
 static List<float[]> decode(Map<String,float[]> outputs,int width,int height,int scaledWidth,int scaledHeight){
  List<float[]> boxes=new ArrayList<>();
  for(int stride:new int[]{8,16,32}){
   float[] cls=outputs.get("cls_"+stride),obj=outputs.get("obj_"+stride),box=outputs.get("bbox_"+stride);int cols=640/stride,count=cols*cols;
   if(cls==null||obj==null||box==null||cls.length!=count||obj.length!=count||box.length!=count*4)throw new IllegalArgumentException("Invalid face model output");
   for(int i=0;i<count;i++){
    double score=Math.sqrt(Math.max(0,Math.min(1,cls[i]))*Math.max(0,Math.min(1,obj[i])));if(!Double.isFinite(score)||score<.75)continue;
    if(Math.abs(box[i*4+2])>20||Math.abs(box[i*4+3])>20)continue;
    double cx=(i%cols+box[i*4])*stride*width/scaledWidth,cy=(i/cols+box[i*4+1])*stride*height/scaledHeight,w=Math.exp(box[i*4+2])*stride*width/scaledWidth,h=Math.exp(box[i*4+3])*stride*height/scaledHeight;
    if(!Double.isFinite(cx)||!Double.isFinite(cy)||!Double.isFinite(w)||!Double.isFinite(h)||w<=0||h<=0)continue;
    float l=(float)Math.max(0,(cx-w/2)/width),t=(float)Math.max(0,(cy-h/2)/height),r=(float)Math.min(1,(cx+w/2)/width),b=(float)Math.min(1,(cy+h/2)/height);
    if(r>l&&b>t)boxes.add(new float[]{l,t,r,b,(float)score});
   }
  }
  boxes.sort((a,b)->Float.compare(b[4],a[4]));List<float[]> keep=new ArrayList<>();
  for(float[] candidate:boxes.subList(0,Math.min(1000,boxes.size()))){boolean duplicate=false;for(float[] old:keep){double intersection=Math.max(0,Math.min(candidate[2],old[2])-Math.max(candidate[0],old[0]))*Math.max(0,Math.min(candidate[3],old[3])-Math.max(candidate[1],old[1]));double union=(candidate[2]-candidate[0])*(candidate[3]-candidate[1])+(old[2]-old[0])*(old[3]-old[1])-intersection;if(union>0&&intersection/union>.3){duplicate=true;break;}}if(!duplicate)keep.add(candidate);}
  return keep;
 }
}
