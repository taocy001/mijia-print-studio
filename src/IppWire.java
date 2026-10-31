package local.liuying.studio;
import java.io.*;
import java.nio.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
final class IppWire {
 static final class Failure extends IOException {final int code;Failure(int c,String s){super(s);code=c;}}
 static final class Attr {final int group,tag;final String name;final byte[] value;Attr(int g,int t,String n,byte[] v){group=g;tag=t;name=n;value=v;}}
 static final class Message {
  int version=0x200,code,id;List<Attr> attrs=new ArrayList<>();byte[] document=new byte[0];
  byte[] one(String name)throws IOException{byte[] out=null;for(Attr a:attrs)if(a.name.equals(name)){if(out!=null)throw new Failure(0x400,"Duplicate attribute");out=a.value;}return out;}
  String text(String name,String fallback)throws IOException{byte[] v=one(name);return v==null?fallback:new String(v,StandardCharsets.UTF_8);}
  int number(String name,int fallback)throws IOException{byte[] v=one(name);if(v==null)return fallback;if(v.length!=4)throw new Failure(0x400,"Invalid integer");return ByteBuffer.wrap(v).getInt();}
 }
 static byte[] number(int n){return ByteBuffer.allocate(4).putInt(n).array();}
 static byte[] utf(String s){return s.getBytes(StandardCharsets.UTF_8);}
 static Attr text(int group,int tag,String name,String value){return new Attr(group,tag,name,utf(value));}
 static Attr integer(int group,int tag,String name,int value){return new Attr(group,tag,name,number(value));}
 static byte[] field(DataInputStream in)throws IOException{int n=in.readUnsignedShort();byte[] b=new byte[n];in.readFully(b);return b;}
 static Message decode(byte[] bytes)throws IOException{
  if(bytes.length<9||bytes.length>33554432)throw new Failure(0x400,"Invalid request size");
  DataInputStream in=new DataInputStream(new ByteArrayInputStream(bytes));Message m=new Message();m.version=in.readUnsignedShort();m.code=in.readUnsignedShort();m.id=in.readInt();int group=0;String previous="";int count=0;
  while(true){int tag=in.readUnsignedByte();if(tag==3)break;if(tag<16){if(tag!=1&&tag!=2&&tag!=4)throw new Failure(0x400,"Invalid group");group=tag;previous="";continue;}
   if(group==0||++count>512||bytes.length-in.available()>65536)throw new Failure(0x400,"Invalid attributes");
   String name=new String(field(in),StandardCharsets.UTF_8);if(name.isEmpty())name=previous;else previous=name;
   byte[] value=field(in);m.attrs.add(new Attr(group,tag,name,value));
  }
  m.document=new byte[in.available()];in.readFully(m.document);return m;
 }
 static void field(DataOutputStream out,byte[] b)throws IOException{out.writeShort(b.length);out.write(b);}
 static byte[] encode(Message m)throws IOException{
  ByteArrayOutputStream b=new ByteArrayOutputStream();DataOutputStream out=new DataOutputStream(b);out.writeShort(m.version);out.writeShort(m.code);out.writeInt(m.id);int group=0;String previous="";
  for(Attr a:m.attrs){if(a.tag==0){out.writeByte(a.group);group=a.group;previous="";continue;}if(a.group!=group){out.writeByte(a.group);group=a.group;previous="";}out.writeByte(a.tag);field(out,utf(a.name.equals(previous)?"":a.name));field(out,a.value);previous=a.name;}
  out.writeByte(3);out.write(m.document);return b.toByteArray();
 }
 static Message response(Message request){Message m=new Message();m.version=request.version;m.id=request.id;m.attrs.add(text(1,0x47,"attributes-charset","utf-8"));m.attrs.add(text(1,0x48,"attributes-natural-language","en"));return m;}
}
