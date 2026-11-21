"""G15: Extend n = 5 exact LTF circuit & G_f-orbit census to 100% cost <= 3 (|w| <= 4) and cost = 4 (|w| <= 3).

Produces `experiments/results/g15_orbits.json` with:
1. Complete n = 5, cost <= 3, |w| <= 4 enumeration (54 cost-1 + 11,487 cost-3 = 11,541 NPN classes).
2. Comparison against |w| <= 3 cost <= 3 (42 cost-1 + 7,253 cost-3 = 7,295 NPN classes) showing how many
   W = 3 cost-4 functions drop to cost <= 3 when |w| = 4 is permitted.
3. Exact n = 5, cost = 4, |w| <= 3 census across:
   - Slice 1 (exhaustive): ALL 64 symmetric 5-variable Boolean functions reduced mod NPN.
   - Slice 2 (time-bounded deterministic catalog): general cost = 4 (W = 3) NPN classes
     ordered balanced-Hamming-weight first (-min(w, 32-w), rep), cross-checked against
     W = 4 cost <= 3 collapse and cost = 3 non-existence.
"""

from __future__ import annotations

import json
import pathlib
import sys
import time
from collections import Counter

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cerp import atlas, orbits
from experiments.g9_orbits import summarize_rows

OUT = ROOT / "experiments" / "results" / "g15_orbits.json"

WORKERS = 2
W4_COST3_TIME_LIMIT = 900.0   # 15 min cap for 100% cost<=3 W=4
W3_COST4_TIME_LIMIT = 900.0   # 15 min cap for symmetric + general cost=4 W=3
MAX_GENERAL_DISCOVER = 1500


def _compact_orbit_rows(rows: list[dict]) -> list[dict]:
    """Compress large orbit_sizes lists (>64 entries) into exact histograms for JSON size hygiene."""
    compacted: list[dict] = []
    for r in rows:
        rc = dict(r)
        for fld, hist_fld in (("orbit_sizes", "orbit_size_hist"), ("oriented_orbit_sizes", "oriented_orbit_size_hist")):
            vals = rc.get(fld, [])
            if len(vals) > 64:
                rc[hist_fld] = {str(k): v for k, v in sorted(Counter(vals).items())}
                rc[f"{fld}_min"] = vals[0]
                rc[f"{fld}_max"] = vals[-1]
                del rc[fld]
        compacted.append(rc)
    return compacted


def _symmetric_signature_map() -> dict[int, list[str]]:
    """Map canonical NPN rep of every symmetric n=5 function -> Hamming-weight indicator strings."""
    T5 = atlas.transforms(5)
    idx5 = np.array([idx for _, _, idx in T5], dtype=np.int64)
    bit_pos = np.arange(32, dtype=np.uint32)
    hw = [x.bit_count() for x in range(32)]
    by_rep: dict[int, list[str]] = {}
    for mask in range(64):
        f = 0
        for x in range(32):
            if (mask >> hw[x]) & 1:
                f |= 1 << x
        bmat = ((np.uint32(f) >> bit_pos) & np.uint32(1)).astype(np.uint8)
        pk = np.packbits(bmat[idx5], axis=1, bitorder="little").view(np.uint32).ravel()
        rep = int(min(pk.min(), (np.uint32(0xFFFFFFFF) ^ pk).min()))
        sig = "".join(str((mask >> w) & 1) for w in range(6))
        by_rep.setdefault(rep, []).append(sig)
    return by_rep


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    t_all = time.perf_counter()

    print("[G15 Step 1] Discovering W = 3 cost <= 3 reference sets...", flush=True)
    _, L3_keys, _, _, c1_w3, c3_w3 = orbits._discover_n5_cost_le3_data(W=3)
    cost_le3_W3_set = set(c1_w3) | set(c3_w3)
    print(f"[G15 Step 1] W = 3 LTFs={len(L3_keys)}, cost1={len(c1_w3)}, cost3={len(c3_w3)}", flush=True)

    print(f"[G15 Step 2] Running 100% parallel W = 4 cost <= 3 enumeration ({WORKERS} workers)...", flush=True)
    w4_res = orbits.enumerate_n5_cost_le3_parallel(W=4, workers=WORKERS, time_limit=W4_COST3_TIME_LIMIT)
    w4_rows = w4_res.pop("classes")
    c1_w4 = set(w4_res.pop("cost1_reps"))
    c3_w4 = set(w4_res.pop("cost3_reps"))
    cost_le3_W4_set = c1_w4 | c3_w4
    w4_summary = summarize_rows(_compact_orbit_rows(w4_rows), extra=w4_res)
    print(
        f"[G15 Step 2] Done W=4 cost<=3: {w4_summary['total_classes']} classes "
        f"({w4_summary['one_orbit_unoriented_count']}/{w4_summary['total_classes']} 1-orbit unoriented, "
        f"{w4_summary['one_orbit_oriented_count']}/{w4_summary['total_classes']} 1-orbit oriented) "
        f"reason={w4_summary['stopped_reason']} in {w4_summary['total_seconds']}s",
        flush=True,
    )

    print(f"[G15 Step 3] Running W = 3 cost = 4 enumeration ({WORKERS} workers, cap={W3_COST4_TIME_LIMIT}s)...", flush=True)
    c4_res = orbits.enumerate_n5_cost4(
        W=3,
        cost_le3_W3_set=cost_le3_W3_set,
        cost_le3_W4_set=cost_le3_W4_set,
        workers=WORKERS,
        time_limit=W3_COST4_TIME_LIMIT,
        max_general_discover=MAX_GENERAL_DISCOVER,
    )
    sym_rows = c4_res.pop("symmetric_classes")
    gen_rows = c4_res.pop("general_classes")

    # Classify all symmetric NPN classes across cost 1, cost 3, cost 4, cost >= 5 (at W=3 and W=4)
    sym_sigs = _symmetric_signature_map()
    sym_all_reps = sorted(sym_sigs)
    sym_cost4_set = {r["rep"] for r in sym_rows}
    sym_classification: list[dict] = []
    for rep in sym_all_reps:
        in_w3_1 = rep in c1_w3
        in_w3_3 = rep in c3_w3
        in_w4_1 = rep in c1_w4
        in_w4_3 = rep in c3_w4
        w3_label = "cost1" if in_w3_1 else ("cost3" if in_w3_3 else ("cost4" if rep in sym_cost4_set else "cost_ge_5"))
        w4_le3 = "cost1" if in_w4_1 else ("cost3" if in_w4_3 else "cost_ge_4")
        sym_classification.append({
            "rep": rep,
            "rep_hex": hex(rep),
            "hamming_signatures": sym_sigs[rep],
            "w3_classification": w3_label,
            "w4_le3_classification": w4_le3,
        })
    for r in sym_rows:
        r["hamming_signatures"] = sym_sigs.get(r["rep"], [])

    sym_summary = summarize_rows(
        _compact_orbit_rows(sym_rows),
        extra={
            "slice": "exhaustive_symmetric",
            "symmetric_total_npn_classes": len(sym_all_reps),
            "symmetric_cost_ge5_reps": c4_res["symmetric_cost_ge5_reps"],
            "symmetric_drops_to_cost3_at_W4": sum(1 for r in sym_rows if r.get("drops_to_cost3_at_W4")),
            "symmetric_all_classification": sym_classification,
        },
    )

    true_c4_rows = [r for r in gen_rows if not r.get("drops_to_cost3_at_W4", False)]
    drop_c3_rows = [r for r in gen_rows if r.get("drops_to_cost3_at_W4", False)]
    gen_summary = summarize_rows(
        _compact_orbit_rows(gen_rows),
        extra={
            "slice": "deterministic_general_w3",
            "general_classes_discovered": c4_res["general_classes_discovered"],
            "general_classes_completed": c4_res["general_classes_completed"],
            "stopped_at_rep": c4_res["stopped_at_rep"],
            "stopped_reason": c4_res["stopped_reason"],
            "discovery_seconds": c4_res["discovery_seconds"],
            "total_seconds": c4_res["total_seconds"],
            "drops_to_cost3_at_W4_count": len(drop_c3_rows),
            "drops_to_cost3_at_W4_fraction": round(len(drop_c3_rows) / max(1, len(gen_rows)), 6),
            "true_cost4_against_W4_count": len(true_c4_rows),
            "true_cost4_one_orbit_unoriented_count": sum(1 for r in true_c4_rows if r["num_orbits"] == 1),
            "true_cost4_one_orbit_oriented_count": sum(1 for r in true_c4_rows if r["oriented_num_orbits"] == 1),
        },
    )

    payload = {
        "n": 5,
        "w3_reference": {
            "ltf_count": len(L3_keys),
            "cost1_classes": len(c1_w3),
            "cost3_classes": len(c3_w3),
            "total_cost_le3": len(cost_le3_W3_set),
        },
        "n5_cost_le3_W4": w4_summary,
        "n5_cost4_W3_symmetric": sym_summary,
        "n5_cost4_W3_general": gen_summary,
        "total_wall_seconds": round(time.perf_counter() - t_all, 3),
    }

    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"[G15 DONE] Wrote {OUT} in {payload['total_wall_seconds']}s", flush=True)


if __name__ == "__main__":
    main()
