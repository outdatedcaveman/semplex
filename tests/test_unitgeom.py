"""Spike 13: unit margins and integer weight cost."""

import math

from cerp import unitgeom

v = lambda j: sum(1 << x for x in range(16) if (x >> j) & 1)


def test_single_variable_and_and4():
    assert abs(unitgeom.margin_l2(v(0)) - 1) < 1e-6
    assert abs(unitgeom.margin_linf(v(0)) - 1) < 1e-6
    assert unitgeom.int_cost(v(0)) == 2                       # x0 >= 1
    and4 = v(0) & v(1) & v(2) & v(3)
    assert abs(unitgeom.margin_l2(and4) - 1 / math.sqrt(13)) < 1e-4
    assert abs(unitgeom.margin_linf(and4) - 1 / 3) < 1e-6
    assert unitgeom.int_cost(and4) == 8                       # x0+x1+x2+x3 >= 4


def test_margins_are_complement_invariant_and_ordered():
    t = (v(0) & v(1)) | v(2)
    assert abs(unitgeom.margin_l2(t) - unitgeom.margin_l2(0xFFFF ^ t)) < 1e-6
    assert abs(unitgeom.margin_linf(t) - unitgeom.margin_linf(0xFFFF ^ t)) < 1e-6
    # l_inf margin >= l2 margin / sqrt(5) and <= l2 margin * ... (norm equivalence in R^5)
    m2, mi = unitgeom.margin_l2(t), unitgeom.margin_linf(t)
    assert m2 / math.sqrt(5) - 1e-9 <= mi * 1 and mi <= m2 * math.sqrt(5) + 1e-9
