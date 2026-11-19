"""Spike 87: the generator principle (C45'), prospectively. Spike 84 found post hoc that on irreversible automata the
top learned direction is the output vector o, the generator of the cyclic observable module O = A.o. Here: 16 FRESH
automata (not used in Spike 84), the same GRU recipe, plus a control learner whose readout is a trained nonlinear MLP
(so a linear readout cannot be what makes o dominant). Rivals for the top learned direction: o; the top eigenvector of
the predictive kernel (t >= 1, Spike 81); the Gibbs-selected kernel mode (Spike 81 rule). See SPIKE_87_REPORT.md."""
import json, os, sys
import numpy as np
import experiments.spike81 as S81
import experiments.spike84 as S84

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "results", "spike87_raw")
OUT = os.path.join(ROOT, "results", "spike87.json")
PRED = os.path.join(ROOT, "results", "spike87_predictions.json")
LEARNERS = ["lin", "mlp"]


def frame(pi):
    W = np.sqrt(pi); one = W / np.linalg.norm(W)
    def to_w(v): x = W * np.asarray(v, float); x = x - one * (one @ x); return x / max(np.linalg.norm(x), 1e-12)
    return W, one, to_w


def predict():
    used = {A["id"] for A in json.load(open(S84.PRED))["automata"]}
    pool = S81.build_pool(); rows = []
    for i, A in enumerate(pool):
        if i in used: continue
        D, o = np.array(A["D"]), np.array(A["O"]); Dl = np.vstack([D, np.arange(D.shape[1])[None]]); k = Dl.shape[0]
        lp = np.ones(k) / k; pi = S81.visit_dist(Dl, A["s0"], lp)
        if (pi <= 1e-6).any(): continue
        hs = S84.head_structure(Dl, o, pi)
        if not (hs["dimR"] >= 1 and hs["dimH"] >= 1): continue
        _, _, to_w = frame(pi); og = to_w(o)
        ms = S81.modes(Dl, o, pi, lp); W = np.sqrt(pi)
        vecs = [to_w(m["v"]) for m in ms]; pr = S81.predict_rule(ms)
        k1, g = vecs[0], vecs[int(np.argmax(pr))]
        rows.append({"id": i, "kind": A["kind"], "D": A["D"], "out": A["O"], "s0": A["s0"], "pi": pi.tolist(),
                     "dimO": hs["dimO"], "dimH": hs["dimH"], "dimR": hs["dimR"], "o_w": og.tolist(), "k1_w": k1.tolist(), "gibbs_w": g.tolist(),
                     "o_k1": float((og @ k1) ** 2), "o_gibbs": float((og @ g) ** 2), "o_in_head": float(np.sum((np.array(hs["H"]).T @ og) ** 2)), "head": hs["H"]})
    rng = np.random.default_rng(87); pick = [rows[j] for j in rng.choice(len(rows), size=min(16, len(rows)), replace=False)]
    json.dump({"automata": pick, "n_available": len(rows), "excluded_spike84": sorted(used)}, open(PRED, "w"))
    print("available", len(rows), "picked", len(pick))
    for r in pick: print(r["id"], r["kind"], "m", len(r["pi"]), "dimH/dimO", r["dimH"], r["dimO"], "(o.k1)^2 %.2f (o.g)^2 %.2f o_in_head %.2f" % (r["o_k1"], r["o_gibbs"], r["o_in_head"]))


def train(A, seed, learner):
    import torch
    from experiments.spike60 import build
    nn = torch.nn
    D, O = np.array(A["D"]), np.array(A["out"]); Dl = np.vstack([D, np.arange(D.shape[1])[None]]); m = Dl.shape[1]; L = Dl.shape[0]
    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    def sample(B, T, r):
        X = r.integers(0, L, size=(B, T)); Y = np.zeros((B, T, 1), np.float32); ST = np.zeros((B, T), int)
        for b in range(B):
            q = A["s0"]
            for t in range(T): q = Dl[X[b, t]][q]; Y[b, t, 0] = O[q]; ST[b, t] = q
        return X, Y, ST
    mdl = build("gru", L, 1)
    if learner == "mlp": mdl.h = nn.Sequential(nn.Linear(64, 64), nn.Tanh(), nn.Linear(64, 64), nn.Tanh(), nn.Linear(64, 1))
    opt = torch.optim.Adam(mdl.parameters(), lr=0.003); sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, 6000)
    for _ in range(6000):
        X, Y, _ = sample(64, 30, rng)
        loss = nn.functional.binary_cross_entropy_with_logits(mdl(torch.tensor(X)), torch.tensor(Y)); opt.zero_grad(); loss.backward(); opt.step(); sch.step()
    with torch.no_grad():
        X, Y, _ = sample(500, 100, np.random.default_rng(seed + 10**6)); fit = float(((mdl(torch.tensor(X)) > 0).float() == torch.tensor(Y)).float().mean())
        X, Y, ST = sample(400, 30, np.random.default_rng(seed + 2 * 10**6)); H = mdl.hidden(torch.tensor(X)).numpy()
    flatH, flatL = H[:, 5:].reshape(-1, 64), ST[:, 5:].ravel()
    Ce = np.stack([flatH[flatL == q].mean(0) if (flatL == q).any() else np.full(64, np.nan) for q in range(m)])
    return fit, Ce


def measure(A, Ce):
    if np.isnan(Ce).any(): return None
    pi = np.array(A["pi"]); W, one, _ = frame(pi)
    mu = (pi[:, None] * Ce).sum(0); X = W[:, None] * (Ce - mu); X = X - np.outer(one, one @ X)
    U, s, _ = np.linalg.svd(X, full_matrices=False); u1 = U[:, 0]
    a = lambda v: float((u1 @ np.array(v)) ** 2)
    Hv = np.array(A["head"])
    return {"o": a(A["o_w"]), "k1": a(A["k1_w"]), "gibbs": a(A["gibbs_w"]), "head": float(np.sum((Hv.T @ u1) ** 2)), "top_var_share": float(s[0] ** 2 / np.sum(s ** 2))}


def run(part="0/1"):
    import torch
    torch.set_num_threads(1); os.makedirs(RAW, exist_ok=True); P = json.load(open(PRED)); k, K = map(int, part.split("/"))
    J = [(A, l, i) for l in LEARNERS for A in P["automata"] for i in range(3)]
    for j, (A, l, i) in enumerate(J):
        if j % K != k: continue
        pth = os.path.join(RAW, f"{A['id']}_{l}_{i}.json")
        if os.path.exists(pth): continue
        fit, Ce = train(A, 8700 + 10 * A["id"] + i + (5000 if l == "mlp" else 0), l)
        np.save(pth.replace(".json", "_centroids.npy"), Ce)
        r = {"id": A["id"], "learner": l, "fit": fit, "res": measure(A, Ce)}; json.dump(r, open(pth, "w"))
        print(A["id"], l, i, round(fit, 3), r["res"] and {x: round(y, 3) for x, y in r["res"].items()}, flush=True)


def analyse():
    P = json.load(open(PRED)); info = {A["id"]: A for A in P["automata"]}
    runs = [json.load(open(os.path.join(RAW, f))) for f in sorted(os.listdir(RAW)) if f.endswith(".json")]
    ok = [r for r in runs if r["fit"] >= 0.99 and r["res"]]
    def frac(rs, f): return (float(np.mean([f(r) for r in rs])), len(rs), len({r["id"] for r in rs})) if rs else (None, 0, 0)
    tri = lambda f, n_aut, need, hi, lo: "NO VERDICT" if f is None or n_aut < need else "HELD" if f >= hi else "BROKEN" if f < lo else "NEITHER"
    lin = [r for r in ok if r["learner"] == "lin"]; mlp = [r for r in ok if r["learner"] == "mlp"]
    f1 = frac(lin, lambda r: r["res"]["o"] >= 0.8)
    d2 = [r for r in lin if info[r["id"]]["o_k1"] < 0.9]; f2 = frac(d2, lambda r: r["res"]["o"] > r["res"]["k1"])
    f3 = frac(mlp, lambda r: r["res"]["o"] >= 0.8)
    d4 = [r for r in lin if info[r["id"]]["o_gibbs"] < 0.9]; f4 = frac(d4, lambda r: r["res"]["o"] > r["res"]["gibbs"])
    d5 = [r for r in lin if info[r["id"]]["o_in_head"] < 0.5]; f5 = frac(d5, lambda r: r["res"]["o"] > r["res"]["head"])
    v = {"H87.1": tri(f1[0], f1[2], 8, 0.75, 0.5), "H87.2": tri(f2[0], f2[2], 4, 0.7, 0.5),
         "H87.3": tri(f3[0], f3[2], 8, 0.75, 0.5), "H87.4": tri(f4[0], f4[2], 4, 0.7, 0.5), "H87.5": tri(f5[0], f5[2], 3, 0.7, 0.5)}
    med = lambda rs, k: float(np.median([r["res"][k] for r in rs])) if rs else None
    out = {"verdicts": v, "frac": {"H87.1": f1, "H87.2": f2, "H87.3": f3, "H87.4": f4, "H87.5": f5},
           "median_alignment": {l: {k: med(rs, k) for k in ("o", "k1", "gibbs", "head", "top_var_share")} for l, rs in (("lin", lin), ("mlp", mlp))},
           "n_runs": len(runs), "n_fitted": {"lin": len(lin), "mlp": len(mlp)}}
    json.dump(out, open(OUT, "w"), indent=1); print(json.dumps(out, indent=1))


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "run": run(sys.argv[2] if len(sys.argv) > 2 else "0/1")
    else: {"predict": predict, "analyse": analyse}[c]()
