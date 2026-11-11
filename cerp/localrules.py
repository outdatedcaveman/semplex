"""Systematic local learning rules (Spike 10b). UNTRUSTED. Needs `jax`.

What a learning rule may OBSERVE is made explicit, as an observational power in
the sense of THEORY.md. For the first layer of  x -> y = tanh(W x) -> z = v.y + c :

  OMEGA_A = {X, W, Y}            the layer's own input, weights, output
  OMEGA_B = OMEGA_A + {E}        plus the scalar output error, broadcast to every unit
  OMEGA_C = OMEGA_B + {V}        plus the downstream (output) weights

For each power the dictionary is EVERY trace monomial of those variables up to
order K: every way of multiplying up to K of the tensors and contracting all
indices in pairs of equal size (Perin, Anselmi & Deny, arXiv:2611.12248, whose
construction this follows; the enumeration code here is our own). A local loss
is a weighted sum of the monomials; the first layer follows its gradient, with
Y differentiated through and E, V held constant. The output layer always uses
its own (local) delta rule. The weights are meta-learned by differentiating
the final task loss through the unrolled training run.

Backpropagation is in the span of OMEGA_C at order 3: the monomial E * (V . Y)
has first-layer gradient  E * V * (1 - Y^2) x^T , the backpropagated gradient.
"""

from __future__ import annotations

import itertools

import numpy as np

SHAPES = {"X": ("m",), "W": ("d", "m"), "Y": ("d",), "E": (), "V": ("d",)}
POWERS = {"A": ("X", "W", "Y"), "B": ("X", "W", "Y", "E"), "C": ("X", "W", "Y", "E", "V")}


def _pairings(items):
    if not items:
        yield []
        return
    first = items[0]
    for i in range(1, len(items)):
        for rest in _pairings(items[1:i] + items[i + 1:]):
            yield [(first, items[i])] + rest


def _canon(names, edges):
    """Canonical form under reordering of identical tensors."""
    groups = {}
    for i, nm in enumerate(names):
        groups.setdefault(nm, []).append(i)
    best = None
    for perms in itertools.product(*[itertools.permutations(g) for g in groups.values()]):
        mp = {}
        for g, p in zip(groups.values(), perms):
            for a, b in zip(g, p):
                mp[a] = b
        e = tuple(sorted((min(mp[a], mp[b]), max(mp[a], mp[b]), s) for a, b, s in edges))
        if best is None or e < best:
            best = e
    return best


def enumerate_monomials(power, K=4):
    """All distinct trace monomials of order 2..K over the variables of `power`
    that involve W or Y (the others have zero first-layer gradient)."""
    names_all = POWERS[power]
    out, seen = [], set()
    for k in range(2, K + 1):
        for names in itertools.combinations_with_replacement(names_all, k):
            if "W" not in names and "Y" not in names:
                continue
            legs = {}
            for ti, nm in enumerate(names):
                for li, sym in enumerate(SHAPES[nm]):
                    legs.setdefault(sym, []).append((ti, li))
            if any(len(v) % 2 for v in legs.values()):
                continue
            for choice in itertools.product(*[list(_pairings(v)) for v in legs.values()]):
                edges = []
                ok = True
                for sym, pairs in zip(legs, choice):
                    for (t1, _), (t2, _) in pairs:
                        if t1 == t2:
                            ok = False
                        edges.append((t1, t2, sym))
                if not ok:
                    continue
                key = (names, _canon(names, edges))
                if key in seen:
                    continue
                seen.add(key)
                # einsum subscripts: one letter per contracted pair
                subs = [[None] * len(SHAPES[nm]) for nm in names]
                letter = iter("abcdefghijklmnopqrstuvw")
                for sym, pairs in zip(legs, choice):
                    for (t1, l1), (t2, l2) in pairs:
                        ch = next(letter)
                        subs[t1][l1] = ch
                        subs[t2][l2] = ch
                out.append({"names": names, "subs": ["".join(s) for s in subs],
                            "label": "*".join(f"{nm}[{''.join(s)}]" if s else nm for nm, s in zip(names, subs))})
    return out


# ------------------------------------------------------------ training (jax)

def make_trainer(monos, n_inputs, backprop=False, eta_out=0.5, eta_bp=0.5, clip=1.0):
    import jax
    import jax.numpy as jnp

    def mono_val(mn, x, W, y, e, v):
        ops = {"X": x, "W": W, "Y": y, "E": e, "V": v}
        tens = [(ops[nm], s) for nm, s in zip(mn["names"], mn["subs"]) if s]
        val = jnp.einsum(",".join(s for _, s in tens) + "->", *[t for t, _ in tens]) if tens else 1.0
        for nm in mn["names"]:
            if nm == "E":
                val = val * e
        return val

    def local_loss(W, X, care, e, v, coef):
        def per_sample(x, es):
            y = jnp.tanh(W @ x)
            return sum(c * mono_val(mn, x, W, y, es, v) for c, mn in zip(coef, monos))
        vals = jax.vmap(per_sample)(X, e)
        return jnp.sum(vals * care) / jnp.sum(care)

    grad_local = jax.grad(local_loss)

    def step(state, X, t, care, coef):
        W, v, c = state
        y = jnp.tanh(X @ W.T)
        z = y @ v + c
        e = (jax.nn.sigmoid(z) - t) * care
        ncare = jnp.sum(care)
        if backprop:
            gW = ((e[:, None] * v[None, :] * (1 - y * y)).T @ X) / ncare * eta_bp
        else:
            gW = grad_local(W, X, care, jax.lax.stop_gradient(e), jax.lax.stop_gradient(v), coef)
        gW = jnp.clip(gW, -clip, clip)
        return (W - gW, v - eta_out * (e @ y) / ncare, c - eta_out * jnp.sum(e) / ncare)

    def final_loss(state, X, t, care):
        W, v, c = state
        z = jnp.tanh(X @ W.T) @ v + c
        l = jnp.logaddexp(0.0, -z) * t + jnp.logaddexp(0.0, z) * (1 - t)
        return jnp.sum(l * care) / jnp.sum(care)

    def run_one(state, X, t, care, coef, T):
        def body(s, _):
            return step(s, X, t, care, coef), None
        s, _ = jax.lax.scan(body, state, None, length=T)
        return s

    def batch_loss(coef, states, X, ts, cares, T):
        fin = jax.vmap(lambda s, t, c: final_loss(run_one(s, X, t, c, coef, T), X, t, c))(states, ts, cares)
        return jnp.mean(jnp.minimum(fin, 3.0))

    def batch_run(coef, states, X, ts, cares, T):
        return jax.vmap(lambda s, t, c: run_one(s, X, t, c, coef, T))(states, ts, cares)

    return {"loss_and_grad": lambda T: jax.jit(jax.value_and_grad(lambda cf, st, X, ts, cs: batch_loss(cf, st, X, ts, cs, T))),
            "run": lambda T: jax.jit(lambda cf, st, X, ts, cs: batch_run(cf, st, X, ts, cs, T)),
            "grad_local": grad_local}


def inputs_aug(n):
    X = np.array([[(i >> j) & 1 for j in range(n)] for i in range(1 << n)], dtype=np.float32) * 2 - 1
    return np.concatenate([X, np.ones((1 << n, 1), dtype=np.float32)], axis=1)       # last column = bias


def init_states(B, H, n, rng, scale=0.5):
    return (rng.normal(0, scale, (B, H, n + 1)).astype(np.float32),
            rng.normal(0, scale, (B, H)).astype(np.float32), np.zeros(B, dtype=np.float32))


def normalisation(monos, trainer, X, H, n, rng, samples=64):
    """Scale each monomial so its first-layer gradient has unit RMS at initialization."""
    import jax
    import jax.numpy as jnp
    W, v, _ = init_states(samples, H, n, rng)
    e = rng.normal(0, 0.5, (samples, X.shape[0])).astype(np.float32)
    care = jnp.ones(X.shape[0])
    scales = []
    for i in range(len(monos)):
        coef = jnp.zeros(len(monos)).at[i].set(1.0)
        g = jax.vmap(lambda Wi, ei, vi: trainer["grad_local"](Wi, X, care, ei, vi, coef))(W, e, v)
        rms = float(jnp.sqrt(jnp.mean(g ** 2)))
        scales.append(1.0 / rms if rms > 1e-8 else 0.0)
    return np.array(scales, dtype=np.float32)


def meta_learn(monos, trainer, scales, X, targets, cares, H, n, rng, horizons=(10, 25, 50, 100, 200),
               iters=120, batch=64, lr=0.02, l1=1e-4, log=None):
    """Adam on the rule coefficients, differentiating the final loss through training."""
    import jax.numpy as jnp
    a = np.zeros(len(monos), dtype=np.float32)
    m, v2, t = np.zeros_like(a), np.zeros_like(a), 0
    hist = []
    for T in horizons:
        f = trainer["loss_and_grad"](T)
        for _ in range(iters):
            idx = rng.choice(len(targets), batch, replace=False)
            st = init_states(batch, H, n, rng)
            val, g = f(jnp.asarray(a * scales), tuple(map(jnp.asarray, st)), X, targets[idx], cares[idx])
            g = np.asarray(g) * scales + l1 * np.sign(a)
            if not np.all(np.isfinite(g)) or not np.isfinite(float(val)):
                continue
            g = np.clip(g, -1.0, 1.0)
            t += 1
            m = 0.9 * m + 0.1 * g
            v2 = 0.999 * v2 + 0.001 * g * g
            a = a - lr * (m / (1 - 0.9 ** t)) / (np.sqrt(v2 / (1 - 0.999 ** t)) + 1e-8)
        hist.append((T, round(float(val), 4)))
        if log:
            log(f"  horizon {T}: loss {float(val):.4f}")
    return a, hist


def read_states(states, n):
    """(g bits, unit bits) from final states, on all 2^n inputs."""
    W, v, c = (np.asarray(s, dtype=np.float64) for s in states)
    X = inputs_aug(n).astype(np.float64)
    pre = np.einsum("bhm,xm->bxh", W, X)
    z = np.einsum("bxh,bh->bx", np.tanh(pre), v) + c[:, None]
    pw = (1 << np.arange(1 << n)).astype(np.int64)
    return ((z >= 0).astype(np.int64) * pw).sum(-1), ((np.transpose(pre >= 0, (0, 2, 1))).astype(np.int64) * pw).sum(-1)
