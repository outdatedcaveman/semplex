"""Spike 70: Spike 65 redesigned with a passable fit guard: tracked direction (S^2) vs tracked axis (RP^2),
testing C36 (linearising double cover) formally. Lower rotation noise (sigma 0.15), guard at the training
length. Helpers reused from the frozen Spike 65. See SPIKE_70_REPORT.md."""
import json, os, sys
import numpy as np
from experiments.spike65 import rot, target, harmonics, fib

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "results", "spike70_raw")
OUT = os.path.join(ROOT, "results", "spike70.json")
READOUTS, SEEDS, STEPS, LEN, SIG, MLEN = ["SIGN", "AXIS"], 5, 6000, 30, 0.15, 40


def sample(readout, B, T, rng):
    W = rng.normal(0, SIG, size=(B, T, 3)); U = np.zeros((B, T, 3)); Y = np.zeros((B, T, 3 if readout == "SIGN" else 5))
    for b in range(B):
        u = np.array([0, 0, 1.0])
        for t in range(T):
            u = rot(W[b, t]) @ u; u /= np.linalg.norm(u); U[b, t] = u; Y[b, t] = target(u, readout)
    return W.astype(np.float32), Y.astype(np.float32), U


def r2(P, Y): return float(1 - ((P - Y) ** 2).sum() / ((Y - Y.mean((0, 1))) ** 2).sum())


def run_one(readout, seed, steps=STEPS):
    import torch
    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    k_out = 3 if readout == "SIGN" else 5
    gru = torch.nn.GRU(3, 64, batch_first=True); head = torch.nn.Linear(64, k_out)
    opt = torch.optim.Adam(list(gru.parameters()) + list(head.parameters()), lr=0.003)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps)
    for step in range(steps):
        W, Y, _ = sample(readout, 64, LEN, rng)
        loss = ((head(gru(torch.tensor(W))[0]) - torch.tensor(Y)) ** 2).mean()
        opt.zero_grad(); loss.backward(); opt.step(); sch.step()
    r = {"readout": readout, "seed": seed}
    with torch.no_grad():
        W, Y, _ = sample(readout, 500, LEN, np.random.default_rng(seed + 10**6))
        r["fit_r2"] = r2(head(gru(torch.tensor(W))[0]).numpy(), Y)
        W, Y, U = sample(readout, 500, MLEN, np.random.default_rng(seed + 2 * 10**6))
        Hfull = gru(torch.tensor(W))[0]; H = Hfull.numpy()
        r["fit_r2_len40"] = r2(head(Hfull).numpy(), Y)
    Hs, Us = H[:, 5:].reshape(-1, 64), U[:, 5:].reshape(-1, 3)
    Hc = Hs - Hs.mean(0); hv = harmonics(Us); tot = (Hc ** 2).sum()
    for l, F in hv.items():
        F = F - F.mean(0); coef, *_ = np.linalg.lstsq(F, Hc, rcond=None)
        r[f"R2_l{l}"] = float(1 - ((Hc - F @ coef) ** 2).sum() / tot)
    # sign decodability: linear probe for the sign of u_z among states with |u_z| >= 0.3
    from sklearn.linear_model import LogisticRegression
    m = np.abs(Us[:, 2]) >= 0.3; Xs, ys = Hs[m], (Us[m, 2] > 0).astype(int); hlf = len(ys) // 2
    r["sign_probe"] = float(LogisticRegression(max_iter=3000).fit(Xs[:hlf], ys[:hlf]).score(Xs[hlf:], ys[hlf:]))
    grid = fib(200); bins = np.argmax(Us @ grid.T, 1)
    Hb = {b: Hs[bins == b].mean(0) for b in range(200) if (bins == b).sum() >= 5}
    anti = {b: int(np.argmax(-grid[b] @ grid.T)) for b in Hb}
    dA = [np.linalg.norm(Hb[b] - Hb[anti[b]]) for b in Hb if anti[b] in Hb]
    keys = list(Hb); prng = np.random.default_rng(seed); dR = []
    for _ in range(2000):
        a, b = prng.choice(keys, 2, replace=False); dR.append(np.linalg.norm(Hb[a] - Hb[b]))
    r["antipodal_ratio"] = float(np.mean(dA) / np.mean(dR)) if dA else float("nan"); r["n_antipodal_pairs"] = len(dA)
    import torch as T_
    irng = np.random.default_rng(seed + 3 * 10**6); flatU = U[:, 5:].reshape(-1, 3); flatH = H[:, 5:].reshape(-1, 64)
    ok = n = 0
    for _ in range(1000):
        b = int(irng.integers(500)); t = int(irng.integers(5, MLEN - 21)); u = U[b, t]
        d = flatU @ (-u); j = int(np.argmax(d))
        if np.arccos(np.clip(d[j], -1, 1)) > 0.1: continue
        with T_.no_grad():
            out = head(gru(T_.tensor(W[b, t + 1:t + 21][None]), T_.tensor(flatH[j][None, None]))[0]).numpy()[0]
        truth = Y[b, t + 1:t + 21]
        ok += (1 - ((out - truth) ** 2).sum() / ((truth - truth.mean(0)) ** 2).sum()) >= 0.9; n += 1
    r["swap_matches_noswap"] = float(ok / max(n, 1)); r["n_swaps"] = n
    return r


def run():
    import torch
    torch.set_num_threads(2); os.makedirs(RAW, exist_ok=True)
    for ro in READOUTS:
        for i in range(SEEDS):
            p = os.path.join(RAW, f"{ro}_{i}.json")
            if os.path.exists(p): continue
            r = run_one(ro, 7000 + 10 * READOUTS.index(ro) + i)
            json.dump(r, open(p, "w"), indent=1)
            print(ro, i, {k: round(v, 3) if isinstance(v, float) else v for k, v in r.items()}, flush=True)


def pilot():
    """guard calibration only (seed outside the registered range); prints fit only."""
    import torch
    torch.set_num_threads(2)
    for ro in READOUTS:
        r = run_one(ro, 99, steps=2000); print(ro, "pilot fit_r2", round(r["fit_r2"], 3), "len40", round(r["fit_r2_len40"], 3), flush=True)


def analyse():
    runs = [json.load(open(os.path.join(RAW, f"{ro}_{i}.json"))) for ro in READOUTS for i in range(SEEDS)]
    F = {ro: [r for r in runs if r["readout"] == ro and r["fit_r2"] >= 0.9] for ro in READOUTS}
    med = lambda ro, k: float(np.median([r[k] for r in F[ro]])) if F[ro] else None
    v = {}
    if len(F["AXIS"]) >= 3:
        ax = F["AXIS"]
        c1 = np.mean([r["R2_l1"] >= 0.2 and r["R2_l1"] > r["R2_l2"] for r in ax]); b1 = np.mean([r["R2_l2"] > r["R2_l1"] for r in ax])
        v["H70.1"] = "HELD" if c1 >= 0.8 else "BROKEN" if b1 >= 0.5 else "NEITHER"
        c2 = np.mean([r["sign_probe"] >= 0.9 for r in ax]); b2 = np.mean([r["sign_probe"] <= 0.6 for r in ax])
        v["H70.2"] = "HELD" if c2 >= 0.8 else "BROKEN" if b2 >= 0.5 else "NEITHER"
    else:
        v["H70.1"] = v["H70.2"] = "NO VERDICT"
    if len(F["AXIS"]) >= 3 and len(F["SIGN"]) >= 3:
        ma, ms = med("AXIS", "swap_matches_noswap"), med("SIGN", "swap_matches_noswap")
        v["H70.3"] = "HELD" if ma >= 0.9 and ms <= 0.1 else "BROKEN" if ma <= ms else "NEITHER"
        sg = np.mean([r["R2_l1"] >= 0.3 and r["R2_l1"] > r["R2_l2"] for r in F["SIGN"]])
        v["H70.4"] = "HELD" if sg >= 0.8 else "BROKEN" if sg < 0.5 else "NEITHER"
    else:
        v["H70.3"] = v["H70.4"] = "NO VERDICT"
    out = {"verdicts": v, "fitted": {ro: len(F[ro]) for ro in READOUTS},
           "median": {ro: {k: med(ro, k) for k in ("antipodal_ratio", "R2_l1", "R2_l2", "R2_l3", "sign_probe", "swap_matches_noswap", "fit_r2", "fit_r2_len40")} for ro in READOUTS},
           "runs": runs}
    json.dump(out, open(OUT, "w"), indent=1); print(json.dumps(v, indent=1)); print(json.dumps(out["median"], indent=1))


if __name__ == "__main__":
    {"run": run, "analyse": analyse, "pilot": pilot}[sys.argv[1]]()
