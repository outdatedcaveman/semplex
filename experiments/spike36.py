"""Spike 36 (pre-registered in SPIKE_36_REPORT.md): replication at n = 5, 6 and width (lazy-regime) arm.

  python -m experiments.spike36 tasks N           build and cache tasks (N = 5 | 6)
  python -m experiments.spike36 occam N
  python -m experiments.spike36 nets N ACT        ACT = tanh | relu (width 8, 10 seeds)
  python -m experiments.spike36 width M           M = 8 | 64 | 512 | 2048 (n = 6, tanh, 100 tasks x 4 seeds)
  python -m experiments.spike36 analyse
"""

from __future__ import annotations

import json
import math
import pathlib
import sys
import time

import numpy as np

from cerp import bounds, kernel, kernel_bounds, netsolve

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "experiments" / "results" / "spike36_raw"
OUT = ROOT / "experiments" / "results" / "spike36.json"
SEEN = {5: 24, 6: 48}
SEED = {5: 3_650, 6: 3_600}


def pts(n):
    return np.array([[(x >> i) & 1 for i in range(n)] for x in range(1 << n)])


def bits(y):
    return sum(int(v) << x for x, v in enumerate(y))


def tasks(n):
    cache = RAW / f"tasks_n{n}.json"
    if cache.exists():
        return [tuple(t) for t in json.loads(cache.read_text())]
    P = pts(n); K = 1 << n; rng = np.random.default_rng(SEED[n]); T = []
    while len(T) < 150:
        W = rng.integers(-3, 4, (2, n)); b = rng.integers(-6, 7, 2); h = (P @ W.T + b >= 0).astype(int)
        o = rng.integers(-2, 3, 2); c = int(rng.integers(-2, 3)); y = (h @ o + c >= 0)
        if not 0.25 * K <= y.sum() <= 0.75 * K:
            continue
        f = bits(y); cert = bounds.not_threshold_cert(n, f)
        if cert and kernel_bounds.check_not_threshold(n, f, cert["pos"], cert["neg"]).ok and f not in T:
            T.append(f)
    rng2 = np.random.default_rng(SEED[n] + 1); out = []
    for f in T:
        for _ in range(2):
            out.append((f, bits(np.isin(np.arange(K), rng2.choice(K, SEEN[n], replace=False)))))
    RAW.mkdir(parents=True, exist_ok=True); cache.write_text(json.dumps(out))
    return out


def compile_occam(n, f, care):
    P = pts(n); K = 1 << n; fc = f & care; t0 = time.time()
    st, art = netsolve.solve(fc, n, netsolve.layered(n, []), W=4, care=care, time_limit=20)
    cost, certified, spec = None, False, None
    if st == "sat":
        cost, spec = 1, netsolve.layered(n, [])
    else:
        c = bounds.not_threshold_cert_partial(n, fc, care)
        certified = bool(c) and kernel_bounds.check_not_threshold_partial(n, fc, care, c["pos"], c["neg"]).ok
        for k, widths in ((3, [2]), (4, [3])):
            st, art = netsolve.solve(fc, n, netsolve.layered(n, widths), W=4, care=care, time_limit=20)
            if st == "sat":
                cost, spec = k, netsolve.layered(n, widths); break
    if cost is None:
        return {"cost": None, "certified": certified, "seconds": time.time() - t0}
    preds, verified = [], True
    for s in range(5):
        st2, a2 = netsolve.solve(fc, n, spec, W=4, care=care, time_limit=20, rand_obj=s)
        a2 = a2 if st2 == "sat" else art
        y = np.array([kernel.evaluate(a2, {f"x{i}": int(P[x, i]) for i in range(n)}) for x in range(K)], dtype=bool)
        verified &= all(y[x] == bool((f >> x) & 1) for x in range(K) if (care >> x) & 1)
        preds.append(y.tolist())
    return {"cost": cost, "certified": certified and cost == 3, "verified": bool(verified), "preds": preds, "seconds": time.time() - t0}


def run_occam(n):
    res = []
    for i, (f, c) in enumerate(tasks(n)):
        r = compile_occam(n, f, c); r.update({"f": f, "care": c}); res.append(r)
    RAW.mkdir(parents=True, exist_ok=True); (RAW / f"occam_n{n}.json").write_text(json.dumps(res))
    print("occam n", n, "done", flush=True)


def phi(pre, act):
    if act == "tanh":
        h = np.tanh(pre); return h, 1 - h * h
    return np.maximum(pre, 0), (pre > 0).astype(np.float32)


def train(n, TK, act, seeds, m, lr, out_scale, seed):
    XS = (2 * pts(n) - 1).astype(np.float32); K = 1 << n
    Y = np.array([[(f >> x) & 1 for x in range(K)] for f, _ in TK for _ in range(seeds)], dtype=np.float32)
    C = np.array([[(c >> x) & 1 for x in range(K)] for _, c in TK for _ in range(seeds)], dtype=np.float32)
    B = len(Y); rng = np.random.default_rng(seed)
    p = {"W1": rng.normal(0, 0.5, (B, m, n)).astype(np.float32), "b1": rng.normal(0, 0.5, (B, m)).astype(np.float32),
         "W2": rng.normal(0, out_scale, (B, m)).astype(np.float32), "b2": np.zeros(B, np.float32)}
    mo = {k: np.zeros_like(v) for k, v in p.items()}; ve = {k: np.zeros_like(x) for k, x in p.items()}
    for t in range(1, 3001):
        pre = np.einsum("bhn,xn->bxh", p["W1"], XS) + p["b1"][:, None, :]
        h, d = phi(pre, act); z = np.einsum("bxh,bh->bx", h, p["W2"]) + p["b2"][:, None]
        dz = (1 / (1 + np.exp(-np.clip(z, -60, 60))) - Y) * C / C.sum(1, keepdims=True)
        g = {"W2": np.einsum("bx,bxh->bh", dz, h), "b2": dz.sum(1)}
        dh = dz[:, :, None] * p["W2"][:, None, :] * d
        g["W1"] = np.einsum("bxh,xn->bhn", dh, XS); g["b1"] = dh.sum(1)
        for k in p:
            mo[k] = 0.9 * mo[k] + 0.1 * g[k]; ve[k] = 0.999 * ve[k] + 0.001 * g[k] ** 2
            p[k] = p[k] - lr * (mo[k] / (1 - 0.9 ** t)) / (np.sqrt(ve[k] / (1 - 0.999 ** t)) + 1e-8) - lr * 0.03 * p[k]
    pre = np.einsum("bhn,xn->bxh", p["W1"], XS) + p["b1"][:, None, :]
    out = (np.einsum("bxh,bh->bx", phi(pre, act)[0], p["W2"]) + p["b2"][:, None]) >= 0
    fit = ((out == Y.astype(bool)) | (C == 0)).all(1)
    return out, fit


def run_nets(n, act):
    out, fit = train(n, tasks(n), act, 10, 8, 0.03, 0.5, 3_660 + 10 * n + (act == "relu"))
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / f"nets_n{n}_{act}.json").write_text(json.dumps({"out": out.astype(int).tolist(), "fit": fit.tolist(), "seeds": 10}))
    print("nets", n, act, "fit", float(fit.mean()), flush=True)


def run_width(m):
    TK = tasks(6)[:100]
    out, fit = train(6, TK, "tanh", 4, m, 0.03 * math.sqrt(8 / m), 0.5 * math.sqrt(8 / m), 3_690 + m)
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / f"width_{m}.json").write_text(json.dumps({"out": out.astype(int).tolist(), "fit": fit.tolist(), "seeds": 4}))
    print("width", m, "fit", float(fit.mean()), flush=True)


def ntk(n, act, m=8, out_var=0.25, samples=400_000, seed=3_670):
    XS = (2 * pts(n) - 1).astype(np.float64); rng = np.random.default_rng(seed)
    w = rng.normal(0, 0.5, (samples, n)); b = rng.normal(0, 0.5, samples)
    h, d = phi((XS @ w.T + b).astype(np.float32), act); h = h.astype(np.float64); d = d.astype(np.float64)
    return m * (h @ h.T / samples) + m * out_var * (d @ d.T / samples) * (XS @ XS.T + 1) + 1


def kpred(K, n, f, care):
    seen = [x for x in range(1 << n) if (care >> x) & 1]; y = np.array([(f >> x) & 1 for x in range(1 << n)], float)
    Kss = K[np.ix_(seen, seen)]
    a = np.linalg.solve(Kss + 1e-3 * np.trace(Kss) / len(seen) * np.eye(len(seen)), 2 * y[seen] - 1)
    return K[:, seen] @ a > 0


def bal(p, t):
    return 0.5 * ((p & t).sum() / t.sum() + ((~p) & (~t)).sum() / (~t).sum())


def compare(n, TK, occ, nets_out, fit, seeds, K):
    a_o = a_k = tot = dis = side = 0; P, T = [], []
    for i, ((f, c), o) in enumerate(zip(TK, occ)):
        h = np.array([not (c >> x) & 1 for x in range(1 << n)]); t = np.array([(f >> x) & 1 for x in range(1 << n)], bool)[h]
        op = np.array(o["preds"], bool)[:, h].mean(0) > 0.5; kp = kpred(K, n, f, c)[h]
        for j in range(seeds):
            if not fit[i * seeds + j]:
                continue
            nt = nets_out[i * seeds + j][h]; a_o += (nt == op).sum(); a_k += (nt == kp).sum(); tot += len(nt)
            mk = nt != kp; dis += mk.sum(); side += (op == nt)[mk].sum(); P.append(nt); T.append(t)
    P, T = np.concatenate(P), np.concatenate(T)
    return {"agree_occam": a_o / tot, "agree_ntk": a_k / tot, "occam_sides_with_net_where_net_ne_ntk": side / dis if dis else None,
            "bal_net": float(bal(P, T)), "n_disagreements": int(dis)}


def analyse():
    res = {"R": {}, "W": {}}
    for n in (5, 6):
        TK = tasks(n); occ = json.loads((RAW / f"occam_n{n}.json").read_text())
        held = [np.array([not (c >> x) & 1 for x in range(1 << n)]) for _, c in TK]
        truth = [np.array([(f >> x) & 1 for x in range(1 << n)], bool) for f, _ in TK]
        Po = np.concatenate([np.array(o["preds"], bool)[:, h].mean(0) > 0.5 for o, h in zip(occ, held)])
        To = np.concatenate([t[h] for t, h in zip(truth, held)])
        base = {"occam_bal": float(bal(Po, To)), "frac_verified": float(np.mean([o.get("verified", False) for o in occ])),
                "frac_cost3_certified": float(np.mean([o["certified"] for o in occ if o["cost"] == 3]))}
        for act in ("tanh", "relu"):
            K = ntk(n, act); d = json.loads((RAW / f"nets_n{n}_{act}.json").read_text())
            r = compare(n, TK, occ, np.array(d["out"], bool), np.array(d["fit"]), d["seeds"], K)
            kp = np.concatenate([kpred(K, n, f, c)[h] for (f, c), h in zip(TK, held)])
            r.update(base); r["ntk_bal"] = float(bal(kp, To)); r["fit"] = float(np.mean(d["fit"]))
            res["R"][f"n{n}_{act}"] = {k: (float(v) if v is not None else None) for k, v in r.items()}
            print("R", n, act, {k: round(float(v), 3) for k, v in r.items() if v is not None}, flush=True)
    TK = tasks(6)[:100]; occ = json.loads((RAW / "occam_n6.json").read_text())[:100]
    for m in (8, 64, 512, 2048):
        f = RAW / f"width_{m}.json"
        if not f.exists():
            continue
        d = json.loads(f.read_text()); K = ntk(6, "tanh", m=m, out_var=0.25 * 8 / m)
        r = compare(6, TK, occ, np.array(d["out"], bool), np.array(d["fit"]), d["seeds"], K); r["fit"] = float(np.mean(d["fit"]))
        res["W"][str(m)] = {k: (float(v) if v is not None else None) for k, v in r.items()}
        print("W", m, {k: round(float(v), 3) for k, v in r.items() if v is not None}, flush=True)
    R = res["R"]; W = res["W"]
    res["H36.1_min_diff_agree_occam_minus_ntk"] = min(r["agree_occam"] - r["agree_ntk"] for r in R.values())
    res["H36.2_min_occam_sides_with_net"] = min(r["occam_sides_with_net_where_net_ne_ntk"] for r in R.values())
    if "8" in W and "2048" in W:
        res["H36.3_agree_ntk_2048_minus_8"] = W["2048"]["agree_ntk"] - W["8"]["agree_ntk"]
        res["H36.4_bal_2048_minus_8"] = W["2048"]["bal_net"] - W["8"]["bal_net"]
        res["H36.5_agree_occam_2048_minus_8"] = W["2048"]["agree_occam"] - W["8"]["agree_occam"]
    OUT.write_text(json.dumps(res, indent=1)); print({k: v for k, v in res.items() if k.startswith("H36")})


if __name__ == "__main__":
    a = sys.argv
    {"tasks": lambda: print(len(tasks(int(a[2])))), "occam": lambda: run_occam(int(a[2])), "nets": lambda: run_nets(int(a[2]), a[3]),
     "width": lambda: run_width(int(a[2])), "analyse": analyse}[a[1]]()
