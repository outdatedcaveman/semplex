"""Spike 73: the smoothness pull (C40). (A) cyclic groups with letter step +s vs readout spectrum;
(B) A5 on its 6 axes with icosahedral letters, fit repaired (no identity letter, 12k steps);
(C) unsigned-axis tracking with large rotation steps. Reuses frozen Spikes 69-72 code. See SPIKE_73_REPORT.md."""
import json, os, sys
import numpy as np
from experiments.spike58 import comp, cyc, closure
import experiments.spike69 as S69
import experiments.spike71 as S71
import experiments.spike72 as S72

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "results", "spike73_raw")
OUT = os.path.join(ROOT, "results", "spike73.json")
PRED = os.path.join(ROOT, "results", "spike73_predictions.json")
SEEDS = 5


def step(n, s): return cyc(n, [(i * s) % n for i in range(n)]) if False else tuple((i + s) % n for i in range(n))

CYC = {  # name: (n, s, readout set on c = x[0])
    "Z11_s1_03": (11, 1, {0, 3}), "Z11_s3_03": (11, 3, {0, 3}), "Z11_s3_012": (11, 3, {0, 1, 2}),
    "Z13_s1_05": (13, 1, {0, 5}), "Z13_s5_012": (13, 5, {0, 1, 2}), "Z13_s5_05": (13, 5, {0, 5}),
}
SIGMAS = {"AX_s050": 0.5, "AX_s100": 1.0}
A5ENC = ["A5_ONEHOT", "A5_RHO3"]
A5_STEPS = 12000


def cyc_spec(name):
    n, s, Sset = CYC[name]
    g = [step(n, s)]; G = sorted(closure(g))
    return G, g + [tuple(range(n))], (lambda x, Sset=Sset: (int(x[0] in Sset),))


def cyc_predict(name):
    S71.spec = cyc_spec; S71._patch()
    n, s, _ = CYC[name]
    G, Kc, _ = S69.predictive_kernel(name); irs = S69.real_irreps(G); wt = S69.isotypic_weights(Kc, irs)
    labels = [S69.irrep_label(ir, k) for k, ir in enumerate(irs)]
    _, L, _ = cyc_spec(name)
    sm = {l: S69.smoothness(ir, G, L) for l, ir in zip(labels, irs)}
    faithful = [l for l, ir in zip(labels, irs) if ir["faithful"]]
    srt = sorted(wt, key=wt.get, reverse=True)
    energy = srt[0] if wt[srt[0]] >= 1.5 * wt[srt[1]] else None
    smooth = max(faithful, key=sm.get)
    # frequency label for readability: k with cos(2 pi k / n) = P(e, +1)/P(e,e) using the +1 element
    idx = {g: i for i, g in enumerate(G)}; e = idx[tuple(range(n))]; one = idx[tuple((i + 1) % n for i in range(n))]
    freq = {l: int(round(np.degrees(np.arccos(np.clip(ir["P"][e, one] / ir["P"][e, e], -1, 1))) / (360 / n))) for l, ir in zip(labels, irs)}
    return {"energy": energy, "smooth": smooth, "shares": wt, "smoothness": sm, "freq": freq}


def predict():
    out = {"cyclic": {}, "A5": {}, "axis": {}}
    for name in CYC:
        p = cyc_predict(name); out["cyclic"][name] = p
        print(name, "energy", p["energy"], "k=", p["freq"].get(p["energy"]), "smooth", p["smooth"], "k=", p["freq"][p["smooth"]], {p["freq"][l]: round(v, 2) for l, v in p["shares"].items()})
    P72 = json.load(open(S72.PRED))
    out["A5"] = {"A5_ONEHOT": P72["ONEHOT"], "A5_RHO3": P72["RHO3"]}
    out["axis"] = {k: "RP2 (no sign) under C40: steps far from identity" for k in SIGMAS}
    json.dump(out, open(PRED, "w"), indent=1); print(json.dumps(out["A5"]))


def run_a5(enc, seed):
    """Spike 72's discrete trainer, without the identity letter and with A5_STEPS steps."""
    orig_spec, orig_steps = S72.disc_spec, S72.STEPS
    def spec_noid():
        G, L, out = orig_spec(); return G, L[:2], out
    S72.disc_spec = spec_noid; S72.STEPS = A5_STEPS
    try:
        if enc == "A5_RHO3":
            M = S72.rho3(); L = spec_noid()[1]
            # run_disc builds features from L via rho3(); identity letter absent so L has 2 letters
        r = S72.run_disc(enc.split("_")[1], seed)
    finally:
        S72.disc_spec, S72.STEPS = orig_spec, orig_steps
    r["enc"] = enc; return r


def run_axis(name, seed):
    import experiments.spike70 as S70
    old = S70.SIG; S70.SIG = SIGMAS[name]
    try:
        r = S72.run_cont("OMEGA", seed)
    finally:
        S70.SIG = old
    r["enc"] = name; r["sigma"] = SIGMAS[name]; return r


def run_cyc(name, seed):
    S71.spec = cyc_spec
    r = S71.run_one(name, seed); r.pop("traj", None); return r


JOBS = list(CYC) + A5ENC + list(SIGMAS)


def run(which=None):
    import torch
    torch.set_num_threads(2); os.makedirs(RAW, exist_ok=True)
    for name in (JOBS if which is None else which.split(",")):
        for i in range(SEEDS):
            p = os.path.join(RAW, f"{name}_{i}.json")
            if os.path.exists(p): continue
            seed = 7300 + 10 * JOBS.index(name) + i
            r = run_cyc(name, seed) if name in CYC else run_a5(name, seed) if name in A5ENC else run_axis(name, seed)
            json.dump(r, open(p, "w"), indent=1)
            print(name, i, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items() if k in ("fit", "fit_r2", "final_leader", "final_leader_white", "leader", "leader_white", "sign_probe_balanced", "R2_l1", "R2_l2")}, flush=True)


def analyse():
    P = json.load(open(PRED))
    load = lambda n: [json.load(open(os.path.join(RAW, f"{n}_{i}.json"))) for i in range(SEEDS) if os.path.exists(os.path.join(RAW, f"{n}_{i}.json"))]
    tri = lambda f, hi, lo: "NO VERDICT" if f is None else "HELD" if f >= hi else "BROKEN" if f < lo else "NEITHER"
    frac = lambda xs: float(np.mean(xs)) if xs else None
    cyc_fit = {n: [r for r in load(n) if r["fit"] >= 0.99] for n in CYC}
    ok = [r for n in CYC if len(cyc_fit[n]) >= 3 for r in cyc_fit[n]]
    f1 = frac([r["final_leader"] == P["cyclic"][r["automaton"]]["smooth"] for r in ok])
    dis = [r for r in ok if P["cyclic"][r["automaton"]]["energy"] and P["cyclic"][r["automaton"]]["energy"] != P["cyclic"][r["automaton"]]["smooth"]]
    f2s = frac([r["final_leader"] == P["cyclic"][r["automaton"]]["smooth"] for r in dis]); f2e = frac([r["final_leader"] == P["cyclic"][r["automaton"]]["energy"] for r in dis])
    v = {"H73.1": tri(f1, 0.8, 0.5) if len({r["automaton"] for r in ok}) >= 4 else "NO VERDICT",
         "H73.2": ("NO VERDICT" if len({r["automaton"] for r in dis}) < 2 else "HELD" if f2s >= 0.8 else "BROKEN" if f2e >= 0.5 else "NEITHER")}
    a5 = {e: [r for r in load(e) if r["fit"] >= 0.99] for e in A5ENC}
    f3 = frac([r["leader"] == P["A5"]["A5_RHO3"] for r in a5["A5_RHO3"]]) if len(a5["A5_RHO3"]) >= 3 else None
    f4 = frac([r["leader"] == P["A5"]["A5_ONEHOT"] for r in a5["A5_ONEHOT"]]) if len(a5["A5_ONEHOT"]) >= 3 else None
    v["H73.3"] = tri(f3, 0.8, 0.5); v["H73.4"] = tri(f4, 0.8, 0.5)
    ax = [r for r in load("AX_s100") if r["fit_r2"] >= 0.9]
    if len(ax) >= 3:
        c = frac([r["sign_probe_balanced"] <= 0.75 for r in ax]); b = frac([r["sign_probe_balanced"] >= 0.95 for r in ax])
        v["H73.5"] = "HELD" if c >= 0.8 else "BROKEN" if b >= 0.5 else "NEITHER"
    else: v["H73.5"] = "NO VERDICT"
    per = {}
    for n in JOBS:
        rs = load(n)
        per[n] = [{k: (round(x, 3) if isinstance(x, float) else x) for k, x in r.items() if k in ("seed", "fit", "fit_r2", "final_leader", "final_leader_white", "leader", "leader_white", "sign_probe_balanced", "R2_l1", "R2_l2")} for r in rs]
    out = {"verdicts": v, "frac": {"H73_1_smooth": f1, "H73_2_smooth": f2s, "H73_2_energy": f2e, "H73_3": f3, "H73_4": f4},
           "fitted": {n: (len(cyc_fit[n]) if n in CYC else len(a5[n]) if n in A5ENC else len([r for r in load(n) if r["fit_r2"] >= 0.9])) for n in JOBS},
           "per": per}
    json.dump(out, open(OUT, "w"), indent=1); print(json.dumps(v, indent=1)); print(json.dumps(out["frac"], indent=1)); print(out["fitted"])


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "run": run(sys.argv[2] if len(sys.argv) > 2 else None)
    else: {"predict": predict, "analyse": analyse}[c]()
