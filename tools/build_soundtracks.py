"""Synthesize eight ORIGINAL adaptive ambient+rhythm chapter scores (no samples).
Requires NumPy for regeneration only. The game itself uses pygame-ce.
Both layers of each chapter have identical sample lengths for phase-safe looping.
"""
from pathlib import Path
from math import pi
import numpy as np, wave, subprocess
ROOT=Path(__file__).resolve().parents[1]
MUSIC=ROOT/'data'/'music'; OUT=ROOT/'soundtrack_previews';OUT.mkdir(exist_ok=True)
FS=22050
# Tempo, scale root MIDI, harmonic mode, color, timbral character, arpeggio octave.
SPECS=[
 (88,50,'minor','glass',.70),
 (110,45,'minor','metal',.84),
 (120,52,'minor','arc',.87),
 (100,54,'minor','prism',.68),
 (92,48,'minor','water',.59),
 (118,41,'minor','fire',.94),
 (132,46,'minor','collapse',.94),
 (116,50,'major','surface',.73),
]
PROG_MINOR=[(0,3,7),(8,12,15),(5,8,12),(7,10,14)]
PROG_MAJOR=[(0,4,7),(5,9,12),(9,12,16),(7,11,14)]
MELODIES=[(0,7,12,10,7,3,7,5),(0,3,5,7,10,7,5,3),(0,7,10,14,12,10,7,5),
 (0,12,7,15,10,7,3,5),(0,5,7,3,12,10,7,5),(0,3,7,10,12,7,5,3),
 (0,10,12,7,5,3,10,7),(0,4,7,12,16,12,7,9)]

def freq(m):return 440.0*2.0**((m-69)/12)
def add(x,start,signal,gain=1):
    i=max(0,int(start*FS)); n=min(len(x)-i,len(signal))
    if n>0:x[i:i+n]+=signal[:n]*gain

def note(n,duration,kind='sine',attack=.01,release=.2):
    N=max(1,int(duration*FS));t=np.arange(N)/FS;f=freq(n)
    if kind=='metal':
        s=(np.sin(2*pi*f*t)+.44*np.sin(2*pi*f*2.87*t)+.16*np.sin(2*pi*f*4.14*t))/1.6
    elif kind=='glass':
        s=(np.sin(2*pi*f*t)+.23*np.sin(2*pi*f*2.01*t)+.08*np.sin(2*pi*f*4.02*t))/1.31
    elif kind=='prism':
        s=(np.sin(2*pi*f*t)+.18*np.sin(2*pi*f*3*t)+.09*np.sin(2*pi*f*5*t))/1.27
    elif kind=='arc':
        s=(np.sin(2*pi*f*t)+.32*np.sin(2*pi*f*2*t)+.15*np.sin(2*pi*f*3*t))/1.47
    elif kind=='water':
        s=(np.sin(2*pi*f*t)*np.sin(2*pi*.8*t)*.17+np.sin(2*pi*f*t))/1.2
    else:
        s=(np.sin(2*pi*f*t)+.25*np.sin(2*pi*f*2*t)+.09*np.sin(2*pi*f*3*t))/1.34
    env=np.minimum(1,t/max(.001,attack)) * np.minimum(1,np.maximum(0,(duration-t))/max(.001,release))
    return (s*env).astype(np.float32)

def synth(ch,bpm,root,mode,color,intensity):
    beat=60.0/bpm; duration=32*beat;N=int(round(duration*FS));duration=N/FS
    quiet=np.zeros(N,dtype=np.float32);rhythm=np.zeros_like(quiet)
    chords=PROG_MAJOR if mode=='major' else PROG_MINOR
    rng=np.random.default_rng(8274+ch)
    # Evolving four-voice pad chords, played as slow, breathy phrases. 2 bars per phrase.
    for idx in range(4):
        start=idx*8*beat; length=8*beat
        chord=chords[(idx+ch-1)%4]
        for m in chord:
            s=note(root+m-12,length,color,attack=.45,release=.55)
            # Gentle, wide filter-like movement differentiates scenes.
            j=np.arange(len(s))/FS
            s*=.67+.33*np.sin(2*pi*(.06+.017*ch)*j+idx)**2
            add(quiet,start,s,.095)
            add(quiet,start+beat*.02,s,.033)
    # Panning-free mono musical bells with melodic pauses and repeating recognizable motif.
    motif=MELODIES[ch-1]
    for b in range(64):
        idx=b%8
        if (b+ch)%7==3:continue
        x=b*beat/2
        degree=motif[idx]
        pitch=root+degree+(12 if ch in (3,4,7,8) else 0)
        if (b//8)%2==1 and idx in (2,6):pitch+=2
        s=note(pitch,beat*(.4 if ch in (2,6,7) else .72),color,attack=.007,release=.16)
        add(quiet,x,s,.11*intensity)
        if ch in (1,4,5,8):add(quiet,x+beat*.42,s,.024)
    # Bass line in quiet layer has long phrases, complementing adaptive percussion.
    for b in range(16):
        ci=b//4
        note_num=root+chords[ci][0]-24
        s=note(note_num,beat*1.7,'sine',attack=.03,release=.3)
        add(quiet,b*2*beat,s,.09)
    # Powered-layer punch and percussion, tailored to chapter mood.
    for b in range(32):
        start=b*beat
        # Rounded low kick
        if b%4 in (0,2) or (ch>=6 and b%4==3):
            t=np.arange(int(.24*FS))/FS
            ph=2*pi*(56*t+58*(1-np.exp(-t*27))/27)
            k=np.sin(ph)*np.exp(-t*19)
            add(rhythm,start,k,.25*intensity)
        if b%4 in (1,3):
            t=np.arange(int(.18*FS))/FS
            n=rng.standard_normal(len(t))
            # Low-tech metallic snare via band tone and filtered white noise
            s=(.3*np.sin(2*pi*190*t)+.5*(n[1:] if False else n))*np.exp(-t*22)
            add(rhythm,start,s,.09*intensity)
        if ch not in (1,5) or b%2==0:
            for eighth in (0,.5):
                t=np.arange(int(.085*FS))/FS
                n=rng.standard_normal(len(t))
                hp=np.r_[0,np.diff(n)]
                hat=np.clip(hp,-2,2)*np.exp(-t*75)
                add(rhythm,start+eighth*beat,hat,.017*intensity)
        # Metallic factory pulse / sparkling electrical sequencer / cascading water ticks
        if b%2==0:
            cc=chords[(b//8)%4]
            n=root+cc[0]-12
            add(rhythm,start,note(n,beat*.7,'arc',release=.15),.09*intensity)
        if ch in (2,3,6,7):
            for sub in (0.25,.75):
                add(rhythm,start+sub*beat,note(root+12+motif[b%8],beat*.18,color,release=.06),.035*intensity)
    # Distinctive timbres: gentle harmonic sway / rain drop / staccato servo / epic final arpeggios.
    if ch==5:
        for j in range(95):
            t=rng.uniform(.1,duration-.5)
            add(quiet,t,note(root+12+rng.choice([0,3,7,10,12]),.37,'water',release=.28),.031)
    if ch==8:
        for j in range(16):
            start=j*2*beat
            add(rhythm,start,note(root+19,1.5*beat,'glass',attack=.15,release=.3),.03)
    if ch==7:
        for j in range(8):
            start=(j*4+1)*beat
            add(rhythm,start,note(root+24,.7,'metal',release=.18),.051)
    # Seam treatment: independent layers remain exactly sample-matched; both play from sample zero.
    fades=int(.065*FS); edge=np.linspace(0,1,fades,dtype=np.float32)
    for track in (quiet,rhythm):
        track[:fades]*=edge; track[-fades:]*=edge[::-1]
        track[:]=np.tanh(track*1.42)
    return quiet,rhythm

def write(path,x):
    a=np.int16(np.clip(x,-1,1)*32767)
    with wave.open(str(path),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(FS);w.writeframes(a.tobytes())

if __name__=='__main__':
    MUSIC.mkdir(exist_ok=True,parents=True)
    for i,sp in enumerate(SPECS,1):
        q,r=synth(i,*sp)
        write(MUSIC/f'chapter_{i}_quiet.wav',q)
        write(MUSIC/f'chapter_{i}_rhythm.wav',r)
        # Single stereo-free source preview from identical layers, also used in gallery mix.
        write(OUT/f'Chapter_{i:02d}_preview.wav',np.tanh(q*.84+r*.66))
        # Compact additional preview file for easy listening on any device.
        wav=OUT/f'Chapter_{i:02d}_preview.wav'; ogg=OUT/f'Chapter_{i:02d}_preview.ogg'
        subprocess.run(['ffmpeg','-loglevel','error','-y','-i',str(wav),'-c:a','libvorbis','-qscale:a','5',str(ogg)],check=True)
        wav.unlink()
        print(f'chapter {i}: {len(q)/FS:.2f} s | {sp[0]} BPM')
