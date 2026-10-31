package local.liuying.studio;
import java.io.IOException;
final class CutoutMath {
 static float[] input(int[] pixels){
  float max=1;for(int p:pixels)max=Math.max(max,Math.max((p>>16)&255,Math.max((p>>8)&255,p&255)));
  float[] result=new float[pixels.length*3],mean={.485f,.456f,.406f},std={.229f,.224f,.225f};
  for(int c=0;c<3;c++)for(int i=0;i<pixels.length;i++)result[c*pixels.length+i]=(((pixels[i]>>(16-c*8))&255)/max-mean[c])/std[c];
  return result;
 }
 static int[] mask(float[] prediction)throws IOException{
  float min=Float.POSITIVE_INFINITY,max=Float.NEGATIVE_INFINITY;
  for(float p:prediction){if(!Float.isFinite(p))throw new IOException("无法识别主体，请换一张背景清晰的照片");min=Math.min(min,p);max=Math.max(max,p);}
  if(max-min<.000001f)throw new IOException("未识别到清晰主体，请换一张照片");
  int[] mask=new int[prediction.length];int foreground=0;
  for(int i=0;i<mask.length;i++){int a=Math.max(0,Math.min(255,Math.round((prediction[i]-min)/(max-min)*255)));if(a>128)foreground++;mask[i]=0xff000000|(a<<16)|(a<<8)|a;}
  if(foreground<mask.length/100||foreground>mask.length*99/100)throw new IOException("主体识别不明确，请换一张照片");
  return mask;
 }
 static int blend(int pixel,int mask,int background){
  int a=mask&255,r=(((pixel>>16)&255)*a+((background>>16)&255)*(255-a)+127)/255,g=(((pixel>>8)&255)*a+((background>>8)&255)*(255-a)+127)/255,b=((pixel&255)*a+(background&255)*(255-a)+127)/255;
  return 0xff000000|(r<<16)|(g<<8)|b;
 }
}
