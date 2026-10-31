package local.liuying.studio;

import java.io.EOFException;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.util.Arrays;
import javax.crypto.Cipher;
import javax.crypto.spec.SecretKeySpec;

/** Hannto framing/DH, based on tuat-yate/xiaomi-photo-printer (MIT).
 * See licenses/Bluetooth-MIT.txt.
 */
public final class Wire {
    public static final int AES_OFFSET = 5120;
    public static byte[] frame(int channel, int op, int encoding, int sequence,
                               int total, int number, byte[] body) {
        if (body.length >= 1024) throw new IllegalArgumentException("Frame body exceeds 10-bit length");
        if(total<0||total>65535||number<0||number>total)throw new IllegalArgumentException("Invalid part number");
        ByteBuffer out = ByteBuffer.allocate(22+body.length).order(ByteOrder.LITTLE_ENDIAN);
        out.put((byte)0x7e).put((byte)0x64).put((byte)0).put((byte)channel);
        out.put((byte)op).put((byte)encoding).putInt(sequence).putInt(sequence);
        out.putShort((short)total).putShort((short)number);
        out.putShort((short)(body.length+AES_OFFSET+(total>1?8192:0))).put(body);
        int sum=0;
        for(int i=1;i<out.position();i++) sum+=out.array()[i]&255;
        out.put((byte)sum).put((byte)0x7e);
        return out.array();
    }

    public static final class Frame {
        public final int channel, op, encoding, total, number, attr;
        public final byte[] raw, body;
        Frame(byte[] data) throws IOException {
            raw=data;
            if(data.length<22 || data[0]!=0x7e || data[1]!=0x64 || data[2]!=0 || data[data.length-1]!=0x7e)
                throw new IOException("Bad frame delimiters");
            ByteBuffer h=ByteBuffer.wrap(data).order(ByteOrder.LITTLE_ENDIAN);
            attr=h.getShort(18)&65535;
            if(data.length != 22+(attr&1023)) throw new IOException("Bad frame length");
            int sum=0;
            for(int i=1;i<data.length-2;i++) sum+=data[i]&255;
            if((sum&255)!=(data[data.length-2]&255)) throw new IOException("Bad checksum");
            channel=data[3]&255;op=data[4]&255;encoding=data[5]&255;
            total=h.getShort(14)&65535;number=h.getShort(16)&65535;
            body=Arrays.copyOfRange(data,20,data.length-2);
        }
    }

    public static Frame read(InputStream input) throws IOException {
        int previous=-1, current;
        do {current=input.read();if(current<0) throw new EOFException("Before frame");
            if(previous==0x7e && current==0x64) break;previous=current;
        } while(true);
        byte[] header=new byte[20];header[0]=0x7e;header[1]=0x64;
        exact(input,header,2,18);
        int size=((header[18]&255)|((header[19]&255)<<8))&1023;
        byte[] raw=Arrays.copyOf(header,22+size);
        exact(input,raw,20,size+2);
        return new Frame(raw);
    }

    private static void exact(InputStream in,byte[] dst,int off,int count) throws IOException {
        while(count>0){int n=in.read(dst,off,count);if(n<0)throw new EOFException("Inside frame");
            if(n==0)continue;off+=n;count-=n;}
    }

    public static byte[] crypt(byte[] key, byte[] bytes, boolean encrypt) throws Exception {
        if(!encrypt && bytes.length%16!=0)throw new IOException("Unaligned ciphertext");
        byte[] input=encrypt?Arrays.copyOf(bytes,(bytes.length+15)/16*16):bytes;
        Cipher cipher=Cipher.getInstance("AES/ECB/NoPadding");
        cipher.init(encrypt?Cipher.ENCRYPT_MODE:Cipher.DECRYPT_MODE,new SecretKeySpec(key,"AES"));
        return cipher.doFinal(input);
    }

    public static String text(byte[] data) {
        int n=data.length;while(n>0&&data[n-1]==0)n--;
        return new String(data,0,n,StandardCharsets.UTF_8);
    }

    public static final class Confirm {
        public final byte[] key, packet;
        Confirm(byte[] key,byte[] packet){this.key=key;this.packet=packet;}
    }

    public static Confirm confirm(byte[] body,int sequence,SecureRandom random) throws Exception {
        if(body.length!=36)throw new IOException("Unexpected DH hello length");
        BigInteger g=new BigInteger(text(Arrays.copyOfRange(body,0,4)),16);
        byte[] pText=Arrays.copyOfRange(body,4,20);
        BigInteger p=new BigInteger(text(pText),16);
        BigInteger peer=new BigInteger(text(Arrays.copyOfRange(body,20,36)),16);
        if(p.signum()<=0||p.bitLength()>64||g.compareTo(BigInteger.ONE)<=0||g.compareTo(p)>=0
                ||peer.compareTo(BigInteger.ONE)<=0||peer.compareTo(p)>=0)throw new IOException("Invalid DH values");
        BigInteger exponent;
        do {exponent=new BigInteger(p.bitLength(),random);}
        while(exponent.compareTo(BigInteger.valueOf(2))<=0||exponent.compareTo(p.subtract(BigInteger.valueOf(2)))>=0);
        String pub=g.modPow(exponent,p).toString(16).toUpperCase(java.util.Locale.ROOT);
        byte[] key=Arrays.copyOf(peer.modPow(exponent,p).toString(16).toUpperCase(java.util.Locale.ROOT)
                .getBytes(StandardCharsets.US_ASCII),16);
        byte[] confirmation=new byte[32];
        byte[] publicBytes=String.format(java.util.Locale.ROOT,"%16s",pub).replace(' ','0').getBytes(StandardCharsets.US_ASCII);
        System.arraycopy(publicBytes,0,confirmation,0,16);
        System.arraycopy(crypt(key,pText,true),0,confirmation,16,16);
        return new Confirm(key,frame(255,18,3,sequence,0,0,confirmation));
    }
}
