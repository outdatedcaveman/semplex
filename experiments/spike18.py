"""Spike 18 (pre-registered in SPIKE_18_REPORT.md).

  python -m experiments.spike18 runA ENV ...     A8-wd0 A8-wd0.03 A8-wd0.1 G8-wd0 G8-wd0.003
  python -m experiments.spike18 runB             CSP on tic-tac-toe and MONK 1-3
  python -m experiments.spike18 analyse
"""

from __future__ import annotations

import itertools
import json
import math
import pathlib
import random
import sys
from collections import defaultdict

import numpy as np

from cerp import atlas, mechvol, train
from experiments import spike12 as S12, spike14 as S14
from experiments.spike09 import tgt

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "experiments" / "results" / "spike18_raw"
OUT = ROOT / "experiments" / "results" / "spike18.json"
FULL = 0xFFFF
ENVS = {"A8-wd0": dict(opt="adamw", lr=0.03, wd=0.0, steps=3000),
        "A8-wd0.03": dict(opt="adamw", lr=0.03, wd=0.03, steps=3000),
        "A8-wd0.1": dict(opt="adamw", lr=0.03, wd=0.1, steps=3000),
        "G8-wd0": dict(opt="gd", lr=0.3, wd=0.0, steps=10000),
        "G8-wd0.003": dict(opt="gd", lr=0.3, wd=0.003, steps=10000)}
CHECKS = (100, 300, 1000, 3000)


def save(key, val):
    res = json.loads(OUT.read_text()) if OUT.exists() else {}
    res[key] = val
    OUT.write_text(json.dumps(res, indent=1))


# ------------------------------------------------------------------ group action on a unit's weights

def act_theta(theta, perm, neg):
    """sigma . (w, b): the weights that compute (T t)(x) = t(idx[x]) when (w, b) computes t."""
    w, b = theta[:4], theta[4]
    w2 = np.zeros(4)
    for j in range(4):
        s = -1.0 if (neg >> j) & 1 else 1.0
        w2[perm[j]] = s * w[j]
    return np.append(w2, b)


def unit_bits(theta):
    return int(train.bits((train.XS @ theta[:4] + theta[4]) >= 0))


def defect(theta, t, stab):
    """stab: list of (perm, neg, flips) with flips = True when sigma t = not t."""
    n = np.linalg.norm(theta)
    vals = []
    for perm, neg, flips in stab:
        st = act_theta(theta, perm, neg)
        vals.append(np.linalg.norm(st + theta if flips else st - theta) / n)
    return float(np.mean(vals)) if vals else None


def unit_stabilizer(t, G):
    out = []
    for perm, neg, idx in G:
        tt = atlas.apply_T(t, idx, False, 4)
        if tt == t and not (perm == (0, 1, 2, 3) and neg == 0):
            out.append((perm, neg, False))
        elif tt == FULL ^ t:
            out.append((perm, neg, True))
    return out


# ------------------------------------------------------------------ arm A

def runA(name):
    cfg = ENVS[name]
    tb, ex, els, iso = S14.setup()
    T = atlas.transforms(4)
    Gfull = {e: [(pm, ng, idx) for pm, ng, idx in T if atlas.apply_T(e, idx, False, 4) in (e, FULL ^ e)] for e in els}
    fs = np.array([e for _ in range(40) for e in els])
    p = train.init(len(fs), 8, np.random.default_rng(18_000 + list(ENVS).index(name)), dtype=np.float32)
    checks = CHECKS if cfg["steps"] == 3000 else CHECKS + (10000,)
    snaps, state, done = [], None, 0
    for cp in checks:
        p, state = train.train(p, tgt(fs), np.ones((len(fs), 16)), cp - done, lr=cfg["lr"], wd=cfg["wd"], opt=cfg["opt"], state=state)
        done = cp
        snaps.append(np.concatenate([p["W1"], p["b1"][:, :, None]], axis=2).astype(float))     # (B, 8, 5)
    g, faithful, units = train.read_circuits(p)
    counts = {str(e): [defaultdict(float), defaultdict(float)] for e in els}
    defects = []
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
            t = int(mechvol.canon(units[b, j]))
            if t not in core:
                continue
            st = unit_stabilizer(int(units[b, j]), Gfull[e])
            if not st:
                continue
            defects.append([t, len(st) + 1, [defect(s[b, j], int(units[b, j]), st) for s in snaps]])
    out = {"env": name, **cfg, "checks": list(checks), "fit": float((g == fs).mean()), "counts": counts, "defects": defects}
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / f"A_{name}.json").write_text(json.dumps(out))
    print("A", name, "fit", out["fit"], "units with nontrivial stabilizer", len(defects), flush=True)


def null_defect(t, G, rng, n=200, max_draws=2_000_000):
    """Defect of isotropic Gaussian weights realizing t (or its complement, mapped to t by negation)."""
    st = unit_stabilizer(t, G)
    vals, draws = [], 0
    while len(vals) < n and draws < max_draws:
        th = rng.normal(size=(20000, 5)); draws += 20000
        bits = train.bits((th[:, :4] @ train.XS.T + th[:, 4:]) >= 0)
        for i in np.nonzero(bits == t)[0][: n - len(vals)]:
            vals.append(defect(th[i], t, st))
        for i in np.nonzero(bits == (FULL ^ t))[0][: n - len(vals)]:
            vals.append(defect(-th[i], t, st))
    return float(np.median(vals)) if vals else None


def analyseA():
    from experiments import spike17 as S17
    tb, ex, els, iso = S14.setup()
    T = atlas.transforms(4)
    okey, osz, uorb, Gfull = {}, {}, {}, {}
    for e in els:
        G = S14.stab_group(e, T)
        okey[e] = S14.orbit_keys(iso[e], G)
        c = defaultdict(int)
        for o in okey[e].values():
            c[o] += 1
        osz[e] = c
        uorb[e] = {t: min(S14.act(t, idx) for idx in G) for pair in iso[e] for t in pair}
        Gfull[e] = [(pm, ng, idx) for pm, ng, idx in T if atlas.apply_T(e, idx, False, 4) in (e, FULL ^ e)]
    rng = np.random.default_rng(1801)
    null_cache = {}
    res = {}
    for f in sorted(RAW.glob("A_*.json")):
        d = json.loads(f.read_text())
        obs, umass = {}, {}
        for e in els:
            c = d["counts"][str(e)]
            tot = {k: c[0].get(k, 0) + c[1].get(k, 0) for k in okey[e]}
            obs[e] = tot
            m = defaultdict(float)
            for k, v in tot.items():
                a, b = map(int, k.split("-")); m[a] += v; m[b] += v
            umass[e] = m
        xs, ys = [], []
        for e in els:
            uo = defaultdict(float); us = defaultdict(int)
            for t, o in uorb[e].items():
                us[o] += 1; uo[o] += umass[e].get(t, 0.0)
            N = sum(uo.values()); K = len(us)
            if N == 0 or K < 2:
                continue
            lm = np.mean([math.log(s) for s in us.values()])
            for o, s in us.items():
                xs.append(math.log(s) - lm); ys.append(uo[o] / N * K)
        row = {"fit": d["fit"], "beta": S17.orbit_beta(obs, okey, osz), "beta_unit": S17.beta_fit(xs, ys)}
        if d["defects"] and d["env"] in ("A8-wd0.03", "A8-wd0"):
            # null per (element-free) unit t: use the element group of the first element where t occurs
            fin = np.array([x[2][-1] for x in d["defects"]])
            first = np.array([x[2][0] for x in d["defects"]])
            nulls = []
            for t, _, _ in d["defects"]:
                if t not in null_cache:
                    e0 = next(e for e in els if t in uorb[e])
                    null_cache[t] = null_defect(t, Gfull[e0], rng)
                nulls.append(null_cache[t])
            nulls = np.array([np.nan if v is None else v for v in nulls])
            row["defect"] = {"units": len(fin), "median_final": float(np.median(fin)), "median_at_100": float(np.median(first)),
                             "median_null": float(np.nanmedian(nulls)),
                             "ratio_final_to_null": float(np.median(fin) / np.nanmedian(nulls)),
                             "median_by_checkpoint": [float(np.median([x[2][i] for x in d["defects"]])) for i in range(len(d["checks"]))]}
        res[d["env"]] = row
        print(d["env"], row, flush=True)
    save("armA", res)


# ------------------------------------------------------------------ arm B: datasets

LINES = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]


def wins(b, p):
    return any(all(b[i] == p for i in l) for l in LINES)


def tictactoe():
    ends = {}

    def rec(b, turn):
        if wins(b, "x") or wins(b, "o") or "b" not in b:
            ends[tuple(b)] = int(wins(b, "x"))
            return
        for i in range(9):
            if b[i] == "b":
                b[i] = turn; rec(b, "o" if turn == "x" else "x"); b[i] = "b"
    rec(["b"] * 9, "x")
    pts = sorted(ends)
    return pts, np.array([ends[p] for p in pts]), [["x", "o", "b"]] * 9


def board_syms():
    r = (6, 3, 0, 7, 4, 1, 8, 5, 2)                                          # rotation: new[i] = old[r[i]]
    f = (2, 1, 0, 5, 4, 3, 8, 7, 6)
    gens = {"id": tuple(range(9))}
    out = set()
    frontier = [tuple(range(9))]
    while frontier:
        q = frontier.pop()
        for g in (r, f):
            c = tuple(q[g[i]] for i in range(9))
            if c not in out:
                out.add(c); frontier.append(c)
    return [s for s in out if s != tuple(range(9))]


def monk():
    doms = [[1, 2, 3], [1, 2, 3], [1, 2], [1, 2, 3], [1, 2, 3, 4], [1, 2]]
    pts = list(itertools.product(*doms))
    m1 = [int(a[0] == a[1] or a[4] == 1) for a in pts]
    m2 = [int(sum(v == 1 for v in a) == 2) for a in pts]
    m3 = [int((a[4] == 3 and a[3] == 1) or (a[4] != 4 and a[1] != 3)) for a in pts]
    return pts, {"MONK-1": np.array(m1), "MONK-2": np.array(m2), "MONK-3": np.array(m3)}, doms


def candidates_ttt():
    syms = [("sym", (lambda s: (lambda x: tuple(x[s[i]] for i in range(9))))(s)) for s in board_syms()]
    dec = []
    for a, b in itertools.combinations(range(9), 2):
        def tr(x, a=a, b=b):
            y = list(x); y[a], y[b] = y[b], y[a]; return tuple(y)
        dec.append(("decoy", tr))
    dec.append(("decoy", lambda x: tuple({"x": "o", "o": "x", "b": "b"}[v] for v in x)))
    return syms + dec


def candidates_monk(doms):
    out = []
    for i, j in itertools.combinations(range(6), 2):
        if doms[i] == doms[j]:
            def sw(x, i=i, j=j):
                y = list(x); y[i], y[j] = y[j], y[i]; return tuple(y)
            out.append(("attr_swap", sw))
    for i, d in enumerate(doms):
        for u, v in itertools.combinations(d, 2):
            def vs(x, i=i, u=u, v=v):
                y = list(x); y[i] = v if x[i] == u else (u if x[i] == v else x[i]); return tuple(y)
            out.append(("value_swap", vs))
    return out


def csp_general(pts, y, lab, cands):
    index = {p: i for i, p in enumerate(pts)}
    images = []
    for kind, fn in cands:
        img = np.array([index.get(fn(p), -1) for p in pts])
        images.append(img)
    acc = []
    for (kind, _), img in zip(cands, images):
        pairs = [(i, img[i]) for i in range(len(pts)) if img[i] >= 0 and img[i] != i and lab[i] and lab[img[i]]]
        if len(pairs) >= 10 and all(y[a] == y[b] for a, b in pairs):
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


def onehot(pts, doms):
    cols = [(i, v) for i, d in enumerate(doms) for v in d]
    return np.array([[1.0 if p[i] == v else 0.0 for i, v in cols] for p in pts])


def train_mlp(X, Y, M, seed, H=64, steps=2000):
    import torch
    torch.manual_seed(seed)
    B, d = Y.shape[0], X.shape[1]
    Xt = torch.tensor(X, dtype=torch.float32).expand(B, -1, -1)
    W1 = (torch.randn(B, d, H) / math.sqrt(d)).requires_grad_(); b1 = torch.zeros(B, 1, H, requires_grad=True)
    W2 = (torch.randn(B, H, 1) / math.sqrt(H)).requires_grad_(); b2 = torch.zeros(B, 1, 1, requires_grad=True)
    Yt, Mt = torch.tensor(Y, dtype=torch.float32), torch.tensor(M, dtype=torch.float32)
    opt = torch.optim.AdamW([W1, b1, W2, b2], lr=0.01, weight_decay=0.01)
    for _ in range(steps):
        opt.zero_grad()
        z = (torch.tanh(Xt @ W1 + b1) @ W2 + b2).squeeze(-1)
        loss = (torch.nn.functional.binary_cross_entropy_with_logits(z, Yt, reduction="none") * Mt).sum(1) / Mt.sum(1)
        loss.sum().backward(); opt.step()
    with torch.no_grad():
        z = (torch.tanh(Xt @ W1 + b1) @ W2 + b2).squeeze(-1)
    return (z >= 0).numpy()


def runB():
    import torch
    torch.set_num_threads(4)
    ttt_pts, ttt_y, ttt_doms = tictactoe()
    mk_pts, mk_ys, mk_doms = monk()
    jobs = [("tic-tac-toe", ttt_pts, ttt_y, ttt_doms, candidates_ttt(), (0.1, 0.2, 0.3))]
    for name, y in mk_ys.items():
        jobs.append((name, mk_pts, y, mk_doms, candidates_monk(mk_doms), (0.15, 0.3)))
    out = {"tictactoe_instances": len(ttt_pts), "tictactoe_positive": int(ttt_y.sum()), "monk_instances": len(mk_pts)}
    for name, pts, y, doms, cands, fracs in jobs:
        X = onehot(pts, doms)
        for frac in fracs:
            rnd = np.random.default_rng(1802)
            labs, rows = [], []
            for s in range(10):
                lab = np.zeros(len(pts), dtype=bool); lab[rnd.choice(len(pts), int(round(frac * len(pts))), replace=False)] = True
                l2, y2, acc, void = csp_general(pts, y, lab, cands)
                labs.append((lab, l2, y2)); rows.append({"accepted": acc, "void": void, "labelled_after": int(l2.sum())})
            Yb = np.array([y for _ in labs] + [y2 for _, _, y2 in labs], dtype=float)
            Mb = np.array([lab for lab, _, _ in labs] + [l2 for _, l2, _ in labs], dtype=float)
            pred = train_mlp(X, Yb, Mb, seed=1803)
            acc_base, acc_csp = [], []
            for s, (lab, _, _) in enumerate(labs):
                test = ~lab
                acc_base.append(float((pred[s][test] == y[test].astype(bool)).mean()))
                acc_csp.append(float((pred[10 + s][test] == y[test].astype(bool)).mean()))
            out[f"{name}@{frac}"] = {"acc_base": acc_base, "acc_csp": acc_csp, "runs": rows}
            print(name, frac, round(np.mean(acc_base), 3), "->", round(np.mean(acc_csp), 3), flush=True)
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "B.json").write_text(json.dumps(out))


def analyseB():
    d = json.loads((RAW / "B.json").read_text())
    res = {k: d[k] for k in ("tictactoe_instances", "tictactoe_positive", "monk_instances")}
    for k, v in d.items():
        if "@" not in k:
            continue
        r = {"acc_base": float(np.mean(v["acc_base"])), "acc_csp": float(np.mean(v["acc_csp"])),
             "gain": float(np.mean(v["acc_csp"]) - np.mean(v["acc_base"])),
             "voided_runs": sum(x["void"] for x in v["runs"]),
             "mean_labelled_after": float(np.mean([x["labelled_after"] for x in v["runs"]])),
             "accepted_kinds": dict(sorted(((kk, sum(x["accepted"].count(kk) for x in v["runs"])) for kk in {a for x in v["runs"] for a in x["accepted"]})))}
        if k.startswith("tic"):
            r["runs_with_any_decoy_accepted"] = sum("decoy" in x["accepted"] for x in v["runs"])
        res[k] = r
        print(k, r, flush=True)
    save("armB", res)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "runA":
        for n in sys.argv[2:]:
            runA(n)
    elif cmd == "runB":
        runB()
    else:
        analyseA(); analyseB()
