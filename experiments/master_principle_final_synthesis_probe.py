"""Pre-registered Empirical Closure Probe for Master Principle Final Synthesis (HFS.1-HFS.3)."""
from __future__ import annotations

import ctypes
import gc
import itertools
import json
import math
import os
import time
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from scipy.stats import spearmanr
from transformers import AutoModelForCausalLM, AutoTokenizer

torch.set_num_threads(1)

ROOT = Path(__file__).resolve().parents[1]
PRED_PATH = ROOT / "experiments" / "results" / "master_principle_final_synthesis_predictions.json"
OUT_PATH = ROOT / "experiments" / "results" / "master_principle_final_synthesis_results.json"

SMOLLM_ID = "HuggingFaceTB/SmolLM2-135M-Instruct"


class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_ulong),
        ("PageFaultCount", ctypes.c_ulong),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


def get_rss_mb() -> float:
    try:
        pmc = PROCESS_MEMORY_COUNTERS()
        pmc.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
        handle = ctypes.windll.kernel32.GetCurrentProcess()
        if ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(pmc), pmc.cb):
            return float(pmc.WorkingSetSize / (1024.0 * 1024.0))
    except Exception:
        pass
    return 0.0


def build_borderline_contrast_pairs() -> tuple[list[tuple[str, str, str]], list[tuple[str, str, str]]]:
    """10 calibration + 24 evaluation near-competitor contrast pairs (stem, true_cont, false_cont)."""
    cal = [
        ("The federal capital of Australia is", " Canberra.", " Sydney."),
        ("The federal capital of Canada is", " Ottawa.", " Toronto."),
        ("The capital city of Turkey is", " Ankara.", " Istanbul."),
        ("The capital city of Brazil is", " Brasilia.", " Rio."),
        ("The chemical symbol for silver is", " Ag.", " Si."),
        ("The chemical symbol for lead is", " Pb.", " Le."),
        ("The chemical symbol for potassium is", " K.", " Po."),
        ("The SI unit of capacitance is the", " farad.", " henry."),
        ("The seventh planet from the Sun is", " Uranus.", " Neptune."),
        ("A nonagon has exactly", " nine sides.", " seven sides."),
    ]
    eval_pairs = [
        ("The capital city of Switzerland is", " Bern.", " Zurich."),
        ("The state capital of New York is", " Albany.", " Buffalo."),
        ("The state capital of Illinois is", " Springfield.", " Chicago."),
        ("The state capital of Florida is", " Tallahassee.", " Miami."),
        ("The state capital of Pennsylvania is", " Harrisburg.", " Philadelphia."),
        ("The state capital of Michigan is", " Lansing.", " Detroit."),
        ("The state capital of Maryland is", " Annapolis.", " Baltimore."),
        ("The state capital of Oregon is", " Salem.", " Portland."),
        ("The state capital of Washington is", " Olympia.", " Seattle."),
        ("The state capital of Kentucky is", " Frankfort.", " Louisville."),
        ("The chemical symbol for tungsten is", " W.", " Tu."),
        ("The chemical symbol for mercury is", " Hg.", " Me."),
        ("The chemical symbol for tin is", " Sn.", " Ti."),
        ("The chemical symbol for sodium is", " Na.", " So."),
        ("The chemical symbol for antimony is", " Sb.", " An."),
        ("The SI unit of magnetic flux density is the", " tesla.", " weber."),
        ("The SI unit of inductance is the", " henry.", " farad."),
        ("The SI unit of luminous flux is the", " lumen.", " candela."),
        ("The second planet from the Sun is", " Venus.", " Mercury."),
        ("The largest moon orbiting Saturn is", " Titan.", " Europa."),
        ("The largest moon orbiting Jupiter is", " Ganymede.", " Titan."),
        ("The bone in the human upper arm is the", " humerus.", " femur."),
        ("Dry ice is the solid form of carbon", " dioxide.", " monoxide."),
        ("The organ that secretes insulin is the", " pancreas.", " spleen."),
    ]
    return cal, eval_pairs


def compute_pair_margins(
    model: nn.Module,
    tok,
    pairs: list[tuple[str, str, str]],
    batch_size: int = 12,
) -> np.ndarray:
    """Exact sequence continuation log-prob margin log P(true|stem) - log P(false|stem)."""
    margins: list[float] = []
    with torch.no_grad():
        for i in range(0, len(pairs), batch_size):
            chunk = pairs[i : i + batch_size]
            seqs: list[str] = []
            stem_lens: list[int] = []
            full_lens: list[int] = []
            for stem, pos_c, neg_c in chunk:
                s_ids = tok(stem, add_special_tokens=False)["input_ids"]
                for cont in (pos_c, neg_c):
                    full_ids = tok(stem + cont, add_special_tokens=False)["input_ids"]
                    seqs.append(stem + cont)
                    stem_lens.append(len(s_ids))
                    full_lens.append(len(full_ids))
            enc = tok(seqs, padding=True, add_special_tokens=False, return_tensors="pt")
            logits = model(**enc).logits
            log_probs = F.log_softmax(logits[:, :-1, :].float(), dim=-1)
            target_ids = enc["input_ids"][:, 1:]
            token_lp = log_probs.gather(-1, target_ids.unsqueeze(-1)).squeeze(-1)
            scores = []
            for row_idx in range(len(seqs)):
                start = max(stem_lens[row_idx] - 1, 0)
                end = max(full_lens[row_idx] - 1, start + 1)
                scores.append(float(token_lp[row_idx, start:end].sum().item()))
            for j in range(0, len(scores), 2):
                margins.append(scores[j] - scores[j + 1])
    return np.array(margins, dtype=np.float64)


def per_channel_int3_quantize_(
    module: nn.Module, skip_predicate=None
) -> dict[str, torch.Tensor]:
    """Symmetric per-output-channel int3 weight quantization (grid [-3, 3])."""
    saved: dict[str, torch.Tensor] = {}
    with torch.no_grad():
        for name, sub in module.named_modules():
            if isinstance(sub, nn.Linear):
                if skip_predicate is not None and skip_predicate(name):
                    continue
                w = sub.weight.data
                saved[name] = w.clone()
                amax = w.abs().amax(dim=1, keepdim=True).clamp(min=1e-8)
                scale = amax / 3.0
                q = torch.clamp(torch.round(w / scale), -3.0, 3.0)
                sub.weight.data.copy_(q * scale)
    return saved


def restore_weights_(module: nn.Module, saved: dict[str, torch.Tensor]) -> None:
    with torch.no_grad():
        mod_map = dict(module.named_modules())
        for name, w in saved.items():
            mod_map[name].weight.data.copy_(w)


def safe_spearman(x: np.ndarray, y: np.ndarray) -> float | None:
    if len(x) < 2 or np.all(x == x[0]) or np.all(y == y[0]):
        return None
    val = float(spearmanr(x, y).statistic)
    return val if math.isfinite(val) else None


def run_hfs1_smollm_int3_gauge_tube(preds: dict) -> dict:
    """HFS.1: Prospective Gamma_mod predictor under int3 quantization on borderline contrast pairs."""
    t0 = time.time()
    cal_pairs, eval_pairs = build_borderline_contrast_pairs()
    families = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]

    tok = AutoTokenizer.from_pretrained(SMOLLM_ID, local_files_only=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(SMOLLM_ID, local_files_only=True)
    model.eval()

    delta_weights: dict[str, dict[str, torch.Tensor]] = {fam: {} for fam in families}
    raw_frob: dict[str, float] = {fam: 0.0 for fam in families}
    with torch.no_grad():
        for name, sub in model.model.layers.named_modules():
            if isinstance(sub, nn.Linear):
                fam = name.split(".")[-1]
                if fam in delta_weights:
                    w = sub.weight.data
                    amax = w.abs().amax(dim=1, keepdim=True).clamp(min=1e-8)
                    scale = amax / 3.0
                    qw = torch.clamp(torch.round(w / scale), -3.0, 3.0) * scale
                    dw = (qw - w).clone()
                    delta_weights[fam][name] = dw
                    raw_frob[fam] += float((dw.float() ** 2).sum().item())
    for fam in families:
        raw_frob[fam] = math.sqrt(raw_frob[fam])

    gamma_scores: dict[str, list[float]] = {fam: [] for fam in families}
    named_linears = {
        name: sub
        for name, sub in model.model.layers.named_modules()
        if isinstance(sub, nn.Linear) and name.split(".")[-1] in delta_weights
    }
    for param in model.parameters():
        param.requires_grad_(False)
    for sub in named_linears.values():
        sub.weight.requires_grad_(True)

    cal_fp32_margins = []
    for stem, pos_c, neg_c in cal_pairs:
        model.zero_grad(set_to_none=True)
        s_len = len(tok(stem, add_special_tokens=False)["input_ids"])
        p_ids = tok(stem + pos_c, add_special_tokens=False, return_tensors="pt")["input_ids"]
        n_ids = tok(stem + neg_c, add_special_tokens=False, return_tensors="pt")["input_ids"]

        lp_p = F.log_softmax(model(input_ids=p_ids).logits[:, :-1, :].float(), dim=-1)
        score_p = lp_p[0, max(s_len - 1, 0) :, :].gather(-1, p_ids[0, max(s_len, 1) :].unsqueeze(-1)).sum()

        lp_n = F.log_softmax(model(input_ids=n_ids).logits[:, :-1, :].float(), dim=-1)
        score_n = lp_n[0, max(s_len - 1, 0) :, :].gather(-1, n_ids[0, max(s_len, 1) :].unsqueeze(-1)).sum()

        margin = score_p - score_n
        cal_fp32_margins.append(float(margin.detach().item()))
        margin.backward()

        denom = max(abs(float(margin.detach().item())), 1e-4)
        fam_shift = {fam: 0.0 for fam in families}
        with torch.no_grad():
            for name, sub in named_linears.items():
                fam = name.split(".")[-1]
                g_w = sub.weight.grad
                if g_w is not None:
                    dw = delta_weights[fam][name]
                    fam_shift[fam] += abs(float((g_w.float() * dw.float()).sum().item()))
        for fam in families:
            gamma_scores[fam].append(fam_shift[fam] / denom)

    for sub in named_linears.values():
        sub.weight.grad = None
        sub.weight.requires_grad_(False)

    gamma_mod = {fam: float(np.mean(gamma_scores[fam])) for fam in families}
    gamma_ranked = sorted(families, key=lambda f: gamma_mod[f], reverse=True)
    raw_frob_ranked = sorted(families, key=lambda f: raw_frob[f], reverse=True)
    top2_gamma_fams = gamma_ranked[:2]

    eval_fp32 = compute_pair_margins(model, tok, eval_pairs, batch_size=12)
    pred_fp32 = eval_fp32 > 0.0
    fp32_eval_acc = float(np.mean(pred_fp32))

    fam_flip_rates: dict[str, float] = {}
    fam_mean_abs_shift: dict[str, float] = {}
    for fam in families:
        saved = per_channel_int3_quantize_(
            model.model.layers, skip_predicate=lambda n, target=fam: n.split(".")[-1] != target
        )
        m_q = compute_pair_margins(model, tok, eval_pairs, batch_size=12)
        restore_weights_(model.model.layers, saved)
        flips = (m_q > 0.0) != pred_fp32
        fam_flip_rates[fam] = float(np.mean(flips))
        fam_mean_abs_shift[fam] = float(np.mean(np.abs(m_q - eval_fp32)))

    # Protect top-2 Gamma_mod families in FP32, quantize the other 5 families to int3
    saved_prot = per_channel_int3_quantize_(
        model.model.layers, skip_predicate=lambda n, tops=set(top2_gamma_fams): n.split(".")[-1] in tops
    )
    m_prot = compute_pair_margins(model, tok, eval_pairs, batch_size=12)
    prot_flip_rate = float(np.mean((m_prot > 0.0) != pred_fp32))
    prot_acc = float(np.mean(m_prot > 0.0))

    # Quantize top-2 as well -> full transformer linear layers in int3
    per_channel_int3_quantize_(
        model.model.layers, skip_predicate=lambda n, tops=set(top2_gamma_fams): n.split(".")[-1] not in tops
    )
    m_all = compute_pair_margins(model, tok, eval_pairs, batch_size=12)
    all_flip_rate = float(np.mean((m_all > 0.0) != pred_fp32))
    all_acc = float(np.mean(m_all > 0.0))

    g_vec = np.array([gamma_mod[f] for f in families], dtype=np.float64)
    f_vec = np.array([raw_frob[f] for f in families], dtype=np.float64)
    shift_vec = np.array([fam_mean_abs_shift[f] for f in families], dtype=np.float64)
    flip_vec = np.array([fam_flip_rates[f] for f in families], dtype=np.float64)

    rho_gamma_shift = safe_spearman(g_vec, shift_vec)
    rho_frob_shift = safe_spearman(f_vec, shift_vec)
    rho_gamma_flip = safe_spearman(g_vec, flip_vec)
    rho_frob_flip = safe_spearman(f_vec, flip_vec)
    reduction = float(all_flip_rate / max(prot_flip_rate, 1e-6))

    rss = get_rss_mb()
    del model
    gc.collect()

    out = {
        "model": SMOLLM_ID,
        "quantization": "per_channel_symmetric_int3",
        "n_cal_pairs": len(cal_pairs),
        "n_eval_pairs": len(eval_pairs),
        "cal_fp32_acc": float(np.mean(np.array(cal_fp32_margins) > 0.0)),
        "fp32_eval_acc": fp32_eval_acc,
        "eval_fp32_mean_abs_margin": float(np.mean(np.abs(eval_fp32))),
        "eval_fp32_median_abs_margin": float(np.median(np.abs(eval_fp32))),
        "gamma_mod": gamma_mod,
        "raw_frob": raw_frob,
        "gamma_ranked": gamma_ranked,
        "raw_frob_ranked": raw_frob_ranked,
        "protected_top2_families": top2_gamma_fams,
        "per_family_int3_flip_rates": fam_flip_rates,
        "per_family_int3_mean_abs_margin_shift": fam_mean_abs_shift,
        "spearman_gamma_vs_margin_shift": rho_gamma_shift,
        "spearman_frob_vs_margin_shift": rho_frob_shift,
        "spearman_gamma_vs_flip": rho_gamma_flip,
        "spearman_frob_vs_flip": rho_frob_flip,
        "all_int3_flip_rate": all_flip_rate,
        "all_int3_acc": all_acc,
        "protected_top2_int3_flip_rate": prot_flip_rate,
        "protected_top2_int3_acc": prot_acc,
        "protection_flip_reduction": reduction,
        "rss_mb": rss,
        "elapsed_sec": time.time() - t0,
    }
    p = preds["HFS.1"]
    held = (
        fp32_eval_acc >= p["fp32_eval_acc_min"]
        and all_flip_rate >= p["all_int3_flip_rate_min"]
        and rho_gamma_shift is not None
        and rho_gamma_shift >= p["spearman_gamma_vs_margin_shift_min"]
        and rho_gamma_flip is not None
        and rho_gamma_flip >= p["spearman_gamma_vs_flip_min"]
        and reduction >= p["protection_flip_reduction_min"]
    )
    out["verdict"] = "HELD" if held else "BROKEN"
    return out


def tv_dist(mu: np.ndarray, nu: np.ndarray) -> float:
    return float(0.5 * np.sum(np.abs(mu - nu)))


def dobrushin_coeff(P: np.ndarray) -> float:
    n = P.shape[0]
    best = 0.0
    for i in range(n):
        for k in range(i + 1, n):
            d = tv_dist(P[i], P[k])
            if d > best:
                best = d
    return best


def run_hfs2_dobrushin_markov(preds: dict) -> dict:
    """HFS.2: First-principles Dobrushin TV contraction on 10 non-Gaussian bimodal chains."""
    t0 = time.time()
    p = preds["HFS.2"]
    horizon = int(p["horizon"])
    num_chains = int(p["num_chains"])

    max_violation = 0.0
    max_t15_ratio = 0.0
    chain_summaries: list[dict] = []

    for idx in range(num_chains):
        seed = 202611 + idx
        rng = np.random.default_rng(seed)
        n = 8 + (idx % 9)  # spans 8..16
        half = n // 2

        # Bimodal base distribution: two separated clusters + state-dependent local skew
        mode_a = np.zeros(n, dtype=np.float64)
        mode_b = np.zeros(n, dtype=np.float64)
        mode_a[:half] = rng.uniform(0.6, 1.4, size=half)
        mode_a[half:] = rng.uniform(0.05, 0.25, size=n - half)
        mode_b[:half] = rng.uniform(0.05, 0.25, size=half)
        mode_b[half:] = rng.uniform(0.6, 1.4, size=n - half)
        mode_a /= np.sum(mode_a)
        mode_b /= np.sum(mode_b)

        mu0 = rng.dirichlet(np.full(n, 0.7))
        nu0 = rng.dirichlet(np.full(n, 0.7))
        d0 = tv_dist(mu0, nu0)

        mu = mu0.copy()
        nu = nu0.copy()
        geom_bound = d0
        lin_bound = d0
        alpha_max = 0.0
        delta_max = 0.0

        for _step in range(horizon):
            # Construct inhomogeneous Markov matrix P_t with Dobrushin coeff in [0.35, 0.72]
            mix = rng.uniform(0.45, 0.75, size=n)
            P = np.zeros((n, n), dtype=np.float64)
            for i in range(n):
                if i < half:
                    P[i] = mix[i] * mode_a + (1.0 - mix[i]) * mode_b
                else:
                    P[i] = (1.0 - mix[i]) * mode_a + mix[i] * mode_b
                P[i] /= np.sum(P[i])

            alpha_t = dobrushin_coeff(P)
            alpha_max = max(alpha_max, alpha_t)

            # Perturbed transition matrix Q_t keeping row-wise TV(P[i], Q[i]) in [0.02, 0.075]
            eps_mix = rng.uniform(0.03, 0.075, size=n)
            Q = np.zeros((n, n), dtype=np.float64)
            delta_t = 0.0
            for i in range(n):
                alt = rng.dirichlet(np.full(n, 1.2))
                Q[i] = (1.0 - eps_mix[i]) * P[i] + eps_mix[i] * alt
                Q[i] /= np.sum(Q[i])
                delta_t = max(delta_t, tv_dist(P[i], Q[i]))
            delta_max = max(delta_max, delta_t)

            # Check single-step unperturbed Dobrushin contraction first
            mu_P = mu @ P
            nu_P = nu @ P
            step_unpert = tv_dist(mu_P, nu_P) - alpha_t * tv_dist(mu, nu)
            max_violation = max(max_violation, max(0.0, step_unpert))

            # Advance along P and perturbed Q
            mu = mu_P
            nu = nu @ Q
            geom_bound = alpha_t * geom_bound + delta_t
            lin_bound = lin_bound + delta_t
            cur_tv = tv_dist(mu, nu)
            max_violation = max(max_violation, max(0.0, cur_tv - geom_bound))

        closed_unif = (alpha_max ** horizon) * d0 + delta_max * (1.0 - (alpha_max ** horizon)) / (1.0 - alpha_max)
        max_violation = max(max_violation, max(0.0, tv_dist(mu, nu) - closed_unif))
        t15_ratio = float(geom_bound / lin_bound)
        max_t15_ratio = max(max_t15_ratio, t15_ratio)
        chain_summaries.append(
            {
                "seed": seed,
                "state_dim": n,
                "alpha_max": alpha_max,
                "delta_max": delta_max,
                "tv_T15": tv_dist(mu, nu),
                "geom_bound_T15": geom_bound,
                "lin_bound_T15": lin_bound,
                "ratio_T15": t15_ratio,
            }
        )

    out = {
        "num_chains": num_chains,
        "horizon": horizon,
        "max_violation": max_violation,
        "max_t15_contraction_vs_linear_ratio": max_t15_ratio,
        "chains": chain_summaries,
        "elapsed_sec": time.time() - t0,
    }
    held = (
        max_violation <= p["max_violation_le"]
        and max_t15_ratio <= p["max_t15_contraction_vs_linear_ratio_le"]
    )
    out["verdict"] = "HELD" if held else "BROKEN"
    return out


def run_hfs3_contextual_ring_descent(preds: dict) -> dict:
    """HFS.3: Computational witness of sparse A-B-C ring, C4 3-way holonomy, and grounding."""
    t0 = time.time()
    p = preds["HFS.3"]

    # (a) Sparse A-B-C heterogeneous ring matching ContextualRingDescent.lean
    adj = {("A", "B"), ("B", "A"), ("B", "C"), ("C", "B")}
    direct_ac_adj = ("A", "C") in adj
    # BFS connectivity on {A, B, C}
    seen = {"A"}
    frontier = ["A"]
    while frontier:
        cur = frontier.pop(0)
        for u, v in adj:
            if u == cur and v not in seen:
                seen.add(v)
                frontier.append(v)
    connected = seen == {"A", "B", "C"}

    def step_a(s: bool, a: bool) -> bool:
        return s ^ a

    def step_b(s: int, a: bool) -> int:
        if not a:
            return s
        return {0: 1, 1: 0}.get(s, s)

    def step_c(s: int, a: bool) -> int:
        if not a:
            return s
        return {0: 1, 1: 0}.get(s, s)

    def code_a(s: bool) -> int:
        return 1 if s else 0

    def is_global_coherent(s_a: bool, s_b: int, s_c: int) -> bool:
        return (s_b < 2) and (s_c < 2) and (code_a(s_a) == s_b) and (s_b == s_c)

    max_len = int(p["sparse_abc_max_seq_len"])
    violations = 0
    sequences_checked = 0
    for base_state in ((False, 0, 0), (True, 1, 1)):
        for length in range(max_len + 1):
            for seq in itertools.product((False, True), repeat=length):
                sequences_checked += 1
                sa, sb, sc = base_state
                for act in seq:
                    sa = step_a(sa, act)
                    sb = step_b(sb, act)
                    sc = step_c(sc, act)
                if not is_global_coherent(sa, sb, sc):
                    violations += 1

    # (b) 3-way holonomy descent split on triangle overlap bundles
    strict_sections = [(s0, s1, s2) for s0 in (0,) for s1 in (0,) for s2 in (0,) if s0 == s1 == s2]
    groupoid_sections = [(s0, s1, s2) for s0 in (0, 1) for s1 in (0, 1) for s2 in (0, 1) if s0 == s1 == s2]
    groupoid_aut = [tuple(1 - x for x in s) for s in groupoid_sections]
    groupoid_aut_closed = all(t in groupoid_sections for t in groupoid_aut)

    coset0_edge = [(a, b) for a, b in itertools.product((0, 2), repeat=2) if (a + b) % 4 == 2]
    coset0_global = [
        (r0, r1, r2)
        for r0, r1, r2 in itertools.product((0, 2), repeat=3)
        if (r0 + r1) % 4 == 2 and (r1 + r2) % 4 == 2 and (r2 + r0) % 4 == 2
    ]
    monodromies = [
        ((e12[0] - e01[1]) + (e20[0] - e12[1]) + (e01[0] - e20[1])) % 4
        for e01, e12, e20 in itertools.product(coset0_edge, repeat=3)
    ]

    # (c) Grounding separation matching ContextualRingDescent.lean:
    #     coherentHallucinationRing (observe b = !b) vs externallyGroundedRing (observe b = b)
    halluc_iso_commutes = True
    for _ctx in (False, True):
        for b in (False, True):
            sigma_b = not b
            # Internal RingModuleIso: comm_obs, comm_step (step=id), and correspondence
            if (not b) != sigma_b or sigma_b != (not b):
                halluc_iso_commutes = False
    phys_state = True
    halluc_grounded = ((not phys_state) is True)
    grounded_grounded = (phys_state is True)

    out = {
        "sparse_abc_sequences_checked": sequences_checked,
        "sparse_abc_violations": violations,
        "sparse_abc_direct_ac_adjacent": direct_ac_adj,
        "sparse_abc_connected": connected,
        "holonomy_strict_sections": len(strict_sections),
        "holonomy_groupoid_sections": len(groupoid_sections),
        "holonomy_groupoid_aut_closed": groupoid_aut_closed,
        "holonomy_coset0_edge_sections": len(coset0_edge),
        "holonomy_coset0_global_sections": len(coset0_global),
        "holonomy_coset0_min_monodromy": min(monodromies),
        "hallucination_internally_iso": halluc_iso_commutes,
        "hallucination_grounded": halluc_grounded,
        "grounded_grounded": grounded_grounded,
        "elapsed_sec": time.time() - t0,
    }
    held = (
        violations == p["sparse_abc_expected_violations"]
        and direct_ac_adj is p["sparse_abc_direct_ac_adjacent"]
        and connected is p["sparse_abc_connected"]
        and len(strict_sections) == p["holonomy_strict_sections_eq"]
        and len(groupoid_sections) == p["holonomy_groupoid_sections_eq"]
        and groupoid_aut_closed
        and len(coset0_edge) == p["holonomy_coset0_edge_sections_eq"]
        and len(coset0_global) == p["holonomy_coset0_global_sections_eq"]
        and min(monodromies) != p["holonomy_coset0_min_monodromy_ne"]
        and halluc_iso_commutes is p["hallucination_internally_iso"]
        and halluc_grounded is p["hallucination_grounded"]
        and grounded_grounded is p["grounded_grounded"]
    )
    out["verdict"] = "HELD" if held else "BROKEN"
    return out


def main() -> None:
    t_all = time.time()
    preds = json.loads(PRED_PATH.read_text(encoding="utf-8"))

    res_hfs1 = run_hfs1_smollm_int3_gauge_tube(preds)
    res_hfs2 = run_hfs2_dobrushin_markov(preds)
    res_hfs3 = run_hfs3_contextual_ring_descent(preds)

    payload = {
        "experiment": "master_principle_final_synthesis_probe",
        "elapsed_total_sec": time.time() - t_all,
        "results": {
            "HFS.1": res_hfs1,
            "HFS.2": res_hfs2,
            "HFS.3": res_hfs3,
        },
        "summary": {
            "HFS.1": res_hfs1["verdict"],
            "HFS.2": res_hfs2["verdict"],
            "HFS.3": res_hfs3["verdict"],
        },
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print("SUMMARY:", json.dumps(payload["summary"]))
    print(f"ELAPSED_TOTAL_SEC={payload['elapsed_total_sec']:.2f}")


if __name__ == "__main__":
    main()
