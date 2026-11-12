"""Exact maximum likelihood for log-linear choice models (convex): Newton's method with backtracking.

Model: for each group e, P(i | e) ∝ exp(F_e[i] · θ) over the group's choices i; counts C_e[i].
Negative log-likelihood is convex in θ, so Newton converges to the global optimum.
Replaces Nelder-Mead fits, which stalled at spurious points in Spike 21's first analysis.
"""

from __future__ import annotations

import numpy as np


def _terms(theta, groups):
    nll, g, H = 0.0, np.zeros_like(theta), np.zeros((len(theta), len(theta)))
    for C, F in groups:
        N = C.sum()
        if N == 0:
            continue
        s = F @ theta; m = s.max(); w = np.exp(s - m); Z = w.sum(); p = w / Z
        nll += N * (m + np.log(Z)) - C @ s
        mu = p @ F
        g += N * mu - C @ F
        H += N * ((F * p[:, None]).T @ F - np.outer(mu, mu))
    return nll, g, H


def fit(groups, k, theta0=None, tol=1e-9, maxit=100):
    """groups: iterable of (counts (n,), features (n, k)). Returns (theta, nll)."""
    groups = [(np.asarray(C, float), np.asarray(F, float)) for C, F in groups]
    th = np.zeros(k) if theta0 is None else np.asarray(theta0, float)
    f, g, H = _terms(th, groups)
    for _ in range(maxit):
        step = np.linalg.solve(H + 1e-10 * np.eye(k), g)
        t = 1.0
        while True:
            nt = th - t * step
            nf, ng, nH = _terms(nt, groups)
            if nf <= f + 1e-12 or t < 1e-8:
                break
            t /= 2
        done = abs(f - nf) < tol * (1 + abs(f))
        th, f, g, H = nt, nf, ng, nH
        if done:
            break
    return th, f
