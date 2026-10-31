package local.liuying.studio;
public class CutoutMathTest {
 public static void main(String[] args)throws Exception{
  float[] input=CutoutMath.input(new int[]{0xffff0000,0xff0000ff});
  if(Math.abs(input[0]-(1-.485f)/.229f)>.0001||Math.abs(input[5]-(1-.406f)/.225f)>.0001)throw new AssertionError("RGB normalization/CHW");
  int[] mask=CutoutMath.mask(new float[]{.2f,.8f,.2f,.8f});if((mask[0]&255)!=0||(mask[1]&255)!=255)throw new AssertionError("mask normalization");
  if(CutoutMath.blend(0xff112233,0xffffffff,0xffff0000)!=0xff112233)throw new AssertionError("foreground");
  if(CutoutMath.blend(0xff112233,0xff000000,0xffff0000)!=0xffff0000)throw new AssertionError("background");
  for(float[] bad:new float[][]{{1,1,1},{Float.NaN,1}}){boolean rejected=false;try{CutoutMath.mask(bad);}catch(Exception e){rejected=true;}if(!rejected)throw new AssertionError("bad mask");}
  System.out.println("PASS native preprocessing, mask normalization, color composition and invalid output rejection");
 }
}
