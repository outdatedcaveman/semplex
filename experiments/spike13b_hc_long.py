"""Spike 13b: Long-horizon 6-input grokking (H-C follow-up, P064)."""

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cerp import learnrules as lr

OUT = ROOT / "experiments" / "results" / "spike13b_hc_long.json"


def run_hc_long(steps=3000, seeds=8, scales=(1.0, 1.5, 2.0), wds=(0.05, 0.1)):
    n = 6
    XS = lr.inputs(n)
    f_bits = [
        ((int((x >> 0) & 1) + int((x >> 1) & 1) + int((x >> 2) & 1) >= 2)
         ^ (int((x >> 3) & 1) + int((x >> 4) & 1) + int((x >> 5) & 1) >= 2))
        for x in range(1 << n)
    ]
    rng_split = np.random.default_rng(42)
    train_idx = rng_split.choice(1 << n, size=32, replace=False)
    care_mask = np.zeros(1 << n, dtype=float)
    care_mask[train_idx] = 1.0
    T = np.array([f_bits] * seeds, dtype=float)
    C = np.array([care_mask] * seeds, dtype=float)

    rows = []
    for wd in wds:
        for scale in scales:
            p = lr.init(seeds, 12, n, np.random.default_rng(100 + int(scale * 10)), scale=scale)
            t_fit = [None] * seeds
            t_gen = [None] * seeds

            def on_step(t, cur):
                if t % 50 != 0:
                    return
                _, _, z = lr.forward(cur, XS)
                pred = (z >= 0).astype(float)
                for b in range(seeds):
                    if t_fit[b] is None and np.all(pred[b, train_idx] == T[b, train_idx]):
                        t_fit[b] = t
                    if t_gen[b] is None and np.mean(pred[b] == T[b]) >= 0.95:
                        t_gen[b] = t

            lr.train(p, XS, T, C, steps=steps, rule="backprop", lr=0.05, wd=wd, on_step=on_step)
            delays = [g - f for f, g in zip(t_fit, t_gen) if f is not None and g is not None]
            rows.append({
                "wd": wd,
                "scale": scale,
                "n_fit": sum(x is not None for x in t_fit),
                "n_grokked": sum(x is not None for x in t_gen),
                "mean_t_fit": round(float(np.mean([x for x in t_fit if x is not None])), 1) if any(x is not None for x in t_fit) else None,
                "mean_t_gen": round(float(np.mean([x for x in t_gen if x is not None])), 1) if any(x is not None for x in t_gen) else None,
                "mean_delay": round(float(np.mean(delays)), 1) if delays else None,
            })
    return rows


def main():
    t0 = time.time()
    rows = run_hc_long()
    res = {"elapsed_s": round(time.time() - t0, 2), "steps": 3000, "rows": rows}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
