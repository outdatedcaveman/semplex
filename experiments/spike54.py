"""Spike 54: are semantic products tensor products in activations? (C29 product row)

Uses Neuronpedia's public top-k-by-token endpoint (published sparse autoencoders);
no model is run here. Responses are cached in experiments/results/spike54_raw/."""
import json, os, sys, time, urllib.request
import numpy as np
from experiments.spike53 import cyc_test

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "results", "spike54_raw")
OUT = os.path.join(ROOT, "results", "spike54.json")
API = "https://www.neuronpedia.org/api/search-topk-by-token"
SOURCES = [("gpt2-small", "4-res-jb"), ("gpt2-small", "8-res-jb"), ("gpt2-small", "10-res-jb"),
           ("gemma-2-2b", "12-gemmascope-res-16k"), ("gemma-2-2b", "20-gemmascope-res-16k"),
           ("gemma-3-1b", "13-gemmascope-2-res-16k"), ("llama3.1-8b", "16-llamascope-res-32k")]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]
# family: (cyclic factor, second factor, templates, phrase(i, j) -> (sentence fill), last word)
FAMILIES = {
    "weekday_x_time": (DAYS, ["morning", "afternoon", "evening", "night"],
                       ["It happened on {a} {b}", "We met on {a} {b}"], lambda a, b: b),
    "month_x_part": (MONTHS, ["early", "late"],
                     ["It happened in {b} {a}", "We met in {b} {a}"], lambda a, b: a),
    "weekday_x_direction": (DAYS, ["last", "next"],
                            ["It happened {b} {a}", "We met {b} {a}"], lambda a, b: a),
}
SEED = 5400


def query(model, source, texts):
    os.makedirs(RAW, exist_ok=True)
    key = f"{model}__{source}__{abs(hash(tuple(texts))) % 10**12}.json"
    p = os.path.join(RAW, key)
    if os.path.exists(p):
        return json.load(open(p))
    body = json.dumps({"modelId": model, "source": source, "text": texts, "numResults": 20}).encode()
    for t in range(6):
        try:
            req = urllib.request.Request(API, body, {"Content-Type": "application/json", "User-Agent": "semplex-np/0.1"})
            d = json.load(urllib.request.urlopen(req, timeout=300))
            break
        except Exception as e:
            if t == 5:
                raise
            time.sleep(10 * (t + 1))
    out = [[{"token": x["token"], "f": [[f["featureIndex"], f["activationValue"]] for f in x["topFeatures"]]}
            for x in r["results"]] for r in d["results"]]
    json.dump({"model": model, "source": source, "texts": texts, "results": out}, open(p, "w"))
    return json.load(open(p))


def run():
    for model, source in SOURCES:
        for fam, (A, B, T, last) in FAMILIES.items():
            for tpl in T:
                texts = [tpl.format(a=a, b=b) for a in A for b in B]
                query(model, source, texts)
            print(model, source, fam, "ok", flush=True)


def analyse():
    rng = np.random.default_rng(SEED)
    cases, skipped = [], []
    for model, source in SOURCES:
        for fam, (A, B, T, last) in FAMILIES.items():
            vecs, ok = {}, True
            for tpl in T:
                texts = [tpl.format(a=a, b=b) for a in A for b in B]
                d = query(model, source, texts)
                for k, (a, b) in enumerate([(a, b) for a in A for b in B]):
                    toks = d["results"][k]
                    if toks[-1]["token"] != " " + last(a, b):
                        ok = False
                    v = vecs.setdefault((a, b), {})
                    for fi, val in toks[-1]["f"]:
                        v[fi] = v.get(fi, 0.0) + val
            if not ok:
                skipped.append(f"{model}:{source}:{fam}"); continue
            feats = sorted({f for v in vecs.values() for f in v})
            col = {f: c for c, f in enumerate(feats)}
            X = np.zeros((len(A), len(B), len(feats)))
            for (a, b), v in vecs.items():
                for f, val in v.items():
                    X[A.index(a), B.index(b), col[f]] = val
            X = X / np.linalg.norm(X, axis=2, keepdims=True)
            mu = X.mean((0, 1)); a_ = X.mean(1) - mu; b_ = X.mean(0) - mu
            r = X - mu - a_[:, None] - b_[None]
            n, m = len(A), len(B)
            share = float((r ** 2).sum() / ((X - mu) ** 2).sum())
            null = (n - 1) * (m - 1) / (n * m - 1)
            c = {"case": f"{model}:{source}", "family": fam, "n_features": len(feats),
                 "additive": cyc_test(a_, rng), "interaction": cyc_test(r.reshape(n, -1), rng),
                 "interaction_share": share, "null_share": null, "relative_interaction": share / null}
            if m == 4:
                c["second_factor_cyclic"] = cyc_test(b_, rng, 23)  # 4 levels: only 4!-1 relabellings
            cases.append(c)
    frac = lambda xs: float(np.mean(xs)) if xs else None
    v = {}
    f1 = frac([c["additive"]["p"] < 0.01 for c in cases])
    f2 = frac([c["interaction"]["p"] < 0.01 for c in cases])
    med = float(np.median([c["relative_interaction"] for c in cases])) if cases else None
    if len(cases) < 12:
        v = {"H54.1": "NO VERDICT", "H54.2": "NO VERDICT", "H54.3": "NO VERDICT"}
    else:
        v["H54.1"] = "HELD" if f1 >= 0.75 else "BROKEN" if f1 < 0.5 else "NEITHER"
        v["H54.2"] = "HELD" if f2 >= 0.5 else "BROKEN" if f2 <= 0.2 else "NEITHER"
        v["H54.3"] = "HELD" if med >= 0.643 else "BROKEN" if med <= 0.543 else "NEITHER"
    by_fam = {f: {"n": len(cs), "additive_frac_sig": frac([c["additive"]["p"] < 0.01 for c in cs]),
                  "interaction_frac_sig": frac([c["interaction"]["p"] < 0.01 for c in cs]),
                  "median_relative_interaction": float(np.median([c["relative_interaction"] for c in cs]))}
              for f in FAMILIES for cs in [[c for c in cases if c["family"] == f]] if cs}
    out = {"verdicts": v, "n_cases": len(cases), "skipped": skipped,
           "additive_frac_sig": f1, "interaction_frac_sig": f2, "median_relative_interaction": med,
           "interaction_frac_p05": frac([c["interaction"]["p"] < 0.05 for c in cases]),
           "by_family": by_fam, "cases": cases}
    json.dump(out, open(OUT, "w"), indent=1, default=float)
    print(json.dumps(v, indent=1))


if __name__ == "__main__":
    {"run": run, "analyse": analyse}[sys.argv[1]]()
