"""Spike 76: is predictive energy a variational principle? Interventions predicted by the 'truncated Hankel realisation /
predictive information bottleneck' picture (charter/FOUNDATIONS.md §15):
(W) state-width bottleneck -> keep the top-energy constituents (Eckart-Young);
(N) noise on the state (a cost on memory) -> prune constituents from the lowest energy up;
(T) unconstrained learning acquires the top-energy constituent first.
GRU (gradients) and an evolution-strategies GRU (width arm). See SPIKE_76_REPORT.md."""
import json, os, sys
import numpy as np
import experiments.spike69 as S69
import experiments.spike71 as S71
import experiments.spike74 as S74
import experiments.spike75 as S75

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "results", "spike76_raw")
OUT = os.path.join(ROOT, "results", "spike76.json")
PRED = os.path.join(ROOT, "results", "spike76_predictions.json")
SEEDS, STEPS, LEN, BATCH, PRESENT = 5, 6000, 30, 64, 0.15
AUT = ["Z9_s1_014", "Z10_s1_014", "S4_12"]
CKPT = list(range(100, 3001, 100)) + list(range(3500, STEPS + 1, 500))


def spec(name):
    if name in S75.TABLE: return S75.spec(name)
    return S74.spec(name)


def energy_order(name):
    S71.spec = spec; S71._patch()
    G, Kc, _ = S69.predictive_kernel(name); irs = S69.real_irreps(G); wt = S69.isotypic_weights(Kc, irs)
    return sorted([l for l in wt if wt[l] > 1e-3], key=wt.get, reverse=True), wt


CONFIGS = ([("W", a, r, 0.0, "GRU") for a, r in [("Z9_s1_014", 2), ("Z9_s1_014", 4), ("Z10_s1_014", 2), ("Z10_s1_014", 4), ("S4_12", 3)]]
           + [("N", a, 64, eta, "GRU") for a in AUT for eta in (0.0, 0.3, 1.0)]
           + [("W", a, 2, 0.0, "ES") for a in ("Z9_s1_014", "Z10_s1_014")])
cname = lambda c: f"{c[0]}_{c[4]}_{c[1]}_w{c[2]}_n{c[3]}"


def predict():
    P = {}
    for a in AUT:
        order, wt = energy_order(a); P[a] = {"order": order, "shares": wt}
        print(a, [(l, round(wt[l], 2)) for l in order])
    for c in CONFIGS:
        kind, a, r, eta, sub = c; order = P[a]["order"]
        if kind == "W":
            if a.startswith("S4"): k = 1
            else: k = r // 2           # each cyclic constituent is a 2-dim real irreducible here
            P[cname(c)] = {"predicted_top": order[:k]}
    json.dump(P, open(PRED, "w"), indent=1)
    print({k: v for k, v in P.items() if k.startswith("W")})


def make_model(nL, k_out, width):
    import torch
    nn = torch.nn
    class Net(nn.Module):
        def __init__(s):
            super().__init__(); s.e = nn.Embedding(nL, 16); s.c = nn.GRUCell(16, width); s.h = nn.Linear(width, k_out); s.eta = 0.0
        def hidden(s, X, noise=False):
            h = torch.zeros(X.shape[0], s.c.hidden_size); E = s.e(X); out = []
            for t in range(X.shape[1]):
                h = s.c(E[:, t], h)
                if noise and s.eta > 0: h = h + s.eta * torch.randn_like(h)
                out.append(h)
            return torch.stack(out, 1)
        def forward(s, X, noise=False): return s.h(s.hidden(X, noise))
    return Net()


def geometry(name, H, ST):
    S71.spec = spec; S71._patch()
    G = spec(name)[0]; irs = S69.real_irreps(G); labels = [S69.irrep_label(ir, k) for k, ir in enumerate(irs)]
    flatH, flatL = H[:, 5:].reshape(-1, H.shape[-1]), ST[:, 5:].ravel()
    Ce = np.stack([flatH[flatL == j].mean(0) for j in range(len(G))])
    C1 = Ce - Ce.mean(0); C1 = C1 / np.maximum(np.linalg.norm(C1, axis=1, keepdims=True), 1e-12)
    return dict(zip(labels, S71.shares(C1, irs).tolist()))


def run_gru(c, seed):
    import torch
    kind, a, width, eta, _ = c
    torch.manual_seed(seed); rng = np.random.default_rng(seed); G, L, out = spec(a); k = len(out(tuple(range(len(G[0])))))
    m = make_model(len(L), k, width); m.eta = eta
    opt = torch.optim.Adam(m.parameters(), lr=0.003); sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, STEPS)
    Xe, Ye, STe = S75.sample(a, 400, LEN, np.random.default_rng(seed + 2 * 10**6)); traj = []
    for step in range(1, STEPS + 1):
        X, Y, _ = S75.sample(a, BATCH, LEN, rng)
        loss = torch.nn.functional.binary_cross_entropy_with_logits(m(torch.tensor(X), noise=True), torch.tensor(Y))
        opt.zero_grad(); loss.backward(); opt.step(); sch.step()
        if kind == "N" and eta == 0.0 and step in CKPT:
            with torch.no_grad(): traj.append({"step": step, "shares": geometry(a, m.hidden(torch.tensor(Xe)).numpy(), STe)})
    with torch.no_grad():
        X, Y, _ = S75.sample(a, 500, 100, np.random.default_rng(seed + 10**6))
        fit = float(((torch.sigmoid(m(torch.tensor(X))) > 0.5).float() == torch.tensor(Y)).float().mean())
        sh = geometry(a, m.hidden(torch.tensor(Xe)).numpy(), STe)
    return {"fit": fit, "shares": sh, "traj": traj}


def run_es(c, seed, iters=4000, pop=64, sigma=0.05, lr=0.03):
    import torch
    from torch.nn.utils import parameters_to_vector, vector_to_parameters
    kind, a, width, eta, _ = c
    torch.manual_seed(seed); rng = np.random.default_rng(seed); G, L, out = spec(a); k = len(out(tuple(range(len(G[0])))))
    m = make_model(len(L), k, width); theta = parameters_to_vector(m.parameters()).detach().clone(); mo = torch.zeros_like(theta); vv = torch.zeros_like(theta)
    def lossv(v, X, Y):
        vector_to_parameters(v, m.parameters())
        with torch.no_grad(): return float(torch.nn.functional.binary_cross_entropy_with_logits(m(X), Y))
    for it in range(1, iters + 1):
        Xn, Yn, _ = S75.sample(a, 32, 20, rng); X, Y = torch.tensor(Xn), torch.tensor(Yn)
        eps = torch.randn(pop // 2, theta.numel()); eps = torch.cat([eps, -eps])
        f = torch.tensor([lossv(theta + sigma * e_, X, Y) for e_ in eps]); rk = torch.argsort(torch.argsort(f)).float(); w = rk / (len(f) - 1) - 0.5
        g = (w[:, None] * eps).sum(0) / (len(f) * sigma); mo = 0.9 * mo + 0.1 * g; vv = 0.999 * vv + 0.001 * g * g
        theta = theta - lr * (mo / (1 - 0.9 ** it)) / (torch.sqrt(vv / (1 - 0.999 ** it)) + 1e-8)
    vector_to_parameters(theta, m.parameters())
    Xe, Ye, STe = S75.sample(a, 400, LEN, np.random.default_rng(seed + 2 * 10**6))
    with torch.no_grad():
        X, Y, _ = S75.sample(a, 500, 100, np.random.default_rng(seed + 10**6))
        fit = float(((torch.sigmoid(m(torch.tensor(X))) > 0.5).float() == torch.tensor(Y)).float().mean())
        sh = geometry(a, m.hidden(torch.tensor(Xe)).numpy(), STe)
    return {"fit": fit, "shares": sh, "traj": []}


def run(which=None):
    import torch
    torch.set_num_threads(2); os.makedirs(RAW, exist_ok=True)
    cs = CONFIGS if which is None else [c for c in CONFIGS if c[4] in which.split(",") or c[0] in which.split(",")]
    for c in cs:
        for i in range(SEEDS if c[4] == "GRU" else 3):
            p = os.path.join(RAW, f"{cname(c)}_{i}.json")
            if os.path.exists(p): continue
            seed = 7600 + 10 * CONFIGS.index(c) + i
            r = run_gru(c, seed) if c[4] == "GRU" else run_es(c, seed)
            r.update({"config": cname(c), "kind": c[0], "automaton": c[1], "width": c[2], "eta": c[3], "substrate": c[4], "seed": seed})
            json.dump(r, open(p, "w"))
            top = sorted(r["shares"], key=r["shares"].get, reverse=True)[:3]
            print(cname(c), i, round(r["fit"], 3), [(t, round(r["shares"][t], 2)) for t in top], flush=True)


def analyse():
    P = json.load(open(PRED)); runs = [json.load(open(os.path.join(RAW, f))) for f in sorted(os.listdir(RAW))]
    tri = lambda f, hi, lo: "NO VERDICT" if f is None else "HELD" if f >= hi else "BROKEN" if f < lo else "NEITHER"
    frac = lambda xs: float(np.mean(xs)) if xs else None
    top_set = lambda sh, k: set(sorted(sh, key=sh.get, reverse=True)[:k])
    # H76.1 width bottleneck (GRU): the k largest learned shares = the k top-energy constituents
    w = [r for r in runs if r["kind"] == "W" and r["substrate"] == "GRU"]
    f1 = frac([top_set(r["shares"], len(P[r["config"]]["predicted_top"])) == set(P[r["config"]]["predicted_top"]) for r in w])
    # H76.2 noise pruning: at every eta, the present set (share >= PRESENT) is a prefix of the energy order
    def prefix(r):
        order = P[r["automaton"]]["order"]; pres = {l for l, v in r["shares"].items() if v >= PRESENT}
        return pres == set(order[:len(pres)]) and len(pres) > 0
    n = [r for r in runs if r["kind"] == "N"]
    f2 = frac([prefix(r) for r in n])
    # monotone: number present non-increasing in eta, per (automaton, seed index)
    mono = []
    for a in AUT:
        for i in range(SEEDS):
            cnt = [sum(v >= PRESENT for v in r["shares"].values()) for eta in (0.0, 0.3, 1.0) for r in n if r["automaton"] == a and r["eta"] == eta and r["seed"] % 10 == i]
            if len(cnt) == 3: mono.append(cnt[0] >= cnt[1] >= cnt[2])
    f2m = frac(mono)
    # H76.3 acquisition order: the top-energy constituent reaches half its final share first (eta = 0, fitted)
    def first_acq(r):
        order = P[r["automaton"]]["order"]; fin = r["shares"]; cand = [l for l in order if fin[l] >= 0.1]
        t = {}
        for l in cand:
            for pt in r["traj"]:
                if pt["shares"][l] >= 0.5 * fin[l]: t[l] = pt["step"]; break
        if not t: return None
        tmin = min(t.values()); return order[0] in t and t[order[0]] == tmin
    acq = [first_acq(r) for r in n if r["eta"] == 0.0 and r["fit"] >= 0.99]
    acq = [x for x in acq if x is not None]; f3 = frac(acq)
    # H76.4 ES width bottleneck
    es = [r for r in runs if r["kind"] == "W" and r["substrate"] == "ES"]
    f4 = frac([top_set(r["shares"], 1) == set(P[r["config"]]["predicted_top"]) for r in es])
    v = {"H76.1": tri(f1, 0.8, 0.5), "H76.2": ("NO VERDICT" if f2 is None else "HELD" if f2 >= 0.8 and (f2m or 0) >= 0.8 else "BROKEN" if f2 < 0.5 else "NEITHER"),
         "H76.3": tri(f3, 0.8, 0.5) if len(acq) >= 5 else "NO VERDICT", "H76.4": tri(f4, 0.8, 0.5) if len(es) >= 3 else "NO VERDICT"}
    per = {}
    for r in runs:
        top = sorted(r["shares"], key=r["shares"].get, reverse=True)[:3]
        per.setdefault(r["config"], []).append({"fit": round(r["fit"], 3), "top": [(t, round(r["shares"][t], 2)) for t in top]})
    out = {"verdicts": v, "frac": {"width": f1, "noise_prefix": f2, "noise_monotone": f2m, "acquisition_first": f3, "es_width": f4, "n_acq": len(acq)}, "per": per}
    json.dump(out, open(OUT, "w"), indent=1); print(json.dumps(v, indent=1)); print(json.dumps(out["frac"], indent=1))
    for k, x in per.items(): print(k, x)


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "run": run(sys.argv[2] if len(sys.argv) > 2 else None)
    else: {"predict": predict, "analyse": analyse}[c]()
