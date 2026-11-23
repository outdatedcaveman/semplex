"""Exact rational counterexample: forward predictive congruence need not be Wc-invariant.

This test implements the MasterPrinciple pastOp_1 recurrence for a four-state,
three-action deterministic system. It uses Fraction throughout: no floating
point, NumPy, or external dependencies.
"""
from fractions import Fraction


STATES = ("A0", "A1", "B0", "B1")
ACTIONS = {
    "a": {"A0": "A0", "A1": "A0", "B0": "A0", "B1": "A1"},
    "b": {"A0": "B0", "A1": "B1", "B0": "B0", "B1": "B1"},
    "c": {"A0": "A1", "A1": "A0", "B0": "B1", "B1": "B0"},
}
PI = {
    "A0": Fraction(7, 22),
    "A1": Fraction(4, 22),
    "B0": Fraction(6, 22),
    "B1": Fraction(5, 22),
}
BLOCK = {"A0": "A", "A1": "A", "B0": "B", "B1": "B"}
F = {
    "A0": Fraction(1, 2),
    "A1": Fraction(1, 2),
    "B0": Fraction(-1, 2),
    "B1": Fraction(-1, 2),
}
EXPECTED_PAST_OP_1 = {
    "A0": Fraction(17, 42),
    "A1": Fraction(5, 24),
    "B0": Fraction(-13, 36),
    "B1": Fraction(-3, 10),
}


def weighted_adjoint(action, values):
    """T_a^* g(r) = pi(r)^-1 sum_{q: delta_a(q)=r} pi(q) g(q)."""
    delta = ACTIONS[action]
    return {
        r: sum(
            (PI[q] * values[q] for q in STATES if delta[q] == r),
            Fraction(0),
        ) / PI[r]
        for r in STATES
    }


def past_op_one(values):
    """pastOp_1 f = average_a T_a^* ( <1,T_a f>_pi * 1 )."""
    result = {q: Fraction(0) for q in STATES}
    for action, delta in ACTIONS.items():
        scalar = sum((PI[q] * values[delta[q]] for q in STATES), Fraction(0))
        constant = {q: scalar for q in STATES}
        adjoint_value = weighted_adjoint(action, constant)
        for q in STATES:
            result[q] += adjoint_value[q] / len(ACTIONS)
    return result


def test_pi_is_full_support_and_stationary_for_uniform_actions():
    assert all(PI[q] > 0 for q in STATES)
    assert sum(PI.values(), Fraction(0)) == 1
    for target in STATES:
        incoming = sum(
            (
                PI[source] / len(ACTIONS)
                for action in ACTIONS
                for source in STATES
                if ACTIONS[action][source] == target
            ),
            Fraction(0),
        )
        assert incoming == PI[target]


def test_partition_is_forward_transition_congruence():
    for action in ACTIONS:
        for x in STATES:
            for y in STATES:
                if BLOCK[x] == BLOCK[y]:
                    assert BLOCK[ACTIONS[action][x]] == BLOCK[ACTIONS[action][y]]


def test_past_reachability_operator_leaves_forward_semantic_algebra():
    # f is centered and block-constant.
    assert sum((PI[q] * F[q] for q in STATES), Fraction(0)) == 0
    assert F["A0"] == F["A1"]
    assert F["B0"] == F["B1"]

    actual = past_op_one(F)
    assert actual == EXPECTED_PAST_OP_1

    # The result remains centered, so P_perp does not remove the leakage.
    assert sum((PI[q] * actual[q] for q in STATES), Fraction(0)) == 0

    # But it is no longer block-constant.
    assert actual["A0"] != actual["A1"]
    assert actual["B0"] != actual["B1"]


def test_reverse_lumpability_fails_for_action_a():
    def kappa(action, target, source_block):
        return sum(
            (
                PI[q]
                for q in STATES
                if BLOCK[q] == source_block and ACTIONS[action][q] == target
            ),
            Fraction(0),
        ) / PI[target]

    # Same target block A, same source block A, unequal reverse weights.
    assert kappa("a", "A0", "A") == Fraction(11, 7)
    assert kappa("a", "A1", "A") == Fraction(0)
    assert kappa("a", "A0", "A") != kappa("a", "A1", "A")
