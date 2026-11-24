"""Modular addition, many small MLPs trained in parallel (Spike 15). UNTRUSTED.

Model (one per batch index): logits(a, b) = U . relu(E1[a] + E2[b]),  E1, E2: (p, h), U: (h, p).
Tokens are one-hot and unstructured, so any permutation of Z_p applied jointly to inputs and
outputs is a symmetry of the initialization law and of the architecture. For the task a + b,
the automorphisms a -> u a (u a unit) map the task to itself, so (Theorem 15 analogue) the law of
the learned mechanism is invariant under them.

Mechanism readout: the Fourier spectrum of each hidden unit's input weights; a unit's frequency
is its dominant k in 1..(p-1)/2 (k and -k merged); the key set S is the set of frequencies that
carry at least `share` of the total first-layer Fourier power.
"""

from __future__ import annotations

import numpy as np
import torch


def data(p, frac=1.0, seed=0):
    a, b = np.meshgrid(np.arange(p), np.arange(p), indexing="ij")
    a, b = a.ravel(), b.ravel()
    y = (a + b) % p
    idx = np.random.default_rng(seed).permutation(p * p)[: int(round(frac * p * p))]
    return torch.tensor(a[idx]), torch.tensor(b[idx]), torch.tensor(y[idx])


def init(B, p, h, seed, scale=1.0):
    g = torch.Generator().manual_seed(seed)
    s1 = scale / np.sqrt(1.0)
    return {"E1": (torch.randn(B, p, h, generator=g) * s1).requires_grad_(),
            "E2": (torch.randn(B, p, h, generator=g) * s1).requires_grad_(),
            "U": (torch.randn(B, h, p, generator=g) * scale / np.sqrt(h)).requires_grad_()}


def logits(P, a, b):
    hdn = torch.relu(P["E1"][:, a, :] + P["E2"][:, b, :])          # (B, N, h)
    return torch.bmm(hdn, P["U"])                                     # (B, N, p)


def train(P, a, b, y, steps, lr=1e-3, wd=1.0, log=None):
    opt = torch.optim.AdamW(list(P.values()), lr=lr, weight_decay=wd, betas=(0.9, 0.98))
    B = P["U"].shape[0]
    for t in range(steps):
        opt.zero_grad()
        z = logits(P, a, b)
        loss = torch.nn.functional.cross_entropy(z.reshape(-1, z.shape[-1]), y.repeat(B)) * B
        loss.backward()
        opt.step()
        if log and (t + 1) % log == 0:
            with torch.no_grad():
                acc = (z.argmax(-1) == y).float().mean(1)
            print(t + 1, round(loss.item() / B, 4), "acc", round(acc.mean().item(), 3), flush=True)
    return P


@torch.no_grad()
def accuracy(P, p):
    a, b, y = data(p)
    return (logits(P, a, b).argmax(-1) == y).float().mean(1).numpy()


@torch.no_grad()
def spectrum(P):
    """Per model: Fourier power of first-layer weights by frequency k = 1..(p-1)/2 (k, -k merged)."""
    E = torch.cat([P["E1"], P["E2"]], dim=2)                          # (B, p, 2h)
    p = E.shape[1]
    F = torch.fft.fft(E - E.mean(1, keepdim=True), dim=1).abs() ** 2  # (B, p, 2h)
    K = (p - 1) // 2
    pw = F[:, 1:K + 1, :] + F[:, p - K:, :].flip(1)                   # merge k and p-k
    return pw.sum(2).numpy()                                          # (B, K), index k-1


def key_set(power, share=0.9):
    """Smallest set of frequencies carrying >= share of the total power."""
    order = np.argsort(-power)
    c = np.cumsum(power[order]) / power.sum()
    m = int(np.searchsorted(c, share)) + 1
    return frozenset(int(k) + 1 for k in order[:m])
