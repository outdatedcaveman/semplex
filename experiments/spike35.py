"""Spike 35 (pre-registered in SPIKE_35_REPORT.md): certified Occam compilation at n = 6; priors compared.

  python -m experiments.spike35 occam       compile all 400 tasks
  python -m experiments.spike35 nets ACT    tanh | relu
  python -m experiments.spike35 analyse
"""

from __future__ import annotations

import json
import pathlib
import sys
import time

import numpy as np

from cerp import bounds, kernel, kernel_bounds, netsolve

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "experiments" / "results" / "spike35_raw"
OUT = ROOT / "experiments" / "results" / "spike35.json"
N = 6
P = np.array([[(x >> i) & 1 for i in range(N)] for x in range(1 << N)])
XS = (2 * P - 1).astype(np.float32)


def bits(y):
    return sum(int(v) << x for x, v in enumerate(y))


def targets(n_targets=200, seed=3_500):
    rng = np.random.default_rng(seed); out = []
    while len(out) < n_targets:
        W = rng.integers(-3, 4, (2, N)); b = rng.integers(-6, 7, 2); h = (P @ W.T + b >= 0).astype(int)
        o = rng.integers(-2, 3, 2); c = int(rng.integers(-2, 3)); y = (h @ o + c >= 0)
        if not 16 <= y.sum() <= 48:
            continue
        f = bits(y)
        cert = bounds.not_threshold_cert(N, f)
        if cert and kernel_bounds.check_not_threshold(N, f, cert["pos"], cert["neg"]).ok:
            out.append(f)
    return out


def tasks():
    cache = RAW / "tasks.json"
    if cache.exists():
        return [tuple(t) for t in json.loads(cache.read_text())]
    T = targets(); rng = np.random.default_rng(3_501); out = []
    for f in T:
        for _ in range(2):
            care = bits(np.isin(np.arange(64), rng.choice(64, 48, replace=False)))
            out.append((f, care))
    RAW.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(out))
    return out


def net_eval(art):
    return np.array([kernel.evaluate(art, {f"x{i}": int(P[x, i]) for i in range(N)}) for x in range(64)], dtype=bool)


def compile_occam(f, care):
    fc = f & care
    t0 = time.time()
    st, art = netsolve.solve(fc, N, netsolve.layered(N, []), W=4, care=care, time_limit=20)
    cost, certified, spec = None, False, None
    if st == "sat":
        cost, spec = 1, netsolve.layered(N, [])
    else:
        c = bounds.not_threshold_cert_partial(N, fc, care)
        certified = bool(c) and kernel_bounds.check_not_threshold_partial(N, fc, care, c["pos"], c["neg"]).ok
        for k, widths in ((3, [2]), (4, [3])):
            st, art = netsolve.solve(fc, N, netsolve.layered(N, widths), W=4, care=care, time_limit=20)
            if st == "sat":
                cost, spec = k, netsolve.layered(N, widths); break
    if cost is None:
        return {"cost": None, "certified": certified, "seconds": time.time() - t0}
    preds, verified = [], True
    for s in range(5):
        st2, a2 = netsolve.solve(fc, N, spec, W=4, care=care, time_limit=20, rand_obj=s)
        a2 = a2 if st2 == "sat" else art
        y = net_eval(a2)
        verified &= all(y[x] == bool((f >> x) & 1) for x in range(64) if (care >> x) & 1)
        preds.append(y.tolist())
    return {"cost": cost, "certified": certified and cost == 3, "verified": bool(verified), "preds": preds,
            "seconds": time.time() - t0}


def run_occam():
    TK = tasks(); res = []
    for i, (f, care) in enumerate(TK):
        r = compile_occam(f, care); r.update({"f": f, "care": care}); res.append(r)
        if i % 50 == 0:
            print(i, r["cost"], r["certified"], round(r["seconds"], 2), flush=True)
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "occam.json").write_text(json.dumps(res))


def phi(pre, act):
    if act == "tanh":
        h = np.tanh(pre); return h, 1 - h * h
    return np.maximum(pre, 0), (pre > 0).astype(np.float32)


def run_nets(act, seeds=10):
    TK = tasks()
    fs = np.array([f for f, _ in TK for _ in range(seeds)], dtype=object)
    cares = np.array([c for _, c in TK for _ in range(seeds)], dtype=object)
    Y = np.array([[(int(f) >> x) & 1 for x in range(64)] for f in fs], dtype=np.float32)
    C = np.array([[(int(c) >> x) & 1 for x in range(64)] for c in cares], dtype=np.float32)
    B = len(fs); rng = np.random.default_rng(3_510 + (act == "relu"))
    p = {"W1": rng.normal(0, 0.5, (B, 8, N)).astype(np.float32), "b1": rng.normal(0, 0.5, (B, 8)).astype(np.float32),
         "W2": rng.normal(0, 0.5, (B, 8)).astype(np.float32), "b2": np.zeros(B, np.float32)}
    m = {k: np.zeros_like(v) for k, v in p.items()}; v = {k: np.zeros_like(x) for k, x in p.items()}
    for t in range(1, 3001):
        pre = np.einsum("bhn,xn->bxh", p["W1"], XS) + p["b1"][:, None, :]
        h, d = phi(pre, act); z = np.einsum("bxh,bh->bx", h, p["W2"]) + p["b2"][:, None]
        dz = (1 / (1 + np.exp(-z)) - Y) * C / C.sum(1, keepdims=True)
        g = {"W2": np.einsum("bx,bxh->bh", dz, h), "b2": dz.sum(1)}
        dh = dz[:, :, None] * p["W2"][:, None, :] * d
        g["W1"] = np.einsum("bxh,xn->bhn", dh, XS); g["b1"] = dh.sum(1)
        for k in p:
            m[k] = 0.9 * m[k] + 0.1 * g[k]; v[k] = 0.999 * v[k] + 0.001 * g[k] ** 2
            p[k] = p[k] - 0.03 * (m[k] / (1 - 0.9 ** t)) / (np.sqrt(v[k] / (1 - 0.999 ** t)) + 1e-8) - 0.03 * 0.03 * p[k]
    pre = np.einsum("bhn,xn->bxh", p["W1"], XS) + p["b1"][:, None, :]
    out = (np.einsum("bxh,bh->bx", phi(pre, act)[0], p["W2"]) + p["b2"][:, None]) >= 0
    fit = ((out == Y.astype(bool)) | (C == 0)).all(1)
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / f"nets_{act}.json").write_text(json.dumps({"out": out.astype(int).tolist(), "fit": fit.tolist(), "seeds": seeds}))
    print(act, "fit", float(fit.mean()), flush=True)


def ntk(act, n=400_000, seed=3_520):
    rng = np.random.default_rng(seed); w = rng.normal(0, 0.5, (n, N)); b = rng.normal(0, 0.5, n)
    z = (XS.astype(np.float64) @ w.T + b).astype(np.float32); h, d = phi(z, act)
    h = h.astype(np.float64); d = d.astype(np.float64); X = XS.astype(np.float64)
    return 8 * (h @ h.T / n + 0.25 * (d @ d.T / n) * (X @ X.T + 1)) + 1


def kernel_pred(K, f, care):
    seen = [x for x in range(64) if (care >> x) & 1]; y = np.array([(f >> x) & 1 for x in range(64)], float)
    Kss = K[np.ix_(seen, seen)]; a = np.linalg.solve(Kss + 1e-3 * np.trace(Kss) / len(seen) * np.eye(len(seen)), 2 * y[seen] - 1)
    return K[:, seen] @ a > 0


def bal(p, t):
    return 0.5 * ((p & t).sum() / t.sum() + ((~p) & (~t)).sum() / (~t).sum())


def analyse():
    occ = json.loads((RAW / "occam.json").read_text()); TK = [(o["f"], o["care"]) for o in occ]
    held = [np.array([not (c >> x) & 1 for x in range(64)]) for _, c in TK]
    truth = [np.array([(f >> x) & 1 for x in range(64)], bool) for f, _ in TK]
    found = [o["cost"] is not None and o.get("verified", False) for o in occ]
    res = {"tasks": len(TK), "H35.1_frac_found_verified": float(np.mean(found)),
           "frac_seen_consistent_with_single_threshold": float(np.mean([o["cost"] == 1 for o in occ])),
           "mean_seconds": float(np.mean([o["seconds"] for o in occ]))}
    c3 = [o for o in occ if o["cost"] == 3]
    res["H35.2_frac_cost3_certified"] = float(np.mean([o["certified"] for o in c3])) if c3 else None
    agree_all = []; P_occ, T_all = [], []
    for o, h, t in zip(occ, held, truth):
        if o["cost"] is None:
            continue
        pr = np.array(o["preds"], bool)[:, h]
        agree_all.append(bool((pr == pr[0]).all()))
        P_occ.append(pr.mean(0) > 0.5); T_all.append(t[h])
    res["H35.3_frac_all5_agree"] = float(np.mean(agree_all))
    Po, To = np.concatenate(P_occ), np.concatenate(T_all)
    res["occam_bal"] = float(bal(Po, To)); res["occam_acc"] = float((Po == To).mean())
    for act in ("tanh", "relu"):
        K = ntk(act); kp = np.concatenate([kernel_pred(K, f, c)[h] for (f, c), h in zip(TK, held)])
        Tt = np.concatenate([t[h] for t, h in zip(truth, held)])
        res[f"ntk_{act}_bal"] = float(bal(kp, Tt)); res[f"ntk_{act}_acc"] = float((kp == Tt).mean())
        d = json.loads((RAW / f"nets_{act}.json").read_text()); out = np.array(d["out"], bool); fit = np.array(d["fit"]); s = d["seeds"]
        P_, T_ = [], []
        for i, (h, t) in enumerate(zip(held, truth)):
            for j in range(s):
                if fit[i * s + j]:
                    P_.append(out[i * s + j][h]); T_.append(t[h])
        P_, T_ = np.concatenate(P_), np.concatenate(T_)
        res[f"net_{act}_bal"] = float(bal(P_, T_)); res[f"net_{act}_acc"] = float((P_ == T_).mean()); res[f"net_{act}_fit"] = float(fit.mean())
    res["H35.4_occam_minus_nets"] = res["occam_bal"] - (res["net_tanh_bal"] + res["net_relu_bal"]) / 2
    res["H35.5_occam_minus_ntk"] = res["occam_bal"] - (res["ntk_tanh_bal"] + res["ntk_relu_bal"]) / 2
    OUT.write_text(json.dumps(res, indent=1)); print(json.dumps(res, indent=1))


if __name__ == "__main__":
    {"occam": lambda: run_occam(), "nets": lambda: run_nets(sys.argv[2]), "analyse": lambda: analyse()}[sys.argv[1]]()
