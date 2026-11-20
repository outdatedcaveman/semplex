"""Spike 23 (pre-registered in SPIKE_23_REPORT.md): distance-matched choice test of symmetry aiming.

  python -m experiments.spike23 run
  python -m experiments.spike23 analyse
"""

from __future__ import annotations

import json
import math
import pathlib
import sys

import numpy as np

from cerp import atlas, mechvol, train
from experiments import spike14 as S14, spike18 as S18, spike19 as S19
from experiments.spike09 import tgt
from experiments.spike21 import mutual_info
from experiments.spike22 import fwd

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "experiments" / "results" / "spike23_raw"
OUT = ROOT / "experiments" / "results" / "spike23.json"
FULL = 0xFFFF
POW = (1 << np.arange(16)).astype(np.int64)


def run():
    tb, ex, els, iso = S14.setup()
    fs = np.array([e for _ in range(40) for e in els])
    p = train.init(len(fs), 8, np.random.default_rng(23_000), dtype=np.float32)
    T = tgt(fs).astype(np.float32)
    XS = train.XS.astype(np.float32)
    m = {k: np.zeros_like(v) for k, v in p.items()}; v = {k: np.zeros_like(x) for k, x in p.items()}
    ev_b, ev_j, ev_old, ev_x, ev_d, ev_t = [], [], [], [], [], []
    pre, h, d, z = fwd(p, None)
    prev = (np.transpose(pre >= 0, (0, 2, 1)).astype(np.int64) * POW).sum(-1)          # (B, H) raw bits
    for t in range(1, 3001):
        dz = (1 / (1 + np.exp(-z)) - T) / 16
        g = {"W2": np.einsum("bx,bxh->bh", dz, h), "b2": dz.sum(1)}
        dh = dz[:, :, None] * p["W2"][:, None, :] * d
        g["W1"] = np.einsum("bxh,xn->bhn", dh, XS); g["b1"] = dh.sum(1)
        dist = np.abs(pre) / (np.linalg.norm(p["W1"], axis=2)[:, None, :] + 1e-12)         # (B, 16, H), before the step
        for k in p:
            m[k] = 0.9 * m[k] + 0.1 * g[k]; v[k] = 0.999 * v[k] + 0.001 * g[k] ** 2
            p[k] = p[k] - 0.03 * (m[k] / (1 - 0.9 ** t)) / (np.sqrt(v[k] / (1 - 0.999 ** t)) + 1e-8) - 0.03 * 0.03 * p[k]
        pre, h, d, z = fwd(p, None)
        cur = (np.transpose(pre >= 0, (0, 2, 1)).astype(np.int64) * POW).sum(-1)
        x = prev ^ cur
        single = (x != 0) & ((x & (x - 1)) == 0)
        bb, jj = np.nonzero(single)
        if len(bb):
            ev_b.append(bb); ev_j.append(jj); ev_old.append(prev[bb, jj]); ev_x.append(np.log2(x[bb, jj]).astype(np.int64))
            ev_d.append(dist[bb, :, jj].astype(np.float32)); ev_t.append(np.full(len(bb), t))
        prev = cur
    gfun = train.bits(z >= 0)
    RAW.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(RAW / "events.npz", b=np.concatenate(ev_b), j=np.concatenate(ev_j), old=np.concatenate(ev_old),
                        x=np.concatenate(ev_x), d=np.concatenate(ev_d), t=np.concatenate(ev_t), fs=fs, fit=float((gfun == fs).mean()))
    print("fit", float((gfun == fs).mean()), "events", sum(len(a) for a in ev_b), flush=True)


def clogit(F, M, y, iters=60):
    """Conditional logit, exact Newton. F (N, 16, k), M (N, 16) bool, y (N,) chosen index."""
    N, _, k = F.shape
    th = np.zeros(k)
    Fy = F[np.arange(N), y]

    def terms(th):
        s = np.where(M, F @ th, -np.inf); mx = s.max(1, keepdims=True); w = np.exp(s - mx); Z = w.sum(1, keepdims=True); pr = w / Z
        nll = float((mx[:, 0] + np.log(Z[:, 0])).sum() - (Fy @ th).sum())
        mu = np.einsum("nc,nck->nk", pr, F)
        g = mu.sum(0) - Fy.sum(0)
        H = np.einsum("nc,nck,ncl->kl", pr, F, F) - mu.T @ mu
        return nll, g, H
    f, g, H = terms(th)
    for _ in range(iters):
        step = np.linalg.solve(H + 1e-9 * np.eye(k), g); a = 1.0
        while True:
            nf, ng, nH = terms(th - a * step)
            if nf <= f + 1e-9 or a < 1e-6:
                break
            a /= 2
        done = abs(f - nf) < 1e-10 * (1 + abs(f))
        th, f, g, H = th - a * step, nf, ng, nH
        if done:
            break
    return th, f


def analyse(boots=200):
    tb, ex, els, iso = S14.setup()
    T4 = atlas.transforms(4)
    Gf = {e: S19.gfull(e, T4) for e in els}
    omega, ns = mechvol.solid_angles(40_000_000, np.random.default_rng(1100))
    D = np.load(RAW / "events.npz")
    b, old, x, dist, fs = D["b"], D["old"], D["x"], D["d"].astype(float), D["fs"]
    e_of = fs[b]
    new_all = old[:, None] ^ POW[None, :]                                                       # (N, 16) candidate raw functions
    can = np.minimum(new_all, FULL ^ new_all)
    oldc = np.minimum(old, FULL ^ old)
    valid = np.vectorize(lambda u: u != 0 and u in omega)(can) & (oldc != 0)[:, None]
    keep = valid[np.arange(len(x)), x] & valid.sum(1).astype(bool)
    b, x, dist, can, valid, e_of = b[keep], x[keep], dist[keep], can[keep], valid[keep], e_of[keep]
    cache = {}

    def feat(e, u):
        key = (int(e), int(u))
        if key not in cache:
            cache[key] = (math.log(omega[u]), math.log(len(S18.unit_stabilizer(int(u), Gf[int(e)])) + 1), mutual_info(int(u), int(e)))
        return cache[key]
    N = len(x)
    F = np.zeros((N, 16, 4))
    F[:, :, 0] = -dist
    for i in range(N):
        e = e_of[i]
        for c in np.nonzero(valid[i])[0]:
            F[i, c, 1:] = feat(e, can[i, c])
    models = {"d": [0], "d+logOmega": [0, 1], "d+logOmega+logStab": [0, 1, 2], "full": [0, 1, 2, 3], "d+logOmega+MI": [0, 1, 3]}
    names = ["kappa(-d)", "a_logOmega", "beta_logStab", "mu_MI"]
    res = {"events": int(N), "fit": float(D["fit"]), "mean_choice_set": float(valid.sum(1).mean()), "models": {}}
    for mn, cols in models.items():
        th, f = clogit(F[:, :, cols], valid, x)
        res["models"][mn] = {"params": {names[c]: float(v) for c, v in zip(cols, th)}, "nll": f, "bits_per_event": f / N / math.log(2)}
        print(mn, res["models"][mn], flush=True)
    M = res["models"]
    res["H23.3_bits_lost_dropping_logStab"] = M["d+logOmega"]["bits_per_event"] - M["d+logOmega+logStab"]["bits_per_event"]
    rng = np.random.default_rng(2300)
    nets = np.unique(b)
    pos = {n: np.nonzero(b == n)[0] for n in nets}
    bs = {"beta_logStab(d+logOmega+logStab)": [], "mu_MI(full)": [], "beta_logStab(full)": []}
    for _ in range(boots):
        idx = np.concatenate([pos[n] for n in rng.choice(nets, size=len(nets))])
        th3, _ = clogit(F[idx][:, :, [0, 1, 2]], valid[idx], x[idx])
        th4, _ = clogit(F[idx], valid[idx], x[idx])
        bs["beta_logStab(d+logOmega+logStab)"].append(th3[2]); bs["mu_MI(full)"].append(th4[3]); bs["beta_logStab(full)"].append(th4[2])
    res["bootstrap_99"] = {k: [float(np.percentile(v, 0.5)), float(np.percentile(v, 99.5))] for k, v in bs.items()}
    print(res["bootstrap_99"], res["H23.3_bits_lost_dropping_logStab"])
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    run() if sys.argv[1] == "run" else analyse()
