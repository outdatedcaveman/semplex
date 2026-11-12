"""Spike 19 (pre-registered in SPIKE_19_REPORT.md).

  python -m experiments.spike19 run1       arm 1 runs (also the fresh data for arm 3)
  python -m experiments.spike19 run2       arm 2: CSP with smoothness-matched null
  python -m experiments.spike19 analyse
"""

from __future__ import annotations

import json
import math
import pathlib
import sys
from collections import defaultdict

import numpy as np

from cerp import atlas, mechvol, train
from experiments import spike12 as S12, spike14 as S14, spike18 as S18
from experiments.spike09 import tgt

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "experiments" / "results" / "spike19_raw"
OUT = ROOT / "experiments" / "results" / "spike19.json"
FULL = 0xFFFF
CH = (1, 3, 10, 30, 100, 300, 1000, 3000)


def save(key, val):
    res = json.loads(OUT.read_text()) if OUT.exists() else {}
    res[key] = val
    OUT.write_text(json.dumps(res, indent=1))


def gfull(e, T):
    return [(pm, ng, idx) for pm, ng, idx in T if atlas.apply_T(e, idx, False, 4) in (e, FULL ^ e)]


def stab_key(st):
    return frozenset((tuple(p), n) for p, n, _ in st)


# ------------------------------------------------------------------ arm 1

def run1():
    tb, ex, els, iso = S14.setup()
    T = atlas.transforms(4)
    G = {e: gfull(e, T) for e in els}
    fs = np.array([e for _ in range(40) for e in els])
    p = train.init(len(fs), 8, np.random.default_rng(19_000), dtype=np.float32)
    snaps, state, done = [], None, 0
    for cp in CH:
        p, state = train.train(p, tgt(fs), np.ones((len(fs), 16)), cp - done, lr=0.03, wd=0.03, opt="adamw", state=state)
        done = cp
        th = np.concatenate([p["W1"], p["b1"][:, :, None]], axis=2).astype(float)
        snaps.append(th)
    g, _, units = train.read_circuits(p)
    fn_at = [train.bits(np.transpose((np.einsum("bhn,xn->bxh", s[:, :, :4], train.XS) + s[:, None, :, 4]) >= 0, (0, 2, 1))) for s in snaps]
    counts = {str(e): [defaultdict(float), defaultdict(float)] for e in els}
    obs = []
    for b in np.nonzero(g == fs)[0]:
        e, half = int(fs[b]), int(b // (len(els) * 20))
        pre = S12.r2_prefix(units[b], p["W2"][b], e)
        if pre is None:
            continue
        c2 = S12.credit({int(x) for x in mechvol.canon(pre)}, iso[e])
        if not c2:
            continue
        for k, v in c2.items():
            counts[str(e)][half][k] += v
        core = {int(x) for k in c2 for x in k.split("-")}
        for j in range(8):
            t = int(units[b, j])
            if int(mechvol.canon(t)) not in core:
                continue
            H = S18.unit_stabilizer(t, G[e])
            if not H:
                continue
            Hk = stab_key(H)
            Hp = None
            for pm, ng, idx in G[e]:
                t2 = atlas.apply_T(t, idx, False, 4)
                cand = S18.unit_stabilizer(t2, G[e])
                if cand and stab_key(cand) != Hk:
                    Hp = cand
                    break
            if Hp is None:
                continue
            seq = [int(mechvol.canon(int(f[b, j]))) for f in fn_at]
            final = int(mechvol.canon(t))
            settle = len(CH) - 1
            while settle > 0 and seq[settle - 1] == final:
                settle -= 1
            pre_obs = [(S18.defect(snaps[i][b, j], t, H), S18.defect(snaps[i][b, j], t, Hp)) for i in range(settle)]
            obs.append({"e": e, "t": t, "stab": len(H) + 1, "settle": settle, "pre": pre_obs})
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "arm1.json").write_text(json.dumps({"fit": float((g == fs).mean()), "counts": counts, "obs": obs}))
    print("arm1 fit", float((g == fs).mean()), "units observed", len(obs), flush=True)


def analyse1():
    d = json.loads((RAW / "arm1.json").read_text())
    diffs, last_better = [], []
    for o in d["obs"]:
        for dh, dhp in o["pre"]:
            if dh is not None and dhp is not None:
                diffs.append(dhp - dh)
        if o["pre"]:
            dh, dhp = o["pre"][-1]
            if dh is not None and dhp is not None:
                last_better.append(dh < dhp)
    diffs = np.array(diffs)
    pos, neg = int((diffs > 0).sum()), int((diffs < 0).sum())
    from math import comb
    from fractions import Fraction
    n = pos + neg
    p = float(Fraction(sum(comb(n, k) for k in range(pos, n + 1)), 2 ** n)) if n else None
    settles = [o["settle"] for o in d["obs"]]
    res = {"units": len(d["obs"]), "pre_settling_observations": len(diffs), "median_DHprime_minus_DH": float(np.median(diffs)) if len(diffs) else None,
           "positive": pos, "negative": neg, "sign_test_p": p,
           "share_last_pre_settling_closer_to_own_H": float(np.mean(last_better)) if last_better else None,
           "units_with_pre_settling_obs": len(last_better),
           "settle_checkpoint_histogram": {str(CH[i]): settles.count(i) for i in range(len(CH))}}
    print("arm1", res, flush=True)
    save("arm1", res)


# ------------------------------------------------------------------ arm 2

def csp_calibrated(pts, y, lab, cands):
    index = {pt: i for i, pt in enumerate(pts)}
    L = np.nonzero(lab)[0]
    P = np.array(pts, dtype=object)
    dist = lambda a, b: sum(u != v for u, v in zip(pts[a], pts[b]))
    agree_by_d, cnt_by_d = defaultdict(int), defaultdict(int)
    for ii in range(len(L)):
        for jj in range(ii + 1, len(L)):
            a, b = L[ii], L[jj]
            dd = dist(a, b)
            cnt_by_d[dd] += 1; agree_by_d[dd] += int(y[a] == y[b])
    p0 = {dd: agree_by_d[dd] / cnt_by_d[dd] for dd in cnt_by_d}
    thr = 0.001 / len(cands)
    acc = []
    for kind, fn in cands:
        img = np.array([index.get(fn(pt), -1) for pt in pts])
        pairs = [(i, int(img[i])) for i in range(len(pts)) if img[i] >= 0 and img[i] != i and lab[i] and lab[img[i]]]
        if not pairs or not all(y[a] == y[b] for a, b in pairs):
            continue
        logp = sum(math.log(p0.get(dist(a, b), 1.0)) for a, b in pairs)
        if logp < math.log(thr):
            acc.append((kind, img))
    parent = list(range(len(pts)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for _, img in acc:
        for i in range(len(pts)):
            if img[i] >= 0:
                a, b = find(i), find(int(img[i]))
                if a != b:
                    parent[a] = b
    orbs = defaultdict(list)
    for i in range(len(pts)):
        orbs[find(i)].append(i)
    lab2, y2 = lab.copy(), y.copy()
    for o in orbs.values():
        ls = {int(y[i]) for i in o if lab[i]}
        if len(ls) > 1:
            return lab.copy(), y.copy(), [k for k, _ in acc], True
        if len(ls) == 1:
            v = ls.pop()
            for i in o:
                if not lab[i]:
                    lab2[i] = True; y2[i] = v
    return lab2, y2, [k for k, _ in acc], False


def run2():
    import torch
    torch.set_num_threads(4)
    ttt_pts, ttt_y, ttt_doms = S18.tictactoe()
    mk_pts, mk_ys, mk_doms = S18.monk()
    jobs = [("tic-tac-toe", ttt_pts, ttt_y, ttt_doms, S18.candidates_ttt(), (0.1, 0.2, 0.3))]
    for name, yy in mk_ys.items():
        jobs.append((name, mk_pts, yy, mk_doms, S18.candidates_monk(mk_doms), (0.15, 0.3)))
    out = {}
    for name, pts, y, doms, cands, fracs in jobs:
        X = S18.onehot(pts, doms)
        for frac in fracs:
            rnd = np.random.default_rng(1802)                     # same splits as Spike 18
            labs, rows = [], []
            for s in range(10):
                lab = np.zeros(len(pts), dtype=bool); lab[rnd.choice(len(pts), int(round(frac * len(pts))), replace=False)] = True
                l2, y2, acc, void = csp_calibrated(pts, y, lab, cands)
                labs.append((lab, l2, y2)); rows.append({"accepted": acc, "void": void, "labelled_after": int(l2.sum())})
            Yb = np.array([y for _ in labs] + [y2 for _, _, y2 in labs], dtype=float)
            Mb = np.array([lab for lab, _, _ in labs] + [l2 for _, l2, _ in labs], dtype=float)
            pred = S18.train_mlp(X, Yb, Mb, seed=1803)
            ab, ac = [], []
            for s, (lab, _, _) in enumerate(labs):
                test = ~lab
                ab.append(float((pred[s][test] == y[test].astype(bool)).mean()))
                ac.append(float((pred[10 + s][test] == y[test].astype(bool)).mean()))
            out[f"{name}@{frac}"] = {"acc_base": ab, "acc_csp": ac, "runs": rows}
            print(name, frac, round(np.mean(ab), 3), "->", round(np.mean(ac), 3),
                  "decoy runs", sum("decoy" in r["accepted"] for r in rows), "sym runs", sum("sym" in r["accepted"] for r in rows), flush=True)
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "arm2.json").write_text(json.dumps(out))


def analyse2():
    d = json.loads((RAW / "arm2.json").read_text())
    res = {}
    for k, v in d.items():
        r = {"acc_base": float(np.mean(v["acc_base"])), "acc_csp": float(np.mean(v["acc_csp"])),
             "gain": float(np.mean(v["acc_csp"]) - np.mean(v["acc_base"])),
             "voided_runs": sum(x["void"] for x in v["runs"]),
             "mean_labelled_after": float(np.mean([x["labelled_after"] for x in v["runs"]]))}
        if k.startswith("tic"):
            r["runs_with_any_decoy"] = sum("decoy" in x["accepted"] for x in v["runs"])
            r["runs_with_a_board_symmetry"] = sum("sym" in x["accepted"] for x in v["runs"])
        res[k] = r
        print(k, r, flush=True)
    save("arm2", res)


# ------------------------------------------------------------------ arm 3

def unit_features(els, iso):
    T = atlas.transforms(4)
    omega, ns = mechvol.solid_angles(40_000_000, np.random.default_rng(1100))
    pc = lambda t: bin(t).count("1")
    feats, okey, osz = {}, {}, {}
    for e in els:
        Gf = gfull(e, T)
        G = S14.stab_group(e, T)
        okey[e] = S14.orbit_keys(iso[e], G)
        c = defaultdict(int)
        for o in okey[e].values():
            c[o] += 1
        osz[e] = c
        F = {}
        for t in {t for q in iso[e] for t in q}:
            F[t] = (math.log(len(S18.unit_stabilizer(t, Gf)) + 1), max(16 - pc(t ^ e), pc(t ^ e)) / 16.0,
                    math.log(omega.get(t, 0.5 / ns)))
        feats[e] = F
    return feats, okey, osz


def loglik(params, data, feats, iso):
    a, b, c = params
    tot = 0.0
    for e, cnt in data.items():
        lw = {t: a * f[0] + b * f[1] + c * f[2] for t, f in feats[e].items()}
        keys = [f"{x}-{y}" for x, y in iso[e]]
        s = np.array([lw[x] + lw[y] for x, y in iso[e]])
        m = s.max(); logZ = m + math.log(np.exp(s - m).sum())
        for k, sv in zip(keys, s):
            n = cnt.get(k, 0.0)
            if n:
                tot += n * (sv - logZ)
    return tot


def gain_bits(pred_logw, cnt, iso_e):
    keys = [f"{x}-{y}" for x, y in iso_e]
    s = np.array([pred_logw[k] for k in keys]); s = s - s.max(); q = np.exp(s); q /= q.sum()
    N = sum(cnt.get(k, 0.0) for k in keys)
    if N == 0:
        return None, 0
    return sum(cnt.get(k, 0.0) * math.log2(q[i] * len(keys)) for i, k in enumerate(keys)), N


def analyse3():
    from scipy.optimize import minimize
    tb, ex, els, iso = S14.setup()
    rng = np.random.default_rng(1901)
    perm = rng.permutation(len(els))
    train_els = [els[i] for i in perm[: len(els) // 2]]
    test_els = [els[i] for i in perm[len(els) // 2:]]
    feats, okey, osz = unit_features(els, iso)
    s14 = json.loads((S14.RAW / "A8.json").read_text())["counts"]
    tot = lambda c: {k: c[0].get(k, 0) + c[1].get(k, 0) for k in set(c[0]) | set(c[1])}
    s14c = {e: tot(s14[str(e)]) for e in els}
    fresh = json.loads((RAW / "arm1.json").read_text())["counts"]
    freshc = {e: tot(fresh[str(e)]) for e in els}
    fresh_h1 = {e: fresh[str(e)][1] for e in els}
    fresh_h0 = {e: fresh[str(e)][0] for e in els}
    trainD = {e: s14c[e] for e in train_els}
    fit = minimize(lambda p: -loglik(p, trainD, feats, iso), x0=np.zeros(3), method="Nelder-Mead", options={"xatol": 1e-4, "fatol": 1e-3, "maxiter": 2000})
    a, b, c = fit.x
    boots = []
    for _ in range(200):
        smp = [train_els[i] for i in rng.integers(len(train_els), size=len(train_els))]
        D = defaultdict(lambda: defaultdict(float))
        for e in smp:
            for k, v in trainD[e].items():
                D[e][k] += v
        r = minimize(lambda p: -loglik(p, D, feats, iso), x0=fit.x, method="Nelder-Mead", options={"xatol": 1e-3, "fatol": 1e-2, "maxiter": 600})
        boots.append(r.x[0])

    def score(predfun, data, elist):
        g = n = 0.0
        for e in elist:
            gb, N = gain_bits(predfun(e), data[e], iso[e])
            if gb is not None:
                g += gb; n += N
        return g / n if n else None

    universal = lambda e: {f"{x}-{y}": sum(a * feats[e][t][0] + b * feats[e][t][1] + c * feats[e][t][2] for t in (x, y)) for x, y in iso[e]}
    curie = lambda e: {f"{x}-{y}": -3.0 * math.log(osz[e][okey[e][f'{x}-{y}']]) for x, y in iso[e]}

    def oracle_weights(e, cnt):
        units = sorted(feats[e])
        ix = {t: i for i, t in enumerate(units)}
        keys = [(ix[x], ix[y], f"{x}-{y}") for x, y in iso[e]]

        def nll(lw):
            s = np.array([lw[i] + lw[j] for i, j, _ in keys]); m = s.max(); lZ = m + math.log(np.exp(s - m).sum())
            return -sum(cnt.get(k, 0.0) * (s[n] - lZ) for n, (_, _, k) in enumerate(keys)) + 0.1 * float(lw @ lw)
        r = minimize(nll, np.zeros(len(units)), method="L-BFGS-B")
        return {k: r.x[i] + r.x[j] for i, j, k in keys}
    oracle_cache = {e: oracle_weights(e, fresh_h0[e]) for e in test_els}
    res = {"fit_params": {"a_log_stabilizer": a, "b_agreement": b, "c_log_solid_angle": c},
           "a_bootstrap_95": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))],
           "train_elements": len(train_els), "test_elements": len(test_els),
           "heldout_spike14": {"universal": score(universal, s14c, test_els), "curie": score(curie, s14c, test_els)},
           "fresh_heldout": {"universal": score(universal, freshc, test_els), "curie": score(curie, freshc, test_els)},
           "fresh_heldout_seeds20_39": {"universal": score(universal, fresh_h1, test_els), "curie": score(curie, fresh_h1, test_els),
                                        "oracle_per_element_product": score(lambda e: oracle_cache[e], fresh_h1, test_els)}}
    print("arm3", json.dumps(res, indent=1), flush=True)
    save("arm3", res)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "run1":
        run1()
    elif cmd == "run2":
        run2()
    else:
        analyse1(); analyse2(); analyse3()
