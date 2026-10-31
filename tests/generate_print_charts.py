"""Synthetic sRGB patches and detail targets; not a calibrated reference chart."""
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import math,argparse
parser=argparse.ArgumentParser(description='Generate synthetic print charts without printing.');parser.add_argument('--out',type=Path,default=Path(__file__).resolve().parents[1]/'build/acceptance');out=parser.parse_args().out;out.mkdir(parents=True,exist_ok=True)
font='/System/Library/Fonts/Supplemental/Arial.ttf';bold='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
def f(n,b=False):
 try:return ImageFont.truetype(bold if b else font,n)
 except OSError:return ImageFont.load_default(size=n)
def label(d,xy,text,n=18,fill='#17212b',b=False):d.text(xy,text,font=f(n,b),fill=fill)
def base(route,page):
 im=Image.new('RGB',(1216,912),'#ffffff');d=ImageDraw.Draw(im);d.rectangle((8,8,1207,903),outline='black',width=2);d.rectangle((20,20,1195,891),outline='#aaaaaa',width=1)
 label(d,(35,30),route+' / '+('COLOR + TONE' if page==1 else 'DETAIL + GEOMETRY'),30,b=True);label(d,(35,68),'SYNTHETIC sRGB TEST  |  HALF '+str(page)+' / 2  |  1216 x 912 px',18)
 for x in range(40,1190,40):d.line((x,884,x,894),fill='black',width=1)
 for y in range(110,875,40):d.line((11,y,21,y),fill='black',width=1)
 d.polygon([(1150,35),(1172,70),(1128,70)],fill='black');label(d,(1120,76),'TOP',14)
 return im,d
patches=[('#ff0000','RED'),('#00ff00','GREEN'),('#0000ff','BLUE'),('#00ffff','CYAN'),('#ff00ff','MAGENTA'),('#ffff00','YELLOW'),('#ff8000','ORANGE'),('#8000ff','VIOLET'),('#006040','DARK GREEN'),('#005080','DEEP BLUE'),('#c02050','ROSE'),('#80c000','LIME'),('#f7d8c4','SKIN LIGHT'),('#cc926e','SKIN MID'),('#805039','SKIN DARK'),('#f9eeee','PALE PINK'),('#edf7ff','PALE BLUE'),('#f4f2d7','PALE CREAM'),('#e88ea5','PINK'),('#81c7e5','SKY'),('#93d6ad','MINT'),('#c6b1e2','LAVENDER'),('#d8ad55','GOLD'),('#a58b76','TAUPE')]
def color(route):
 im,d=base(route,1)
 for i,(c,name) in enumerate(patches):
  x=35+(i%6)*192;y=110+(i//6)*119;d.rectangle((x,y,x+177,y+78),fill=c);label(d,(x,y+82),name,14);label(d,(x+107,y+82),c.upper(),12)
 label(d,(35,594),'GRAY STEPS: BLACK TO WHITE',16,b=True)
 for i in range(21):
  x=35+i*54;v=round(i*255/20);d.rectangle((x,620,x+53,672),fill=(v,v,v));label(d,(x+8,678),str(v),13)
 for row,mode in enumerate(['gray','red','green','blue']):
  y=706+row*34
  for x in range(1144):
   v=round(x*255/1143);c=(v,v,v) if mode=='gray' else (v,0,0) if mode=='red' else (0,v,0) if mode=='green' else (0,0,v);d.line((35+x,y,35+x,y+23),fill=c)
 label(d,(35,850),'Check smooth gradients, highlight/shadow separation, neutral gray and distinct color patches.',15)
 return im
def detail(route):
 im,d=base(route,2)
 for i,step in enumerate([1,2,3,4,6,8]):
  x=35+i*192;y=120;label(d,(x,100),str(step)+' PX LINES',16,b=True)
  for a in range(0,176,step*2):d.rectangle((x+a,y,x+min(a+step-1,175),y+109),fill='black')
  for a in range(0,108,step*2):d.rectangle((x,y+124+a,x+175,y+124+min(a+step-1,107)),fill='black')
 for i,size in enumerate([1,2,3,4]):
  x=35+i*165;y=390;label(d,(x,y-25),str(size)+' PX CHECK',15,b=True)
  for yy in range(128):
   for xx in range(128):
    if (xx//size+yy//size)%2==0:im.putpixel((x+xx,y+yy),(0,0,0))
 cx,cy=815,451;r=104
 for n in range(72):
  a=2*math.pi*n/72;b=2*math.pi*(n+1)/72;d.polygon([(cx,cy),(cx+r*math.cos(a),cy+r*math.sin(a)),(cx+r*math.cos(b),cy+r*math.sin(b))],fill='black' if n%2==0 else 'white')
 label(d,(719,560),'72-SECTOR STAR',14)
 d.rectangle((970,375,1165,550),fill='#eeeeee');d.polygon([(980,390),(1045,390),(1102,535),(1037,535)],fill='black');label(d,(975,560),'SLANTED EDGE',14)
 for row,size in enumerate([9,12,16,20,28,36]):
  text=f'{size}px  AaBb 0123456789'+('  FINE DETAIL + EDGE SHARPNESS' if size<=20 else '')
  label(d,(35,590+row*37),text,size)
 for i,v in enumerate([0,4,8,12,16,20,24,32,223,231,239,243,247,251,255]):
  x=730+(i%8)*57;y=610+(i//8)*85;d.rectangle((x,y,x+49,y+49),fill=(v,v,v));label(d,(x+4,y+52),str(v),12)
 label(d,(35,850),'Check fine patterns, small text, ringing/halos, straight edges and complete outer borders.',15)
 return im
for number,route in [('03','MAC'),('04','PIXEL')]:
 pages=[color(route),detail(route)]
 for i,im in enumerate(pages,1):im.save(out/f'{number}-chart-{i}.png')
 pages[0].save(out/f'{number}-{route.lower()}-splice.pdf',save_all=True,append_images=pages[1:],resolution=304,quality=100,subsampling=0)
 sheet=Image.new('RGB',(1216,1824));sheet.paste(pages[0],(0,0));sheet.paste(pages[1],(0,912));sheet.save(out/f'{number}-{route.lower()}-splice-expected.png')
print('Generated two rich, wholly synthetic charts per AirPrint route; no photos, no print calls')
