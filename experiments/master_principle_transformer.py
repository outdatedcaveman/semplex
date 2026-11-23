"""Master Principle Transformer Experiment (`gemini/master-principle-transformer`):
Empirical companion to `MasterPrincipleWindow.lean` comparing 2L Pre-LN Causal Transformer
against GRU-MLP, RNN-MLP, and Hankel SPEC at horizon T = 16 (burn = 4) across:
  - 8 fresh `free` monoids (reserved from `master-principle-mech`, disjoint from all spikes)
  - 4 verified `k`-definite reset monoids (`k in {2, 3, 4}`, `m in {6, 8}`)
  - 4 fresh discriminating cyclic groups from S77.POOL
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
RAW = RESULTS / "master_principle_transformer_raw"
OUT = RESULTS / "master_principle_transformer.json"
PRED = RESULTS / "master_principle_transformer_predictions.json"

GAMMA_C = 0.6
GAMMA_O = 0.7
T_SEQ = 16
BURN = 4
T_OP = 16
BATCH = 64
LAM0 = float(S77.LAMBDA / S77.ALPHA)

# Exact reserved & excluded sets (disjoint from all prior spikes, master-principle, & master-principle-mech)
RESERVED_FREE_IDS = [11, 35, 68, 140, 146, 317, 380, 599]
PRIOR_MP_MONOIDS = {65, 70, 76, 103, 127, 193, 281, 368, 409, 512, 515, 584}
PRIOR_MECH_MONOIDS = {467, 583, 110, 358, 308, 532, 350, 535, 578, 352, 449, 52}
PRIOR_MP_GROUPS = {"Z11_s1_048", "Z11_s2_035", "Z12_s1_045", "Z7_s2_013", "Z7_s3_015", "Z8_s3_047"}
PRIOR_MECH_GROUPS = {"Z11_s2_039", "Z12_s1_029", "Z7_s1_025", "Z8_s1_036", "Z7_s3_046", "Z7_s2_056"}


def cos_mat(A: np.ndarray, B: np.ndarray) -> float:
    na = float(np.linalg.norm(A))
    nb = float(np.linalg.norm(B))
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return float(np.sum(A * B) / (na * nb))


def exact_k_definite(Dl: np.ndarray, max_k: int = 12) -> int | None:
    """Return exact minimum synchronizing horizon k if IsDefinite(Dl, k) holds, else None."""
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


def base_operators(Dl: np.ndarray, O: np.ndarray, pi: np.ndarray,
                   gc: float = GAMMA_C, go: float = GAMMA_O, T: int = T_OP) -> dict:
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
    G0 = Pperp @ (0.5 * ((Wc + Wo) + (Wc + Wo).T)) @ Pperp
    H0 = expm(-0.5 * LAM0 * Lkin)
    sym = lambda M: Pperp @ (0.5 * (M + M.T)) @ Pperp
    G_lam0 = sym(H0 @ (Wc + Wo) @ H0)
    Wo_heat = sym(H0 @ Wo @ H0)

    return {
        "Lkin": Lkin,
        "Wo": Wo,
        "Wc": Wc,
        "G0": G0,
        "G_lam0": G_lam0,
        "Wo_heat": Wo_heat,
        "o": o_gram,
        "k1": k1_gram,
        "cos_G0_o": cos_mat(G0, o_gram),
        "cos_Glam0_o": cos_mat(G_lam0, o_gram),
    }


def norm_dirichlet_theoretical(Lkin: np.ndarray, Wsrc: np.ndarray, lam: float) -> float:
    E = expm(-lam * Lkin)
    M = E @ Wsrc
    den = float(np.trace(M))
    if den <= 1e-15:
        return 0.0
    return float(np.trace(Lkin @ M) / den)


def invert_lambda_from_kin(Lkin: np.ndarray, Wsrc: np.ndarray, kin_obs: float,
                           lo: float = -4.0, hi: float = 12.0) -> float:
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


def eval_G_at(Lkin: np.ndarray, Wsrc: np.ndarray, pi: np.ndarray, lam: float) -> np.ndarray:
    W = np.sqrt(pi)
    one = W / np.linalg.norm(W)
    Pperp = np.eye(len(pi)) - np.outer(one, one)
    H = expm(-0.5 * lam * Lkin)
    M = H @ Wsrc @ H
    return Pperp @ (0.5 * (M + M.T)) @ Pperp


def _collect_excluded_monoids() -> set[int]:
    used = set(PRIOR_MP_MONOIDS) | set(PRIOR_MECH_MONOIDS)
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
    for rd in ["spike84_raw", "spike87_raw", "master_principle_raw", "master_principle_mech_raw"]:
        rp = RESULTS / rd
        if rp.exists():
            for f in rp.glob("*.json"):
                d = json.loads(f.read_text())
                if isinstance(d.get("id"), int):
                    used.add(d["id"])
    return used


def _pack_automaton_row(name: str, family: str, Dl: np.ndarray, O: np.ndarray, s0: int,
                        extra: dict | None = None) -> dict:
    L, m = Dl.shape
    pi = S81.visit_dist(Dl, s0, np.ones(L) / L, T=T_SEQ, burn=BURN)
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
        "Lkin": ops["Lkin"].tolist(),
        "Wo": ops["Wo"].tolist(),
        "Wc": ops["Wc"].tolist(),
        "G0": ops["G0"].tolist(),
        "G_lam0": ops["G_lam0"].tolist(),
        "Wo_heat": ops["Wo_heat"].tolist(),
        "o": ops["o"].tolist(),
        "k1": ops["k1"].tolist(),
        "cos_G0_o": ops["cos_G0_o"],
        "cos_Glam0_o": ops["cos_Glam0_o"],
    }
    if extra:
        row.update(extra)
    return row


def predict():
    rng = np.random.default_rng(20261122)
    excluded_m = _collect_excluded_monoids()
    assert set(RESERVED_FREE_IDS).isdisjoint(excluded_m), "Overlap with prior monoid IDs!"
    pool = S81.build_pool()

    items: list[dict] = []

    # 1. Exact 8 reserved fresh free monoids
    for mid in RESERVED_FREE_IDS:
        A = pool[mid]
        assert A["kind"] == "free"
        Dl = np.vstack([np.array(A["D"]), np.arange(len(A["D"][0]))[None]])
        O = np.array(A["O"], float)
        items.append(_pack_automaton_row(f"M_{mid}", "free", Dl, O, A["s0"], {"id": int(mid)}))

    # 2. 4 verified k-definite reset monoids (no stay-identity letter!)
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
        assert k_got == exp_k, f"{nm}: expected k={exp_k}, got {k_got}"
        items.append(_pack_automaton_row(nm, "k_definite", Dl, O, s0, {"k_definite": int(k_got)}))

    # 3. 4 fresh discriminating cyclic groups from S77.POOL
    P77 = json.loads((RESULTS / "spike77_predictions.json").read_text())
    P78 = json.loads((RESULTS / "spike78_predictions.json").read_text())
    used_g = set(S77.USED) | set(P77["automata"]) | set(P78["sample"]) | PRIOR_MP_GROUPS | PRIOR_MECH_GROUPS
    S71.spec = S77.spec
    S71._patch()

    cand_cyc: dict[str, dict] = {}
    for name in sorted(S77.POOL):
        if name in used_g or not name.startswith("Z"):
            continue
        grp, L_let, out_fn = S77.spec(name)
        idx = {g: i for i, g in enumerate(grp)}
        m = len(grp)
        Dl = np.array([[idx[S58.comp(g, a)] for g in grp] for a in L_let], dtype=int)
        assert all(len(set(Dl[a].tolist())) == m for a in range(len(L_let)))
        assert exact_k_definite(Dl, max_k=6) is None
        O = np.array([out_fn(g) for g in grp], float)
        pi = np.ones(m) / m
        ops = base_operators(Dl, O, pi)
        irs = S69.real_irreps(grp)
        labels = [S69.irrep_label(ir, k) for k, ir in enumerate(irs)]
        F = S77.feats(name)
        pg = S77.probs(F, S77.ALPHA, S77.LAMBDA)
        pe = S77.probs(F, P77["energy_alpha"], 0.0)
        ps = S77.probs(F, 0.0, P77["smooth_lambda"])
        mg, me, ms = max(pg, key=pg.get), max(pe, key=pe.get), max(ps, key=ps.get)
        ev, EV = np.linalg.eigh(ops["G_lam0"])
        tol = 1e-6 * max(float(ev.max()), 1e-12)
        top_cols = EV[:, ev >= ev[-1] - tol]
        lead_G = labels[int(np.argmax(S71.shares(top_cols, irs)))]
        if pg[mg] >= 0.6 and (lead_G != me or lead_G != ms):
            cand_cyc[name] = (Dl, O, int(idx[tuple(range(len(grp[0])))]), {"lead_G": lead_G})

    picked_cyc: list[str] = []
    by_pref: dict[str, list[str]] = {}
    for nm in sorted(cand_cyc):
        by_pref.setdefault(nm.split("_")[0], []).append(nm)
    for pref in sorted(by_pref):
        if len(picked_cyc) >= 4:
            break
        opts = by_pref[pref]
        picked_cyc.append(opts[int(rng.integers(len(opts)))])
    if len(picked_cyc) < 4:
        rem = [nm for nm in sorted(cand_cyc) if nm not in picked_cyc]
        picked_cyc += [rem[int(j)] for j in rng.choice(len(rem), size=4 - len(picked_cyc), replace=False)]

    for nm in picked_cyc:
        Dl, O, s0, extra = cand_cyc[nm]
        items.append(_pack_automaton_row(nm, "group", Dl, O, s0, extra))

    out = {
        "constants": {"gamma_c": GAMMA_C, "gamma_o": GAMMA_O, "T_seq": T_SEQ, "burn": BURN, "T_op": T_OP, "lam0": LAM0},
        "reserved_free_ids": RESERVED_FREE_IDS,
        "picked_cyclic_groups": picked_cyc,
        "automata": items,
    }
    PRED.parent.mkdir(parents=True, exist_ok=True)
    PRED.write_text(json.dumps(out))
    print(f"Panel total={len(items)}: free={[r['name'] for r in items if r['family']=='free']}, "
          f"k_def={[r['name'] for r in items if r['family']=='k_definite']}, cyc={picked_cyc}")


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


def make_model(arch: str, L: int, k_out: int):
    import torch
    nn = torch.nn

    if arch == "causal_tf":
        class CausalTF(nn.Module):
            def __init__(self):
                super().__init__()
                self.tok = nn.Embedding(L, 64)
                self.pos = nn.Embedding(T_SEQ, 64)
                layer = nn.TransformerEncoderLayer(
                    d_model=64, nhead=4, dim_feedforward=128, dropout=0.0,
                    activation="gelu", batch_first=True, norm_first=True,
                )
                self.enc = nn.TransformerEncoder(layer, num_layers=2, enable_nested_tensor=False)
                self.head = nn.Linear(64, k_out)
                mask = torch.triu(torch.full((T_SEQ, T_SEQ), float("-inf")), diagonal=1)
                self.register_buffer("cmask", mask)

            def hidden(self, X):
                pos = torch.arange(X.shape[1], device=X.device)[None, :]
                x = self.tok(X) + self.pos(pos)
                return self.enc(x, mask=self.cmask[:X.shape[1], :X.shape[1]])

            def forward(self, X):
                return self.head(self.hidden(X))

        return CausalTF()

    def mlp_head():
        return nn.Sequential(nn.Linear(64, 64), nn.Tanh(), nn.Linear(64, 64), nn.Tanh(), nn.Linear(64, k_out))

    class RecNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.e = nn.Embedding(L, 16)
            if arch == "gru_mlp":
                self.r = nn.GRU(16, 64, batch_first=True)
            elif arch == "rnn_mlp":
                self.r = nn.RNN(16, 64, nonlinearity="tanh", batch_first=True)
                nn.init.orthogonal_(self.r.weight_hh_l0)
            else:
                raise ValueError(arch)
            self.h = mlp_head()

        def hidden(self, X):
            return self.r(self.e(X))[0]

        def forward(self, X):
            return self.h(self.hidden(X))

    return RecNet()


def extract_centroids(mdl, Dl: np.ndarray, O: np.ndarray, s0: int, m: int, seed: int) -> np.ndarray:
    import torch
    mdl.eval()
    with torch.no_grad():
        Xv, _, ST = fast_sample(Dl, O, s0, 500, T_SEQ, np.random.default_rng(seed + 2_000_000))
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
    lam_emp = invert_lambda_from_kin(ops["Lkin"], ops["G0"], kin_obs=kin_norm)
    G_emp = eval_G_at(ops["Lkin"], ops["G0"], pi, lam_emp)
    return {
        "kin_norm": kin_norm,
        "lam_emp": lam_emp,
        "cos_G0": cos_mat(Gl, ops["G0"]),
        "cos_G_lam0": cos_mat(Gl, ops["G_lam0"]),
        "cos_G_emp": cos_mat(Gl, G_emp),
        "cos_Wo_heat": cos_mat(Gl, ops["Wo_heat"]),
        "cos_Wo": cos_mat(Gl, ops["Wo"]),
        "cos_Wc": cos_mat(Gl, ops["Wc"]),
        "cos_o": cos_mat(Gl, ops["o"]),
        "cos_k1": cos_mat(Gl, ops["k1"]),
    }


def train_one(Dl: np.ndarray, O: np.ndarray, s0: int, m: int, arch: str,
              steps: int, lr: float, seed: int, clip_norm: float | None = None):
    import torch
    nn = torch.nn
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    L = Dl.shape[0]
    k_out = 1 if O.ndim == 1 else O.shape[1]
    mdl = make_model(arch, L, k_out)
    opt = torch.optim.AdamW(mdl.parameters(), lr=lr, weight_decay=0.0)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps)
    for _ in range(steps):
        X, Y, _ = fast_sample(Dl, O, s0, BATCH, T_SEQ, rng)
        loss = nn.functional.binary_cross_entropy_with_logits(mdl(X), Y)
        opt.zero_grad()
        loss.backward()
        if clip_norm is not None:
            nn.utils.clip_grad_norm_(mdl.parameters(), clip_norm)
        opt.step()
        sch.step()

    mdl.eval()
    with torch.no_grad():
        Xv, Yv, _ = fast_sample(Dl, O, s0, 500, T_SEQ, np.random.default_rng(seed + 1_000_000))
        preds = (mdl(Xv) > 0).float()
        fit = float((preds[:, BURN:] == Yv[:, BURN:]).float().mean())
        fit_all = float((preds == Yv).float().mean())
    Ce = extract_centroids(mdl, Dl, O, s0, m, seed)
    return fit, fit_all, Ce


def run_spec_one(Dl: np.ndarray, O: np.ndarray, m: int, seed: int = 42) -> np.ndarray:
    rng = np.random.default_rng(seed)
    L = Dl.shape[0]
    O_2d = O[:, None] if O.ndim == 1 else O
    sufs = [rng.integers(0, L, size=rng.integers(0, 9)) for _ in range(400)]
    F = np.zeros((m, len(sufs), O_2d.shape[1]))
    for j, s in enumerate(sufs):
        q = np.arange(m)
        for a in s:
            q = Dl[a, q]
        F[:, j, :] = O_2d[q]
    return F.reshape(m, -1)


def _ops_from_item(row: dict) -> dict:
    return {k: np.array(row[k]) for k in ("Lkin", "Wo", "Wc", "G0", "G_lam0", "Wo_heat", "o", "k1")}


def run(which: str | None = None, part: str = "0/1"):
    import torch
    torch.set_num_threads(1)
    RAW.mkdir(parents=True, exist_ok=True)
    P = json.loads(PRED.read_text())
    automata = P["automata"]
    arms = {"causal_tf", "gru_mlp", "rnn_mlp", "spec"}
    sel = arms if which is None else {x.strip() for x in which.split(",")}

    k, K = map(int, part.split("/"))
    job_idx = 0

    def take() -> bool:
        nonlocal job_idx
        ok = (job_idx % K) == k
        job_idx += 1
        return ok

    cfgs = [
        ("causal_tf", 2000, 3e-3, None, 410_000),
        ("gru_mlp", 1200, 4e-3, None, 420_000),
        ("rnn_mlp", 1500, 4e-3, 1.0, 430_000),
    ]
    for arch, steps, lr, cnorm, sbase in cfgs:
        if arch not in sel:
            continue
        for idx_a, A in enumerate(automata):
            if not take():
                continue
            pth = RAW / f"{arch}_{A['name']}.json"
            if pth.exists():
                continue
            t0 = time.perf_counter()
            Dl = np.array(A["Dl"], dtype=int)
            O = np.array(A["out"], float)
            pi = np.array(A["pi"], float)
            ops = _ops_from_item(A)
            seed = sbase + 10 * idx_a
            fit, fit_all, Ce = train_one(Dl, O, A["s0"], A["m"], arch, steps, lr, seed, clip_norm=cnorm)
            res = measure_gram(Ce, pi, ops)
            rec = {"arm": arch, "name": A["name"], "family": A["family"], "k_definite": A.get("k_definite"),
                   "seed": seed, "fit": fit, "fit_all": fit_all, "res": res, "secs": round(time.perf_counter() - t0, 1)}
            pth.write_text(json.dumps(rec))
            print(f"{arch:10s} {A['name']:15s} ({A['family']:10s}) fit={fit:.4f} "
                  f"kin={round(res['kin_norm'],3) if res else None} lam={round(res['lam_emp'],2) if res else None} "
                  f"cos0={round(res['cos_G0'],3) if res else None} cosL0={round(res['cos_G_lam0'],3) if res else None} "
                  f"cosEmp={round(res['cos_G_emp'],3) if res else None} ({rec['secs']}s)", flush=True)

    if "spec" in sel:
        for idx_a, A in enumerate(automata):
            if not take():
                continue
            pth = RAW / f"spec_{A['name']}.json"
            if pth.exists():
                continue
            Dl = np.array(A["Dl"], dtype=int)
            O = np.array(A["out"], float)
            pi = np.array(A["pi"], float)
            ops = _ops_from_item(A)
            F = run_spec_one(Dl, O, A["m"], 440_000 + idx_a)
            res = measure_gram(F, pi, ops)
            rec = {"arm": "spec", "name": A["name"], "family": A["family"], "fit": 1.0, "res": res}
            pth.write_text(json.dumps(rec))
            print(f"spec       {A['name']:15s} ({A['family']:10s}) cosWo={res['cos_Wo']:.3f} cosG0={res['cos_G0']:.3f}", flush=True)


def analyse():
    P = json.loads(PRED.read_text())
    info = {A["name"]: A for A in P["automata"]}
    runs = [json.loads(f.read_text()) for f in sorted(RAW.glob("*.json"))]

    tri = lambda val, n_unit, need, hi, lo: (
        "NO VERDICT" if val is None or n_unit < need
        else "HELD" if val >= hi
        else "BROKEN" if val < lo
        else "NEITHER"
    )

    by_arm_fam: dict[str, dict[str, dict]] = {}
    for arm in ("causal_tf", "gru_mlp", "rnn_mlp", "spec"):
        by_arm_fam[arm] = {}
        for fam in ("free", "k_definite", "group", "non_group"):
            rs = [
                r for r in runs
                if r["arm"] == arm and r["res"] is not None and r["fit"] >= 0.90
                and (r["family"] in ("free", "k_definite") if fam == "non_group" else r["family"] == fam)
            ]
            all_rs = [
                r for r in runs
                if r["arm"] == arm
                and (r["family"] in ("free", "k_definite") if fam == "non_group" else r["family"] == fam)
            ]
            if not rs:
                by_arm_fam[arm][fam] = {
                    "n_total": len(all_rs), "n_fitted": 0,
                    "mean_fit_all_runs": float(np.mean([x["fit"] for x in all_rs])) if all_rs else None,
                }
                continue
            by_arm_fam[arm][fam] = {
                "n_total": len(all_rs),
                "n_fitted": len(rs),
                "mean_fit_all_runs": float(np.mean([x["fit"] for x in all_rs])),
                "med_kin": float(np.median([x["res"]["kin_norm"] for x in rs])),
                "mean_kin": float(np.mean([x["res"]["kin_norm"] for x in rs])),
                "med_lam_emp": float(np.median([x["res"]["lam_emp"] for x in rs])),
                "mean_lam_emp": float(np.mean([x["res"]["lam_emp"] for x in rs])),
                "mean_cos_G0": float(np.mean([x["res"]["cos_G0"] for x in rs])),
                "mean_cos_G_lam0": float(np.mean([x["res"]["cos_G_lam0"] for x in rs])),
                "mean_cos_G_emp": float(np.mean([x["res"]["cos_G_emp"] for x in rs])),
                "mean_cos_Wo": float(np.mean([x["res"]["cos_Wo"] for x in rs])),
                "mean_cos_Wo_heat": float(np.mean([x["res"]["cos_Wo_heat"] for x in rs])),
                "mean_cos_Wc": float(np.mean([x["res"]["cos_Wc"] for x in rs])),
                "mean_cos_o": float(np.mean([x["res"]["cos_o"] for x in rs])),
            }

    # HTF.1: CausalTF higher kin_norm and lower lam_emp than RNN-MLP on matched non_group (fit >= 0.90)
    tf_ng = {r["name"]: r for r in runs if r["arm"] == "causal_tf" and r["family"] != "group" and r["fit"] >= 0.90 and r["res"]}
    rnn_ng = {r["name"]: r for r in runs if r["arm"] == "rnn_mlp" and r["family"] != "group" and r["fit"] >= 0.90 and r["res"]}
    common_names = sorted(set(tf_ng) & set(rnn_ng))
    htf1_pairs = [{
        "name": nm,
        "kin_tf": tf_ng[nm]["res"]["kin_norm"], "kin_rnn": rnn_ng[nm]["res"]["kin_norm"],
        "lam_tf": tf_ng[nm]["res"]["lam_emp"], "lam_rnn": rnn_ng[nm]["res"]["lam_emp"],
        "tf_rougher": tf_ng[nm]["res"]["kin_norm"] > rnn_ng[nm]["res"]["kin_norm"],
        "tf_cooler_lam_lower": tf_ng[nm]["res"]["lam_emp"] < rnn_ng[nm]["res"]["lam_emp"],
    } for nm in common_names]
    htf1_frac = float(np.mean([p["tf_rougher"] and p["tf_cooler_lam_lower"] for p in htf1_pairs])) if htf1_pairs else None

    # HTF.2: CausalTF G_emp (and G0) beats raw observable o where cos(G_emp, o) < 0.95 (on fitted non_group)
    disc_o = [
        r for r in tf_ng.values()
        if cos_mat(eval_G_at(np.array(info[r["name"]]["Lkin"]), np.array(info[r["name"]]["G0"]),
                             np.array(info[r["name"]]["pi"]), r["res"]["lam_emp"]),
                   np.array(info[r["name"]]["o"])) < 0.95
    ]
    htf2_beat_o = float(np.mean([r["res"]["cos_G_emp"] > r["res"]["cos_o"] for r in disc_o])) if disc_o else None

    # HTF.3: k-definite vs periodic-group fit dichotomy for CausalTF
    tf_def_all = [r for r in runs if r["arm"] == "causal_tf" and r["family"] == "k_definite"]
    tf_grp_all = [r for r in runs if r["arm"] == "causal_tf" and r["family"] == "group"]
    m_fit_def = float(np.mean([r["fit"] for r in tf_def_all])) if tf_def_all else None
    m_fit_grp = float(np.mean([r["fit"] for r in tf_grp_all])) if tf_grp_all else None

    # HTF.4: Boundary test G(0) vs G(LAM0) on CausalTF (fitted non_group)
    htf4_g0_gt_lam0 = float(np.mean([r["res"]["cos_G0"] > r["res"]["cos_G_lam0"] for r in tf_ng.values()])) if tf_ng else None

    verdicts = {
        "HTF.1": tri(htf1_frac, len(htf1_pairs), 8, 0.75, 0.50),
        "HTF.2": tri(htf2_beat_o, len(disc_o), 6, 0.75, 0.50),
        "HTF.3": ("NO VERDICT" if (m_fit_def is None or m_fit_grp is None or len(tf_def_all) < 4 or len(tf_grp_all) < 4)
                  else "HELD" if (m_fit_def >= 0.95 and m_fit_def > m_fit_grp + 0.05)
                  else "BROKEN" if m_fit_def <= m_fit_grp
                  else "NEITHER"),
        "HTF.4": tri(htf4_g0_gt_lam0, len(tf_ng), 8, 0.75, 0.50),
    }

    summary = {
        "verdicts": verdicts,
        "by_arm_family": by_arm_fam,
        "htf1_detail": {"n_pairs": len(htf1_pairs), "frac": htf1_frac, "pairs": htf1_pairs},
        "htf2_detail": {"n_disc_o": len(disc_o), "frac_G_emp_gt_o": htf2_beat_o},
        "htf3_detail": {
            "n_def": len(tf_def_all), "mean_fit_k_def": m_fit_def, "fits_k_def": {r["name"]: r["fit"] for r in tf_def_all},
            "n_grp": len(tf_grp_all), "mean_fit_group": m_fit_grp, "fits_group": {r["name"]: r["fit"] for r in tf_grp_all},
        },
        "htf4_detail": {"n_non_group_fitted": len(tf_ng), "frac_G0_gt_Glam0": htf4_g0_gt_lam0},
    }
    OUT.write_text(json.dumps(summary, indent=1))
    print(json.dumps({"verdicts": verdicts, "htf3": summary["htf3_detail"], "htf4": summary["htf4_detail"],
                      "by_arm_family": by_arm_fam}, indent=2))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "run":
        run(sys.argv[2] if len(sys.argv) > 2 else None,
            sys.argv[3] if len(sys.argv) > 3 else "0/1")
    else:
        {"predict": predict, "analyse": analyse}[cmd]()
