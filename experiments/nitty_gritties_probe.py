"""Pre-registered Empirical Probe for Master Principle Nitty-Gritties (HNG.1-HNG.4)."""
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
os.environ["HF_HUB_DISABLE_XET"] = "1"
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from huggingface_hub import hf_hub_download
from safetensors import safe_open
from scipy.special import gammaln
from scipy.stats import spearmanr
from transformers import AutoConfig, AutoTokenizer
from transformers.models.qwen2.modeling_qwen2 import (
    Qwen2DecoderLayer,
    Qwen2RMSNorm,
    Qwen2RotaryEmbedding,
)

torch.set_num_threads(1)

SEED = 20261124
ROOT = Path(__file__).resolve().parents[1]
PRED_PATH = ROOT / "experiments" / "results" / "nitty_gritties_predictions.json"
OUT_PATH = ROOT / "experiments" / "results" / "nitty_gritties_results.json"

QWEN_ID = "Qwen/Qwen2.5-1.5B-Instruct"


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


def safe_spearman(x: np.ndarray, y: np.ndarray) -> float | None:
    if len(x) < 2 or np.all(x == x[0]) or np.all(y == y[0]):
        return None
    val = float(spearmanr(x, y).statistic)
    return val if math.isfinite(val) else None


def build_single_token_contrast_pairs() -> tuple[list[tuple[str, str, str]], list[tuple[str, str, str]]]:
    """12 calibration + 32 evaluation single-token near-competitor factual contrast pairs."""
    cal = [
        ("The federal capital of Australia is", " Canberra", " Sydney"),
        ("The federal capital of Canada is", " Ottawa", " Toronto"),
        ("The capital city of Turkey is", " Ankara", " Istanbul"),
        ("The capital city of Pakistan is", " Islamabad", " Karachi"),
        ("The chemical symbol for silver is", " Ag", " Si"),
        ("The chemical symbol for lead is", " Pb", " Le"),
        ("The chemical symbol for potassium is", " K", " Po"),
        ("The chemical symbol for gold is", " Au", " Go"),
        ("The chemical symbol for iron is", " Fe", " Ir"),
        ("The chemical symbol for copper is", " Cu", " Co"),
        ("A nonagon has exactly", " nine", " seven"),
        ("A heptagon has exactly", " seven", " six"),
    ]
    eval_pairs = [
        ("The capital city of Switzerland is", " Bern", " Zurich"),
        ("The capital city of Scotland is", " Edinburgh", " Glasgow"),
        ("The capital city of New Zealand is", " Wellington", " Auckland"),
        ("The capital city of Norway is", " Oslo", " Bergen"),
        ("The capital city of Portugal is", " Lisbon", " Porto"),
        ("The state capital of New York is", " Albany", " Buffalo"),
        ("The state capital of Illinois is", " Springfield", " Chicago"),
        ("The state capital of Michigan is", " Lansing", " Detroit"),
        ("The state capital of Oregon is", " Salem", " Portland"),
        ("The state capital of Washington is", " Olympia", " Seattle"),
        ("The state capital of Texas is", " Austin", " Houston"),
        ("The state capital of Ohio is", " Columbus", " Cleveland"),
        ("The state capital of Georgia is", " Atlanta", " Savannah"),
        ("The state capital of Colorado is", " Denver", " Boulder"),
        ("The state capital of Virginia is", " Richmond", " Norfolk"),
        ("The state capital of Nevada is", " Carson", " Reno"),
        ("The state capital of Wisconsin is", " Madison", " Milwaukee"),
        ("The state capital of Arizona is", " Phoenix", " Tucson"),
        ("The state capital of Tennessee is", " Nashville", " Memphis"),
        ("The state capital of Massachusetts is", " Boston", " Worcester"),
        ("The state capital of Hawaii is", " Honolulu", " Maui"),
        ("The state capital of Alabama is", " Montgomery", " Birmingham"),
        ("The chemical symbol for tungsten is", " W", " Tu"),
        ("The chemical symbol for tin is", " Sn", " Ti"),
        ("The chemical symbol for sodium is", " Na", " So"),
        ("The chemical symbol for helium is", " He", " Hy"),
        ("The chemical symbol for argon is", " Ar", " Ag"),
        ("The second planet from the Sun is", " Venus", " Mercury"),
        ("The largest moon orbiting Saturn is", " Titan", " Europa"),
        ("The smallest planet in the Solar System is", " Mercury", " Mars"),
        ("The largest planet in the Solar System is", " Jupiter", " Saturn"),
        ("Sound cannot travel through a", " vacuum", " liquid"),
    ]
    return cal, eval_pairs


def quantize_tensor_int3(w: torch.Tensor) -> torch.Tensor:
    """Symmetric per-output-channel int3 weight quantizer (grid [-3, 3])."""
    wf = w.float()
    amax = wf.abs().amax(dim=1, keepdim=True).clamp(min=1e-8)
    scale = amax / 3.0
    qw = torch.clamp(torch.round(wf / scale), -3.0, 3.0) * scale
    return qw.to(w.dtype)


def encode_single_token_ids(tok, pairs: list[tuple[str, str, str]]) -> tuple[list[str], list[int], list[int]]:
    stems: list[str] = []
    pos_ids: list[int] = []
    neg_ids: list[int] = []
    for stem, pos_c, neg_c in pairs:
        pi = tok.encode(pos_c, add_special_tokens=False)
        ni = tok.encode(neg_c, add_special_tokens=False)
        if len(pi) != 1 or len(ni) != 1 or pi[0] == ni[0]:
            raise ValueError(f"Expected distinct 1-token continuations for {stem!r}: {pi}, {ni}")
        stems.append(stem)
        pos_ids.append(pi[0])
        neg_ids.append(ni[0])
    return stems, pos_ids, neg_ids


def _prepare_batch_tensors(
    tok,
    rotary: Qwen2RotaryEmbedding,
    emb_lookup: dict[int, torch.Tensor],
    stems: list[str],
    pos_ids: list[int],
    neg_ids: list[int],
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, tuple[torch.Tensor, torch.Tensor], torch.Tensor]:
    """Build initial hidden states, 4D left-padded causal mask, position_ids, RoPE, and head diff vectors."""
    enc = tok(stems, padding=True, add_special_tokens=False, return_tensors="pt")
    input_ids = enc["input_ids"]
    attn = enc["attention_mask"]
    bsz, seqlen = input_ids.shape

    h0 = torch.stack(
        [torch.stack([emb_lookup[int(tid)] for tid in input_ids[b]], dim=0) for b in range(bsz)],
        dim=0,
    ).float()
    pos_ids_t = (attn.long().cumsum(dim=-1) - 1).clamp(min=0) * attn.long()
    pos_emb = rotary(h0, pos_ids_t)

    causal_bool = torch.tril(torch.ones((seqlen, seqlen), dtype=torch.bool)).unsqueeze(0).unsqueeze(0)
    key_valid = attn[:, None, None, :].bool()
    eye = torch.eye(seqlen, dtype=torch.bool).unsqueeze(0).unsqueeze(0)
    allow = (causal_bool & key_valid) | eye
    mask_4d = torch.zeros((bsz, 1, seqlen, seqlen), dtype=torch.float32).masked_fill(
        ~allow, torch.finfo(torch.float32).min
    )
    diff_vecs = torch.stack(
        [(emb_lookup[p_id] - emb_lookup[n_id]).float() for p_id, n_id in zip(pos_ids, neg_ids)],
        dim=0,
    )
    return h0, mask_4d, pos_ids_t, pos_emb, diff_vecs


def _step_layer(
    layer: Qwen2DecoderLayer,
    h: torch.Tensor,
    mask_4d: torch.Tensor,
    pos_ids_t: torch.Tensor,
    pos_emb: tuple[torch.Tensor, torch.Tensor],
) -> torch.Tensor:
    out = layer(h, attention_mask=mask_4d, position_ids=pos_ids_t, position_embeddings=pos_emb)
    return out[0] if isinstance(out, tuple) else out


def _score_final_margins(
    final_norm: Qwen2RMSNorm, h: torch.Tensor, diff_vecs: torch.Tensor
) -> np.ndarray:
    normed = final_norm(h[:, -1, :].float())
    margins = (normed * diff_vecs).sum(dim=-1)
    return margins.detach().cpu().numpy().astype(np.float64)


def _find_layer_family_modules(layer: Qwen2DecoderLayer) -> dict[str, nn.Linear]:
    targets = {
        "q_proj": layer.self_attn.q_proj,
        "k_proj": layer.self_attn.k_proj,
        "v_proj": layer.self_attn.v_proj,
        "o_proj": layer.self_attn.o_proj,
        "gate_proj": layer.mlp.gate_proj,
        "up_proj": layer.mlp.up_proj,
        "down_proj": layer.mlp.down_proj,
    }
    return targets


def run_hng1_qwen_scaleup(preds: dict) -> dict:
    """HNG.1: >=1B open-weight Qwen2.5-1.5B-Instruct replication via low-memory layer streaming."""
    t0 = time.time()
    p = preds["HNG.1"]
    eps = float(p["eps"])
    families = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    cal_pairs, eval_pairs = build_single_token_contrast_pairs()
    if len(cal_pairs) != int(p["num_cal"]) or len(eval_pairs) != int(p["num_eval"]):
        raise RuntimeError("Mismatch in HNG.1 pair counts vs predictions.json")

    tok = AutoTokenizer.from_pretrained(QWEN_ID)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    tok.padding_side = "left"

    cal_stems, cal_pos, cal_neg = encode_single_token_ids(tok, cal_pairs)
    eval_stems, eval_pos, eval_neg = encode_single_token_ids(tok, eval_pairs)

    cfg = AutoConfig.from_pretrained(QWEN_ID)
    cfg._attn_implementation = "sdpa"
    try:
        st_path = hf_hub_download(QWEN_ID, filename="model.safetensors", local_files_only=True)
    except Exception:
        st_path = hf_hub_download(QWEN_ID, filename="model.safetensors", local_files_only=False)

    layer = Qwen2DecoderLayer(cfg, layer_idx=0).float().eval()
    rotary = Qwen2RotaryEmbedding(cfg).float().eval()
    final_norm = Qwen2RMSNorm(cfg.hidden_size, eps=cfg.rms_norm_eps).float().eval()
    fam_mods = _find_layer_family_modules(layer)

    needed_ids: set[int] = set(cal_pos) | set(cal_neg) | set(eval_pos) | set(eval_neg)
    for s in cal_stems + eval_stems:
        needed_ids.update(tok.encode(s, add_special_tokens=False))
    if tok.pad_token_id is not None:
        needed_ids.add(int(tok.pad_token_id))

    with safe_open(st_path, framework="pt", device="cpu") as sf:
        param_count = int(sum(math.prod(sf.get_slice(k).get_shape()) for k in sf.keys()))
        emb_slice = sf.get_slice("model.embed_tokens.weight")
        emb_lookup = {tid: emb_slice[int(tid)].float() for tid in sorted(needed_ids)}
        head_key = "lm_head.weight" if "lm_head.weight" in sf.keys() else "model.embed_tokens.weight"
        head_slice = sf.get_slice(head_key)
        head_lookup = {
            tid: head_slice[int(tid)].float()
            for tid in sorted(set(cal_pos) | set(cal_neg) | set(eval_pos) | set(eval_neg))
        }
        final_norm.load_state_dict({"weight": sf.get_tensor("model.norm.weight").float()}, strict=True)

        h0_s0, m4_s0, pid_s0, pe_s0, diff_s0 = _prepare_batch_tensors(
            tok, rotary, emb_lookup, [eval_stems[0]], [eval_pos[0]], [eval_neg[0]]
        )
        h0_cal, m4_cal, pid_cal, pe_cal, diff_cal = _prepare_batch_tensors(
            tok, rotary, emb_lookup, cal_stems, cal_pos, cal_neg
        )
        h0_eval, m4_eval, pid_eval, pe_eval, diff_eval = _prepare_batch_tensors(
            tok, rotary, emb_lookup, eval_stems, eval_pos, eval_neg
        )
        # Recompute exact head difference vectors from head_lookup (handles tied or untied heads)
        diff_s0 = (head_lookup[eval_pos[0]] - head_lookup[eval_neg[0]]).unsqueeze(0).float()
        diff_cal = torch.stack(
            [(head_lookup[p_id] - head_lookup[n_id]).float() for p_id, n_id in zip(cal_pos, cal_neg)], dim=0
        )
        diff_eval = torch.stack(
            [(head_lookup[p_id] - head_lookup[n_id]).float() for p_id, n_id in zip(eval_pos, eval_neg)], dim=0
        )

        print(
            f"[HNG.1] Streaming {QWEN_ID} ({param_count:,} params, {cfg.num_hidden_layers} layers), rss={get_rss_mb():.1f} MB",
            flush=True,
        )

        # Pass 1: baseline + 7 per-family +/-eps directional derivatives + single-family int3 eval
        h_s0 = h0_s0.clone()
        h_cal_base = h0_cal.clone()
        h_eval_base = h0_eval.clone()
        h_cal_plus = {fam: h0_cal.clone() for fam in families}
        h_cal_minus = {fam: h0_cal.clone() for fam in families}
        h_eval_fam = {fam: h0_eval.clone() for fam in families}
        frob_sq = {fam: 0.0 for fam in families}

        with torch.inference_mode():
            for l_idx in range(cfg.num_hidden_layers):
                prefix = f"model.layers.{l_idx}."
                sd = {k[len(prefix) :]: sf.get_tensor(k).float() for k in sf.keys() if k.startswith(prefix)}
                layer.load_state_dict(sd, strict=True)
                clean_w = {fam: fam_mods[fam].weight.data.clone() for fam in families}

                h_s0 = _step_layer(layer, h_s0, m4_s0, pid_s0, pe_s0)
                h_cal_base = _step_layer(layer, h_cal_base, m4_cal, pid_cal, pe_cal)
                h_eval_base = _step_layer(layer, h_eval_base, m4_eval, pid_eval, pe_eval)

                for fam in families:
                    w = clean_w[fam]
                    qw = quantize_tensor_int3(w)
                    dw = qw - w
                    frob_sq[fam] += float((dw**2).sum().item())

                    fam_mods[fam].weight.data.copy_(w + eps * dw)
                    h_cal_plus[fam] = _step_layer(layer, h_cal_plus[fam], m4_cal, pid_cal, pe_cal)

                    fam_mods[fam].weight.data.copy_(w - eps * dw)
                    h_cal_minus[fam] = _step_layer(layer, h_cal_minus[fam], m4_cal, pid_cal, pe_cal)

                    fam_mods[fam].weight.data.copy_(qw)
                    h_eval_fam[fam] = _step_layer(layer, h_eval_fam[fam], m4_eval, pid_eval, pe_eval)

                    fam_mods[fam].weight.data.copy_(w)

                if l_idx in (0, 6, 13, 20, cfg.num_hidden_layers - 1):
                    print(f"[HNG.1] Pass 1 layer {l_idx + 1}/{cfg.num_hidden_layers} elapsed={time.time() - t0:.1f}s", flush=True)

            single_m0 = float(_score_final_margins(final_norm, h_s0, diff_s0)[0])
            m_cal_base = _score_final_margins(final_norm, h_cal_base, diff_cal)
            m_eval_base = _score_final_margins(final_norm, h_eval_base, diff_eval)

            batch_pad_consistency_err = abs(single_m0 - float(m_eval_base[0]))
            if batch_pad_consistency_err > 1e-3:
                raise RuntimeError(f"Left-padding consistency check failed: {batch_pad_consistency_err}")

            pred_fp32 = m_eval_base > 0.0
            fp32_eval_acc = float(np.mean(pred_fp32))
            print(
                f"[HNG.1] Baseline fp32_cal_acc={np.mean(m_cal_base > 0):.4f}, fp32_eval_acc={fp32_eval_acc:.4f}, pad_err={batch_pad_consistency_err:.2e}",
                flush=True,
            )

            raw_frob = {fam: math.sqrt(frob_sq[fam]) for fam in families}
            gamma_mod: dict[str, float] = {}
            fam_flip_rates: dict[str, float] = {}
            fam_mean_abs_shift: dict[str, float] = {}
            denom = np.maximum(np.abs(m_cal_base), 1e-4)

            for fam in families:
                m_plus = _score_final_margins(final_norm, h_cal_plus[fam], diff_cal)
                m_minus = _score_final_margins(final_norm, h_cal_minus[fam], diff_cal)
                dir_deriv = (m_plus - m_minus) / (2.0 * eps)
                gamma_mod[fam] = float(np.mean(np.abs(dir_deriv) / denom))

                m_q = _score_final_margins(final_norm, h_eval_fam[fam], diff_eval)
                fam_flip_rates[fam] = float(np.mean((m_q > 0.0) != pred_fp32))
                fam_mean_abs_shift[fam] = float(np.mean(np.abs(m_q - m_eval_base)))
                print(
                    f"[HNG.1] {fam}: gamma={gamma_mod[fam]:.4f}, shift={fam_mean_abs_shift[fam]:.4f}, flip={fam_flip_rates[fam]:.4f}",
                    flush=True,
                )

            gamma_ranked = sorted(families, key=lambda f: gamma_mod[f], reverse=True)
            raw_frob_ranked = sorted(families, key=lambda f: raw_frob[f], reverse=True)
            top2_gamma_fams = gamma_ranked[:2]
            bottom2_gamma_fams = gamma_ranked[-2:]

            # Pass 2: multi-family sweeps (top-2 protected, all int3, bottom-2 protected control)
            h_top2 = h0_eval.clone()
            h_all = h0_eval.clone()
            h_bot2 = h0_eval.clone()
            top2_set = set(top2_gamma_fams)
            bot2_set = set(bottom2_gamma_fams)

            for l_idx in range(cfg.num_hidden_layers):
                prefix = f"model.layers.{l_idx}."
                sd = {k[len(prefix) :]: sf.get_tensor(k).float() for k in sf.keys() if k.startswith(prefix)}
                layer.load_state_dict(sd, strict=True)
                clean_w = {fam: fam_mods[fam].weight.data.clone() for fam in families}
                qw_map = {fam: quantize_tensor_int3(clean_w[fam]) for fam in families}

                for fam in families:
                    fam_mods[fam].weight.data.copy_(clean_w[fam] if fam in top2_set else qw_map[fam])
                h_top2 = _step_layer(layer, h_top2, m4_eval, pid_eval, pe_eval)

                for fam in top2_set:
                    fam_mods[fam].weight.data.copy_(qw_map[fam])
                h_all = _step_layer(layer, h_all, m4_eval, pid_eval, pe_eval)

                for fam in families:
                    fam_mods[fam].weight.data.copy_(clean_w[fam] if fam in bot2_set else qw_map[fam])
                h_bot2 = _step_layer(layer, h_bot2, m4_eval, pid_eval, pe_eval)

                if l_idx in (0, 13, cfg.num_hidden_layers - 1):
                    print(f"[HNG.1] Pass 2 layer {l_idx + 1}/{cfg.num_hidden_layers} elapsed={time.time() - t0:.1f}s", flush=True)

            m_top2 = _score_final_margins(final_norm, h_top2, diff_eval)
            m_all = _score_final_margins(final_norm, h_all, diff_eval)
            m_bot2 = _score_final_margins(final_norm, h_bot2, diff_eval)

    top2_flip_rate = float(np.mean((m_top2 > 0.0) != pred_fp32))
    top2_acc = float(np.mean(m_top2 > 0.0))
    top2_mean_shift = float(np.mean(np.abs(m_top2 - m_eval_base)))

    all_flip_rate = float(np.mean((m_all > 0.0) != pred_fp32))
    all_acc = float(np.mean(m_all > 0.0))
    all_mean_shift = float(np.mean(np.abs(m_all - m_eval_base)))

    bot2_flip_rate = float(np.mean((m_bot2 > 0.0) != pred_fp32))
    bot2_acc = float(np.mean(m_bot2 > 0.0))
    bot2_mean_shift = float(np.mean(np.abs(m_bot2 - m_eval_base)))
    print(
        f"[HNG.1] sweeps: all_flip={all_flip_rate:.4f} (acc={all_acc:.4f}), "
        f"top2_flip={top2_flip_rate:.4f} (acc={top2_acc:.4f}, shift={top2_mean_shift:.4f}), "
        f"bot2_flip={bot2_flip_rate:.4f} (acc={bot2_acc:.4f}, shift={bot2_mean_shift:.4f})",
        flush=True,
    )

    rss = get_rss_mb()
    del layer, rotary, final_norm, tok
    gc.collect()

    g_vec = np.array([gamma_mod[f] for f in families], dtype=np.float64)
    f_vec = np.array([raw_frob[f] for f in families], dtype=np.float64)
    shift_vec = np.array([fam_mean_abs_shift[f] for f in families], dtype=np.float64)
    flip_vec = np.array([fam_flip_rates[f] for f in families], dtype=np.float64)

    rho_gamma_shift = safe_spearman(g_vec, shift_vec)
    rho_frob_shift = safe_spearman(f_vec, shift_vec)
    rho_gamma_flip = safe_spearman(g_vec, flip_vec)
    rho_frob_flip = safe_spearman(f_vec, flip_vec)
    reduction = float(all_flip_rate / max(top2_flip_rate, 1e-6))

    checks = {
        "fp32_eval_acc_ge_min": fp32_eval_acc >= float(p["fp32_eval_acc_min"]),
        "all_int3_flip_rate_ge_min": all_flip_rate >= float(p["all_int3_flip_rate_min"]),
        "spearman_gamma_vs_margin_shift_ge_min": (
            rho_gamma_shift is not None and rho_gamma_shift >= float(p["spearman_gamma_vs_margin_shift_min"])
        ),
        "protection_flip_reduction_ge_min": reduction >= float(p["protection_flip_reduction_min"]),
        "top2_less_shift_than_bottom2": top2_mean_shift < bot2_mean_shift,
    }
    status = "HELD" if all(checks.values()) else "BROKEN"

    return {
        "hypothesis": "HNG.1",
        "status": status,
        "checks": checks,
        "model_id": QWEN_ID,
        "param_count": param_count,
        "num_cal": len(cal_pairs),
        "num_eval": len(eval_pairs),
        "batch_pad_consistency_err": batch_pad_consistency_err,
        "fp32_cal_acc": float(np.mean(m_cal_base > 0.0)),
        "fp32_eval_acc": fp32_eval_acc,
        "gamma_mod": gamma_mod,
        "gamma_ranked": gamma_ranked,
        "raw_frob": raw_frob,
        "raw_frob_ranked": raw_frob_ranked,
        "per_family_int3_flip_rate": fam_flip_rates,
        "per_family_int3_mean_abs_margin_shift": fam_mean_abs_shift,
        "top2_protected_families": top2_gamma_fams,
        "bottom2_protected_families": bottom2_gamma_fams,
        "top2_protected_flip_rate": top2_flip_rate,
        "top2_protected_acc": top2_acc,
        "top2_protected_mean_margin_shift": top2_mean_shift,
        "bottom2_protected_flip_rate": bot2_flip_rate,
        "bottom2_protected_acc": bot2_acc,
        "bottom2_protected_mean_margin_shift": bot2_mean_shift,
        "all_int3_flip_rate": all_flip_rate,
        "all_int3_acc": all_acc,
        "all_int3_mean_margin_shift": all_mean_shift,
        "protection_flip_reduction": reduction,
        "spearman_gamma_vs_margin_shift": rho_gamma_shift,
        "spearman_frob_vs_margin_shift": rho_frob_shift,
        "spearman_gamma_vs_flip": rho_gamma_flip,
        "spearman_frob_vs_flip": rho_frob_flip,
        "rss_mb": rss,
        "runtime_sec": round(time.time() - t0, 2),
    }


def beta_pdf(y: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Vectorized exact Beta(a, b) density on open grid (0, 1)."""
    log_norm = gammaln(a + b) - gammaln(a) - gammaln(b)
    return np.exp(log_norm + (a - 1.0) * np.log(y) + (b - 1.0) * np.log(1.0 - y))


def continuous_beta_mixture_params_k1(x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    sig = 1.0 / (1.0 + np.exp(-3.0 * (x - 0.5)))
    w = 0.35 + 0.30 * sig
    a1 = 3.0 + 1.5 * np.sin(math.pi * x) ** 2
    b1 = 6.0 - 1.5 * np.sin(math.pi * x)
    a2 = 6.0 - 1.5 * np.cos(math.pi * x)
    b2 = 3.0 + 1.5 * np.sin(2.0 * math.pi * x)
    return w, a1, b1, a2, b2


def continuous_beta_mixture_params_k2(x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    w = 0.5 + 0.25 * np.cos(2.0 * math.pi * x)
    a1 = 2.5 + 1.2 * np.cos(math.pi * x) ** 2
    b1 = 5.0 + 1.0 * np.sin(math.pi * x)
    a2 = 5.5 - 1.2 * np.sin(math.pi * x)
    b2 = 2.5 + 1.2 * np.cos(math.pi * x) ** 2
    return w, a1, b1, a2, b2


def build_continuous_kernel_matrix(grid: np.ndarray, param_fn) -> np.ndarray:
    w, a1, b1, a2, b2 = param_fn(grid[:, None])
    y = grid[None, :]
    dens = w * beta_pdf(y, a1, b1) + (1.0 - w) * beta_pdf(y, a2, b2)
    P = dens / dens.sum(axis=1, keepdims=True)
    return P


def kernel_dobrushin_coeff(P: np.ndarray) -> float:
    m = P.shape[0]
    c_max = 0.0
    for i in range(m):
        diffs = 0.5 * np.abs(P - P[i : i + 1, :]).sum(axis=1)
        c_max = max(c_max, float(diffs.max()))
    return c_max


def sample_next_continuous(rng: np.random.Generator, states: np.ndarray, eps_mix: float = 0.0) -> np.ndarray:
    """Exact rejection-free continuous sampler on (0, 1) without grid discretization."""
    n = len(states)
    is_pert = rng.random(n) < eps_mix
    u_pert = rng.uniform(1e-6, 1.0 - 1e-6, size=n)
    w, a1, b1, a2, b2 = continuous_beta_mixture_params_k1(states)
    use_first = rng.random(n) < w
    a = np.where(use_first, a1, a2)
    b = np.where(use_first, b1, b2)
    out = np.clip(rng.beta(a, b), 1e-6, 1.0 - 1e-6)
    return np.where(is_pert, u_pert, out)


def run_hng2_measurable_dobrushin(preds: dict) -> dict:
    """HNG.2: Continuous [0,1] nonlinear bimodal Beta-mixture kernel contraction, comp & MC verification."""
    t0 = time.time()
    p = preds["HNG.2"]
    M = int(p["grid_bins"])
    num_pairs = int(p["num_initial_pairs"])
    H = int(p["horizon"])
    N_mc = int(p["mc_samples"])
    rng = np.random.default_rng(SEED + 20)

    grid = (np.arange(M, dtype=np.float64) + 0.5) / M
    K1 = build_continuous_kernel_matrix(grid, continuous_beta_mixture_params_k1)
    K2 = build_continuous_kernel_matrix(grid, continuous_beta_mixture_params_k2)
    eps_mix = 0.04
    U = np.full((M, M), 1.0 / M, dtype=np.float64)
    K1_pert = (1.0 - eps_mix) * K1 + eps_mix * U

    c1 = kernel_dobrushin_coeff(K1)
    c2 = kernel_dobrushin_coeff(K2)
    c_comp = kernel_dobrushin_coeff(K1 @ K2)
    eps_pert = float(np.max(0.5 * np.abs(K1 - K1_pert).sum(axis=1)))

    max_contraction_violation = 0.0
    max_horizon_violation = 0.0
    t15_ratios: list[float] = []

    for _ in range(num_pairs):
        w_mu = np.exp(rng.normal(0.0, 1.2, size=M))
        w_nu = np.exp(rng.normal(0.0, 1.2, size=M))
        mu = w_mu / w_mu.sum()
        nu = w_nu / w_nu.sum()

        d0 = 0.5 * float(np.abs(mu - nu).sum())
        d1 = 0.5 * float(np.abs(mu @ K1 - nu @ K1).sum())
        max_contraction_violation = max(max_contraction_violation, d1 - c1 * d0)

        m_t = mu.copy()
        n_t = nu.copy()
        for t in range(1, H + 1):
            m_t = m_t @ K1
            n_t = n_t @ K1_pert
            dt = 0.5 * float(np.abs(m_t - n_t).sum())
            bound = (c1**t) * d0 + eps_pert * (1.0 - c1**t) / (1.0 - c1)
            max_horizon_violation = max(max_horizon_violation, dt - bound)
            if t == H:
                lin = max(d0 + t * eps_pert, 1e-12)
                t15_ratios.append(dt / lin)

    comp_violation = max(0.0, c_comp - c1 * c2)

    # Independent continuous Monte Carlo cross-check (T = 1..5, two separated Beta priors)
    coarse_bins = 25
    s_mu = np.clip(rng.beta(2.0, 6.0, size=N_mc), 1e-6, 1.0 - 1e-6)
    s_nu = np.clip(rng.beta(6.0, 2.0, size=N_mc), 1e-6, 1.0 - 1e-6)
    mu_g = beta_pdf(grid, np.full(M, 2.0), np.full(M, 6.0))
    mu_g /= mu_g.sum()
    nu_g = beta_pdf(grid, np.full(M, 6.0), np.full(M, 2.0))
    nu_g /= nu_g.sum()
    mc_errs: list[float] = []
    for _ in range(5):
        s_mu = sample_next_continuous(rng, s_mu, eps_mix=0.0)
        s_nu = sample_next_continuous(rng, s_nu, eps_mix=eps_mix)
        mu_g = mu_g @ K1
        nu_g = nu_g @ K1_pert
        h_mu, _ = np.histogram(s_mu, bins=coarse_bins, range=(0.0, 1.0))
        h_nu, _ = np.histogram(s_nu, bins=coarse_bins, range=(0.0, 1.0))
        tv_mc = 0.5 * float(np.abs(h_mu / N_mc - h_nu / N_mc).sum())
        c_mu = mu_g.reshape(coarse_bins, M // coarse_bins).sum(axis=1)
        c_nu = nu_g.reshape(coarse_bins, M // coarse_bins).sum(axis=1)
        tv_grid = 0.5 * float(np.abs(c_mu - c_nu).sum())
        mc_errs.append(abs(tv_mc - tv_grid))

    mc_tv_max_abs_err = max(mc_errs)
    max_t15_vs_linear_ratio = max(t15_ratios)

    checks = {
        "max_contraction_violation_le": max_contraction_violation <= float(p["max_contraction_violation_le"]),
        "max_comp_violation_le": comp_violation <= float(p["max_comp_violation_le"]),
        "max_horizon_violation_le": max_horizon_violation <= float(p["max_horizon_violation_le"]),
        "max_t15_vs_linear_ratio_le": max_t15_vs_linear_ratio <= float(p["max_t15_vs_linear_ratio_le"]),
        "mc_tv_max_abs_err_le": mc_tv_max_abs_err <= float(p["mc_tv_max_abs_err_le"]),
    }

    return {
        "hypothesis": "HNG.2",
        "status": "HELD" if all(checks.values()) else "BROKEN",
        "checks": checks,
        "grid_bins": M,
        "c1": c1,
        "c2": c2,
        "c_comp": c_comp,
        "c1_times_c2": c1 * c2,
        "eps_pert": eps_pert,
        "max_contraction_violation": max_contraction_violation,
        "max_comp_violation": comp_violation,
        "max_horizon_violation": max_horizon_violation,
        "max_t15_vs_linear_ratio": max_t15_vs_linear_ratio,
        "mc_tv_max_abs_err": mc_tv_max_abs_err,
        "runtime_sec": round(time.time() - t0, 3),
    }


def run_hng3_cech_nerve_and_pou(preds: dict) -> dict:
    """HNG.3: Cech nerve descent, partition-of-unity overlap exactness, non-surjectivity & C4."""
    t0 = time.time()
    p = preds["HNG.3"]

    # Cover p: {0, 1, 2} -> {0, 1}, p(0)=0, p(1)=0, p(2)=1, split section s(0)=0, s(1)=2
    proj = {0: 0, 1: 0, 2: 1}
    sec = {0: 0, 1: 2}
    # Cech1 = {(u, v) : p(u) == p(v)}, Cech2 = {(u, v, w) : p(u)==p(v)==p(w)}
    cech1 = [(u, v) for u in range(3) for v in range(3) if proj[u] == proj[v]]
    cech2 = [(u, v, w) for u in range(3) for v in range(3) for w in range(3) if proj[u] == proj[v] == proj[w]]

    # Fiber family F(0) = Z/4Z, F(1) = Z/2Z encoded in float phases on S^1 / group elements
    # Non-trivial cocycle gauge along split descent from F
    tau = {0: 1.0, 1: -1.0, 2: 1.0}  # trivialization gauges over u in U
    cocycle = {(u, v): tau[u] * (1.0 / tau[v]) for u, v in cech1}
    cocycle_err = max(abs(cocycle[(u, v)] * cocycle[(v, w)] - cocycle[(u, w)]) for u, v, w in cech2)

    # Effective descent reconstruction over arbitrary sections f : {0, 1} -> R
    test_globals = [{0: 1.25, 1: -3.5}, {0: 0.0, 1: 7.0}, {0: 2.0, 1: 2.0}]
    split_exact = True
    for g in test_globals:
        local = {u: tau[u] * g[proj[u]] for u in range(3)}
        # Compatibility across Cech1:
        for u, v in cech1:
            if abs(cocycle[(u, v)] * local[v] - local[u]) > 1e-12:
                split_exact = False
        reconstructed = {x: (1.0 / tau[sec[x]]) * local[sec[x]] for x in range(2)}
        if max(abs(reconstructed[x] - g[x]) for x in range(2)) > 1e-12:
            split_exact = False

    # Scalar mass on X={0,1}: true mass(0)=1.0, mass(1)=2.5 => total=3.5
    true_mass = {0: 1.0, 1: 2.5}
    true_total = sum(true_mass.values())
    patch_mass = {u: true_mass[proj[u]] for u in range(3)}
    pou_weights = {0: 0.4, 1: 0.6, 2: 1.0}  # sum_{p(u)=x} pou[u] = 1
    pou_total = sum(pou_weights[u] * patch_mass[u] for u in range(3))
    raw_total = sum(patch_mass[u] for u in range(3))
    pou_abs_err = abs(pou_total - true_total)
    raw_overlap_err = abs(raw_total - true_total)

    # Non-surjective subcover U' = {0} misses fiber at x=1
    covered_base = {proj[u] for u in (0,)}
    missing_fibers = len(set(true_mass.keys()) - covered_base)

    # C4 -> C2 Specker triangle under coset-0 anchor vs coset-1 anchor
    def sol_count(allowed: dict[int, tuple[int, ...]]) -> tuple[int, int]:
        edge_sols = [
            sum(1 for a in allowed[u] for b in allowed[v] if a != b)
            for u, v in ((0, 1), (1, 2), (2, 0))
        ]
        glob = sum(
            1
            for a in allowed[0]
            for b in allowed[1]
            for c in allowed[2]
            if a != b and b != c and c != a
        )
        return min(edge_sols), glob

    _, c4_global = sol_count({0: (0, 2), 1: (0, 2), 2: (0, 2)})
    edge_pairs = [(a, b) for a in (0, 2) for b in (0, 2) if a != b]
    coset0_monodromies = [
        ((b01 - a01) + (b12 - a12) + (b20 - a20)) % 4
        for (a01, b01), (a12, b12), (a20, b20) in itertools.product(edge_pairs, repeat=3)
    ]
    c4_min_monodromy = min(m for m in coset0_monodromies if m != 0)

    checks = {
        "cocycle_max_err_eq": cocycle_err == float(p["cocycle_max_err_eq"]),
        "split_descent_exact": split_exact is bool(p["split_descent_exact"]),
        "pou_abs_err_le": pou_abs_err <= float(p["pou_abs_err_le"]),
        "raw_overlap_err_ge": raw_overlap_err >= float(p["raw_overlap_err_ge"]),
        "non_surjective_missing_fibers_ge": missing_fibers >= int(p["non_surjective_missing_fibers_ge"]),
        "c4_global_solutions_eq": c4_global == int(p["c4_global_solutions_eq"]),
        "c4_min_monodromy_eq": c4_min_monodromy == int(p["c4_min_monodromy_eq"]),
    }

    return {
        "hypothesis": "HNG.3",
        "status": "HELD" if all(checks.values()) else "BROKEN",
        "checks": checks,
        "cocycle_max_err": cocycle_err,
        "split_descent_exact": split_exact,
        "true_total": true_total,
        "pou_total": pou_total,
        "raw_total": raw_total,
        "pou_abs_err": pou_abs_err,
        "raw_overlap_err": raw_overlap_err,
        "non_surjective_missing_fibers": missing_fibers,
        "c4_global_solutions": c4_global,
        "c4_min_monodromy": c4_min_monodromy,
        "runtime_sec": round(time.time() - t0, 4),
    }


def cyclic_bispectrum(x: np.ndarray) -> np.ndarray:
    """Exact 2D cyclic C_n bispectrum B[k1, k2] = X[k1] X[k2] conj(X[(k1+k2) mod n])."""
    n = x.shape[-1]
    X = np.fft.fft(x, axis=-1)
    idx = (np.arange(n)[:, None] + np.arange(n)[None, :]) % n
    return X[..., :, None] * X[..., None, :] * np.conj(X[..., idx])


def run_hng4_bispectrum_symmetrization(preds: dict) -> dict:
    """HNG.4: Exact C_16 / D_16 bispectrum orbit completeness and test-time symmetrization."""
    t0 = time.time()
    p = preds["HNG.4"]
    n = int(p["group_order"])
    rng = np.random.default_rng(SEED + 40)

    # 1) Orbit invariance across C_16 shifts and D_16 (Re(B), |B|) reflections
    x0 = rng.normal(0.0, 1.0, size=n)
    B0 = cyclic_bispectrum(x0)
    orbit_errs: list[float] = []
    for s in range(n):
        xs = np.roll(x0, s)
        Bs = cyclic_bispectrum(xs)
        orbit_errs.append(float(np.max(np.abs(Bs - B0))))
        x_rev = xs[::-1]
        Brev = cyclic_bispectrum(x_rev)
        orbit_errs.append(float(np.max(np.abs(np.real(Brev) - np.real(B0)))))
        orbit_errs.append(float(np.max(np.abs(np.abs(Brev) - np.abs(B0)))))
    max_orbit_invariance_err = max(orbit_errs)

    # 2) Same power spectrum, distinct phase coupling separated by bispectrum (triad k1=1, k2=2, k3=3)
    t_grid = 2.0 * math.pi * np.arange(n) / n
    sig_plus = np.cos(t_grid) + np.cos(2.0 * t_grid) + np.cos(3.0 * t_grid + 0.0)
    sig_minus = np.cos(t_grid) + np.cos(2.0 * t_grid) + np.cos(3.0 * t_grid + math.pi / 2.0)
    ps_plus = np.abs(np.fft.fft(sig_plus)) ** 2
    ps_minus = np.abs(np.fft.fft(sig_minus)) ** 2
    power_spectrum_matched_diff = float(np.max(np.abs(ps_plus - ps_minus)))
    min_phase_matched_bispectrum_sep = float(
        np.linalg.norm(cyclic_bispectrum(sig_plus) - cyclic_bispectrum(sig_minus))
    )

    # 3) Test-time symmetrization variance elimination & MSE reduction
    # Ground-truth C_16-invariant target y*(x) = sum_i (x_i * x_{i+1})^2 + 0.25 * (sum_i x_i)^2
    def target_fn(X: np.ndarray) -> np.ndarray:
        return ((X * np.roll(X, -1, axis=1)) ** 2).sum(axis=1) + 0.25 * (X.sum(axis=1) ** 2)

    n_train = 80
    X_train = rng.normal(0.0, 1.0, size=(n_train, n))
    y_train = target_fn(X_train) + rng.normal(0.0, 2.0, size=n_train)
    # Non-equivariant finite-sample OLS over 49 position-specific quadratic/linear features
    asym_mask = np.linspace(0.5, 2.0, n)

    def asym_features(X: np.ndarray) -> np.ndarray:
        quad_pair = (X * np.roll(X, -1, axis=1)) ** 2 * asym_mask[None, :]
        sq = (X ** 2) * asym_mask[None, :]
        bias = np.ones((X.shape[0], 1))
        return np.hstack([quad_pair, sq, X, bias])

    Phi_tr = asym_features(X_train)
    w_hat, *_ = np.linalg.lstsq(Phi_tr, y_train, rcond=None)

    X_test = rng.normal(0.0, 1.0, size=(200, n))
    y_test = target_fn(X_test)
    pred_raw = asym_features(X_test) @ w_hat
    pred_orbit = np.stack([asym_features(np.roll(X_test, s, axis=1)) @ w_hat for s in range(n)], axis=0)
    pred_sym = pred_orbit.mean(axis=0)

    sym_orbit_vars = []
    for x_single in X_test[:25]:
        syms = [float(np.mean([asym_features(np.roll(np.roll(x_single, g)[None, :], s, axis=1)) @ w_hat for s in range(n)])) for g in range(n)]
        sym_orbit_vars.append(float(np.var(syms)))
    sym_orbit_variance_max = max(sym_orbit_vars)

    mse_raw = float(np.mean((pred_raw - y_test) ** 2))
    mse_sym = float(np.mean((pred_sym - y_test) ** 2))
    sym_mse_ratio = mse_sym / max(mse_raw, 1e-12)

    checks = {
        "max_orbit_invariance_err_le": max_orbit_invariance_err <= float(p["max_orbit_invariance_err_le"]),
        "power_spectrum_matched_diff_le": power_spectrum_matched_diff <= float(p["power_spectrum_matched_diff_le"]),
        "min_phase_matched_bispectrum_sep_ge": min_phase_matched_bispectrum_sep >= float(p["min_phase_matched_bispectrum_sep_ge"]),
        "sym_orbit_variance_max_le": sym_orbit_variance_max <= float(p["sym_orbit_variance_max_le"]),
        "sym_mse_ratio_le": sym_mse_ratio <= float(p["sym_mse_ratio_le"]),
    }

    return {
        "hypothesis": "HNG.4",
        "status": "HELD" if all(checks.values()) else "BROKEN",
        "checks": checks,
        "group_order": n,
        "max_orbit_invariance_err": max_orbit_invariance_err,
        "power_spectrum_matched_diff": power_spectrum_matched_diff,
        "min_phase_matched_bispectrum_sep": min_phase_matched_bispectrum_sep,
        "sym_orbit_variance_max": sym_orbit_variance_max,
        "mse_raw": mse_raw,
        "mse_sym": mse_sym,
        "sym_mse_ratio": sym_mse_ratio,
        "runtime_sec": round(time.time() - t0, 4),
    }


def main() -> None:
    t_all = time.time()
    preds = json.loads(PRED_PATH.read_text(encoding="utf-8"))
    h1 = run_hng1_qwen_scaleup(preds)
    h2 = run_hng2_measurable_dobrushin(preds)
    h3 = run_hng3_cech_nerve_and_pou(preds)
    h4 = run_hng4_bispectrum_symmetrization(preds)

    results = {
        "suite": "master_principle_nitty_gritties",
        "seed": SEED,
        "total_runtime_sec": round(time.time() - t_all, 2),
        "hypotheses": {
            "HNG.1": h1,
            "HNG.2": h2,
            "HNG.3": h3,
            "HNG.4": h4,
        },
        "held_count": sum(1 for h in (h1, h2, h3, h4) if h["status"] == "HELD"),
        "total_count": 4,
    }
    OUT_PATH.write_text(json.dumps(results, indent=2, allow_nan=False), encoding="utf-8")
    print(f"COMPLETED held={results['held_count']}/4 total_sec={results['total_runtime_sec']}")


if __name__ == "__main__":
    main()
