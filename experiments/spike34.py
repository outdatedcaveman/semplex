"""Spike 34 (pre-registered in SPIKE_34_REPORT.md): the compiler's minimum-circuit-cost completion as a generalization prior.

  python -m experiments.spike34
"""

from __future__ import annotations

import json
import pathlib

import numpy as np
from scipy.stats import spearmanr

from experiments import spike14 as S14, spike29 as S29, spike30 as S30, spike32 as S32
from experiments.spike09 import tgt

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "experiments" / "results" / "spike34.json"


def bal(p, t):
    return 0.5 * ((p & t).sum() / t.sum() + ((~p) & (~t)).sum() / (~t).sum())


def completions(f, seen, held):
    base = sum(int((f >> x) & 1) << x for x in seen)
    out = []
    for m in range(16):
        c = base
        for j, x in enumerate(held):
            if (m >> j) & 1:
                c |= 1 << x
        out.append(c)
    return np.array(out, dtype=np.int64)


def vote(cands, held, seen_major):
    bits = np.array([[(c >> x) & 1 for x in held] for c in cands], dtype=float)
    v = bits.mean(0)
    return np.where(v == 0.5, seen_major, v > 0.5)


def main():
    tb, ex, els, iso = S14.setup()
    fs = np.array([e for _ in range(10) for e in els]); T = tgt(fs).astype(bool); care = S30.masks(len(fs))
    occ, ties, exact_n, total, cheaper_than_target, cand_store = [], [], 0, 0, 0, []
    for b in range(len(fs)):
        seen = np.nonzero(care[b])[0]; held = np.nonzero(~care[b])[0]
        C = completions(int(fs[b]), seen, held)
        exact_n += int(sum(tb.exact(int(c)) for c in C)); total += len(C)
        key = tb.hi[C].astype(np.int64) * 8 + tb.depth[C].astype(np.int64)
        mins = C[key == key.min()]
        cheaper_than_target += int(tb.hi[mins[0]] < tb.hi[int(fs[b])])
        sm = T[b, seen].mean() > 0.5
        occ.append(vote(mins, held, sm)); ties.append(len(mins)); cand_store.append((C, mins, held, sm))
    occ = np.array(occ); tru_all = np.array([T[b, ~care[b]] for b in range(len(fs))])
    res = {"exact_fraction": exact_n / total, "mean_minimal_ties": float(np.mean(ties)),
           "frac_tasks_with_cheaper_completion_than_target": cheaper_than_target / len(fs),
           "occam_bal_all": float(bal(occ, tru_all)), "occam_acc_all": float((occ == tru_all).mean()), "rows": {}}
    dis_n = dis_occ_net = 0
    for a in S29.ACTS:
        d30 = json.loads((S30.RAW / f"{a}.json").read_text()); post = np.array(json.loads((S32.RAW / f"{a}.json").read_text())["post"])
        fit = np.array(d30["fit"]); net = np.array(d30["net"])
        # Occam -> volume: tie-break by the init-prior frequency table restricted to the minimal completions
        freq = S32.freq_table(a)
        ov = []
        for b in range(len(fs)):
            C, mins, held, sm = cand_store[b]
            if len(mins) == 1:
                ov.append(vote(mins, held, sm)); continue
            w = freq[mins] + 0.5; w = w / w.sum()
            bits = np.array([[(c >> x) & 1 for x in held] for c in mins], dtype=float)
            v = w @ bits
            ov.append(np.where(np.isclose(v, 0.5), sm, v > 0.5))
        ov = np.array(ov)
        n, p_, o, ovf, t = net[fit], post[fit], occ[fit], ov[fit], tru_all[fit]
        dis = n != p_; dis_n += int(dis.sum()); dis_occ_net += int((o == n)[dis].sum())
        res["rows"][a] = {"bal_net": float(bal(n, t)), "bal_post": float(bal(p_, t)), "bal_occam": float(bal(o, t)),
                          "bal_occam_volume": float(bal(ovf, t)), "agree_net_occam": float((n == o).mean()),
                          "agree_net_post": float((n == p_).mean())}
        print(a, {k: round(v, 3) for k, v in res["rows"][a].items()}, flush=True)
    R = res["rows"]; ks = sorted(R)
    res["H34.1_occam_bal"] = res["occam_bal_all"]
    res["H34.2_rho_agreeoccam_balnet"] = float(spearmanr([R[k]["agree_net_occam"] for k in ks], [R[k]["bal_net"] for k in ks]).correlation)
    res["H34.3_occam_sides_with_net_on_net_posterior_disagreements"] = dis_occ_net / dis_n; res["pooled_disagreements"] = dis_n
    res["H34.4_mean_bal_occam_volume_minus_occam"] = float(np.mean([R[k]["bal_occam_volume"] - R[k]["bal_occam"] for k in ks]))
    OUT.write_text(json.dumps(res, indent=1))
    print({k: v for k, v in res.items() if k != "rows"})


if __name__ == "__main__":
    main()
