package local.liuying.studio;
import java.util.*;
public class FaceCropMathTest {
 static void check(boolean value,String why){if(!value)throw new AssertionError(why);}
 static void near(double actual,double expected){check(Math.abs(actual-expected)<1e-6,"expected "+expected+", got "+actual);}
 static List<float[]> faces(float[]... boxes){return Arrays.asList(boxes);}
 public static void main(String[] args){
  FaceCropMath.Plan noFace=FaceCropMath.plan(2000,1000,1,faces());near(noFace.left,.25);near(noFace.width,.5);check(!noFace.fit,"center fallback");
  FaceCropMath.Plan left=FaceCropMath.plan(2000,1000,1,faces(new float[]{.05f,.3f,.15f,.5f}));check(left.left<.031,"protect left face with margin");near(left.width,.5);
  FaceCropMath.Plan top=FaceCropMath.plan(1000,2000,1,faces(new float[]{.4f,.1f,.6f,.2f}));check(top.top<.051,"protect head at top");
  FaceCropMath.Plan group=FaceCropMath.plan(2000,1000,1,faces(new float[]{.05f,.3f,.15f,.5f},new float[]{.85f,.3f,.95f,.5f}));check(group.fit,"separated group uses fit");
  FaceCropMath.Plan unchanged=FaceCropMath.plan(2000,1000,1,faces(new float[]{.4f,.3f,.6f,.5f}));near(unchanged.left,.25);
  FaceCropMath.Plan malformed=FaceCropMath.plan(2000,1000,1,faces(new float[]{Float.NaN,.2f,.3f,.4f},new float[]{.8f,.3f,.2f,.4f}));near(malformed.left,.25);
  for(double ratio:new double[]{1,2.0/3,4.0/3}){
   FaceCropMath.Plan p=FaceCropMath.plan(1200,1800,ratio,faces(new float[]{.3f,.05f,.5f,.2f}));check(p.fit||p.top<=.05,"paper head safety");
   if(!p.fit)near(p.width*1200/(p.height*1800),ratio);
  }
  FaceCropMath.Plan right=FaceCropMath.plan(2000,1000,1,faces(new float[]{.8f,.25f,.9f,.45f}));near(right.left,.42);near(right.width,.5);
  FaceCropMath.Plan splice=FaceCropMath.plan(1000,2000,4.0/3,faces(new float[]{.3f,.05f,.5f,.15f}));near(splice.top,0);near(splice.height,.375);
  FaceCropMath.Plan full=FaceCropMath.plan(1000,1500,2.0/3,faces(new float[]{.35f,.2f,.65f,.4f}));near(full.width,1);near(full.height,1);
  float[] tensor=FaceCropMath.input(new int[]{0xff123456},1,1);near(tensor[0],0x56);near(tensor[640*640],0x34);near(tensor[2*640*640],0x12);near(tensor[1],0);
  Map<String,float[]> outputs=new HashMap<>();for(int s:new int[]{8,16,32}){int n=(640/s)*(640/s);outputs.put("cls_"+s,new float[n]);outputs.put("obj_"+s,new float[n]);outputs.put("bbox_"+s,new float[n*4]);}
  int i=10*80+10;outputs.get("cls_8")[i]=1;outputs.get("obj_8")[i]=1;float[] b=outputs.get("bbox_8");b[4*i]=.5f;b[4*i+1]=.5f;b[4*i+2]=(float)Math.log(4);b[4*i+3]=(float)Math.log(4);
  List<float[]> result=FaceCropMath.decode(outputs,1000,501,640,321);check(result.size()==1,"decode candidate");near(result.get(0)[0],68.0/640);near(result.get(0)[1],68.0/321);
  outputs.get("cls_8")[i]=Float.NaN;check(FaceCropMath.decode(outputs,1000,501,640,321).isEmpty(),"ignore NaN prediction");
  System.out.println("PASS face geometry: three papers, all faces, head margin, centered fallback, malformed boxes, BGR padding and actual resize axes");
 }
}
