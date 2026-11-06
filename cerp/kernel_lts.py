"""Trusted kernel extension for fragment F1: finite labelled transition systems.

Same rules as cerp/kernel.py: stdlib only, no imports from the rest of
cerp (tests enforce it), and every judgment is a cheap CHECK of a
certificate produced by untrusted search in cerp/lts.py.

Artifact:  {"kind": "lts", "body": {"init": s, "trans": [[s, action, t], ...],
                                     "states": [...]}}   (states optional)

Judgments (each returns a Verdict minted by cerp.kernel's token):
  bisimulation(P, Q, relation)         relation is a bisimulation containing (init_P, init_Q)
  distinguishing_formula(P, Q, phi)    HML formula phi holds at init_P and fails at init_Q
  trace_cert(P, Q, pairs, completed)   pairs of state-SETS closed under every action,
                                       starting from ({init_P}, {init_Q}), agreeing on
                                       emptiness (and, if completed, on deadlock)
  trace_witness(P, Q, trace, completed) trace (completed: ending in deadlock) is possible
                                       in P and impossible in Q
"""

from __future__ import annotations

from .kernel import KERNEL_VERSION, KernelError, Verdict, _TOKEN

MAX_STATES = 10_000


def _succ(lts):
    b = lts["body"]
    if lts.get("kind") != "lts":
        raise KernelError("not an lts artifact")
    out = {}
    for s, a, t in b["trans"]:
        out.setdefault(s, {}).setdefault(a, set()).add(t)
    states = set(b.get("states", [])) | {b["init"]} | set(out)
    states |= {t for d in out.values() for ts in d.values() for t in ts}
    if len(states) > MAX_STATES:
        raise KernelError("lts too large")
    return out, states


def _post(succ, X, a):
    return frozenset(t for s in X for t in succ.get(s, {}).get(a, ()))


def _deadlocked(succ, s):
    return not succ.get(s)


def _verdict(ok, rel, n):
    return Verdict(bool(ok), rel, (), n, None, KERNEL_VERSION, _TOKEN)


def check_bisimulation(P, Q, relation) -> Verdict:
    sp, _ = _succ(P)
    sq, _ = _succ(Q)
    R = {tuple(x) for x in relation}
    ok = (P["body"]["init"], Q["body"]["init"]) in R
    for p, q in R:
        if not ok:
            break
        for a, ps in sp.get(p, {}).items():
            qs = sq.get(q, {}).get(a, set())
            if not all(any((p2, q2) in R for q2 in qs) for p2 in ps):
                ok = False
        for a, qs in sq.get(q, {}).items():
            ps = sp.get(p, {}).get(a, set())
            if not all(any((p2, q2) in R for p2 in ps) for q2 in qs):
                ok = False
    return _verdict(ok, "bisimulation", len(R))


def _hml(succ, s, phi, memo):
    key = (s, repr(phi))
    if key in memo:
        return memo[key]
    op = phi[0]
    if op == "tt":
        r = True
    elif op == "not":
        r = not _hml(succ, s, phi[1], memo)
    elif op == "and":
        r = all(_hml(succ, s, f, memo) for f in phi[1:])
    elif op == "dia":
        r = any(_hml(succ, t, phi[2], memo) for t in succ.get(s, {}).get(phi[1], ()))
    else:
        raise KernelError(f"unknown HML operator {op!r}")
    memo[key] = r
    return r


def check_distinguishing_formula(P, Q, phi) -> Verdict:
    sp, _ = _succ(P)
    sq, _ = _succ(Q)
    ok = _hml(sp, P["body"]["init"], phi, {}) and not _hml(sq, Q["body"]["init"], phi, {})
    return _verdict(ok, "hml-distinguishes", 1)


def check_trace_cert(P, Q, pairs, completed=False) -> Verdict:
    sp, _ = _succ(P)
    sq, _ = _succ(Q)
    R = {(frozenset(x), frozenset(y)) for x, y in pairs}
    actions = {a for d in list(sp.values()) + list(sq.values()) for a in d}
    ok = (frozenset([P["body"]["init"]]), frozenset([Q["body"]["init"]])) in R
    for X, Y in R:
        if not ok:
            break
        if bool(X) != bool(Y):
            ok = False
        if completed and any(_deadlocked(sp, s) for s in X) != any(_deadlocked(sq, s) for s in Y):
            ok = False
        for a in actions:
            if (_post(sp, X, a), _post(sq, Y, a)) not in R:
                ok = False
    return _verdict(ok, "completed-trace-equivalence" if completed else "trace-equivalence", len(R))


def check_trace_witness(P, Q, trace, completed=False) -> Verdict:
    sp, _ = _succ(P)
    sq, _ = _succ(Q)
    X, Y = frozenset([P["body"]["init"]]), frozenset([Q["body"]["init"]])
    for a in trace:
        X, Y = _post(sp, X, a), _post(sq, Y, a)
    if completed:
        ok = any(_deadlocked(sp, s) for s in X) and not any(_deadlocked(sq, s) for s in Y)
    else:
        ok = bool(X) and not Y
    return _verdict(ok, "completed-trace-witness" if completed else "trace-witness", len(trace))


def check_context_deadlock(P, T, sync) -> Verdict:
    """Decide (by exhaustive exploration, computed HERE, not trusted from
    outside) whether P || T (CSP synchronization on `sync`) can reach a
    stuck state. ok = a deadlock is reachable."""
    sp, _ = _succ(P)
    st, _ = _succ(T)
    sync = set(sync)
    init = (P["body"]["init"], T["body"]["init"])
    seen, frontier = {init}, [init]
    while frontier:
        p, t = frontier.pop()
        nxt = []
        for a, ps in sp.get(p, {}).items():
            if a in sync:
                nxt += [(p2, t2) for p2 in ps for t2 in st.get(t, {}).get(a, ())]
            else:
                nxt += [(p2, t) for p2 in ps]
        for a, ts in st.get(t, {}).items():
            if a not in sync:
                nxt += [(p, t2) for t2 in ts]
        if not nxt:
            return _verdict(True, "context-deadlock", len(seen))
        for x in nxt:
            if x not in seen:
                if len(seen) > MAX_STATES:
                    raise KernelError("product too large")
                seen.add(x)
                frontier.append(x)
    return _verdict(False, "context-deadlock", len(seen))


def check_reachable_deadlock(P, path) -> Verdict:
    """path = [s0, a1, s1, a2, s2, ...] from init to a deadlocked state."""
    sp, _ = _succ(P)
    states = path[0::2]
    acts = path[1::2]
    ok = states[0] == P["body"]["init"] and _deadlocked(sp, states[-1])
    for s, a, t in zip(states, acts, states[1:]):
        ok = ok and t in sp.get(s, {}).get(a, ())
    return _verdict(ok, "reachable-deadlock", len(acts))
