"""Master Principle Transformer Resolution & Powered Causal Inertia (`gemini/master-principle-tf-causal`):

Arm 1 (`16` automata x `5` archs = `80` runs, `T_train = 16`, `burn = 4`, `steps = 1200`):
  - Resolves `HTF.2` (`CausalTF` Linear vs 3-layer tanh MLP head; probing both Layer-1 and Layer-2 residuals).
  - Tests `MasterPrincipleWindow.lean` via OOD length extrapolation (`T_test in {16, 32, 64}`) across:
      * `tf_rope_mlp`: 2L Pre-LN Causal Transformer with RoPE + 3L tanh MLP head.
      * `tf_sw4_mlp`: 2L Pre-LN RoPE Sliding-Window Causal Transformer (`W_1=2`, `W_2=3` => exact `RF=4`).
      * `gru_mlp`: 1L GRU + 3L tanh MLP head (recurrent OOD control).

Arm 2 (`12` monoids x `5` interventions = `60` runs, `T = 16`, `burn = 4`, `steps = 2500`):
  - Powered settlement of `HMM.3` (`LeakyRNN` `alpha in {1.0, 0.50, 0.25}`) and `HMM.4`
    (warmup-annealed normalized Dirichlet step-velocity penalty `0 -> 0.05` after 40% warmup)
    plus `weight_decay = 3e-2` control across the 12 `master-principle-mech` monoids.
"""

from __future__ import annotations

import json
import math
import pathlib
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
from scipy.linalg import expm

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments import spike58 as S58
from experiments import spike77 as S77
from experiments import spike81 as S81

RESULTS = ROOT / "experiments" / "results"
RAW = RESULTS / "master_principle_tf_causal_raw"
OUT = RESULTS / "master_principle_tf_causal.json"
PRED = RESULTS / "master_principle_tf_causal_predictions.json"

GAMMA_C = 0.6
GAMMA_O = 0.7
T_TRAIN = 16
BURN = 4
T_OP = 16
BATCH = 64
LAM0 = float(S77.LAMBDA / S77.ALPHA)

# Exact panel definitions (diagnostic follow-ups preserving prior disjointness metadata)
TF_FREE_IDS = [11, 35, 68, 140, 146, 317, 380, 599]
TF_GROUP_NAMES = ["Z11_s1_04a", "Z12_s1_015", "Z7_s2_016", "Z8_s3_023"]
MECH_MONOIDS_SPEC = [467, 583, 110, 358, 308, 532, 350, 535, 578, 352, 449, 52]

ARM1_ARCHS = ("tf_lin", "tf_mlp", "tf_rope_mlp", "tf_sw4_mlp", "gru_mlp")
ARM2_ARMS = ("leaky_a100", "leaky_a050", "leaky_a025", "vel_warmup", "wd_3e2")


def cos_mat(A: np.ndarray, B: np.ndarray) -> float:
    na = float(np.linalg.norm(A))
    nb = float(np.linalg.norm(B))
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return float(np.sum(A * B) / (na * nb))


def sym_perp(M: np.ndarray, Pperp: np.ndarray) -> np.ndarray:
    S = 0.5 * (M + M.T)
    return 0.5 * ((Pperp @ S @ Pperp) + (Pperp @ S @ Pperp).T)


def psd_powers(A: np.ndarray, rel_tol: float = 1e-4):
    vals, vecs = np.linalg.eigh(0.5 * (A + A.T))
    top = float(max(vals.max(), 1e-12))
    thr = rel_tol * top
    sqrt_v = np.sqrt(np.maximum(vals, 0.0))
    inv_sqrt_v = np.where(vals > thr, 1.0 / np.sqrt(np.maximum(vals, 1e-15)), 0.0)
    return 0.5 * ((vecs * sqrt_v) @ vecs.T + ((vecs * sqrt_v) @ vecs.T).T), (
        0.5 * ((vecs * inv_sqrt_v) @ vecs.T + ((vecs * inv_sqrt_v) @ vecs.T).T)
    )


def exact_k_definite(Dl: np.ndarray, max_k: int = 12) -> int | None:
    L, m = Dl.shape
    frontier = {tuple(range(m))}
    if len(next(iter(frontier))) == 1:
        return 0
    for k in range(1, max_k + 1):
        nxt = set()
        for S in frontier:
            for a in range(L):
                nxt.add(tuple(sorted({int(Dl[a, q]) for q in S})))
        if all(len(S) == 1 for S in nxt):
            return k
        frontier = nxt
    return None


def base_operators(Dl: np.ndarray, O: np.ndarray, pi: np.ndarray) -> dict:
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
    Lkin = 0.5 / L * sym_perp(Lkin, Pperp)

    mu_o = (pi[:, None] * O).sum(0, keepdims=True)
    Oc = O - mu_o
    sd = np.sqrt((pi[:, None] * (Oc ** 2)).sum(0, keepdims=True))
    Os = Oc / np.maximum(sd, 1e-12)
    F = W[:, None] * Os
    At = F @ F.T
    o_gram = sym_perp(At, Pperp)

    Wo = np.zeros((m, m))
    g = 1.0
    for _ in range(T_OP):
        Wo += g * At
        At_next = np.zeros((m, m))
        for Ta in Ts:
            At_next += Ta @ At @ Ta.T
        At = At_next / L
        g *= GAMMA_O
    Wo = sym_perp(Wo, Pperp)

    Bt = np.outer(one, one)
    Wc = np.zeros((m, m))
    g = GAMMA_C
    for _ in range(1, T_OP):
        Bt_next = np.zeros((m, m))
        for Ta in Ts:
            Bt_next += Ta.T @ Bt @ Ta
        Bt = Bt_next / L
        Wc += g * (Pperp @ Bt @ Pperp)
        g *= GAMMA_C
    Wc = sym_perp(Wc, Pperp)
    W_sum = sym_perp(Wc + Wo, Pperp)

    wc_h, wc_ih = psd_powers(Wc, rel_tol=1e-4)
    inner_gm = 0.5 * (wc_ih @ Wo @ wc_ih + (wc_ih @ Wo @ wc_ih).T)
    inner_gm_h, _ = psd_powers(inner_gm, rel_tol=1e-6)
    W_gm = sym_perp(wc_h @ inner_gm_h @ wc_h, Pperp)

    return {
        "Pperp": Pperp,
        "Lkin": Lkin,
        "Wc": Wc,
        "Wo": Wo,
        "W_sum": W_sum,
        "W_gm": W_gm,
        "G_lam0": sym_perp(expm(-0.5 * LAM0 * Lkin) @ W_sum @ expm(-0.5 * LAM0 * Lkin), Pperp),
        "o": o_gram,
    }


def norm_dirichlet_theoretical(Lkin: np.ndarray, Wsrc: np.ndarray, lam: float) -> float:
    E = expm(-lam * Lkin)
    M = E @ Wsrc
    den = float(np.trace(M))
    if den <= 1e-15:
        return 0.0
    return float(np.trace(Lkin @ M) / den)


def invert_lambda_from_kin(
    Lkin: np.ndarray, Wsrc: np.ndarray, kin_obs: float, lo: float = -4.0, hi: float = 12.0
) -> float:
    if float(np.linalg.norm(Wsrc)) < 1e-12:
        return 0.0
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


def eval_G_at(Lkin: np.ndarray, Wsrc: np.ndarray, Pperp: np.ndarray, lam: float) -> np.ndarray:
    H = expm(-0.5 * lam * Lkin)
    return sym_perp(H @ Wsrc @ H, Pperp)


def _pack_row(name: str, family: str, Dl: np.ndarray, O: np.ndarray, s0: int, extra: dict | None = None) -> dict:
    L, m = Dl.shape
    pi = S81.visit_dist(Dl, s0, np.ones(L) / L, T=T_TRAIN, burn=BURN)
    assert (pi > 1e-4).all(), f"{name} has dead state min_pi={pi.min()}"
    ops = base_operators(Dl, O, pi)
    row = {
        "name": name,
        "family": family,
        "Dl": Dl.tolist(),
        "out": O.tolist(),
        "s0": int(s0),
        "m": int(m),
        "L": int(L),
        "pi": pi.tolist(),
        "Pperp": ops["Pperp"].tolist(),
        "Lkin": ops["Lkin"].tolist(),
        "Wc": ops["Wc"].tolist(),
        "Wo": ops["Wo"].tolist(),
        "W_sum": ops["W_sum"].tolist(),
        "W_gm": ops["W_gm"].tolist(),
        "G_lam0": ops["G_lam0"].tolist(),
        "o": ops["o"].tolist(),
    }
    if extra:
        row.update(extra)
    return row


def make_arm1_model(arch: str, L: int, k_out: int):
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    def mlp_head():
        return nn.Sequential(nn.Linear(64, 64), nn.Tanh(), nn.Linear(64, 64), nn.Tanh(), nn.Linear(64, k_out))

    def apply_rope(q: torch.Tensor, k: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        # q, k: (B, nh, T, hd)
        T = q.shape[2]
        hd = q.shape[3]
        half = hd // 2
        pos = torch.arange(T, device=q.device, dtype=q.dtype)
        freqs = 1.0 / (10000.0 ** (torch.arange(0, half, device=q.device, dtype=q.dtype) / half))
        ang = pos[:, None] * freqs[None, :]
        c = torch.cos(ang)[None, None, :, :]
        s = torch.sin(ang)[None, None, :, :]

        def rot(x: torch.Tensor) -> torch.Tensor:
            x1, x2 = x[..., :half], x[..., half:]
            return torch.cat([x1 * c - x2 * s, x1 * s + x2 * c], dim=-1)

        return rot(q), rot(k)

    class CausalBlock(nn.Module):
        def __init__(self, use_rope: bool, window: int | None):
            super().__init__()
            self.use_rope = use_rope
            self.window = window
            self.nh = 4
            self.hd = 16
            self.ln1 = nn.LayerNorm(64)
            self.qkv = nn.Linear(64, 192)
            self.proj = nn.Linear(64, 64)
            self.ln2 = nn.LayerNorm(64)
            self.ffn = nn.Sequential(nn.Linear(64, 128), nn.GELU(), nn.Linear(128, 64))

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            B, T, D = x.shape
            h = self.ln1(x)
            qkv = self.qkv(h).view(B, T, 3, self.nh, self.hd)
            q = qkv[:, :, 0].transpose(1, 2)
            k = qkv[:, :, 1].transpose(1, 2)
            v = qkv[:, :, 2].transpose(1, 2)
            if self.use_rope:
                q, k = apply_rope(q, k)
            att = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.hd)
            idx = torch.arange(T, device=x.device)
            diff = idx[:, None] - idx[None, :]
            allowed = diff >= 0
            if self.window is not None:
                allowed = allowed & (diff < self.window)
            att = att.masked_fill(~allowed[None, None, :, :], float("-inf"))
            w = F.softmax(att, dim=-1)
            y = torch.matmul(w, v).transpose(1, 2).contiguous().view(B, T, D)
            x = x + self.proj(y)
            x = x + self.ffn(self.ln2(x))
            return x

    if arch in ("tf_lin", "tf_mlp", "tf_rope_mlp", "tf_sw4_mlp"):
        use_rope = arch in ("tf_rope_mlp", "tf_sw4_mlp")
        w1, w2 = (2, 3) if arch == "tf_sw4_mlp" else (None, None)

        class CustomTF(nn.Module):
            def __init__(self):
                super().__init__()
                self.use_rope = use_rope
                self.tok = nn.Embedding(L, 64)
                self.pos = None if use_rope else nn.Embedding(T_TRAIN, 64)
                self.b1 = CausalBlock(use_rope=use_rope, window=w1)
                self.b2 = CausalBlock(use_rope=use_rope, window=w2)
                self.head = nn.Linear(64, k_out) if arch == "tf_lin" else mlp_head()

            def hidden_layers(self, X: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
                x = self.tok(X)
                if self.pos is not None:
                    pos = torch.arange(X.shape[1], device=X.device)[None, :]
                    x = x + self.pos(pos)
                h1 = self.b1(x)
                h2 = self.b2(h1)
                return h1, h2

            def hidden(self, X: torch.Tensor) -> torch.Tensor:
                return self.hidden_layers(X)[1]

            def forward(self, X: torch.Tensor) -> torch.Tensor:
                return self.head(self.hidden(X))

        return CustomTF()

    if arch == "gru_mlp":
        class GRUModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.emb = nn.Embedding(L, 16)
                self.rnn = nn.GRU(16, 64, batch_first=True)
                self.head = mlp_head()

            def hidden_layers(self, X: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
                h = self.rnn(self.emb(X))[0]
                return h, h

            def hidden(self, X: torch.Tensor) -> torch.Tensor:
                return self.hidden_layers(X)[1]

            def forward(self, X: torch.Tensor) -> torch.Tensor:
                return self.head(self.hidden(X))

        return GRUModel()

    raise ValueError(f"Unknown arm1 arch {arch}")


def assert_strict_rf4():
    """Verify mathematically & programmatically that tf_sw4_mlp (W1=2, W2=3) has exact RF=4."""
    import torch
    torch.manual_seed(0)
    mdl = make_arm1_model("tf_sw4_mlp", L=4, k_out=2)
    mdl.eval()
    X = torch.tensor([[0, 1, 2, 3, 1, 2, 0, 3, 1, 0, 2, 3, 1, 2, 0, 3]], dtype=torch.long)
    with torch.no_grad():
        base_out = mdl(X)[0, 15].clone()
        for pos in range(12):  # strictly <= t - 4 = 11
            Xm = X.clone()
            Xm[0, pos] = (Xm[0, pos] + 1) % 4
            diff = float(torch.max(torch.abs(mdl(Xm)[0, 15] - base_out)))
            assert diff == 0.0, f"Sliding window leakage at pos={pos} (t=15): diff={diff}"
        # Confirm pos = 12 (t - 3) is inside RF=4
        Xm = X.clone()
        Xm[0, 12] = (Xm[0, 12] + 1) % 4
        diff_in = float(torch.max(torch.abs(mdl(Xm)[0, 15] - base_out)))
        assert diff_in > 1e-6, f"Expected sensitivity at pos=12 (t-3), got {diff_in}"


def predict():
    assert_strict_rf4()
    pool = S81.build_pool()

    # Arm 1 panel (exact 16 automata matching master-principle-transformer)
    arm1_items: list[dict] = []
    for mid in TF_FREE_IDS:
        A = pool[mid]
        assert A["kind"] == "free"
        Dl = np.vstack([np.array(A["D"]), np.arange(len(A["D"][0]))[None]])
        O = np.array(A["O"], float)
        arm1_items.append(_pack_row(f"M_{mid}", "free", Dl, O, A["s0"], {"id": int(mid)}))

    def_specs = [
        ("def_k2_m6", 2, np.array([[0, 0, 0, 0, 1, 1], [2, 2, 2, 2, 3, 3], [4, 4, 4, 4, 5, 5]], dtype=int),
         np.array([0, 1, 1, 0, 0, 1], float), 0),
        ("def_k3_m8_par", 3, np.array([[((q << 1) | a) & 7 for q in range(8)] for a in range(2)], dtype=int),
         np.array([q.bit_count() % 2 for q in range(8)], float), 0),
        ("def_k3_m8_rst", 3, np.array([[((q & 3) << 1) for q in range(8)], [((q & 3) << 1) | 1 for q in range(8)], [0] * 8], dtype=int),
         np.array([1 if q in {1, 4, 6, 7} else 0 for q in range(8)], float), 0),
        ("def_k4_m8", 4, np.array([[0, 0, 1, 2, 2, 3, 3, 4], [5, 5, 6, 7, 7, 7, 7, 7]], dtype=int),
         np.array([1, 0, 1, 0, 1, 0, 1, 0], float), 0),
    ]
    for nm, exp_k, Dl, O, s0 in def_specs:
        k_got = exact_k_definite(Dl)
        assert k_got == exp_k, f"{nm}: expected {exp_k}, got {k_got}"
        arm1_items.append(_pack_row(nm, "k_definite", Dl, O, s0, {"k_definite": int(k_got)}))

    for gname in TF_GROUP_NAMES:
        grp, L_let, out_fn = S77.spec(gname)
        idx = {g: i for i, g in enumerate(grp)}
        Dl = np.array([[idx[S58.comp(g, a)] for g in grp] for a in L_let], dtype=int)
        assert exact_k_definite(Dl, max_k=6) is None
        O = np.array([out_fn(g) for g in grp], float)
        s0 = int(idx[tuple(range(len(grp[0])))])
        arm1_items.append(_pack_row(gname, "group", Dl, O, s0))

    # Arm 2 panel (exact 12 monoids from master-principle-mech)
    arm2_items: list[dict] = []
    for mid in MECH_MONOIDS_SPEC:
        A = pool[mid]
        Dl = np.vstack([np.array(A["D"]), np.arange(len(A["D"][0]))[None]])
        O = np.array(A["O"], float)
        arm2_items.append(_pack_row(f"MM_{mid}", A["kind"], Dl, O, A["s0"], {"id": int(mid)}))

    out = {
        "constants": {"gamma_c": GAMMA_C, "gamma_o": GAMMA_O, "T_train": T_TRAIN, "burn": BURN, "T_op": T_OP, "lam0": LAM0},
        "arm1_automata": arm1_items,
        "arm2_monoids": arm2_items,
    }
    PRED.parent.mkdir(parents=True, exist_ok=True)
    PRED.write_text(json.dumps(out))
    print(f"Verified RF=4 strict mask; Arm1={len(arm1_items)} automata; Arm2={len(arm2_items)} monoids")


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


def extract_and_score(H_np: np.ndarray, ST: np.ndarray, pi: np.ndarray, m: int, A: dict) -> dict | None:
    flat_h = H_np[:, BURN:].reshape(-1, 64)
    flat_q = ST[:, BURN:].ravel()
    Ce = np.stack([
        flat_h[flat_q == q].mean(0) if (flat_q == q).any() else np.full(64, np.nan)
        for q in range(m)
    ])
    if np.isnan(Ce).any():
        return None
    Lkin = np.array(A["Lkin"], dtype=float)
    Pperp = np.array(A["Pperp"], dtype=float)
    W_sum = np.array(A["W_sum"], dtype=float)
    W_gm = np.array(A["W_gm"], dtype=float)
    G_lam0 = np.array(A["G_lam0"], dtype=float)
    Wc = np.array(A["Wc"], dtype=float)
    Wo = np.array(A["Wo"], dtype=float)
    o_gram = np.array(A["o"], dtype=float)

    W = np.sqrt(pi)[:, None]
    mu = (pi[:, None] * Ce).sum(0, keepdims=True)
    G_net = sym_perp((W * (Ce - mu)) @ (W * (Ce - mu)).T, Pperp)
    kin = float(np.trace(G_net @ Lkin) / max(float(np.trace(G_net)), 1e-12))

    lam_sum = invert_lambda_from_kin(Lkin, W_sum, kin)
    lam_gm = invert_lambda_from_kin(Lkin, W_gm, kin)
    G_sum_kin = eval_G_at(Lkin, W_sum, Pperp, lam_sum)
    G_gm_kin = eval_G_at(Lkin, W_gm, Pperp, lam_gm)
    G_sum_0 = eval_G_at(Lkin, W_sum, Pperp, 0.0)
    return {
        "kin_norm": kin,
        "lam_sum": float(lam_sum),
        "lam_gm": float(lam_gm),
        "cos_Gsum_kin": cos_mat(G_net, G_sum_kin),
        "cos_Wgm_kin": cos_mat(G_net, G_gm_kin),
        "cos_Gsum_0": cos_mat(G_net, G_sum_0),
        "cos_G_lam0": cos_mat(G_net, G_lam0),
        "cos_Wo": cos_mat(G_net, Wo),
        "cos_Wc": cos_mat(G_net, Wc),
        "cos_o": cos_mat(G_net, o_gram),
        "cos_Gsum_vs_o": cos_mat(G_sum_kin, o_gram),
    }


def train_arm1_task(job: tuple[dict, str]) -> dict:
    import torch
    import torch.nn as nn
    torch.set_num_threads(1)

    A, arch = job
    name = A["name"]
    Dl = np.array(A["Dl"], dtype=np.int64)
    O = np.array(A["out"], dtype=np.float32)
    pi = np.array(A["pi"], dtype=float)
    L, m = Dl.shape
    k_out = 1 if O.ndim == 1 else O.shape[1]

    seed = 20261124 + (sum(ord(c) for c in f"a1:{name}:{arch}") * 131 + hash((name, arch)) % 100000) % 1000000
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)

    mdl = make_arm1_model(arch, L, k_out)
    opt = torch.optim.AdamW(mdl.parameters(), lr=3e-3, weight_decay=0.0)
    steps = 1200
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps, eta_min=3e-4)

    t0 = time.time()
    for _ in range(steps):
        X, Y, _ = fast_sample(Dl, O, A["s0"], BATCH, T_TRAIN, rng)
        loss = nn.functional.binary_cross_entropy_with_logits(mdl(X)[:, BURN:], Y[:, BURN:])
        opt.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(mdl.parameters(), 1.0)
        opt.step()
        sch.step()

    mdl.eval()
    eval_lengths = (16,) if arch in ("tf_lin", "tf_mlp") else (16, 32, 64)
    fits = {}
    h1_scores = None
    h2_scores = None
    with torch.no_grad():
        for T_ev in eval_lengths:
            Xv, Yv, STv = fast_sample(Dl, O, A["s0"], 300, T_ev, np.random.default_rng(seed + 100_000 + T_ev))
            logits = mdl(Xv)[:, BURN:]
            fits[f"T{T_ev}"] = float(((logits > 0).float() == Yv[:, BURN:]).float().mean())
            if T_ev == 16:
                H1, H2 = mdl.hidden_layers(Xv)
                h1_scores = extract_and_score(H1.numpy(), STv, pi, m, A)
                h2_scores = extract_and_score(H2.numpy(), STv, pi, m, A)

    res = {
        "arm": "arm1",
        "name": name,
        "family": A["family"],
        "arch": arch,
        "fit": fits["T16"],
        "fits": fits,
        "l1": h1_scores,
        "l2": h2_scores,
        "elapsed_s": float(time.time() - t0),
    }
    p = RAW / f"arm1_{name}_{arch}.json"
    p.write_text(json.dumps(res))
    return res


def make_leaky_rnn(L: int, k_out: int, alpha: float):
    import torch
    import torch.nn as nn

    class LeakyRNN(nn.Module):
        def __init__(self):
            super().__init__()
            self.alpha = float(alpha)
            self.e = nn.Embedding(L, 16)
            self.cell = nn.RNNCell(16, 64, nonlinearity="tanh")
            nn.init.orthogonal_(self.cell.weight_hh)
            self.head = nn.Sequential(
                nn.Linear(64, 64), nn.Tanh(), nn.Linear(64, 64), nn.Tanh(), nn.Linear(64, k_out)
            )

        def hidden(self, X: torch.Tensor) -> torch.Tensor:
            emb = self.e(X)
            h = torch.zeros(X.shape[0], 64, dtype=emb.dtype, device=emb.device)
            outs = []
            a = self.alpha
            for t in range(X.shape[1]):
                h_cand = self.cell(emb[:, t], h)
                h = (1.0 - a) * h + a * h_cand if a < 1.0 else h_cand
                outs.append(h)
            return torch.stack(outs, dim=1)

        def forward(self, X: torch.Tensor) -> torch.Tensor:
            return self.head(self.hidden(X))

    return LeakyRNN()


def train_arm2_task(job: tuple[dict, str]) -> dict:
    import torch
    import torch.nn as nn
    torch.set_num_threads(1)

    A, arm_tag = job
    name = A["name"]
    Dl = np.array(A["Dl"], dtype=np.int64)
    O = np.array(A["out"], dtype=np.float32)
    pi = np.array(A["pi"], dtype=float)
    Lkin = np.array(A["Lkin"], dtype=float)
    Pperp = np.array(A["Pperp"], dtype=float)
    W_sum = np.array(A["W_sum"], dtype=float)
    L, m = Dl.shape
    k_out = 1 if O.ndim == 1 else O.shape[1]

    alpha = {"leaky_a100": 1.0, "leaky_a050": 0.50, "leaky_a025": 0.25}.get(arm_tag, 1.0)
    wd = 3e-2 if arm_tag == "wd_3e2" else 0.0
    use_vel = (arm_tag == "vel_warmup")

    seed = 20261125 + (sum(ord(c) for c in f"a2:{name}") * 137 + A["id"] * 17) % 1000000
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)

    mdl = make_leaky_rnn(L, k_out, alpha=alpha)
    opt = torch.optim.AdamW(mdl.parameters(), lr=3e-3, weight_decay=wd)
    steps = 2500
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps, eta_min=3e-4)

    t0 = time.time()
    for step in range(steps):
        X, Y, _ = fast_sample(Dl, O, A["s0"], BATCH, T_TRAIN, rng)
        H = mdl.hidden(X)
        logits = mdl.head(H)
        loss = nn.functional.binary_cross_entropy_with_logits(logits[:, BURN:], Y[:, BURN:])
        if use_vel and step >= 1000:
            mu = 0.05 if step >= 1500 else 0.05 * ((step - 1000) / 500.0)
            H_st = H[:, BURN:]
            dh = (H_st[:, 1:] - H_st[:, :-1]).pow(2).mean()
            var_h = (H_st - H_st.mean(dim=(0, 1), keepdim=True)).pow(2).mean().clamp_min(1e-4)
            loss = loss + mu * (dh / var_h)
        opt.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(mdl.parameters(), 1.0)
        opt.step()
        sch.step()

    mdl.eval()
    with torch.no_grad():
        Xv, Yv, STv = fast_sample(Dl, O, A["s0"], 400, T_TRAIN, np.random.default_rng(seed + 100_000))
        fit = float(((mdl(Xv)[:, BURN:] > 0).float() == Yv[:, BURN:]).float().mean())
        H_np = mdl.hidden(Xv).numpy()

    flat_h = H_np[:, BURN:].reshape(-1, 64)
    flat_q = STv[:, BURN:].ravel()
    Ce = np.stack([
        flat_h[flat_q == q].mean(0) if (flat_q == q).any() else np.full(64, np.nan)
        for q in range(m)
    ])
    scores = extract_and_score(H_np, STv, pi, m, A)
    W = np.sqrt(pi)[:, None]
    mu_c = (pi[:, None] * Ce).sum(0, keepdims=True)
    G_net = sym_perp((W * (Ce - mu_c)) @ (W * (Ce - mu_c)).T, Pperp) if not np.isnan(Ce).any() else None

    res = {
        "arm": "arm2",
        "name": name,
        "id": int(A["id"]),
        "kind": A["family"],
        "arm_tag": arm_tag,
        "alpha": alpha,
        "wd": wd,
        "fit": fit,
        "kin_norm": scores["kin_norm"] if scores else None,
        "lam_emp": scores["lam_sum"] if scores else None,
        "cos_Gsum_kin": scores["cos_Gsum_kin"] if scores else None,
        "G_net": G_net.tolist() if G_net is not None else None,
        "elapsed_s": float(time.time() - t0),
    }
    p = RAW / f"arm2_{name}_{arm_tag}.json"
    p.write_text(json.dumps(res))
    return res


def _run_job(kind_job):
    kind, job = kind_job
    if kind == "arm1":
        return train_arm1_task(job)
    return train_arm2_task(job)


def run():
    assert_strict_rf4()
    RAW.mkdir(parents=True, exist_ok=True)
    P = json.loads(PRED.read_text())
    jobs = []
    for A in P["arm1_automata"]:
        for arch in ARM1_ARCHS:
            if not (RAW / f"arm1_{A['name']}_{arch}.json").exists():
                jobs.append(("arm1", (A, arch)))
    for A in P["arm2_monoids"]:
        for arm_tag in ARM2_ARMS:
            if not (RAW / f"arm2_{A['name']}_{arm_tag}.json").exists():
                jobs.append(("arm2", (A, arm_tag)))

    print(f"Pending jobs: {len(jobs)} (2 workers, threads=1)")
    t0 = time.time()
    if jobs:
        with ProcessPoolExecutor(max_workers=2) as ex:
            futs = [ex.submit(_run_job, j) for j in jobs]
            done = 0
            for fut in as_completed(futs):
                r = fut.result()
                done += 1
                if r["arm"] == "arm1":
                    c_sum = round(r["l2"]["cos_Gsum_kin"], 3) if r["l2"] else None
                    c_o = round(r["l2"]["cos_o"], 3) if r["l2"] else None
                    print(f"[{done}/{len(jobs)}] arm1 {r['name']} {r['arch']} fit16={r['fit']:.3f} fits={ {k:round(v,3) for k,v in r['fits'].items()} } L2(G={c_sum}, o={c_o})", flush=True)
                else:
                    print(f"[{done}/{len(jobs)}] arm2 {r['name']} {r['arm_tag']} fit={r['fit']:.3f} kin={round(r['kin_norm'],3) if r['kin_norm'] is not None else None} lam={round(r['lam_emp'],3) if r['lam_emp'] is not None else None}", flush=True)
    print(f"All runs finished in {time.time() - t0:.1f}s")


def analyse():
    P = json.loads(PRED.read_text())
    arm1_by_meta = {a["name"]: a for a in P["arm1_automata"]}
    arm2_by_meta = {a["name"]: a for a in P["arm2_monoids"]}

    a1_runs = [json.loads(p.read_text()) for p in sorted(RAW.glob("arm1_*.json"))]
    a2_runs = [json.loads(p.read_text()) for p in sorted(RAW.glob("arm2_*.json"))]
    assert len(a1_runs) == 80, f"Expected 80 arm1 runs, got {len(a1_runs)}"
    assert len(a2_runs) == 60, f"Expected 60 arm2 runs, got {len(a2_runs)}"

    # --- Summary tables for Arm 1 ---
    a1_summary = {}
    for arch in ARM1_ARCHS:
        a1_summary[arch] = {}
        for fam in ("free", "k_definite", "group"):
            rs = [r for r in a1_runs if r["arch"] == arch and r["family"] == fam]
            conv = [r for r in rs if r["fit"] >= 0.90]
            row = {"n": len(rs), "n_conv": len(conv), "mean_fit_T16": float(np.mean([r["fit"] for r in rs]))}
            if "T32" in rs[0]["fits"]:
                row["mean_fit_T32"] = float(np.mean([r["fits"]["T32"] for r in rs]))
                row["mean_fit_T64"] = float(np.mean([r["fits"]["T64"] for r in rs]))
            for lyr in ("l1", "l2"):
                vals = [r[lyr] for r in conv if r[lyr] is not None]
                if vals:
                    row[lyr] = {
                        k: float(np.mean([v[k] for v in vals]))
                        for k in ("kin_norm", "lam_sum", "cos_Gsum_kin", "cos_Wgm_kin", "cos_Gsum_0", "cos_G_lam0", "cos_Wo", "cos_Wc", "cos_o")
                    }
            a1_summary[arch][fam] = row

    # HTC.1: Head Confound vs Attention Law (tf_mlp vs tf_lin on converged non-group)
    tf_mlp_ng = [r for r in a1_runs if r["arch"] == "tf_mlp" and r["family"] != "group" and r["fit"] >= 0.90 and r["l2"] is not None]
    tf_lin_ng = [r for r in a1_runs if r["arch"] == "tf_lin" and r["family"] != "group" and r["fit"] >= 0.90 and r["l2"] is not None]
    mlp_l2_beat_o = sum(1 for r in tf_mlp_ng if r["l2"]["cos_Gsum_kin"] > r["l2"]["cos_o"])
    mlp_l1_beat_o = sum(1 for r in tf_mlp_ng if r["l1"]["cos_Gsum_kin"] > r["l1"]["cos_o"])
    lin_l2_beat_o = sum(1 for r in tf_lin_ng if r["l2"]["cos_Gsum_kin"] > r["l2"]["cos_o"])
    lin_l1_beat_o = sum(1 for r in tf_lin_ng if r["l1"]["cos_Gsum_kin"] > r["l1"]["cos_o"])
    if len(tf_mlp_ng) < 8:
        htc1 = "NO VERDICT"
    elif mlp_l2_beat_o >= 9:
        htc1 = "HEAD_CONFOUND"
    elif mlp_l2_beat_o <= 4:
        htc1 = "ATTENTION_LAW"
    else:
        htc1 = "NEITHER"

    # HTC.2: Strict finite window RF=4 dichotomy
    sw_def = [r for r in a1_runs if r["arch"] == "tf_sw4_mlp" and r["family"] == "k_definite"]
    sw_grp = [r for r in a1_runs if r["arch"] == "tf_sw4_mlp" and r["family"] == "group"]
    def_all_95 = all(all(v >= 0.95 for v in r["fits"].values()) for r in sw_def)
    grp_all_le50 = all(all(v <= 0.50 for v in r["fits"].values()) for r in sw_grp)
    if def_all_95 and grp_all_le50:
        htc2 = "HELD"
    elif all(r["fits"]["T64"] >= 0.90 for r in sw_def) and max(r["fits"]["T64"] for r in sw_grp) > 0.70:
        htc2 = "BROKEN"
    else:
        htc2 = "NEITHER"

    # HTC.3: OOD length extrapolation T=16 -> T=64 (GRU vs RoPE)
    gru_grp = [r for r in a1_runs if r["arch"] == "gru_mlp" and r["family"] == "group"]
    rope_grp = [r for r in a1_runs if r["arch"] == "tf_rope_mlp" and r["family"] == "group"]
    rope_def = [r for r in a1_runs if r["arch"] == "tf_rope_mlp" and r["family"] == "k_definite"]
    gru_grp_90 = sum(1 for r in gru_grp if r["fits"]["T64"] >= 0.90)
    rope_grp_lt70 = sum(1 for r in rope_grp if r["fits"]["T64"] < 0.70)
    rope_def_90 = sum(1 for r in rope_def if r["fits"]["T64"] >= 0.90)
    if gru_grp_90 == 4 and rope_grp_lt70 >= 3 and rope_def_90 >= 3:
        htc3 = "HELD"
    elif rope_grp_lt70 == 0:
        htc3 = "BROKEN"
    else:
        htc3 = "NEITHER"

    # --- Arm 2: Powered HMM.3 & HMM.4 ---
    a2_by_key = {(r["name"], r["arm_tag"]): r for r in a2_runs}
    arm2_summary = {}
    for tag in ARM2_ARMS:
        rs = [r for r in a2_runs if r["arm_tag"] == tag]
        conv = [r for r in rs if r["fit"] >= 0.90]
        arm2_summary[tag] = {
            "n_conv_12": len(conv),
            "mean_fit": float(np.mean([r["fit"] for r in rs])),
            "mean_kin_conv": float(np.mean([r["kin_norm"] for r in conv])) if conv else None,
            "mean_lam_conv": float(np.mean([r["lam_emp"] for r in conv])) if conv else None,
            "mean_cos_conv": float(np.mean([r["cos_Gsum_kin"] for r in conv])) if conv else None,
        }

    # HTC.4: Powered HMM.3 (requires >= 8/12 converged triplets across 1.0, 0.50, 0.25)
    hmm3_triplets = []
    for nm in sorted(arm2_by_meta):
        r1 = a2_by_key[(nm, "leaky_a100")]
        r5 = a2_by_key[(nm, "leaky_a050")]
        r2 = a2_by_key[(nm, "leaky_a025")]
        if r1["fit"] >= 0.90 and r5["fit"] >= 0.90 and r2["fit"] >= 0.90:
            meta = arm2_by_meta[nm]
            Lkin = np.array(meta["Lkin"], float)
            W_sum = np.array(meta["W_sum"], float)
            Pperp = np.array(meta["Pperp"], float)
            G2 = np.array(r2["G_net"], float)
            c_own = cos_mat(G2, eval_G_at(Lkin, W_sum, Pperp, r2["lam_emp"]))
            c_base = cos_mat(G2, eval_G_at(Lkin, W_sum, Pperp, r1["lam_emp"]))
            hmm3_triplets.append({
                "name": nm,
                "kin_mono": bool(r1["kin_norm"] > r5["kin_norm"] > r2["kin_norm"]),
                "lam_mono": bool(r1["lam_emp"] < r5["lam_emp"] < r2["lam_emp"]),
                "cos_shift_ok": bool(c_own > c_base),
                "kins": [r1["kin_norm"], r5["kin_norm"], r2["kin_norm"]],
                "lams": [r1["lam_emp"], r5["lam_emp"], r2["lam_emp"]],
                "cos_025_at_lam025": c_own,
                "cos_025_at_lam100": c_base,
            })

    if len(hmm3_triplets) < 8:
        htc4 = "NO VERDICT"
    else:
        n3 = len(hmm3_triplets)
        f_mono = sum(1 for t in hmm3_triplets if t["kin_mono"] and t["lam_mono"]) / n3
        f_cos = sum(1 for t in hmm3_triplets if t["cos_shift_ok"]) / n3
        if f_mono >= 0.80 and f_cos >= 0.75:
            htc4 = "HELD"
        elif f_mono < 0.50:
            htc4 = "BROKEN"
        else:
            htc4 = "NEITHER"

    # HTC.5: Powered HMM.4 (vel_warmup vs leaky_a100, requires >= 8/12 converged pairs)
    hmm4_pairs = []
    for nm in sorted(arm2_by_meta):
        rb = a2_by_key[(nm, "leaky_a100")]
        rv = a2_by_key[(nm, "vel_warmup")]
        if rb["fit"] >= 0.90 and rv["fit"] >= 0.90:
            meta = arm2_by_meta[nm]
            Lkin = np.array(meta["Lkin"], float)
            W_sum = np.array(meta["W_sum"], float)
            Pperp = np.array(meta["Pperp"], float)
            Gv = np.array(rv["G_net"], float)
            c_own = cos_mat(Gv, eval_G_at(Lkin, W_sum, Pperp, rv["lam_emp"]))
            c_base = cos_mat(Gv, eval_G_at(Lkin, W_sum, Pperp, rb["lam_emp"]))
            hmm4_pairs.append({
                "name": nm,
                "kin_drop": bool(rv["kin_norm"] < rb["kin_norm"] and rv["lam_emp"] > rb["lam_emp"]),
                "cos_shift_ok": bool(c_own >= c_base),
                "kin_base": rb["kin_norm"], "kin_vel": rv["kin_norm"],
                "lam_base": rb["lam_emp"], "lam_vel": rv["lam_emp"],
                "cos_vel_at_own": c_own, "cos_vel_at_base": c_base,
            })

    if len(hmm4_pairs) < 8:
        htc5 = "NO VERDICT"
    else:
        n4 = len(hmm4_pairs)
        f_drop = sum(1 for p in hmm4_pairs if p["kin_drop"]) / n4
        f_cos4 = sum(1 for p in hmm4_pairs if p["cos_shift_ok"]) / n4
        if f_drop >= 0.75 and f_cos4 >= 0.75:
            htc5 = "HELD"
        elif f_drop < 0.50:
            htc5 = "BROKEN"
        else:
            htc5 = "NEITHER"

    verdicts = {"HTC.1": htc1, "HTC.2": htc2, "HTC.3": htc3, "HTC.4": htc4, "HTC.5": htc5}
    out = {
        "verdicts": verdicts,
        "arm1_summary": a1_summary,
        "htc1_detail": {
            "n_tf_mlp_ng": len(tf_mlp_ng), "n_tf_lin_ng": len(tf_lin_ng),
            "mlp_l2_beat_o": mlp_l2_beat_o, "mlp_l1_beat_o": mlp_l1_beat_o,
            "lin_l2_beat_o": lin_l2_beat_o, "lin_l1_beat_o": lin_l1_beat_o,
        },
        "htc2_detail": {
            "def_all_95": def_all_95, "grp_all_le50": grp_all_le50,
            "sw_def_fits": {r["name"]: r["fits"] for r in sw_def},
            "sw_grp_fits": {r["name"]: r["fits"] for r in sw_grp},
        },
        "htc3_detail": {
            "gru_grp_90": gru_grp_90, "rope_grp_lt70": rope_grp_lt70, "rope_def_90": rope_def_90,
            "gru_grp": {r["name"]: r["fits"] for r in gru_grp},
            "rope_grp": {r["name"]: r["fits"] for r in rope_grp},
            "rope_def": {r["name"]: r["fits"] for r in rope_def},
        },
        "arm2_summary": arm2_summary,
        "htc4_triplets": hmm3_triplets,
        "htc5_pairs": hmm4_pairs,
    }
    OUT.write_text(json.dumps(out, indent=2))
    print("VERDICTS:", json.dumps(verdicts))
    print(json.dumps({k: out[k] for k in ("htc1_detail", "htc2_detail", "htc3_detail", "arm2_summary")}, indent=2))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "predict":
        predict()
    elif cmd == "run":
        run()
    elif cmd == "analyse":
        analyse()
    else:
        raise ValueError(f"Unknown command {cmd}")
