"""Synthetic square-paper test pattern; no device access."""
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import math,argparse
parser=argparse.ArgumentParser(description='Generate synthetic square charts without printing.');parser.add_argument('--out',type=Path,default=Path(__file__).resolve().parents[1]/'build/acceptance-square');out=parser.parse_args().out;out.mkdir(parents=True,exist_ok=True)
im=Image.new('RGB',(1040,1040),'white');d=ImageDraw.Draw(im)
def font(n):
 try:return ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',n)
 except OSError:return ImageFont.load_default(size=n)
def text(x,y,s,n=16):d.text((x,y),s,font=font(n),fill='black')
d.rectangle((8,8,1031,1031),outline='black',width=2);d.rectangle((20,20,1019,1019),outline='#999999',width=1)
text(35,32,'3-INCH SQUARE / SYNTHETIC sRGB',30);text(35,74,'1040 x 1040 pixels | colors, tone, detail and orientation',18)
d.polygon([(960,35),(980,70),(940,70)],fill='#ee2200');text(937,74,'TOP',16)
colors=['ff0000','00ff00','0000ff','00ffff','ff00ff','ffff00','ff8000','8000ff','006040','005080','c02050','80c000','f7d8c4','cc926e','805039','f9eeee','edf7ff','f4f2d7','e88ea5','81c7e5','93d6ad','c6b1e2','d8ad55','a58b76']
for i,c in enumerate(colors):
 x=35+(i%6)*162;y=113+(i//6)*90;d.rectangle((x,y,x+150,y+62),fill='#'+c);text(x,y+65,'#'+c.upper(),14)
text(35,479,'21-STEP GRAY / 0 TO 255',16)
for i in range(21):
 x=35+i*46;v=round(255*i/20);d.rectangle((x,505,x+45,551),fill=(v,v,v));text(x+5,555,str(v),12)
for row in range(4):
 y=589+row*26
 for x in range(970):
  v=round(x*255/969);c=(v,v,v) if row==0 else (v,0,0) if row==1 else (0,v,0) if row==2 else (0,0,v);d.line((35+x,y,35+x,y+19),fill=c)
for i,step in enumerate([1,2,3,4,6,8]):
 x=35+i*162;text(x,707,str(step)+' PX LINES',15)
 for a in range(0,150,step*2):d.rectangle((x+a,732,x+min(a+step-1,149),783),fill='black')
 for a in range(0,50,step*2):d.rectangle((x,794+a,x+149,794+min(a+step-1,49)),fill='black')
for i,n in enumerate([10,14,20,28]):text(35,855+i*32,str(n)+'px  AaBb 0123456789',n)
for i,size in enumerate([1,2,4]):
 x=465+i*105;text(x,862,str(size)+'PX',14)
 for yy in range(90):
  for xx in range(90):
   if (xx//size+yy//size)%2==0:im.putpixel((x+xx,885+yy),(0,0,0))
for n in range(72):
 a=2*math.pi*n/72;b=2*math.pi*(n+1)/72;d.polygon([(900,933),(900+70*math.cos(a),933+70*math.sin(a)),(900+70*math.cos(b),933+70*math.sin(b))],fill='black' if n%2==0 else 'white')
d.rectangle((24,1001,36,1013),fill='black');text(45,995,'BOTTOM / black square at left',14)
web=im.copy();ImageDraw.Draw(web).text((815,77),'WEB',font=font(18),fill='black');web.save(out/'square-chart.png')
pixel=im.copy();ImageDraw.Draw(pixel).text((815,77),'PIXEL',font=font(18),fill='black');pixel.save(out/'square-chart.pdf',resolution=1040/3,quality=100,subsampling=0);pixel.save(out/'pixel-expected.png')
print('Prepared synthetic 1040 square PNG and one-page 3-inch PDF; no printing')
