"""Spike 62: prospective test of the sufficiency law C31''' on new readouts. Reuses Spike 60's
training and measurement code with new subgroups. See SPIKE_62_REPORT.md."""
import itertools, json, os, sys
import numpy as np
import experiments.spike60 as S
from experiments.spike58 import comp, inv, cyc, closure
from experiments.theory.sufficiency_lp import iso_features, separable, faithful

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "results", "spike62_raw")
OUT = os.path.join(ROOT, "results", "spike62.json")
PRED = os.path.join(ROOT, "results", "spike62_predictions.json")
SUB = {"S4_6c": [cyc(4, [0, 1, 2, 3])], "S4_8": [cyc(4, [0, 1, 2])], "S4_12b": [cyc(4, [0, 1], [2, 3])],
       "A5_10": [cyc(5, [0, 1, 2]), cyc(5, [0, 1], [3, 4])], "A5_15": [cyc(5, [0, 1], [2, 3]), cyc(5, [0, 2], [1, 3])]}
AUTOMATA = list(SUB)
_old = S.subgroup
S.subgroup = lambda name: closure(SUB[name]) if name in SUB else _old(name)


def predict():
    out = {}
    for name in AUTOMATA:
        G, H, cos, lab = S.setup(name); tab, _ = S.irreps(name)
        names = [k for k, _ in tab]; dim = {k: int(round(f(G[0]))) for k, f in tab}
        feats = {k: iso_features(G, f) for k, f in tab}; ok = []
        for r in range(1, len(tab) + 1):
            for sub in itertools.combinations(names, r):
                F = np.concatenate([feats[k] for k in sub], 1)
                if faithful(G, [f for k, f in tab if k in sub]) and all(separable(F, np.array([lab[x] == c for x in G], float)) for c in range(len(cos))):
                    ok.append((sum(dim[k] for k in sub), list(sub)))
        m = min(d for d, _ in ok)
        out[name] = [s for d, s in ok if d == m]
        print(name, out[name])
    json.dump(out, open(PRED, "w"), indent=1)


def run():
    import torch
    torch.set_num_threads(2)
    os.makedirs(RAW, exist_ok=True)
    for name in AUTOMATA:
        assert S.minimal_size(name) == len(S.make(name)[0]), name
        for i in range(5):
            p = os.path.join(RAW, f"{name}_{i}.json")
            if os.path.exists(p): continue
            r = run_one(name, 6200 + 10 * AUTOMATA.index(name) + i)
            json.dump(r, open(p, "w"), indent=1)
            print(name, i, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items() if k in ("fit", "first99", "best_irrep", "rho_readout")}, flush=True)


def analyse():
    pred = json.load(open(PRED))
    runs = [json.load(open(os.path.join(RAW, f"{n}_{i}.json"))) for n in AUTOMATA for i in range(5)]
    by = {n: [r for r in runs if r["automaton"] == n and r["fit"] >= 0.99] for n in AUTOMATA}
    ok = [n for n in AUTOMATA if len(by[n]) >= 3]
    single = [n for n in ok if all(len(s) == 1 for s in pred[n])]
    h1 = [r["best_irrep"] in {s[0] for s in pred[n]} for n in single for r in by[n]]
    f1 = float(np.mean(h1)) if h1 else None
    tri = lambda f, hi, lo: "NO VERDICT" if f is None else "HELD" if f >= hi else "BROKEN" if f < lo else "NEITHER"
    v = {"H62.1": tri(f1, 0.8, 0.5)}
    two = [r for r in by.get("S4_12b", []) if "S4_12b" in ok]
    if two:
        h2 = []
        for r in two:
            best_set = max(r["set_scores"].values())
            h2.append(best_set > max(r["irrep_scores"].values()) and best_set > r["rho_readout"])
        f2 = float(np.mean(h2))
    else:
        f2 = None
    v["H62.2"] = tri(f2, 0.8, 0.5)
    h3 = [max(r["set_scores"].values()) > r["rho_readout"] for n in ok for r in by[n]]
    f3 = float(np.mean(h3)) if h3 else None
    v["H62.3"] = tri(f3, 0.8, 0.5)
    out = {"verdicts": v, "predictions": pred, "fitted": {n: len(by[n]) for n in AUTOMATA}, "H62_1_frac": f1, "H62_2_frac": f2, "H62_3_frac": f3,
           "best_irrep": {n: [r["best_irrep"] for r in by[n]] for n in AUTOMATA}, "runs": runs}
    json.dump(out, open(OUT, "w"), indent=1)
    print(json.dumps(v, indent=1))


def run_one(name, seed):
    """Spike 60's GRU procedure (same recipe and measurements) plus set-kernel scores."""
    import torch
    from scipy.stats import spearmanr
    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    Sx, L, st, out, s0 = S.make(name); k_out = len(out(s0))
    m = S.build("gru", len(L), k_out)
    opt = torch.optim.Adam(m.parameters(), lr=0.003); sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, S.STEPS)
    first99 = -1
    for step in range(S.STEPS):
        X, Y, _ = S.sample(name, S.BATCH, S.LEN, rng)
        logit = m(torch.tensor(X)); loss = torch.nn.functional.binary_cross_entropy_with_logits(logit, torch.tensor(Y))
        opt.zero_grad(); loss.backward(); opt.step(); sch.step()
        if first99 < 0 and step % 25 == 0 and float(((logit > 0).float() == torch.tensor(Y)).float().mean()) >= 0.99:
            first99 = step
    r = {"automaton": name, "seed": seed, "first99": first99}
    m.eval()
    with torch.no_grad():
        X, Y, _ = S.sample(name, 500, 100, np.random.default_rng(seed + 10**6))
        r["fit"] = float(((m(torch.tensor(X)) > 0).float() == torch.tensor(Y)).float().mean())
        X, Y, ST = S.sample(name, 400, S.LEN, np.random.default_rng(seed + 2 * 10**6))
        H = m.hidden(torch.tensor(X)).numpy()
    idx = {g: i for i, g in enumerate(Sx)}
    lab = np.array([[idx[s] for s in row] for row in ST]); Hs, Ls = H[:, 5:], lab[:, 5:]; d = H.shape[2]
    flatH, flatL = Hs.reshape(-1, d), Ls.ravel()
    present = [j for j in range(len(Sx)) if (flatL == j).any()]
    C = np.stack([flatH[flatL == j].mean(0) for j in present]); el = [Sx[j] for j in present]
    C = C - C.mean(0); C = C / np.linalg.norm(C, axis=1, keepdims=True); Gm = C @ C.T
    iu = np.triu_indices(len(el), 1)
    def score(f):
        K = np.array([[f(comp(inv(a), b)) for b in el] for a in el], float)
        return float(spearmanr(Gm[iu], K[iu])[0])
    pc = S.perm_char(name); tab, _ = S.irreps(name); fd = dict(tab)
    r["rho_readout"] = score(lambda x: pc(x) - 1)
    r["irrep_scores"] = {k: score(f) for k, f in tab}
    r["best_irrep"] = max(r["irrep_scores"], key=r["irrep_scores"].get)
    pred = json.load(open(PRED))[name]
    r["set_scores"] = {"+".join(sub): score(lambda x, sub=sub: sum(fd[k](x) for k in sub)) for sub in pred}
    r["n_states_seen"] = len(el)
    return r


if __name__ == "__main__":
    {"predict": predict, "run": run, "analyse": analyse}[sys.argv[1]]()
