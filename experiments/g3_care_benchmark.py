"""Fixed G3 benchmark (Gap B2): partial-care compilation at n = 8 and n = 10.

Generates 100 non-threshold 2-hidden-unit targets per dimension using the
experiments/spike36.py generator (seeds 8800 and 8810) restricted to 75%
care points (192/256 at n=8, 768/1024 at n=10), compiles each via
cerp.netsolve.compile_partial (W=4, max_width=4, time_limit=60.0, workers=4),
and verifies every returned network with cerp.kernel.evaluate on all care points.
"""

from __future__ import annotations

import json
import pathlib
import statistics
import time

import numpy as np

from cerp import bounds, kernel, kernel_bounds, netsolve

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "experiments" / "results" / "g3_care_benchmark.json"

SEEDS = {8: 8800, 10: 8810}
SEEN = {8: 192, 10: 768}
N_TARGETS = 100


def pts(n: int) -> np.ndarray:
    return np.array([[(x >> i) & 1 for i in range(n)] for x in range(1 << n)])


def bits(y) -> int:
    return sum(int(v) << x for x, v in enumerate(y))


def generate_tasks(n: int, count: int = N_TARGETS) -> list[tuple[int, int]]:
    P = pts(n)
    K = 1 << n
    rng = np.random.default_rng(SEEDS[n])
    T: list[int] = []
    T_set: set[int] = set()
    while len(T) < count:
        W = rng.integers(-3, 4, (2, n))
        b = rng.integers(-6, 7, 2)
        h = (P @ W.T + b >= 0).astype(int)
        o = rng.integers(-2, 3, 2)
        c = int(rng.integers(-2, 3))
        y = (h @ o + c >= 0)
        if not 0.25 * K <= y.sum() <= 0.75 * K:
            continue
        f = bits(y)
        if f in T_set:
            continue
        cert = bounds.not_threshold_cert(n, f)
        if cert and kernel_bounds.check_not_threshold(n, f, cert["pos"], cert["neg"]).ok:
            T.append(f)
            T_set.add(f)

    rng2 = np.random.default_rng(SEEDS[n] + 1)
    seen_k = SEEN[n]
    out: list[tuple[int, int]] = []
    for f in T:
        care = bits(np.isin(np.arange(K), rng2.choice(K, seen_k, replace=False)))
        out.append((f, care))
    return out


def verify_care(art: dict, f: int, n: int, care: int) -> bool:
    K = 1 << n
    for x in range(K):
        if (care >> x) & 1:
            inp = {f"x{i}": (x >> i) & 1 for i in range(n)}
            if int(kernel.evaluate(art, inp)) != ((f >> x) & 1):
                return False
    return True


def run_dim(n: int) -> dict:
    t_gen0 = time.perf_counter()
    tasks = generate_tasks(n, N_TARGETS)
    gen_sec = round(time.perf_counter() - t_gen0, 3)
    print(f"[n={n}] generated {len(tasks)} tasks (seed={SEEDS[n]}, seen={SEEN[n]}) in {gen_sec}s", flush=True)

    rows = []
    t_run0 = time.perf_counter()
    for idx, (f, care) in enumerate(tasks):
        res = netsolve.compile_partial(f, n, care, W=4, max_width=4, time_limit=60.0, workers=4)
        verified = False
        if res["status"] == "sat" and res["artifact"] is not None:
            verified = verify_care(res["artifact"], f, n, care)
        row = {
            "idx": idx,
            "status": res["status"],
            "verified": verified,
            "cost": res["cost"],
            "lower_bound": res["lower_bound"],
            "certified_minimal": bool(res["certified_minimal"] and verified),
            "cert_kind": res["cert_kind"],
            "seconds": res["seconds"],
        }
        rows.append(row)
        if (idx + 1) % 10 == 0:
            sat_ok = sum(1 for r in rows if r["verified"])
            cert_ok = sum(1 for r in rows if r["certified_minimal"])
            print(f"[n={n}] {idx + 1}/{len(tasks)}: verified={sat_ok}, certified_minimal={cert_ok}, last={row['seconds']}s", flush=True)

    wall_sec = round(time.perf_counter() - t_run0, 3)
    secs = [r["seconds"] for r in rows]
    within_60 = [r for r in rows if r["seconds"] <= 60.0]
    costs: dict[str, int] = {}
    for r in rows:
        k = str(r["cost"])
        costs[k] = costs.get(k, 0) + 1

    return {
        "n": n,
        "seed": SEEDS[n],
        "seen": SEEN[n],
        "total": len(rows),
        "gen_seconds": gen_sec,
        "wall_seconds": wall_sec,
        "sat_count": sum(1 for r in rows if r["status"] == "sat"),
        "verified_count": sum(1 for r in rows if r["verified"]),
        "verified_within_60s": sum(1 for r in within_60 if r["verified"]),
        "certified_minimal_count": sum(1 for r in rows if r["certified_minimal"]),
        "certified_minimal_within_60s": sum(1 for r in within_60 if r["certified_minimal"]),
        "cost_histogram": costs,
        "median_seconds": round(statistics.median(secs), 4),
        "mean_seconds": round(statistics.mean(secs), 4),
        "max_seconds": round(max(secs), 4),
        "tasks": rows,
    }


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    results = {"dims": {}}
    for n in (8, 10):
        summary = run_dim(n)
        results["dims"][str(n)] = summary
        OUT.write_text(json.dumps(results, indent=2) + "\n")
    print(f"Saved G3 benchmark results to {OUT}", flush=True)


if __name__ == "__main__":
    main()
