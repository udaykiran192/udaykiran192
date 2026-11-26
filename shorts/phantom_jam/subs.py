"""Word-by-word captions + hook/title text as an ASS subtitle file (1080x1920)."""
import json,re
T=json.load(open('timing.json'))
KEY={'jam','brakes','harder.','harder','backwards,','wave.','stop,','phantom','gap,','calm','entire','nothing.','second.','cause.'}
def ts(t):
    h=int(t//3600); m=int(t%3600//60); s=t%60
    return f"{h}:{m:02d}:{s:05.2f}"
head="""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Poppins ExtraBold,82,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,6,4,2,60,60,560,1
Style: Hook,Anton,150,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,2,0,1,9,6,8,50,50,250,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
ev=[]
Y='{\\c&H00D7FF&}'  # yellow (BGR)
G='{\\c&H66FF33&}'  # green
W='{\\c&HFFFFFF&}'
for i,m in enumerate(T):
    words=m['text'].split(); dur=m['end']-m['start']
    w8=[len(w)+2 for w in words]; tot=sum(w8); t=m['start']; times=[]
    for w,k in zip(words,w8): times.append((t,t+dur*k/tot)); t+=dur*k/tot
    # chunk: up to 3 words, break after punctuation
    chunks=[];cur=[]
    for j,w in enumerate(words):
        cur.append(j)
        if len(cur)==3 or re.search(r'[.,?!]$',w) or (len(cur)==2 and len(words[j])>8): chunks.append(cur);cur=[]
    if cur: chunks.append(cur)
    for c in chunks:
        a=times[c[0]][0]; b=times[c[-1]][1]
        if c[-1]==len(words)-1: b=min(b+0.2, T[i+1]['start'] if i+1<len(T) else b+0.6)
        txt=' '.join((Y+words[j].upper()+W) if words[j].lower() in KEY else words[j].upper() for j in c)
        ev.append(f"Dialogue: 1,{ts(a)},{ts(b)},Cap,,0,0,0,,{{\\fscx85\\fscy85\\t(0,90,\\fscx100\\fscy100)}}{txt}")
def hook(a,b,txt):
    ev.append(f"Dialogue: 2,{ts(a)},{ts(b)},Hook,,0,0,0,,{{\\fad(120,150)\\fscx70\\fscy70\\t(0,160,\\fscx100\\fscy100)}}{txt}")
s=[m['start'] for m in T]
hook(0.0,s[2]-0.1,'WHERE DID THIS\\N'+Y+'JAM'+W+' COME FROM?')
hook(s[7],s[8]-0.15,Y+'PHANTOM\\NTRAFFIC JAM')
hook(s[8]+0.4,s[9]-0.1,'THE FIX:\\N'+G+'BIGGER GAP')
hook(s[9],T[-1]['end']+0.9,G+'WAVE\\NABSORBED')
open('captions.ass','w').write(head+'\n'.join(ev)+'\n')
print(len(ev),'events')
