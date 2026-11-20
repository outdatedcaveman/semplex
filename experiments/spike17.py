"""Spike 17 (pre-registered in SPIKE_17_REPORT.md).

  python -m experiments.spike17 arm1                  mechanism of the Curie bias (Spike 14 stored cores)
  python -m experiments.spike17 run3 CELL ...         kernel departures (fresh runs)
  python -m experiments.spike17 run2                  certified symmetry propagation, n = 8
  python -m experiments.spike17 analyse
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
from experiments import spike15 as S15, spike16 as S16
from experiments.spike09 import tgt

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "experiments" / "results" / "spike17_raw"
OUT = ROOT / "experiments" / "results" / "spike17.json"


def save(key, val):
    res = json.loads(OUT.read_text()) if OUT.exists() else {}
    res[key] = val
    OUT.write_text(json.dumps(res, indent=1))


# ------------------------------------------------------------------ arm 1

def beta_fit(xs, ys):
    X, Y = np.array(xs), np.array(ys)
    q = np.quantile(X, np.linspace(0, 1, 7)); bx, by = [], []
    for i in range(6):
        m = (X >= q[i]) & ((X <= q[i + 1]) if i == 5 else (X < q[i + 1]))
        if m.sum() and Y[m].mean() > 0:
            bx.append(X[m].mean()); by.append(math.log(Y[m].mean()))
    return float(np.polyfit(bx, by, 1)[0])


def orbit_beta(mass_by_key, okey, osz):
    """Same estimator as Spike 14: pooled, element-normalized orbit mass vs relative log orbit size."""
    xs, ys = [], []
    for e, masses in mass_by_key.items():
        om = defaultdict(float)
        for k, v in masses.items():
            om[okey[e][k]] += v
        N = sum(om.values()); orbs = list(osz[e]); K = len(orbs)
        if N == 0 or K < 2:
            continue
        lm = np.mean([math.log(osz[e][o]) for o in orbs])
        for o in orbs:
            xs.append(math.log(osz[e][o]) - lm); ys.append(om.get(o, 0.0) / N * K)
    return beta_fit(xs, ys)


def arm1():
    from experiments import spike14 as S14
    tb, ex, els, iso = S14.setup()
    T = atlas.transforms(4)
    okey, osz, uorb = {}, {}, {}
    for e in els:
        G = S14.stab_group(e, T)
        okey[e] = S14.orbit_keys(iso[e], G)
        c = defaultdict(int)
        for o in okey[e].values():
            c[o] += 1
        osz[e] = c
        uorb[e] = {t: min(S14.act(t, idx) for idx in G) for pair in iso[e] for t in pair}
    out = {}
    for env in ("A8", "G8", "A128"):
        d = json.loads((S14.RAW / f"{env}.json").read_text())
        obs, ind, umass = {}, {}, {}
        for e in els:
            c = d["counts"][str(e)]
            tot = {k: c[0].get(k, 0) + c[1].get(k, 0) for k in okey[e]}
            obs[e] = tot
            m = defaultdict(float)
            for k, v in tot.items():
                a, b = map(int, k.split("-"))
                m[a] += v; m[b] += v
            ind[e] = {k: m[int(k.split('-')[0])] * m[int(k.split('-')[1])] for k in okey[e]}
            umass[e] = m
        b_obs = orbit_beta(obs, okey, osz)
        b_ind = orbit_beta(ind, okey, osz)
        # unit-level exponent: unit-orbit mass vs unit-orbit size (units appearing in some isomer of g)
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
        out[env] = {"beta_obs": b_obs, "beta_independent_pairing": b_ind, "beta_unit": beta_fit(xs, ys)}
        print(env, out[env], flush=True)
    save("arm1", out)


# ------------------------------------------------------------------ arm 3

CELLS3 = {"tanh-W8-adam": dict(H=8, act="tanh", opt="adamw", lr=0.03, wd=0.03, steps=4000),
          "tanh-W64-adam": dict(H=64, act="tanh", opt="adamw", lr=0.03, wd=0.03, steps=4000),
          "tanh-W512-adam": dict(H=512, act="tanh", opt="adamw", lr=0.03, wd=0.03, steps=4000),
          "tanh-W8-gd": dict(H=8, act="tanh", opt="gd", lr=0.3, wd=0.003, steps=10000)}


def run3(cell):
    cfg = CELLS3[cell]
    tasks = S15.make_tasks()
    fs = np.array([t["f"] for t in tasks] * 5); cs = np.array([t["care"] for t in tasks] * 5)
    p = train.init(len(fs), cfg["H"], np.random.default_rng(17_000 + list(CELLS3).index(cell)),
                   out_scale=0.5 * math.sqrt(8 / cfg["H"]), dtype=np.float32)
    p, _ = train.train(p, tgt(fs), tgt(cs), cfg["steps"], lr=cfg["lr"], wd=cfg["wd"], opt=cfg["opt"], act=cfg["act"])
    g, _, _ = train.read_circuits(p, act=cfg["act"])
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / f"arm3_{cell}.json").write_text(json.dumps({"cell": cell, "learned": g.tolist()}))
    print("arm3", cell, "done", flush=True)


def analyse3():
    tb = atlas.build_all(4)[4]
    tasks = S15.make_tasks()
    K = S16.ntk("tanh", np.random.default_rng(1702))
    hk = [S16.kernel_completion(K, t["f"], t["care"]) for t in tasks]
    from math import comb
    out = {}
    for f in sorted(RAW.glob("arm3_*.json")):
        d = json.loads(f.read_text())
        same = n = cheaper = costlier = dev = dev_sym = 0
        q_dev = 0.0
        for i, h in enumerate(d["learned"]):
            t = tasks[i % len(tasks)]; care, fv = t["care"], t["f"]
            if (h & care) != (fv & care):
                continue
            n += 1
            k = hk[i % len(tasks)]
            if h == k:
                same += 1
                continue
            ch, ck = int(tb.hi[h]), int(tb.hi[k])
            cheaper += ch < ck; costlier += ch > ck
            comps = [fv & care]
            for x in range(16):
                if not (care >> x) & 1:
                    comps += [c | (1 << x) for c in comps]
            comps = np.array(comps); cost = tb.hi[comps]
            orbs = S15.point_orbits(S15.GROUPS[t["group"]])
            same_cost = comps[cost == ch]
            q = float(np.mean([S15.invariant(int(c), orbs) for c in same_cost]))
            dev += 1; dev_sym += S15.invariant(int(h), orbs); q_dev += q
        m = cheaper + costlier
        p = sum(comb(m, j) for j in range(cheaper, m + 1)) / 2 ** m if m else None
        out[d["cell"]] = {"fit_runs": n, "P_learned_equals_kernel": same / n,
                          "departures": dev, "departures_cheaper": cheaper, "departures_costlier": costlier,
                          "sign_test_p_cheaper": p,
                          "P_symmetric_given_departure": dev_sym / max(dev, 1),
                          "symmetric_share_of_equal_cost_completions": q_dev / max(dev, 1)}
        print(d["cell"], out[d["cell"]], flush=True)
    save("arm3", out)


# ------------------------------------------------------------------ arm 2 (n = 8, torch)

N8 = 8
PTS = np.arange(256)


def pmap(fn):
    return np.array([fn(x) for x in PTS])


def perm_map(perm):
    return pmap(lambda x: sum(((x >> perm[j]) & 1) << j for j in range(N8)))


def neg_map(mask):
    return pmap(lambda x: x ^ mask)


CANDIDATES = ([perm_map(tuple(k if k not in (a, b) else (b if k == a else a) for k in range(N8)))
               for a, b in itertools.combinations(range(N8), 2)]
              + [perm_map(tuple((j + 1) % N8 for j in range(N8))), perm_map(tuple(N8 - 1 - j for j in range(N8)))]
              + [neg_map(1 << j) for j in range(N8)] + [neg_map(255)])


def group_orbits(gens):
    parent = list(range(256))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for g in gens:
        for x in PTS:
            a, b = find(int(x)), find(int(g[x]))
            if a != b:
                parent[a] = b
    orb = defaultdict(list)
    for x in PTS:
        orb[find(int(x))].append(int(x))
    return list(orb.values())


FAMILIES = {"S8": group_orbits([perm_map(tuple((j + 1) % 8 for j in range(8))), perm_map((1, 0, 2, 3, 4, 5, 6, 7))]),
            "C8": group_orbits([perm_map(tuple((j + 1) % 8 for j in range(8)))]),
            "S4xS4": group_orbits([perm_map((1, 2, 3, 0, 4, 5, 6, 7)), perm_map((1, 0, 2, 3, 4, 5, 6, 7)),
                                   perm_map((0, 1, 2, 3, 5, 6, 7, 4)), perm_map((0, 1, 2, 3, 5, 4, 6, 7))]),
            "none": [[int(x)] for x in PTS]}


def make_tasks8():
    rnd = random.Random(1703)
    tasks = []
    for fam, orbs in FAMILIES.items():
        for _ in range(30):
            while True:
                vals = [rnd.randint(0, 1) for _ in orbs]
                y = np.zeros(256, dtype=int)
                for v, o in zip(vals, orbs):
                    y[o] = v
                if 0.2 <= y.mean() <= 0.8:
                    break
            lab = np.zeros(256, dtype=bool); lab[rnd.sample(range(256), 128)] = True
            tasks.append({"family": fam, "y": y, "lab": lab})
    return tasks


def csp(y, lab, oracle_orbs=None):
    """Certified symmetry propagation. Returns (new label mask, new labels, accepted generator count)."""
    if oracle_orbs is None:
        acc = []
        for g in CANDIDATES:
            pairs = [(x, int(g[x])) for x in PTS if lab[x] and lab[g[x]] and g[x] != x]
            if len(pairs) >= 10 and all(y[a] == y[b] for a, b in pairs):
                acc.append(g)
        if not acc:
            return lab.copy(), y.copy(), 0
        orbs = group_orbits(acc)
    else:
        acc, orbs = [None], oracle_orbs
    lab2, y2 = lab.copy(), y.copy()
    for o in orbs:
        ls = {int(y[x]) for x in o if lab[x]}
        if len(ls) > 1:
            return lab.copy(), y.copy(), -1                     # conflict: void
        if len(ls) == 1:
            v = ls.pop()
            for x in o:
                if not lab[x]:
                    lab2[x] = True; y2[x] = v
    return lab2, y2, len(acc)


def train8(Y, M, seed, H=64, steps=3000):
    import torch
    torch.manual_seed(seed)
    X = torch.tensor([[1.0 if (x >> j) & 1 else -1.0 for j in range(N8)] for x in PTS])
    B = Y.shape[0]
    W1 = (torch.randn(B, N8, H) * 0.5).requires_grad_(); b1 = (torch.randn(B, 1, H) * 0.5).requires_grad_()
    W2 = (torch.randn(B, H, 1) * 0.5 * math.sqrt(8 / H)).requires_grad_(); b2 = torch.zeros(B, 1, 1, requires_grad=True)
    Yt, Mt = torch.tensor(Y, dtype=torch.float32), torch.tensor(M, dtype=torch.float32)
    opt = torch.optim.AdamW([W1, b1, W2, b2], lr=0.03, weight_decay=0.03)
    Xb = X.expand(B, -1, -1)
    for _ in range(steps):
        opt.zero_grad()
        z = (torch.tanh(Xb @ W1 + b1) @ W2 + b2).squeeze(-1)
        loss = (torch.nn.functional.binary_cross_entropy_with_logits(z, Yt, reduction="none") * Mt).sum(1) / Mt.sum(1)
        loss.sum().backward(); opt.step()
    with torch.no_grad():
        z = (torch.tanh(Xb @ W1 + b1) @ W2 + b2).squeeze(-1)
    return (z >= 0).numpy()


def run2():
    import torch
    torch.set_num_threads(4)
    tasks = make_tasks8()
    rows = []
    conds = {"base": [], "csp": [], "oracle": []}
    meta = []
    for t in tasks:
        l1, y1, nacc = csp(t["y"], t["lab"])
        l2, y2, _ = csp(t["y"], t["lab"], FAMILIES[t["family"]])
        conds["base"].append((t["y"], t["lab"])); conds["csp"].append((y1, l1)); conds["oracle"].append((y2, l2))
        meta.append({"family": t["family"], "accepted": nacc, "csp_labelled": int(l1.sum()), "oracle_labelled": int(l2.sum())})
    res = {"meta": meta}
    for c, lst in conds.items():
        Y = np.array([a for a, _ in lst] * 3, dtype=float); M = np.array([b for _, b in lst] * 3, dtype=float)
        pred = train8(Y, M, seed=1704)
        acc = []
        for i, t in enumerate(tasks * 3):
            test = ~t["lab"]
            acc.append(float((pred[i][test] == t["y"][test].astype(bool)).mean()))
        res[c] = acc
        print("arm2", c, "done", flush=True)
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "arm2.json").write_text(json.dumps(res))


def analyse2():
    d = json.loads((RAW / "arm2.json").read_text())
    tasks = make_tasks8()
    fam = [t["family"] for t in tasks] * 3
    out = {}
    for F in FAMILIES:
        idx = [i for i, f in enumerate(fam) if f == F]
        base = np.mean([d["base"][i] for i in idx]); cs = np.mean([d["csp"][i] for i in idx]); orc = np.mean([d["oracle"][i] for i in idx])
        mt = [m for m in d["meta"] if m["family"] == F]
        out[F] = {"acc_base": base, "acc_csp": cs, "acc_oracle": orc, "gain_csp": cs - base, "gain_oracle": orc - base,
                  "mean_generators_accepted": float(np.mean([max(m["accepted"], 0) for m in mt])),
                  "tasks_voided_by_conflict": int(sum(m["accepted"] == -1 for m in mt)),
                  "mean_labelled_after_csp": float(np.mean([m["csp_labelled"] for m in mt]))}
        print(F, out[F], flush=True)
    save("arm2", out)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "arm1":
        arm1()
    elif cmd == "run3":
        for c in sys.argv[2:]:
            run3(c)
    elif cmd == "run2":
        run2()
    else:
        analyse3(); analyse2()
