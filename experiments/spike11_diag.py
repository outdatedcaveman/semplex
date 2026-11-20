"""Spike 11 exploratory diagnostics (post hoc, NOT pre-registered). python -m experiments.spike11_diag"""
import numpy as np
from collections import defaultdict
from cerp import atlas, mechvol, train
from experiments.spike09 import wstar_table
from experiments import spike11 as S
tb=atlas.build_all(4)[4]; w,_=wstar_table(tb)
els=[int(tb.exhibit[c]) for c in tb.classes()]; els=[e for e in els if w[e]==2 and tb.hi[e]==3]
om,ns=mechvol.solid_angles(4_000_000,np.random.default_rng(1100)); fl=0.5/ns
pidx=mechvol.PairIndex(tb.ltf)
iso={e:pidx.isomers(e) for e in els}
pc=lambda t: bin(t).count('1')
def feats(q):
    a,b=q
    return {'logV':np.log(om.get(a,fl)*om.get(b,fl)),
            'balance':-(abs(pc(a)-8)+abs(pc(b)-8)),
            'neg_minLogOmega':-min(np.log(om.get(a,fl)),np.log(om.get(b,fl)))}
fs=np.array(els*100)
obs,_=S.run(fs,8,1108,{e:set(v) for e,v in iso.items()},None)
res=defaultdict(list); norm_x=[]; norm_y=[]
for e in els:
    o=obs[e]; n=sum(o.values()); K=len(iso[e])
    if n==0: continue
    y=np.array([o.get(q,0) for q in iso[e]])
    F={k:np.array([feats(q)[k] for q in iso[e]]) for k in feats(iso[e][0])}
    for k,v in F.items(): res[k].append(mechvol._spearman(y,v))
    V=np.exp(F['logV']); V/=V.sum()
    norm_x+=list(np.log10(V*K)); norm_y+=list(y/n*K)
for k,v in res.items(): print(k,'median within-element spearman',round(float(np.nanmedian(v)),3))
x=np.array(norm_x); y=np.array(norm_y); e=np.quantile(x,np.linspace(0,1,11))
bx,by=[],[]
for i in range(10):
    m=(x>=e[i])&(x<=e[i+1]) if i==9 else (x>=e[i])&(x<e[i+1])
    if y[m].mean()>0: bx.append(np.log10(np.mean(10**x[m]))); by.append(np.log10(y[m].mean()))
print('per-element-normalised bins (pred*K, obs*K):',[(round(10**a,2),round(10**b,2)) for a,b in zip(bx,by)])
print('normalised slope',round(float(np.polyfit(bx,by,1)[0]),3))
