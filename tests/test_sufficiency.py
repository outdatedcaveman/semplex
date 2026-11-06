"""Layer H: task-relative minimal sufficient sets."""

import itertools
import random

from cerp import kernel
from cerp.semantics import TruthTable
from cerp.substrates import semantics
from cerp.sufficiency import (insufficiency_witness, minimal_sufficient_sets, project,
                              report)
from cerp.translate import truthtable_to_bdd

from .conftest import VARS6, random_exprs


def brute_force_minimal(f, care):
    """Reference implementation straight from the definition."""
    def sufficient(s):
        seen = {}
        for i in care.ones():
            env = f.env(i)
            key = tuple(env[v] for v in s)
            if seen.setdefault(key, f.at(i)) != f.at(i):
                return False
        return True

    suff = [frozenset(s) for k in range(f.n + 1) for s in itertools.combinations(f.vars, k) if sufficient(s)]
    return {s for s in suff if not any(t < s for t in suff)}


def test_matches_definition_on_random_tasks():
    rng = random.Random(11)
    V = ["a", "b", "c", "d", "e"]
    for e in random_exprs(80, V, depth=5, seed=5):
        f = semantics(e, V)
        care = TruthTable(tuple(V), rng.getrandbits(32))
        assert set(minimal_sufficient_sets(f, care)) == brute_force_minimal(f, care)


def test_full_care_gives_unique_minimal_set_equal_to_support(exprs6):
    """Proposition in cerp/sufficiency.py, tested on random functions."""
    for e in exprs6:
        f = semantics(e, VARS6)
        sets = minimal_sufficient_sets(f)
        assert sets == [f.support()]


def test_restricted_care_can_give_incomparable_minimal_sets():
    V = ["a", "b", "c", "d"]
    f = TruthTable.from_function(V, lambda x: (x["a"] & x["c"]) | (x["b"] & x["d"]))
    care = TruthTable.from_function(V, lambda x: x["a"] == x["b"])
    r = report(f, care)
    assert r["minimal_sufficient_sets"] == [["a", "c", "d"], ["b", "c", "d"]]
    assert r["necessary"] == ["c", "d"] and r["substitutable"] == ["a", "b"]


def test_projection_is_kernel_verified_and_witnesses_check():
    rng = random.Random(2)
    V = ["a", "b", "c", "d", "e"]
    for e in random_exprs(40, V, depth=5, seed=9):
        f = semantics(e, V)
        care = TruthTable(tuple(V), rng.getrandbits(32))
        care_art = truthtable_to_bdd(care)
        for s in minimal_sufficient_sets(f, care):
            g = truthtable_to_bdd(project(f, care, s))
            assert kernel.check({"relation": "task", "vars": V, "left": e, "right": g, "care": care_art}).ok
            for x in s:
                w = insufficiency_witness(f, care, s - {x})
                assert w is not None
                assert kernel.check_insufficiency({"vars": V, "f": e, "care": care_art,
                                                   "subset": sorted(s - {x}), "x": w[0], "y": w[1]}).ok


def test_restrict_agrees_with_f_on_care():
    from cerp.translate import restrict_to_care
    rng = random.Random(4)
    V = ["a", "b", "c", "d", "e"]
    for e in random_exprs(60, V, depth=5, seed=12):
        f = semantics(e, V)
        care = TruthTable(tuple(V), rng.getrandbits(32) | 1)  # non-empty
        r = restrict_to_care(f, care)
        assert kernel.check({"relation": "task", "vars": V, "left": e, "right": r,
                             "care": truthtable_to_bdd(care)}).ok
