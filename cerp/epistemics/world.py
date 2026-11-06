"""Synthetic worlds: the calibration sandbox (charter §11.1).

GROUND TRUTH LIVES HERE. The inquiring agent (cerp/epistemics/inquiry.py)
must never import this module; it only receives an `Interface`, which
exposes the measurement/intervention protocols and nothing else
(enforced by tests/test_epistemics.py::test_agent_has_no_access_to_truth).

The synthetic world is a sandbox, not evidence that natural-world
grounding is solved.

Worlds (observables always A, S1, S2, Y):
  latent_causal       A -> Z;  Z -> S1, S2, Y          (A really acts on Z)
  latent_confounded   Z -> A;  Z -> S1, S2, Y          (A is a symptom of Z)
  copy_chain          A -> S1; S1 -> S2; S1 -> Y       (no latent; S2 copies S1)

latent_causal and latent_confounded are parameterized to have IDENTICAL
observational distributions (verified in tests): no method whatsoever
can tell them apart by passive observation. That is the point.
"""

from __future__ import annotations

import random
from collections import Counter

from .bayesnet import Structure, distribution, regime_key, sample

OBS = ("A", "S1", "S2", "Y")

WORLDS = {
    "latent_causal": (
        Structure("latent_causal", OBS, ("Z",),
                  {"Z": ("A",), "S1": ("Z",), "S2": ("Z",), "Y": ("Z",)}),
        {"A": [0.5], "Z": [0.2, 0.8], "S1": [0.1, 0.9], "S2": [0.15, 0.85], "Y": [0.2, 0.75]},
    ),
    "latent_confounded": (
        Structure("latent_confounded", OBS, ("Z",),
                  {"A": ("Z",), "S1": ("Z",), "S2": ("Z",), "Y": ("Z",)}),
        {"Z": [0.5], "A": [0.2, 0.8], "S1": [0.1, 0.9], "S2": [0.15, 0.85], "Y": [0.2, 0.75]},
    ),
    "copy_chain": (
        Structure("copy_chain", OBS, (),
                  {"S1": ("A",), "S2": ("S1",), "Y": ("S1",)}),
        {"A": [0.5], "S1": [0.25, 0.75], "S2": [0.1, 0.9], "Y": [0.2, 0.75]},
    ),
}

# Worlds outside every hand-written candidate (Spike 02b). Kept separate so
# that Spike 02's experiment (which iterates WORLDS) stays reproducible.
OUTSIDE_WORLDS = {
    "direct_and_latent": (
        Structure("direct_and_latent", OBS, ("Z",),
                  {"Z": ("A",), "S1": ("Z",), "S2": ("Z",), "Y": ("A",)}),
        {"A": [0.5], "Z": [0.2, 0.8], "S1": [0.1, 0.9], "S2": [0.15, 0.85], "Y": [0.25, 0.7]},
    ),
}
_ALL = {**WORLDS, **OUTSIDE_WORLDS}

ALL_ACTIONS = ({}, {"A": 0}, {"A": 1}, {"S1": 0}, {"S1": 1})


class BudgetExceeded(Exception):
    pass


class Interface:
    """What the agent can do: run declared protocols, get counts. Nothing else."""

    def __init__(self, world_name: str, actions=ALL_ACTIONS, seed=0, budget=100_000):
        s, p = _ALL[world_name]
        self.__s, self.__p = s, p
        self.__rng = random.Random(seed)
        self.observables = s.observables
        self.__actions = [dict(a) for a in actions]
        self.budget = budget
        self.spent = 0
        self.log = []  # provenance: (protocol, n)

    def protocols(self):
        return [dict(a) for a in self.__actions]

    def run(self, do: dict, n: int) -> Counter:
        if dict(do) not in self.__actions:
            raise PermissionError(f"protocol do={do} not available in this interface")
        if self.spent + n > self.budget:
            raise BudgetExceeded
        self.spent += n
        self.log.append((regime_key(do), n))
        return sample(self.__s, self.__p, n, self.__rng, do)


# ------------------------------------------------------------ harness-only

def truth(world_name):
    """For the EVALUATION HARNESS only (experiments/, tests/)."""
    return _ALL[world_name]


def true_effect(world_name, do_var, target, delta=0.05):
    """Does intervening on do_var change target's distribution by > delta (TV)?"""
    s, p = _ALL[world_name]
    m = []
    for val in (0, 1):
        d = distribution(s, p, {do_var: val})
        i = s.observables.index(target)
        m.append(sum(pr for c, pr in d.items() if c[i] == 1))
    return abs(m[0] - m[1]) > delta
