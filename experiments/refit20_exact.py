"""Audit: refit every Spike 20 law fit with the exact (Newton) fitter and compare with the Nelder-Mead values reported."""
import json, numpy as np
from cerp import loglin
from experiments import spike20 as S20, spike14 as S14
tb, ex, els, iso = S14.setup()
feats, okey, osz = S20.build_feats(els, iso)
runs = S20.load_runs(els)
for f in sorted(S20.RAW.glob("*.json")):
    d = json.loads(f.read_text()); runs["S20:"+d["run"]] = {e: S20.tot(d["counts"][str(e)]) for e in els}
out = {}
for tilt in ("agree", "mi"):
    for name, data in runs.items():
        groups = []
        for e, cnt in data.items():
            if not cnt: continue
            F = np.array([[feats[e][x]["logomega"]+feats[e][y]["logomega"], feats[e][x][tilt]+feats[e][y][tilt]] for x,y in iso[e]])
            C = np.array([cnt.get(f"{x}-{y}",0.0) for x,y in iso[e]])
            groups.append((C,F))
        th, nll = loglin.fit(groups, 2)
        nm = S20.fit2(data, feats, iso, tilt)
        out[f"{tilt}|{name}"] = {"exact": th.tolist(), "nelder_mead": list(map(float,nm)), "nll_exact": nll, "nll_nm": -S20.ll2(nm, data, feats, iso, tilt)}
        print(tilt, name, np.round(th,3), np.round(nm,3), round(nll,2), round(out[f"{tilt}|{name}"]["nll_nm"],2), flush=True)
json.dump(out, open("experiments/results/spike20_refit_exact.json","w"), indent=1)
