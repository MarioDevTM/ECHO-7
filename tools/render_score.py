"""Render an original synth motif and rhythmic counterlayer for ECHO-7. No source recording used."""
import math, wave
from pathlib import Path
import numpy as np

SR=22050
BPM=112
BEAT=60/BPM
BARS=8
DURATION=BARS*4*BEAT
N=int(round(DURATION*SR))
RNG=np.random.default_rng(7007)
OUTPUT=Path('data/music')
OUTPUT.mkdir(exist_ok=True,parents=True)
# All five arrangements use a single original melody's contour; changes are harmonic timbres, not a quote.
MOTIF=[0,3,7,5,10,7,3,2,0,-2,3,5,7,5,3,0]
BASE_ROOTS=[62,57,65,60,62]
HARMONIES=[(-2,3,7), (0,3,7), (0,4,7), (0,3,9), (0,5,9)]

def hz(midi):return 440.0*2**((midi-69)/12)

def note(buf,at,length,midi,amp=0.1,timbre='bell'):
    start=int(round(at*SR))
    end=min(N,start+int(length*SR))
    if end<=start:return
    t=np.arange(end-start,dtype=np.float64)/SR
    f=hz(midi)
    attack=np.minimum(1,t/0.012)
    release=np.minimum(1,(length-t)/0.06).clip(0,1)
    if timbre=='bell':
        wave_=(np.sin(2*np.pi*f*t)+0.32*np.sin(2*np.pi*2.01*f*t)+
               0.13*np.sin(2*np.pi*3.99*f*t))
        env=attack*np.exp(-2.5*t/max(length,0.1))*release
    elif timbre=='pad':
        wave_=(np.sin(2*np.pi*f*t)*0.8 + np.sin(2*np.pi*f*1.006*t)*0.3)
        env=np.minimum(1,t/0.32)*np.minimum(1,(length-t)/0.38).clip(0,1)
    elif timbre=='pulse':
        wave_=(np.sin(2*np.pi*f*t)+0.24*np.sin(2*np.pi*3*f*t)+0.1*np.sin(2*np.pi*5*f*t))
        env=attack*np.exp(-1.2*t/max(length,0.1))*release
    else: # bass
        wave_=np.sin(2*np.pi*f*t)*0.8+np.sin(2*np.pi*2*f*t)*0.2
        env=attack*np.minimum(1,(length-t)/0.05).clip(0,1)
    buf[start:end]+=wave_*env*amp

def kick(buf,at,amp):
    duration=.31
    start=int(round(at*SR));end=min(N,start+int(duration*SR))
    t=np.arange(end-start)/SR
    # descending pitch kick, entirely synthesized
    wave_=np.sin(2*np.pi*(58*t+35*(1-np.exp(-23*t))/23))
    buf[start:end]+=wave_*(np.exp(-17*t))*amp

def snare(buf,at,amp):
    duration=.18
    start=int(round(at*SR));end=min(N,start+int(duration*SR))
    t=np.arange(end-start)/SR
    noise=RNG.standard_normal(len(t))
    # Highpassed component, synthetic clap
    hp=noise-np.convolve(noise,np.ones(21)/21,mode='same')
    buf[start:end]+=hp*np.exp(-25*t)*amp

def hat(buf,at,amp):
    duration=.08
    start=int(round(at*SR));end=min(N,start+int(duration*SR))
    t=np.arange(end-start)/SR
    noise=RNG.standard_normal(len(t))
    hp=noise-np.convolve(noise,np.ones(9)/9,mode='same')
    buf[start:end]+=hp*np.exp(-48*t)*amp

def make(ch):
    base=np.zeros(N,dtype=np.float64)
    layer=np.zeros(N,dtype=np.float64)
    root=BASE_ROOTS[ch-1]
    harmony=HARMONIES[ch-1]
    # Different voices: foundry's tight pulses, flood's airy glass, core's sustained pads
    cadence=[.48,.30,.36,.65,.45][ch-1]
    for bar in range(BARS):
        chord_root=root + [0,-2,3,0][bar%4]
        for interval in harmony:
            note(base,bar*4*BEAT,4*BEAT,chord_root-12+interval,
                 .020+(0.011 if ch==4 else 0), 'pad')
        for q in range(8):
            step=bar*8+q
            idx=step%len(MOTIF)
            # sparse, recognizable motif with a short answer in alternating bars
            if q%2==0 or (bar%2 and q==5):
                midi=root+MOTIF[idx]
                note(base,(bar*4+q/2)*BEAT,BEAT*cadence,midi,
                     [.060,.056,.066,.055,.060][ch-1],'bell')
            if q%2 == 1:
                note(layer,(bar*4+q/2)*BEAT,BEAT*.38,
                     root+MOTIF[(idx+2)%len(MOTIF)]-12, .025, 'pulse')
        for beat in range(4):
            when=(bar*4+beat)*BEAT
            bass_note=chord_root-24 + (7 if beat==3 else 0)
            note(base,when,BEAT*.72,bass_note,.058,'bass')
            kick(layer,when,.16 if ch!=4 else .10)
            if beat in (1,3):snare(layer,when,.060 if ch!=4 else .040)
            hat(layer,when,.029)
            hat(layer,when+BEAT/2,.018)
            if ch in (2,5) and beat==3:
                note(layer,when+BEAT/2,BEAT*.45,chord_root+12,.036,'pulse')
    # Smooth cyclic end with short fade; rhythmic offsets remain sample-synchronized.
    fade=int(.035*SR)
    for buf in (base,layer):
        buf[:fade]*=np.linspace(0,1,fade)
        buf[-fade:]*=np.linspace(1,0,fade)
    return base,layer

def save(name,a):
    peak=max(0.8,float(np.max(np.abs(a))))
    pcm=np.int16(np.clip(a/peak*0.84,-1,1)*32767)
    with wave.open(str(OUTPUT/name),'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(SR);f.writeframes(pcm.tobytes())

for chapter in range(1,6):
    quiet,rhythm=make(chapter)
    save(f'chapter_{chapter}_quiet.wav',quiet)
    save(f'chapter_{chapter}_rhythm.wav',rhythm)
# Resolved finale: phrase lifted to a luminous major-key answer; separately authored, no track sample.
final=np.zeros(N,dtype=np.float64)
for bar in range(BARS):
    r=62+[0,5,7,12][bar%4]
    for i in (0,4,7):note(final,4*bar*BEAT,3.7*BEAT,r-12+i,.048,'pad')
    for q in range(4):
        note(final,(4*bar+q)*BEAT,BEAT*.87,r+[0,4,7,12][q],.10,'bell')
    if bar%2==1:
        note(final,4*bar*BEAT+2*BEAT,BEAT*1.7,r+16,.045,'pad')
fade=int(.04*SR);final[:fade]*=np.linspace(0,1,fade);final[-fade:]*=np.linspace(1,0,fade)
save('surface_resolution.wav',final)
print('Rendered',len(list(OUTPUT.glob('*.wav'))),'original loops',round(DURATION,2),'seconds each')
