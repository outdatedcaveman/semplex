"""Small, dependency-free statistics used by the inquiry loop."""

from __future__ import annotations

import math
from statistics import NormalDist


def _gser(a, x):
    s = term = 1.0 / a
    n = a
    for _ in range(1000):
        n += 1
        term *= x / n
        s += term
        if abs(term) < abs(s) * 1e-15:
            break
    return s * math.exp(-x + a * math.log(x) - math.lgamma(a))


def _gcf(a, x):
    tiny = 1e-300
    b = x + 1 - a
    c = 1 / tiny
    d = 1 / b
    h = d
    for i in range(1, 1000):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        d = tiny if abs(d) < tiny else d
        c = b + an / c
        c = tiny if abs(c) < tiny else c
        d = 1 / d
        h *= d * c
        if abs(d * c - 1) < 1e-15:
            break
    return math.exp(-x + a * math.log(x) - math.lgamma(a)) * h


def chi2_sf(x: float, df: int) -> float:
    """P(chi2_df > x)."""
    if math.isinf(x):
        return 0.0
    if x <= 0:
        return 1.0
    a, y = df / 2.0, x / 2.0
    return 1.0 - _gser(a, y) if y < a + 1 else _gcf(a, y)


def g_test(counts: dict, probs: dict):
    """Goodness of fit of observed counts to a FIXED predicted distribution
    (no parameters estimated on these counts). Returns (G, df, p)."""
    n = sum(counts.values())
    g = 0.0
    for cell, k in counts.items():
        p = probs.get(cell, 0.0)
        if p <= 0:
            return math.inf, None, 0.0
        g += 2 * k * math.log(k / (n * p))
    df = sum(1 for p in probs.values() if p > 0) - 1
    return g, df, chi2_sf(g, max(df, 1))


def paired_log_score(counts: dict, pa: dict, pb: dict):
    """Per-sample log-score difference a - b on fresh data: (mean, se, z)."""
    n = sum(counts.values())
    diffs = []
    for cell, k in counts.items():
        la = math.log(pa[cell]) if pa.get(cell, 0) > 0 else -math.inf
        lb = math.log(pb[cell]) if pb.get(cell, 0) > 0 else -math.inf
        if math.isinf(la) or math.isinf(lb):
            if la == lb:
                d = 0.0
            else:
                return (math.inf if la > lb else -math.inf), 0.0, (math.inf if la > lb else -math.inf)
        else:
            d = la - lb
        diffs.append((d, k))
    mean = sum(d * k for d, k in diffs) / n
    var = sum(k * (d - mean) ** 2 for d, k in diffs) / max(n - 1, 1)
    se = math.sqrt(var / n)
    if se == 0:
        return mean, 0.0, 0.0 if mean == 0 else math.copysign(math.inf, mean)
    return mean, se, mean / se


def z_two_sided(alpha: float) -> float:
    return NormalDist().inv_cdf(1 - alpha / 2)


def entropy(p: dict) -> float:
    return -sum(v * math.log(v) for v in p.values() if v > 0)


def kl(p: dict, q: dict) -> float:
    out = 0.0
    for c, pv in p.items():
        if pv > 0:
            qv = q.get(c, 0.0)
            if qv <= 0:
                return math.inf
            out += pv * math.log(pv / qv)
    return out
