"""Spike 26 (pre-registered in SPIKE_26_REPORT.md): lawful completion of partial operation tables.

  python -m experiments.spike26 run
  python -m experiments.spike26 analyse
"""

from __future__ import annotations

import itertools
import json
import math
import pathlib
import sys
from collections import defaultdict

import numpy as np

from experiments.spike17 import orbit_beta

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "experiments" / "results" / "spike26_raw"
OUT = ROOT / "experiments" / "results" / "spike26.json"
CELLS = [(a, b) for a in range(3) for b in range(3)]
PERMS = list(itertools.permutations(range(3)))


def assoc(t):
    return all(t[3 * t[3 * a + b] + c] == t[3 * a + t[3 * b + c]] for a in range(3) for b in range(3) for c in range(3))


SEMI = [t for t in itertools.product(range(3), repeat=9) if assoc(t)]


def tasks(n=300, n_sym=150):
    """n general tasks (seed 2600), then n_sym further tasks with a nontrivial symmetry group (seed 2603)."""
    out, seen = [], set()
    for seed, want, need_sym in ((2600, n, False), (2603, n + n_sym, True)):
        rng = np.random.default_rng(seed)
        while len(out) < want:
            S = SEMI[rng.integers(len(SEMI))]
            k = int(rng.integers(4, 7))
            R = tuple(sorted(rng.choice(9, size=k, replace=False).tolist()))
            key = (R, tuple(S[i] for i in R))
            if key in seen:
                continue
            comps = [t for t in SEMI if all(t[i] == S[i] for i in R)]
            task = {"S": list(S), "R": list(R), "assoc_completions": [list(c) for c in comps], "pool": "symmetric" if need_sym else "general"}
            if len(comps) >= 2 and (not need_sym or len(group(task)) > 1):
                seen.add(key); out.append(task)
    return out


def group(task):
    R, S = set(task["R"]), task["S"]
    G = []
    for p in PERMS:
        img = {3 * p[a] + p[b] for a, b in (CELLS[i] for i in R)}
        if img == R and all(p[S[3 * a + b]] == S[3 * p[a] + p[b]] for a, b in (CELLS[i] for i in R)):
            G.append(p)
    return G


def act(p, t):
    out = [0] * 9
    for a in range(3):
        for b in range(3):
            out[3 * p[a] + p[b]] = p[t[3 * a + b]]
    return tuple(out)


def train(T, seeds, frozen, steps=2000):
    nt = len(T); B = nt * seeds
    X = np.zeros((9, 6), np.float32)
    for i, (a, b) in enumerate(CELLS):
        X[i, a] = 1; X[i, 3 + b] = 1
    rng = np.random.default_rng(2601 + int(frozen))
    H = 256 if frozen else 16
    W1 = (rng.normal(size=(B, 6, H)) / math.sqrt(6)).astype(np.float32); b1 = np.zeros((B, 1, H), np.float32)
    W2 = (rng.normal(size=(B, H, 3)) / math.sqrt(H) * (math.sqrt(16 / H))).astype(np.float32); b2 = np.zeros((B, 1, 3), np.float32)
    Y = np.zeros((B, 9, 3), np.float32); M = np.zeros((B, 9, 1), np.float32)
    for i, t in enumerate(T):
        for s in range(seeds):
            b = i * seeds + s
            for c in t["R"]:
                Y[b, c, t["S"][c]] = 1; M[b, c] = 1
    P = {"W2": W2, "b2": b2} if frozen else {"W1": W1, "b1": b1, "W2": W2, "b2": b2}
    m = {k: np.zeros_like(v) for k, v in P.items()}; v = {k: np.zeros_like(x) for k, x in P.items()}
    for step in range(1, steps + 1):
        pre = X[None] @ P.get("W1", W1) + P.get("b1", b1); h = np.tanh(pre)
        z = h @ P["W2"] + P["b2"]; z = z - z.max(-1, keepdims=True); pr = np.exp(z); pr /= pr.sum(-1, keepdims=True)
        dz = (pr - Y) * M / M.sum(1, keepdims=True)
        g = {"W2": np.swapaxes(h, 1, 2) @ dz, "b2": dz.sum(1, keepdims=True)}
        if not frozen:
            dh = (dz @ np.swapaxes(P["W2"], 1, 2)) * (1 - h * h)
            g["W1"] = np.swapaxes(np.broadcast_to(X, dh.shape[:2] + (6,)), 1, 2) @ dh; g["b1"] = dh.sum(1, keepdims=True)
        for k in P:
            m[k] = 0.9 * m[k] + 0.1 * g[k]; v[k] = 0.999 * v[k] + 0.001 * g[k] ** 2
            P[k] = P[k] - 0.03 * (m[k] / (1 - 0.9 ** step)) / (np.sqrt(v[k] / (1 - 0.999 ** step)) + 1e-8) - 0.03 * 0.01 * P[k]
    pre = X[None] @ P.get("W1", W1) + P.get("b1", b1)
    return (np.tanh(pre) @ P["W2"] + P["b2"]).argmax(-1)                      # (B, 9)


def run():
    T = tasks()
    out = {"tasks": T}
    for name, frozen in (("full", False), ("selection", True)):
        pred = train(T, 40, frozen)
        out[name] = pred.reshape(len(T), 40, 9).tolist()
        print(name, "done", flush=True)
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "runs.json").write_text(json.dumps(out))


def analyse():
    d = json.loads((RAW / "runs.json").read_text())
    T = d["tasks"]
    res = {"n_tasks": len(T), "n_semigroups": len(SEMI)}
    gen = [i for i, t in enumerate(T) if t["pool"] == "general"]
    unif = [len(T[i]["assoc_completions"]) / 3 ** (9 - len(T[i]["R"])) for i in gen]
    res["uniform_lawful_rate"] = float(np.mean(unif))
    for name in ("full", "selection"):
        fit = law = src = chance_src = gfit = glaw = 0
        mass, okey, osz = {}, {}, {}
        per_task = []
        for i, t in enumerate(T):
            comps = [tuple(c) for c in t["assoc_completions"]]
            cset = set(comps)
            cnt = defaultdict(float); f_i = l_i = 0
            for c in d[name][i]:
                c = tuple(c)
                if any(c[r] != t["S"][r] for r in t["R"]):
                    continue
                fit += 1; f_i += 1
                if c in cset:
                    law += 1; l_i += 1; cnt[c] += 1
                    src += int(c == tuple(t["S"])); chance_src += 1 / len(comps)
            per_task.append((f_i, l_i))
            if t["pool"] == "general":
                gfit += f_i; glaw += l_i
            G = group(t)
            if len(G) > 1:
                ok = {c: min(act(p, c) for p in G) for c in comps}
                sz = defaultdict(int)
                for o in ok.values():
                    sz[o] += 1
                mass[i] = {c: cnt.get(c, 0.0) for c in comps}; okey[i] = ok; osz[i] = sz
        r = {"fit_rate": fit / (40 * len(T)), "lawful_rate": glaw / gfit, "lawful_rate_all_tasks": law / fit, "source_rate": src / max(law, 1), "source_chance": chance_src / max(law, 1),
             "tasks_with_symmetry": len(mass)}
        r["ratio_to_uniform"] = r["lawful_rate"] / res["uniform_lawful_rate"]
        r["beta"] = orbit_beta(mass, okey, osz) if mass else None
        rng = np.random.default_rng(2602); keys = list(mass); bs = []
        for _ in range(1000):
            smp = rng.choice(len(keys), size=len(keys))
            mb = {j: mass[keys[s]] for j, s in enumerate(smp)}; kb = {j: okey[keys[s]] for j, s in enumerate(smp)}; sb = {j: osz[keys[s]] for j, s in enumerate(smp)}
            try:
                bs.append(orbit_beta(mb, kb, sb))
            except Exception:
                pass
        r["beta_95"] = [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))] if bs else None
        res[name] = r
        print(name, r, flush=True)
    res["full_over_selection_lawful"] = res["full"]["lawful_rate"] / res["selection"]["lawful_rate"]
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    run() if sys.argv[1] == "run" else analyse()
