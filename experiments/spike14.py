"""Spike 14: a Curie principle for learning, and other bold candidates (charter/ABDUCTION.md section 5).

  python -m experiments.spike14 run A8|G8|A128|U1|PART     (raw output to results/spike14_raw/)
  python -m experiments.spike14 analyse

Pre-registered in experiments/SPIKE_14_REPORT.md. Fresh seeds (base 14_000); 128 elements,
80 of which were never scored before.
"""

from __future__ import annotations

import json
import math
import pathlib
import random
import sys
import time
from collections import defaultdict

import numpy as np

from cerp import atlas, mechvol, train
from experiments import spike12 as S12
from experiments.spike09 import tgt, wstar_table

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "experiments" / "results" / "spike14_raw"
FULL = 0xFFFF
SEEDS, HALF = 40, 20
CHECKS = (10, 20, 50, 100, 200, 500, 1000, 2000)
BETA = -2.0                        # fixed from the exploratory screen BEFORE fresh data: orbit mass ~ |orbit|^BETA
ENVS = {
    "A8": dict(H=8, opt="adamw", lr=0.03, wd=0.03, steps=3000),
    "G8": dict(H=8, opt="gd", lr=0.3, wd=0.003, steps=10000),
    "A128": dict(H=128, opt="adamw", lr=0.03, wd=0.03, steps=3000),
}


def setup():
    tb = atlas.build_all(4)[4]
    wstar, _ = wstar_table(tb)
    ex = [int(tb.exhibit[c]) for c in tb.classes()]
    els = [e for e in ex if wstar[e] == 2 and tb.hi[e] == 3]
    pidx = mechvol.PairIndex(tb.ltf)
    iso = {e: pidx.isomers(e) for e in els}
    return tb, ex, els, iso


# ------------------------------------------------------------------ symmetry (B0, B1)

def stab_group(g, T):
    return [idx for _, _, idx in T if atlas.apply_T(g, idx, False, 4) in (g, FULL ^ g)]


def act(t, idx):
    return int(mechvol.canon(atlas.apply_T(t, idx, False, 4)))


def orbit_keys(iso, G):
    return {f"{a}-{b}": min(tuple(sorted((act(a, idx), act(b, idx)))) for idx in G) for a, b in iso}


# ------------------------------------------------------------------ runs

def run_env(name):
    cfg = ENVS[name]
    tb, ex, els, iso = setup()
    H = cfg["H"]
    fs = np.array([e for _ in range(SEEDS) for e in els])
    rng = np.random.default_rng(14_000 + list(ENVS).index(name))
    p = train.init(len(fs), H, rng, scale=0.5, out_scale=0.5 * math.sqrt(8 / H), dtype=np.float32)
    T, C = tgt(fs), np.ones((len(fs), 16))
    state, done, traj = None, 0, []
    t0 = time.time()
    for cp in CHECKS + (cfg["steps"],):
        p, state = train.train(p, T, C, cp - done, lr=cfg["lr"], wd=cfg["wd"], opt=cfg["opt"], state=state)
        done = cp
        traj.append(train.read_circuits(p)[0])
    g, faithful, units = train.read_circuits(p)
    counts = {str(e): [defaultdict(float), defaultdict(float)] for e in els}
    fossils = {str(e): [] for e in els}                       # per credited run: (fossil or None, credited keys)
    fit = g == fs
    for b in np.nonzero(fit)[0]:
        e, half = int(fs[b]), int(b // (len(els) * HALF))
        pre = S12.r2_prefix(units[b], p["W2"][b], e)
        if pre is None:
            continue
        c2 = S12.credit({int(x) for x in mechvol.canon(pre)}, iso[e])
        if not c2:
            continue
        for k, v in c2.items():
            counts[str(e)][half][k] += v
        fossil = None
        for gt in traj[:-1]:
            h = int(gt[b])
            if h != e and h not in (0, FULL) and int(tb.hi[h]) == 1:
                fossil = int(mechvol.canon(h))
        fossils[str(e)].append([fossil, c2])
    out = {"env": name, **cfg, "elements": els, "nets": len(fs), "fit": float(fit.mean()),
           "faithful_when_fit": float(faithful[fit].mean()), "train_seconds": round(time.time() - t0, 1),
           "counts": counts, "fossils": fossils}
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / f"{name}.json").write_text(json.dumps(out))
    print(name, {k: v for k, v in out.items() if k in ("fit", "faithful_when_fit", "train_seconds")}, flush=True)


def run_single_unit():
    """B4: what does ONE unit converge to on g? 200 seeds per element, AdamW, 3000 steps."""
    tb, ex, els, iso = setup()
    fs = np.array([e for _ in range(200) for e in els])
    p = train.init(len(fs), 1, np.random.default_rng(14_100), scale=0.5, out_scale=0.5 * math.sqrt(8), dtype=np.float32)
    p, _ = train.train(p, tgt(fs), np.ones((len(fs), 16)), 3000, lr=0.03, wd=0.03)
    _, _, units = train.read_circuits(p)
    U = defaultdict(lambda: defaultdict(int))
    for b in range(len(fs)):
        U[str(int(fs[b]))][str(int(mechvol.canon(units[b, 0])))] += 1
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "U1.json").write_text(json.dumps(U))
    print("U1 done", flush=True)


def run_partial():
    """B1 at the level of functions: which cheapest completion does training pick?"""
    tb, ex, els, iso = setup()
    rnd = random.Random(1401)
    tasks = []
    for e in ex:
        for _ in range(6):
            care = sum(1 << x for x in rnd.sample(range(16), 8))
            tasks.append((e, care))
    fs = np.array([t[0] for t in tasks] * 5)
    cs = np.array([t[1] for t in tasks] * 5)
    p = train.init(len(fs), 8, np.random.default_rng(14_200), scale=0.5, dtype=np.float32)
    p, _ = train.train(p, tgt(fs), tgt(cs), 4000, lr=0.03, wd=0.03)
    g, _, _ = train.read_circuits(p)
    out = [[int(f), int(c), int(h)] for f, c, h in zip(fs, cs, g)]
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "PART.json").write_text(json.dumps(out))
    print("PART done", flush=True)


# ------------------------------------------------------------------ analysis

def stab_size_table(tb):
    """|Stab(h)| in the group of input permutations/negations and output negation (order 768)."""
    sizes = np.bincount(tb.canon, minlength=65536)
    return 768 // sizes[tb.canon]


def analyse():
    tb, ex, els, iso = setup()
    T = atlas.transforms(4)
    seen = set(S12.elements()[1])
    pc = lambda t: bin(t).count("1")
    omega, ns = mechvol.solid_angles(40_000_000, np.random.default_rng(1100))
    U = json.loads((RAW / "U1.json").read_text())
    pre = {}
    for e in els:
        ok = orbit_keys(iso[e], stab_group(e, T))
        osz = defaultdict(int)
        for o in ok.values():
            osz[o] += 1
        deg = defaultdict(int)
        for a, b in iso[e]:
            deg[a] += 1; deg[b] += 1
        ag = {b: max(16 - pc(b ^ e), pc(b ^ e)) for b in omega if b not in (0,)}
        m = max(ag.values())
        tstar = {b for b, v in ag.items() if v == m}
        u = U[str(e)]; nu = sum(u.values())
        pr = {}
        for a, b in iso[e]:
            k = f"{a}-{b}"
            pr[k] = {"curie": (BETA - 1) * math.log(osz[ok[k]]),
                     "vol": math.log(omega.get(a, 0.5 / ns) * omega.get(b, 0.5 / ns)),
                     "agree": max(ag[a], ag[b]),
                     "hub": deg[a] + deg[b],
                     "U": math.log((u.get(str(a), 0) + 0.5) / nu) + math.log((u.get(str(b), 0) + 0.5) / nu),
                     "tstar": float(a in tstar or b in tstar)}
        pre[e] = (ok, osz, pr, tstar)
    res = {}
    for env in ENVS:
        f = RAW / f"{env}.json"
        if not f.exists():
            continue
        d = json.loads(f.read_text())
        r = {"fit": d["fit"], "faithful_when_fit": d["faithful_when_fit"]}
        for subset, sel in (("all", els), ("unseen", [e for e in els if e not in seen])):
            r[subset] = score_env(d, sel, pre)
        res[env] = r
    res["PART"] = partial_test(tb)
    (ROOT / "experiments" / "results" / "spike14.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


def score_env(d, sel, pre):
    out = {}
    # H14.1 within-orbit share of count variance, against a multinomial null with the same orbit masses
    obs_share, null_share = [], []
    rng = np.random.default_rng(1402)
    betas_x, betas_y, strata = [], [], []
    gains = defaultdict(list)
    rhos = defaultdict(list)
    fos = {"runs": 0, "with_fossil": 0, "core_has_fossil": 0.0, "fossil_baseline": 0.0, "core_has_tstar": 0.0}
    for e in sel:
        ok, osz, pr, tstar = pre[e]
        c = d["counts"][str(e)]
        tot = {k: c[0].get(k, 0) + c[1].get(k, 0) for k in pr}
        N = sum(tot.values())
        if N == 0:
            continue
        keys = list(pr)
        y = np.array([tot[k] for k in keys])
        orb = defaultdict(list)
        for k in keys:
            orb[ok[k]].append(tot[k])
        if len(orb) < len(keys) and y.var() > 0:
            obs_share.append(sum(np.var(v) * len(v) for v in orb.values()) / (y.var() * len(y)))
            # null: same orbit masses, spread multinomially and uniformly within orbits
            p_iso = np.array([sum(orb[ok[k]]) / len(orb[ok[k]]) for k in keys]); p_iso /= p_iso.sum()
            sim = rng.multinomial(int(round(N)), p_iso)
            so = defaultdict(list)
            for k, v in zip(keys, sim):
                so[ok[k]].append(v)
            null_share.append(sum(np.var(v) * len(v) for v in so.values()) / max(sim.var() * len(sim), 1e-12))
        # B1 beta at the orbit level
        mass = {o: sum(v) for o, v in orb.items()}
        K = len(mass)
        if K >= 2:
            lm = np.mean([math.log(osz[o]) for o in mass])
            for o in mass:
                betas_x.append(math.log(osz[o]) - lm); betas_y.append(mass[o] / N * K)
            # H14.3: within strata of equal agreement
            byag = defaultdict(list)
            for o in mass:
                k0 = next(k for k in keys if ok[k] == o)
                byag[pr[k0]["agree"]].append((osz[o], mass[o]))
            for lst in byag.values():
                if len(lst) >= 3 and len({s for s, _ in lst}) > 1:
                    strata.append(mechvol._spearman(np.array([m for _, m in lst], float), np.array([s for s, _ in lst], float)))
        # predictors: rank and log-likelihood gain over uniform
        for s in ("curie", "vol", "agree", "hub", "U"):
            x = np.array([pr[k][s] for k in keys], float)
            rhos[s].append(mechvol._spearman(y, x))
        for s in ("curie", "vol", "U"):
            lw = np.array([pr[k][s] for k in keys]); lw -= lw.max(); q = np.exp(lw); q /= q.sum()
            gains[s].append((sum(tot[k] * math.log2(q[i] * len(keys)) for i, k in enumerate(keys)), N))
        # B3 fossil
        iso_keys = keys
        for fossil, c2 in d["fossils"][str(e)]:
            fos["runs"] += 1
            fos["core_has_tstar"] += sum(v for k, v in c2.items() if pr[k]["tstar"])
            if fossil is None:
                continue
            fos["with_fossil"] += 1
            has = lambda k: fossil in map(int, k.split("-"))
            fos["core_has_fossil"] += sum(v for k, v in c2.items() if has(k))
            fos["fossil_baseline"] += np.mean([has(k) for k in iso_keys])
    X, Y = np.array(betas_x), np.array(betas_y)
    q = np.quantile(X, np.linspace(0, 1, 7)); bx, by = [], []
    for i in range(6):
        m = (X >= q[i]) & ((X <= q[i + 1]) if i == 5 else (X < q[i + 1]))
        if m.sum() and Y[m].mean() > 0:
            bx.append(float(X[m].mean())); by.append(math.log(Y[m].mean()))
    out["H14.1_within_orbit_share"] = {"observed": float(np.mean(obs_share)), "multinomial_null": float(np.mean(null_share)), "elements": len(obs_share)}
    out["H14.2_beta"] = float(np.polyfit(bx, by, 1)[0])
    out["H14.2_bins"] = list(zip(bx, by))
    out["H14.3_within_agreement_strata"] = {"strata": len(strata), "median_spearman_mass_vs_orbit_size": float(np.nanmedian(strata)) if strata else None,
                                            "share_negative": float(np.mean([s < 0 for s in strata if not math.isnan(s)])) if strata else None}
    out["median_spearman"] = {s: float(np.nanmedian(v)) for s, v in rhos.items()}
    out["gain_bits_per_run"] = {s: sum(g for g, _ in v) / sum(n for _, n in v) for s, v in gains.items()}
    n = fos["runs"]; nf = fos["with_fossil"]
    nonmin, niso = [], []
    for e in sel:
        c = d["counts"][str(e)]
        nonmin.append(1 - (sum(c[0].values()) + sum(c[1].values())) / SEEDS)
        niso.append(math.log(len(pre[e][2])))
    out["H14.9_spearman_nonminimal_vs_log_isomers"] = mechvol._spearman(np.array(nonmin), np.array(niso))
    out["B3_fossil"] = {"credited_runs": n, "runs_with_fossil": nf,
                        "share_core_has_fossil": fos["core_has_fossil"] / nf if nf else None,
                        "fossil_isomer_baseline": fos["fossil_baseline"] / nf if nf else None,
                        "share_core_has_tstar_all_runs": fos["core_has_tstar"] / n if n else None}
    return out


def partial_test(tb):
    rows = json.loads((RAW / "PART.json").read_text())
    stab = stab_size_table(tb)
    up = dn = eq = skipped = 0
    for f, care, h in rows:
        if (h & care) != (f & care):
            continue
        comps = [f & care]
        for x in range(16):
            if not (care >> x) & 1:
                comps += [c | (1 << x) for c in comps]
        comps = np.array(comps)
        cost = tb.hi[comps]
        cheapest = comps[cost == cost.min()]
        if tb.hi[h] != cost.min() or len(set(stab[cheapest].tolist())) < 2:
            skipped += 1
            continue
        m = stab[cheapest].astype(float).mean()
        s = stab[h]
        up += s > m; dn += s < m; eq += s == m
    from fractions import Fraction
    from math import comb
    up, dn, eq = int(up), int(dn), int(eq)
    n = up + dn
    p = float(Fraction(sum(comb(n, k) for k in range(up, n + 1)), 2 ** n)) if n else None
    return {"learned_more_symmetric_than_mean_cheapest": up, "less": dn, "equal": eq, "skipped": skipped,
            "share_up": up / n if n else None, "one_sided_sign_test_p": p}


if __name__ == "__main__":
    if sys.argv[1] == "run":
        for n in sys.argv[2:]:
            {"U1": run_single_unit, "PART": run_partial}.get(n, lambda: run_env(n))()
    else:
        analyse()
