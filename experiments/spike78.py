"""Spike 78: closing the loopholes of the Gibbs selection rule (C43, P212), with alpha and lambda FROZEN from Spike 77:
(L1) other learners: LSTM, tanh RNN, GRU trained with SGD; (L2) a random, unselected sample of new automata;
(L3) discriminating subset reported separately; (L4) letter-frequency arm: same group and readout, only input
frequencies change -> usage-weighted cost and kernel predict a flip; (L5) richer rival model (dimension, faithfulness)
on the calibration data; (L6) whitened (reparametrisation-invariant) leaders. See SPIKE_78_REPORT.md."""
import json, os, sys, itertools
import numpy as np
from experiments.spike58 import comp, closure
import experiments.spike69 as S69
import experiments.spike71 as S71
import experiments.spike77 as S77

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "results", "spike78_raw")
OUT = os.path.join(ROOT, "results", "spike78.json")
PRED = os.path.join(ROOT, "results", "spike78_predictions.json")
ALPHA, LAMBDA = S77.ALPHA, S77.LAMBDA
STEPS, LEN, BATCH = 6000, 30, 64
LEARNERS = ["gru_adam", "lstm_adam", "rnn_adam", "gru_sgd"]
FREQ = {"F7_2_013": (7, 2, (0, 1, 3)), "F7_3_013": (7, 3, (0, 1, 3)), "F11_2_024": (11, 2, (0, 2, 4))}
PROBS = {"a": [0.8, 0.1, 0.1], "b": [0.1, 0.8, 0.1]}


def zstep(n, s): return tuple((i + s) % n for i in range(n))

def spec(name):
    if name in FREQ:
        n, s, S = FREQ[name]; g = [zstep(n, 1), zstep(n, s)]; Sf = frozenset(S)
        return sorted(closure(g)), g + [tuple(range(n))], (lambda x, Sf=Sf: (int(x[0] in Sf),))
    return S77.spec(name)


def wkernel(G, L, p, out, T=30):
    n = len(G); idx = {g: i for i, g in enumerate(G)}; O = np.array([out(g) for g in G], float)
    pair = np.zeros((n * n, n * n))
    for g in G:
        for h in G:
            for a, w in zip(L, p): pair[idx[g] * n + idx[h], idx[comp(g, a)] * n + idx[comp(h, a)]] += w
    v = (O @ O.T).ravel(); K = np.zeros(n * n)
    for _ in range(T): v = pair @ v; K += v
    K = K.reshape(n, n); return K - K.mean(0) - K.mean(1)[:, None] + K.mean()


def feats(name, p=None):
    G, L, out = spec(name); p = p or [1 / len(L)] * len(L)
    irs = S69.real_irreps(G); wt = S69.isotypic_weights(wkernel(G, L, p, out), irs)
    idx = {g: i for i, g in enumerate(G)}; e = idx[tuple(range(len(G[0])))]
    nz = [(a, w) for a, w in zip(L, p) if a != tuple(range(len(G[0])))]
    F = {}
    for k, ir in enumerate(irs):
        lab = S69.irrep_label(ir, k)
        c = sum(w * (1 - ir["P"][e, idx[a]] / ir["P"][e, e]) for a, w in nz) / sum(w for _, w in nz)
        F[lab] = (max(wt[lab], 1e-6), c, ir["dim_real_sq"], ir["faithful"])
    return F


def probs(F, a, lam, extra=None):
    ks = list(F); s = np.array([a * np.log(F[k][0]) - lam * F[k][1] + (0 if extra is None else extra[0] * np.log(F[k][2]) + extra[1] * F[k][3]) for k in ks])
    pr = np.exp(s - s.max()); return dict(zip(ks, pr / pr.sum()))


def predict():
    P77 = json.load(open(S77.PRED)); used = set(P77["automata"]) | S77.USED
    pool = sorted(n for n in S77.POOL if n not in used)
    rng = np.random.default_rng(78); sample = sorted(rng.choice(pool, size=12, replace=False).tolist())
    rows = {}
    for n in sample:
        F = feats(n); pg = probs(F, ALPHA, LAMBDA); pe = probs(F, P77["energy_alpha"], 0.0); ps = probs(F, 0.0, P77["smooth_lambda"])
        rows[n] = {"gibbs": pg, "energy": pe, "smooth": ps, "argmax": {m: max(d, key=d.get) for m, d in (("gibbs", pg), ("energy", pe), ("smooth", ps))}}
    freq = {}
    for n in FREQ:
        for c, p in PROBS.items():
            F = feats(n, p); pg = probs(F, ALPHA, LAMBDA); freq[f"{n}_{c}"] = {"gibbs": pg, "argmax": max(pg, key=pg.get), "pmax": max(pg.values())}
    P = {"alpha": ALPHA, "lambda": LAMBDA, "energy_alpha": P77["energy_alpha"], "smooth_lambda": P77["smooth_lambda"], "sample": sample, "rows": rows, "freq": freq}
    json.dump(P, open(PRED, "w"), indent=1)
    for n in sample: print(n, rows[n]["argmax"], round(max(rows[n]["gibbs"].values()), 2))
    for k, v in freq.items(): print(k, v["argmax"], round(v["pmax"], 2))


def train(name, learner, seed, p=None):
    import torch
    nn = torch.nn
    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    G, L, out = spec(name); idx = {g: i for i, g in enumerate(G)}; e = tuple(range(len(G[0]))); k = len(out(e))
    p = np.array(p or [1 / len(L)] * len(L))
    arch, opt_name = learner.split("_")
    R = {"gru": nn.GRU, "lstm": nn.LSTM, "rnn": nn.RNN}[arch]
    class Net(nn.Module):
        def __init__(s): super().__init__(); s.e = nn.Embedding(len(L), 16); s.r = R(16, 64, batch_first=True); s.h = nn.Linear(64, k)
        def hidden(s, X): return s.r(s.e(X))[0]
        def forward(s, X): return s.h(s.hidden(X))
    m = Net()
    opt = torch.optim.Adam(m.parameters(), lr=0.003) if opt_name == "adam" else torch.optim.SGD(m.parameters(), lr=0.1, momentum=0.9)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, STEPS)
    def sample(B, T, r):
        X = r.choice(len(L), size=(B, T), p=p); Y = np.zeros((B, T, k), np.float32); ST = np.zeros((B, T), int)
        for b in range(B):
            s_ = e
            for t in range(T): s_ = comp(s_, L[X[b, t]]); Y[b, t] = out(s_); ST[b, t] = idx[s_]
        return X, Y, ST
    for _ in range(STEPS):
        X, Y, _ = sample(BATCH, LEN, rng)
        loss = nn.functional.binary_cross_entropy_with_logits(m(torch.tensor(X)), torch.tensor(Y))
        opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(m.parameters(), 5.0); opt.step(); sch.step()
    with torch.no_grad():
        X, Y, _ = sample(500, 100, np.random.default_rng(seed + 10**6)); fit = float(((m(torch.tensor(X)) > 0).float() == torch.tensor(Y)).float().mean())
        X, Y, ST = sample(400, LEN, np.random.default_rng(seed + 2 * 10**6)); H = m.hidden(torch.tensor(X)).numpy()
    irs = S69.real_irreps(G); labels = [S69.irrep_label(ir, kk) for kk, ir in enumerate(irs)]
    flatH, flatL = H[:, 5:].reshape(-1, 64), ST[:, 5:].ravel()
    present = sorted(set(flatL.tolist()))
    Ce = np.stack([flatH[flatL == j].mean(0) if j in present else np.zeros(64) for j in range(len(G))])
    C1 = Ce - Ce.mean(0); C1 = C1 / np.maximum(np.linalg.norm(C1, axis=1, keepdims=True), 1e-12)
    Rr = flatH - Ce[flatL]; W = np.cov(Rr.T) + 1e-4 * np.eye(64); ev, EV = np.linalg.eigh(W); C2 = (Ce - Ce.mean(0)) @ EV @ np.diag(ev ** -0.5) @ EV.T
    s1, s2 = S71.shares(C1, irs), S71.shares(C2, irs)
    return {"fit": fit, "leader": labels[int(np.argmax(s1))], "leader_white": labels[int(np.argmax(s2))], "shares": dict(zip(labels, s1.tolist()))}


def run(which=None):
    import torch
    torch.set_num_threads(2); os.makedirs(RAW, exist_ok=True); P = json.load(open(PRED))
    jobs = [(n, l, None) for l in LEARNERS for n in P["sample"]] + [(n, "gru_adam", c) for n in FREQ for c in PROBS]
    if which: jobs = [j for j in jobs if j[1] in which.split(",") or (j[2] and "freq" in which)]
    for name, learner, c in jobs:
        for i in range(3 if c is None else 4):
            tag = f"{name}_{learner}" + (f"_{c}" if c else "") + f"_{i}"; pth = os.path.join(RAW, tag + ".json")
            if os.path.exists(pth): continue
            seed = 7800 + 1000 * LEARNERS.index(learner) + 10 * (sorted(P["sample"]).index(name) if c is None else 200 + list(FREQ).index(name) * 2 + list(PROBS).index(c)) + i
            r = train(name, learner, seed, PROBS[c] if c else None); r.update({"automaton": name, "learner": learner, "freq": c, "seed": seed})
            json.dump(r, open(pth, "w")); print(tag, round(r["fit"], 3), r["leader"], r["leader_white"], flush=True)


def analyse():
    P = json.load(open(PRED)); runs = [json.load(open(os.path.join(RAW, f))) for f in sorted(os.listdir(RAW))]
    fit = [r for r in runs if r["fit"] >= 0.99]
    nll = lambda rs, m: -sum(np.log(P["rows"][r["automaton"]][m][r["leader"]] + 1e-12) for r in rs)
    acc = lambda rs, key="leader": float(np.mean([r[key] == P["rows"][r["automaton"]]["argmax"]["gibbs"] for r in rs])) if rs else None
    v = {}; det = {}
    for l in LEARNERS:
        rs = [r for r in fit if r["learner"] == l and r["freq"] is None]; na = len({r["automaton"] for r in rs})
        det[l] = {"n_runs": len(rs), "n_automata": na, "acc": acc(rs), "nll": {m: nll(rs, m) for m in ("gibbs", "energy", "smooth")} if rs else None,
                  "acc_discriminating": acc([r for r in rs if len(set(P["rows"][r["automaton"]]["argmax"].values())) > 1])}
    g = det["gru_adam"]
    v["H78.1"] = "NO VERDICT" if g["n_automata"] < 6 else ("HELD" if g["acc"] >= 0.75 and g["nll"]["gibbs"] < min(g["nll"]["energy"], g["nll"]["smooth"]) else "BROKEN" if g["acc"] < 0.5 else "NEITHER")
    others = [l for l in LEARNERS[1:] if det[l]["n_automata"] >= 6]
    wins = [det[l]["nll"]["gibbs"] < min(det[l]["nll"]["energy"], det[l]["nll"]["smooth"]) for l in others]
    v["H78.2"] = "NO VERDICT" if len(others) < 2 else ("HELD" if all(wins) else "BROKEN" if sum(not w for w in wins) >= 2 else "NEITHER")
    # H78.3 per-learner exchange rate (leave-one-automaton-out argmax accuracy with refitted alpha, lambda)
    from scipy.optimize import minimize
    def loo(rs):
        names = sorted({r["automaton"] for r in rs}); hits = []
        Fc = {n: feats(n) for n in names}
        for nm in names:
            tr = [r for r in rs if r["automaton"] != nm]
            f = lambda pp: -sum(np.log(probs(Fc[r["automaton"]], pp[0], pp[1])[r["leader"]] + 1e-12) for r in tr)
            x = minimize(f, [ALPHA, LAMBDA], method="Nelder-Mead").x
            pr = probs(Fc[nm], x[0], x[1]); hits += [r["leader"] == max(pr, key=pr.get) for r in rs if r["automaton"] == nm]
        full = minimize(lambda pp: -sum(np.log(probs(Fc[r["automaton"]], pp[0], pp[1])[r["leader"]] + 1e-12) for r in rs), [ALPHA, LAMBDA], method="Nelder-Mead").x
        return float(np.mean(hits)), float(full[1] / max(abs(full[0]), 1e-6))
    for l in LEARNERS:
        rs = [r for r in fit if r["learner"] == l and r["freq"] is None]
        det[l]["loo_acc"], det[l]["rate"] = loo(rs) if len({r["automaton"] for r in rs}) >= 6 else (None, None)
    accs = [det[l]["loo_acc"] for l in LEARNERS if det[l]["loo_acc"] is not None]
    v["H78.3"] = "NO VERDICT" if len(accs) < 3 else ("HELD" if min(accs) >= 0.7 else "BROKEN" if min(accs) < 0.5 else "NEITHER")
    # H78.4 frequency flip
    fr = [r for r in runs if r["freq"] is not None]
    f4 = float(np.mean([r["leader"] == P["freq"][f"{r['automaton']}_{r['freq']}"]["argmax"] for r in fr])) if fr else None
    v["H78.4"] = "NO VERDICT" if f4 is None else ("HELD" if f4 >= 0.8 else "BROKEN" if f4 < 0.5 else "NEITHER")
    # H78.5 richer rival on calibration data (log dimension, faithfulness added): LOO NLL improvement < 10%
    import experiments.theory.exchange_rate as XR
    cs = [c for c in XR.cases if c[0] == "default"]
    def ext_feats(c):
        G = None
        return c
    # reconstruct dimension/faithfulness from labels r<k>_tr<d2>_ker<K>
    def F4(F):
        out = {}
        for lab, (e_, c_) in F.items():
            d2 = int(lab.split("_tr")[1].split("_")[0]); ker = int(lab.split("_ker")[1]); out[lab] = (e_, c_, d2, int(ker == 1))
        return out
    def nll_cs(cs_, pp, rich):
        t = 0.0
        for _, _, F, obs in cs_:
            pr = probs(F4(F), pp[0], pp[1], (pp[2], pp[3]) if rich else None)
            t -= sum(np.log(pr[o] + 1e-12) for o in obs if o in pr)
        return t
    names = sorted({c[1] for c in cs}); l2 = l4 = 0.0
    for nm in names:
        tr = [c for c in cs if c[1] != nm]; te = [c for c in cs if c[1] == nm]
        x2 = minimize(lambda pp: nll_cs(tr, pp, False), [ALPHA, LAMBDA], method="Nelder-Mead").x
        x4 = minimize(lambda pp: nll_cs(tr, pp, True), [ALPHA, LAMBDA, 0.0, 0.0], method="Nelder-Mead").x
        l2 += nll_cs(te, x2, False); l4 += nll_cs(te, list(x4), True)
    imp = (l2 - l4) / l2
    v["H78.5"] = "HELD" if imp < 0.10 else "BROKEN" if imp >= 0.25 else "NEITHER"
    # H78.6 whitened leaders
    rsw = [r for r in fit if r["freq"] is None]
    f6 = acc(rsw, "leader_white")
    v["H78.6"] = "NO VERDICT" if not rsw else ("HELD" if f6 >= 0.7 else "BROKEN" if f6 < 0.5 else "NEITHER")
    out = {"verdicts": v, "learners": det, "freq_acc": f4, "rich_loo_improvement": imp, "loo_nll_2param": l2, "loo_nll_4param": l4, "white_acc": f6,
           "freq_runs": {f"{r['automaton']}_{r['freq']}_{r['seed']}": (r["leader"], round(r["fit"], 3)) for r in fr}}
    json.dump(out, open(OUT, "w"), indent=1); print(json.dumps(v, indent=1))
    print(json.dumps({k: out[k] for k in ("freq_acc", "rich_loo_improvement", "white_acc")}, indent=1))
    for l, d in det.items(): print(l, {k: (round(x, 3) if isinstance(x, float) else x) for k, x in d.items() if k != "nll"}, {m: round(x, 1) for m, x in (d["nll"] or {}).items()})


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "run": run(sys.argv[2] if len(sys.argv) > 2 else None)
    else: {"predict": predict, "analyse": analyse}[c]()
