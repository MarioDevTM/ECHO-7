"""Generate three original, seam-faded exploration loops for chapters 6-8.

Uses only Python's standard library. Safe to re-run on a distribution build.
"""
import math
import wave
from pathlib import Path

OUT=Path(__file__).resolve().parents[1]/'data'/'music'
SR=22050; SECONDS=16; N=SR*SECONDS
CHORDS={
 6: [[110.0,138.59,164.81],[116.54,146.83,174.61],[98,123.47,146.83],[103.83,130.81,155.56]],
 7: [[130.81,164.81,196],[123.47,155.56,185],[146.83,185,220],[110,146.83,174.61]],
 8: [[146.83,185,220],[164.81,207.65,246.94],[174.61,220,261.63],[196,246.94,293.66]],
}

def make(ch,layer):
    import array
    notes=CHORDS[ch];buf=array.array('h')
    # 4 long 4-second phrases with cyclic triadic bass and a restrained rhythmic pulse.
    # Stereo effects deliberately avoided; game's existing mixer is mono 22050 Hz.
    for i in range(N):
        t=i/SR
        phrase=min(3,int(t//4))
        chord=notes[phrase]
        voice=sum(math.sin(t*2*math.pi*f) for f in chord)/3
        pad=(.55*voice+.27*math.sin(t*2*math.pi*chord[0]/2))
        trem=.78+.22*math.sin(2*math.pi*t/8)
        if layer=='quiet':
            sample=pad*trem*.18
        else:
            beat=t%(.5 if ch==6 else .375)
            click=math.sin(2*math.pi*(85+ch*7)*t)*math.exp(-beat*28)
            sparkle=math.sin(2*math.pi*chord[2]*2*t)*(.4+.6*math.sin(2*math.pi*t/2)**2)
            sample=(click*.14+sparkle*.042)*(.85+.15*math.sin(2*math.pi*t/4))
        # avoid a transient at the loop boundary
        fade=min(1.,t/.06,(SECONDS-t)/.06)
        v=int(max(-1.,min(1.,sample*max(0,fade)))*32767)
        buf.append(v)
    OUT.mkdir(parents=True,exist_ok=True)
    p=OUT/f'chapter_{ch}_{layer}.wav'
    with wave.open(str(p),'wb') as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(SR);wav.writeframes(buf.tobytes())
    print(p.name)

for chapter in CHORDS:
 for layer in ('quiet','rhythm'): make(chapter,layer)
