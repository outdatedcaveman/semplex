"""Partial-function not-threshold certificates (Spike 35): sound on don't-cares."""
from cerp import bounds, kernel_bounds

N = 2
XOR = 0b0110                       # points 01, 10 true; 00, 11 false
ALL = 0b1111


def test_xor_certified_when_fully_specified():
    c = bounds.not_threshold_cert_partial(N, XOR, ALL)
    assert c and kernel_bounds.check_not_threshold_partial(N, XOR, ALL, c["pos"], c["neg"]).ok


def test_no_certificate_when_a_dont_care_makes_it_threshold():
    care = 0b0111                  # point 11 unlabelled: completion 0b1110 = OR is threshold
    assert bounds.not_threshold_cert_partial(N, XOR & care, care) is None


def test_kernel_rejects_certificate_using_a_dont_care():
    care = 0b0111
    # the total-function certificate for XOR uses point 3 (11) as a negative: invalid here
    assert not kernel_bounds.check_not_threshold_partial(N, XOR & care, care, [1, 2], [0, 3]).ok


def test_total_search_is_unsound_on_masked_tables():
    care = 0b0111
    # documents the Spike 35 bug: treating don't-cares as 0 yields a (wrong) certificate
    assert bounds.not_threshold_cert(N, XOR & care) is not None


def test_netsolve_min_errors_and_budget():
    """A single threshold unit cannot compute XOR on 2 inputs; its best fit misses exactly 1 of 4 points."""
    from cerp import kernel, netsolve
    f, n = 0b0110, 2
    spec = netsolve.layered(n, [])
    assert netsolve.solve(f, n, spec, W=2, time_limit=10)[0] == "unsat"
    st, art = netsolve.solve(f, n, spec, W=2, time_limit=10, min_errors=True)
    assert st == "optimal"
    wrong = sum(int(kernel.evaluate(art, {"x0": x & 1, "x1": x >> 1})) != (f >> x) & 1 for x in range(4))
    assert wrong == 1
    assert netsolve.solve(f, n, spec, W=2, time_limit=10, max_errors=0)[0] == "unsat"
    assert netsolve.solve(f, n, spec, W=2, time_limit=10, max_errors=1)[0] == "sat"


def test_not_two_halfspaces_partial_and_forgeries():
    from cerp import bounds, kernel_bounds
    import pytest

    # 3-bit parity requires >= 3 halfspaces (neither 2-AND nor 2-OR works on all 8 inputs)
    n, parity3, full = 3, 0b10010110, 0xFF
    bad_pos = bounds.not_two_halfspaces_cert_partial(n, parity3, full)
    bad_neg = bounds.not_two_halfspaces_cert_partial(n, (~parity3) & full, full)
    assert bad_pos is not None and bad_neg is not None
    assert kernel_bounds.check_not_two_halfspaces_partial(n, parity3, full, bad_pos).ok
    assert kernel_bounds.check_not_two_halfspaces_partial(n, (~parity3) & full, full, bad_neg).ok

    # Drop one used point from care -> forged care set must fail verification
    used_pt = bad_pos[0]["set"][0]
    assert not kernel_bounds.check_not_two_halfspaces_partial(n, parity3, full ^ (1 << used_pt), bad_pos).ok
    # Empty bad list allows trivial colouring -> must fail
    assert not kernel_bounds.check_not_two_halfspaces_partial(n, parity3, full, []).ok
    # Parity3 without input 0 IS an OR of two halfspaces (sum<=1 or sum>=3 on nonzero inputs)
    assert bounds.not_two_halfspaces_cert_partial(n, (~parity3) & 0xFE, 0xFE) is None
    with pytest.raises(kernel_bounds.KernelError):
        kernel_bounds.check_not_two_halfspaces_partial(n, parity3, -1, bad_pos)


def test_not_threshold_partial_lp_n8():
    import random
    from cerp import bounds, kernel_bounds

    n = 8
    K = 1 << n
    rng = random.Random(1234)
    pts = rng.sample(range(K), int(round(0.75 * K)))
    care = sum(1 << x for x in pts)

    # Linearly separable threshold function on n=8: sum(x_i) >= 4
    f_sep = sum((1 << x) for x in range(K) if x.bit_count() >= 4)
    assert bounds.not_threshold_cert_partial(n, f_sep & care, care) is None

    # Non-threshold function on n=8: x0 XOR x1
    f_xor = sum((1 << x) for x in range(K) if ((x & 1) ^ ((x >> 1) & 1)))
    wit = bounds.not_threshold_cert_partial(n, f_xor & care, care)
    assert wit is not None
    assert kernel_bounds.check_not_threshold_partial(n, f_xor & care, care, wit["pos"], wit["neg"]).ok


def test_compile_partial_n4_and_n8():
    import random
    from cerp import kernel, netsolve

    # 1. n=4 cost-1 threshold target (75% care)
    n4 = 4
    care4 = 0b1110_1101_1011_0111
    f4_lin = sum((1 << x) for x in range(16) if x.bit_count() >= 2)
    r1 = netsolve.compile_partial(f4_lin, n4, care4, W=3, time_limit=15.0, workers=2)
    assert r1["status"] == "sat" and r1["cost"] == 1 and r1["certified_minimal"]
    for x in range(16):
        if (care4 >> x) & 1:
            assert int(kernel.evaluate(r1["artifact"], {f"x{i}": (x >> i) & 1 for i in range(n4)})) == ((f4_lin >> x) & 1)

    # 2. n=4 cost-4 parity3 lifted to x0..x2 (not 2-halfspaces, width-3 solves it)
    f4_par = sum((1 << x) for x in range(16) if (x & 7).bit_count() % 2 == 1)
    r4 = netsolve.compile_partial(f4_par, n4, 0xFFFF, W=3, max_width=4, time_limit=20.0, workers=2)
    assert r4["status"] == "sat" and r4["cost"] == 4 and r4["certified_minimal"]
    assert r4["lower_bound"] == 4 and r4["cert_kind"] == "not-two-halfspaces-partial"
    for x in range(16):
        assert int(kernel.evaluate(r4["artifact"], {f"x{i}": (x >> i) & 1 for i in range(n4)})) == ((f4_par >> x) & 1)

    # 3. n=8 cost-3 2-halfspace AND target with 75% care
    n8 = 8
    K8 = 1 << n8
    rng = random.Random(42)
    care8 = sum(1 << x for x in rng.sample(range(K8), 192))
    f8 = sum(
        (1 << x)
        for x in range(K8)
        if (2 * ((x >> 0) & 1) - ((x >> 1) & 1) + ((x >> 2) & 1) + ((x >> 3) & 1) >= 2)
        and (-((x >> 4) & 1) + 2 * ((x >> 5) & 1) + ((x >> 6) & 1) - ((x >> 7) & 1) >= 1)
    )
    r8 = netsolve.compile_partial(f8, n8, care8, W=4, time_limit=30.0, workers=4)
    assert r8["status"] == "sat" and r8["cost"] in (1, 3) and r8["certified_minimal"]
    for x in range(K8):
        if (care8 >> x) & 1:
            assert int(kernel.evaluate(r8["artifact"], {f"x{i}": (x >> i) & 1 for i in range(n8)})) == ((f8 >> x) & 1)


def test_solve_three_halfspaces_all_gates_and_w1():
    from cerp import kernel, netsolve

    n = 4
    K = 1 << n

    def truth_table(fn):
        return sum((1 << x) for x in range(K) if fn((x >> 0) & 1, (x >> 1) & 1, (x >> 2) & 1, (x >> 3) & 1))

    def check_sol(f, W, care=None):
        st, art = netsolve.solve(f, n, netsolve.layered(n, [3]), W=W, time_limit=15.0, workers=2, care=care)
        assert st == "sat"
        for x in range(K):
            if care is None or ((care >> x) & 1):
                assert int(kernel.evaluate(art, {f"x{i}": (x >> i) & 1 for i in range(n)})) == ((f >> x) & 1)

    # All three W=1-representable 3-input threshold gates (AND3, OR3, MAJ3)
    f_and3 = truth_table(lambda x0, x1, x2, x3: (x0 + x1 >= 2) and (x2 + x3 <= 0) and (x0 + x3 >= 1))
    f_or3 = truth_table(lambda x0, x1, x2, x3: (x0 + x1 >= 2) or (x2 + x3 >= 2) or (x0 - x3 >= 1))
    f_maj3 = truth_table(
        lambda x0, x1, x2, x3: ((x0 + x1 >= 2) + (x2 + x3 >= 2) + (x0 + x2 - x1 - x3 >= 1)) >= 2
    )
    check_sol(f_and3, W=1)
    check_sol(f_or3, W=1)
    check_sol(f_maj3, W=1)

    # W=2-only 3-input threshold gates (OR-AND, AND-OR)
    f_or_and = truth_table(lambda x0, x1, x2, x3: (x0 + x1 + x2 + x3 >= 3) or ((x0 - x1 >= 1) and (x2 - x3 >= 1)))
    f_and_or = truth_table(lambda x0, x1, x2, x3: (x0 - x1 + x2 >= 2) and ((x0 + x3 >= 2) or (x1 + x2 <= 0)))
    check_sol(f_or_and, W=2)
    check_sol(f_and_or, W=2)

    # Partial care mask preserves care agreement
    care = sum(1 << x for x in range(0, K, 2)) | (1 << 1) | (1 << 15)
    check_sol(f_and_or, W=2, care=care)


def test_compile_partial_cost4_certification_and_fields():
    import random
    from cerp import kernel, kernel_bounds, netsolve

    # n=3 parity3 requires 3 hidden units (cost 4) and has valid not-two-halfspaces certs
    n3 = 3
    K3 = 1 << n3
    care3 = (1 << K3) - 1
    f_par3 = sum((1 << x) for x in range(K3) if bin(x).count("1") % 2 == 1)
    r3 = netsolve.compile_partial(f_par3, n3, care3, W=3, max_width=4, time_limit=20.0, workers=2)
    assert r3["status"] == "sat"
    assert r3["cost"] == 4
    assert r3["lower_bound"] == 4
    assert r3["certified_minimal"] is True
    assert r3["cert_kind"] == "not-two-halfspaces-partial"
    assert r3["cost3_status"] == "certified_impossible"
    assert r3["cost3_solver_unsat"] is False
    assert kernel_bounds.check_not_two_halfspaces_partial(
        n3, f_par3, care3, r3["certs"]["not_two_halfspaces_pos"]
    ).ok
    assert kernel_bounds.check_not_two_halfspaces_partial(
        n3, (~f_par3) & care3, care3, r3["certs"]["not_two_halfspaces_neg"]
    ).ok
    for x in range(K3):
        assert int(kernel.evaluate(r3["artifact"], {f"x{i}": (x >> i) & 1 for i in range(n3)})) == ((f_par3 >> x) & 1)

    # n=6 disjoint 3-OR on partial care (90% of table) certifies cost 4
    n6 = 6
    K6 = 1 << n6
    rng = random.Random(101)
    care6 = sum(1 << x for x in rng.sample(range(K6), 58))
    f6 = sum(
        (1 << x)
        for x in range(K6)
        if (((x >> 0) & 1) and ((x >> 1) & 1))
        or (((x >> 2) & 1) and ((x >> 3) & 1))
        or (((x >> 4) & 1) and ((x >> 5) & 1))
    )
    r6 = netsolve.compile_partial(f6, n6, care6, W=4, max_width=4, time_limit=30.0, workers=2)
    assert r6["status"] == "sat"
    assert r6["cost"] == 4
    assert r6["lower_bound"] == 4
    assert r6["certified_minimal"] is True
    assert r6["cost3_status"] == "certified_impossible"
    assert r6["cost3_solver_unsat"] is False
    assert "not_two_halfspaces_pos" in r6["certs"] and "not_two_halfspaces_neg" in r6["certs"]
    for x in range(K6):
        if (care6 >> x) & 1:
            assert int(kernel.evaluate(r6["artifact"], {f"x{i}": (x >> i) & 1 for i in range(n6)})) == ((f6 >> x) & 1)


