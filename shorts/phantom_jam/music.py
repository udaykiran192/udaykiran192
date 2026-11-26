"""Generates a soft ambient pad + low road rumble as a background bed."""
import numpy as np,soundfile as sf,json
sr=48000; T=json.load(open('timing.json')); dur=T[-1]['end']+1.0
t=np.arange(int(sr*dur))/sr; out=np.zeros_like(t)
chords=[[110,164.8,220,277.2],[98,146.8,196,246.9],[87.3,130.8,174.6,220],[98,146.8,196,293.7]]
seg=dur/len(chords)
for k,ch in enumerate(chords):
    env=np.clip(1-np.abs((t-(k+0.5)*seg)/(seg*0.75)),0,1)**0.7
    for f in ch:
        for det in (0.997,1.003):
            out+=env*np.sin(2*np.pi*f*det*t+np.random.rand()*6)*0.05
# gentle pulse
out*=0.85+0.15*np.sin(2*np.pi*t*0.5)
# road rumble: lowpassed noise
n=np.random.randn(len(t)); r=np.zeros_like(n); a=0.995
for i in range(1,len(n)): r[i]=a*r[i-1]+(1-a)*n[i]
out+=r*1.2
fade=np.minimum(1,np.minimum(t/1.0,(dur-t)/1.2))
out*=fade; out/=np.abs(out).max(); sf.write('music.wav',(out*0.5).astype(np.float32),sr)
print('ok',dur)
