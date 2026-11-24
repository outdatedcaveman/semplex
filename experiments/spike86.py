"""Spike 86: the growth-rate race. Mechanism behind the Gibbs selection rule (C43): from a small initialisation each
isotypic block grows at its own early rate sigma_rho; the block that wins the race leads. Tests:
(H86.1) leader = argmax early growth rate; (H86.2) sigma_rho rises with log energy share and falls with kinetic cost;
(H86.3) the energy effect survives a block-dimension covariate (He et al. 2606.02993 confound);
(H86.4) the seed lottery sharpens at small initialisation; (H86.5) weight decay raises the exchange rate (favours the
cheaper block); (H86.6) log-linear vs linear-in-energy form. Learner: GRU + Adam(W), the learner alpha and lambda were
frozen on, with an initialisation scale and decoupled weight decay (SGD stayed on its plateau in the pilot).
See SPIKE_86_REPORT.md."""
import json, os, sys
import numpy as np
from experiments.spike58 import comp
import experiments.spike69 as S69
import experiments.spike71 as S71
import experiments.spike77 as S77

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "results", "spike86_raw")
OUT = os.path.join(ROOT, "results", "spike86.json")
PRED = os.path.join(ROOT, "results", "spike86_predictions.json")
STEPS, LEN, BATCH = 6000, 30, 64
OPT = "adam"
CK = list(range(0, 501, 10)) + list(range(750, STEPS + 1, 250))
ARMS = {"R": (0.1, 0.0), "D": (1.0, 0.0), "W": (1.0, 0.05)}          # (init scale, weight decay)
USED = set(S77.USED) | {"Z7_s1_015", "Z7_s3_023", "Z8_s3_037", "Z8_s3_015", "Z11_s3_045", "Z11_s2_012", "Z12_s1_037",
        "Z12_s1_035", "D7_pt", "A4_sub012", "S3_pt", "Z11_s1_019", "Z11_s1_038", "Z11_s2_015", "Z11_s2_016", "Z11_s3_023",
        "Z11_s3_035", "Z11_s3_039", "Z12_s1_014", "Z12_s1_034", "Z7_s1_014", "Z7_s3_025", "Z8_s1_026"}


def predict():
    P77 = json.load(open(S77.PRED)); A = P77["automata"]; rows = {}
    for name in S77.POOL:
        if name in USED: continue
        F = S77.feats(name); pg = S77.probs(F, S77.ALPHA, S77.LAMBDA); top = sorted(pg, key=pg.get, reverse=True)[:2]
        if 0.35 <= pg[top[0]] <= 0.6 and abs(F[top[0]][1] - F[top[1]][1]) > 0.05:
            rows[name] = {"gibbs": pg, "top2": top, "cheaper": min(top, key=lambda k: F[k][1])}
    rng = np.random.default_rng(86); B = [str(x) for x in rng.choice(sorted(rows), size=min(8, len(rows)), replace=False)]
    feats = {n: {k: list(v) for k, v in S77.feats(n).items()} for n in A + B}
    json.dump({"A": A, "B": B, "rows_B": {n: rows[n] for n in B}, "feats": feats, "n_near_tie": len(rows)}, open(PRED, "w"), indent=1)
    print("A", A); print("B", B, "of", len(rows), "near-tie candidates")
    for n in B: print(n, rows[n]["top2"], "cheaper", rows[n]["cheaper"], {k: round(rows[n]["gibbs"][k], 2) for k in rows[n]["top2"]})


def train(name, seed, scale, wd):
    import torch
    nn = torch.nn
    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    G, L, out = S77.spec(name); idx = {g: i for i, g in enumerate(G)}; e = tuple(range(len(G[0]))); k = len(out(e))
    class Net(nn.Module):
        def __init__(s): super().__init__(); s.e = nn.Embedding(len(L), 16); s.r = nn.GRU(16, 64, batch_first=True); s.h = nn.Linear(64, k)
        def hidden(s, X): return s.r(s.e(X))[0]
        def forward(s, X): return s.h(s.hidden(X))
    m = Net()
    with torch.no_grad():
        for p in m.parameters(): p.mul_(scale)
    opt = (torch.optim.AdamW(m.parameters(), lr=0.003, weight_decay=wd) if OPT == "adam" else
           torch.optim.SGD(m.parameters(), lr=0.1, momentum=0.9, weight_decay=wd)); sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, STEPS)
    def sample(B, T, r):
        X = r.integers(0, len(L), size=(B, T)); Y = np.zeros((B, T, k), np.float32); ST = np.zeros((B, T), int)
        for b in range(B):
            s_ = e
            for t in range(T): s_ = comp(s_, L[X[b, t]]); Y[b, t] = out(s_); ST[b, t] = idx[s_]
        return X, Y, ST
    irs = S69.real_irreps(G); labels = [S69.irrep_label(ir, kk) for kk, ir in enumerate(irs)]
    Xe, _, STe = sample(400, LEN, np.random.default_rng(seed + 2 * 10**6)); flatL = STe[:, 5:].ravel()
    def energies():
        with torch.no_grad(): H = m.hidden(torch.tensor(Xe)).numpy()
        flatH = H[:, 5:].reshape(-1, 64)
        Ce = np.stack([flatH[flatL == j].mean(0) if (flatL == j).any() else np.zeros(64) for j in range(len(G))])
        C = Ce - Ce.mean(0); Gm = C @ C.T
        return [float(np.trace(ir["P"] @ Gm @ ir["P"])) for ir in irs], C
    traj = []
    for step in range(STEPS + 1):
        if step in CK: traj.append([step] + energies()[0])
        if step == STEPS: break
        X, Y, _ = sample(BATCH, LEN, rng)
        loss = nn.functional.binary_cross_entropy_with_logits(m(torch.tensor(X)), torch.tensor(Y))
        opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(m.parameters(), 5.0); opt.step(); sch.step()
    with torch.no_grad():
        X, Y, _ = sample(500, 100, np.random.default_rng(seed + 10**6)); fit = float(((m(torch.tensor(X)) > 0).float() == torch.tensor(Y)).float().mean())
    _, C = energies(); Cn = C / np.maximum(np.linalg.norm(C, axis=1, keepdims=True), 1e-12); sh = S71.shares(Cn, irs)
    dims = [int(round(np.trace(ir["P"]))) for ir in irs]
    return {"fit": fit, "labels": labels, "dims": dims, "leader": labels[int(np.argmax(sh))], "shares": sh.tolist(), "traj": traj}


def growth(r):
    """pre-registered window: checkpoints from step 10 up to the first where total energy >= 10% of its final value
    (at least 3 checkpoints); sigma = least-squares slope of log energy per block over the window"""
    T = np.array(r["traj"]); steps, E = T[:, 0], np.maximum(T[:, 1:], 1e-30); tot = E.sum(1)
    ok = np.where(steps >= 10)[0]; hit = [i for i in ok if tot[i] >= 0.1 * tot[-1]]
    end = max(hit[0] if hit else ok[-1], ok[2]); w = [i for i in ok if i <= end]
    x = steps[w]; return [float(np.polyfit(x, np.log(E[w, j]), 1)[0]) for j in range(E.shape[1])]


def jobs():
    P = json.load(open(PRED)); J = [(n, "R", i) for n in P["A"] for i in range(5)]
    J += [(n, a, i) for a in ("R", "D", "W") for n in P["B"] for i in range(8)]
    return J


def run(part="0/1"):
    import torch
    torch.set_num_threads(1); os.makedirs(RAW, exist_ok=True)
    k, K = map(int, part.split("/"))
    for j, (name, arm, i) in enumerate(jobs()):
        if j % K != k: continue
        pth = os.path.join(RAW, f"{name}_{arm}_{i}.json")
        if os.path.exists(pth): continue
        sc, wd = ARMS[arm]; r = train(name, 8600 + 1000 * "RDW".index(arm) + 10 * (hash_name(name) % 97) + i, sc, wd)
        r.update({"automaton": name, "arm": arm, "i": i}); json.dump(r, open(pth, "w"))
        print(name, arm, i, round(r["fit"], 3), r["leader"], flush=True)


def hash_name(s): return sum(ord(c) * (7 ** i) for i, c in enumerate(s)) % 10007


def analyse():
    from scipy.optimize import minimize
    P = json.load(open(PRED)); F = P["feats"]
    runs = [json.load(open(os.path.join(RAW, f))) for f in sorted(os.listdir(RAW)) if f.endswith(".json")]
    ok = [r for r in runs if r["fit"] >= 0.99]
    R = [r for r in ok if r["arm"] == "R"]
    tri = lambda f, hi, lo: "NO VERDICT" if f is None else "HELD" if f >= hi else "BROKEN" if f < lo else "NEITHER"
    # H86.1
    f1 = float(np.mean([r["labels"][int(np.argmax(growth(r)))] == r["leader"] for r in R])) if len(R) >= 20 else None
    # H86.2 / H86.3: within-run z-scored sigma regressed on (log e, c[, log dim]); bootstrap over automata
    rows = []
    for r in R:
        s = np.array(growth(r)); s = (s - s.mean()) / (s.std() + 1e-12)
        for j, lab in enumerate(r["labels"]):
            e_, c_ = F[r["automaton"]][lab]; rows.append((r["automaton"], s[j], np.log(e_), c_, np.log(r["dims"][j])))
    auts = sorted({x[0] for x in rows}); rng = np.random.default_rng(860)
    def coefs(sel, cov):
        X = np.array([[1, x[2], x[3]] + ([x[4]] if cov else []) for x in sel]); y = np.array([x[1] for x in sel])
        return np.linalg.lstsq(X, y, rcond=None)[0][1:]
    def boot(cov):
        pt = coefs(rows, cov); bs = []
        for _ in range(2000):
            pick = rng.choice(auts, size=len(auts)); sel = [x for a in pick for x in rows if x[0] == a]; bs.append(coefs(sel, cov))
        return pt, np.percentile(np.array(bs), [2.5, 97.5], axis=0)
    v = {"H86.1": tri(f1, 0.75, 0.5)}
    if len(auts) >= 6:
        (b, ci), (b3, ci3) = boot(False), boot(True)
        good = ci[0][0] > 0 and ci[1][1] < 0; wrong = ci[1][0] < 0 or ci[0][1] > 0
        v["H86.2"] = "HELD" if good else "BROKEN" if wrong else "NEITHER"
        v["H86.3"] = "HELD" if ci3[0][0] > 0 else "BROKEN" if ci3[1][0] < 0 else "NEITHER"
    else: b = ci = b3 = ci3 = None; v["H86.2"] = v["H86.3"] = "NO VERDICT"
    # H86.4 lottery sharpness on B: mean modal-leader frequency, arm R minus arm D
    def modal(arm):
        fs = []
        for n in P["B"]:
            ls = [r["leader"] for r in ok if r["automaton"] == n and r["arm"] == arm]
            if len(ls) >= 4: fs.append(max(ls.count(x) for x in set(ls)) / len(ls))
        return (float(np.mean(fs)), len(fs)) if fs else (None, 0)
    (mR, nR), (mD, nD), (mW, nW) = modal("R"), modal("D"), modal("W")
    d4 = mR - mD if (mR is not None and mD is not None and min(nR, nD) >= 5) else None
    v["H86.4"] = "NO VERDICT" if d4 is None else "HELD" if d4 >= 0.10 else "BROKEN" if d4 < 0 else "NEITHER"
    # H86.5 weight decay favours the cheaper of the two top Gibbs blocks
    def cheap(arm):
        xs = [r["leader"] == P["rows_B"][r["automaton"]]["cheaper"] for r in ok if r["arm"] == arm and r["automaton"] in P["B"]]
        return (float(np.mean(xs)), len(xs)) if xs else (None, 0)
    (cW, kW), (cD, kD) = cheap("W"), cheap("D")
    d5 = cW - cD if (cW is not None and cD is not None and min(kW, kD) >= 20) else None
    v["H86.5"] = "NO VERDICT" if d5 is None else "HELD" if d5 >= 0.10 else "BROKEN" if d5 < 0 else "NEITHER"
    # H86.6 linear-in-energy vs log-linear form, each with two parameters fitted by maximum likelihood on arms R and D
    LR = [r for r in ok if r["arm"] in ("R", "D")]
    def nll(p, lin):
        t = 0.0
        for r in LR:
            Fn = F[r["automaton"]]; ks = list(Fn)
            s = np.array([(p[0] * Fn[q][0] if lin else p[0] * np.log(Fn[q][0])) - p[1] * Fn[q][1] for q in ks]); s -= s.max()
            t -= s[ks.index(r["leader"])] - np.log(np.exp(s).sum())
        return t
    if len(LR) >= 30:
        nl = minimize(lambda p: nll(p, True), [5.0, 3.0], method="Nelder-Mead").fun; ng = minimize(lambda p: nll(p, False), [2.5, 3.7], method="Nelder-Mead").fun
        v["H86.6"] = "HELD" if nl < ng else "BROKEN"
    else: nl = ng = None; v["H86.6"] = "NO VERDICT"
    out = {"verdicts": v, "race_argmax_frac": f1, "coef_logE_c": None if b is None else list(map(float, b)), "ci": None if ci is None else np.array(ci).tolist(),
           "coef_with_logdim": None if b3 is None else list(map(float, b3)), "ci_with_logdim": None if ci3 is None else np.array(ci3).tolist(),
           "modal_freq": {"R": mR, "D": mD, "W": mW}, "cheaper_frac": {"W": cW, "D": cD}, "nll_linear": nl, "nll_log": ng,
           "n_fitted": {a: sum(r["arm"] == a for r in ok) for a in "RDW"}, "n_runs": {a: sum(r["arm"] == a for r in runs) for a in "RDW"}}
    json.dump(out, open(OUT, "w"), indent=1); print(json.dumps(out, indent=1))


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "run": run(sys.argv[2] if len(sys.argv) > 2 else "0/1")
    else: {"predict": predict, "analyse": analyse}[c]()
