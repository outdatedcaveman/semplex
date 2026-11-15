"""Fixed G8 benchmark (Gap B2): partial-care cost-4 compilation at n = 8.

Generates 100 random 3-hidden-unit step targets at n = 8 (seed 8820, hidden
weights in [-3, 3], hidden biases in [-6, 6], output weights in [-2, 2],
output bias in [-3, 3], 25%-75% ones) confirmed to have no 2-hidden-unit
network with |w| <= 4 on the full 256-row truth table. Each target is masked
to 192/256 (75%) care points using seed 8821 and compiled with
cerp.netsolve.compile_partial(f, 8, care, W=4, max_width=4, time_limit=60.0,
workers=4). Every solution is verified with cerp.kernel.evaluate on all care
points and every lower-bound certificate is checked with cerp.kernel_bounds.
"""

from __future__ import annotations

import json
import pathlib
import statistics
import time

import numpy as np

from cerp import bounds, kernel, kernel_bounds, netsolve

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "experiments" / "results" / "g8_cost4_benchmark.json"

N_VARS = 8
TARGET_SEED = 8820
CARE_SEED = 8821
SEEN = 192
N_TARGETS = 100
W_BOUND = 4
TIME_LIMIT = 60.0
WORKERS = 4


def pts(n: int) -> np.ndarray:
    return np.array([[(x >> i) & 1 for i in range(n)] for x in range(1 << n)])


def bits(y) -> int:
    return sum(int(v) << x for x, v in enumerate(y))


def generate_tasks(count: int = N_TARGETS) -> tuple[list[tuple[int, int]], dict]:
    P = pts(N_VARS)
    K = 1 << N_VARS
    full_mask = (1 << K) - 1
    rng = np.random.default_rng(TARGET_SEED)
    spec0 = netsolve.layered(N_VARS, [])
    spec2 = netsolve.layered(N_VARS, [2])

    targets: list[int] = []
    seen_f: set[int] = set()
    attempts = 0
    rejected_balance = 0
    rejected_dup = 0
    rejected_cost1_or_w1 = 0
    rejected_width2_w4 = 0
    rejected_width2_unknown = 0

    while len(targets) < count:
        attempts += 1
        W_h = rng.integers(-3, 4, (3, N_VARS))
        b_h = rng.integers(-6, 7, 3)
        h = (P @ W_h.T + b_h >= 0).astype(int)
        o = rng.integers(-2, 3, 3)
        c = int(rng.integers(-3, 4))
        y = (h @ o + c >= 0)
        ones = int(y.sum())
        if not (0.25 * K <= ones <= 0.75 * K):
            rejected_balance += 1
            continue
        f = bits(y)
        if f in seen_f:
            rejected_dup += 1
            continue

        # Fast exact pre-rejectors (every W<=4 0-hidden or W<=1 width-2 solution implies W=4 width-2 SAT)
        st0, _ = netsolve.solve(f, N_VARS, spec0, W=W_BOUND, time_limit=5.0, workers=WORKERS)
        if st0 == "sat":
            rejected_cost1_or_w1 += 1
            continue
        st1, _ = netsolve.solve(f, N_VARS, spec2, W=1, time_limit=5.0, workers=WORKERS)
        if st1 == "sat":
            rejected_cost1_or_w1 += 1
            continue

        st2, _ = netsolve.solve(f, N_VARS, spec2, W=W_BOUND, time_limit=30.0, workers=WORKERS)
        if st2 == "unsat":
            targets.append(f)
            seen_f.add(f)
            if len(targets) % 20 == 0:
                print(f"[gen] {len(targets)}/{count} targets found (attempts={attempts})", flush=True)
        elif st2 == "sat":
            rejected_width2_w4 += 1
        else:
            rejected_width2_unknown += 1

    rng_care = np.random.default_rng(CARE_SEED)
    tasks: list[tuple[int, int]] = []
    for f in targets:
        care = bits(np.isin(np.arange(K), rng_care.choice(K, SEEN, replace=False)))
        tasks.append((f, care))

    gen_stats = {
        "attempts": attempts,
        "rejected_balance": rejected_balance,
        "rejected_dup": rejected_dup,
        "rejected_cost1_or_w1": rejected_cost1_or_w1,
        "rejected_width2_w4": rejected_width2_w4,
        "rejected_width2_unknown": rejected_width2_unknown,
        "full_table_care_bits": full_mask.bit_count(),
    }
    return tasks, gen_stats


def verify_care(art: dict, f: int, n: int, care: int) -> bool:
    K = 1 << n
    for x in range(K):
        if (care >> x) & 1:
            inp = {f"x{i}": (x >> i) & 1 for i in range(n)}
            if int(kernel.evaluate(art, inp)) != ((f >> x) & 1):
                return False
    return True


def verify_certs(res: dict, f: int, n: int, care: int) -> bool:
    fc = f & care
    full_mask = (1 << (1 << n)) - 1
    f_neg = (~fc) & care & full_mask
    certs = res.get("certs", {})
    lb = res.get("lower_bound", 1)
    if lb >= 4:
        c_pos = certs.get("not_two_halfspaces_pos")
        c_neg = certs.get("not_two_halfspaces_neg")
        if c_pos is None or c_neg is None:
            return False
        return bool(
            kernel_bounds.check_not_two_halfspaces_partial(n, fc, care, c_pos).ok
            and kernel_bounds.check_not_two_halfspaces_partial(n, f_neg, care, c_neg).ok
        )
    if lb >= 3:
        c1 = certs.get("not_threshold")
        if c1 is None:
            return False
        return bool(kernel_bounds.check_not_threshold_partial(n, fc, care, c1["pos"], c1["neg"]).ok)
    return True


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    t_gen0 = time.perf_counter()
    tasks, gen_stats = generate_tasks(N_TARGETS)
    gen_sec = round(time.perf_counter() - t_gen0, 3)
    print(f"[G8] generated {len(tasks)} targets in {gen_sec}s: {gen_stats}", flush=True)

    rows = []
    t_run0 = time.perf_counter()
    for idx, (f, care) in enumerate(tasks):
        res = netsolve.compile_partial(
            f, N_VARS, care, W=W_BOUND, max_width=4, time_limit=TIME_LIMIT, workers=WORKERS
        )
        verified = False
        if res["status"] == "sat" and res["artifact"] is not None:
            verified = verify_care(res["artifact"], f, N_VARS, care)
        kb_ok = verify_certs(res, f, N_VARS, care)
        certified_min = bool(verified and res["certified_minimal"] and kb_ok)
        row = {
            "idx": idx,
            "f_hex": hex(f),
            "care_hex": hex(care),
            "status": res["status"],
            "verified": verified,
            "cost": res["cost"],
            "lower_bound": res["lower_bound"],
            "certified_minimal": certified_min,
            "cert_kind": res["cert_kind"],
            "kernel_bounds_ok": kb_ok,
            "cost3_status": res.get("cost3_status"),
            "cost3_solver_unsat": bool(res.get("cost3_solver_unsat")),
            "seconds": res["seconds"],
        }
        rows.append(row)
        if (idx + 1) % 10 == 0:
            sat_ok = sum(1 for r in rows if r["verified"])
            c4_ok = sum(1 for r in rows if r["cost"] == 4 and r["certified_minimal"])
            col3 = sum(1 for r in rows if r["cost"] == 3 and r["verified"])
            print(
                f"[G8] {idx + 1}/{len(tasks)}: verified={sat_ok}, cert_cost4={c4_ok}, "
                f"collapsed_cost3={col3}, last={row['seconds']}s",
                flush=True,
            )

    wall_sec = round(time.perf_counter() - t_run0, 3)
    secs = [r["seconds"] for r in rows]
    within_60 = [r for r in rows if r["seconds"] <= TIME_LIMIT]

    collapsed_cost1 = sum(1 for r in rows if r["verified"] and r["cost"] == 1)
    collapsed_cost3 = sum(1 for r in rows if r["verified"] and r["cost"] == 3)
    collapsed_total = collapsed_cost1 + collapsed_cost3
    non_collapsed = len(rows) - collapsed_total

    cert_cost4 = sum(1 for r in rows if r["verified"] and r["cost"] == 4 and r["certified_minimal"])
    cert_cost4_within_60 = sum(
        1 for r in within_60 if r["verified"] and r["cost"] == 4 and r["certified_minimal"]
    )
    uncert_cost4 = sum(1 for r in rows if r["verified"] and r["cost"] == 4 and not r["certified_minimal"])
    solver_unsat_no_cert = sum(1 for r in rows if r["cost3_solver_unsat"])

    costs: dict[str, int] = {}
    for r in rows:
        k = str(r["cost"])
        costs[k] = costs.get(k, 0) + 1

    summary = {
        "n": N_VARS,
        "target_seed": TARGET_SEED,
        "care_seed": CARE_SEED,
        "seen": SEEN,
        "W": W_BOUND,
        "time_limit": TIME_LIMIT,
        "workers": WORKERS,
        "total": len(rows),
        "gen_seconds": gen_sec,
        "gen_stats": gen_stats,
        "wall_seconds": wall_sec,
        "sat_count": sum(1 for r in rows if r["status"] == "sat"),
        "verified_count": sum(1 for r in rows if r["verified"]),
        "verified_within_60s": sum(1 for r in within_60 if r["verified"]),
        "collapsed_to_cost1_on_care": collapsed_cost1,
        "collapsed_to_cost3_on_care": collapsed_cost3,
        "collapsed_to_le_cost3_total": collapsed_total,
        "remaining_cost4_targets": non_collapsed,
        "certified_cost4_count": cert_cost4,
        "certified_cost4_within_60s": cert_cost4_within_60,
        "certified_cost4_rate_of_noncollapsed": round(cert_cost4_within_60 / max(1, non_collapsed), 4),
        "certified_cost4_rate_of_all": round(cert_cost4_within_60 / len(rows), 4),
        "uncertified_cost4_count": uncert_cost4,
        "solver_unsat_without_cert_count": solver_unsat_no_cert,
        "solver_unsat_without_cert_fraction_of_all": round(solver_unsat_no_cert / len(rows), 4),
        "solver_unsat_without_cert_fraction_of_noncollapsed": round(
            solver_unsat_no_cert / max(1, non_collapsed), 4
        ),
        "certified_minimal_count": sum(1 for r in rows if r["certified_minimal"]),
        "certified_minimal_within_60s": sum(1 for r in within_60 if r["certified_minimal"]),
        "cost_histogram": costs,
        "median_seconds": round(statistics.median(secs), 4),
        "mean_seconds": round(statistics.mean(secs), 4),
        "max_seconds": round(max(secs), 4),
        "tasks": rows,
    }
    OUT.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "tasks"}, indent=2), flush=True)


if __name__ == "__main__":
    main()
