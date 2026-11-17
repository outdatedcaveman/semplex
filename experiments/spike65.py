"""Spike 65: continuous sufficiency law, S^2 (signed) vs RP^2 (unsigned axis). See SPIKE_65_REPORT.md."""
import json, math, os, sys
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "results", "spike65_raw")
OUT = os.path.join(ROOT, "results", "spike65.json")
READOUTS, SEEDS, STEPS, LEN, SIG = ["SIGN", "AXIS"], 5, 6000, 30, 0.3


def rot(w):
    th = np.linalg.norm(w)
    if th < 1e-12: return np.eye(3)
    k = w / th; K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + math.sin(th) * K + (1 - math.cos(th)) * K @ K


def target(u, readout):
    if readout == "SIGN": return u
    P = np.outer(u, u) - np.eye(3) / 3
    return np.array([P[0, 0], P[1, 1], P[0, 1], P[0, 2], P[1, 2]])


def sample(readout, B, T, rng, u0=None):
    W = rng.normal(0, SIG, size=(B, T, 3)); U = np.zeros((B, T, 3)); Y = np.zeros((B, T, 3 if readout == "SIGN" else 5))
    for b in range(B):
        u = np.array([0, 0, 1.0]) if u0 is None else u0[b]
        for t in range(T):
            u = rot(W[b, t]) @ u; u /= np.linalg.norm(u); U[b, t] = u; Y[b, t] = target(u, readout)
    return W.astype(np.float32), Y.astype(np.float32), U


def harmonics(U):
    x, y, z = U[:, 0], U[:, 1], U[:, 2]
    h1 = U
    h2 = np.c_[x * y, y * z, z * x, x * x - y * y, 3 * z * z - 1]
    h3 = np.c_[y * (3 * x * x - y * y), x * y * z, y * (5 * z * z - 1), z * (5 * z * z - 3), x * (5 * z * z - 1), z * (x * x - y * y), x * (x * x - 3 * y * y)]
    return {1: h1, 2: h2, 3: h3}


def fib(n):
    i = np.arange(n) + 0.5; phi = np.arccos(1 - 2 * i / n); th = np.pi * (1 + 5 ** 0.5) * i
    return np.c_[np.cos(th) * np.sin(phi), np.sin(th) * np.sin(phi), np.cos(phi)]


def run_one(readout, seed):
    import torch
    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    k_out = 3 if readout == "SIGN" else 5
    gru = torch.nn.GRU(3, 64, batch_first=True); head = torch.nn.Linear(64, k_out)
    opt = torch.optim.Adam(list(gru.parameters()) + list(head.parameters()), lr=0.003)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, STEPS)
    for step in range(STEPS):
        W, Y, _ = sample(readout, 64, LEN, rng)
        loss = ((head(gru(torch.tensor(W))[0]) - torch.tensor(Y)) ** 2).mean()
        opt.zero_grad(); loss.backward(); opt.step(); sch.step()
    r = {"readout": readout, "seed": seed}
    with torch.no_grad():
        W, Y, _ = sample(readout, 500, 100, np.random.default_rng(seed + 10**6))
        P = head(gru(torch.tensor(W))[0]).numpy()
        r["fit_r2"] = float(1 - ((P - Y) ** 2).sum() / ((Y - Y.mean((0, 1))) ** 2).sum())
        W, Y, U = sample(readout, 500, 60, np.random.default_rng(seed + 2 * 10**6))
        H = gru(torch.tensor(W))[0].numpy()
    Hs, Us = H[:, 5:].reshape(-1, 64), U[:, 5:].reshape(-1, 3)
    Hc = Hs - Hs.mean(0)
    hv = harmonics(Us); tot = (Hc ** 2).sum()
    for l, F in hv.items():
        F = F - F.mean(0); coef, *_ = np.linalg.lstsq(F, Hc, rcond=None)
        r[f"R2_l{l}"] = float(1 - ((Hc - F @ coef) ** 2).sum() / tot)
    grid = fib(200); bins = np.argmax(Us @ grid.T, 1)
    Hb = {b: Hs[bins == b].mean(0) for b in range(200) if (bins == b).sum() >= 5}
    anti = {b: int(np.argmax(-grid[b] @ grid.T)) for b in Hb}
    dA = [np.linalg.norm(Hb[b] - Hb[anti[b]]) for b in Hb if anti[b] in Hb]
    keys = list(Hb); prng = np.random.default_rng(seed); dR = []
    for _ in range(2000):
        a, b = prng.choice(keys, 2, replace=False); dR.append(np.linalg.norm(Hb[a] - Hb[b]))
    r["antipodal_ratio"] = float(np.mean(dA) / np.mean(dR))
    # antipodal swap intervention
    import torch as T_
    irng = np.random.default_rng(seed + 3 * 10**6); flatU = U[:, 5:40].reshape(-1, 3); flatH = H[:, 5:40].reshape(-1, 64)
    ok = 0; n = 0
    for _ in range(500):
        b = int(irng.integers(500)); t = int(irng.integers(10, 39)); u = U[b, t]
        d = flatU @ (-u); j = int(np.argmax(d))
        if np.arccos(np.clip(d[j], -1, 1)) > 0.1: continue
        suffix = W[b, t + 1:t + 21][None]
        with T_.no_grad():
            out = head(gru(T_.tensor(suffix), T_.tensor(flatH[j][None, None]))[0]).numpy()[0]
        truth = Y[b, t + 1:t + 21]
        r2 = 1 - ((out - truth) ** 2).sum() / ((truth - truth.mean(0)) ** 2).sum()
        ok += r2 >= 0.9; n += 1
    r["swap_matches_noswap"] = float(ok / max(n, 1)); r["n_swaps"] = n
    return r


def run():
    import torch
    torch.set_num_threads(2); os.makedirs(RAW, exist_ok=True)
    for ro in READOUTS:
        for i in range(SEEDS):
            p = os.path.join(RAW, f"{ro}_{i}.json")
            if os.path.exists(p): continue
            r = run_one(ro, 6500 + 10 * READOUTS.index(ro) + i)
            json.dump(r, open(p, "w"), indent=1)
            print(ro, i, {k: round(v, 3) if isinstance(v, float) else v for k, v in r.items()}, flush=True)


def analyse():
    runs = [json.load(open(os.path.join(RAW, f"{ro}_{i}.json"))) for ro in READOUTS for i in range(SEEDS)]
    F = {ro: [r for r in runs if r["readout"] == ro and r["fit_r2"] >= 0.95] for ro in READOUTS}
    ok = all(len(F[ro]) >= 3 for ro in READOUTS)
    med = lambda ro, k: float(np.median([r[k] for r in F[ro]])) if F[ro] else None
    v = {}
    if not ok:
        v = {"H65.1": "NO VERDICT", "H65.2": "NO VERDICT", "H65.3": "NO VERDICT"}
    else:
        a, s = med("AXIS", "antipodal_ratio"), med("SIGN", "antipodal_ratio")
        v["H65.1"] = "HELD" if a <= 0.25 and s >= 0.75 else "BROKEN" if a >= s else "NEITHER"
        sg = sum(r["R2_l1"] >= 0.6 and r["R2_l1"] > r["R2_l2"] for r in F["SIGN"]); ax = sum(r["R2_l2"] >= 0.4 and r["R2_l1"] <= 0.05 for r in F["AXIS"])
        rev = sum(r["R2_l2"] > r["R2_l1"] for r in F["SIGN"]) >= 3 or sum(r["R2_l1"] > r["R2_l2"] for r in F["AXIS"]) >= 3
        v["H65.2"] = "HELD" if sg >= 4 and ax >= 4 else "BROKEN" if rev else "NEITHER"
        ma, ms = med("AXIS", "swap_matches_noswap"), med("SIGN", "swap_matches_noswap")
        v["H65.3"] = "HELD" if ma >= 0.9 and ms <= 0.1 else "BROKEN" if ma <= ms else "NEITHER"
    out = {"verdicts": v, "fitted": {ro: len(F[ro]) for ro in READOUTS},
           "median": {ro: {k: med(ro, k) for k in ("antipodal_ratio", "R2_l1", "R2_l2", "R2_l3", "swap_matches_noswap", "fit_r2")} for ro in READOUTS},
           "runs": runs}
    json.dump(out, open(OUT, "w"), indent=1); print(json.dumps(v, indent=1))


if __name__ == "__main__":
    {"run": run, "analyse": analyse}[sys.argv[1]]()
