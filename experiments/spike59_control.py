import sys; sys.path.insert(0,'/home/user/semplex')
import json, numpy as np, itertools, os
os.environ.setdefault('SPIKE53_DATA','/tmp/claude-0/-home-user/c1370310-95be-56d2-b761-b9e47fdba1e8/scratchpad/s53/data')
from cerp import hfrows
from experiments import spike59 as S
from experiments.spike53 import MODELS, model_matrices
R='/home/user/semplex/experiments/results/spike59_raw/'
words=open('/home/user/semplex/experiments/data/google-10000-english-no-swears.txt').read().split(); rank={w:r for r,w in enumerate(words)}
toks={m:hfrows.tokenizer(m) for m in MODELS}
excl=set(S.PRIMES)|set(S.ABSTRACT)
common=[w for w in words if w.isalpha() and len(w)>=2 and w not in excl and all(S.single(toks[m],w) is not None for m in MODELS)]
cr=np.array([rank[w] for w in common])
dicts=[('primes',list(S.PRIMES))]
for draw in range(5):
    rng=np.random.default_rng(777+draw); dic=[]
    for p in S.PRIMES:
        ok=[common[i] for i in np.nonzero(np.abs(cr-rank[p])<=100)[0] if common[i] not in dic]
        dic.append(ok[rng.integers(len(ok))])
    dicts.append((f'rand{draw}',dic))
out={}
for name,dic in dicts:
    sel={'conc':{},'abst':{}}
    for m in MODELS:
        tok=toks[m]
        for side,tensor in model_matrices(m):
            z=np.load(R+f"{m.replace('/','__')}__{side}.npz")
            conc=json.loads(str(z['conc'])); abst=json.loads(str(z['abst']))
            dids=[S.single(tok,w) for w in dic]
            ids=sorted(set(conc.values())|set(abst.values())|set(dids))
            M=hfrows.rows(m,tensor,ids).astype(np.float64)
            M=M-M.mean(0); M/=np.linalg.norm(M,axis=1,keepdims=True); row={i:M[j] for j,i in enumerate(ids)}
            D=np.stack([row[i] for i in dids])
            for key,T in (('conc',conc),('abst',abst)):
                tw=sorted(T); X=np.stack([row[T[w]] for w in tw]); _,coef=S.omp_r2(D,X,8)
                sel[key][f'{m}:{side}']={w:frozenset(dic[j] for j in np.nonzero(coef[t])[0]) for t,w in enumerate(tw)}
    for key in ('conc','abst'):
        Sx=sel[key]; mk=list(Sx); ws=sorted(set.intersection(*[set(Sx[x]) for x in mk]))
        tot=0;n=0
        for w in ws:
            for a,b in itertools.combinations(mk,2): tot+=len(Sx[a][w]&Sx[b][w]); n+=1
        out[f'{name}:{key}']=tot/n
        print(name,key,len(ws),round(tot/n,3),flush=True)
json.dump(out,open('/home/user/semplex/experiments/results/spike59_control.json','w'),indent=1)
