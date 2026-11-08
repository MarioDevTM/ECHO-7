"""Build reproducible original background plates and ECHO-7 astronaut pixel sprites.
Requires Pillow ONLY to regenerate; runtime simply loads PNG files with pygame-ce.
These assets are intentionally not copied from the design reference concept boards.
"""
from PIL import Image, ImageDraw, ImageFilter
from pathlib import Path
import random, math
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data'/'art'
W,H=1280,720
THEMES=[
 ('awakening',(8,20,31),(23,42,58),(56,143,156),'#54cfe8'),
 ('mechanical',(29,16,14),(56,29,21),(130,72,43),'#f3a04e'),
 ('power',(9,16,35),(18,37,68),(39,77,105),'#4abaff'),
 ('optical',(21,12,36),(40,25,66),(81,42,106),'#dc6efa'),
 ('flood',(8,22,34),(14,50,65),(26,90,106),'#45dfe9'),
 ('furnace',(35,12,13),(68,26,19),(133,55,29),'#ff8945'),
 ('spire',(17,12,30),(53,31,55),(105,49,69),'#ff797c'),
 ('surface',(10,21,43),(33,59,87),(74,92,124),'#72ddfc'),
]

def lerp(a,b,t):return tuple(int(a[k]*(1-t)+b[k]*t) for k in range(3))
def color(v):return tuple(int(v[i:i+2],16) for i in (1,3,5))
def polyline(d,points,fill,width=1):d.line(points,fill=fill,width=width,joint='curve')
def glow(overlay,x,y,r,tint,alpha):
    # Layering low-opacity circles avoids GPU postprocessing at runtime.
    for rad in range(r,0,-max(6,r//12)):
        k=1-rad/r
        a=max(0,int(alpha*(0.03+0.09*k)))
        overlay.ellipse((x-rad,y-rad,x+rad,y+rad),fill=(*tint,a))

def gear(d,cx,cy,r,teeth,body,edge):
    for i in range(teeth):
        a=2*math.pi*i/teeth
        x=cx+math.cos(a)*r; y=cy+math.sin(a)*r
        d.rectangle((x-10,y-10,x+10,y+10),fill=body)
    d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=body,outline=edge,width=5)
    d.ellipse((cx-r*.76,cy-r*.76,cx+r*.76,cy+r*.76),outline=edge,width=4)
    d.ellipse((cx-r*.25,cy-r*.25,cx+r*.25,cy+r*.25),fill=(15,23,36),outline=edge,width=4)
    for a in range(0,360,45):
        th=math.radians(a)
        d.line((cx+math.cos(th)*r*.28,cy+math.sin(th)*r*.28,cx+math.cos(th)*r*.73,cy+math.sin(th)*r*.73),fill=edge,width=8)

def building(d,x,top,w,fill,outline):
    d.rectangle((x,top,x+w,720),fill=fill,outline=outline,width=2)
    for xx in range(x+11,x+w-10,28):
        for yy in range(top+20,690,43):
            if ((xx+yy)//11)%5 != 1:
                d.rectangle((xx,yy,xx+12,yy+18),fill=tuple(min(255,z+22) for z in fill))

def scene(ch):
    name,dark,mid,near,acc=THEMES[ch-1]; a=color(acc); rng=random.Random(740+ch)
    im=Image.new('RGB',(W,H));pix=im.load()
    for y in range(H):
        base=lerp(dark,mid,max(0,min(1,y/H))*.8)
        for x in range(W):
            shade=6*math.sin(x/157.0)*math.sin(y/181.0)
            pix[x,y]=tuple(max(0,min(255,int(q+shade))) for q in base)
    d=ImageDraw.Draw(im)
    # Background stars/pollution/haze are different from the gameplay hitboxes.
    for i in range(125):
        x=rng.randrange(W);y=rng.randrange(30,620);v=rng.randrange(32,80)
        d.point((x,y),fill=(v//2,v//2,v))
    for i in range(8):
        x=i*190-70; d.rectangle((x,70,x+23,630),fill=lerp(dark,near,.3))
        d.line((x+23,95,x+115,30),fill=lerp(dark,near,.45),width=6)
    # Large chapter-specific distant machinery / landscapes.
    if name=='awakening':
        d.rectangle((110,118,555,420),fill=(17,39,61),outline=(45,88,113),width=10)
        d.rectangle((133,141,535,390),fill=(22,75,107))
        for i in range(9):
            x=140+48*i; d.line((x,142,x,390),fill=(42,107,135),width=4)
        d.line((130,280,535,280),fill=(49,105,132),width=5)
        for x in (790,980):
            d.rounded_rectangle((x,170,x+140,450),radius=12,fill=(22,45,57),outline=(70,126,140),width=5)
            d.rectangle((x+40,202,x+102,245),fill=(28,126,160),outline=(65,222,228),width=3)
        d.text((800,260),'LAB 07',fill=(113,175,184))
        for i in range(35):
            x=rng.randrange(W);start=rng.randrange(-40,80);ln=rng.randrange(50,210)
            d.line((x,start,x+12,start+ln//2,x-12,start+ln),fill=(33,89,65),width=rng.randrange(2,6))
            for j in range(3):
                yy=start+ln*(j+1)//4;d.ellipse((x-10,yy-4,x+3,yy+5),fill=(35,99,68))
    elif name=='mechanical':
        gear(d,350,360,195,16,(66,42,34),(164,91,50));gear(d,810,275,125,12,(65,43,37),(178,92,47))
        gear(d,1065,435,165,16,(45,35,30),(113,64,42))
        for y in [115,190,555]:
            d.rectangle((0,y,W,y+16),fill=(82,50,39),outline=(183,97,56),width=3)
        for x in range(75,1280,135):
            d.line((x,0,x+6,200),fill=(80,58,52),width=9)
            d.ellipse((x-13,180,x+24,215),fill=(91,51,39),outline=(179,95,56),width=3)
    elif name=='power':
        for x in (190,425,702,980):
            d.rectangle((x-35,165,x+68,530),fill=(23,53,79),outline=(73,132,166),width=5)
            for y in range(192,505,65):
                d.ellipse((x-20,y,x+53,y+35),fill=(18,42,66),outline=(67,160,214),width=4)
        for x,y in [(240,253),(480,290),(754,220),(1000,360)]:
            d.line((x,y,x+105,y-60,x+180,y+4),fill=(44,116,174),width=5)
            d.line((x,y,x+95,y-57,x+180,y+4),fill=(111,220,255),width=2)
        d.line((0,470,1280,470),fill=(51,96,144),width=10)
    elif name=='optical':
        for x in (60,400,805,1100):
            d.rounded_rectangle((x,144,x+100,480),radius=14,fill=(33,26,59),outline=(108,67,140),width=6)
            d.ellipse((x+20,175,x+80,235),fill=(90,46,129),outline=(200,91,237),width=6)
        d.ellipse((470,200,805,535),fill=(29,20,53),outline=(127,82,175),width=13)
        d.ellipse((510,240,765,492),fill=(44,37,93),outline=(199,102,247),width=8)
        polyline(d,[(520,354),(700,340),(780,265),(1050,265)],(142,65,177),6)
        polyline(d,[(520,353),(700,339),(780,264),(1050,264)],(251,116,255),2)
    elif name=='flood':
        for y in (130,275,420):
            d.line((0,y,1280,y),fill=(38,98,109),width=35)
            d.line((0,y-12,1280,y-12),fill=(67,162,163),width=6)
        gear(d,920,374,170,10,(24,72,81),(62,161,179))
        d.rectangle((0,490,1280,715),fill=(9,66,96))
        for y in range(493,680,23):d.line((0,y,1280,y),fill=(24,109,139),width=2)
        for x in range(30,1280,92):
            d.arc((x,485,x+65,500),190,345,fill=(80,189,214),width=2)
    elif name=='furnace':
        for x in (110,475,935):
            d.rectangle((x,40,x+80,570),fill=(77,40,31),outline=(152,69,40),width=8)
            for yy in range(120,550,80):d.rectangle((x+16,yy,x+66,yy+30),fill=(164,59,24))
        d.ellipse((480,190,920,600),fill=(70,27,23),outline=(159,75,43),width=17)
        d.ellipse((555,250,850,575),fill=(170,63,32),outline=(245,117,49),width=12)
        for x in (610,650,690,730,770):
            d.rectangle((x,275,x+23,600),fill=(234,116,30))
            d.rectangle((x+6,290,x+14,595),fill=(255,190,72))
        for i in range(100):
            x=rng.randrange(W);y=rng.randrange(250,720)
            d.line((x,y,x+3,y-12),fill=(rng.randrange(175,255),80,38),width=2)
    elif name=='spire':
        d.polygon([(0,380),(110,320),(220,355),(290,190),(410,300),(550,180),(700,355),(870,170),(1050,325),(1150,210),(1280,330),(1280,720),(0,720)],fill=(68,38,58))
        for x,y in [(120,350),(500,190),(780,240),(1030,350)]:
            d.line((x-160,y+230,x+220,y-50),fill=(91,64,82),width=20)
            d.line((x-160,y+225,x+220,y-54),fill=(178,87,92),width=3)
        d.polygon([(0,540),(210,480),(460,580),(640,490),(850,620),(1050,530),(1280,580),(1280,720),(0,720)],fill=(39,24,48))
    else:
        d.ellipse((920,75,1100,255),fill=(176,205,218))
        d.ellipse((953,95,1094,238),fill=(194,217,227))
        d.polygon([(0,470),(160,315),(310,460),(540,260),(680,480),(850,340),(1020,500),(1180,390),(1280,470),(1280,720),(0,720)],fill=(37,65,94))
        d.polygon([(0,550),(210,410),(450,560),(720,390),(965,565),(1180,470),(1280,530),(1280,720),(0,720)],fill=(31,54,79))
        for x in (80,390,750,1070):
            d.rectangle((x,220,x+78,550),fill=(30,57,85),outline=(81,138,170),width=5)
            d.rectangle((x+10,250,x+66,335),fill=(23,102,130))
        d.line((0,535,1280,535),fill=(68,106,130),width=8)
    # Common foreground cable trays, dark work surfaces and seam details.
    for x in range(35,1280,185):
        y=555 + ((x//185)%2)*25
        d.rectangle((x,y,x+90,y+26),fill=lerp(dark,near,.7),outline=near,width=3)
        for xx in range(x+7,x+85,17):d.line((xx,y+5,xx,y+22),fill=lerp(near,(120,160,180),.2),width=2)
    d.rectangle((0,620,W,720),fill=lerp(dark,mid,.63))
    d.line((0,620,W,620),fill=lerp(near,a,.22),width=4)
    for x in range(0,W,82):
        d.rectangle((x,646,x+78,708),outline=lerp(dark,near,.68),width=2)
        d.ellipse((x+9,650,x+12,653),fill=lerp(near,a,.5))
    # Neon atmospheric signs behind actual gameplay geometry.
    for idx in range(5):
        x=120+idx*250+rng.randrange(-35,35);y=rng.randrange(150,425)
        d.rectangle((x,y,x+30,y+10),fill=lerp(dark,a,.27))
        d.line((x+4,y+5,x+23,y+5),fill=lerp(a,near,.3),width=2)
    overlay=Image.new('RGBA',(W,H),(0,0,0,0));gd=ImageDraw.Draw(overlay,'RGBA')
    for i in range(8):
        xx=rng.randint(60,1200); yy=rng.randint(150,520);glow(gd,xx,yy,75,a,65)
    overlay=overlay.filter(ImageFilter.GaussianBlur(30))
    im=Image.alpha_composite(im.convert('RGBA'),overlay)
    # vignette, leaving the center relatively readable.
    vign=Image.new('RGBA',(W,H));vd=ImageDraw.Draw(vign,'RGBA')
    for i in range(18):
        alpha=int(i*.7)
        vd.rectangle((i*12,i*7,W-i*12,H-i*7),outline=(2,5,12,alpha),width=10)
    im=Image.alpha_composite(im,vign)
    (OUT/'backgrounds').mkdir(parents=True,exist_ok=True)
    im.convert('RGB').save(OUT/'backgrounds'/f'chapter_{ch:02d}.png',optimize=True)

# 36x56 sprites are drawn at native pixel resolution with transparent margins.
# Geometry is visual only: the actual character collision box stays 26x46.
INK=(9,18,35,255); WHITE=(233,247,255,255);HILITE=(255,255,255,255);SHADOW=(139,165,197,255); BLUE=(0,209,253,255); DEEP=(3,68,126,255)
def bot(state,phase=0):
    im=Image.new('RGBA',(36,56),(0,0,0,0));d=ImageDraw.Draw(im)
    step=1 if phase%4==1 else -1 if phase%4==3 else 0
    leap=state=='jump';fall=state=='fall';land=state=='land'; run=state=='run'; interact=state=='interact'
    bob=(-1 if run and phase%2 else 0) + (2 if land else 0)
    d.rounded_rectangle((7,19+bob,28,43+bob),radius=6,fill=INK)
    d.rounded_rectangle((9,20+bob,26,40+bob),radius=5,fill=WHITE)
    d.rectangle((14,30+bob,22,37+bob),fill=SHADOW)
    d.rectangle((16,29+bob,23,35+bob),fill=WHITE)
    # backpack and its warning indicator
    d.rounded_rectangle((5,24+bob,10,38+bob),radius=2,fill=INK)
    d.rectangle((6,28+bob,8,33+bob),fill=(83,142,160,255))
    # bent running arms, small cartoon proportions
    d.rounded_rectangle((25,23+bob+(2 if run and step<0 else 0),32,34+bob+(2 if run and step<0 else 0)),radius=3,fill=INK)
    d.rectangle((27,25+bob,31,31+bob),fill=WHITE)
    d.rounded_rectangle((3,25+bob+(2 if run and step>0 else 0),10,35+bob+(2 if run and step>0 else 0)),radius=3,fill=INK)
    d.rectangle((5,27+bob,9,31+bob),fill=SHADOW)
    # boots
    left=step*3 if run else (-2 if leap else 2 if fall else 0)
    right=-step*3 if run else (3 if leap else -2 if fall else 0)
    for x,off in [(10,left),(22,right)]:
        legbottom=48+bob + (off if run else 0)
        d.rectangle((x,39+bob,x+4,legbottom),fill=INK)
        d.rectangle((x+1,40+bob,x+3,legbottom-2),fill=WHITE)
        d.rounded_rectangle((x-2,legbottom-3,x+7,legbottom+2),radius=2,fill=INK)
        d.rectangle((x,legbottom-3,x+6,legbottom-1),fill=SHADOW)
    # generous large round helmet: approved white-cyan robot aesthetic
    d.rounded_rectangle((5,4+bob,30,27+bob),radius=8,fill=INK)
    d.rounded_rectangle((7,6+bob,28,25+bob),radius=7,fill=WHITE)
    d.line((9,9+bob,16,8+bob),fill=HILITE,width=2)
    d.rounded_rectangle((15,12+bob,29,22+bob),radius=4,fill=INK)
    d.rounded_rectangle((16,13+bob,28,21+bob),radius=3,fill=DEEP)
    d.rectangle((19,14+bob,27,17+bob),fill=BLUE)
    d.line((20,14+bob,26,14+bob),fill=(166,255,255,255),width=1)
    d.point((15,23+bob),fill=(101,141,178,255))
    if interact:
        d.ellipse((31,20,35,24),fill=(68,240,227,255))
    if state=='death':
        # visible broken telemetry flash; normal death animation is handled by particles.
        d.line((15,13+bob,29,20+bob),fill=(255,128,93,255),width=2)
    return im

def make_sprites():
    dest=OUT/'player';dest.mkdir(exist_ok=True,parents=True)
    for state,count in [('idle',2),('run',4),('jump',1),('fall',1),('land',1),('interact',1),('death',1)]:
        for frame in range(count):bot(state,frame).save(dest/f'{state}_{frame}.png')

if __name__=='__main__':
    for i in range(1,9):scene(i)
    make_sprites()
    print('Created 8 original chapter backgrounds and 11 robot frames in',OUT)
