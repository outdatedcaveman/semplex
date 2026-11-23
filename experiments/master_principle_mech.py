"""Mechanistic test of the Master Operator G(lam): out-of-sample lambda*(arch),
fluctuation-dissipation inversion, LeakyRNN step-inertia, Dirichlet penalty, and WD control.

Isolated experiment on `gemini/master-principle-mech` (zero overlap with Spike 77/78/81/84/87
or `origin/gemini/master-principle`, preserving 8 free monoids for `master-principle-transformer`).
"""

from __future__ import annotations

import json
import pathlib
import sys
import time

import numpy as np
from scipy.linalg import expm

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments import spike58 as S58
from experiments import spike69 as S69
from experiments import spike71 as S71
from experiments import spike77 as S77
from experiments import spike81 as S81
from experiments import spike84 as S84

RESULTS = ROOT / "experiments" / "results"
RAW = RESULTS / "master_principle_mech_raw"
OUT = RESULTS / "master_principle_mech.json"
PRED = RESULTS / "master_principle_mech_predictions.json"

# Frozen Master Operator constants (from Spike 77 + prior gemini/master-principle calibration only)
GAMMA_C = 0.6
GAMMA_O = 0.7
T_OP = 30
LAM0 = float(S77.LAMBDA / S77.ALPHA)  # ~1.476410
LAM_CAL = {"gru_lin": 0.85, "gru_mlp": 0.85, "lstm_mlp": 1.20, "rnn_mlp": 1.50}
LAM_KIN = {"gru_lin": 0.857, "gru_mlp": 1.085, "lstm_mlp": 1.137, "rnn_mlp": 1.782}

# Exact IDs used on origin/gemini/master-principle (must remain strictly disjoint)
PRIOR_MP_MONOIDS = {65, 70, 76, 103, 127, 193, 281, 368, 409, 512, 515, 584}
PRIOR_MP_GROUPS = {"Z11_s1_048", "Z11_s2_035", "Z12_s1_045", "Z7_s2_013", "Z7_s3_015", "Z8_s3_047"}

BATCH = 64
SEQ_LEN = 30
BURN = 5


def cos_mat(A: np.ndarray, B: np.ndarray) -> float:
    na = float(np.linalg.norm(A))
    nb = float(np.linalg.norm(B))
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return float(np.sum(A * B) / (na * nb))


def base_operators(Dl: np.ndarray, O: np.ndarray, pi: np.ndarray,
                   gc: float = GAMMA_C, go: float = GAMMA_O, T: int = T_OP) -> dict:
    """Compute base structural operators Lkin, Wc, Wo, o, k1, Wc+Wo in centered L^2(pi)."""
    L, m = Dl.shape
    O = np.asarray(O, float)
    if O.ndim == 1:
        O = O[:, None]
    W = np.sqrt(pi)
    one = W / np.linalg.norm(W)
    Pperp = np.eye(m) - np.outer(one, one)

    Ts = []
    for a in range(L):
        Pa = np.zeros((m, m))
        for q in range(m):
            Pa[q, Dl[a, q]] = 1.0
        Ts.append((W[:, None] * Pa) / W[None, :])

    Lkin = np.zeros((m, m))
    for Ta in Ts:
        diff = Ta - np.eye(m)
        Lkin += diff.T @ diff
    Lkin = 0.5 / L * (Pperp @ Lkin @ Pperp)
    Lkin = 0.5 * (Lkin + Lkin.T)

    mu_o = (pi[:, None] * O).sum(0, keepdims=True)
    Oc = O - mu_o
    sd = np.sqrt((pi[:, None] * (Oc ** 2)).sum(0, keepdims=True))
    Os = Oc / np.maximum(sd, 1e-12)
    F = W[:, None] * Os
    At = F @ F.T
    o_gram = Pperp @ (0.5 * (At + At.T)) @ Pperp

    Wo = np.zeros((m, m))
    K_fut_t1 = np.zeros((m, m))
    g = 1.0
    for t in range(T):
        Wo += g * At
        if t >= 1:
            K_fut_t1 += At
        At_next = np.zeros((m, m))
        for Ta in Ts:
            At_next += Ta @ At @ Ta.T
        At = At_next / L
        g *= go
    Wo = Pperp @ (0.5 * (Wo + Wo.T)) @ Pperp
    k1_gram = Pperp @ (0.5 * (K_fut_t1 + K_fut_t1.T)) @ Pperp

    Bt = np.outer(one, one)
    Wc = np.zeros((m, m))
    g = gc
    for _ in range(1, T):
        Bt_next = np.zeros((m, m))
        for Ta in Ts:
            Bt_next += Ta.T @ Bt @ Ta
        Bt = Bt_next / L
        Wc += g * (Pperp @ Bt @ Pperp)
        g *= gc
    Wc = 0.5 * (Wc + Wc.T)
    WcWo = Pperp @ (0.5 * ((Wc + Wo) + (Wc + Wo).T)) @ Pperp

    return {
        "Lkin": Lkin,
        "Wo": Wo,
        "Wc": Wc,
        "WcWo_noheat": WcWo,
        "o": o_gram,
        "k1": k1_gram,
        "wc_over_wo": float(np.linalg.norm(Wc) / max(np.linalg.norm(Wo), 1e-12)),
    }


def eval_sandwich(Lkin: np.ndarray, Wc: np.ndarray, Wo: np.ndarray, pi: np.ndarray, lam: float) -> tuple[np.ndarray, np.ndarray]:
    """Compute G(lam) and Wo_heat(lam) from base operators."""
    W = np.sqrt(pi)
    one = W / np.linalg.norm(W)
    Pperp = np.eye(len(pi)) - np.outer(one, one)
    H = expm(-0.5 * lam * Lkin)
    sym = lambda M: Pperp @ (0.5 * (M + M.T)) @ Pperp
    G = sym(H @ (Wc + Wo) @ H)
    Wo_heat = sym(H @ Wo @ H)
    return G, Wo_heat


def norm_dirichlet_theoretical(Lkin: np.ndarray, Wsrc: np.ndarray, lam: float) -> float:
    """Normalized Dirichlet expectation E_lam[L_kin] = Tr(Lkin * exp(-lam*Lkin) * Wsrc) / Tr(exp(-lam*Lkin) * Wsrc)."""
    E = expm(-lam * Lkin)
    M = E @ Wsrc
    den = float(np.trace(M))
    if den <= 1e-15:
        return 0.0
    return float(np.trace(Lkin @ M) / den)


def invert_lambda_from_kin(Lkin: np.ndarray, Wsrc: np.ndarray, kin_obs: float,
                           lo: float = -4.0, hi: float = 12.0) -> float:
    """Monotone bisection for unique lam satisfying normDirichlet(lam) == kin_obs."""
    k_lo = norm_dirichlet_theoretical(Lkin, Wsrc, lo)
    k_hi = norm_dirichlet_theoretical(Lkin, Wsrc, hi)
    if kin_obs >= k_lo:
        return lo
    if kin_obs <= k_hi:
        return hi
    a, b = lo, hi
    for _ in range(50):
        mid = 0.5 * (a + b)
        if norm_dirichlet_theoretical(Lkin, Wsrc, mid) > kin_obs:
            a = mid
        else:
            b = mid
    return 0.5 * (a + b)


def _collect_excluded_monoid_ids() -> set[int]:
    used = set(PRIOR_MP_MONOIDS)
    for fn in ["spike81.json", "spike84.json", "spike87.json",
               "spike84_predictions.json", "spike87_predictions.json"]:
        p = RESULTS / fn
        if not p.exists():
            continue
        d = json.loads(p.read_text())
        def walk(obj):
            if isinstance(obj, dict):
                for key in ("id", "aid"):
                    if key in obj and isinstance(obj[key], int):
                        used.add(obj[key])
                for v in obj.values():
                    walk(v)
            elif isinstance(obj, list):
                for v in obj:
                    walk(v)
        walk(d)
    for rd in ["spike84_raw", "spike87_raw", "master_principle_raw"]:
        rp = RESULTS / rd
        if rp.exists():
            for f in rp.glob("*.json"):
                d = json.loads(f.read_text())
                if isinstance(d.get("id"), int):
                    used.add(d["id"])
    return used


def predict():
    rng = np.random.default_rng(20261121)
    excluded_monoids = _collect_excluded_monoid_ids()
    pool = S81.build_pool()
    cand_free, cand_mixed = [], []
    for i, A in enumerate(pool):
        if i in excluded_monoids:
            continue
        D, O = np.array(A["D"]), np.array(A["O"])
        Dl = np.vstack([D, np.arange(D.shape[1])[None]])
        k = Dl.shape[0]
        pi = S81.visit_dist(Dl, A["s0"], np.ones(k) / k, T=SEQ_LEN, burn=BURN)
        if (pi <= 1e-4).any():
            continue
        hs = S84.head_structure(Dl, O, pi)
        if not (hs["dimR"] >= 1 and hs["dimH"] >= 1):
            continue
        ops = base_operators(Dl, O, pi)
        G0, Woh0 = eval_sandwich(ops["Lkin"], ops["Wc"], ops["Wo"], pi, LAM0)
        row = {
            "id": int(i),
            "kind": A["kind"],
            "D": A["D"],
            "out": A["O"],
            "s0": int(A["s0"]),
            "m": int(Dl.shape[1]),
            "L": int(Dl.shape[0]),
            "pi": pi.tolist(),
            "Lkin": ops["Lkin"].tolist(),
            "Wo": ops["Wo"].tolist(),
            "Wc": ops["Wc"].tolist(),
            "WcWo_noheat": ops["WcWo_noheat"].tolist(),
            "o": ops["o"].tolist(),
            "k1": ops["k1"].tolist(),
            "G_lam0": G0.tolist(),
            "Wo_heat_lam0": Woh0.tolist(),
            "wc_over_wo": ops["wc_over_wo"],
            "cos_G0_o": cos_mat(G0, ops["o"]),
            "cos_G0_Woh0": cos_mat(G0, Woh0),
        }
        # Precompute target matrices for frozen LAM_CAL and LAM_KIN per architecture
        for arch in ("gru_lin", "gru_mlp", "lstm_mlp", "rnn_mlp"):
            Gc, Wohc = eval_sandwich(ops["Lkin"], ops["Wc"], ops["Wo"], pi, LAM_CAL[arch])
            Gk, Wohk = eval_sandwich(ops["Lkin"], ops["Wc"], ops["Wo"], pi, LAM_KIN[arch])
            row[f"G_cal_{arch}"] = Gc.tolist()
            row[f"Wo_heat_cal_{arch}"] = Wohc.tolist()
            row[f"G_kin_{arch}"] = Gk.tolist()
            row[f"Wo_heat_kin_{arch}"] = Wohk.tolist()
            row[f"cos_Gkin_{arch}_o"] = cos_mat(Gk, ops["o"])

        if A["kind"] == "free":
            cand_free.append(row)
        elif A["kind"] == "mixed":
            cand_mixed.append(row)

    assert len(cand_free) >= 14 and len(cand_mixed) >= 6, f"free={len(cand_free)}, mixed={len(cand_mixed)}"
    idx_free = rng.choice(len(cand_free), size=6, replace=False)
    idx_mixed = rng.choice(len(cand_mixed), size=6, replace=False)
    picked_free = [cand_free[int(j)] for j in idx_free]
    picked_mixed = [cand_mixed[int(j)] for j in idx_mixed]
    # Interleave free and mixed so monoids[:6] = 3 free + 3 mixed
    monoids = [x for pair in zip(picked_free, picked_mixed) for x in pair]
    picked_free_ids = {r["id"] for r in picked_free}
    reserved_free_ids = sorted(r["id"] for r in cand_free if r["id"] not in picked_free_ids)

    P77 = json.loads((RESULTS / "spike77_predictions.json").read_text())
    P78 = json.loads((RESULTS / "spike78_predictions.json").read_text())
    used_groups = set(S77.USED) | set(P77["automata"]) | set(P78["sample"]) | PRIOR_MP_GROUPS
    S71.spec = S77.spec
    S71._patch()
    cand_groups = {}
    for name in sorted(S77.POOL):
        if name in used_groups:
            continue
        grp, L_let, out_fn = S77.spec(name)
        idx = {g: i for i, g in enumerate(grp)}
        m = len(grp)
        Dl = np.array([[idx[S58.comp(g, a)] for g in grp] for a in L_let], dtype=int)
        O = np.array([out_fn(g) for g in grp], float)
        pi = np.ones(m) / m
        ops = base_operators(Dl, O, pi)
        G0, _ = eval_sandwich(ops["Lkin"], ops["Wc"], ops["Wo"], pi, LAM0)
        irs = S69.real_irreps(grp)
        labels = [S69.irrep_label(ir, k) for k, ir in enumerate(irs)]
        F = S77.feats(name)
        pg = S77.probs(F, S77.ALPHA, S77.LAMBDA)
        pe = S77.probs(F, P77["energy_alpha"], 0.0)
        ps = S77.probs(F, 0.0, P77["smooth_lambda"])
        mg, me, ms = max(pg, key=pg.get), max(pe, key=pe.get), max(ps, key=ps.get)
        ev, EV = np.linalg.eigh(G0)
        tol = 1e-6 * max(float(ev.max()), 1e-12)
        top_cols = EV[:, ev >= ev[-1] - tol]
        sh_G = S71.shares(top_cols, irs)
        lead_G = labels[int(np.argmax(sh_G))]
        if pg[mg] >= 0.6 and (lead_G != me or lead_G != ms):
            cand_groups[name] = {
                "name": name,
                "order": int(m),
                "k_out": int(O.shape[1]),
                "Dl": Dl.tolist(),
                "O": O.tolist(),
                "s0": int(idx[tuple(range(len(grp[0])))]),
                "pi": pi.tolist(),
                "Lkin": ops["Lkin"].tolist(),
                "Wo": ops["Wo"].tolist(),
                "Wc": ops["Wc"].tolist(),
                "G_lam0": G0.tolist(),
                "lead_G": lead_G,
                "gibbs": mg,
                "energy": me,
                "smooth": ms,
                "pmax": float(pg[mg]),
            }

    picked_group_names: list[str] = []
    by_prefix: dict[str, list[str]] = {}
    for nm in sorted(cand_groups):
        by_prefix.setdefault(nm.split("_")[0], []).append(nm)
    for pref in sorted(by_prefix):
        if len(picked_group_names) >= 6:
            break
        opts = by_prefix[pref]
        picked_group_names.append(opts[int(rng.integers(len(opts)))])
    if len(picked_group_names) < 6:
        rem = [nm for nm in sorted(cand_groups) if nm not in picked_group_names]
        picked_group_names += [rem[int(j)] for j in rng.choice(len(rem), size=6 - len(picked_group_names), replace=False)]
    groups = [cand_groups[nm] for nm in picked_group_names]

    out = {
        "constants": {"gamma_c": GAMMA_C, "gamma_o": GAMMA_O, "T_op": T_OP,
                      "lam0": LAM0, "lam_cal": LAM_CAL, "lam_kin": LAM_KIN},
        "excluded_monoids_count": len(excluded_monoids),
        "n_eligible_free": len(cand_free),
        "n_eligible_mixed": len(cand_mixed),
        "reserved_free_monoids_for_transformer": reserved_free_ids,
        "n_candidate_groups": len(cand_groups),
        "monoids": monoids,
        "groups": groups,
    }
    PRED.parent.mkdir(parents=True, exist_ok=True)
    PRED.write_text(json.dumps(out))
    print(f"LAM0={LAM0:.6f} LAM_CAL={LAM_CAL} LAM_KIN={LAM_KIN}")
    print(f"Eligible fresh monoids: free={len(cand_free)}, mixed={len(cand_mixed)} (excluded={len(excluded_monoids)})")
    print(f"Picked 12 monoids: {[r['id'] for r in monoids]} (reserved 8 free={reserved_free_ids})")
    print(f"Eligible fresh discriminating groups: {len(cand_groups)}; picked 6: {picked_group_names}")


def fast_sample(Dl: np.ndarray, O: np.ndarray, s0: int, B: int, T: int, rng: np.random.Generator):
    import torch
    L = Dl.shape[0]
    X = rng.integers(0, L, size=(B, T))
    ST = np.empty((B, T), dtype=np.int64)
    q = np.full(B, s0, dtype=np.int64)
    for t in range(T):
        q = Dl[X[:, t], q]
        ST[:, t] = q
    O_mat = O[:, None] if O.ndim == 1 else O
    Y = O_mat[ST].astype(np.float32)
    return torch.from_numpy(X).long(), torch.from_numpy(Y), ST


def make_model(arch: str, L: int, k_out: int, alpha: float = 1.0):
    import torch
    nn = torch.nn

    def mlp_head():
        return nn.Sequential(nn.Linear(64, 64), nn.Tanh(), nn.Linear(64, 64), nn.Tanh(), nn.Linear(64, k_out))

    class Net(nn.Module):
        def __init__(s):
            super().__init__()
            s.e = nn.Embedding(L, 16)
            s.arch = arch
            s.alpha = alpha
            if arch in ("gru_lin", "gru_mlp"):
                s.r = nn.GRU(16, 64, batch_first=True)
            elif arch == "lstm_mlp":
                s.r = nn.LSTM(16, 64, batch_first=True)
            elif arch == "rnn_mlp":
                s.r = nn.RNN(16, 64, nonlinearity="tanh", batch_first=True)
                nn.init.orthogonal_(s.r.weight_hh_l0)
            elif arch == "leaky_rnn":
                s.cell = nn.RNNCell(16, 64, nonlinearity="tanh")
                nn.init.orthogonal_(s.cell.weight_hh)
            else:
                raise ValueError(arch)
            s.h = nn.Linear(64, k_out) if arch == "gru_lin" else mlp_head()

        def hidden(s, X):
            emb = s.e(X)
            if s.arch == "leaky_rnn":
                h = torch.zeros(X.shape[0], 64)
                outs = []
                a = s.alpha
                for t in range(X.shape[1]):
                    h_cand = s.cell(emb[:, t], h)
                    h = (1.0 - a) * h + a * h_cand if a < 1.0 else h_cand
                    outs.append(h)
                return torch.stack(outs, 1)
            return s.r(emb)[0]

        def forward(s, X):
            return s.h(s.hidden(X))

    return Net()


def extract_centroids(mdl, Dl: np.ndarray, O: np.ndarray, s0: int, m: int, seed: int) -> np.ndarray:
    import torch
    mdl.eval()
    with torch.no_grad():
        Xv, _, ST = fast_sample(Dl, O, s0, 400, SEQ_LEN, np.random.default_rng(seed + 2_000_000))
        H = mdl.hidden(Xv).numpy()
    flatH = H[:, BURN:].reshape(-1, 64)
    flatL = ST[:, BURN:].ravel()
    Ce = np.stack([flatH[flatL == q].mean(0) if (flatL == q).any() else np.full(64, np.nan) for q in range(m)])
    mdl.train()
    return Ce


def measure_gram(Ce: np.ndarray, pi: np.ndarray, ops: dict) -> dict | None:
    if np.isnan(Ce).any():
        return None
    W = np.sqrt(pi)
    one = W / np.linalg.norm(W)
    mu = (pi[:, None] * Ce).sum(0)
    X = W[:, None] * (Ce - mu)
    X = X - np.outer(one, one @ X)
    Gl = X @ X.T
    tr = max(float(np.trace(Gl)), 1e-12)
    kin_norm = float(np.trace(Gl @ ops["Lkin"]) / tr)
    lam_emp = invert_lambda_from_kin(ops["Lkin"], ops["WcWo_noheat"], kin_obs=kin_norm)

    res = {
        "kin_norm": kin_norm,
        "lam_emp": lam_emp,
        "cos_WcWo_noheat": cos_mat(Gl, ops["WcWo_noheat"]),
        "cos_Wo": cos_mat(Gl, ops["Wo"]),
        "cos_Wc": cos_mat(Gl, ops["Wc"]),
        "cos_o": cos_mat(Gl, ops["o"]),
        "cos_k1": cos_mat(Gl, ops["k1"]),
        "cos_G_lam0": cos_mat(Gl, ops["G_lam0"]),
        "cos_Wo_heat_lam0": cos_mat(Gl, ops["Wo_heat_lam0"]),
    }
    for arch in ("gru_lin", "gru_mlp", "lstm_mlp", "rnn_mlp"):
        if f"G_cal_{arch}" in ops:
            res[f"cos_G_cal_{arch}"] = cos_mat(Gl, ops[f"G_cal_{arch}"])
            res[f"cos_Wo_heat_cal_{arch}"] = cos_mat(Gl, ops[f"Wo_heat_cal_{arch}"])
            res[f"cos_G_kin_{arch}"] = cos_mat(Gl, ops[f"G_kin_{arch}"])
            res[f"cos_Wo_heat_kin_{arch}"] = cos_mat(Gl, ops[f"Wo_heat_kin_{arch}"])
    return res


def train_one(Dl: np.ndarray, O: np.ndarray, s0: int, m: int, arch: str,
              steps: int, lr: float, seed: int, *, alpha: float = 1.0,
              wd: float = 0.0, dirichlet_mu: float = 0.0, clip_norm: float | None = None):
    import torch
    nn = torch.nn
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    L = Dl.shape[0]
    k_out = 1 if O.ndim == 1 else O.shape[1]
    mdl = make_model(arch, L, k_out, alpha=alpha)
    opt = torch.optim.AdamW(mdl.parameters(), lr=lr, weight_decay=wd)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps)
    for _ in range(steps):
        X, Y, _ = fast_sample(Dl, O, s0, BATCH, SEQ_LEN, rng)
        H = mdl.hidden(X)
        logits = mdl.h(H)
        loss = nn.functional.binary_cross_entropy_with_logits(logits, Y)
        if dirichlet_mu > 0.0:
            H_st = H[:, BURN:]
            dh = (H_st[:, 1:] - H_st[:, :-1]).pow(2).mean()
            var_h = (H_st - H_st.mean(dim=(0, 1), keepdim=True)).pow(2).mean().clamp_min(1e-4)
            loss = loss + dirichlet_mu * (dh / var_h)
        opt.zero_grad()
        loss.backward()
        if clip_norm is not None:
            nn.utils.clip_grad_norm_(mdl.parameters(), clip_norm)
        opt.step()
        sch.step()

    mdl.eval()
    with torch.no_grad():
        Xv, Yv, _ = fast_sample(Dl, O, s0, 500, 100, np.random.default_rng(seed + 1_000_000))
        fit = float(((mdl(Xv) > 0).float() == Yv).float().mean())
    Ce = extract_centroids(mdl, Dl, O, s0, m, seed)
    return fit, Ce


def _ops_from_monoid_row(A: dict) -> dict:
    keys = ["Lkin", "Wo", "Wc", "WcWo_noheat", "o", "k1", "G_lam0", "Wo_heat_lam0"]
    for arch in ("gru_lin", "gru_mlp", "lstm_mlp", "rnn_mlp"):
        keys.extend([f"G_cal_{arch}", f"Wo_heat_cal_{arch}", f"G_kin_{arch}", f"Wo_heat_kin_{arch}"])
    return {k: np.array(A[k]) for k in keys if k in A}


def run(which: str | None = None, part: str = "0/1"):
    import torch
    torch.set_num_threads(1)
    RAW.mkdir(parents=True, exist_ok=True)
    P = json.loads(PRED.read_text())
    monoids = P["monoids"]
    groups = P["groups"]

    arms = {"cal", "leaky_m", "leaky_g", "dirichlet", "wd"}
    sel = arms if which is None else {x.strip() for x in which.split(",")}
    k, K = map(int, part.split("/"))
    job_idx = 0

    def take() -> bool:
        nonlocal job_idx
        ok = (job_idx % K) == k
        job_idx += 1
        return ok

    # Arm 1: out-of-sample calibration across 12 fresh monoids and 4 architectures
    if "cal" in sel:
        cfg = [
            ("gru_lin", 1200, 0.004, None, 310_000),
            ("gru_mlp", 1200, 0.004, None, 320_000),
            ("lstm_mlp", 1200, 0.008, None, 330_000),
            ("rnn_mlp", 1500, 0.004, 1.0, 340_000),
        ]
        for arch, steps, lr, cnorm, sbase in cfg:
            for A in monoids:
                if not take():
                    continue
                pth = RAW / f"cal_{arch}_{A['id']}.json"
                if pth.exists():
                    continue
                t0 = time.perf_counter()
                Dl = np.vstack([np.array(A["D"]), np.arange(A["m"])[None]])
                O = np.array(A["out"], float)
                pi = np.array(A["pi"], float)
                ops = _ops_from_monoid_row(A)
                seed = sbase + 10 * A["id"]
                fit, Ce = train_one(Dl, O, A["s0"], A["m"], arch, steps, lr, seed, clip_norm=cnorm)
                res = measure_gram(Ce, pi, ops)
                rec = {"arm": f"cal_{arch}", "arch": arch, "id": A["id"], "kind": A["kind"],
                       "seed": seed, "fit": fit, "res": res, "secs": round(time.perf_counter() - t0, 1)}
                pth.write_text(json.dumps(rec))
                c_k = res[f"cos_G_kin_{arch}"] if res else None
                c_0 = res["cos_G_lam0"] if res else None
                print(f"cal {arch:8s} id={A['id']:3d} fit={fit:.4f} c0={c_0} cKin={c_k} lam={res['lam_emp'] if res else None} ({rec['secs']}s)",
                      flush=True)

    # Helpers for monoid[:6] and groups interventions
    def run_interv_monoid(arm_tag: str, *, alpha: float = 1.0, wd: float = 0.0, dirichlet_mu: float = 0.0):
        for A in monoids[:6]:
            if not take():
                continue
            pth = RAW / f"int_m_{arm_tag}_{A['id']}.json"
            if pth.exists():
                continue
            t0 = time.perf_counter()
            Dl = np.vstack([np.array(A["D"]), np.arange(A["m"])[None]])
            O = np.array(A["out"], float)
            pi = np.array(A["pi"], float)
            Lkin = np.array(A["Lkin"], float)
            Wc = np.array(A["Wc"], float)
            Wo = np.array(A["Wo"], float)
            WcWo = np.array(A["WcWo_noheat"], float)
            seed = 350_000 + 10 * A["id"]
            fit, Ce = train_one(Dl, O, A["s0"], A["m"], "leaky_rnn", 1000, 0.004, seed,
                                alpha=alpha, wd=wd, dirichlet_mu=dirichlet_mu, clip_norm=1.0)
            if np.isnan(Ce).any():
                kin_norm, lam_emp = None, None
            else:
                W = np.sqrt(pi)
                one = W / np.linalg.norm(W)
                mu = (pi[:, None] * Ce).sum(0)
                X = W[:, None] * (Ce - mu)
                X = X - np.outer(one, one @ X)
                Gl = X @ X.T
                kin_norm = float(np.trace(Gl @ Lkin) / max(float(np.trace(Gl)), 1e-12))
                lam_emp = invert_lambda_from_kin(Lkin, WcWo, kin_obs=kin_norm)
            rec = {"arm": arm_tag, "kind": "monoid", "id": A["id"], "alpha": alpha, "wd": wd,
                   "dirichlet_mu": dirichlet_mu, "fit": fit, "kin_norm": kin_norm, "lam_emp": lam_emp,
                   "secs": round(time.perf_counter() - t0, 1)}
            pth.write_text(json.dumps(rec))
            print(f"{arm_tag:14s} M_{A['id']:3d} fit={fit:.4f} kin={kin_norm} lam={lam_emp} ({rec['secs']}s)", flush=True)

    def run_interv_group(arm_tag: str, *, alpha: float = 1.0, wd: float = 0.0, dirichlet_mu: float = 0.0):
        for g in groups:
            if not take():
                continue
            pth = RAW / f"int_g_{arm_tag}_{g['name']}.json"
            if pth.exists():
                continue
            t0 = time.perf_counter()
            Dl = np.array(g["Dl"], dtype=int)
            O = np.array(g["O"], float)
            pi = np.array(g["pi"], float)
            Lkin = np.array(g["Lkin"], float)
            WcWo = np.array(g["Wc"], float) + np.array(g["Wo"], float)
            seed = 360_000 + 10 * groups.index(g)
            fit, Ce = train_one(Dl, O, g["s0"], g["order"], "leaky_rnn", 1000, 0.004, seed,
                                alpha=alpha, wd=wd, dirichlet_mu=dirichlet_mu, clip_norm=1.0)
            if np.isnan(Ce).any():
                kin_norm, lam_emp = None, None
            else:
                W = np.sqrt(pi)
                mu = (pi[:, None] * Ce).sum(0)
                X = W[:, None] * (Ce - mu)
                Gl = X @ X.T
                kin_norm = float(np.trace(Gl @ Lkin) / max(float(np.trace(Gl)), 1e-12))
                lam_emp = invert_lambda_from_kin(Lkin, WcWo, kin_obs=kin_norm)
            rec = {"arm": arm_tag, "kind": "group", "name": g["name"], "alpha": alpha, "wd": wd,
                   "dirichlet_mu": dirichlet_mu, "fit": fit, "kin_norm": kin_norm, "lam_emp": lam_emp,
                   "secs": round(time.perf_counter() - t0, 1)}
            pth.write_text(json.dumps(rec))
            print(f"{arm_tag:14s} G_{g['name']:14s} fit={fit:.4f} kin={kin_norm} lam={lam_emp} ({rec['secs']}s)", flush=True)

    if "leaky_m" in sel:
        for a, nm in ((1.0, "alpha_1.0"), (0.5, "alpha_0.5"), (0.25, "alpha_0.25")):
            run_interv_monoid(nm, alpha=a)
    if "leaky_g" in sel:
        for a, nm in ((1.0, "alpha_1.0"), (0.5, "alpha_0.5"), (0.25, "alpha_0.25")):
            run_interv_group(nm, alpha=a)
    if "dirichlet" in sel:
        run_interv_monoid("dirichlet_0.20", alpha=1.0, dirichlet_mu=0.20)
        run_interv_group("dirichlet_0.20", alpha=1.0, dirichlet_mu=0.20)
    if "wd" in sel:
        run_interv_monoid("wd_3e-2", alpha=1.0, wd=3e-2)
        run_interv_group("wd_3e-2", alpha=1.0, wd=3e-2)


def analyse():
    P = json.loads(PRED.read_text())
    info_m = {A["id"]: A for A in P["monoids"]}
    runs = [json.loads(f.read_text()) for f in sorted(RAW.glob("*.json"))]

    tri = lambda val, n_unit, need, hi, lo: (
        "NO VERDICT" if val is None or n_unit < need
        else "HELD" if val >= hi
        else "BROKEN" if val < lo
        else "NEITHER"
    )

    # 1. Calibration summary per architecture (fit >= 0.99)
    cal_summary = {}
    arch_kin_gt_0 = []
    for arch in ("gru_lin", "gru_mlp", "lstm_mlp", "rnn_mlp"):
        rs = [r for r in runs if r["arm"] == f"cal_{arch}" and r["fit"] >= 0.99 and r["res"] is not None]
        if not rs:
            cal_summary[arch] = {"n_fitted": 0}
            continue
        mean_0 = float(np.mean([r["res"]["cos_G_lam0"] for r in rs]))
        mean_cal = float(np.mean([r["res"][f"cos_G_cal_{arch}"] for r in rs]))
        mean_kin = float(np.mean([r["res"][f"cos_G_kin_{arch}"] for r in rs]))
        med_0 = float(np.median([r["res"]["cos_G_lam0"] for r in rs]))
        med_cal = float(np.median([r["res"][f"cos_G_cal_{arch}"] for r in rs]))
        med_kin = float(np.median([r["res"][f"cos_G_kin_{arch}"] for r in rs]))
        rivals_med = {rk: float(np.median([r["res"][rk] for r in rs])) for rk in ("cos_Wo", "cos_Wc", "cos_WcWo_noheat", "cos_o", "cos_k1")}
        rivals_med[f"cos_Wo_heat_kin_{arch}"] = float(np.median([r["res"][f"cos_Wo_heat_kin_{arch}"] for r in rs]))
        rivals_mean = {rk: float(np.mean([r["res"][rk] for r in rs])) for rk in ("cos_Wo", "cos_Wc", "cos_WcWo_noheat", "cos_o", "cos_k1")}
        rivals_mean[f"cos_Wo_heat_kin_{arch}"] = float(np.mean([r["res"][f"cos_Wo_heat_kin_{arch}"] for r in rs]))
        beat_o_disc = [r for r in rs if info_m[r["id"]][f"cos_Gkin_{arch}_o"] < 0.95]
        frac_beat_o = float(np.mean([r["res"][f"cos_G_kin_{arch}"] > r["res"]["cos_o"] for r in beat_o_disc])) if beat_o_disc else None
        cal_summary[arch] = {
            "n_fitted": len(rs),
            "med_lam_emp": float(np.median([r["res"]["lam_emp"] for r in rs])),
            "med_kin_norm": float(np.median([r["res"]["kin_norm"] for r in rs])),
            "mean_cos_G_lam0": mean_0,
            "mean_cos_G_cal": mean_cal,
            "mean_cos_G_kin": mean_kin,
            "med_cos_G_lam0": med_0,
            "med_cos_G_cal": med_cal,
            "med_cos_G_kin": med_kin,
            "rivals_med": rivals_med,
            "rivals_mean": rivals_mean,
            "beat_all_rivals_med": all(med_kin > v for v in rivals_med.values()),
            "beat_all_rivals_mean": all(mean_kin > v for v in rivals_mean.values()),
            "n_disc_o": len(beat_o_disc),
            "frac_kin_beat_o_where_diff": frac_beat_o,
        }
        arch_kin_gt_0.append(mean_kin >= mean_0)

    # 2. Intervention pairings (fit >= 0.90)
    def collect_pairs(arm_tag: str):
        pairs = []
        for kind, key_id in ([("monoid", A["id"]) for A in P["monoids"][:6]] + [("group", g["name"]) for g in P["groups"]]):
            fld = "id" if kind == "monoid" else "name"
            b = [r for r in runs if r["arm"] == "alpha_1.0" and r["kind"] == kind and r.get(fld) == key_id and r["fit"] >= 0.90 and r.get("kin_norm") is not None]
            t = [r for r in runs if r["arm"] == arm_tag and r["kind"] == kind and r.get(fld) == key_id and r["fit"] >= 0.90 and r.get("kin_norm") is not None]
            if b and t:
                pairs.append({
                    "unit": f"{kind[0].upper()}_{key_id}",
                    "kin_base": b[0]["kin_norm"],
                    "kin_arm": t[0]["kin_norm"],
                    "lam_base": b[0]["lam_emp"],
                    "lam_arm": t[0]["lam_emp"],
                    "lower_kin": t[0]["kin_norm"] < b[0]["kin_norm"],
                    "higher_lam": t[0]["lam_emp"] > b[0]["lam_emp"],
                })
        return pairs

    p_05 = collect_pairs("alpha_0.5")
    p_025 = collect_pairs("alpha_0.25")
    p_dir = collect_pairs("dirichlet_0.20")
    p_wd = collect_pairs("wd_3e-2")

    # Monotone a=1.0 -> 0.5 -> 0.25 per unit
    mono_units = []
    by_05 = {x["unit"]: x for x in p_05}
    for x25 in p_025:
        u = x25["unit"]
        if u in by_05:
            x05 = by_05[u]
            mono_units.append({
                "unit": u,
                "k10": x25["kin_base"], "k05": x05["kin_arm"], "k025": x25["kin_arm"],
                "strict_drop": x25["kin_base"] > x05["kin_arm"] > x25["kin_arm"],
                "end_drop": x25["kin_base"] > x25["kin_arm"],
            })

    frac_025_drop = float(np.mean([x["lower_kin"] for x in p_025])) if p_025 else None
    frac_025_lam_up = float(np.mean([x["higher_lam"] for x in p_025])) if p_025 else None
    frac_dir_drop = float(np.mean([x["lower_kin"] for x in p_dir])) if p_dir else None
    frac_wd_drop = float(np.mean([x["lower_kin"] for x in p_wd])) if p_wd else None

    verdicts = {}
    if len(arch_kin_gt_0) < 4:
        verdicts["HMM.1a"] = "NO VERDICT"
    else:
        frac_arch = float(np.mean(arch_kin_gt_0))
        verdicts["HMM.1a"] = "HELD" if frac_arch >= 0.75 else ("BROKEN" if frac_arch < 0.50 else "NEITHER")

    rnn_s = cal_summary.get("rnn_mlp", {})
    lstm_s = cal_summary.get("lstm_mlp", {})
    if rnn_s.get("n_fitted", 0) < 8 or lstm_s.get("n_fitted", 0) < 8:
        verdicts["HMM.1b"] = "NO VERDICT"
    elif (rnn_s["beat_all_rivals_mean"] and lstm_s["beat_all_rivals_mean"]
          and (rnn_s["frac_kin_beat_o_where_diff"] or 0.0) >= 0.70):
        verdicts["HMM.1b"] = "HELD"
    elif (not rnn_s["beat_all_rivals_mean"]) or (not lstm_s["beat_all_rivals_mean"]):
        verdicts["HMM.1b"] = "BROKEN"
    else:
        verdicts["HMM.1b"] = "NEITHER"

    if len(arch_kin_gt_0) < 4:
        verdicts["HMM.2"] = "NO VERDICT"
    else:
        gaps = [abs(cal_summary[a]["mean_cos_G_kin"] - cal_summary[a]["mean_cos_G_cal"]) for a in cal_summary]
        max_gap = max(gaps)
        verdicts["HMM.2"] = "HELD" if max_gap <= 0.02 else ("BROKEN" if max_gap > 0.05 else "NEITHER")

    verdicts["HMM.3"] = tri(frac_025_drop, len(p_025), 8, 0.75, 0.50)
    verdicts["HMM.4"] = tri(frac_dir_drop, len(p_dir), 8, 0.75, 0.50)
    if frac_wd_drop is None or len(p_wd) < 8 or frac_025_drop is None or frac_dir_drop is None:
        verdicts["HMM.5"] = "NO VERDICT"
    elif frac_wd_drop < frac_025_drop and frac_wd_drop < frac_dir_drop:
        verdicts["HMM.5"] = "HELD"
    else:
        verdicts["HMM.5"] = "BROKEN"

    summary = {
        "verdicts": verdicts,
        "calibration": cal_summary,
        "interventions": {
            "alpha_0.5": {"n": len(p_05), "frac_lower_kin": float(np.mean([x["lower_kin"] for x in p_05])) if p_05 else None, "pairs": p_05},
            "alpha_0.25": {"n": len(p_025), "frac_lower_kin": frac_025_drop, "frac_higher_lam": frac_025_lam_up, "pairs": p_025},
            "monotone_chain": {"n": len(mono_units), "strict_drop_frac": float(np.mean([x["strict_drop"] for x in mono_units])) if mono_units else None, "units": mono_units},
            "dirichlet_0.20": {"n": len(p_dir), "frac_lower_kin": frac_dir_drop, "pairs": p_dir},
            "wd_3e-2": {"n": len(p_wd), "frac_lower_kin": frac_wd_drop, "pairs": p_wd},
        },
    }
    OUT.write_text(json.dumps(summary, indent=1))
    print(json.dumps({"verdicts": verdicts, "calibration": cal_summary,
                      "interventions": {k: {kk: vv for kk, vv in v.items() if kk != "pairs" and kk != "units"}
                                        for k, v in summary["interventions"].items()}}, indent=2))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "run":
        run(sys.argv[2] if len(sys.argv) > 2 else None,
            sys.argv[3] if len(sys.argv) > 3 else "0/1")
    else:
        {"predict": predict, "analyse": analyse}[cmd]()
