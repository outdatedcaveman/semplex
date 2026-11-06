"""Fragment F1: labelled transition systems (Spike 05). Untrusted search.

Charter §1.3: "Do not collapse all semantics into input-output functions:
state, traces, ... contexts ... may matter." F1 makes that concrete with a
hierarchy of behavioural equivalences, each the right notion for a
different observation protocol Omega:

    trace equivalence            observer records the sequence of actions
    completed-trace equivalence  ... and also sees when the system gets stuck
    bisimilarity                 observer can probe after every step, i.e.
                                 equivalence is preserved by every context
Each search below returns a certificate the trusted kernel_lts can check.
"""

from __future__ import annotations

import random
from itertools import product


def lts(init, trans, states=None):
    body = {"init": init, "trans": [list(t) for t in trans]}
    if states is not None:
        body["states"] = list(states)
    return {"kind": "lts", "body": body}


def succ(P):
    out = {}
    for s, a, t in P["body"]["trans"]:
        out.setdefault(s, {}).setdefault(a, set()).add(t)
    return out


def states_of(P):
    b = P["body"]
    s = set(b.get("states", [])) | {b["init"]}
    for x, _, y in b["trans"]:
        s |= {x, y}
    return s


def actions_of(*Ps):
    return sorted({a for P in Ps for _, a, _ in P["body"]["trans"]})


def deterministic(P):
    return all(len(ts) <= 1 for d in succ(P).values() for ts in d.values())


# ------------------------------------------------------------ bisimulation

def bisimulation(P, Q):
    """Greatest bisimulation by fixpoint refinement over state pairs.
    Returns ("bisimilar", relation) or ("not-bisimilar", HML formula)."""
    sp, sq = succ(P), succ(Q)
    pairs = set(product(states_of(P), states_of(Q)))
    rank = {}
    k = 0
    R = set(pairs)
    while True:
        k += 1
        bad = set()
        for p, q in R:
            ok = True
            for a, ps in sp.get(p, {}).items():
                if not all(any((p2, q2) in R for q2 in sq.get(q, {}).get(a, ())) for p2 in ps):
                    ok = False
            for a, qs in sq.get(q, {}).items():
                if not all(any((p2, q2) in R for p2 in sp.get(p, {}).get(a, ())) for q2 in qs):
                    ok = False
            if not ok:
                bad.add((p, q))
        if not bad:
            break
        for x in bad:
            rank[x] = k
        R -= bad
    p0, q0 = P["body"]["init"], Q["body"]["init"]
    if (p0, q0) in R:
        return "bisimilar", sorted(R)
    return "not-bisimilar", _formula(sp, sq, p0, q0, R, rank)


def _formula(sp, sq, p, q, R, rank):
    """HML formula true at p (in P) and false at q (in Q). Recursion on rank."""
    k = rank[(p, q)]
    for a, ps in sp.get(p, {}).items():
        for p2 in ps:
            qs = sq.get(q, {}).get(a, set())
            if all((p2, q2) not in R and rank.get((p2, q2), 0) < k for q2 in qs):
                return ["dia", a, ["and", ["tt"]] + [_formula(sp, sq, p2, q2, R, rank) for q2 in sorted(qs)]]
    for a, qs in sq.get(q, {}).items():
        for q2 in qs:
            ps = sp.get(p, {}).get(a, set())
            if all((p2, q2) not in R and rank.get((p2, q2), 0) < k for p2 in ps):
                # q can do a-step that no p-step matches: p satisfies NOT <a>(AND of formulas true at q2)
                inner = ["and", ["tt"]] + [["not", _formula(sp, sq, p2, q2, R, rank)] for p2 in sorted(ps)]
                return ["not", ["dia", a, inner]]
    raise AssertionError("rank invariant violated")


# ------------------------------------------------------------ traces

def trace_equivalence(P, Q, completed=False):
    """Explore pairs of reachable state-sets (on-the-fly determinization).
    Returns ("equivalent", pairs) or ("different", witness_trace, side, kind)
    where side says which system has the trace and kind is "trace" or
    "completed" (a completed-trace search may find a plain trace difference)."""
    sp, sq = succ(P), succ(Q)
    acts = actions_of(P, Q)
    dead = lambda s_, X: any(not s_.get(x) for x in X)
    start = (frozenset([P["body"]["init"]]), frozenset([Q["body"]["init"]]))
    seen, frontier = {start: ()}, [start]
    while frontier:
        X, Y = frontier.pop(0)
        tr = seen[(X, Y)]
        if bool(X) != bool(Y):
            return "different", list(tr), "P" if X else "Q", "trace"
        if completed and dead(sp, X) != dead(sq, Y):
            return "different", list(tr), "P" if dead(sp, X) else "Q", "completed"
        for a in acts:
            nxt = (frozenset(t for s in X for t in sp.get(s, {}).get(a, ())),
                   frozenset(t for s in Y for t in sq.get(s, {}).get(a, ())))
            if nxt not in seen:
                seen[nxt] = tr + (a,)
                frontier.append(nxt)
    return "equivalent", [[sorted(x), sorted(y)] for x, y in seen]


# ------------------------------------------------------------ contexts

def parallel(P, T, sync):
    """CSP-style parallel composition: actions in `sync` need both sides;
    all other actions interleave."""
    sp, st = succ(P), succ(T)
    init = (P["body"]["init"], T["body"]["init"])
    trans, seen, frontier = [], {init}, [init]
    while frontier:
        p, t = frontier.pop()
        moves = []
        for a, ps in sp.get(p, {}).items():
            if a in sync:
                moves += [(a, (p2, t2)) for p2 in ps for t2 in st.get(t, {}).get(a, ())]
            else:
                moves += [(a, (p2, t)) for p2 in ps]
        for a, ts in st.get(t, {}).items():
            if a not in sync:
                moves += [(a, (p, t2)) for t2 in ts]
        for a, nxt in moves:
            trans.append([f"{p}|{t}", a, f"{nxt[0]}|{nxt[1]}"])
            if nxt not in seen:
                seen.add(nxt)
                frontier.append(nxt)
    return lts(f"{init[0]}|{init[1]}", trans, [f"{p}|{t}" for p, t in seen])


def deadlock_path(P):
    sp = succ(P)
    init = P["body"]["init"]
    prev, frontier = {init: None}, [init]
    while frontier:
        s = frontier.pop(0)
        if not sp.get(s):
            path = [s]
            while prev[path[0]] is not None:
                ps, a = prev[path[0]]
                path = [ps, a] + path
            return path
        for a, ts in sorted(sp[s].items()):
            for t in sorted(ts):
                if t not in prev:
                    prev[t] = (s, a)
                    frontier.append(t)
    return None


# ------------------------------------------------------------ canonical quotient

def bisim_quotient(P):
    """Minimal LTS bisimilar to P: states = bisimulation classes (reachable part)."""
    status, R = bisimulation(P, P)
    cls = {}
    for p, q in R:
        cls.setdefault(p, set()).add(q)
    name = {s: "{" + ",".join(sorted(map(str, c))) + "}" for s, c in cls.items()}
    trans = {(name[s], a, name[t]) for s, a, t in P["body"]["trans"]}
    reach, frontier = {name[P["body"]["init"]]}, [name[P["body"]["init"]]]
    while frontier:
        x = frontier.pop()
        for s, a, t in trans:
            if s == x and t not in reach:
                reach.add(t)
                frontier.append(t)
    return lts(name[P["body"]["init"]], sorted(t for t in trans if t[0] in reach), sorted(reach))


def random_lts(rng: random.Random, n_states=4, actions=("a", "b"), p=0.3, det=False):
    trans = []
    for s in range(n_states):
        for a in actions:
            targets = [t for t in range(n_states) if rng.random() < p]
            if det and targets:
                targets = [rng.choice(targets)]
            trans += [[f"s{s}", a, f"s{t}"] for t in targets]
    return lts("s0", trans, [f"s{i}" for i in range(n_states)])
