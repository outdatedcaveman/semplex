"""Exact finite POMDP realization of a hidden Z3 Wilson-loop holonomy."""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from typing import Iterable, Sequence

Q = 3
Belief = tuple[Fraction, Fraction, Fraction]
Connection = tuple[int, int, int]

def _belief(values: Sequence[Fraction]) -> Belief:
    if len(values) != Q:
        raise ValueError("a Z3 belief must have exactly three entries")
    result = tuple(Fraction(v) for v in values)
    if any(v < 0 for v in result) or sum(result) != 1:
        raise ValueError("belief entries must be nonnegative and sum to one")
    return result  # type: ignore[return-value]

def gauge_transform(a: Connection, g: Connection) -> Connection:
    """A'_i = A_i + g_(i+1) - g_i, with indices modulo three."""
    if len(a) != 3 or len(g) != 3:
        raise ValueError("the ring has exactly three vertices and edges")
    return tuple((a[i] + g[(i + 1) % 3] - g[i]) % Q for i in range(3))  # type: ignore[return-value]

def holonomy(a: Connection) -> int:
    if len(a) != 3 or any(x not in range(Q) for x in a):
        raise ValueError("connection must be a triple over Z/3")
    return sum(a) % Q

def all_connections() -> tuple[Connection, ...]:
    return tuple(product(range(Q), repeat=3))  # type: ignore[return-value]

def gauge_orbit(a: Connection) -> frozenset[Connection]:
    return frozenset(gauge_transform(a, g) for g in all_connections())


def execute_walk(a: Connection, actions: Sequence[int]) -> tuple[int, int]:
    """Execute primitive clockwise/counterclockwise edge controls from vertex 0."""
    if len(a) != 3 or any(x not in range(Q) for x in a):
        raise ValueError("connection must be a triple over Z/3")
    vertex = 0
    phase = 0
    for direction in actions:
        if direction == 1:
            phase += a[vertex]
            vertex = (vertex + 1) % 3
        elif direction == -1:
            edge = (vertex - 1) % 3
            phase -= a[edge]
            vertex = (vertex - 1) % 3
        else:
            raise ValueError("each control must be +1 or -1")
    return vertex, phase % Q

def winding_number(actions: Sequence[int]) -> int:
    displacement = sum(actions)
    if displacement % 3 != 0:
        raise ValueError("the intervention path is not closed")
    return displacement // 3

def closed_walks(max_steps: int) -> tuple[tuple[int, ...], ...]:
    if max_steps < 0:
        raise ValueError("max_steps cannot be negative")
    return tuple(
        word for n in range(1, max_steps + 1)
        for word in product((-1, 1), repeat=n)
        if sum(word) % 3 == 0
    )

def path_response_distribution(noise: Fraction, belief: Sequence[Fraction],
                                actions: Sequence[int]) -> tuple[Fraction, ...]:
    """Noisy response to a closed path; open paths have no gauge-invariant readout."""
    winding = winding_number(actions)
    b = _belief(belief)
    k = channel_matrix(Fraction(noise))
    return tuple(
        sum(b[t] * k[(winding * t) % Q][y] for t in range(Q))
        for y in range(Q)
    )

def channel_matrix(noise: Fraction) -> tuple[tuple[Fraction, ...], ...]:
    """K[theta,y] = P(y|theta); eta to each wrong outcome."""
    eta = Fraction(noise)
    if not 0 <= eta <= Fraction(1, 2):
        raise ValueError("noise must lie in [0, 1/2]")
    return tuple(tuple(Fraction(1) - 2 * eta if y == theta else eta
                       for y in range(Q)) for theta in range(Q))

def channel_determinant(noise: Fraction) -> Fraction:
    return (1 - 3 * Fraction(noise)) ** 2

@dataclass(frozen=True)
class HolonomyPOMDP:
    """Static hidden holonomy with costed local and global interventions."""
    noise: Fraction = Fraction(0)
    local_probe_cost: int = 1
    loop_probe_cost: int = 3

    def __post_init__(self) -> None:
        channel_matrix(Fraction(self.noise))
        if self.local_probe_cost <= 0 or self.loop_probe_cost <= 0:
            raise ValueError("intervention costs must be positive")

    def local_response(self, theta: int) -> int:
        if theta not in range(Q):
            raise ValueError("hidden holonomy must lie in Z/3")
        return 0

    def loop_likelihood(self, theta: int, observation: int) -> Fraction:
        if theta not in range(Q) or observation not in range(Q):
            raise ValueError("theta and observation must lie in Z/3")
        return channel_matrix(Fraction(self.noise))[theta][observation]

    def response_distribution(self, belief: Sequence[Fraction]) -> tuple[Fraction, ...]:
        b = _belief(belief)
        k = channel_matrix(Fraction(self.noise))
        return tuple(sum(b[t] * k[t][y] for t in range(Q)) for y in range(Q))

    def sequence_distribution(self, belief: Sequence[Fraction],
                              observations: Sequence[int]) -> Fraction:
        """Joint law; observations share one static hidden theta."""
        b = _belief(belief)
        k = channel_matrix(Fraction(self.noise))
        if any(y not in range(Q) for y in observations):
            raise ValueError("observations must lie in Z/3")
        return sum(b[t] * _product(k[t][y] for y in observations)
                   for t in range(Q))

    def profile(self, belief: Sequence[Fraction], budget: int) -> tuple[Fraction, ...]:
        """Responses to every closed primitive-control path within budget."""
        if budget < 0:
            raise ValueError("budget cannot be negative")
        if self.loop_probe_cost != 3 * self.local_probe_cost:
            raise ValueError("on this three-cycle, one winding costs three edge steps")
        b = _belief(belief)
        walks = closed_walks(budget // self.local_probe_cost)
        return tuple(
            value
            for walk in walks
            for value in path_response_distribution(self.noise, b, walk)
        )

    def equivalent(self, left: Sequence[Fraction], right: Sequence[Fraction],
                   budget: int) -> bool:
        return self.profile(left, budget) == self.profile(right, budget)

    def posterior_sequence(self, prior: Sequence[Fraction],
                           observations: Sequence[int]) -> Belief:
        """Posterior after a finite ordered history of clockwise-loop outcomes."""
        b = _belief(prior)
        if any(y not in range(Q) for y in observations):
            raise ValueError("observations must lie in Z/3")
        k = channel_matrix(Fraction(self.noise))
        unnormalized = tuple(
            b[t] * _product(k[t][y] for y in observations)
            for t in range(Q)
        )
        evidence = sum(unnormalized)
        if evidence == 0:
            raise ValueError("history has zero probability under this prior")
        return _belief(tuple(x / evidence for x in unnormalized))

    def posterior(self, prior: Sequence[Fraction], observation: int) -> Belief:
        return self.posterior_sequence(prior, (observation,))

def _product(values: Iterable[Fraction]) -> Fraction:
    result = Fraction(1)
    for value in values:
        result *= value
    return result

def exhaustive_gauge_audit() -> dict[str, int | bool]:
    connections = all_connections()
    transformations = all_connections()
    invariant = all(holonomy(gauge_transform(a, g)) == holonomy(a)
                    for a in connections for g in transformations)
    distinct_orbits = {gauge_orbit(a) for a in connections}
    exact_orbits = all(
        gauge_orbit(a) == frozenset(b for b in connections
                                    if holonomy(b) == holonomy(a))
        for a in connections
    )
    return {
        "connections": len(connections),
        "gauge_transformations": len(transformations),
        "distinct_gauge_orbits": len(distinct_orbits),
        "each_orbit_size": len(next(iter(distinct_orbits))),
        "holonomy_gauge_invariant": invariant,
        "orbits_exactly_holonomy_classes": exact_orbits,
    }

def exhaustive_resource_audit() -> dict[str, object]:
    beliefs: tuple[Belief, ...] = (
        (Fraction(1), Fraction(0), Fraction(0)),
        (Fraction(0), Fraction(1), Fraction(0)),
        (Fraction(0), Fraction(0), Fraction(1)),
        (Fraction(1, 3), Fraction(1, 3), Fraction(1, 3)),
        (Fraction(1, 2), Fraction(1, 3), Fraction(1, 6)),
    )
    exact = HolonomyPOMDP(Fraction(0))
    erased = HolonomyPOMDP(Fraction(1, 3))
    below = all(exact.equivalent(beliefs[0], b, budget)
                for b in beliefs for budget in range(3))
    above = all(not exact.equivalent(a, b, 3)
                for i, a in enumerate(beliefs) for b in beliefs[i + 1:]
                if a != b)
    erased_all = all(erased.equivalent(a, b, 6)
                     for a in beliefs for b in beliefs)
    return {
        "budgets_below_3_collapse_all_beliefs": below,
        "budget_3_exact_loop_separates_beliefs": above,
        "uniform_noise_erases_all_information": erased_all,
        "noise_channel_determinant_eta_0": channel_determinant(Fraction(0)),
        "noise_channel_determinant_eta_1_over_3": channel_determinant(Fraction(1, 3)),
    }

def _matmul(a: Sequence[Sequence[Fraction]],
            b: Sequence[Sequence[Fraction]]) -> tuple[tuple[Fraction, ...], ...]:
    if not a or not b or len(a[0]) != len(b):
        raise ValueError("incompatible matrix dimensions")
    return tuple(
        tuple(sum(a[i][k] * b[k][j] for k in range(len(b)))
              for j in range(len(b[0])))
        for i in range(len(a))
    )

def posterior_hankel_diagnostics(noise: Fraction) -> dict[str, object]:
    """Exact H=RO and centered balanced-Gram identity for uniform prior."""
    model = HolonomyPOMDP(Fraction(noise))
    prior = (Fraction(1, 3), Fraction(1, 3), Fraction(1, 3))
    r = tuple(model.posterior(prior, y) for y in range(Q))
    o = channel_matrix(Fraction(noise))
    h = _matmul(r, o)
    p = tuple(tuple((Fraction(1) if i == j else Fraction(0)) - Fraction(1, 3)
                    for j in range(Q)) for i in range(Q))
    hc = _matmul(_matmul(p, h), p)
    lam = 1 - 3 * Fraction(noise)
    wc = tuple(tuple(lam**2 * p[i][j] for j in range(Q))
               for i in range(Q))
    wo = wc
    balanced = tuple(tuple(lam**4 * p[i][j] for j in range(Q))
                     for i in range(Q))
    return {
        "R": r, "O": o, "H": h, "centered_H": hc,
        "Wc": wc, "Wo": wo, "balanced_gram": balanced,
        "lambda": lam,
    }

if __name__ == "__main__":
    import json
    print(json.dumps({
        "gauge_audit": exhaustive_gauge_audit(),
        "resource_audit": exhaustive_resource_audit(),
        "hankel_eta_1_over_6": posterior_hankel_diagnostics(Fraction(1, 6)),
        "hankel_eta_1_over_3": posterior_hankel_diagnostics(Fraction(1, 3)),
    }, indent=2, default=str))
