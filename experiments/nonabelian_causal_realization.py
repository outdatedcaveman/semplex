"""Exact S3 gauge-ring + controlled conjugacy-class HMM benchmark.

This is a finite mathematical realization test, not a claim about a new physical law.
All probability calculations use fractions; no NumPy/SciPy dependency is required.
"""
from __future__ import annotations

from fractions import Fraction as F
from itertools import permutations, product
import json
from pathlib import Path

Perm = tuple[int, int, int]
Connection = tuple[Perm, Perm, Perm]
IDENTITY: Perm = (0, 1, 2)
GROUP: tuple[Perm, ...] = tuple(permutations(range(3)))
CLASS_REPS: tuple[Perm, ...] = (IDENTITY, (1, 0, 2), (1, 2, 0))
CLASS_NAMES = ("identity", "transposition", "3-cycle")
PERM_NAMES = {
    IDENTITY: "e",
    (1, 0, 2): "s01",
    (0, 2, 1): "s12",
    (2, 1, 0): "s02",
    (1, 2, 0): "c012",
    (2, 0, 1): "c021",
}
ACTIONS = ("wait", "probe")
ACTION_COST = {"wait": 1, "probe": 3}
P_WAIT = (
    (F(3, 4), F(1, 4), F(0)),
    (F(1, 8), F(3, 4), F(1, 8)),
    (F(0), F(1, 4), F(3, 4)),
)
P_PROBE = (
    (F(1, 2), F(1, 2), F(0)),
    (F(0), F(1, 2), F(1, 2)),
    (F(1, 4), F(0), F(3, 4)),
)
TRANSITIONS = {"wait": P_WAIT, "probe": P_PROBE}


def compose(p: Perm, q: Perm) -> Perm:
    """Permutation composition p after q."""
    return tuple(p[q[i]] for i in range(3))


def inverse(p: Perm) -> Perm:
    return tuple(p.index(i) for i in range(3))


def conjugacy_class(g: Perm) -> frozenset[Perm]:
    return frozenset(compose(compose(k, g), inverse(k)) for k in GROUP)


CLASS_SETS = tuple(conjugacy_class(rep) for rep in CLASS_REPS)
CLASS_INDEX = {c: i for i, c in enumerate(CLASS_SETS)}


def class_index(g: Perm) -> int:
    return CLASS_INDEX[conjugacy_class(g)]


def holonomy(connection: Connection) -> Perm:
    # Edges are oriented i -> i+1; compose along the path in traversal order.
    return compose(connection[2], compose(connection[1], connection[0]))


def gauge_transform(connection: Connection, gauge: Connection) -> Connection:
    # A_i : i -> i+1 transforms as g_(i+1) A_i g_i^{-1}.
    return tuple(
        compose(compose(gauge[(i + 1) % 3], connection[i]), inverse(gauge[i]))
        for i in range(3)
    )  # type: ignore[return-value]


def orbit_partition() -> dict:
    configurations = set(product(GROUP, repeat=3))
    gauges = tuple(product(GROUP, repeat=3))
    unseen = set(configurations)
    rows = []
    while unseen:
        representative = min(unseen)
        orbit = {gauge_transform(representative, g) for g in gauges}
        if not orbit <= unseen:
            raise AssertionError("gauge transformations did not form a partition")
        unseen.difference_update(orbit)
        hclass = class_index(holonomy(representative))
        rows.append({"class": CLASS_NAMES[hclass], "size": len(orbit)})
    rows.sort(key=lambda x: CLASS_NAMES.index(x["class"]))
    return {
        "connection_count": len(configurations),
        "gauge_transformation_count": len(gauges),
        "orbit_count": len(rows),
        "orbits": rows,
        "orbit_sizes_by_class": {r["class"]: r["size"] for r in rows},
    }


def find_local_order_collision() -> dict:
    """Same multiset of edge conjugacy classes, different loop conjugacy class."""
    seen: dict[tuple[int, ...], tuple[Connection, int]] = {}
    for raw in product(GROUP, repeat=3):
        conn: Connection = raw  # type: ignore[assignment]
        local = tuple(sorted(class_index(edge) for edge in conn))
        loop_class = class_index(holonomy(conn))
        old = seen.get(local)
        if old is not None and old[1] != loop_class:
            return {
                "first": [PERM_NAMES[x] for x in old[0]],
                "second": [PERM_NAMES[x] for x in conn],
                "same_local_conjugacy_multiset": [CLASS_NAMES[i] for i in local],
                "first_holonomy": PERM_NAMES[holonomy(old[0])],
                "second_holonomy": PERM_NAMES[holonomy(conn)],
                "first_holonomy_class": CLASS_NAMES[old[1]],
                "second_holonomy_class": CLASS_NAMES[loop_class],
                "warning": "An individual open-edge conjugacy class is not gauge-invariant under independent endpoint gauge transformations; this is only a gauge-fixed local-statistics witness.",
            }
        seen[local] = (conn, loop_class)
    raise AssertionError("expected an order-sensitive local-statistics collision")


def representation_baseline_summary() -> dict:
    local_to_holonomy: dict[tuple[int, ...], set[int]] = {}
    for raw in product(GROUP, repeat=3):
        conn: Connection = raw  # type: ignore[assignment]
        signature = tuple(sorted(class_index(edge) for edge in conn))
        local_to_holonomy.setdefault(signature, set()).add(class_index(holonomy(conn)))
    ambiguous = [classes for classes in local_to_holonomy.values() if len(classes) > 1]
    return {
        "strict_single_open_edge_gauge_invariant_scalar": "constant: independent gauge transformations at the two endpoints act transitively on S3",
        "naive_gauge_fixed_edge_class_multisets": len(local_to_holonomy),
        "naive_local_signatures_ambiguous_across_holonomy_classes": len(ambiguous),
        "ordered_group_holonomy_states": len(GROUP),
        "gauge_invariant_holonomy_classes": len(CLASS_SETS),
        "frame_redundancy_factor": len(GROUP) // len(CLASS_SETS),
        "predictive_belief_dimension": len(CLASS_SETS) - 1,
        "interpretation": "Local gauge-invariant scalar probes cannot separate sectors; ordered composition recovers holonomy, conjugacy quotient removes base-frame redundancy, and the dynamic posterior is the predictive state.",
    }


def det3(m) -> F:
    a, b, c = m[0]
    d, e, f = m[1]
    g, h, i = m[2]
    return a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)


def matmul(a, b):
    return [
        [sum((a[i][k] * b[k][j] for k in range(len(b))), F(0))
         for j in range(len(b[0]))]
        for i in range(len(a))
    ]


def row_mul(v, m):
    return [sum((v[i] * m[i][j] for i in range(len(v))), F(0))
            for j in range(len(m[0]))]


def matvec(m, v):
    return [sum((m[i][j] * v[j] for j in range(len(v))), F(0))
            for i in range(len(m))]


def normalize(v):
    total = sum(v, F(0))
    if total == 0:
        raise ZeroDivisionError("zero-probability history")
    return [x / total for x in v]


def matrix_add(a, b):
    return [[a[i][j] + b[i][j] for j in range(len(a[0]))] for i in range(len(a))]


def centering_projector(n: int):
    return [
        [F(1) - F(1, n) if i == j else F(-1, n) for j in range(n)]
        for i in range(n)
    ]


def centered_diagnostics(result: dict) -> dict:
    """Compare centered Hankel rank with the centered Gram sum Wc+Wo."""
    h = result["H"]
    wc, wo = result["Wc"], result["Wo"]
    ph, pt = centering_projector(len(h)), centering_projector(len(h[0]))
    ps = centering_projector(len(wc))
    hc = matmul(matmul(ph, h), pt)
    wcc = matmul(matmul(ps, wc), ps)
    woc = matmul(matmul(ps, wo), ps)
    gram_sum = matrix_add(wcc, woc)
    return {
        "rank_centered_H": matrix_rank(hc),
        "rank_centered_Wc": matrix_rank(wcc),
        "rank_centered_Wo": matrix_rank(woc),
        "rank_centered_Wc_plus_Wo": matrix_rank(gram_sum),
        "centered_H_equals_factorization": hc == matmul(matmul(ph, matmul(result["R"], result["O"])), pt),
    }


def matrix_rank(matrix) -> int:
    if not matrix:
        return 0
    a = [[F(x) for x in row] for row in matrix]
    rows, cols = len(a), len(a[0])
    pivot_row = 0
    for col in range(cols):
        pivot = next((r for r in range(pivot_row, rows) if a[r][col]), None)
        if pivot is None:
            continue
        a[pivot_row], a[pivot] = a[pivot], a[pivot_row]
        scale = a[pivot_row][col]
        a[pivot_row] = [x / scale for x in a[pivot_row]]
        for r in range(rows):
            if r != pivot_row and a[r][col]:
                factor = a[r][col]
                a[r] = [a[r][j] - factor * a[pivot_row][j] for j in range(cols)]
        pivot_row += 1
        if pivot_row == rows:
            break
    return pivot_row


def observation_probability(action: str, hidden_class: int, outcome: int, eta: F) -> F:
    if action == "wait":
        return F(1, 3)
    return F(1) - 2 * eta if hidden_class == outcome else eta


def joint_matrix(action: str, outcome: int, eta: F):
    transition = TRANSITIONS[action]
    return [
        [transition[i][j] * observation_probability(action, j, outcome, eta)
         for j in range(3)]
        for i in range(3)
    ]


def action_words(budget: int):
    yield ()
    for length in range(1, budget + 1):
        for word in product(ACTIONS, repeat=length):
            if sum(ACTION_COST[a] for a in word) <= budget:
                yield word


def stationary_wait_prior():
    """Stationary distribution of P_WAIT; removes action-only prior drift."""
    return [F(1, 4), F(1, 2), F(1, 4)]


def history_rows(budget: int, eta: F, prior=None):
    prior = list(prior) if prior is not None else [F(1, 3)] * 3
    rows = []
    for actions in action_words(budget):
        for observations in product(range(3), repeat=len(actions)):
            alpha = list(prior)
            for action, outcome in zip(actions, observations):
                alpha = row_mul(alpha, joint_matrix(action, outcome, eta))
            mass = sum(alpha, F(0))
            if mass:
                rows.append({
                    "actions": actions,
                    "observations": observations,
                    "posterior": normalize(alpha),
                })
    return rows


def future_likelihood(actions, observations, eta: F):
    likelihood = [F(1)] * 3
    for action, outcome in reversed(tuple(zip(actions, observations))):
        likelihood = matvec(joint_matrix(action, outcome, eta), likelihood)
    return likelihood


def future_columns(budget: int, eta: F):
    columns = []
    for actions in action_words(budget):
        for observations in product(range(3), repeat=len(actions)):
            columns.append({
                "actions": actions,
                "observations": observations,
                "likelihood": future_likelihood(actions, observations, eta),
            })
    return columns


def hankel_factorization(budget: int, eta: F, prior=None):
    histories = history_rows(budget, eta, prior=prior)
    tests = future_columns(budget, eta)
    r = [h["posterior"] for h in histories]
    o = [[t["likelihood"][i] for t in tests] for i in range(3)]
    h = matmul(r, o)
    # Uniform finite-set weights: Wc = R^T D_H R and Wo = O D_T O^T.
    wc = [
        [sum((row[i] * row[j] for row in r), F(0)) / len(r) for j in range(3)]
        for i in range(3)
    ]
    wo = [
        [sum((o[i][t] * o[j][t] for t in range(len(tests))), F(0)) / len(tests)
         for j in range(3)]
        for i in range(3)
    ]
    wcwo = matmul(wc, wo)
    return {
        "history_count": len(histories),
        "test_count": len(tests),
        "R": r,
        "O": o,
        "H": h,
        "Wc": wc,
        "Wo": wo,
        "WcWo": wcwo,
        "rank_R": matrix_rank(r),
        "rank_O": matrix_rank(o),
        "rank_H": matrix_rank(h),
        "rank_Wc": matrix_rank(wc),
        "rank_Wo": matrix_rank(wo),
        "rank_WcWo": matrix_rank(wcwo),
        "factorization_exact": h == matmul(r, o),
        "full_abstraction_on_simplex": matrix_rank(o) == 3,
    }


def group_level_transition(action: str):
    """Lift class Markov dynamics uniformly to S3; this is conjugation-equivariant."""
    p = TRANSITIONS[action]
    sizes = [len(CLASS_SETS[i]) for i in range(3)]
    return [
        [p[class_index(g)][class_index(gp)] / sizes[class_index(gp)] for gp in GROUP]
        for g in GROUP
    ]


def check_group_lift_equivariance() -> bool:
    for action in ACTIONS:
        q = group_level_transition(action)
        for g in GROUP:
            for gp in GROUP:
                for k in GROUP:
                    kgk = compose(compose(k, g), inverse(k))
                    kgpk = compose(compose(k, gp), inverse(k))
                    if q[GROUP.index(g)][GROUP.index(gp)] != q[GROUP.index(kgk)][GROUP.index(kgpk)]:
                        return False
    return True


def check_group_lift_row_stochastic() -> bool:
    return all(
        sum(row, F(0)) == 1
        for action in ACTIONS
        for row in group_level_transition(action)
    )


def fraction_matrix(m):
    return [[str(x) for x in row] for row in m]


def analyze() -> dict:
    eta_informative = F(1, 6)
    eta_uniform = F(1, 3)
    k = [
        [F(1) - 2 * eta_informative if i == j else eta_informative for j in range(3)]
        for i in range(3)
    ]
    k_uniform = [
        [F(1) - 2 * eta_uniform if i == j else eta_uniform for j in range(3)]
        for i in range(3)
    ]
    b2 = hankel_factorization(2, eta_informative)
    stationary_prior = stationary_wait_prior()
    b2_stationary = hankel_factorization(2, eta_informative, prior=stationary_prior)
    b3 = hankel_factorization(3, eta_informative)
    b3_uniform = hankel_factorization(3, eta_uniform)
    return {
        "model": "S3 gauge ring with a conjugacy-class controlled HMM",
        "conjugacy_classes": {
            name: [PERM_NAMES[g] for g in sorted(CLASS_SETS[i])]
            for i, name in enumerate(CLASS_NAMES)
        },
        "gauge_orbits": orbit_partition(),
        "local_order_collision": find_local_order_collision(),
        "representation_baselines": representation_baseline_summary(),
        "dynamics": {
            "P_wait": fraction_matrix(P_WAIT),
            "P_probe": fraction_matrix(P_PROBE),
            "det_P_wait": str(det3(P_WAIT)),
            "det_P_probe": str(det3(P_PROBE)),
            "P_wait_P_probe_commute": matmul(P_WAIT, P_PROBE) == matmul(P_PROBE, P_WAIT),
            "group_level_lift_conjugation_equivariant": check_group_lift_equivariance(),
            "group_level_lift_row_stochastic": check_group_lift_row_stochastic(),
        },
        "observation": {
            "eta_informative": str(eta_informative),
            "K_informative": fraction_matrix(k),
            "det_K_informative": str(det3(k)),
            "eta_uniform": str(eta_uniform),
            "K_uniform": fraction_matrix(k_uniform),
            "det_K_uniform": str(det3(k_uniform)),
        },
        "resource_hankel": {
            "budget_2_informative_noise": {
                key: value for key, value in b2.items()
                if key not in {"R", "O", "H", "Wc", "Wo", "WcWo"}
            },
            "budget_3_informative_noise": {
                key: value for key, value in b3.items()
                if key not in {"R", "O", "H", "Wc", "Wo", "WcWo"}
            },
            "budget_3_uniform_noise": {
                key: value for key, value in b3_uniform.items()
                if key not in {"R", "O", "H", "Wc", "Wo", "WcWo"}
            },
            "budget_2_stationary_prior": {
                key: value for key, value in b2_stationary.items()
                if key not in {"R", "O", "H", "Wc", "Wo", "WcWo"}
            },
            "centered_gram_sum_diagnostics": {
                "B2_eta_1_6": centered_diagnostics(b2),
                "B3_eta_1_6": centered_diagnostics(b3),
                "B3_eta_1_3": centered_diagnostics(b3_uniform),
            },
            "prior_sensitivity": {
                "uniform_prior": ["1/3", "1/3", "1/3"],
                "stationary_wait_prior": [str(x) for x in stationary_prior],
                "stationary_under_wait": row_mul(stationary_prior, P_WAIT) == stationary_prior,
                "rank_R_uniform_prior_budget_2": b2["rank_R"],
                "rank_R_stationary_prior_budget_2": b2_stationary["rank_R"],
                "interpretation": "The B=2 rank-R growth under a uniform prior is caused by known wait-transition drift, not observation learning; stationary initialization removes it.",
            },
            "budget_3_matrices": {
                "R": fraction_matrix(b3["R"]),
                "O": fraction_matrix(b3["O"]),
                "H": fraction_matrix(b3["H"]),
                "Wc": fraction_matrix(b3["Wc"]),
                "Wo": fraction_matrix(b3["Wo"]),
                "WcWo": fraction_matrix(b3["WcWo"]),
            },
            "budget_3_gram_ranks": {
                "Wc": b3["rank_Wc"],
                "Wo": b3["rank_Wo"],
                "WcWo": b3["rank_WcWo"],
            },
        },
        "theorem": {
            "budget_below_3": "Only wait actions are affordable; wait observations are uniform, so every prior belief has the same future response profile.",
            "budget_at_least_3": "The one-step probe response is b P_probe K_eta. Since det(P_probe)=1/4 and det(K_eta)=(1-3 eta)^2, it separates all beliefs iff eta != 1/3.",
            "uniform_noise": "At eta=1/3 every emission is uniform, so all finite action-observation response profiles are independent of the prior at every budget.",
            "posterior_sufficiency": "The Bayesian belief is a sufficient state because every future-test likelihood is linear in the current belief.",
        },
    }


if __name__ == "__main__":
    result = analyze()
    out = Path(__file__).resolve().parents[1] / "artifacts" / "nonabelian-causal-realization-20261122.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "artifact": str(out),
        "gauge_orbits": result["gauge_orbits"],
        "local_order_collision": result["local_order_collision"],
        "resource_hankel": result["resource_hankel"],
    }, indent=2))
