"""Spike 83: the invariance principle — closure all the way down. A learned concept's dominant geometry spans a
subspace of observables (functions on the minimal states) that is (approximately) INVARIANT under every input's
action (T_a f)(q) = f(delta_a q): for groups an isotypic component, for monoids (resets, merges) a submodule.
Tests on group automata (Spike 77) and non-group automata (Spike 81), against random subspaces and against the
top predictive-kernel eigenvectors used in Spike 81. See SPIKE_83_REPORT.md."""
import json, os, sys
import numpy as np
from experiments.spike58 import comp, closure
import experiments.spike77 as S77
import experiments.spike81 as S81

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "results", "spike83_raw")
OUT = os.path.join(ROOT, "results", "spike83.json")
PRED = os.path.join(ROOT, "results", "spike83_predictions.json")
VAR = 0.7; NRAND = 300


def group_as_automaton(name):
    """state table on group elements for a Spike 77 automaton: D[a][q], O[q] (first output bit), start index"""
    G, L, out = S77.spec(name); idx = {g: i for i, g in enumerate(G)}
    D = np.array([[idx[comp(g, a)] for g in G] for a in L]); O = np.array([out(g)[0] for g in G])
    return D, O, idx[tuple(range(len(G[0])))]


def defect(U, D, pi):
    """mean over letters of ||(I-P_U) T_a P_U||^2 / ||T_a P_U||^2 in the pi-weighted inner product; U: m x r
    (columns pi-orthonormal, include the constant function)."""
    W = np.sqrt(pi)[:, None]; Uw = W * U; Q, _ = np.linalg.qr(Uw); P = Q @ Q.T; out = []
    for a in range(D.shape[0]):
        T = np.eye(len(pi))[D[a]]                                   # (T f)(q) = f(delta_a q)
        Tw = W * T / W.T                                             # conjugate to the sqrt(pi) frame
        A = Tw @ Q; num = np.linalg.norm(A - P @ A) ** 2; den = np.linalg.norm(A) ** 2
        out.append(num / max(den, 1e-12))
    return float(np.mean(out))


def basis_with_const(F, pi):
    """columns: constant + given functions (m x r), pi-orthonormalised"""
    M = np.column_stack([np.ones(len(pi)), F]); W = np.sqrt(pi)[:, None]
    Q, _ = np.linalg.qr(W * M); return Q / W


def run_one(kind, ident_, D, O, s0, seed):
    """train a GRU (Spike 81 trainer) and return centroid functions per state, visit distribution, fit"""
    A = {"D": D[:-1].tolist() if kind == "group" else D.tolist(), "O": O.tolist(), "s0": int(s0), "modes": [], "pi": None}
    import torch
    from experiments.spike60 import build
    nn = torch.nn
    Dl = D if kind == "group" else np.vstack([D, np.arange(D.shape[1])[None]]); m = Dl.shape[1]; L = Dl.shape[0]
    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    def sample(B, T, r):
        X = r.integers(0, L, size=(B, T)); Y = np.zeros((B, T, 1), np.float32); ST = np.zeros((B, T), int)
        for b in range(B):
            q = s0
            for t in range(T): q = Dl[X[b, t]][q]; Y[b, t, 0] = O[q]; ST[b, t] = q
        return X, Y, ST
    mdl = build("gru", L, 1); opt = torch.optim.Adam(mdl.parameters(), lr=0.003); sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, 6000)
    for _ in range(6000):
        X, Y, _ = sample(64, 30, rng)
        loss = nn.functional.binary_cross_entropy_with_logits(mdl(torch.tensor(X)), torch.tensor(Y)); opt.zero_grad(); loss.backward(); opt.step(); sch.step()
    with torch.no_grad():
        X, Y, _ = sample(500, 100, np.random.default_rng(seed + 10**6)); fit = float(((mdl(torch.tensor(X)) > 0).float() == torch.tensor(Y)).float().mean())
        X, Y, ST = sample(400, 30, np.random.default_rng(seed + 2 * 10**6)); H = mdl.hidden(torch.tensor(X)).numpy()
    flatH, flatL = H[:, 5:].reshape(-1, 64), ST[:, 5:].ravel()
    pi = np.bincount(flatL, minlength=m).astype(float); pi = pi / pi.sum()
    seen = pi > 0
    Ce = np.stack([flatH[flatL == q].mean(0) if seen[q] else np.zeros(64) for q in range(m)])
    return Dl, pi, Ce, fit


def analyse_run(Dl, pi, Ce, kernel_modes, rng):
    keep = pi > 0; Dk = Dl                                          # all states visited in practice; guard below
    mu = (pi[:, None] * Ce).sum(0); Cc = Ce - mu
    G = (np.sqrt(pi)[:, None] * Cc) @ (np.sqrt(pi)[:, None] * Cc).T; ev, EV = np.linalg.eigh(G); ev, EV = ev[::-1], EV[:, ::-1]
    m = len(pi); r = int(np.searchsorted(np.cumsum(ev) / ev.sum(), VAR) + 1); r = min(r, m - 2)
    if r < 1: return None
    learned = basis_with_const(EV[:, :r] / np.sqrt(np.maximum(pi, 1e-12))[:, None], pi)
    d_learned = defect(learned, Dk, pi)
    d_rand = [defect(basis_with_const(rng.normal(size=(m, r)), pi), Dk, pi) for _ in range(NRAND)]
    out = {"r": r, "m": m, "d_learned": d_learned, "pct_vs_random": float(np.mean(np.array(d_rand) <= d_learned)), "d_random_median": float(np.median(d_rand))}
    if kernel_modes is not None and len(kernel_modes) >= r:
        Kv = np.column_stack([np.array(md["v"]) for md in kernel_modes[:r]]); out["d_kernel"] = defect(basis_with_const(Kv, pi), Dk, pi)
    return out


def predict():
    P77 = json.load(open(S77.PRED)); P81 = json.load(open(S81.PRED))
    groups = P77["automata"]
    nongroups = [r for r in P81["random"] + P81["discriminating"] if r["kind"] != "perm"]
    P = {"groups": groups, "nongroups": [{"id": r["id"], "kind": r["kind"]} for r in nongroups], "VAR": VAR, "NRAND": NRAND,
         "note": "No numeric predictions needed beyond the registered thresholds; automata fixed here before any run."}
    json.dump(P, open(PRED, "w"), indent=1); print(len(groups), "group automata;", len(nongroups), "non-group automata")


def run(which=None):
    import torch
    torch.set_num_threads(2); os.makedirs(RAW, exist_ok=True); P = json.load(open(PRED)); P81 = json.load(open(S81.PRED))
    by81 = {r["id"]: r for r in P81["random"] + P81["discriminating"]}
    jobs = [("group", n) for n in P["groups"]] + [("nongroup", x["id"]) for x in P["nongroups"]]
    if which: jobs = [j for j in jobs if j[0] in which.split(",")]
    for kind, key in jobs:
        for i in range(2):
            pth = os.path.join(RAW, f"{kind}_{key}_{i}.json")
            if os.path.exists(pth): continue
            seed = 8300 + (0 if kind == "group" else 500) + 10 * ([j[1] for j in jobs].index(key)) + i
            if kind == "group":
                D, O, s0 = group_as_automaton(key); modes = None
            else:
                A = by81[key]; D, O, s0 = np.array(A["D"]), np.array(A["O"]), A["s0"]; modes = A["modes"]
            Dl, pi, Ce, fit = run_one(kind, None, D, O, s0, seed)
            res = analyse_run(Dl, pi, Ce, modes, np.random.default_rng(seed))
            r = {"kind": kind, "key": key, "seed": seed, "fit": fit, "res": res}
            json.dump(r, open(pth, "w")); print(kind, key, i, round(fit, 3), res and {k: (round(v, 3) if isinstance(v, float) else v) for k, v in res.items()}, flush=True)


def analyse():
    runs = [json.load(open(os.path.join(RAW, f))) for f in sorted(os.listdir(RAW))]
    ok = [r for r in runs if r["fit"] >= 0.99 and r["res"]]
    g = [r for r in ok if r["kind"] == "group"]; n = [r for r in ok if r["kind"] == "nongroup"]
    frac = lambda xs: float(np.mean(xs)) if xs else None
    f1g = frac([r["res"]["pct_vs_random"] <= 0.2 for r in g]); f1n = frac([r["res"]["pct_vs_random"] <= 0.2 for r in n])
    f2 = frac([r["res"]["d_learned"] < r["res"]["d_kernel"] for r in n if "d_kernel" in r["res"]])
    tri = lambda f, hi, lo: "NO VERDICT" if f is None else "HELD" if f >= hi else "BROKEN" if f < lo else "NEITHER"
    v = {"H83.1": tri(f1g, 0.8, 0.5) if len(g) >= 5 else "NO VERDICT", "H83.2": tri(f1n, 0.8, 0.5) if len(n) >= 5 else "NO VERDICT",
         "H83.3": tri(f2, 0.7, 0.5) if f2 is not None and len(n) >= 5 else "NO VERDICT"}
    summ = lambda rs, k: (float(np.median([r["res"][k] for r in rs if k in r["res"]])) if rs else None)
    out = {"verdicts": v, "frac": {"groups_invariant": f1g, "nongroups_invariant": f1n, "learned_beats_kernel": f2},
           "median": {"group_defect": summ(g, "d_learned"), "group_random": summ(g, "d_random_median"),
                      "nongroup_defect": summ(n, "d_learned"), "nongroup_random": summ(n, "d_random_median"), "nongroup_kernel": summ(n, "d_kernel")},
           "n": {"group": len(g), "nongroup": len(n), "all": len(runs)}}
    json.dump(out, open(OUT, "w"), indent=1); print(json.dumps(out, indent=1))


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "run": run(sys.argv[2] if len(sys.argv) > 2 else None)
    else: {"predict": predict, "analyse": analyse}[c]()
