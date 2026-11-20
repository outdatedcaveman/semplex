"""Pre-registered multi-substrate test of the Two-Sided Causal-Kinetic Master Principle:

  G(lam) = P_perp exp(-lam/2 L_kin) (W_c(gamma_c) + W_o(gamma_o)) exp(-lam/2 L_kin) P_perp

evaluated in L^2(pi) with ZERO free parameter tuning:
  gamma_c = 0.6, gamma_o = 0.7, T_op = 30,
  lam_0 = lambda_S77 / alpha_S77 (= 3.6753248 / 2.4893651 = 1.476410..., frozen from Spike 77).

Covers:
  - Arm 1 (gru_mlp): GRU + 3-layer tanh MLP on 12 FRESH irreversible monoids (saves step0 + final centroids)
  - Arm 2 (gru_lin): GRU + linear readout on the same 12 monoids
  - Arm 3 (lstm_mlp, rnn_mlp, spec): LSTM-MLP, orthogonal-init clipped tanh RNN-MLP, and Hankel-SVD (SPEC)
  - Arm 4 (grp): GRU-LIN + GRU-MLP on 6 FRESH discriminating group automata (exact unification check)
  - Arm 5 (noise): state-noise causal intervention (eta = 0.20) on 6 monoids + 6 groups vs eta = 0.0

Usage:
  python -m experiments.master_principle predict
  python -m experiments.master_principle run [arm]    # arm in gru_mlp,gru_lin,lstm_mlp,rnn_mlp,spec,grp,noise
  python -m experiments.master_principle analyse

Pre-registered criteria (HM.1-HM.5) in HANDOFF_MASTER_PRINCIPLE.md.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import time
from collections import Counter

import numpy as np
from scipy.linalg import expm

from experiments import spike58 as S58
from experiments import spike69 as S69
from experiments import spike71 as S71
from experiments import spike77 as S77
from experiments import spike78 as S78
from experiments import spike81 as S81
from experiments import spike84 as S84

ROOT = pathlib.Path(__file__).resolve().parent
RAW = ROOT / "results" / "master_principle_raw"
OUT = ROOT / "results" / "master_principle.json"
PRED = ROOT / "results" / "master_principle_predictions.json"

# Frozen Master Operator constants (never tuned on evaluation automata)
GAMMA_C = 0.6
GAMMA_O = 0.7
T_OP = 30
LAM0 = float(S77.LAMBDA / S77.ALPHA)

BATCH = 64
SEQ_LEN = 30
BURN = 5


def cos_mat(A: np.ndarray, B: np.ndarray) -> float:
    na = float(np.linalg.norm(A))
    nb = float(np.linalg.norm(B))
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return float(np.sum(A * B) / (na * nb))


def master_operators(Dl: np.ndarray, O: np.ndarray, pi: np.ndarray,
                     gc: float = GAMMA_C, go: float = GAMMA_O,
                     lam: float = LAM0, T: int = T_OP) -> dict:
    """Compute G(lam) and all mechanistic / ablation operators in sqrt(pi)-weighted centered L^2(pi)."""
    L, m = Dl.shape
    O = np.asarray(O, float)
    if O.ndim == 1:
        O = O[:, None]
    W = np.sqrt(pi)
    one = W / np.linalg.norm(W)
    Pperp = np.eye(m) - np.outer(one, one)

    # T_a = D^{1/2} P_a D^{-1/2} for all letters a in Dl
    Ts = []
    for a in range(L):
        Pa = np.zeros((m, m))
        for q in range(m):
            Pa[q, Dl[a, q]] = 1.0
        Ts.append((W[:, None] * Pa) / W[None, :])

    # Dirichlet kinetic operator L_kin = (1 / 2|A|) sum_a P_perp (T_a - I)^T (T_a - I) P_perp
    Lkin = np.zeros((m, m))
    for Ta in Ts:
        diff = Ta - np.eye(m)
        Lkin += diff.T @ diff
    Lkin = 0.5 / L * (Pperp @ Lkin @ Pperp)
    Lkin = 0.5 * (Lkin + Lkin.T)

    # Future Koopman observability Gramian W_o (unit-variance standardized O, t = 0..T-1)
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

    # Past-reachability chi^2 Gramian W_c (adjoint Perron-Frobenius B_t, t = 1..T-1)
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

    H = expm(-0.5 * lam * Lkin)
    sym = lambda M: Pperp @ (0.5 * (M + M.T)) @ Pperp
    G = sym(H @ (Wc + Wo) @ H)
    Wo_heat = sym(H @ Wo @ H)
    WcWo_noheat = sym(Wc + Wo)

    ev, EV = np.linalg.eigh(G)
    g1 = EV[:, -1]
    ev_k1, EV_k1 = np.linalg.eigh(k1_gram)
    k1_w = EV_k1[:, -1]
    ev_o, EV_o = np.linalg.eigh(o_gram)
    o_w = EV_o[:, -1]

    return {
        "G": G,
        "Wo": Wo,
        "Wo_heat": Wo_heat,
        "Wc": Wc,
        "WcWo_noheat": WcWo_noheat,
        "o": o_gram,
        "k1": k1_gram,
        "Lkin": Lkin,
        "g1_w": g1,
        "o_w": o_w,
        "k1_w": k1_w,
        "cos_G_Woheat": cos_mat(G, Wo_heat),
        "cos_G_o": cos_mat(G, o_gram),
        "cos_G_WcWonoheat": cos_mat(G, WcWo_noheat),
        "wc_over_wo": float(np.linalg.norm(Wc) / max(np.linalg.norm(Wo), 1e-12)),
    }


def _collect_used_monoid_ids() -> set[int]:
    used: set[int] = set()
    for fn in ["spike81.json", "spike84.json", "spike87.json",
               "spike84_predictions.json", "spike87_predictions.json"]:
        p = ROOT / "results" / fn
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
    for rd in ["spike84_raw", "spike87_raw"]:
        rp = ROOT / "results" / rd
        if rp.exists():
            for f in rp.glob("*.json"):
                d = json.loads(f.read_text())
                if isinstance(d.get("id"), int):
                    used.add(d["id"])
    return used


def predict():
    rng = np.random.default_rng(20261120)
    used_monoids = _collect_used_monoid_ids()
    pool = S81.build_pool()
    cand_free, cand_mixed = [], []
    for i, A in enumerate(pool):
        if i in used_monoids:
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
        ops = master_operators(Dl, O, pi)
        row = {
            "id": int(i),
            "kind": A["kind"],
            "D": A["D"],
            "out": A["O"],
            "s0": int(A["s0"]),
            "m": int(Dl.shape[1]),
            "L": int(L := Dl.shape[0]),
            "pi": pi.tolist(),
            "dimO": int(hs["dimO"]),
            "dimH": int(hs["dimH"]),
            "dimR": int(hs["dimR"]),
            "G": ops["G"].tolist(),
            "Wo": ops["Wo"].tolist(),
            "Wo_heat": ops["Wo_heat"].tolist(),
            "Wc": ops["Wc"].tolist(),
            "WcWo_noheat": ops["WcWo_noheat"].tolist(),
            "o": ops["o"].tolist(),
            "k1": ops["k1"].tolist(),
            "Lkin": ops["Lkin"].tolist(),
            "g1_w": ops["g1_w"].tolist(),
            "o_w": ops["o_w"].tolist(),
            "k1_w": ops["k1_w"].tolist(),
            "cos_G_Woheat": ops["cos_G_Woheat"],
            "cos_G_o": ops["cos_G_o"],
            "cos_G_WcWonoheat": ops["cos_G_WcWonoheat"],
            "wc_over_wo": ops["wc_over_wo"],
        }
        if A["kind"] == "free":
            cand_free.append(row)
        elif A["kind"] == "mixed":
            cand_mixed.append(row)

    idx_free = rng.choice(len(cand_free), size=6, replace=False)
    idx_mixed = rng.choice(len(cand_mixed), size=6, replace=False)
    # Interleave free and mixed so first 6 = 3 free + 3 mixed for the noise arm
    picked_free = [cand_free[int(j)] for j in idx_free]
    picked_mixed = [cand_mixed[int(j)] for j in idx_mixed]
    monoids = [x for pair in zip(picked_free, picked_mixed) for x in pair]

    # Fresh discriminating group automata from S77.POOL excluding S77/S78/P77 sets
    P77 = json.loads((ROOT / "results" / "spike77_predictions.json").read_text())
    P78 = json.loads((ROOT / "results" / "spike78_predictions.json").read_text())
    used_groups = set(S77.USED) | set(P77["automata"]) | set(P78["sample"])
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
        ops = master_operators(Dl, O, pi)
        irs = S69.real_irreps(grp)
        labels = [S69.irrep_label(ir, k) for k, ir in enumerate(irs)]
        F = S77.feats(name)
        pg = S77.probs(F, S77.ALPHA, S77.LAMBDA)
        pe = S77.probs(F, P77["energy_alpha"], 0.0)
        ps = S77.probs(F, 0.0, P77["smooth_lambda"])
        mg, me, ms = max(pg, key=pg.get), max(pe, key=pe.get), max(ps, key=ps.get)

        # Leading irrep predicted by Master Operator G(LAM0) (using top eigenspace)
        ev, EV = np.linalg.eigh(ops["G"])
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
                "G": ops["G"].tolist(),
                "wc_norm": float(np.linalg.norm(ops["Wc"])),
                "lead_G": lead_G,
                "gibbs": mg,
                "energy": me,
                "smooth": ms,
                "pmax": float(pg[mg]),
            }

    # Diversify across group families
    picked_group_names = []
    by_prefix: dict[str, list[str]] = {}
    for nm in sorted(cand_groups):
        pref = nm.split("_")[0]
        by_prefix.setdefault(pref, []).append(nm)
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
        "constants": {"gamma_c": GAMMA_C, "gamma_o": GAMMA_O, "T_op": T_OP, "lam0": LAM0},
        "excluded_monoid_ids_count": len(used_monoids),
        "n_eligible_free": len(cand_free),
        "n_eligible_mixed": len(cand_mixed),
        "n_candidate_groups": len(cand_groups),
        "monoids": monoids,
        "groups": groups,
    }
    PRED.parent.mkdir(parents=True, exist_ok=True)
    PRED.write_text(json.dumps(out))

    print(f"LAM0 = {LAM0:.6f} (gamma_c={GAMMA_C}, gamma_o={GAMMA_O}, T_op={T_OP})")
    print(f"Eligible fresh monoids: free={len(cand_free)}, mixed={len(cand_mixed)} (excluded {len(used_monoids)})")
    print("Picked 12 monoids:")
    for r in monoids:
        print(f"  id={r['id']:3d} kind={r['kind']:5s} m={r['m']} cos(G,Wo_h)={r['cos_G_Woheat']:.2f} "
              f"cos(G,o)={r['cos_G_o']:.2f} cos(G,noheat)={r['cos_G_WcWonoheat']:.2f} |Wc|/|Wo|={r['wc_over_wo']:.2f}")
    print(f"Eligible fresh discriminating groups: {len(cand_groups)}")
    print("Picked 6 groups:")
    for g in groups:
        print(f"  {g['name']:14s} |G|={g['order']:2d} |Wc|={g['wc_norm']:.1e} lead_G={g['lead_G']:12s} "
              f"gibbs={g['gibbs']:12s} energy={g['energy']:12s} smooth={g['smooth']:12s}")


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


def make_neural_model(arch: str, L: int, k_out: int, eta: float = 0.0):
    import torch
    nn = torch.nn

    def mlp_head():
        return nn.Sequential(nn.Linear(64, 64), nn.Tanh(), nn.Linear(64, 64), nn.Tanh(), nn.Linear(64, k_out))

    class Net(nn.Module):
        def __init__(s):
            super().__init__()
            s.e = nn.Embedding(L, 16)
            s.arch = arch
            s.eta = eta
            if arch in ("gru_lin", "gru_mlp"):
                s.r = nn.GRU(16, 64, batch_first=True)
            elif arch == "gru_noise":
                s.r = nn.GRUCell(16, 64)
            elif arch == "lstm_mlp":
                s.r = nn.LSTM(16, 64, batch_first=True)
            elif arch == "rnn_mlp":
                s.r = nn.RNN(16, 64, nonlinearity="tanh", batch_first=True)
                nn.init.orthogonal_(s.r.weight_hh_l0)
            else:
                raise ValueError(arch)
            s.h = nn.Linear(64, k_out) if arch == "gru_lin" else mlp_head()

        def hidden(s, X, noise: bool = False):
            emb = s.e(X)
            if s.arch == "gru_noise":
                h = torch.zeros(X.shape[0], 64)
                outs = []
                for t in range(X.shape[1]):
                    h = s.r(emb[:, t], h)
                    if noise and s.eta > 0:
                        h = h + s.eta * torch.randn_like(h)
                    outs.append(h)
                return torch.stack(outs, 1)
            return s.r(emb)[0]

        def forward(s, X, noise: bool = False):
            return s.h(s.hidden(X, noise=noise))

    return Net()


def extract_centroids(mdl, Dl: np.ndarray, O: np.ndarray, s0: int, m: int, seed: int) -> np.ndarray:
    import torch
    mdl.eval()
    with torch.no_grad():
        Xv, _, ST = fast_sample(Dl, O, s0, 400, SEQ_LEN, np.random.default_rng(seed + 2_000_000))
        H = mdl.hidden(Xv, noise=False).numpy()
    flatH = H[:, BURN:].reshape(-1, 64)
    flatL = ST[:, BURN:].ravel()
    Ce = np.stack([flatH[flatL == q].mean(0) if (flatL == q).any() else np.full(64, np.nan) for q in range(m)])
    mdl.train()
    return Ce


def measure_state_gram(Ce: np.ndarray, pi: np.ndarray, ops: dict) -> dict | None:
    if np.isnan(Ce).any():
        return None
    W = np.sqrt(pi)
    one = W / np.linalg.norm(W)
    mu = (pi[:, None] * Ce).sum(0)
    X = W[:, None] * (Ce - mu)
    X = X - np.outer(one, one @ X)
    Gl = X @ X.T
    U, s, _ = np.linalg.svd(X, full_matrices=False)
    u1 = U[:, 0]

    res = {
        "cos_G": cos_mat(Gl, ops["G"]),
        "cos_Wo_heat": cos_mat(Gl, ops["Wo_heat"]),
        "cos_WcWo_noheat": cos_mat(Gl, ops["WcWo_noheat"]),
        "cos_Wo": cos_mat(Gl, ops["Wo"]),
        "cos_Wc": cos_mat(Gl, ops["Wc"]),
        "cos_o": cos_mat(Gl, ops["o"]),
        "cos_k1": cos_mat(Gl, ops["k1"]),
        "u1_G": float((u1 @ ops["g1_w"]) ** 2),
        "u1_o": float((u1 @ ops["o_w"]) ** 2),
        "u1_k1": float((u1 @ ops["k1_w"]) ** 2),
        "kin_norm": float(np.trace(Gl @ ops["Lkin"]) / max(np.trace(Gl), 1e-12)),
        "top_var_share": float((s[0] ** 2) / max(float(np.sum(s ** 2)), 1e-12)),
    }
    return res


def train_neural(Dl: np.ndarray, O: np.ndarray, s0: int, m: int, arch: str,
                 steps: int, lr: float, seed: int, eta: float = 0.0,
                 clip_norm: float | None = None, save_step0: bool = False):
    import torch
    nn = torch.nn
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    L = Dl.shape[0]
    k_out = 1 if O.ndim == 1 else O.shape[1]
    mdl = make_neural_model(arch, L, k_out, eta=eta)
    Ce0 = extract_centroids(mdl, Dl, O, s0, m, seed) if save_step0 else None

    opt = torch.optim.AdamW(mdl.parameters(), lr=lr, weight_decay=0.0)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps)
    for _ in range(steps):
        X, Y, _ = fast_sample(Dl, O, s0, BATCH, SEQ_LEN, rng)
        loss = nn.functional.binary_cross_entropy_with_logits(mdl(X, noise=(eta > 0)), Y)
        opt.zero_grad()
        loss.backward()
        if clip_norm is not None:
            nn.utils.clip_grad_norm_(mdl.parameters(), clip_norm)
        opt.step()
        sch.step()

    mdl.eval()
    with torch.no_grad():
        Xv, Yv, _ = fast_sample(Dl, O, s0, 500, 100, np.random.default_rng(seed + 1_000_000))
        fit = float(((mdl(Xv, noise=False) > 0).float() == Yv).float().mean())
    Ce = extract_centroids(mdl, Dl, O, s0, m, seed)
    return fit, Ce, Ce0


def run_spec_one(Dl: np.ndarray, O: np.ndarray, s0: int, m: int, seed: int = 42):
    """Exact Hankel-SVD spectral realization (no recurrence, no gradients)."""
    rng = np.random.default_rng(seed)
    L = Dl.shape[0]
    sufs = [rng.integers(0, L, size=rng.integers(0, 9)) for _ in range(400)]
    F = np.zeros((m, len(sufs)))
    for j, s in enumerate(sufs):
        q = np.arange(m)
        for a in s:
            q = Dl[a, q]
        F[:, j] = O[q]
    return 1.0, F


def _ops_from_row(A: dict) -> dict:
    return {k: np.array(A[k]) for k in ("G", "Wo", "Wo_heat", "Wc", "WcWo_noheat", "o", "k1", "Lkin", "g1_w", "o_w", "k1_w")}


def run(which: str | None = None):
    import torch
    torch.set_num_threads(4)
    RAW.mkdir(parents=True, exist_ok=True)
    P = json.loads(PRED.read_text())
    monoids = P["monoids"]
    groups = P["groups"]

    arms = {"gru_mlp", "gru_lin", "lstm_mlp", "rnn_mlp", "spec", "grp", "noise"}
    sel = arms if which is None else {x.strip() for x in which.split(",")}

    def run_monoid_arm(tag: str, arch: str, n_seeds: int, steps: int, lr: float,
                       seed_base: int, clip_norm: float | None = None, save_step0: bool = False):
        for A in monoids:
            Dl = np.vstack([np.array(A["D"]), np.arange(A["m"])[None]])
            O = np.array(A["out"], float)
            pi = np.array(A["pi"], float)
            ops = _ops_from_row(A)
            for s_idx in range(n_seeds):
                pth = RAW / f"{tag}_{A['id']}_{s_idx}.json"
                if pth.exists():
                    continue
                t0 = time.perf_counter()
                seed = seed_base + 10 * A["id"] + s_idx
                fit, Ce, Ce0 = train_neural(Dl, O, A["s0"], A["m"], arch, steps, lr, seed,
                                            clip_norm=clip_norm, save_step0=save_step0)
                np.save(RAW / f"{tag}_{A['id']}_{s_idx}_centroids.npy", Ce)
                res0 = None
                if save_step0 and Ce0 is not None:
                    np.save(RAW / f"{tag}_{A['id']}_{s_idx}_step0_centroids.npy", Ce0)
                    res0 = measure_state_gram(Ce0, pi, ops)
                res = measure_state_gram(Ce, pi, ops)
                rec = {"arm": tag, "id": A["id"], "kind": A["kind"], "seed": seed,
                       "fit": fit, "res": res, "res0": res0, "secs": round(time.perf_counter() - t0, 1)}
                pth.write_text(json.dumps(rec))
                print(f"{tag:8s} id={A['id']:3d} ({A['kind']:5s}) s={s_idx} fit={fit:.4f} "
                      f"cosG={res['cos_G']:.3f} cosWoH={res['cos_Wo_heat']:.3f} cos_o={res['cos_o']:.3f} ({rec['secs']}s)",
                      flush=True)

    if "gru_mlp" in sel:
        run_monoid_arm("gru_mlp", "gru_mlp", 3, 2000, 0.004, 210_000, save_step0=True)
    if "gru_lin" in sel:
        run_monoid_arm("gru_lin", "gru_lin", 2, 2000, 0.004, 220_000)
    if "lstm_mlp" in sel:
        run_monoid_arm("lstm_mlp", "lstm_mlp", 2, 1500, 0.008, 230_000)
    if "rnn_mlp" in sel:
        run_monoid_arm("rnn_mlp", "rnn_mlp", 2, 2500, 0.004, 240_000, clip_norm=1.0)

    if "spec" in sel:
        for A in monoids:
            pth = RAW / f"spec_{A['id']}_0.json"
            if pth.exists():
                continue
            Dl = np.vstack([np.array(A["D"]), np.arange(A["m"])[None]])
            O = np.array(A["out"], float)
            pi = np.array(A["pi"], float)
            ops = _ops_from_row(A)
            fit, F = run_spec_one(Dl, O, A["s0"], A["m"], 250_000 + A["id"])
            res = measure_state_gram(F, pi, ops)
            rec = {"arm": "spec", "id": A["id"], "kind": A["kind"], "seed": 250_000 + A["id"], "fit": fit, "res": res}
            pth.write_text(json.dumps(rec))
            print(f"spec     id={A['id']:3d} cos_Wo={res['cos_Wo']:.3f} cos_G={res['cos_G']:.3f}", flush=True)

    if "grp" in sel:
        for arch in ("gru_lin", "gru_mlp"):
            for g in groups:
                Dl = np.array(g["Dl"], dtype=int)
                O = np.array(g["O"], float)
                pi = np.array(g["pi"], float)
                Lkin = np.array(g["Lkin"], float)
                Gop = np.array(g["G"], float)
                grp_list, _, _ = S77.spec(g["name"])
                irs = S69.real_irreps(grp_list)
                labels = [S69.irrep_label(ir, k) for k, ir in enumerate(irs)]
                for s_idx in range(3):
                    pth = RAW / f"grp_{arch}_{g['name']}_{s_idx}.json"
                    if pth.exists():
                        continue
                    t0 = time.perf_counter()
                    seed = 260_000 + (0 if arch == "gru_lin" else 5000) + 10 * groups.index(g) + s_idx
                    fit, Ce, _ = train_neural(Dl, O, g["s0"], g["order"], arch, 2500, 0.004, seed)
                    np.save(RAW / f"grp_{arch}_{g['name']}_{s_idx}_centroids.npy", Ce)
                    if np.isnan(Ce).any():
                        rec = {"arm": "grp", "arch": arch, "name": g["name"], "seed": seed, "fit": fit, "ok": False}
                    else:
                        C1 = Ce - Ce.mean(0)
                        C1 = C1 / np.maximum(np.linalg.norm(C1, axis=1, keepdims=True), 1e-12)
                        sh = S71.shares(C1, irs)
                        leader = labels[int(np.argmax(sh))]
                        W = np.sqrt(pi)
                        mu = (pi[:, None] * Ce).sum(0)
                        X = W[:, None] * (Ce - mu)
                        Gl = X @ X.T
                        kin_norm = float(np.trace(Gl @ Lkin) / max(np.trace(Gl), 1e-12))
                        rec = {"arm": "grp", "arch": arch, "name": g["name"], "seed": seed, "fit": fit, "ok": True,
                               "leader": leader, "cos_G": cos_mat(Gl, Gop), "kin_norm": kin_norm,
                               "secs": round(time.perf_counter() - t0, 1)}
                    pth.write_text(json.dumps(rec))
                    print(f"grp {arch:7s} {g['name']:14s} s={s_idx} fit={fit:.4f} lead={rec.get('leader')} pred={g['lead_G']}",
                          flush=True)

    if "noise" in sel:
        # First 6 monoids (3 free + 3 mixed) + all 6 fresh groups with eta = 0.20
        for A in monoids[:6]:
            Dl = np.vstack([np.array(A["D"]), np.arange(A["m"])[None]])
            O = np.array(A["out"], float)
            pi = np.array(A["pi"], float)
            ops = _ops_from_row(A)
            for s_idx in range(2):
                pth = RAW / f"noise_m_{A['id']}_{s_idx}.json"
                if pth.exists():
                    continue
                t0 = time.perf_counter()
                seed = 270_000 + 10 * A["id"] + s_idx
                fit, Ce, _ = train_neural(Dl, O, A["s0"], A["m"], "gru_noise", 2500, 0.004, seed, eta=0.20)
                np.save(RAW / f"noise_m_{A['id']}_{s_idx}_centroids.npy", Ce)
                res = measure_state_gram(Ce, pi, ops)
                rec = {"arm": "noise", "kind": "monoid", "id": A["id"], "seed": seed, "fit": fit, "res": res,
                       "secs": round(time.perf_counter() - t0, 1)}
                pth.write_text(json.dumps(rec))
                print(f"noise-M  id={A['id']:3d} s={s_idx} fit={fit:.4f} kin={res['kin_norm'] if res else None}", flush=True)
        for g in groups:
            Dl = np.array(g["Dl"], dtype=int)
            O = np.array(g["O"], float)
            pi = np.array(g["pi"], float)
            Lkin = np.array(g["Lkin"], float)
            for s_idx in range(2):
                pth = RAW / f"noise_g_{g['name']}_{s_idx}.json"
                if pth.exists():
                    continue
                t0 = time.perf_counter()
                seed = 280_000 + 10 * groups.index(g) + s_idx
                fit, Ce, _ = train_neural(Dl, O, g["s0"], g["order"], "gru_noise", 2500, 0.004, seed, eta=0.20)
                np.save(RAW / f"noise_g_{g['name']}_{s_idx}_centroids.npy", Ce)
                if np.isnan(Ce).any():
                    kin = None
                else:
                    W = np.sqrt(pi)
                    mu = (pi[:, None] * Ce).sum(0)
                    X = W[:, None] * (Ce - mu)
                    Gl = X @ X.T
                    kin = float(np.trace(Gl @ Lkin) / max(np.trace(Gl), 1e-12))
                rec = {"arm": "noise", "kind": "group", "name": g["name"], "seed": seed, "fit": fit,
                       "kin_norm": kin, "secs": round(time.perf_counter() - t0, 1)}
                pth.write_text(json.dumps(rec))
                print(f"noise-G  {g['name']:14s} s={s_idx} fit={fit:.4f} kin={kin}", flush=True)


def analyse():
    P = json.loads(PRED.read_text())
    info_m = {A["id"]: A for A in P["monoids"]}
    info_g = {g["name"]: g for g in P["groups"]}
    files = sorted(RAW.glob("*.json"))
    runs = [json.loads(f.read_text()) for f in files]

    tri = lambda val, n_unit, need, hi, lo: (
        "NO VERDICT" if val is None or n_unit < need
        else "HELD" if val >= hi
        else "BROKEN" if val < lo
        else "NEITHER"
    )

    def monoid_stats(arm: str):
        rs = [r for r in runs if r["arm"] == arm and r["fit"] >= 0.99 and r["res"] is not None]
        n_aut = len({r["id"] for r in rs})
        meds = {k: (float(np.median([r["res"][k] for r in rs])) if rs else None)
                for k in ("cos_G", "cos_Wo_heat", "cos_WcWo_noheat", "cos_Wo", "cos_Wc", "cos_o", "cos_k1",
                          "u1_G", "u1_o", "u1_k1", "top_var_share")}
        means = {k: (float(np.mean([r["res"][k] for r in rs])) if rs else None)
                 for k in ("cos_G", "cos_Wo_heat", "cos_WcWo_noheat", "cos_Wo", "cos_Wc", "cos_o", "cos_k1",
                           "u1_G", "u1_o", "u1_k1")}
        return {"n_total": sum(r["arm"] == arm for r in runs), "n_fitted": len(rs), "n_automata": n_aut,
                "median": meds, "mean": means, "runs": rs}

    st_gmlp = monoid_stats("gru_mlp")
    st_glin = monoid_stats("gru_lin")
    st_lstm = monoid_stats("lstm_mlp")
    st_rnn = monoid_stats("rnn_mlp")
    st_spec = monoid_stats("spec")

    verdicts = {}
    # HM.1a: GRU-MLP median cos(G_learned, G(LAM0)) >= 0.85 held, < 0.70 broken
    verdicts["HM.1a"] = tri(st_gmlp["median"]["cos_G"], st_gmlp["n_automata"], 8, 0.85, 0.70)

    # HM.1b: G(LAM0) beats all 5 rivals in median Gram cosine, beats o where cos(G,o)<0.95 (>=70%),
    # and beats Wo_heat where |Wc|/|Wo|>=0.25 (>=70%)
    r_gmlp = st_gmlp["runs"]
    disc_o = [r for r in r_gmlp if info_m[r["id"]]["cos_G_o"] < 0.95]
    disc_wc = [r for r in r_gmlp if info_m[r["id"]]["wc_over_wo"] >= 0.25]
    hm1b_beat_o = float(np.mean([r["res"]["cos_G"] > r["res"]["cos_o"] for r in disc_o])) if disc_o else None
    hm1b_beat_woh = float(np.mean([r["res"]["cos_G"] > r["res"]["cos_Wo_heat"] for r in disc_wc])) if disc_wc else None
    rivals = ("cos_Wo_heat", "cos_WcWo_noheat", "cos_Wo", "cos_o", "cos_k1")
    hm1b_all_med = bool(r_gmlp) and all(st_gmlp["median"]["cos_G"] > st_gmlp["median"][rk] for rk in rivals)
    hm1b_all_pairs = {rk: (float(np.mean([r["res"]["cos_G"] > r["res"][rk] for r in r_gmlp])) if r_gmlp else None) for rk in rivals}
    n_disc_o = len({r["id"] for r in disc_o})
    n_disc_wc = len({r["id"] for r in disc_wc})
    if hm1b_beat_o is None or hm1b_beat_woh is None or n_disc_o < 4 or n_disc_wc < 4 or not r_gmlp:
        verdicts["HM.1b"] = "NO VERDICT"
    elif hm1b_all_med and hm1b_beat_o >= 0.70 and hm1b_beat_woh >= 0.70:
        verdicts["HM.1b"] = "HELD"
    elif (not hm1b_all_med) or hm1b_beat_o < 0.50 or hm1b_beat_woh < 0.50:
        verdicts["HM.1b"] = "BROKEN"
    else:
        verdicts["HM.1b"] = "NEITHER"

    # HM.2: GRU-LIN median cos(G_learned, G(LAM0)) >= 0.90 AND beats o in Gram cosine on >= 70% of fitted runs
    r_glin = st_glin["runs"]
    hm2_beat_o = float(np.mean([r["res"]["cos_G"] > r["res"]["cos_o"] for r in r_glin])) if r_glin else None
    if not r_glin or st_glin["n_automata"] < 8 or hm2_beat_o is None:
        verdicts["HM.2"] = "NO VERDICT"
    elif st_glin["median"]["cos_G"] >= 0.90 and hm2_beat_o >= 0.70:
        verdicts["HM.2"] = "HELD"
    elif st_glin["median"]["cos_G"] < 0.75 or hm2_beat_o < 0.50:
        verdicts["HM.2"] = "BROKEN"
    else:
        verdicts["HM.2"] = "NEITHER"

    # HM.3a: Both LSTM-MLP and RNN-MLP achieve median cos_G >= 0.80 (>= 6 fitted automata each)
    if st_lstm["n_automata"] < 6 or st_rnn["n_automata"] < 6:
        verdicts["HM.3a"] = "NO VERDICT"
    else:
        m1, m2 = st_lstm["median"]["cos_G"], st_rnn["median"]["cos_G"]
        if m1 >= 0.80 and m2 >= 0.80:
            verdicts["HM.3a"] = "HELD"
        elif m1 < 0.65 or m2 < 0.65:
            verdicts["HM.3a"] = "BROKEN"
        else:
            verdicts["HM.3a"] = "NEITHER"

    # HM.3b: SPEC (non-recurrent Hankel-SVD) aligns closer with Wo than G(LAM0) on >= 75% of monoids
    r_spec = st_spec["runs"]
    hm3b_frac = float(np.mean([r["res"]["cos_Wo"] > r["res"]["cos_G"] for r in r_spec])) if r_spec else None
    verdicts["HM.3b"] = tri(hm3b_frac, len(r_spec), 8, 0.75, 0.50)

    # HM.4: Exact group unification on 6 fresh discriminating group automata
    grp_runs = [r for r in runs if r["arm"] == "grp" and r.get("ok") and r["fit"] >= 0.99]
    n_grp = len({r["name"] for r in grp_runs})
    hm4_acc_G = float(np.mean([r["leader"] == info_g[r["name"]]["lead_G"] for r in grp_runs])) if grp_runs else None
    hm4_acc_E = float(np.mean([r["leader"] == info_g[r["name"]]["energy"] for r in grp_runs])) if grp_runs else None
    hm4_acc_S = float(np.mean([r["leader"] == info_g[r["name"]]["smooth"] for r in grp_runs])) if grp_runs else None
    if hm4_acc_G is None or n_grp < 4:
        verdicts["HM.4"] = "NO VERDICT"
    elif hm4_acc_G >= 0.75 and hm4_acc_G > max(hm4_acc_E, hm4_acc_S):
        verdicts["HM.4"] = "HELD"
    elif hm4_acc_G < 0.50:
        verdicts["HM.4"] = "BROKEN"
    else:
        verdicts["HM.4"] = "NEITHER"

    # HM.5a: State noise eta=0.20 lowers normalized Dirichlet energy kin_norm on >= 75% of tested automata (fit >= 0.90)
    noise_drops = []
    for A in P["monoids"][:6]:
        base = [r["res"]["kin_norm"] for r in runs if r["arm"] == "gru_mlp" and r["id"] == A["id"] and r["fit"] >= 0.90 and r["res"]]
        hi = [r["res"]["kin_norm"] for r in runs if r["arm"] == "noise" and r["kind"] == "monoid" and r["id"] == A["id"] and r["fit"] >= 0.90 and r["res"]]
        if base and hi:
            noise_drops.append({"key": f"M_{A['id']}", "kin0": float(np.mean(base)), "kin_noise": float(np.mean(hi)), "lower": float(np.mean(hi) < np.mean(base))})
    for g in P["groups"]:
        base = [r["kin_norm"] for r in runs if r["arm"] == "grp" and r["arch"] == "gru_mlp" and r["name"] == g["name"] and r["fit"] >= 0.90 and r.get("ok")]
        hi = [r["kin_norm"] for r in runs if r["arm"] == "noise" and r["kind"] == "group" and r["name"] == g["name"] and r["fit"] >= 0.90 and r.get("kin_norm") is not None]
        if base and hi:
            noise_drops.append({"key": f"G_{g['name']}", "kin0": float(np.mean(base)), "kin_noise": float(np.mean(hi)), "lower": float(np.mean(hi) < np.mean(base))})
    hm5a_frac = float(np.mean([d["lower"] for d in noise_drops])) if noise_drops else None
    verdicts["HM.5a"] = tri(hm5a_frac, len(noise_drops), 8, 0.75, 0.50)

    # HM.5b: Step 0 aligns closer to Wc than Wo (>= 75%), AND training increases Wo alignment (>= 80%)
    with0 = [r for r in r_gmlp if r.get("res0") is not None]
    hm5b_step0_wc = float(np.mean([r["res0"]["cos_Wc"] > r["res0"]["cos_Wo"] for r in with0])) if with0 else None
    hm5b_train_wo = float(np.mean([r["res"]["cos_Wo"] > r["res0"]["cos_Wo"] for r in with0])) if with0 else None
    if len(with0) < 12:
        verdicts["HM.5b"] = "NO VERDICT"
    elif hm5b_step0_wc >= 0.75 and hm5b_train_wo >= 0.80:
        verdicts["HM.5b"] = "HELD"
    elif hm5b_step0_wc < 0.50 or hm5b_train_wo < 0.50:
        verdicts["HM.5b"] = "BROKEN"
    else:
        verdicts["HM.5b"] = "NEITHER"

    summary = {
        "verdicts": verdicts,
        "arms": {
            nm: {k: st[k] for k in ("n_total", "n_fitted", "n_automata", "median", "mean")}
            for nm, st in [("gru_mlp", st_gmlp), ("gru_lin", st_glin), ("lstm_mlp", st_lstm),
                           ("rnn_mlp", st_rnn), ("spec", st_spec)]
        },
        "hm1b_detail": {"all_rivals_beaten_median": hm1b_all_med,
                        "beat_o_where_diff_frac": hm1b_beat_o, "n_disc_o_runs": len(disc_o), "n_disc_o_aut": n_disc_o,
                        "beat_Wo_heat_where_Wc_ge_025_frac": hm1b_beat_woh, "n_disc_wc_runs": len(disc_wc), "n_disc_wc_aut": n_disc_wc,
                        "pairwise_all_rivals": hm1b_all_pairs},
        "hm2_detail": {"beat_o_frac": hm2_beat_o},
        "hm3b_detail": {"spec_closer_to_Wo_frac": hm3b_frac},
        "hm4_detail": {"n_fitted": len(grp_runs), "n_groups": n_grp,
                       "acc_G": hm4_acc_G, "acc_energy": hm4_acc_E, "acc_smooth": hm4_acc_S,
                       "by_arch": {arch: float(np.mean([r["leader"] == info_g[r["name"]]["lead_G"]
                                                        for r in grp_runs if r["arch"] == arch]))
                                   if any(r["arch"] == arch for r in grp_runs) else None
                                   for arch in ("gru_lin", "gru_mlp")}},
        "hm5a_detail": {"frac_lower_kin": hm5a_frac, "n_pairs": len(noise_drops), "pairs": noise_drops},
        "hm5b_detail": {"n_runs": len(with0), "step0_Wc_gt_Wo": hm5b_step0_wc, "train_raises_Wo": hm5b_train_wo,
                        "med_step0_cosWc": float(np.median([r["res0"]["cos_Wc"] for r in with0])) if with0 else None,
                        "med_step0_cosWo": float(np.median([r["res0"]["cos_Wo"] for r in with0])) if with0 else None},
    }
    OUT.write_text(json.dumps(summary, indent=1))
    print(json.dumps({k: summary[k] for k in ("verdicts", "hm1b_detail", "hm2_detail", "hm3b_detail", "hm4_detail", "hm5b_detail")}, indent=2))
    print("HM.5a pairs:", hm5a_frac, "of", len(noise_drops))
    for nm, st in summary["arms"].items():
        print(f"ARM {nm:8s}: fitted={st['n_fitted']}/{st['n_total']} aut={st['n_automata']} med={ {k: round(v,3) if v is not None else None for k,v in st['median'].items()} }")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "run":
        run(sys.argv[2] if len(sys.argv) > 2 else None)
    else:
        {"predict": predict, "analyse": analyse}[cmd]()
