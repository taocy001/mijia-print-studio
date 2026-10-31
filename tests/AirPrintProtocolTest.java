package local.liuying.studio;
import java.nio.file.*;
import java.util.*;
public class AirPrintProtocolTest {
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[] args)throws Exception{
  for(String ext:new String[]{"urf","pwg"})for(String shape:new String[]{"one-page","landscape"}){byte[] data=Files.readAllBytes(Paths.get(args[0],shape+"."+ext));RasterImage r=RasterImage.decode(data,ext.equals("urf")?"image/urf":"image/pwg-raster");check(r.width==(shape.equals("landscape")?1800:1200));check(r.pixels[0]==0xffff0000);check(r.pixels[r.pixels.length-1]==0xff0000ff);try{RasterImage.decode(Arrays.copyOf(data,data.length-1),ext.equals("urf")?"image/urf":"image/pwg-raster");throw new AssertionError();}catch(java.io.IOException expected){}}
  try{RasterImage.decode(Files.readAllBytes(Paths.get(args[0],"two-pages.pwg")),"image/pwg-raster");throw new AssertionError();}catch(java.io.IOException expected){}
  IppWire.Message req=new IppWire.Message();req.code=11;req.id=42;req.attrs.add(IppWire.text(1,0x47,"attributes-charset","utf-8"));req.attrs.add(IppWire.integer(2,0x21,"copies",1));IppWire.Message decoded=IppWire.decode(IppWire.encode(req));check(decoded.id==42&&decoded.number("copies",0)==1);decoded.attrs.add(IppWire.integer(2,0x21,"copies",2));try{decoded.number("copies",0);throw new AssertionError();}catch(java.io.IOException expected){}
  System.out.println("PASS: IPP roundtrip, duplicate rejection, URF/PWG portrait/landscape pixels, truncated and multi-page rejection");
 }
}
