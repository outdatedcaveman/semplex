"""Tabulate minimum-cost layered threshold circuits and G_f-orbits for n <= 4 and n = 5 (cost <= 3).

Produces `experiments/results/g9_orbits.json` with per-class fields:
- rep, rep_hex, cost
- num_circuits, num_orbits, orbit_sizes (unoriented hyperplane-pair equivalence)
- oriented_num_circuits, oriented_num_orbits, oriented_orbit_sizes (literal Boolean-function equivalence)
- gf_order (|G_f| including output negation where it applies), gf_np_order

Plus exact summaries per dimension and timing/stopping point for n = 5 (cost <= 3).
"""

from __future__ import annotations

import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cerp import atlas, orbits

OUT = ROOT / "experiments" / "results" / "g9_orbits.json"
N5_TIME_LIMIT = 5400.0  # 1.5 hours (< 2 hours limit)


def summarize_rows(rows: list[dict], *, extra: dict | None = None) -> dict:
    total = len(rows)
    by_cost: dict[str, dict] = {}
    for r in rows:
        ck = str(r["cost"])
        entry = by_cost.setdefault(ck, {
            "classes": 0,
            "one_orbit_unoriented": 0,
            "one_orbit_oriented": 0,
            "total_circuits_unoriented": 0,
            "total_orbits_unoriented": 0,
            "total_circuits_oriented": 0,
            "total_orbits_oriented": 0,
        })
        entry["classes"] += 1
        entry["total_circuits_unoriented"] += r["num_circuits"]
        entry["total_orbits_unoriented"] += r["num_orbits"]
        entry["total_circuits_oriented"] += r["oriented_num_circuits"]
        entry["total_orbits_oriented"] += r["oriented_num_orbits"]
        if r["num_orbits"] == 1:
            entry["one_orbit_unoriented"] += 1
        if r["oriented_num_orbits"] == 1:
            entry["one_orbit_oriented"] += 1

    one_u = sum(1 for r in rows if r["num_orbits"] == 1)
    one_o = sum(1 for r in rows if r["oriented_num_orbits"] == 1)
    non_c1 = [r for r in rows if r["cost"] > 1]
    one_u_non1 = sum(1 for r in non_c1 if r["num_orbits"] == 1)
    one_o_non1 = sum(1 for r in non_c1 if r["oriented_num_orbits"] == 1)

    res = {
        "total_classes": total,
        "one_orbit_unoriented_count": one_u,
        "one_orbit_unoriented_fraction": round(one_u / max(1, total), 6),
        "one_orbit_oriented_count": one_o,
        "one_orbit_oriented_fraction": round(one_o / max(1, total), 6),
        "non_cost1_classes": len(non_c1),
        "non_cost1_one_orbit_unoriented_count": one_u_non1,
        "non_cost1_one_orbit_unoriented_fraction": round(one_u_non1 / max(1, len(non_c1)), 6),
        "non_cost1_one_orbit_oriented_count": one_o_non1,
        "non_cost1_one_orbit_oriented_fraction": round(one_o_non1 / max(1, len(non_c1)), 6),
        "by_cost": by_cost,
        "classes": rows,
    }
    if extra:
        res.update(extra)
    return res


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    t_all = time.perf_counter()
    tables = atlas.build_all(4)
    dims: dict[str, dict] = {}

    for m in (1, 2, 3, 4):
        t0 = time.perf_counter()
        rows = orbits.enumerate_dimension(m, tb=tables[m])
        sec = round(time.perf_counter() - t0, 3)
        dims[str(m)] = summarize_rows(rows, extra={"n": m, "W": 3, "seconds": sec})
        s = dims[str(m)]
        print(
            f"[G9 n={m}] classes={s['total_classes']} 1-orbit(unorient)={s['one_orbit_unoriented_count']}/{s['total_classes']} "
            f"({s['one_orbit_unoriented_fraction']}), 1-orbit(orient)={s['one_orbit_oriented_count']}/{s['total_classes']} "
            f"in {sec}s",
            flush=True,
        )

    print("[G9 n=5 cost<=3] starting exact |w|<=3 enumeration...", flush=True)
    n5_res = orbits.enumerate_n5_cost_le3(W=3, time_limit=N5_TIME_LIMIT)
    n5_rows = n5_res.pop("classes")
    dims["5_cost_le_3"] = summarize_rows(n5_rows, extra=n5_res)
    s5 = dims["5_cost_le_3"]
    print(
        f"[G9 n=5 cost<=3] completed={s5['cost3_classes_completed']}/{s5['cost3_classes_total']} cost=3 + "
        f"{s5['cost1_classes']} cost=1 classes ({s5['stopped_reason']}), "
        f"1-orbit(unorient)={s5['one_orbit_unoriented_count']}/{s5['total_classes']} "
        f"in {s5['total_seconds']}s",
        flush=True,
    )

    # Combined n <= 4 aggregate
    rows_le4 = [r for m in (1, 2, 3, 4) for r in dims[str(m)]["classes"]]
    summary_le4 = summarize_rows(rows_le4)
    summary_le4.pop("classes")

    payload = {
        "W": 3,
        "wall_seconds": round(time.perf_counter() - t_all, 3),
        "aggregate_n_le_4": summary_le4,
        "dims": dims,
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"Saved G9 orbit counts to {OUT}", flush=True)


if __name__ == "__main__":
    main()
