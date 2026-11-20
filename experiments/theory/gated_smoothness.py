"""Exploratory, post hoc (after Spike 73 verdicts): 'gated smoothness' rule for cyclic (and other) automata —
among constituents whose predictive-kernel share is >= theta, the leader is the smoothest along the letters
(mean P(e,a)/P(e,e)); energy breaks smoothness ties. Scored on Spikes 69, 71, 73 fitted runs."""
import json, os
from collections import Counter
R = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
def L(f): return json.load(open(os.path.join(R, f)))
cases = []
p69, r69 = L("spike69_predictions.json"), L("spike69.json")["per_automaton"]
for n, p in p69.items():
    sh = p["kernel_isotypic_weight"]; sm = {k: v["smooth"] for k, v in p["irreps"].items()}
    cases.append(("69", n, sh, sm, r69[n]["best_irreps"]))
p71, r71 = L("spike71_predictions.json"), L("spike71.json")["per_automaton"]
for n, p in p71.items():
    sh = {k: v["energy"] for k, v in p["irreps"].items()}; sm = {k: v["smooth"] for k, v in p["irreps"].items()}
    cases.append(("71", n, sh, sm, r71[n]["final"]))
p73, r73 = L("spike73_predictions.json")["cyclic"], L("spike73.json")["per"]
for n, p in p73.items():
    fit = [r["final_leader"] for r in r73[n] if r.get("fit", 0) >= 0.99]
    cases.append(("73", n, p["shares"], p["smoothness"], fit))
def rule(sh, sm, theta):
    pres = [k for k in sh if sh[k] >= theta]
    return max(pres, key=lambda k: (round(sm[k], 6), sh[k])) if pres else None
out = {}
for theta in (0.03, 0.05, 0.08, 0.1, 0.12, 0.15):
    tot = hit = 0; rows = []
    for sp, n, sh, sm, obs in cases:
        if not obs: continue
        pr = rule(sh, sm, theta); h = sum(o == pr for o in obs); tot += len(obs); hit += h
        rows.append((sp, n, pr, dict(Counter(obs)), h, len(obs)))
    out[theta] = {"hit": hit, "total": tot, "rows": rows}
    cyc = [r for r in rows if r[1].startswith("Z")]
    print(theta, "all", hit, "/", tot, "| cyclic", sum(r[4] for r in cyc), "/", sum(r[5] for r in cyc))
json.dump({str(k): v for k, v in out.items()}, open(os.path.join(R, "theory_gated_smoothness.json"), "w"), indent=1)
for r in out[0.08]["rows"]: print(r)
