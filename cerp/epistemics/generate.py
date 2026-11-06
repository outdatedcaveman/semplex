"""Constrained ontology generation (Spike 02b).

When every candidate ontology has failed, the charter (§3.4, §8.11) asks
for revision, not just refutation -- but "not unconstrained relativism"
(§1.3). Generation here is constrained by what the inquiry has already
established WITHOUT any ontology:

  * directly measured intervention effects (two-arm measurements):
      effect X -> Y measured YES  =>  a directed path X ~> Y must exist
      effect X -> Y measured NO   =>  no directed path X ~> Y
    (the NO rule assumes faithfulness at the measurement resolution --
     recorded as an explicit assumption in the ledger)
  * structures already refuted are excluded
  * structural hygiene: a latent must have >= 2 children (a latent with
    one child is absorbable and unidentifiable)

Survivors are ordered by parsimony (parameter count) -- a declared
POLICY, not evidence -- and screened by fit to the data already seen.
Screening on seen data is NOT acceptance: generated ontologies must pass
the same fresh-data prediction tests as every other candidate.
"""

from __future__ import annotations

import math
import random
from itertools import permutations

from .bayesnet import Structure, em_fit, loglik
from .stats import chi2_sf


def enumerate_dags(nodes):
    """All DAGs on `nodes` (dedupe of forward-edge subsets over all orders)."""
    seen = set()
    for order in permutations(nodes):
        fwd = [(order[i], order[j]) for i in range(len(order)) for j in range(i + 1, len(order))]
        for mask in range(1 << len(fwd)):
            edges = frozenset(e for k, e in enumerate(fwd) if mask >> k & 1)
            if edges not in seen:
                seen.add(edges)
                yield edges


def _reach(edges, x):
    out, frontier = set(), [x]
    while frontier:
        u = frontier.pop()
        for a, b in edges:
            if a == u and b not in out:
                out.add(b)
                frontier.append(b)
    return out


def constrained_structures(observables, facts, refuted_edgesets, max_latents=1):
    """Yield (edges, latents) satisfying all constraints, plus counts per stage."""
    counts = {"enumerated": 0, "after_hygiene": 0, "after_measured_facts": 0, "after_refuted": 0}
    out = []
    for n_lat in range(max_latents + 1):
        latents = tuple(f"L{i}" for i in range(n_lat))
        for edges in enumerate_dags(tuple(observables) + latents):
            counts["enumerated"] += 1
            if any(sum(1 for a, _ in edges if a == z) < 2 for z in latents):
                continue
            counts["after_hygiene"] += 1
            ok = True
            for x, y, present in facts:
                if (y in _reach(edges, x)) != present:
                    ok = False
                    break
            if not ok:
                continue
            counts["after_measured_facts"] += 1
            if _canon(edges, latents) in refuted_edgesets:
                continue
            counts["after_refuted"] += 1
            out.append((edges, latents))
    return out, counts


def _canon(edges, latents):
    ren = {z: f"L{i}" for i, z in enumerate(sorted(latents))}
    return frozenset((ren.get(a, a), ren.get(b, b)) for a, b in edges)


def canon_of_structure(s: Structure):
    return _canon(s.edges(), s.latents)


def to_structure(edges, latents, observables, idx):
    parents = {v: tuple(sorted(a for a, b in edges if b == v)) for v in tuple(observables) + latents}
    desc = "; ".join(f"{a}->{b}" for a, b in sorted(edges)) or "no edges"
    return Structure(f"G{idx}:" + desc, tuple(observables), latents, parents, f"generated: {desc}")


def _screen(s, train, rng):
    """Fit on SEEN data and test against the saturated model. A screen, not acceptance."""
    params, ll = em_fit(s, train, rng, restarts=3)
    ll_sat, cells = 0.0, 0
    for counts in train.values():
        n = sum(counts.values())
        ll_sat += sum(k * math.log(k / n) for k in counts.values())
        cells += len(counts) - 1
    g = 2 * (ll_sat - ll)
    df = max(cells - s.n_params(), 1)
    return chi2_sf(max(g, 0.0), df), params


def generate(observables, facts, refuted_structures, train, rng: random.Random,
             k=3, max_fits=400, screen_alpha=1e-3):
    refuted = {canon_of_structure(s) for s in refuted_structures}
    cands, counts = constrained_structures(observables, facts, refuted)
    structs = [to_structure(e, lat, observables, i) for i, (e, lat) in enumerate(cands)]
    structs.sort(key=lambda s: (s.n_params(), len(s.latents), s.name))  # parsimony POLICY
    accepted, fits = [], 0
    for s in structs:
        if fits >= max_fits or len(accepted) >= k:
            break
        fits += 1
        p, _ = _screen(s, train, rng)
        if p >= screen_alpha:
            accepted.append(s)
    counts.update(screened=fits, proposed=len(accepted))
    return accepted, counts
