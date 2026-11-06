"""The ontology-epistemology co-development loop (charter §8), v0.

    inquire(interface, candidates)  ->  report with a ledger

The agent sees ONLY `interface` (protocols + counts). It never imports the
world module (enforced by a test). Each round:

  1. fit every surviving ontology to all data so far (EM; heuristic)
  2. pick the protocol with the highest expected information gain about
     WHICH surviving ontology is right (charter §8 step 7)
  3. run it and use the fresh batch as a PREDICTION TEST of fits that have
     never seen it: adequacy (G-test) and pairwise log-score comparison,
     with Bonferroni control over every test the run may perform
  4. ontologies that fail are dropped; the change is recorded as a typed
     REVISION (what was dropped, which commitments became settled or open,
     which earlier claims are invalidated) -- charter §3.4
  5. answer the declared queries: only if every survivor agrees; an
     intervention claim is EMPIRICALLY-SUPPORTED only if that intervention
     was actually run, otherwise it is a model-derived CONJECTURE
When no available protocol discriminates the survivors, the agent stops,
attaches equivalence witnesses, and reports what is UNDETERMINED.
"""

from __future__ import annotations

import math
import random
from collections import Counter
from itertools import combinations

from ..ledger import Ledger, Status
from .bayesnet import distribution, em_fit, regime_key
from .stats import chi2_sf, entropy, kl, paired_log_score, z_two_sided

# ------------------------------------------------------------------ queries

DEFAULT_QUERIES = (
    ("effect", "A", "Y"),
    ("effect", "S1", "S2"),
    ("effect", "S1", "Y"),
    ("shared-latent", "S1", "S2"),
)


# Richer measurement set for generation: every effect the protocols can measure.
EXTENDED_QUERIES = DEFAULT_QUERIES + (("effect", "A", "S1"), ("effect", "A", "S2"))


def query_text(q):
    if q[0] == "effect":
        return f"intervening on {q[1]} changes {q[2]}"
    return f"{q[1]} and {q[2]} measure a shared hidden quantity"


def model_answer(structure, params, q, delta=0.05):
    if q[0] == "effect":
        _, x, y = q
        i = structure.observables.index(y)
        m = [sum(p for c, p in distribution(structure, params, {x: v}).items() if c[i]) for v in (0, 1)]
        return abs(m[0] - m[1]) > delta
    if q[0] == "shared-latent":
        _, a, b = q
        return any(z in structure.parents[a] and z in structure.parents[b] for z in structure.latents)
    raise ValueError(q)


def fmt_do(do):
    return "observe" if not do else "do(" + ",".join(f"{k}={v}" for k, v in sorted(do.items())) + ")"


# ------------------------------------------------------------------ the loop

def inquire(interface, candidates, *, queries=DEFAULT_QUERIES, n_initial=1500, n_batch=1500,
            max_rounds=14, alpha=0.05, eig_min=0.003, seed=0, ledger=None, confirm_untested=True,
            generate_on_refutation=False, max_generations=2):
    rng = random.Random(seed)
    L = ledger or Ledger(prefix="E")
    k = len(candidates)
    n_tests = max_rounds * (k + k * (k - 1) // 2)
    a_each = alpha / n_tests
    z_crit = z_two_sided(a_each)
    rep = {"rounds": [], "ledger": L, "alpha_per_test": a_each}

    closed_world = L.assumption(
        "Closed world: at least one candidate ontology is adequate to the world",
        why="researcher-chosen candidate set: " + ", ".join(c.name for c in candidates)
            + ". Cannot be established from inside the candidate set; only refuted "
              "(if every candidate fails adequacy).")

    train = {(): interface.run({}, n_initial)}
    tested = {()}
    alive = list(candidates)
    elim_claims = []
    answers = {}  # q -> claim id
    settled_before = None
    refuted = []      # structures eliminated so far (generation must not re-propose them)
    validated = None  # after generation: protocols the generated set has faced on FRESH data
    generations = 0
    rep["generations"] = []

    for r in range(max_rounds):
        fits = {m.name: em_fit(m, train, rng)[0] for m in alive}
        protocols = interface.protocols()
        eig = {regime_key(do): _eig(alive, fits, do) for do in protocols}
        best = max(protocols, key=lambda d: eig[regime_key(d)])
        if eig[regime_key(best)] < eig_min:
            untested = [d for d in protocols if regime_key(d) not in tested]
            if validated is not None:  # generated after seeing data: re-test on every protocol
                untested = [d for d in protocols if regime_key(d) not in validated]
            imprecise = _imprecise_arms(train, tested, queries, interface.observables, protocols)
            arms = {regime_key({q[1]: v}) for q in queries if q[0] == "effect" for v in (0, 1)}
            if not alive:  # model-free mode: only arms that measure an effect query are worth running
                untested = [d for d in untested if regime_key(d) in arms]
            if confirm_untested and untested:
                best = untested[0]  # confirmation probe: test predictions we would rely on
                why = "confirmation probe (no discriminating protocol; testing untested predictions)"
            elif imprecise:
                best = imprecise[0]  # precision probe: a direct measurement is unresolved
                why = "precision probe (direct effect estimate cannot yet exclude or confirm the threshold)"
            elif not alive and generate_on_refutation and generations < max_generations:
                generations += 1
                alive, closed_world = _generate(L, interface, train, answers, refuted, rng, rep,
                                                generations)
                validated = set()
                if not alive:
                    break
                continue
            else:
                break
        else:
            why = f"max expected information gain {eig[regime_key(best)]:.4f} nats/sample"

        batch = interface.run(best, n_batch)
        rk = regime_key(best)
        preds = {m.name: distribution(m, fits[m.name], best) for m in alive}
        round_rec = {"round": r, "protocol": fmt_do(best), "why": why,
                     "eig": {fmt_do(dict(k_)): round(v, 4) for k_, v in eig.items()}, "dropped": []}
        new_elims = []

        # 3a. adequacy of each survivor's PREDICTION on fresh data -- the only
        # ground for ELIMINATION. Calibrated for parameter-estimation error
        # (spike-02 finding: a naive G-test rejects the true ontology).
        for m in alive:
            g, df, p = adequacy_test(m, fits[m.name], train, best, batch, rng)
            data = {"n": n_batch, "G": round(g, 2), "df_eff": df}
            proto = (f"G-test of a prediction made before the data, null calibrated by parametric "
                     f"bootstrap (B={BOOT_B}, Satterthwaite); Bonferroni alpha={a_each:.2e}")
            if p < a_each:
                c = L.empirical(f"{m.name} is NOT adequate under {fmt_do(best)}", protocol=proto,
                                data=data, uncertainty=f"p={p:.2e}", category="adequacy")
                new_elims.append((m, c.id))
            else:
                L.empirical(f"{m.name} is adequate under {fmt_do(best)} at the tested resolution",
                            protocol=proto, data=data,
                            uncertainty=f"p={p:.3f}; adequacy is protocol- and n-indexed (charter §5.8)",
                            category="adequacy")

        # 3b. pairwise predictive comparison: recorded as PREFERENCE, never as
        # grounds for rejection (a better-fitted predictor is not a truer ontology).
        for a, b in combinations(alive, 2):
            mean, se, z = paired_log_score(batch, preds[a.name], preds[b.name])
            if abs(z) > z_crit:
                win, lose = (a, b) if z > 0 else (b, a)
                L.empirical(f"preference: {win.name} predicts {fmt_do(best)} better than {lose.name}",
                            protocol=f"paired log score on fresh batch, |z|>{z_crit:.2f}",
                            data={"n": n_batch, "mean_diff": round(abs(mean), 5), "z": round(abs(z), 2)},
                            uncertainty=f"se={se:.5f}; Bonferroni over {n_tests} tests",
                            category="preference")

        for k_, v in batch.items():
            train.setdefault(rk, Counter())[k_] += v
        tested.add(rk)
        if validated is not None:
            validated.add(rk)

        dropped = {m.name for m, _ in new_elims}
        if dropped:
            survivors = [m for m in alive if m.name not in dropped]
            refuted += [m for m in alive if m.name in dropped]
            ids = sorted({cid for m, cid in new_elims})
            elim_claims += ids
            rev = _revise(L, alive, survivors, ids, answers, settled_before)
            settled_before = rev["settled"]
            round_rec["dropped"] = sorted(dropped)
            round_rec["revision"] = rev["claim"]
            alive = survivors
        rep["rounds"].append(round_rec)
        if not alive:
            if L.claims[closed_world.id].retracted_by is None:
                b = L.boundary("Every candidate ontology failed: the closed-world assumption is refuted",
                               reason="no candidate is adequate; the candidate set must be revised by the "
                                      "researcher. Inquiry continues in model-free measurement mode.",
                               category="ontology-revision")
                L.retract(closed_world.id, by=b.id)
            _answer(L, [], {}, queries, tested, elim_claims, closed_world.id, answers,
                    train, interface.observables)
            continue
        # 5. (re)answer queries with fits that include the new batch
        fits = {m.name: em_fit(m, train, rng)[0] for m in alive}
        _answer(L, alive, fits, queries, tested, elim_claims, closed_world.id, answers,
                train, interface.observables)

    rep["survivors"] = [m.name for m in alive]
    rep["tested_protocols"] = sorted(fmt_do(dict(t)) for t in tested)
    rep["spent"] = interface.spent
    if len(alive) > 1:
        fits = {m.name: em_fit(m, train, rng)[0] for m in alive}
        rep["equivalence"] = _witness_equivalence(L, alive, fits, sorted(tested), rng)
    rep["answers"] = {query_text(q): _answer_summary(L, cid) for q, cid in answers.items()}
    return rep


# ------------------------------------------------------------------ pieces

BOOT_B = 30


def _g_stat(counts, probs):
    n = sum(counts.values())
    g = 0.0
    for cell, k in counts.items():
        p = probs.get(cell, 0.0)
        if p <= 0:
            return math.inf
        g += 2 * k * math.log(k / (n * p))
    return g


def _sample_counts(dist, n, rng):
    cells = list(dist)
    return Counter(rng.choices(cells, weights=[dist[c] for c in cells], k=n))


def adequacy_test(model, params, train, do, batch, rng, B=BOOT_B):
    """Is `batch` consistent with the model's prediction for protocol `do`,
    given that the prediction was itself estimated from `train`?

    Null distribution of G by parametric bootstrap: simulate train* and
    test* from the fitted model, refit on train*, predict, compute G*.
    The tail is taken from a scaled chi-square matched to the bootstrap
    moments (Satterthwaite), so small Bonferroni alphas remain reachable.
    Approximate (heuristic calibration); returns (G, effective df, p).
    """
    pred = distribution(model, params, do)
    g = _g_stat(batch, pred)
    if math.isinf(g):
        return g, None, 0.0
    n = sum(batch.values())
    gs = []
    for _ in range(B):
        tr = {rk: _sample_counts(distribution(model, params, dict(rk)), sum(c.values()), rng)
              for rk, c in train.items()}
        pb = em_fit(model, tr, rng, restarts=2)[0]
        gs.append(_g_stat(_sample_counts(pred, n, rng), distribution(model, pb, do)))
    gs = [x for x in gs if not math.isinf(x)]
    mu = sum(gs) / len(gs)
    var = sum((x - mu) ** 2 for x in gs) / (len(gs) - 1)
    c, nu = var / (2 * mu), 2 * mu * mu / var
    return g, round(nu, 2), chi2_sf(g / c, nu)

def _eig(models, fits, do):
    """Mutual information between model identity (uniform) and one sample."""
    if len(models) < 2:
        return 0.0
    ps = [distribution(m, fits[m.name], do) for m in models]
    cells = set().union(*ps)
    mix = {c: sum(p.get(c, 0.0) for p in ps) / len(ps) for c in cells}
    return max(0.0, entropy(mix) - sum(entropy(p) for p in ps) / len(ps))


def _revise(L, before, after, motivating, answers, settled_before):
    cb = [m.commitments() for m in before]
    ca = [m.commitments() for m in after]
    settled = frozenset.intersection(*ca) if ca else frozenset()
    open_ = (frozenset.union(*ca) - settled) if ca else frozenset()
    prev_settled = settled_before if settled_before is not None else frozenset.intersection(*cb)
    stale = [cid for cid in answers.values() if L.claims[cid].retracted_by is None]
    claim = L.derived(
        f"Ontology revision: drop {sorted(m.name for m in before if m not in after)}; "
        f"keep {[m.name for m in after]}",
        depends_on=motivating, category="ontology-revision",
        rule="drop ontologies whose predictions failed on fresh data (charter §3.4, §8.8)",
        evidence={
            "dropped": sorted(m.name for m in before if m not in after),
            "surviving": [m.name for m in after],
            "commitments_settled": sorted(map(str, settled)),
            "commitments_newly_settled": sorted(map(str, settled - prev_settled)),
            "commitments_still_open": sorted(map(str, open_)),
            "claims_up_for_reevaluation": stale,
        })
    return {"claim": claim.id, "settled": settled}


def direct_effect(train, observables, x, y, z):
    """Model-free estimate of P(y=1 | do(x=1)) - P(y=1 | do(x=0)) from the two
    intervention arms actually run, with a z-level interval. No ontology used."""
    i = observables.index(y)
    est = []
    for v in (0, 1):
        c = train[regime_key({x: v})]
        n = sum(c.values())
        p = sum(k for cell, k in c.items() if cell[i]) / n
        est.append((p, n))
    (p0, n0), (p1, n1) = est
    d = p1 - p0
    se = math.sqrt(p0 * (1 - p0) / n0 + p1 * (1 - p1) / n1)
    return d, d - z * se, d + z * se


def _direct_facts(L, answers):
    """(x, y, present) for every effect query settled by DIRECT two-arm measurement."""
    out, ids = [], []
    for q, cid in answers.items():
        c = L.claims[cid]
        if q[0] == "effect" and "[direct" in c.statement and not c.statement.startswith("UNDETERMINED"):
            out.append((q[1], q[2], c.statement.startswith("YES")))
            ids.append(cid)
    return out, ids


def _generate(L, interface, train, answers, refuted, rng, rep, generation):
    from .generate import generate

    facts, fact_ids = _direct_facts(L, answers)
    faith = L.assumption(
        f"Faithfulness at resolution 0.05 (generation {generation}): a measured NO-effect means no "
        "directed causal path", why="needed to turn measured absences into forbidden paths; can fail "
        "with cancelling paths or effects below the resolution")
    new, counts = generate(interface.observables, facts, refuted, train, rng)
    gen = L.derived(
        f"Ontology generation {generation}: proposed {[m.name for m in new]}",
        depends_on=fact_ids + [faith.id] if fact_ids else [faith.id], category="ontology-generation",
        rule="enumerate DAGs (<=1 latent), keep those consistent with directly measured effects and not "
             "already refuted; order by parameter count (parsimony POLICY); screen on seen data",
        evidence={"facts": facts, "refuted": [m.name for m in refuted], "counts": counts})
    rep["generations"].append({"generation": generation, "facts": facts, "counts": counts,
                               "proposed": [m.name for m in new], "claim": gen.id})
    rep.setdefault("generated_structures", {}).update({m.name: m for m in new})
    cw = L.assumption(
        f"Closed world (generation {generation}): at least one generated ontology is adequate",
        why=f"generated set {[m.name for m in new]}; provenance {gen.id}")
    return new, cw


def _imprecise_arms(train, tested, queries, observables, protocols, z=3.0, delta=0.05):
    """Intervention arms whose extra data would resolve an UNDETERMINED direct effect."""
    out = []
    for q in queries:
        if q[0] != "effect" or not {regime_key({q[1]: 0}), regime_key({q[1]: 1})} <= tested:
            continue
        d, lo, hi = direct_effect(train, observables, q[1], q[2], z)
        resolved = (min(abs(lo), abs(hi)) > delta and lo * hi > 0) or (-delta < lo and hi < delta)
        if not resolved:
            arm = min((0, 1), key=lambda v: sum(train[regime_key({q[1]: v})].values()))
            if {q[1]: arm} in protocols:
                out.append({q[1]: arm})
    return out


def _answer(L, alive, fits, queries, tested, elim_claims, closed_world_id, answers,
            train=None, observables=None, z=3.0, delta=0.05):
    for q in queries:
        direct = (q[0] == "effect" and train is not None
                  and {regime_key({q[1]: 0}), regime_key({q[1]: 1})} <= tested)
        if direct:
            # Theory-light route (spike-02 finding F5): measured, not modelled.
            d, lo, hi = direct_effect(train, observables, q[1], q[2], z)
            if min(abs(lo), abs(hi)) > delta and lo * hi > 0:
                head = "YES"
            elif -delta < lo and hi < delta:
                head = "NO"
            else:
                head = "UNDETERMINED"
            stmt = f"{head}: {query_text(q)} [direct two-arm measurement, no ontology]"
        elif alive:
            votes = {m.name: model_answer(m, fits[m.name], q) for m in alive}
            if len(set(votes.values())) == 1:
                head = "YES" if next(iter(votes.values())) else "NO"
                stmt = f"{head}: {query_text(q)}" + (" [model-derived; intervention never run]"
                                                     if q[0] == "effect" else "")
            else:
                head = "UNDETERMINED"
                stmt = f"UNDETERMINED: {query_text(q)} (survivors disagree: {votes})"
        else:
            head = "UNDETERMINED"
            stmt = f"UNDETERMINED: {query_text(q)} (no surviving ontology; not directly measured)"
        prev = answers.get(q)
        if prev and L.claims[prev].statement == stmt and L.effective_status(prev) is not Status.RETRACTED:
            continue
        if direct:
            c = L.empirical(stmt, protocol=f"do({q[1]}=0) vs do({q[1]}=1) arms, difference in P({q[2]}=1); "
                                           f"YES iff the {z}-sigma interval excludes ±{delta}",
                            data={"diff": round(d, 4), "interval": [round(lo, 4), round(hi, 4)]},
                            uncertainty=f"normal approximation, z={z}", category="answer")
        elif head == "UNDETERMINED":
            c = L.boundary(stmt, reason="not measured directly, and the surviving ontologies "
                                        "(if any) do not agree", category="answer", undetermined=True)
        else:
            c = L.derived(stmt, depends_on=[closed_world_id] + elim_claims[-20:], category="answer",
                          rule="all surviving candidate ontologies agree",
                          assumptions=["closed world over candidates"])
        if prev and L.claims[prev].retracted_by is None:
            L.retract(prev, by=c.id)
        answers[q] = c.id


def _answer_summary(L, cid):
    c = L.claims[cid]
    return {"claim": cid, "statement": c.statement, "status": L.effective_status(cid).label}


def _witness_equivalence(L, alive, fits, regimes, rng, n_pseudo=20000):
    """For each ordered pair (a, b): can b reproduce a's fitted predictions on
    every protocol run so far? A successful fit is a checkable witness of
    (approximate) Omega-equivalence on these data; a failed fit proves nothing."""
    out = {}
    for a, b in ((x, y) for x in alive for y in alive if x is not y):
        pseudo = {}
        for rk in regimes:
            d = distribution(a, fits[a.name], dict(rk))
            pseudo[rk] = Counter({c: p * n_pseudo for c, p in d.items()})
        pb, _ = em_fit(b, pseudo, rng, restarts=6)
        worst = max(kl(distribution(a, fits[a.name], dict(rk)), distribution(b, pb, dict(rk)))
                    for rk in regimes)
        ok = worst < 1e-3
        stmt = (f"{b.name} {'CAN' if ok else 'could not be fitted to'} reproduce {a.name}'s fitted "
                f"predictions on protocols {[fmt_do(dict(r)) for r in regimes]} (max KL {worst:.2e})")
        if ok:
            c = L.witnessed(stmt, witness_check="KL recomputed in float64 from EM witness parameters",
                            category="equivalence")
        else:
            c = L.heuristic(stmt, procedure="EM fit failure is not proof of non-equivalence (local optima)",
                            category="equivalence")
        out[f"{b.name} ⊒ {a.name}"] = {"max_kl": worst, "witnessed": ok, "claim": c.id}
    return out
