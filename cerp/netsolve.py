"""Exact existence search for small networks with a CP-SAT solver (Spike 08b). UNTRUSTED.

Question answered: is there a network with THIS wiring, activation types and
integer weights in [-W, W] (biases in [-B, B]) that computes f on all 2^n inputs?

  SAT      -> a `dnet` artifact; cerp.kernel checks it against the truth table
  UNSAT    -> a lower bound, valid only WITHIN the declared weight box and only
              as far as the solver is trusted (no certificate): COMPUTED-UNCERTIFIED
  UNKNOWN  -> time limit hit; no claim

Wiring spec: list of neurons, each (act, refs). refs index the value list
(inputs 0..n-1, then earlier neurons). The last neuron is the step output.
"""

from __future__ import annotations

from ortools.sat.python import cp_model


def layered(n, widths, act="step", skip=False):
    """Hidden layers of the given widths, then one step output.
    skip=True lets every neuron also read all earlier layers and the inputs."""
    spec, prev, allprev = [], list(range(n)), list(range(n))
    for w in widths:
        cur = []
        for _ in range(w):
            spec.append((act, list(allprev if skip else prev)))
            cur.append(n + len(spec) - 1)
        prev = cur
        allprev = allprev + cur
    spec.append(("step", list(allprev if skip else prev)))
    return spec


def chain(n, k, act="step"):
    """Most general feedforward wiring on k neurons: each reads everything before it."""
    return [(act if j < k - 1 else "step", list(range(n + j))) for j in range(k)]


def solve(f, n, spec, W=3, B=None, time_limit=60.0, workers=4, relu_cap=None):
    B = B if B is not None else W * (n + len(spec)) + 1
    m = cp_model.CpModel()
    pts = range(1 << n)
    wv = [[m.NewIntVar(-W, W, f"w{j}_{i}") for i in range(len(refs))] for j, (_, refs) in enumerate(spec)]
    bv = [m.NewIntVar(-B, B, f"b{j}") for j in range(len(spec))]
    kinds = ["in"] * n + [a for a, _ in spec]
    cap = relu_cap or (W * (n + len(spec)) + B)
    last = len(spec) - 1
    for x in pts:
        vals = [(x >> i) & 1 for i in range(n)]
        for j, (act, refs) in enumerate(spec):
            terms = []
            for i, r in enumerate(refs):
                v = vals[r]
                if isinstance(v, int):
                    if v:
                        terms.append(wv[j][i])
                elif kinds[r] == "step":
                    p = m.NewIntVar(-W, W, "")
                    m.Add(p == wv[j][i]).OnlyEnforceIf(v)
                    m.Add(p == 0).OnlyEnforceIf(v.Not())
                    terms.append(p)
                else:  # relu value: integer product
                    p = m.NewIntVar(-W * cap, W * cap, "")
                    m.AddMultiplicationEquality(p, [wv[j][i], v])
                    terms.append(p)
            pre = sum(terms) + bv[j]
            if j == last:
                if (f >> x) & 1:
                    m.Add(pre >= 0)
                else:
                    m.Add(pre <= -1)
                vals.append((f >> x) & 1)
            elif act == "step":
                h = m.NewBoolVar("")
                m.Add(pre >= 0).OnlyEnforceIf(h)
                m.Add(pre <= -1).OnlyEnforceIf(h.Not())
                vals.append(h)
            else:
                pv = m.NewIntVar(-cap * W * 4, cap * W * 4, "")
                m.Add(pv == pre)
                r_ = m.NewIntVar(0, cap, "")
                m.AddMaxEquality(r_, [pv, m.NewConstant(0)])
                vals.append(r_)
    # symmetry breaking between interchangeable neurons (same act, same refs)
    for j in range(len(spec) - 2):
        if spec[j] == spec[j + 1]:
            key = lambda q: sum(wv[q][i] * (2 * W + 1) ** i for i in range(len(spec[q][1]))) + bv[q] * (2 * W + 1) ** len(spec[q][1])
            m.Add(key(j) <= key(j + 1))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = time_limit
    s.parameters.num_workers = workers
    st = s.Solve(m)
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        neurons = [{"in": list(refs), "w": [int(s.Value(v)) for v in wv[j]], "b": int(s.Value(bv[j])), "act": act}
                   for j, (act, refs) in enumerate(spec)]
        return "sat", {"kind": "dnet", "body": {"inputs": [f"x{i}" for i in range(n)], "neurons": neurons}}
    return ("unsat" if st == cp_model.INFEASIBLE else "unknown"), None
