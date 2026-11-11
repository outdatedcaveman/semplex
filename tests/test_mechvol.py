"""Spike 11: isomer enumeration and the volume predictor."""

import numpy as np
import pytest

from cerp import atlas, mechvol, train

v = lambda j: sum(1 << x for x in range(16) if (x >> j) & 1)


@pytest.fixture(scope="module")
def tb():
    return atlas.build_all(4)[4]


def test_isomers_are_exactly_the_minimal_layers(tb):
    pidx = mechvol.PairIndex(tb.ltf)
    for g in ((v(0) & v(1)) | (v(2) & v(3)), v(0) ^ v(1), (v(0) & v(1)) ^ v(2)):
        iso = pidx.isomers(g)
        w, k = atlas.min_determining_layers(tb, g)
        assert w == 2 and len(iso) == k
        assert all(train.determines(q, g) for q in iso)
    g = (v(0) & v(1)) | (v(2) & v(3))
    want = tuple(sorted(int(mechvol.canon(t)) for t in (v(0) & v(1), v(2) & v(3))))
    assert want in set(pidx.isomers(g))


def test_solid_angles_are_a_distribution_with_the_right_symmetry():
    om, n = mechvol.solid_angles(400_000, np.random.default_rng(0))
    assert abs(sum(om.values()) - 1) < 1e-9
    singles = [om[mechvol.canon(v(j)).item()] for j in range(4)]           # single variables: equal by symmetry
    assert max(singles) - min(singles) < 0.01


def test_score_rewards_the_truth_and_not_uniform():
    pred = {"a": 0.7, "b": 0.2, "c": 0.1}
    obs = {"a": 70, "b": 20, "c": 10}
    s = mechvol.score(obs, pred)
    assert s["gain_bits"] > 0.2 and s["top1"] and s["spearman"] > 0.99
    u = mechvol.score(obs, {k: 1 / 3 for k in pred})
    assert abs(u["gain_bits"]) < 1e-12
    wrong = mechvol.score(obs, {"a": 0.1, "b": 0.2, "c": 0.7})                # mutation: reversed predictor
    assert wrong["gain_bits"] < 0 and not wrong["top1"]


def test_minimal_pairs_reads_every_determining_pair():
    g = (v(0) & v(1)) | (v(2) & v(3))
    units = [v(0) & v(1), v(2) & v(3), 0xFFFF ^ (v(2) & v(3)), v(1)]
    assert len(mechvol.minimal_pairs(units, g)) == 1
