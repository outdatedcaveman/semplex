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
