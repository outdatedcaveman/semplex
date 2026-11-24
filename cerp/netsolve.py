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


def _solve_two_halfspaces(f, n, care, W, time_limit, workers, and_mode=True, rand_obj=None):
    """Fast decoupled CP-SAT solver for f = h0 AND h1 (or h0 OR h1) over care points."""
    pts = [x for x in range(1 << n) if care is None or (care >> x) & 1]
    want_t = 1 if and_mode else 0
    T = [x for x in pts if ((f >> x) & 1) == want_t]
    F = [x for x in pts if ((f >> x) & 1) != want_t]
    B = W * n + 1
    m = cp_model.CpModel()
    w0 = [m.NewIntVar(-W, W, f"w0_{i}") for i in range(n)]
    w1 = [m.NewIntVar(-W, W, f"w1_{i}") for i in range(n)]
    b0 = m.NewIntVar(-B, B, "b0")
    b1 = m.NewIntVar(-B, B, "b1")
    for x in T:
        idx = [i for i in range(n) if (x >> i) & 1]
        m.Add(sum(w0[i] for i in idx) + b0 >= 0)
        m.Add(sum(w1[i] for i in idx) + b1 >= 0)
    s_vars = []
    for k, x in enumerate(F):
        idx = [i for i in range(n) if (x >> i) & 1]
        s = m.NewBoolVar(f"s_{k}")
        s_vars.append(s)
        m.Add(sum(w0[i] for i in idx) + b0 <= -1).OnlyEnforceIf(s.Not())
        m.Add(sum(w1[i] for i in idx) + b1 <= -1).OnlyEnforceIf(s)
    if F:
        m.Add(s_vars[0] == 0)
    if rand_obj is not None:
        import random
        r = random.Random(rand_obj)
        m.Minimize(sum(r.randint(-5, 5) * v for v in w0 + w1 + [b0, b1]))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = workers
    st = solver.Solve(m)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return ("unsat" if st == cp_model.INFEASIBLE else "unknown"), None
    v0 = [int(solver.Value(v)) for v in w0]; c0 = int(solver.Value(b0))
    v1 = [int(solver.Value(v)) for v in w1]; c1 = int(solver.Value(b1))
    refs = list(range(n))
    if and_mode:
        neurons = [
            {"in": refs, "w": v0, "b": c0, "act": "step"},
            {"in": refs, "w": v1, "b": c1, "act": "step"},
            {"in": [n, n + 1], "w": [1, 1], "b": -2, "act": "step"},
        ]
    else:
        neurons = [
            {"in": refs, "w": [-z for z in v0], "b": -c0 - 1, "act": "step"},
            {"in": refs, "w": [-z for z in v1], "b": -c1 - 1, "act": "step"},
            {"in": [n, n + 1], "w": [1, 1], "b": -1, "act": "step"},
        ]
    return "sat", {"kind": "dnet", "body": {"inputs": [f"x{i}" for i in range(n)], "neurons": neurons}}


_THREE_HALFSPACE_GATES = (
    ("or_and", [2, 1, 1], -2),
    ("and_or", [2, 1, 1], -3),
    ("maj3", [1, 1, 1], -2),
    ("and3", [1, 1, 1], -3),
    ("or3", [1, 1, 1], -1),
)


def _solve_three_halfspaces_gate(f, n, care, W, time_limit, workers, gate, rand_obj=None):
    """Exact decoupled CP-SAT solver for a fixed 3-input threshold output gate over care points."""
    gate_name, out_w, out_b = gate
    pts = [x for x in range(1 << n) if care is None or (care >> x) & 1]
    B = W * n + 1
    m = cp_model.CpModel()
    ws = [[m.NewIntVar(-W, W, f"w{j}_{i}") for i in range(n)] for j in range(3)]
    bs = [m.NewIntVar(-B, B, f"b{j}") for j in range(3)]

    def add_sign(expr, want_pos, cond=None):
        ct = m.Add(expr >= 0) if want_pos else m.Add(expr <= -1)
        if cond is not None:
            ct.OnlyEnforceIf(cond)

    def require_at_least(pres, indices, k, want_pos):
        if k >= len(indices):
            for j in indices:
                add_sign(pres[j], want_pos)
            return
        flags = [m.NewBoolVar("") for _ in indices]
        for j, fl in zip(indices, flags):
            add_sign(pres[j], want_pos, fl)
        m.Add(sum(flags) >= k)

    first_T = True
    first_F = True
    for x in pts:
        idx = [i for i in range(n) if (x >> i) & 1]
        pres = [sum(ws[j][i] for i in idx) + bs[j] for j in range(3)]
        y = (f >> x) & 1
        if gate_name == "and3":
            if y:
                require_at_least(pres, (0, 1, 2), 3, True)
            elif first_F:
                first_F = False
                add_sign(pres[0], False)
            else:
                require_at_least(pres, (0, 1, 2), 1, False)
        elif gate_name == "or3":
            if not y:
                require_at_least(pres, (0, 1, 2), 3, False)
            elif first_T:
                first_T = False
                add_sign(pres[0], True)
            else:
                require_at_least(pres, (0, 1, 2), 1, True)
        elif gate_name == "maj3":
            if y and first_T:
                first_T = False
                add_sign(pres[0], True)
                add_sign(pres[1], True)
            elif y:
                require_at_least(pres, (0, 1, 2), 2, True)
            else:
                require_at_least(pres, (0, 1, 2), 2, False)
        elif gate_name == "or_and":
            if y:
                sel = m.NewBoolVar("")
                add_sign(pres[0], True, sel)
                add_sign(pres[1], True, sel.Not())
                add_sign(pres[2], True, sel.Not())
            else:
                add_sign(pres[0], False)
                if first_F:
                    first_F = False
                    add_sign(pres[1], False)
                else:
                    require_at_least(pres, (1, 2), 1, False)
        else:  # and_or: h0 & (h1 | h2)
            if y:
                add_sign(pres[0], True)
                if first_T:
                    first_T = False
                    add_sign(pres[1], True)
                else:
                    require_at_least(pres, (1, 2), 1, True)
            else:
                sel = m.NewBoolVar("")
                add_sign(pres[0], False, sel)
                add_sign(pres[1], False, sel.Not())
                add_sign(pres[2], False, sel.Not())

    if rand_obj is not None:
        import random
        r = random.Random(rand_obj)
        all_vars = [v for row in ws for v in row] + bs
        m.Minimize(sum(r.randint(-5, 5) * v for v in all_vars))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = workers
    st = solver.Solve(m)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return ("unsat" if st == cp_model.INFEASIBLE else "unknown"), None
    refs = list(range(n))
    neurons = [
        {
            "in": refs,
            "w": [int(solver.Value(v)) for v in ws[j]],
            "b": int(solver.Value(bs[j])),
            "act": "step",
        }
        for j in range(3)
    ]
    neurons.append({"in": [n, n + 1, n + 2], "w": list(out_w), "b": out_b, "act": "step"})
    return "sat", {"kind": "dnet", "body": {"inputs": [f"x{i}" for i in range(n)], "neurons": neurons}}


def _solve_three_halfspaces(f, n, care, W, time_limit, workers, rand_obj=None):
    """Exact decoupled CP-SAT solver for layered(n, [3]) across all canonical 3-input threshold gates."""
    import time

    gates = [g for g in _THREE_HALFSPACE_GATES if max(abs(x) for x in g[1]) <= W]
    t0 = time.perf_counter()
    deadline = t0 + time_limit
    unknown = []
    # Round 1: quick pass per gate so a fast SAT gate is never starved behind a hard UNSAT one.
    for idx, gate in enumerate(gates):
        rem = max(0.05, deadline - time.perf_counter())
        if rem <= 0.06:
            unknown.extend(gates[idx:])
            break
        slice_t = min(max(0.5, time_limit * 0.16), rem / max(1, len(gates) - idx))
        st, art = _solve_three_halfspaces_gate(f, n, care, W, slice_t, workers, gate, rand_obj=rand_obj)
        if st == "sat":
            return st, art
        if st == "unknown":
            unknown.append(gate)
        if time.perf_counter() >= deadline:
            unknown.extend(gates[idx + 1:])
            break
    if not unknown:
        return "unsat", None
    # Round 2: give remaining time to gates that timed out in Round 1.
    all_unsat = True
    for idx, gate in enumerate(unknown):
        rem = deadline - time.perf_counter()
        if rem <= 0.05:
            all_unsat = False
            break
        slice_t = max(0.05, rem / (len(unknown) - idx))
        st, art = _solve_three_halfspaces_gate(f, n, care, W, slice_t, workers, gate, rand_obj=rand_obj)
        if st == "sat":
            return st, art
        if st != "unsat":
            all_unsat = False
    return ("unsat" if all_unsat else "unknown"), None


def solve(f, n, spec, W=3, B=None, time_limit=60.0, workers=4, relu_cap=None, care=None, rand_obj=None,
          max_errors=None, min_errors=False):
    """care: optional bitmask of the input points that must be matched (default: all).
    rand_obj: optional int seed; minimizes a random linear objective over the weights so that
    repeated calls return different satisfying networks (Spike 35 tie sampling). Status and
    feasibility are unchanged by it.
    max_errors: optional int; the net may disagree with f on at most this many care points (Spike 46).
    min_errors: if True, minimize the number of disagreeing care points; the status is then "optimal"
    (proved minimum) or "feasible" (best found within the time limit) instead of "sat"."""
    if (B is None and max_errors is None and not min_errors and W >= 1
            and len(spec) == 3
            and spec[0] == ("step", list(range(n)))
            and spec[1] == ("step", list(range(n)))
            and spec[2] == ("step", [n, n + 1])):
        half = max(0.05, time_limit * 0.5)
        st1, art1 = _solve_two_halfspaces(f, n, care, W, half, workers, and_mode=True, rand_obj=rand_obj)
        if st1 == "sat":
            return st1, art1
        st2, art2 = _solve_two_halfspaces(f, n, care, W, max(0.05, time_limit - half), workers, and_mode=False, rand_obj=rand_obj)
        if st2 == "sat":
            return st2, art2
        return ("unsat" if st1 == "unsat" and st2 == "unsat" else "unknown"), None
    if (B is None and max_errors is None and not min_errors and W >= 1
            and len(spec) == 4
            and spec[0] == ("step", list(range(n)))
            and spec[1] == ("step", list(range(n)))
            and spec[2] == ("step", list(range(n)))
            and spec[3] == ("step", [n, n + 1, n + 2])):
        return _solve_three_halfspaces(f, n, care, W, time_limit, workers, rand_obj=rand_obj)
    B = B if B is not None else W * (n + len(spec)) + 1
    m = cp_model.CpModel()
    pts = range(1 << n)
    wv = [[m.NewIntVar(-W, W, f"w{j}_{i}") for i in range(len(refs))] for j, (_, refs) in enumerate(spec)]
    bv = [m.NewIntVar(-B, B, f"b{j}") for j in range(len(spec))]
    kinds = ["in"] * n + [a for a, _ in spec]
    cap = relu_cap or (W * (n + len(spec)) + B)
    last = len(spec) - 1
    slack = max_errors is not None or min_errors
    errs = []
    for x in pts:
        if care is not None and not (care >> x) & 1:
            continue
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
                if slack:
                    e = m.NewBoolVar("")
                    errs.append(e)
                    (m.Add(pre >= 0) if (f >> x) & 1 else m.Add(pre <= -1)).OnlyEnforceIf(e.Not())
                    (m.Add(pre <= -1) if (f >> x) & 1 else m.Add(pre >= 0)).OnlyEnforceIf(e)
                elif (f >> x) & 1:
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
            xs = [bv[j]] + list(wv[j])
            ys = [bv[j + 1]] + list(wv[j + 1])
            pref = None
            for idx, (vx, vy) in enumerate(zip(xs, ys)):
                if pref is None:
                    m.Add(vx <= vy)
                    if idx + 1 < len(xs):
                        lt = m.NewBoolVar("")
                        nxt = m.NewBoolVar("")
                        m.Add(vx <= vy - 1).OnlyEnforceIf(lt)
                        m.Add(vx >= vy).OnlyEnforceIf(lt.Not())
                        m.AddBoolOr([lt, nxt])
                        pref = nxt
                else:
                    m.Add(vx <= vy).OnlyEnforceIf(pref)
                    if idx + 1 < len(xs):
                        lt = m.NewBoolVar("")
                        nxt = m.NewBoolVar("")
                        m.Add(vx <= vy - 1).OnlyEnforceIf([pref, lt])
                        m.Add(vx >= vy).OnlyEnforceIf([pref, lt.Not()])
                        m.AddBoolOr([pref.Not(), lt, nxt])
                        pref = nxt
    if max_errors is not None:
        m.Add(sum(errs) <= max_errors)
    if min_errors:
        m.Minimize(sum(errs))
    elif rand_obj is not None:
        import random
        r = random.Random(rand_obj)
        m.Minimize(sum(r.randint(-5, 5) * v for row in wv for v in row) + sum(r.randint(-5, 5) * v for v in bv))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = time_limit
    s.parameters.num_workers = workers
    st = s.Solve(m)
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        neurons = [{"in": list(refs), "w": [int(s.Value(v)) for v in wv[j]], "b": int(s.Value(bv[j])), "act": act}
                   for j, (act, refs) in enumerate(spec)]
        tag = "sat" if not min_errors else ("optimal" if st == cp_model.OPTIMAL else "feasible")
        return tag, {"kind": "dnet", "body": {"inputs": [f"x{i}" for i in range(n)], "neurons": neurons}}
    return ("unsat" if st == cp_model.INFEASIBLE else "unknown"), None


def compile_partial(f, n, care, W=4, max_width=4, time_limit=60.0, workers=4):
    """Compile a partial Boolean function (f on care-set bits) into a minimal
    layered threshold net with kernel-verified lower-bound certificates."""
    import time
    from . import bounds, kernel_bounds

    t0 = time.perf_counter()
    full_mask = (1 << (1 << n)) - 1
    fc = f & care
    deadline = t0 + time_limit

    def rem():
        return max(0.05, deadline - time.perf_counter())

    w_sched = [W] if W <= 3 else [3, W]

    # 1. Check 1-threshold lower bound via partial Farkas witness first
    lower_bound = 1
    certs = {}
    c1 = bounds.not_threshold_cert_partial(n, fc, care)
    if c1 is not None and kernel_bounds.check_not_threshold_partial(n, fc, care, c1["pos"], c1["neg"]).ok:
        lower_bound = 3
        certs["not_threshold"] = c1
    else:
        spec0 = layered(n, [])
        for wi, W_try in enumerate(w_sched):
            if time.perf_counter() >= deadline:
                break
            budget = min(10.0, rem()) / (len(w_sched) - wi)
            st, art = solve(fc, n, spec0, W=W_try, time_limit=budget, workers=workers, care=care)
            if st == "sat":
                return {
                    "status": "sat",
                    "cost": 1,
                    "artifact": art,
                    "certified_minimal": True,
                    "lower_bound": 1,
                    "cert_kind": "trivial",
                    "certs": {},
                    "cost3_status": "skipped",
                    "cost3_solver_unsat": False,
                    "seconds": round(time.perf_counter() - t0, 4),
                }

    # 2. Try width-2 hidden layer (cost 3: 2 hidden + 1 output) at fast weight W<=3 first
    spec2 = layered(n, [2])
    st2, art2 = solve(fc, n, spec2, W=min(W, 3), time_limit=min(10.0, rem() * 0.3), workers=workers, care=care)
    if st2 == "sat":
        cert_min = (lower_bound >= 3)
        return {
            "status": "sat",
            "cost": 3,
            "artifact": art2,
            "certified_minimal": cert_min,
            "lower_bound": lower_bound,
            "cert_kind": "not-threshold-partial" if cert_min else "uncertified",
            "certs": certs,
            "cost3_status": "sat",
            "cost3_solver_unsat": False,
            "seconds": round(time.perf_counter() - t0, 4),
        }

    # 3. Try certifying >= 4 neurons (no 2-halfspace AND/OR representation exists for any weights)
    f_neg = (~fc) & care & full_mask
    if lower_bound >= 3 and time.perf_counter() < deadline:
        c_pos = bounds.not_two_halfspaces_cert_partial(n, fc, care)
        c_neg = bounds.not_two_halfspaces_cert_partial(n, f_neg, care) if c_pos is not None else None
        if (c_pos is not None and c_neg is not None
                and kernel_bounds.check_not_two_halfspaces_partial(n, fc, care, c_pos).ok
                and kernel_bounds.check_not_two_halfspaces_partial(n, f_neg, care, c_neg).ok):
            lower_bound = 4
            certs["not_two_halfspaces_pos"] = c_pos
            certs["not_two_halfspaces_neg"] = c_neg

    # If lower_bound < 4, finish checking spec2 at full W so cost-3 collapses & solver-UNSAT are exact
    cost3_at_W = st2 if W <= 3 else "unknown"
    if lower_bound >= 4:
        cost3_status = "certified_impossible"
    else:
        w2_list = [W] if W > 3 else ([3] if st2 == "unknown" else [])
        for W_try in w2_list:
            if time.perf_counter() >= deadline:
                break
            st2b, art2b = solve(fc, n, spec2, W=W_try, time_limit=min(15.0, rem() * 0.45), workers=workers, care=care)
            cost3_at_W = st2b
            if st2b == "sat":
                cert_min = (lower_bound >= 3)
                return {
                    "status": "sat",
                    "cost": 3,
                    "artifact": art2b,
                    "certified_minimal": cert_min,
                    "lower_bound": lower_bound,
                    "cert_kind": "not-threshold-partial" if cert_min else "uncertified",
                    "certs": certs,
                    "cost3_status": "sat",
                    "cost3_solver_unsat": False,
                    "seconds": round(time.perf_counter() - t0, 4),
                }
        cost3_status = cost3_at_W
    cost3_solver_unsat = (lower_bound < 4 and cost3_status == "unsat")

    # 4. Incremental search over widths w = 3 .. max_width (cost = w + 1)
    for w in range(3, max_width + 1):
        if time.perf_counter() >= deadline:
            break
        spec_w = layered(n, [w])
        widths_left = max_width - w + 1
        for wi, W_try in enumerate(w_sched):
            if time.perf_counter() >= deadline:
                break
            budget = rem() / max(1, widths_left * len(w_sched) - wi)
            st, art = solve(fc, n, spec_w, W=W_try, time_limit=budget, workers=workers, care=care)
            if st == "sat":
                cost = w + 1
                cert_min = (lower_bound == cost)
                return {
                    "status": "sat",
                    "cost": cost,
                    "artifact": art,
                    "certified_minimal": cert_min,
                    "lower_bound": lower_bound,
                    "cert_kind": "not-two-halfspaces-partial" if cert_min else (
                        "not-threshold-partial" if lower_bound >= 3 else "uncertified"
                    ),
                    "certs": certs,
                    "cost3_status": cost3_status,
                    "cost3_solver_unsat": cost3_solver_unsat,
                    "seconds": round(time.perf_counter() - t0, 4),
                }

    return {
        "status": "unknown",
        "cost": None,
        "artifact": None,
        "certified_minimal": False,
        "lower_bound": lower_bound,
        "cert_kind": "not-two-halfspaces-partial" if lower_bound >= 4 else (
            "not-threshold-partial" if lower_bound >= 3 else "uncertified"
        ),
        "certs": certs,
        "cost3_status": cost3_status,
        "cost3_solver_unsat": cost3_solver_unsat,
        "seconds": round(time.perf_counter() - t0, 4),
    }
