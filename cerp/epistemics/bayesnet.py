"""Discrete (binary) causal Bayesian networks with latent variables.

This is the model class for ontologies in Spike 02. A Structure is the
*ontological commitment* (which variables exist, which cause which); the
parameters are the quantitative part fitted to evidence.

Data format: {regime: Counter({cell: count})}
  regime = tuple(sorted(do.items()))   -- () for pure observation
  cell   = tuple of 0/1 values for structure.observables (fixed order)
"""

from __future__ import annotations

import math
import random
from collections import Counter
from dataclasses import dataclass, field
from itertools import product


@dataclass(frozen=True)
class Structure:
    name: str
    observables: tuple
    latents: tuple
    parents: dict = field(hash=False)  # var -> tuple of parent vars
    description: str = ""

    def __post_init__(self):
        allv = set(self.observables) | set(self.latents)
        for v, ps in self.parents.items():
            if v not in allv or not set(ps) <= allv:
                raise ValueError(f"{self.name}: unknown variable in parents of {v}")
        for v in allv:
            self.parents.setdefault(v, ())
        self.order  # raises on cycles

    @property
    def variables(self):
        return tuple(self.observables) + tuple(self.latents)

    @property
    def order(self):
        """Topological order."""
        out, seen, temp = [], set(), set()

        def visit(v):
            if v in seen:
                return
            if v in temp:
                raise ValueError(f"{self.name}: cycle through {v}")
            temp.add(v)
            for p in self.parents[v]:
                visit(p)
            temp.discard(v)
            seen.add(v)
            out.append(v)

        for v in sorted(self.variables):
            visit(v)
        return tuple(out)

    def edges(self):
        return {(p, c) for c, ps in self.parents.items() for p in ps}

    def n_params(self):
        return sum(1 << len(ps) for ps in self.parents.values())

    def commitments(self):
        """Typed ontological commitments (charter §3.1), name-based.

        Latent identity across structures is by NAME only -- an explicit,
        flagged simplification (spike-02 finding on identity criteria)."""
        c = {("exists-latent", z) for z in self.latents}
        c |= {("causes", p, ch) for p, ch in self.edges()}
        return frozenset(c)


def regime_key(do: dict) -> tuple:
    return tuple(sorted(do.items()))


def _pa_index(ps, assign):
    i = 0
    for p in ps:
        i = (i << 1) | assign[p]
    return i


def random_params(s: Structure, rng: random.Random, lo=0.15, hi=0.85):
    return {v: [rng.uniform(lo, hi) for _ in range(1 << len(s.parents[v]))] for v in s.variables}


def _full_configs(s: Structure, do: dict):
    """Yield (assignment dict, factor weight fn) over all variables consistent with do."""
    free = [v for v in s.variables if v not in do]
    for bits in product((0, 1), repeat=len(free)):
        a = dict(zip(free, bits))
        a.update(do)
        yield a


def _weight(s: Structure, params, a: dict, do: dict) -> float:
    w = 1.0
    for v in s.variables:
        if v in do:
            continue  # intervened: mechanism replaced (graph surgery)
        p1 = params[v][_pa_index(s.parents[v], a)]
        w *= p1 if a[v] else 1.0 - p1
    return w


def distribution(s: Structure, params, do: dict | None = None) -> dict:
    """P_do(cell) over observables."""
    do = do or {}
    out = Counter()
    for a in _full_configs(s, do):
        out[tuple(a[o] for o in s.observables)] += _weight(s, params, a, do)
    return dict(out)


def loglik(s: Structure, params, data) -> float:
    ll = 0.0
    for regime, counts in data.items():
        dist = distribution(s, params, dict(regime))
        for cell, n in counts.items():
            p = dist.get(cell, 0.0)
            if p <= 0:
                return -math.inf
            ll += n * math.log(p)
    return ll


def sample(s: Structure, params, n: int, rng: random.Random, do: dict | None = None) -> Counter:
    do = do or {}
    out = Counter()
    for _ in range(n):
        a = {}
        for v in s.order:
            if v in do:
                a[v] = do[v]
            else:
                a[v] = 1 if rng.random() < params[v][_pa_index(s.parents[v], a)] else 0
        out[tuple(a[o] for o in s.observables)] += 1
    return out


def em_fit(s: Structure, data, rng: random.Random, restarts=4, iters=400, alpha=0.5, tol=1e-8):
    """Maximum a-posteriori-smoothed EM. Returns (params, loglik).

    Heuristic in the charter's sense: local optima are possible; restarts
    mitigate but do not exclude them. A returned fit is a WITNESS that the
    structure can reach at least this likelihood (checkable by recomputing
    loglik); failure to fit well is NOT proof that no good fit exists.
    """
    best = (None, -math.inf)
    if not s.latents:
        restarts = 1
    # precompute per regime the consistent full configs per cell
    pre = {}
    for regime in data:
        do = dict(regime)
        by_cell = {}
        for a in _full_configs(s, do):
            by_cell.setdefault(tuple(a[o] for o in s.observables), []).append(a)
        pre[regime] = (do, by_cell)

    for _ in range(restarts):
        params = random_params(s, rng)
        prev = -math.inf
        for _ in range(iters):
            n1 = {v: [alpha] * (1 << len(s.parents[v])) for v in s.variables}
            nt = {v: [2 * alpha] * (1 << len(s.parents[v])) for v in s.variables}
            ll = 0.0
            for regime, counts in data.items():
                do, by_cell = pre[regime]
                for cell, n in counts.items():
                    configs = by_cell.get(cell, [])
                    ws = [_weight(s, params, a, do) for a in configs]
                    z = sum(ws)
                    if z <= 0:
                        ll = -math.inf
                        continue
                    ll += n * math.log(z)
                    for a, w in zip(configs, ws):
                        r = n * w / z
                        for v in s.variables:
                            if v in do:
                                continue
                            j = _pa_index(s.parents[v], a)
                            nt[v][j] += r
                            if a[v]:
                                n1[v][j] += r
            params = {v: [n1[v][j] / nt[v][j] for j in range(len(n1[v]))] for v in s.variables}
            if abs(ll - prev) < tol * max(1.0, abs(ll)):
                break
            prev = ll
        ll = loglik(s, params, data)
        if ll > best[1]:
            best = (params, ll)
    return best
