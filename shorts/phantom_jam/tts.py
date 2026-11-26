import json,sys,numpy as np,soundfile as sf
from kokoro_onnx import Kokoro
k=Kokoro('/tmp/claude-0/models/kokoro.onnx','/tmp/claude-0/models/voices.bin')
voice=sys.argv[1] if len(sys.argv)>1 else 'am_michael'
lines=json.load(open('script.json'));out=[];t=0.0;meta=[];sr=24000
pad=np.zeros(int(0.25*sr),dtype=np.float32)
for i,l in enumerate(lines):
    a,sr=k.create(l,voice=voice,speed=1.08,lang='en-us')
    # trim silence
    nz=np.where(np.abs(a)>0.01)[0]; a=a[max(nz[0]-200,0):nz[-1]+800]
    meta.append({'text':l,'start':t,'end':t+len(a)/sr}); out+= [a,pad]; t+= (len(a)+len(pad))/sr
sf.write('voice.wav',np.concatenate(out),sr); json.dump(meta,open('timing.json','w'),indent=1); print(t)
