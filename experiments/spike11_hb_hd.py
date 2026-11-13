"""Spike 11: Testing H-B (volume law for mechanisms) and H-D (coarser, not folded).

  python -m experiments.spike11_hb_hd

H-B (Volume law for mechanisms):
  Among minimal determining isomers of the SAME function f, does AdamW land on
  each isomer with frequency correlated with its weight-space volume?
  Measured on:
    (1) n=3 exact integer weight grid (geometry.phenotype_grid, W=1, h=2) vs AdamW
    (2) n=4 Gaussian initialization volume (100k samples, H=8) vs AdamW (200 seeds)

H-D (Cammarata's "coarser, not folded" width claim):
  As hidden width H varies across {1, 2, 3, 4, 6, 8, 12, 16} on 4-input elements
  with minimal width w*(f) in {2, 3}, classify each non-constant hidden unit u:
    - clean:      u (up to complement) belongs to a minimal determining set Omega* of f
    - coarsening: u is not clean, but some Omega* determines u (u is a union of cells)
    - folded:     u splits at least one cell of every known Omega*
"""

from __future__ import annotations

import itertools
import json
import pathlib
import time

import numpy as np

from cerp import atlas, geometry as geom, learnrules as lr, train as tr

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "experiments" / "results" / "spike11_hb_hd.json"


def _spearman(x, y):
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if len(x) < 2 or np.std(x) == 0 or np.std(y) == 0:
        return None
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    rx -= rx.mean()
    ry -= ry.mean()
    denom = np.sqrt((rx * rx).sum() * (ry * ry).sum())
    return float((rx * ry).sum() / denom) if denom > 0 else None


def _pearson(x, y):
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if len(x) < 2 or np.std(x) == 0 or np.std(y) == 0:
        return None
    xc, yc = x - x.mean(), y - y.mean()
    denom = np.sqrt((xc * xc).sum() * (yc * yc).sum())
    return float((xc * yc).sum() / denom) if denom > 0 else None


def _determines_n(units, g, n_bits):
    seen = {}
    for x in range(n_bits):
        cell = tuple((int(u) >> x) & 1 for u in units)
        v = (int(g) >> x) & 1
        if seen.setdefault(cell, v) != v:
            return False
    return True


def _effective_width_n(units, g, n_bits):
    full = (1 << n_bits) - 1
    uniq = sorted({min(int(u), full ^ int(u)) for u in units} - {0})
    if g in (0, full):
        return 0, ()
    for k in range(1, len(uniq) + 1):
        for s in itertools.combinations(uniq, k):
            if _determines_n(s, g, n_bits):
                return k, s
    return None, None


def run_hb_n3(seeds=200):
    """Exact grid volume (W=1, h=2) vs AdamW isomer frequencies for n=3, w*=2."""
    tb3 = atlas.build_all(3)[3]
    # Elements with hi == 3 (2 hidden neurons + 1 output = 3)
    exs = [int(tb3.exhibit[c]) for c in tb3.classes() if int(tb3.hi[tb3.exhibit[c]]) == 3]
    ph = geom.phenotype_grid(3, 2, 1)  # shape (3,)*11 = 177,147
    # Also compute exact hidden-unit pairs on the grid for each f
    vals = np.arange(-1, 2)
    X3 = np.array([[(i >> j) & 1 for j in range(3)] for i in range(8)])
    params = np.array(list(itertools.product(vals, repeat=4)))  # (81, 4)
    act = ((params[:, :3] @ X3.T + params[:, 3:]) >= 0).astype(np.int64)
    ubits = (act * (1 << np.arange(8))).sum(1)  # (81,)
    ucanon = np.minimum(ubits, 255 ^ ubits)
    # ph has shape (81, 81, 27) when reshaped
    ph_flat = ph.reshape(81, 81, 27)

    XS3 = lr.inputs(3)
    rows = []
    all_grid, all_train = [], []
    for f in exs:
        mask = (ph_flat == f)
        grid_iso = {}
        idxs = np.argwhere(mask)
        for i1, i2, _ in idxs:
            u1, u2 = int(ucanon[i1]), int(ucanon[i2])
            if u1 == 0 or u2 == 0 or u1 == u2:
                continue
            key = (min(u1, u2), max(u1, u2))
            grid_iso[key] = grid_iso.get(key, 0) + 1
        # Train AdamW with H=4
        rng = np.random.default_rng(1000 + f)
        p = lr.init(seeds, 4, 3, rng, scale=0.5)
        T = np.array([[(f >> x) & 1 for x in range(8)]] * seeds, dtype=float)
        C = np.ones_like(T)
        p, _ = lr.train(p, XS3, T, C, steps=300, rule="backprop", lr=0.05)
        pre, _, z = lr.forward(p, XS3)
        g = lr.bits(z >= 0)
        units = lr.bits(np.transpose(pre >= 0, (0, 2, 1)))
        train_iso = {}
        n_fit = 0
        for b in range(seeds):
            if int(g[b]) != f:
                continue
            n_fit += 1
            w, iso = _effective_width_n(units[b], f, 8)
            if w == 2:
                train_iso[iso] = train_iso.get(iso, 0) + 1
        union = sorted(set(grid_iso) | set(train_iso))
        if len(union) >= 2 and sum(grid_iso.values()) > 0 and sum(train_iso.values()) > 0:
            gv = [grid_iso.get(k, 0) for k in union]
            tv = [train_iso.get(k, 0) for k in union]
            # Normalize per function for pooled comparison
            gsum, tsum = sum(gv), sum(tv)
            all_grid.extend([v / gsum for v in gv])
            all_train.extend([v / tsum for v in tv])
            rows.append({
                "f": f,
                "n_fit": n_fit,
                "n_isomers_seen": len(union),
                "spearman": _spearman(gv, tv),
                "pearson": _pearson(gv, tv),
                "top_grid": max(gv) / gsum,
                "top_train": max(tv) / tsum,
                "top_match": union[int(np.argmax(gv))] == union[int(np.argmax(tv))],
            })
    return {
        "n_elements": len(rows),
        "pooled_spearman": _spearman(all_grid, all_train),
        "pooled_pearson": _pearson(all_grid, all_train),
        "top_isomer_match_rate": sum(r["top_match"] for r in rows) / max(1, len(rows)),
        "per_element": rows,
    }


def run_hb_n4(n_samples=100_000, seeds=200):
    """Gaussian prior volume (H=8, scale=0.5) vs AdamW isomer frequencies for n=4, w*=2."""
    tb4 = atlas.build_all(4)[4]
    exs = [int(tb4.exhibit[c]) for c in tb4.classes() if int(tb4.hi[tb4.exhibit[c]]) == 3]
    exs = exs[:10]  # 10 representative w*=2 classes
    ex_set = set(exs)

    rng = np.random.default_rng(77)
    prior_iso = {f: {} for f in exs}
    for _ in range(0, n_samples, 10_000):
        p = tr.init(10_000, 8, rng, scale=0.5)
        g, faithful, units = tr.read_circuits(p)
        for b in np.nonzero(faithful)[0]:
            f = int(g[b])
            if f not in ex_set:
                continue
            w, iso = tr.effective_width(units[b], f)
            if w == 2:
                prior_iso[f][iso] = prior_iso[f].get(iso, 0) + 1

    rows = []
    all_prior, all_train = [], []
    for f in exs:
        p = tr.init(seeds, 8, np.random.default_rng(2000 + f), scale=0.5)
        T = np.array([[(f >> x) & 1 for x in range(16)]] * seeds, dtype=float)
        C = np.ones_like(T)
        p, _ = tr.train(p, T, C, steps=300, lr=0.05)
        g, faithful, units = tr.read_circuits(p)
        train_iso = {}
        n_fit = 0
        for b in range(seeds):
            if not (faithful[b] and int(g[b]) == f):
                continue
            n_fit += 1
            w, iso = tr.effective_width(units[b], f)
            if w == 2:
                train_iso[iso] = train_iso.get(iso, 0) + 1
        union = sorted(set(prior_iso[f]) | set(train_iso))
        if len(union) >= 2 and sum(prior_iso[f].values()) > 0 and sum(train_iso.values()) > 0:
            pv = [prior_iso[f].get(k, 0) for k in union]
            tv = [train_iso.get(k, 0) for k in union]
            psum, tsum = sum(pv), sum(tv)
            all_prior.extend([v / psum for v in pv])
            all_train.extend([v / tsum for v in tv])
            rows.append({
                "f": f,
                "n_prior_hits": psum,
                "n_fit": n_fit,
                "n_isomers": len(union),
                "spearman": _spearman(pv, tv),
                "pearson": _pearson(pv, tv),
                "top_match": union[int(np.argmax(pv))] == union[int(np.argmax(tv))],
            })
    return {
        "n_elements": len(rows),
        "pooled_spearman": _spearman(all_prior, all_train),
        "pooled_pearson": _pearson(all_prior, all_train),
        "top_isomer_match_rate": sum(r["top_match"] for r in rows) / max(1, len(rows)),
        "per_element": rows,
    }


def run_hd(widths=(1, 2, 3, 4, 6, 8, 12, 16), seeds=20):
    """Cammarata's 'coarser, not folded' test across widths H on 4-input elements."""
    tb4 = atlas.build_all(4)[4]
    w2_exs = [int(tb4.exhibit[c]) for c in tb4.classes() if int(tb4.hi[tb4.exhibit[c]]) == 3][:4]
    w3_exs = [int(tb4.exhibit[c]) for c in tb4.classes() if int(tb4.hi[tb4.exhibit[c]]) == 4][:6]
    targets = [(f, 2) for f in w2_exs] + [(f, 3) for f in w3_exs]

    # Precompute all LTFs up to complement for exact w*=2 minimal sets
    ltf_map, _ = atlas.ltfs(4)
    ltf_canon = sorted({min(b, 0xFFFF ^ b) for b in ltf_map} - {0})

    summary_by_rel = {}  # (H - w*) -> counts
    per_width = []

    for f, w_star in targets:
        # Collect minimal determining sets Omega* of size w_star:
        # For w_star == 2, exact over all LTF pairs; for w_star == 3, collect from atlas witness + H>=8 runs.
        omega_stars = []
        if w_star == 2:
            for u1, u2 in itertools.combinations(ltf_canon, 2):
                if _determines_n((u1, u2), f, 16):
                    omega_stars.append((u1, u2))
        else:
            # Atlas witness first-layer units
            wit = tb4.wit[f]
            if wit[0] != "seed":
                w_wit = tuple(sorted(min(u, 0xFFFF ^ u) for u in wit[1]))
                if len(w_wit) == w_star and _determines_n(w_wit, f, 16):
                    omega_stars.append(w_wit)

        # First pass at H in (8, 12, 16) to also harvest any additional minimal determining sets for w*=3
        trained_runs = {}
        XS4 = lr.inputs(4)
        for H in widths:
            p = lr.init(seeds, H, 4, np.random.default_rng(3000 + f * 31 + H), scale=0.5)
            T = np.array([[(f >> x) & 1 for x in range(16)]] * seeds, dtype=float)
            C = np.ones_like(T)
            p, _ = lr.train(p, XS4, T, C, steps=350, rule="backprop", lr=0.05)
            pre, _, z = lr.forward(p, XS4)
            g = lr.bits(z >= 0)
            units = lr.bits(np.transpose(pre >= 0, (0, 2, 1)))
            trained_runs[H] = (g, units)
            if w_star == 3 and H >= 8:
                for b in range(seeds):
                    if int(g[b]) == f:
                        we, iso = _effective_width_n(units[b], f, 16)
                        if we == w_star and iso not in omega_stars:
                            omega_stars.append(iso)

        clean_members = {u for om in omega_stars for u in om}

        for H in widths:
            g, units = trained_runs[H]
            counts = {"clean": 0, "coarsening": 0, "folded": 0, "constant": 0, "fit": 0}
            for b in range(seeds):
                if int(g[b]) == f:
                    counts["fit"] += 1
                for raw_u in units[b]:
                    u = min(int(raw_u), 0xFFFF ^ int(raw_u))
                    if u == 0:
                        counts["constant"] += 1
                    elif u in clean_members:
                        counts["clean"] += 1
                    elif any(_determines_n(om, u, 16) for om in omega_stars):
                        counts["coarsening"] += 1
                    else:
                        counts["folded"] += 1
            active = counts["clean"] + counts["coarsening"] + counts["folded"]
            rel = "below" if H < w_star else ("at" if H == w_star else "above")
            bucket = summary_by_rel.setdefault(rel, {"clean": 0, "coarsening": 0, "folded": 0, "constant": 0, "fit": 0, "total_nets": 0})
            for k in ("clean", "coarsening", "folded", "constant", "fit"):
                bucket[k] += counts[k]
            bucket["total_nets"] += seeds
            per_width.append({
                "f": f, "w_star": w_star, "H": H, "regime": rel,
                "fit_rate": round(counts["fit"] / seeds, 3),
                "clean_frac": round(counts["clean"] / max(1, active), 3),
                "coarsening_frac": round(counts["coarsening"] / max(1, active), 3),
                "folded_frac": round(counts["folded"] / max(1, active), 3),
            })

    regime_summary = {}
    for rel, b in summary_by_rel.items():
        act = b["clean"] + b["coarsening"] + b["folded"]
        regime_summary[rel] = {
            "fit_rate": round(b["fit"] / b["total_nets"], 3),
            "active_units": act,
            "clean_frac": round(b["clean"] / max(1, act), 3),
            "coarsening_frac": round(b["coarsening"] / max(1, act), 3),
            "folded_frac": round(b["folded"] / max(1, act), 3),
            "constant_frac": round(b["constant"] / max(1, act + b["constant"]), 3),
        }
    return {"regime_summary": regime_summary, "per_width": per_width}


def main():
    t0 = time.time()
    hb3 = run_hb_n3()
    hb4 = run_hb_n4()
    hd = run_hd()
    res = {"elapsed_s": round(time.time() - t0, 2), "hb_n3": hb3, "hb_n4": hb4, "hd": hd}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=2))
    print(json.dumps({"elapsed_s": res["elapsed_s"],
                      "hb_n3": {k: v for k, v in hb3.items() if k != "per_element"},
                      "hb_n4": {k: v for k, v in hb4.items() if k != "per_element"},
                      "hd_regimes": hd["regime_summary"]}, indent=2))


if __name__ == "__main__":
    main()
