"""Spike 63: deeper transformer with length curriculum on S4_4 and A5_5. See SPIKE_63_REPORT.md."""
import json, math, os, sys
import numpy as np
import experiments.spike60 as S
from experiments.spike58 import comp, inv

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "results", "spike63_raw")
OUT = os.path.join(ROOT, "results", "spike63.json")
AUTOMATA, SEEDS, STEPS, WARM, LEN = ["S4_4", "A5_5"], 3, 15000, 500, 30
PRED = {"S4_4": "std", "A5_5": "chi4"}


def build(nL, k_out):
    import torch
    nn = torch.nn
    class T(nn.Module):
        def __init__(s):
            super().__init__(); s.e = nn.Embedding(nL, 64); s.p = nn.Embedding(LEN, 64)
            layer = nn.TransformerEncoderLayer(64, 4, 256, dropout=0.0, batch_first=True, norm_first=True)
            s.t = nn.TransformerEncoder(layer, 4, enable_nested_tensor=False); s.n = nn.LayerNorm(64); s.h = nn.Linear(64, k_out)
        def hidden(s, X):
            Tn = X.shape[1]; mask = torch.triu(torch.full((Tn, Tn), float("-inf")), 1)
            return s.n(s.t(s.e(X) + s.p(torch.arange(Tn))[None], mask=mask, is_causal=True))
        def forward(s, X):
            return s.h(s.hidden(X))
    return T()


def run_one(name, seed):
    import torch
    from sklearn.linear_model import LogisticRegression
    from scipy.stats import spearmanr
    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    Sx, L, st, out, s0 = S.make(name); m = build(len(L), len(out(s0)))
    opt = torch.optim.AdamW(m.parameters(), lr=0.001)
    sched = lambda t: (t + 1) / WARM if t < WARM else 0.5 * (1 + math.cos(math.pi * (t - WARM) / (STEPS - WARM)))
    sch = torch.optim.lr_scheduler.LambdaLR(opt, sched)
    first99 = -1
    for step in range(STEPS):
        T = int(round(6 + (LEN - 6) * min(1.0, step / (STEPS / 2))))
        X, Y, _ = S.sample(name, 64, T, rng)
        logit = m(torch.tensor(X)); loss = torch.nn.functional.binary_cross_entropy_with_logits(logit, torch.tensor(Y))
        opt.zero_grad(); loss.backward(); opt.step(); sch.step()
        if first99 < 0 and T == LEN and step % 25 == 0 and float(((logit > 0).float() == torch.tensor(Y)).float().mean()) >= 0.99:
            first99 = step
    r = {"automaton": name, "seed": seed, "first99": first99}
    m.eval()
    with torch.no_grad():
        X, Y, _ = S.sample(name, 500, LEN, np.random.default_rng(seed + 10**6))
        r["fit"] = float(((m(torch.tensor(X)) > 0).float() == torch.tensor(Y)).float().mean())
        X, Y, ST = S.sample(name, 400, LEN, np.random.default_rng(seed + 2 * 10**6))
        H = m.hidden(torch.tensor(X)).numpy()
    idx = {g: i for i, g in enumerate(Sx)}
    lab = np.array([[idx[s] for s in row] for row in ST]); Hs, Ls = H[:, 5:], lab[:, 5:]; d = H.shape[2]
    clf = LogisticRegression(max_iter=3000).fit(Hs[:200].reshape(-1, d), Ls[:200].ravel())
    r["probe_acc"] = float(clf.score(Hs[200:].reshape(-1, d), Ls[200:].ravel()))
    flatH, flatL = Hs.reshape(-1, d), Ls.ravel()
    present = [j for j in range(len(Sx)) if (flatL == j).any()]
    C = np.stack([flatH[flatL == j].mean(0) for j in present]); el = [Sx[j] for j in present]
    C = C - C.mean(0); C = C / np.linalg.norm(C, axis=1, keepdims=True); Gm = C @ C.T; iu = np.triu_indices(len(el), 1)
    score = lambda f: float(spearmanr(Gm[iu], np.array([[f(comp(inv(a), b)) for b in el] for a in el], float)[iu])[0])
    pc = S.perm_char(name); tab, mf = S.irreps(name)
    r["rho_readout"] = score(lambda x: pc(x) - 1); r["irrep_scores"] = {k: score(f) for k, f in tab}
    r["best_irrep"] = max(r["irrep_scores"], key=r["irrep_scores"].get)
    return r


def run():
    import torch
    torch.set_num_threads(2); os.makedirs(RAW, exist_ok=True)
    for name in AUTOMATA:
        for i in range(SEEDS):
            p = os.path.join(RAW, f"{name}_{i}.json")
            if os.path.exists(p): continue
            r = run_one(name, 6300 + 10 * AUTOMATA.index(name) + i)
            json.dump(r, open(p, "w"), indent=1)
            print(name, i, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items() if k in ("fit", "first99", "probe_acc", "best_irrep")}, flush=True)


def analyse():
    runs = [json.load(open(os.path.join(RAW, f"{n}_{i}.json"))) for n in AUTOMATA for i in range(SEEDS)]
    fit = {n: [r["fit"] >= 0.99 for r in runs if r["automaton"] == n] for n in AUTOMATA}
    fs, fa = float(np.mean(fit["S4_4"])), float(np.mean(fit["A5_5"]))
    v = {"H63.1": "HELD" if sum(fit["S4_4"]) >= 2 else "BROKEN" if sum(fit["S4_4"]) == 0 else "NEITHER",
         "H63.2": "HELD" if fs - fa >= 2 / 3 - 1e-9 else "BROKEN" if fa >= fs else "NEITHER"}
    fitted = [r for r in runs if r["fit"] >= 0.99]
    if len(fitted) >= 2:
        hits = [r["best_irrep"] == PRED[r["automaton"]] for r in fitted]
        v["H63.3"] = "HELD" if all(hits) else "BROKEN" if not any(hits) else "NEITHER"
    else:
        v["H63.3"] = "NO VERDICT"
    out = {"verdicts": v, "fit_rate": {"S4_4": fs, "A5_5": fa}, "runs": runs}
    json.dump(out, open(OUT, "w"), indent=1); print(json.dumps(v, indent=1))


if __name__ == "__main__":
    {"run": run, "analyse": analyse}[sys.argv[1]]()
