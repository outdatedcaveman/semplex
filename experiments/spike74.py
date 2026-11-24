"""Spike 74: prospective test of gated smoothness (C41, post hoc in Spike 73): the leader is the smoothest
constituent along the letters among those with predictive-kernel share >= THETA (fixed at 0.08 before any run),
energy breaking smoothness ties. Against pure predictive energy (C37). Trainer of Spike 71. See SPIKE_74_REPORT.md."""
import json, os, sys
import numpy as np
from experiments.spike58 import cyc, closure
import experiments.spike69 as S69
import experiments.spike71 as S71

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "results", "spike74_raw")
OUT = os.path.join(ROOT, "results", "spike74.json")
PRED = os.path.join(ROOT, "results", "spike74_predictions.json")
SEEDS, THETA = 5, 0.08


def zstep(n, s): return tuple((i + s) % n for i in range(n))
def dih(m):
    return [cyc(m, list(range(m))), tuple((-i) % m for i in range(m))]

TABLE = {
    # cyclic, gated smoothness and energy disagree
    "Z9_s1_014": ([zstep(9, 1)], {0, 1, 4}), "Z9_s2_014": ([zstep(9, 2)], {0, 1, 4}),
    "Z10_s1_014": ([zstep(10, 1)], {0, 1, 4}), "Z10_s1_024": ([zstep(10, 1)], {0, 2, 4}),
    "Z10_s3_026": ([zstep(10, 3)], {0, 2, 6}),
    # cyclic, agreement controls
    "Z7_s1_01": ([zstep(7, 1)], {0, 1}), "Z7_s2_01": ([zstep(7, 2)], {0, 1}),
    # dihedral, energy ties broken by gated smoothness
    "D5_pt": (dih(5), "pt"), "D6_pt": (dih(6), "pt"),
}
NAMES = list(TABLE)


def spec(name):
    g, S = TABLE[name]; n = len(g[0])
    out = (lambda x, n=n: tuple(int(x[0] == i) for i in range(n))) if S == "pt" else (lambda x, S=frozenset(S): (int(x[0] in S),))
    return sorted(closure(g)), g + [tuple(range(n))], out


def predict_one(name):
    S71.spec = spec; S71._patch()
    G, Kc, _ = S69.predictive_kernel(name); irs = S69.real_irreps(G); wt = S69.isotypic_weights(Kc, irs)
    lab = [S69.irrep_label(ir, k) for k, ir in enumerate(irs)]; L = spec(name)[1]
    sm = {l: S69.smoothness(ir, G, L) for l, ir in zip(lab, irs)}
    srt = sorted(wt, key=wt.get, reverse=True); energy = srt[0] if wt[srt[0]] >= 1.5 * wt[srt[1]] else None
    pres = [l for l in wt if wt[l] >= THETA]; gated = max(pres, key=lambda l: (round(sm[l], 6), wt[l]))
    return {"energy": energy, "gated": gated, "present": {l: [wt[l], sm[l]] for l in pres},
            "all": {l: [wt[l], sm[l], ir["faithful"]] for l, ir in zip(lab, irs)}}


def predict():
    P = {n: predict_one(n) for n in NAMES}
    for n, p in P.items(): print(n, "energy", p["energy"], "gated", p["gated"], {k: [round(v[0], 2), round(v[1], 2)] for k, v in p["present"].items()})
    json.dump(P, open(PRED, "w"), indent=1)


def run(which=None):
    import torch
    torch.set_num_threads(2); os.makedirs(RAW, exist_ok=True)
    S71.spec = spec
    for name in (NAMES if which is None else which.split(",")):
        for i in range(SEEDS):
            p = os.path.join(RAW, f"{name}_{i}.json")
            if os.path.exists(p): continue
            r = S71.run_one(name, 7400 + 10 * NAMES.index(name) + i); r.pop("traj", None)
            json.dump(r, open(p, "w"), indent=1)
            print(name, i, round(r["fit"], 3), r["final_leader"], r["final_leader_white"], flush=True)


def analyse():
    P = json.load(open(PRED))
    load = lambda n: [json.load(open(os.path.join(RAW, f"{n}_{i}.json"))) for i in range(SEEDS) if os.path.exists(os.path.join(RAW, f"{n}_{i}.json"))]
    fit = {n: [r for r in load(n) if r["fit"] >= 0.99] for n in NAMES}
    ok = [r for n in NAMES if len(fit[n]) >= 3 for r in fit[n]]
    tri = lambda f, hi, lo: "NO VERDICT" if f is None else "HELD" if f >= hi else "BROKEN" if f < lo else "NEITHER"
    frac = lambda xs: float(np.mean(xs)) if xs else None
    f1 = frac([r["final_leader"] == P[r["automaton"]]["gated"] for r in ok])
    dis = [r for r in ok if P[r["automaton"]]["energy"] and P[r["automaton"]]["energy"] != P[r["automaton"]]["gated"]]
    fg = frac([r["final_leader"] == P[r["automaton"]]["gated"] for r in dis]); fe = frac([r["final_leader"] == P[r["automaton"]]["energy"] for r in dis])
    ties = [r for r in ok if r["automaton"].startswith("D")]
    f3 = frac([r["final_leader"] == P[r["automaton"]]["gated"] for r in ties])
    nq = lambda rs: len({r["automaton"] for r in rs})
    v = {"H74.1": tri(f1, 0.8, 0.5) if nq(ok) >= 5 else "NO VERDICT",
         "H74.2": ("NO VERDICT" if nq(dis) < 3 else "HELD" if fg >= 0.8 else "BROKEN" if fe >= 0.5 else "NEITHER"),
         "H74.3": tri(f3, 0.8, 0.5) if nq(ties) >= 1 else "NO VERDICT"}
    per = {n: {"pred": {"energy": P[n]["energy"], "gated": P[n]["gated"]}, "fits": [round(r["fit"], 3) for r in load(n)],
               "final": [r["final_leader"] for r in load(n)], "white": [r["final_leader_white"] for r in load(n)], "fitted": len(fit[n])} for n in NAMES}
    out = {"verdicts": v, "frac": {"gated_all": f1, "discrim_gated": fg, "discrim_energy": fe, "dihedral_gated": f3}, "per": per}
    json.dump(out, open(OUT, "w"), indent=1); print(json.dumps(v, indent=1)); print(json.dumps(out["frac"], indent=1))
    for n, x in per.items(): print(n, x)


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "run": run(sys.argv[2] if len(sys.argv) > 2 else None)
    else: {"predict": predict, "analyse": analyse}[c]()
