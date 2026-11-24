"""Spike 11: does weight-space volume predict WHICH minimal circuit training finds?

  python -m experiments.spike11

A  width 2 (the minimal circuit itself), 200 seeds per element
B  width 8 (Spike 09's network), 100 seeds per element
Predictor: V(I) = Omega(t1) * Omega(t2), no fitted parameters (cerp/mechvol.py).
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from collections import defaultdict

import numpy as np

from cerp import atlas, mechvol, train
from experiments.spike09 import tgt, wstar_table

ROOT = pathlib.Path(__file__).resolve().parent.parent
STEPS = 3000
OMEGA_SAMPLES = 40_000_000


def run(fs, H, seed, iso_sets, pred, wd=0.03):
    rng = np.random.default_rng(seed)
    p = train.init(len(fs), H, rng)
    _, _, units0 = train.read_circuits(p)
    p, _ = train.train(p, tgt(fs), np.ones((len(fs), 16)), STEPS, wd=wd)
    g, faithful, units = train.read_circuits(p)
    obs = defaultdict(lambda: defaultdict(float))
    fit = g == fs
    stats = {"nets": len(fs), "fit": int(fit.sum()), "faithful_when_fit": float(faithful[fit].mean())}
    with_min, kept_init, n2 = 0, 0, 0
    for b in np.nonzero(fit)[0]:
        f = int(fs[b])
        pairs = [q for q in mechvol.minimal_pairs(units[b], f) if q in iso_sets[f]]
        if not pairs:
            continue
        with_min += 1
        for q in pairs:
            obs[f][q] += 1 / len(pairs)
        if H == 2:
            n2 += 1
            kept_init += set(mechvol.canon(units0[b]).tolist()) == set(mechvol.canon(units[b]).tolist())
    stats["fit_with_minimal_pair"] = with_min
    if H == 2:
        stats["share_final_units_equal_initial_units"] = kept_init / max(n2, 1)
    return obs, stats


def evaluate(obs, pred, iso_sets):
    per = {}
    for f, o in obs.items():
        s = mechvol.score(o, pred[f])
        if s is not None:
            per[f] = s
    runs = sum(s["runs"] for s in per.values())
    agg = {
        "elements_scored": len(per),
        "gain_bits_per_run": sum(s["gain_bits"] * s["runs"] for s in per.values()) / runs,
        "ceiling_bits_per_run_in_sample": sum(s["ceiling_bits"] * s["runs"] for s in per.values()) / runs,
        "share_elements_gain_positive": float(np.mean([s["gain_bits"] > 0 for s in per.values()])),
        "median_spearman": float(np.nanmedian([s["spearman"] for s in per.values()])),
        "top1_hit_rate": float(np.mean([s["top1"] for s in per.values()])),
        "top1_hit_rate_uniform_chance": float(np.mean([1 / s["isomers"] for s in per.values()])),
    }
    # pooled calibration: bin isomers by predicted share, compare observed share
    xs, ys, ws = [], [], []
    for f, s in per.items():
        n = s["runs"]
        for q, pq in pred[f].items():
            xs.append(math.log10(pq)); ys.append(obs[f].get(q, 0.0) / n); ws.append(pq)
    xs, ys = np.array(xs), np.array(ys)
    edges = np.quantile(xs, np.linspace(0, 1, 11))
    bins = []
    for k in range(10):
        m = (xs >= edges[k]) & (xs <= edges[k + 1]) if k == 9 else (xs >= edges[k]) & (xs < edges[k + 1])
        if m.sum() and ys[m].mean() > 0:
            bins.append((float(np.mean(10 ** xs[m])), float(ys[m].mean()), int(m.sum())))
    bx = np.log10([b[0] for b in bins]); by = np.log10([b[1] for b in bins])
    agg["calibration_bins"] = [{"mean_predicted": b[0], "mean_observed": b[1], "isomers": b[2]} for b in bins]
    agg["pooled_loglog_slope"] = float(np.polyfit(bx, by, 1)[0])
    return agg, per


def main():
    t0 = time.time()
    tb = atlas.build_all(4)[4]
    wstar, x2 = wstar_table(tb)
    ex = [int(tb.exhibit[c]) for c in tb.classes()]
    els = [e for e in ex if wstar[e] == 2 and tb.hi[e] == 3]
    omega, ns = mechvol.solid_angles(OMEGA_SAMPLES, np.random.default_rng(1100))
    floor = 0.5 / ns                                                              # unseen functions
    pidx = mechvol.PairIndex(tb.ltf)
    iso_sets, pred = {}, {}
    for e in els:
        iso = pidx.isomers(e)
        v = {q: omega.get(q[0], floor) * omega.get(q[1], floor) for q in iso}
        z = sum(v.values())
        iso_sets[e] = set(iso)
        pred[e] = {q: x / z for q, x in v.items()}
    res = {"elements": len(els), "omega_samples": ns, "threshold_functions_seen": len(omega),
           "steps": STEPS, "weight_decay": 0.03,
           "isomers_per_element": {"min": min(map(len, iso_sets.values())), "max": max(map(len, iso_sets.values())),
                                   "mean": float(np.mean([len(s) for s in iso_sets.values()]))},
           "mean_predicted_share_of_favourite": float(np.mean([max(p.values()) for p in pred.values()]))}
    print(json.dumps(res), flush=True)
    for name, H, seeds, seed in (("A_width2", 2, 200, 1101), ("B_width8", 8, 100, 1108)):
        fs = np.array(els * seeds)
        obs, stats = run(fs, H, seed, iso_sets, pred)
        agg, per = evaluate(obs, pred, iso_sets)
        res[name] = {**stats, **agg}
        res[name + "_per_element"] = {str(f): s for f, s in per.items()}
        print(name, json.dumps({**stats, **{k: v for k, v in agg.items() if k != "calibration_bins"}}), flush=True)
    res["wall_seconds"] = round(time.time() - t0, 1)
    (ROOT / "experiments" / "results" / "spike11.json").write_text(json.dumps(res, indent=1))
    print("done", res["wall_seconds"])


if __name__ == "__main__":
    main()
