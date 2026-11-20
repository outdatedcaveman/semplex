"""Spike 52 (pre-registered in SPIKE_52_REPORT.md): canonical form of a moral concept (Moral Machine pilot).

  python -m experiments.spike52 build      # stream the data, aggregate verdicts per feature pattern
  python -m experiments.spike52 analyse
"""

from __future__ import annotations

import io
import json
import os
import pathlib
import sys
import tarfile
import zipfile

import numpy as np

from cerp import kernel, netsolve

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "experiments" / "results" / "spike52_raw"
OUT = ROOT / "experiments" / "results" / "spike52.json"
DATA = pathlib.Path(os.environ.get("MM_DATA", "/tmp/claude-0/-home-user/c1370310-95be-56d2-b761-b9e47fdba1e8/scratchpad/justice_data"))
n, K = 8, 256
COLS = ["ResponseID", "Intervention", "Barrier", "CrossingSignal", "AttributeLevel", "ScenarioType", "NumberOfCharacters", "Saved", "UserCountry3"]
FEATURES = ["lawful", "unlawful", "passengers", "more", "fewer", "younger", "older", "pets"]
MIN_COUNT = 30


def clusters():
    z = zipfile.ZipFile(DATA / "cluster.zip"); txt = z.read("country_cluster_map.csv").decode()
    out = {}
    for line in txt.splitlines()[1:]:
        parts = line.split(",")
        if len(parts) >= 3 and parts[-1].strip() != "":
            out[parts[0]] = int(parts[-1])
    return out


def build():
    """The file is ordered by Intervention, so the two outcomes of a dilemma are far apart: load the
    needed columns whole and join the stay side to the swerve side on ResponseID."""
    import pandas as pd
    cl = clusters(); agg = {}
    tf = tarfile.open(DATA / "survey.csv.tar.gz", "r:gz"); fh = tf.extractfile(tf.next())
    d = pd.read_csv(fh, usecols=COLS, dtype={"ResponseID": str, "AttributeLevel": "category", "ScenarioType": "category", "UserCountry3": "category"})
    rows = len(d)
    d = d.dropna(subset=["Intervention", "Barrier", "CrossingSignal", "NumberOfCharacters", "Saved"])
    d = d[d.groupby("ResponseID")["Intervention"].transform("size") == 2]
    S = d[d["Intervention"] == 0].drop_duplicates("ResponseID").set_index("ResponseID")
    O = d[d["Intervention"] == 1].drop_duplicates("ResponseID").set_index("ResponseID")[["NumberOfCharacters"]]
    S = S.join(O, rsuffix="_other", how="inner"); del d, O
    st = S["ScenarioType"].astype(str); al = S["AttributeLevel"].astype(str)
    bits = np.stack([(S["CrossingSignal"] == 1).values, (S["CrossingSignal"] == 2).values, (S["Barrier"] == 1).values,
                     (S["NumberOfCharacters"].values > S["NumberOfCharacters_other"].values),
                     (S["NumberOfCharacters"].values < S["NumberOfCharacters_other"].values),
                     ((st == "Age") & (al == "Young")).values, ((st == "Age") & (al == "Old")).values,
                     ((st == "Species") & (al == "Pets")).values], 1).astype(int)
    pat = bits @ (1 << np.arange(n)); saved = S["Saved"].values.astype(int)
    cc = np.array([cl.get(str(c), -1) for c in S["UserCountry3"].astype(str)])
    for key, mask in (("all", np.ones(len(pat), bool)), ("0", cc == 0), ("1", cc == 1), ("2", cc == 2)):
        agg[key] = [np.bincount(pat[mask], minlength=K).tolist(), np.bincount(pat[mask], weights=saved[mask], minlength=K).tolist()]
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "cells.json").write_text(json.dumps({"features": FEATURES, "rows": int(rows), "pairs": int(len(S)), "agg": agg}))
    print("built", len(S), "dilemmas from", rows, "rows", flush=True)


def verdicts(key):
    d = json.loads((RAW / "cells.json").read_text())["agg"][key]; cnt = np.array(d[0]); sv = np.array(d[1])
    obs = (cnt >= MIN_COUNT) & (2 * sv != cnt)
    f = sum(1 << x for x in range(K) if obs[x] and 2 * sv[x] > cnt[x]); care = sum(1 << x for x in range(K) if obs[x])
    return f, care, cnt, sv


def ev(a):
    return np.array([kernel.evaluate(a, {f"x{i}": (x >> i) & 1 for i in range(n)}) for x in range(K)], dtype=bool)


def forced_values(f, care, targets):
    """Values at `targets` forced by every minimum-cost circuit consistent with (f, care); -1 if not forced."""
    r = netsolve.compile_partial(f, n, care, W=4, time_limit=60)
    if r["status"] != "sat":
        return None, None, None
    fc = f & care; spec = netsolve.layered(n, [] if r["cost"] == 1 else [r["cost"] - 1])
    samples = []
    for s in range(10):
        st, a = netsolve.solve(fc, n, spec, W=4, care=care, time_limit=3, rand_obj=s, workers=2)
        samples.append(ev(a if a is not None else r["artifact"]))
    S = np.array(samples); out = {}
    for x in targets:
        col = S[:, x]
        if col.min() != col.max():
            out[x] = -1; continue
        v = bool(col[0]); f2 = (fc | (1 << x)) if not v else (fc & ~(1 << x))
        st, _ = netsolve.solve(f2, n, spec, W=4, care=care | (1 << x), time_limit=5, workers=2)
        out[x] = int(v) if st == "unsat" else -1
    return out, S.mean(0) > 0.5, r["cost"]


def logistic_pred(cnt, sv, shown, targets):
    X = np.array([[(x >> i) & 1 for i in range(n)] for x in range(K)], float); Xb = np.c_[X, np.ones(K)]
    w = np.zeros(n + 1); idx = np.array(shown); N = cnt[idx]; Yp = sv[idx]
    for _ in range(200):                                      # Newton on weighted logistic loss, small ridge
        p = 1 / (1 + np.exp(-Xb[idx] @ w)); g = Xb[idx].T @ (N * p - Yp) + 1e-3 * w
        H = (Xb[idx] * (N * p * (1 - p))[:, None]).T @ Xb[idx] + 1e-3 * np.eye(n + 1)
        w -= np.linalg.solve(H, g)
    return {x: int(Xb[x] @ w > 0) for x in targets}, w


def analyse():
    res = {"pairs": json.loads((RAW / "cells.json").read_text())["pairs"], "features": FEATURES}
    f, care, cnt, sv = verdicts("all"); obs = [x for x in range(K) if (care >> x) & 1]
    res["n_observed_cells"] = len(obs); res["n_dilemmas_in_observed"] = int(cnt[obs].sum())
    r = netsolve.compile_partial(f, n, care, W=4, time_limit=60)
    res["min_cost"] = r["cost"]; res["certified_minimal"] = bool(r["certified_minimal"])
    st, a = netsolve.solve(f & care, n, netsolve.layered(n, []), W=4, care=care, time_limit=60, min_errors=True)
    y = ev(a); res["threshold_min_errors"] = int(sum(y[x] != bool((f >> x) & 1) for x in obs)); res["threshold_min_errors_status"] = st
    res["threshold_weights"] = a["body"]["neurons"][0] if a else None
    # inference from partial evidence
    rng = np.random.default_rng(5_200); acc_forced = []; frac_forced = []; acc_major = []; acc_log = []
    for s in range(40):
        perm = rng.permutation(obs); k = int(round(0.6 * len(obs))); shown = sorted(int(x) for x in perm[:k]); hid = sorted(int(x) for x in perm[k:])
        care_s = sum(1 << x for x in shown)
        fv, maj, _ = forced_values(f, care_s, hid)
        if fv is None:
            continue
        truth = {x: (f >> x) & 1 for x in hid}
        F = [x for x in hid if fv[x] >= 0]; frac_forced.append(len(F) / len(hid))
        if F:
            acc_forced.append(np.mean([fv[x] == truth[x] for x in F]))
        acc_major.append(np.mean([int(maj[x]) == truth[x] for x in hid]))
        lp, _ = logistic_pred(cnt, sv, shown, hid); acc_log.append(np.mean([lp[x] == truth[x] for x in hid]))
    res["partial"] = {"splits": len(frac_forced), "frac_forced": float(np.mean(frac_forced)), "acc_forced": float(np.mean(acc_forced)),
                      "acc_majority_of_minimal_forms": float(np.mean(acc_major)), "acc_logistic": float(np.mean(acc_log))}
    # cultures
    V = {k: verdicts(k) for k in ("0", "1", "2")}
    common = [x for x in range(K) if all((V[k][1] >> x) & 1 for k in V)]
    agree = [x for x in common if len({(V[k][0] >> x) & 1 for k in V}) == 1]
    res["cultures"] = {"n_common_cells": len(common), "frac_all_agree": len(agree) / len(common) if common else None,
                       "n_observed": {k: bin(V[k][1]).count("1") for k in V},
                       "min_cost": {k: netsolve.compile_partial(V[k][0], n, V[k][1], W=4, time_limit=60)["cost"] for k in V},
                       "disagreeing_cells": [{"cell": x, "features": [FEATURES[i] for i in range(n) if (x >> i) & 1],
                                              "verdict_by_cluster": {k: (V[k][0] >> x) & 1 for k in V},
                                              "saved_share": {k: round(V[k][3][x] / V[k][2][x], 3) for k in V}} for x in common if x not in agree]}
    P = res["partial"]; ok = len(obs) >= 40
    res["H52.1"] = "NO VERDICT" if not ok else "HELD" if res["threshold_min_errors"] == 0 else "BROKEN" if res["threshold_min_errors"] > 0.10 * len(obs) else "NEITHER"
    res["H52.2"] = "NO VERDICT" if not ok else "HELD" if (P["acc_forced"] >= 0.90 and P["frac_forced"] >= 0.20) else "BROKEN" if P["acc_forced"] < 0.75 else "NEITHER"
    res["H52.3"] = "NO VERDICT" if not ok else "HELD" if P["acc_majority_of_minimal_forms"] >= P["acc_logistic"] - 0.02 else "BROKEN" if P["acc_majority_of_minimal_forms"] < P["acc_logistic"] - 0.05 else "NEITHER"
    okc = all(v >= 25 for v in res["cultures"]["n_observed"].values()) and common
    fa = res["cultures"]["frac_all_agree"]
    res["H52.4"] = "NO VERDICT" if not okc else "HELD" if fa >= 0.85 else "BROKEN" if fa < 0.70 else "NEITHER"
    OUT.write_text(json.dumps(res, indent=1, default=int)); print(json.dumps(res, indent=1, default=int))


if __name__ == "__main__":
    {"build": build, "analyse": analyse}[sys.argv[1]]()
