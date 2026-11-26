"""Collision-free 'designed' phantom-jam wave.
Each car follows a speed dip; dips grow car by car (amplification).
Each car's braking onset is solved so the gap to the car ahead never drops below a target."""
import numpy as np, json
N=46; L=4.6; DT=1/60; TEND=44; VI=20.0; GAP0=18.0
t=np.arange(0,TEND,DT)
def ss(u): u=np.clip(u,0,1); return u*u*(3-2*u)
def dip(c,D,up,hold,dn):
    return D*(ss((t-c)/up)-ss((t-c-up-hold)/dn))
def solve(params,gap0s):
    X=[];V=[];C=[]
    for i,(D,up,hold,dn,target,_f) in enumerate(params):
        if i==0:
            v=VI-dip(2.0,D,up,hold,dn); x=np.cumsum(v)*DT
            X.append(x);V.append(v);C.append(2.0);continue
        lo,hi=X[-1].__len__()*0, 20.0
        base=-sum(gap0s[1:i+1])-i*L
        def mingap(c):
            v=VI-dip(c,D,up,hold,dn); x=base+np.cumsum(v)*DT
            return (X[-1]-x-L).min(),x,v
        lo,hi=0.0,40.0
        for _ in range(50):   # later onset -> smaller min gap
            m=(lo+hi)/2
            if mingap(m)[0]>target: lo=m
            else: hi=m
        if params[i][5] is not None:
            cc=C[-1]+params[i][5]
            if mingap(cc)[0]>=target: lo=cc
        g,x,v=mingap(lo); X.append(x);V.append(v); C.append(lo)
    X=np.array(X).T; V=np.array(V).T
    A=np.gradient(V,DT,axis=0)
    gaps=X[:,:-1]-X[:,1:]-L
    print('min gap',gaps.min().round(2),'min v',V.min(0).round(1)[::4])
    s=slice(0,None,2)
    return dict(x=X[s].round(3).tolist(),v=V[s].round(3).tolist(),a=A[s].round(3).tolist())
def params(calm=None):
    P=[];G=[]
    for i in range(N):
        D=min(VI,5.5*1.17**i); up=1.0+0.12*i; hold=max(0,i-7)*0.35; hold=min(hold,5); dn=3.0+0.08*i
        tgt=max(2.6,GAP0-0.8*D); gap=GAP0
        if calm is not None and i>=calm:
            k=i-calm
            if k==0: D=4.0; up=4.0; hold=0; dn=5.0; tgt=12; gap=48
            else: D=4.0*0.78**k; up=4.0; hold=0; dn=5.0; tgt=GAP0-1.5
        follow=None
        if calm is not None and i>calm: follow=1.2
        P.append((D,up,hold,dn,tgt,follow)); G.append(gap)
    return P,G
A=solve(*params()); B=solve(*params(calm=5))
json.dump(dict(dt=DT*2,N=N,L=L,A=A,B=B),open('sim.json','w'))
