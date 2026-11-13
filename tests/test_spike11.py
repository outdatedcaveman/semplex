"""Fast sanity tests for Spike 11 (H-B and H-D helpers)."""

from experiments.spike11_hb_hd import _determines_n, _effective_width_n, _pearson, _spearman


def test_determines_and_effective_width_n3():
    # XOR on 3 inputs (x0 ^ x1) = bits 0b01100110 = 0x66
    xor01 = sum(1 << x for x in range(8) if ((x >> 0) ^ (x >> 1)) & 1)
    x0 = sum(1 << x for x in range(8) if (x >> 0) & 1)
    x1 = sum(1 << x for x in range(8) if (x >> 1) & 1)
    assert _determines_n((x0, x1), xor01, 8)
    assert not _determines_n((x0,), xor01, 8)
    w, iso = _effective_width_n([x0, x1, x0], xor01, 8)
    assert w == 2 and len(iso) == 2


def test_correlations():
    assert _spearman([1, 2, 3, 4], [10, 20, 30, 40]) == 1.0
    assert abs(_pearson([1, 2, 3], [2, 4, 6]) - 1.0) < 1e-12


def test_localrules_embed_coefficients():
    from cerp import localrules as L
    src = L.enumerate_monomials("C", 3, "O")
    dst = L.enumerate_monomials("C", 4, "O")
    coef = [float(i + 1) for i in range(len(src))]
    emb = L.embed_coefficients(src, coef, dst)
    assert len(emb) == len(dst)
    by_lbl = {m["label"]: float(v) for m, v in zip(dst, emb)}
    for m, c in zip(src, coef):
        assert by_lbl[m["label"]] == c

