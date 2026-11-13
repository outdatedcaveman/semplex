"""Spike 14b: Real tabular case study on UCI Breast Cancer (569 rows, 4 binary features)."""

import json
import random
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.feature_selection import mutual_info_classif

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cerp import atlas, csir
from cerp.epistemics.bayesnet import Structure, em_fit
from cerp.kernel import _eval_expr

OUT = ROOT / "experiments" / "results" / "spike14b_breast_cancer.json"


def build_breast_cancer_rows():
    ds = load_breast_cancer()
    X, y = ds.data, ds.target  # 569 x 30, target 0=malignant, 1=benign
    X_bin = (X > np.median(X, axis=0, keepdims=True)).astype(int)
    mi = mutual_info_classif(X_bin, y, random_state=42)
    top4 = np.argsort(mi)[-4:][::-1]
    feat_names = ["F0", "F1", "F2", "F3"]
    orig_names = [str(ds.feature_names[idx]) for idx in top4]
    tuples = [
        (int(X_bin[r, top4[0]]), int(X_bin[r, top4[1]]), int(X_bin[r, top4[2]]), int(X_bin[r, top4[3]]), int(y[r]))
        for r in range(X_bin.shape[0])
    ]
    return tuples, feat_names, orig_names, [round(float(mi[idx]), 4) for idx in top4]


def main():
    t0 = time.time()
    tuples, feat_names, orig_names, mis = build_breast_cancer_rows()
    s = Structure(
        name="breast_cancer_top4",
        observables=("F0", "F1", "F2", "F3", "Benign"),
        latents=(),
        parents={"F0": (), "F1": (), "F2": (), "F3": (), "Benign": ("F0", "F1", "F2", "F3")},
    )
    data = {(): Counter(tuples)}
    params, ll = em_fit(s, data, random.Random(0), restarts=2, iters=50)
    b = csir.distill_causal_rule(s, params, target="Benign", model_id="breast_cancer_top4")
    errs = csir.validate(b)
    recheck = csir.recheck(b)

    circ_node = [n for n in b["nodes"] if n["artifact"]["kind"] == "circuit"][0]
    expr_node = [n for n in b["nodes"] if n["artifact"]["kind"] == "expr"][0]
    tb = atlas.build_all(4)[4]
    tt_bits = 0
    for i in range(16):
        env = {feat_names[j]: bool((i >> j) & 1) for j in range(4)}
        if _eval_expr(expr_node["artifact"]["body"], env):
            tt_bits |= (1 << i)
    atlas_min_neurons = int(tb.hi[tt_bits])

    # Empirical accuracy of the distilled Boolean rule on the 569 binarized rows
    acc = sum(
        int(((tt_bits >> (t[0] + 2 * t[1] + 4 * t[2] + 8 * t[3])) & 1) == t[4])
        for t in tuples
    ) / len(tuples)

    res = {
        "dataset": "sklearn_breast_cancer_569",
        "n_rows": len(tuples),
        "selected_features": orig_names,
        "mutual_info": mis,
        "distilled_rule_accuracy": round(acc, 4),
        "loglik": round(float(ll), 4),
        "csir_validation_errors": errs,
        "csir_recheck": recheck,
        "distilled_circuit_cost": circ_node["resources"]["cost"],
        "atlas_min_threshold_neurons": atlas_min_neurons,
        "truth_table_bits": tt_bits,
        "elapsed_s": round(time.time() - t0, 3),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
