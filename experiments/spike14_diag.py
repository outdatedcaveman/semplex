"""Spike 14 post hoc diagnostics (NOT pre-registered): is the U-product's high Spearman an artifact of
shared zeros? And does Curie add to U? python -m experiments.spike14_diag"""
import json, math
import numpy as np
from collections import defaultdict
from cerp import atlas, mechvol
from experiments import spike14 as S

tb, ex, els, iso = S.setup(); T = atlas.transforms(4)
U = json.loads((S.RAW / "U1.json").read_text())
for env in S.ENVS:
    d = json.loads((S.RAW / f"{env}.json").read_text())
    r_pos, r_upos, r_cur_pos, cover, r_join = [], [], [], [], []
    for e in els:
        ok = S.orbit_keys(iso[e], S.stab_group(e, T))
        osz = defaultdict(int)
        for o in ok.values(): osz[o] += 1
        u = U[str(e)]; nu = sum(u.values())
        c = d["counts"][str(e)]
        keys = [f"{a}-{b}" for a, b in iso[e]]
        y = np.array([c[0].get(k, 0) + c[1].get(k, 0) for k in keys])
        if y.sum() == 0: continue
        uu = np.array([math.log((u.get(k.split('-')[0], 0) + .5) / nu) + math.log((u.get(k.split('-')[1], 0) + .5) / nu) for k in keys])
        cur = np.array([-3 * math.log(osz[ok[k]]) for k in keys])
        both = np.array([(u.get(k.split('-')[0], 0) > 0) and (u.get(k.split('-')[1], 0) > 0) for k in keys])
        m = y > 0
        if m.sum() >= 3:
            r_pos.append(mechvol._spearman(y[m], uu[m])); r_cur_pos.append(mechvol._spearman(y[m], cur[m]))
        if both.sum() >= 3:
            r_upos.append(mechvol._spearman(y[both], uu[both]))
        cover.append(y[both].sum() / y.sum())
        r_join.append(mechvol._spearman(y, uu + cur))
    f = lambda v: round(float(np.nanmedian(v)), 2)
    print(env, "| among observed isomers: U", f(r_pos), "Curie", f(r_cur_pos),
          "| among isomers with both units reached by single nets: U", f(r_upos),
          "| share of runs on such isomers", round(float(np.mean(cover)), 2), "| U+Curie", f(r_join))
