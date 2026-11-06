import random

import pytest

from cerp.substrates import random_expr

VARS4 = ["a", "b", "c", "d"]
VARS6 = ["a", "b", "c", "d", "e", "f"]


def random_exprs(n, vars, depth=5, seed=0):
    rng = random.Random(seed)
    return [{"kind": "expr", "body": random_expr(vars, depth, rng)} for _ in range(n)]


@pytest.fixture
def exprs6():
    return random_exprs(150, VARS6, seed=1)
