"""Spike 20 (pre-registered in SPIKE_20_REPORT.md).

  python -m experiments.spike20 runB relu8|tanh32
  python -m experiments.spike20 runC
  python -m experiments.spike20 analyse
"""

from __future__ import annotations

import json
import math
import pathlib
import sys
from collections import defaultdict

import numpy as np
from scipy.optimize import minimize

from cerp import atlas, mechvol, train
from experiments import spike12 as S12, spike13 as S13, spike14 as S14, spike18 as S18, spike19 as S19
from experiments.spike09 import tgt

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "experiments" / "results" / "spike20_raw"
OUT = ROOT / "experiments" / "results" / "spike20.json"
FULL = 0xFFFF


def save(key, val):
    res = json.loads(OUT.read_text()) if OUT.exists() else {}
    res[key] = val
    OUT.write_text(json.dumps(res, indent=1))


def tot(c):
    return {k: c[0].get(k, 0) + c[1].get(k, 0) for k in set(c[0]) | set(c[1])}


def core_counts(fs, g, units, W2, iso, els):
    counts = {str(e): [defaultdict(float), defaultdict(float)] for e in els}
    for b in np.nonzero(g == fs)[0]:
        e, half = int(fs[b]), int(b // (len(els) * 20))
        pre = S12.r2_prefix(units[b], W2[b], e)
        if pre is None:
            continue
        for k, v in S12.credit({int(x) for x in mechvol.canon(pre)}, iso[e]).items():
            counts[str(e)][half][k] += v
    return counts


# ------------------------------------------------------------------ runs

def runB(name):
    tb, ex, els, iso = S14.setup()
    act, H = {"relu8": ("relu", 8), "tanh32": ("tanh", 32)}[name]
    fs = np.array([e for _ in range(40) for e in els])
    p = train.init(len(fs), H, np.random.default_rng(20_000 + H), out_scale=0.5 * math.sqrt(8 / H), dtype=np.float32)
    p, _ = train.train(p, tgt(fs), np.ones((len(fs), 16)), 3000, lr=0.03, wd=0.03, act=act)
    g, _, units = train.read_circuits(p, act=act)
    out = {"run": name, "fit": float((g == fs).mean()), "counts": core_counts(fs, g, units, p["W2"], iso, els)}
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / f"B_{name}.json").write_text(json.dumps(out))
    print("B", name, "fit", out["fit"], flush=True)


def runC(H=512, steps=3000, lr=0.03, l1=1e-3):
    """Selection only: first layer frozen at random init; output layer trained with L1 (AdamW-style, no wd)."""
    tb, ex, els, iso = S14.setup()
    fs = np.array([e for _ in range(40) for e in els])
    p = train.init(len(fs), H, np.random.default_rng(20_100), out_scale=0.5 * math.sqrt(8 / H), dtype=np.float32)
    pre = np.einsum("bhn,xn->bxh", p["W1"], train.XS.astype(np.float32)) + p["b1"][:, None, :]
    h = np.tanh(pre)                                                                        # fixed features (B, 16, H)
    T = tgt(fs).astype(np.float32)
    W2, b2 = p["W2"], p["b2"]
    m = {k: np.zeros_like(v) for k, v in (("W2", W2), ("b2", b2))}
    v = {k: np.zeros_like(x) for k, x in (("W2", W2), ("b2", b2))}
    for t in range(1, steps + 1):
        z = np.einsum("bxh,bh->bx", h, W2) + b2[:, None]
        dz = (1 / (1 + np.exp(-z)) - T) / 16
        g = {"W2": np.einsum("bx,bxh->bh", dz, h) + l1 * np.sign(W2), "b2": dz.sum(1)}
        for k, x in (("W2", W2), ("b2", b2)):
            m[k] = 0.9 * m[k] + 0.1 * g[k]; v[k] = 0.999 * v[k] + 0.001 * g[k] ** 2
            x -= lr * (m[k] / (1 - 0.9 ** t)) / (np.sqrt(v[k] / (1 - 0.999 ** t)) + 1e-8)
    z = np.einsum("bxh,bh->bx", h, W2) + b2[:, None]
    gfun = train.bits(z >= 0)
    units = train.bits(np.transpose(pre >= 0, (0, 2, 1)))
    out = {"run": "selection", "fit": float((gfun == fs).mean()), "counts": core_counts(fs, gfun, units, W2, iso, els),
           "mean_units_with_abs_w2_gt_0.05": float((np.abs(W2) > 0.05).sum(1).mean())}
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "C_selection.json").write_text(json.dumps(out))
    print("C fit", out["fit"], "active units", out["mean_units_with_abs_w2_gt_0.05"], flush=True)


# ------------------------------------------------------------------ analysis

def mutual_info(t, g):
    n = np.zeros((2, 2))
    for x in range(16):
        n[(t >> x) & 1, (g >> x) & 1] += 1
    p = n / 16; pt = p.sum(1); pg = p.sum(0)
    return float(sum(p[i, j] * math.log2(p[i, j] / (pt[i] * pg[j])) for i in range(2) for j in range(2) if p[i, j] > 0))


def build_feats(els, iso):
    base, okey, osz = S19.unit_features(els, iso)
    feats = {}
    for e in els:
        feats[e] = {t: {"agree": f[1], "logomega": f[2], "logstab": f[0], "mi": mutual_info(t, e)} for t, f in base[e].items()}
    return feats, okey, osz


def ll2(params, data, feats, iso, tilt):
    gam, lam = params
    tot_ = 0.0
    for e, cnt in data.items():
        if not cnt:
            continue
        lw = {t: gam * f["logomega"] + lam * f[tilt] for t, f in feats[e].items()}
        s = np.array([lw[x] + lw[y] for x, y in iso[e]]); m = s.max(); lZ = m + math.log(np.exp(s - m).sum())
        for (x, y), sv in zip(iso[e], s):
            n = cnt.get(f"{x}-{y}", 0.0)
            if n:
                tot_ += n * (sv - lZ)
    return tot_


def fit2(data, feats, iso, tilt, x0=(0.9, 10.0)):
    r = minimize(lambda p: -ll2(p, data, feats, iso, tilt), np.array(x0), method="Nelder-Mead",
                 options={"xatol": 1e-3, "fatol": 1e-2, "maxiter": 800})
    return r.x


def score(params, data, feats, iso, tilt, elist):
    gam, lam = params
    g = n = 0.0
    for e in elist:
        pred = {f"{x}-{y}": sum(gam * feats[e][t]["logomega"] + lam * feats[e][t][tilt] for t in (x, y)) for x, y in iso[e]}
        gb, N = S19.gain_bits(pred, data[e], iso[e])
        if gb is not None:
            g += gb; n += N
    return g / n if n else None


def load_runs(els):
    runs = {}
    for name, f in (("S14:A8", S14.RAW / "A8.json"), ("S14:G8", S14.RAW / "G8.json"), ("S14:A128", S14.RAW / "A128.json")):
        runs[name] = json.loads(f.read_text())["counts"]
    for f in sorted(S18.RAW.glob("A_*.json")):
        runs["S18:" + f.stem[2:]] = json.loads(f.read_text())["counts"]
    runs["S19:arm1"] = json.loads((S19.RAW / "arm1.json").read_text())["counts"]
    runs["S12:W8"] = {k: v for k, v in json.loads((S12.RAW / "W8.json").read_text())["counts"]["R2"].items()}
    runs["S13:A8-10k"] = {k: v for k, v in json.loads((S13.RAW / "A8-10k.json").read_text())["counts"]["R2"].items()}
    out = {}
    for name, c in runs.items():
        out[name] = {e: tot(c[str(e)]) for e in els if str(e) in c}
    return out


def analyse():
    tb, ex, els, iso = S14.setup()
    feats, okey, osz = build_feats(els, iso)
    rng = np.random.default_rng(2001)
    runs = load_runs(els)
    for f in sorted(RAW.glob("*.json")):
        d = json.loads(f.read_text())
        runs["S20:" + d["run"]] = {e: tot(d["counts"][str(e)]) for e in els}
    # ---- arm A (and fits used by arm C)
    armA = {}
    boots = {}
    for name, data in runs.items():
        p = fit2(data, feats, iso, "agree")
        el = list(data)
        bl = []
        for _ in range(100):
            smp = [el[i] for i in rng.integers(len(el), size=len(el))]
            D = defaultdict(lambda: defaultdict(float))
            for e in smp:
                for k, v in data[e].items():
                    D[e][k] += v
            bl.append(fit2(D, feats, iso, "agree", x0=p))
        boots[name] = np.array(bl)
        armA[name] = {"gamma_logomega": float(p[0]), "lambda_agree": float(p[1]), "elements": len(el),
                      "lambda_95": [float(np.percentile(boots[name][:, 1], 2.5)), float(np.percentile(boots[name][:, 1], 97.5))],
                      "gamma_95": [float(np.percentile(boots[name][:, 0], 2.5)), float(np.percentile(boots[name][:, 0], 97.5))]}
        print("A", name, armA[name], flush=True)

    def p_greater(a, b):
        return float(np.mean(boots[a][:, 1] > boots[b][:, 1]))
    orders = {"A8 wd0.1 > wd0.03": p_greater("S18:A8-wd0.1", "S18:A8-wd0.03"),
              "A8 wd0.03 > wd0": p_greater("S18:A8-wd0.03", "S18:A8-wd0"),
              "G8 wd0.003 > wd0": p_greater("S18:G8-wd0.003", "S18:G8-wd0"),
              "A8 10k steps > 3k steps (48 elements)": p_greater("S13:A8-10k", "S12:W8")}
    save("armA", {"fits": armA, "bootstrap_P_ordering": orders})
    print("orders", orders, flush=True)
    # ---- arm B
    perm = np.random.default_rng(1901).permutation(len(els))
    test = [els[i] for i in perm[len(els) // 2:]]
    train_els = [els[i] for i in perm[: len(els) // 2]]
    a, b, c = 0.13113884253726468, 9.919786304308806, 0.879561909976921         # Spike 19 fit, fixed
    def uni(e):
        return {f"{x}-{y}": sum(a * feats[e][t]["logstab"] + b * feats[e][t]["agree"] + c * feats[e][t]["logomega"] for t in (x, y)) for x, y in iso[e]}
    def cur(e):
        return {f"{x}-{y}": -3.0 * math.log(osz[e][okey[e][f'{x}-{y}']]) for x, y in iso[e]}
    def sc(pred, data):
        g = n = 0.0
        for e in test:
            gb, N = S19.gain_bits(pred(e), data[e], iso[e])
            if gb is not None:
                g += gb; n += N
        return g / n if n else None
    armB = {}
    for name in ("S20:relu8", "S20:tanh32"):
        if name in runs:
            armB[name] = {"universal_S19_params": sc(uni, runs[name]), "curie": sc(cur, runs[name])}
    save("armB", armB); print("B", armB, flush=True)
    # ---- arm C
    if "S20:selection" in runs:
        armC = {"selection": armA["S20:selection"], "training_S19_arm1": armA["S19:arm1"],
                "lambda_ratio_train_over_selection": armA["S19:arm1"]["lambda_agree"] / armA["S20:selection"]["lambda_agree"],
                "ratio_bootstrap_95": [float(np.percentile(boots["S19:arm1"][:, 1] / boots["S20:selection"][:, 1], q)) for q in (2.5, 97.5)]}
        save("armC", armC); print("C", armC, flush=True)
    # ---- arm D
    trainD = {e: runs["S14:A8"][e] for e in train_els}
    armD = {}
    for tilt in ("agree", "mi"):
        p = fit2(trainD, feats, iso, tilt, x0=(0.9, 10.0 if tilt == "agree" else 3.0))
        armD[tilt] = {"params": [float(x) for x in p],
                      "heldout_S14": score(p, runs["S14:A8"], feats, iso, tilt, test),
                      "heldout_S19_fresh": score(p, runs["S19:arm1"], feats, iso, tilt, test)}
    save("armD", armD); print("D", armD, flush=True)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "runB":
        runB(sys.argv[2])
    elif cmd == "runC":
        runC()
    else:
        analyse()
