"""Spike 13: Empirical probes for C1 (statistical lift), H-C (grokking delay), and H-E (n=5 depth-3).

  python -m experiments.spike13_c1_hc_he
"""

from __future__ import annotations

import json
import pathlib
import time

import numpy as np

from cerp import bounds, learnrules as lr
from cerp.epistemics.inquiry import inquire
from cerp.epistemics.ontologies import CANDIDATES
from cerp.epistemics.world import ALL_ACTIONS, Interface
from cerp.ledger import Status

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "experiments" / "results" / "spike13_c1_hc_he.json"


def run_c1_lift(seeds=4):
    """Sweep sample budget per protocol (n_per) vs alpha on noisy worlds."""
    truth_map = {"latent_causal": "O1:latent-causal", "latent_confounded": "O3:latent-confounded"}
    rows = []
    for n_per in (200, 600, 1200):
        for alpha in (0.005, 0.05):
            total_emp, truth_rej = 0, 0
            for wname, tname in truth_map.items():
                for s in range(seeds):
                    rep = inquire(Interface(wname, ALL_ACTIONS, seed=s), CANDIDATES,
                                  seed=s, n_initial=n_per, n_batch=n_per, alpha=alpha)
                    if tname not in rep["survivors"]:
                        truth_rej += 1
                    for qname, ans in rep["answers"].items():
                        st = getattr(ans.get("status"), "value", ans.get("status"))
                        if st == Status.EMPIRICALLY_SUPPORTED.value:
                            total_emp += 1
            rows.append({
                "n_per": n_per, "alpha": alpha,
                "runs": 2 * seeds,
                "truth_rejected": truth_rej,
                "truth_rejection_rate": round(truth_rej / (2 * seeds), 3),
                "empirical_answers": total_emp,
            })
    return rows


def run_hc_grokking(scales=(0.5, 1.0, 1.5, 2.0), seeds=8, steps=600):
    """6-input planted 2-neuron XOR-of-halfspaces: grokking delay vs init scale."""
    n = 6
    XS = lr.inputs(n)
    # Planted function: (x0 + x1 + x2 >= 2) XOR (x3 + x4 + x5 >= 2)
    f_bits = [((int((x >> 0) & 1) + int((x >> 1) & 1) + int((x >> 2) & 1) >= 2) ^
               (int((x >> 3) & 1) + int((x >> 4) & 1) + int((x >> 5) & 1) >= 2))
              for x in range(1 << n)]
    rng_split = np.random.default_rng(42)
    train_idx = rng_split.choice(1 << n, size=32, replace=False)
    care_mask = np.zeros(1 << n, dtype=float)
    care_mask[train_idx] = 1.0
    T = np.array([f_bits] * seeds, dtype=float)
    C = np.array([care_mask] * seeds, dtype=float)

    rows = []
    for scale in scales:
        p = lr.init(seeds, 12, n, np.random.default_rng(100 + int(scale * 10)), scale=scale)
        t_fit = [None] * seeds
        t_gen = [None] * seeds

        def on_step(t, cur):
            if t % 20 != 0:
                return
            _, _, z = lr.forward(cur, XS)
            pred = (z >= 0).astype(float)
            for b in range(seeds):
                if t_fit[b] is None and np.all(pred[b, train_idx] == T[b, train_idx]):
                    t_fit[b] = t
                if t_gen[b] is None and np.mean(pred[b] == T[b]) >= 0.95:
                    t_gen[b] = t

        lr.train(p, XS, T, C, steps=steps, rule="backprop", lr=0.05, wd=0.05, on_step=on_step)
        delays = [g - f for f, g in zip(t_fit, t_gen) if f is not None and g is not None]
        rows.append({
            "scale": scale,
            "n_fit": sum(x is not None for x in t_fit),
            "n_grokked": sum(x is not None for x in t_gen),
            "mean_t_fit": round(float(np.mean([x for x in t_fit if x is not None])), 1) if any(x is not None for x in t_fit) else None,
            "mean_t_gen": round(float(np.mean([x for x in t_gen if x is not None])), 1) if any(x is not None for x in t_gen) else None,
            "mean_delay": round(float(np.mean(delays)), 1) if delays else None,
        })
    return rows


def run_he_depth5(n_samples=300):
    """Sample 5-input depth-3 (2-layer hidden + output) candidates and check not_two_halfspaces_cert."""
    rng = np.random.default_rng(7)
    X5 = np.array([[(i >> j) & 1 for j in range(5)] for i in range(32)], dtype=np.int64)
    certified_not_2hs = 0
    seen = set()
    for _ in range(n_samples):
        # 2 units in layer 1 -> 1 unit in layer 2 (AND/OR) -> output XOR with another L1 unit
        W1 = rng.integers(-2, 3, size=(3, 5))
        t1 = rng.integers(-2, 3, size=3)
        h1 = ((X5 @ W1.T) >= t1).astype(np.int64)  # (32, 3)
        # Depth-3 output: (h1[:,0] & h1[:,1]) ^ h1[:,2]
        out = (h1[:, 0] & h1[:, 1]) ^ h1[:, 2]
        f = sum(int(v) << i for i, v in enumerate(out))
        if f in seen:
            continue
        seen.add(f)
        if bounds.not_two_halfspaces_cert(5, f, kmax=2) is not None:
            certified_not_2hs += 1
    return {"distinct_candidates": len(seen), "certified_not_two_halfspaces_k2": certified_not_2hs}


def main():
    t0 = time.time()
    c1 = run_c1_lift()
    hc = run_hc_grokking()
    he = run_he_depth5()
    res = {"elapsed_s": round(time.time() - t0, 2), "c1_lift": c1, "hc_grokking": hc, "he_depth5": he}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
