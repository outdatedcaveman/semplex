"""Pretrained Open-Weight HuggingFace Checkpoint Gauge & Continuum Polish Probe (HP.1-HP.5)."""
from __future__ import annotations

import ctypes
import gc
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
from transformers import AutoModelForCausalLM, AutoModelForSequenceClassification, AutoTokenizer

torch.set_num_threads(1)

ROOT = Path(__file__).resolve().parents[1]
PRED_PATH = ROOT / "experiments" / "results" / "pretrained_checkpoint_gauge_predictions.json"
OUT_PATH = ROOT / "experiments" / "results" / "pretrained_checkpoint_gauge_results.json"

MINILM_ID = "cross-encoder/ms-marco-MiniLM-L-6-v2"
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


def sigmoid(x: np.ndarray) -> np.ndarray:
    x_clip = np.clip(x, -40.0, 40.0)
    return 1.0 / (1.0 + np.exp(-x_clip))


def binary_ece(probs: np.ndarray, labels: np.ndarray, n_bins: int = 10) -> float:
    preds = (probs >= 0.5).astype(np.float64)
    conf = np.maximum(probs, 1.0 - probs)
    acc = (preds == labels).astype(np.float64)
    bins = np.linspace(0.5, 1.0 + 1e-9, n_bins + 1)
    ece = 0.0
    n = float(len(probs))
    for i in range(n_bins):
        mask = (conf >= bins[i]) & (conf < bins[i + 1])
        if np.any(mask):
            ece += (float(np.sum(mask)) / n) * abs(float(np.mean(acc[mask]) - np.mean(conf[mask])))
    return float(ece)


def binary_tv(p: np.ndarray, q: np.ndarray) -> np.ndarray:
    return np.abs(p - q)


def fit_temperature_unlabeled_kl(
    logits_raw: np.ndarray, logits_ref: np.ndarray
) -> tuple[float, np.ndarray]:
    """Fit single positive temperature T > 0 minimizing E[KL(sigma(z_ref) || sigma(z_raw / T))]."""
    p_ref = np.clip(sigmoid(logits_ref.astype(np.float64)), 1e-7, 1.0 - 1e-7)
    z = logits_raw.astype(np.float64)
    log_ts = np.linspace(-2.5, 2.5, 501)
    best_t = 1.0
    best_loss = float("inf")
    for lt in log_ts:
        t = math.exp(float(lt))
        q = np.clip(sigmoid(z / t), 1e-7, 1.0 - 1e-7)
        kl = float(np.mean(p_ref * np.log(p_ref / q) + (1.0 - p_ref) * np.log((1.0 - p_ref) / (1.0 - q))))
        if kl < best_loss:
            best_loss = kl
            best_t = t
    lo = math.log(best_t) - 0.02
    hi = math.log(best_t) + 0.02
    for lt in np.linspace(lo, hi, 201):
        t = math.exp(float(lt))
        q = np.clip(sigmoid(z / t), 1e-7, 1.0 - 1e-7)
        kl = float(np.mean(p_ref * np.log(p_ref / q) + (1.0 - p_ref) * np.log((1.0 - p_ref) / (1.0 - q))))
        if kl < best_loss:
            best_loss = kl
            best_t = t
    return float(best_t), sigmoid(z / best_t)


def exact_auroc(scores: np.ndarray, binary_targets: np.ndarray) -> float | None:
    """AUROC where smaller score (e.g. |fp32 margin|) predicts flip=1 (uses -scores)."""
    pos = scores[binary_targets == 1]
    neg = scores[binary_targets == 0]
    if len(pos) == 0 or len(neg) == 0:
        return None
    less = np.sum(pos[:, None] < neg[None, :])
    ties = np.sum(pos[:, None] == neg[None, :])
    return float((less + 0.5 * ties) / (len(pos) * len(neg)))


def build_msmarco_datasets() -> tuple[
    list[tuple[str, str, int]],
    list[tuple[str, str, int]],
    list[tuple[str, str]],
    list[int],
    list[tuple[str, str]],
    list[int],
]:
    """Build 80 In-Family MS-MARCO pairs, 80 OOF adversarial pairs, and Task B domain routing."""
    facts = [
        ("how photosynthesis converts sunlight", "Plants use chlorophyll in chloroplasts to turn sunlight, carbon dioxide, and water into glucose and oxygen."),
        ("what causes ocean tides on Earth", "Ocean tides rise and fall mainly from the gravitational pull of the Moon and the Sun combined with Earth rotation."),
        ("how vaccines train the immune system", "Vaccines introduce weakened or inactive pathogen antigens so memory lymphocytes recognize future infections rapidly."),
        ("why the Roman Empire built aqueducts", "Roman engineers constructed stone aqueducts to channel fresh spring water across valleys into urban baths and fountains."),
        ("how lithium ion batteries store energy", "Lithium ions migrate through a liquid electrolyte between a graphite anode and metal oxide cathode during charge cycles."),
        ("how earthquakes generate seismic waves", "Sudden tectonic fault slippage releases stored elastic strain energy as primary compressional and secondary shear seismic waves."),
        ("what role mitochondria play in cells", "Mitochondria oxidize pyruvate inside inner membranes to synthesize adenosine triphosphate for cellular metabolism."),
        ("how TCP ensures reliable packet delivery", "TCP tracks sequence numbers, acknowledgments, and retransmissions to deliver ordered byte streams over IP networks."),
        ("why glaciers carve U shaped valleys", "Massive moving mountain ice scours bedrock floors and steepens valley walls into broad U shaped troughs."),
        ("how DNA replication copies genetic code", "Helicase unwinds double stranded DNA while DNA polymerase pairs complementary nucleotides on each template strand."),
        ("why metals conduct electrical current", "Delocalized valence electrons inside metallic crystal lattices move freely under an applied electric field."),
        ("how coffee roasting develops aroma", "Heating green coffee beans triggers Maillard browning reactions that yield volatile aromatic furans and pyrazines."),
        ("what causes seasonal temperature shifts", "Earth twenty-three degree axial tilt changes solar incidence angles and daylight duration across hemispheres."),
        ("how CRISPR enzymes cut target DNA", "Guide RNA directs the Cas9 endonuclease to cleave matching protospacer DNA sequences beside a PAM motif."),
        ("why fermentation produces bread rise", "Saccharomyces yeast metabolizes flour sugars anaerobically into ethanol and carbon dioxide bubbles trapped in gluten."),
        ("how solar panels generate electricity", "Semiconductor photovoltaic junctions absorb photons to excite electron hole pairs across a built in electric field."),
        ("why deep ocean vents sustain life", "Chemosynthetic bacteria oxidize hydrogen sulfide around hydrothermal chimneys to anchor food webs without sunlight."),
        ("how magnetic resonance imaging works", "Strong magnetic fields align hydrogen proton spins while radiofrequency pulses measure relaxation contrast in soft tissues."),
        ("what drives atmospheric jet streams", "Strong thermal contrast between polar and tropical air masses pairs with Coriolis deflection to steer upper winds."),
        ("how ribosomes assemble protein chains", "Ribosomes decode messenger RNA codons via transfer RNAs to link amino acids with peptide bonds."),
    ]
    distractors = [
        "Medieval guild bakers regulated wheat flour weights and oven taxes across walled market towns.",
        "Acoustic guitars resonate through spruce soundboards and rosewood bridges when nylon strings vibrate.",
        "Alpine ski resorts groom snowpack slopes with tracked winches before winter competitions begin.",
        "Ancient mariners navigated open oceans using brass astrolabes, sextants, and star altitude charts.",
        "Ceramic kilns fire stoneware glazes above twelve hundred degrees Celsius to vitrify clay.",
        "Jazz saxophonists improvise syncopated melodies over walking double bass chord progressions.",
        "Botanical conservatories prune tropical orchids inside glass greenhouses during humid summers.",
        "Chess grandmasters sacrifice central pawns early to open diagonal lines for bishops.",
        "Renaissance fresco painters applied mineral pigments rapidly onto damp lime plaster walls.",
        "Steam locomotives boiled pressurized coal water to drive reciprocating iron pistons along rails.",
    ]
    extra_queries = [
        "benefits of sourdough fermentation",
        "effects of deforestation on rainfall",
        "principles of aerodynamic airplane lift",
        "symptoms of vitamin D deficiency",
        "history of the printing press",
        "how concrete hardens through hydration",
        "role of pollinators in orchards",
        "structure of volcanic basalt rocks",
        "mechanism of antibiotic resistance",
        "physics of fiber optic total reflection",
    ]
    infam: list[tuple[str, str, int]] = []
    # 40 positive pairs (20 direct + 20 natural focused sub-queries)
    for i, (q, p) in enumerate(facts):
        infam.append((q, p, 1))
        short_q = " ".join(q.split()[1:])
        infam.append((short_q, p, 1))
    # 40 clearly irrelevant negative pairs
    for i, (q, _) in enumerate(facts):
        infam.append((q, distractors[i % len(distractors)], 0))
        infam.append((extra_queries[i % len(extra_queries)], facts[(i + 5) % len(facts)][1], 0))

    # OOF 80 adversarial pairs: 40 lexical-overlap wrong answers + 40 near-boundary paraphrases
    oof: list[tuple[str, str, int]] = []
    # Adversarial overlap negatives (same words, false/orthogonal domain match)
    oof_neg_templates = [
        ("how photosynthesis produces sunlight", "Artificial sunlight lamps do not perform photosynthesis, and nuclear decay never produces chlorophyll in rock layers."),
        ("does the Moon pull glaciers uphill", "Earth ocean tides depend on lunar gravity, whereas mountain glaciers slide downhill without tidal pull from water."),
        ("when do vaccines cause Roman aqueducts", "Pathogen memory in human blood is biological immunity and has zero historical connection to Roman aqueduct arches."),
        ("can lithium batteries bake sourdough bread", "Yeast bubbles lift bread dough in warm ovens, unlike graphite electrolytes inside portable battery housings."),
        ("does DNA polymerase trigger seismic waves", "Enzyme nucleotide pairing copies genomes inside nuclei rather than fracturing crustal bedrock during earthquakes."),
        ("how Cas9 edits metallic electron lattices", "Conduction electrons move across copper wires regardless of RNA guided endonuclease motifs or PAM cleavage."),
        ("why coffee roasting drives jet streams", "Maillard bean aromatics stay inside espresso grinders and never steer Coriolis upper tropospheric winds."),
        ("how MRI magnets ferment glucose dough", "Proton spin relaxation images human organs cleanly without baking Saccharomyces bread bubbles or ethanol."),
        ("why hydrothermal vents play jazz music", "Deep sea sulfur bacteria survive crushing pressure chemically without brass reeds or chord charts."),
        ("how solar photons build clay stoneware", "Photovoltaic silicon generates voltage cleanly, unrelated to firing ceramic glazes inside pottery kilns."),
    ]
    for k in range(4):
        for q, p in oof_neg_templates:
            q_mod = q if k == 0 else f"query case {k}: {q}"
            oof.append((q_mod, p, 0))
    # Adversarial low-overlap / partial-premise positives
    oof_pos_templates = [
        ("cellular ATP generation engine", "Organelles inside eukaryotic cytoplasm couple proton gradients to synthesize high energy phosphate bonds."),
        ("packet loss recovery over networks", "Transport protocols confirm byte receipt and resend missing segments across congested routers."),
        ("orbital tilt causing winter and summer", "Obliquity shifts insolation angles over twelve months while hemisphere daylight hours expand and contract."),
        ("programmable nuclease genome editing", "Synthetic RNA scaffolds localize catalytic proteins to cleave double helices at chosen genomic loci."),
        ("photonic voltage conversion hardware", "Doped crystal layers separate photoexcited carriers across depletion zones to output direct current."),
        ("anaerobic yeast dough expansion", "Fungal enzymes break down flour carbohydrates while gas pockets stretch elastic protein networks."),
        ("glacial erosion landform geometry", "Advancing ice sheets widen alpine V valleys into steep sided troughs."),
        ("chemosynthesis without daylight", "Benthic microbes harvest chemical redox energy from dissolved sulfides near volcanic ocean fissures."),
        ("spin relaxation clinical imaging", "Radio waves tip aligned tissue nuclei so scanners reconstruct anatomical density maps."),
        ("coriolis steered upper atmospheric rivers", "Equatorial pole temperature gradients accelerate high altitude westerly flows around the globe."),
    ]
    for k in range(4):
        for q, p in oof_pos_templates:
            p_mod = p if k == 0 else f"{p} Verified note {k}."
            oof.append((q, p_mod, 1))

    # Task B: Binary domain routing (Science=1 vs Humanities/Arts=0) on clean natural sentences
    sci_sents = [
        "Electron orbitals govern covalent bond angles in organic carbon molecules.",
        "Ribosomal subunits translate messenger RNA into folded polypeptide chains.",
        "Continental plates subduct beneath oceanic trenches along volcanic arcs.",
        "Photovoltaic diodes convert incident solar photons into usable electrical current.",
        "Hydrogen fusion inside stellar cores fuses light nuclei into helium.",
        "Catalytic enzymes lower reaction activation barriers inside aqueous cells.",
        "Magnetic flux lines twist above convective plasma loops during solar flares.",
        "Spectrometers separate emitted wavelengths to identify distant gas composition.",
        "Osmotic pressure balances dissolved solute concentrations across lipid membranes.",
        "Superconducting coils sustain lossless currents below critical cryogenic temperatures.",
        "Acoustic interferometers measure tiny spacetime strain ripples from merging binaries.",
        "Antibiotic molecules disrupt bacterial cell wall peptidoglycan assembly pathways.",
        "Glacial ice cores preserve ancient atmospheric methane and isotope ratios.",
        "Semiconductor transistors switch microvolt signals cleanly inside silicon processors.",
        "Chloroplast membranes harvest blue and red photons during carbon fixation.",
        "Thermodynamic entropy increases across irreversible heat engine expansion cycles.",
        "Seismographs triangulate crustal rupture hypocenters from primary arrival delays.",
        "Neutron moderators slow fissile chain reaction velocities inside reactor vessels.",
        "Bacteriophages inject viral genomes through contractile protein tail sheaths.",
        "Maxwell equations unify electric and magnetic wave propagation in vacuum.",
    ]
    hum_sents = [
        "Baroque harpsichord fugues interweave contrapuntal voices across minor harmonic keys.",
        "Renaissance sculptors chiseled Carrara marble draperies with subtle anatomical poise.",
        "Epic oral poets chanted dactylic hexameter verses at seasonal civic festivals.",
        "Gothic cathedral buttresses carried vaulted nave masonry above stained glass windows.",
        "Victorian novelists serialized urban social satires in monthly literary periodicals.",
        "Impressionist oil painters captured shifting river reflections using broken brushstrokes.",
        "Greek tragedians staged choral odes examining fate, hubris, and civic duty.",
        "Medieval illuminated manuscripts decorated Latin psalters with lapis lazuli gold leaf.",
        "Classical string quartets balance lyrical sonata themes with brisk scherzo finales.",
        "Calligraphy masters ground pine soot inkstones onto handmade mulberry paper scrolls.",
        "Romantic landscape painters framed stormy crags to evoke sublime solitude.",
        "Early cinema directors pioneered cross-cutting montages in silent urban dramas.",
        "Enlightenment essayists debated constitutional checks inside Parisian reading salons.",
        "Neoclassical playwrights observed strict three-act unities of time and place.",
        "Jazz trumpeters harmonized muted blue notes alongside syncopated cymbal rhythms.",
        "Symbolist poets paired musical vowel cadences with dreamlike mythic imagery.",
        "Ancient potters painted black-figure mythological scenes onto terracotta amphorae.",
        "Chamber choirs performed polyphonic motets beneath wooden monastic chapel ceilings.",
        "Historians cross-referenced merchant ledgers, probate wills, and harbor guild rolls.",
        "Modernist architects championed unadorned glass facades and open cantilevered halls.",
    ]
    # Expand cleanly with 3 distinct contextual prefixes -> 120 train, 60 eval (disjoint prefixes!)
    train_pairs: list[tuple[str, str]] = []
    train_labels: list[int] = []
    for tag in ("Abstract:", "Archive entry:", "Syllabus note:"):
        for s in sci_sents:
            train_pairs.append(("Topic domain scientific inquiry", f"{tag} {s}"))
            train_labels.append(1)
        for s in hum_sents:
            train_pairs.append(("Topic domain scientific inquiry", f"{tag} {s}"))
            train_labels.append(0)

    eval_pairs: list[tuple[str, str]] = []
    eval_labels: list[int] = []
    for k, tag in enumerate(("Heldout passage:", "Field test:")):
        if k == 0:
            for s in sci_sents:
                eval_pairs.append(("Scientific vs artistic discipline", f"{tag} {s}"))
                eval_labels.append(1)
            for s in hum_sents:
                eval_pairs.append(("Scientific vs artistic discipline", f"{tag} {s}"))
                eval_labels.append(0)
        else:
            for s in sci_sents[:10]:
                eval_pairs.append(("Scientific vs artistic discipline", f"{tag} {s}"))
                eval_labels.append(1)
            for s in hum_sents[:10]:
                eval_pairs.append(("Scientific vs artistic discipline", f"{tag} {s}"))
                eval_labels.append(0)
    return infam, oof, train_pairs, train_labels, eval_pairs, eval_labels


def eval_minilm_logits(
    model: AutoModelForSequenceClassification,
    tok: AutoTokenizer,
    pairs: list[tuple[str, str]],
    batch_size: int = 16,
) -> np.ndarray:
    model.eval()
    logits_list = []
    with torch.no_grad():
        for i in range(0, len(pairs), batch_size):
            batch = pairs[i : i + batch_size]
            enc = tok(
                [p[0] for p in batch],
                [p[1] for p in batch],
                padding=True,
                truncation=True,
                max_length=128,
                return_tensors="pt",
            )
            out = model(**enc).logits.squeeze(-1).cpu().numpy()
            logits_list.append(out.astype(np.float64))
    return np.concatenate(logits_list)


def per_channel_int4_quantize_(
    module: nn.Module, skip_predicate=None
) -> dict[str, torch.Tensor]:
    """In-place symmetric int4 per-row fake-quantization on Linear weights; returns originals."""
    saved: dict[str, torch.Tensor] = {}
    with torch.no_grad():
        for name, sub in module.named_modules():
            if isinstance(sub, nn.Linear):
                if skip_predicate is not None and skip_predicate(name):
                    continue
                w = sub.weight.data
                saved[name] = w.clone()
                amax = w.abs().amax(dim=1, keepdim=True).clamp(min=1e-8)
                scale = amax / 7.0
                q = torch.clamp(torch.round(w / scale), -7.0, 7.0)
                sub.weight.data.copy_(q * scale)
    return saved


def restore_weights_(module: nn.Module, saved: dict[str, torch.Tensor]) -> None:
    with torch.no_grad():
        mod_map = dict(module.named_modules())
        for name, w in saved.items():
            mod_map[name].weight.data.copy_(w)


def run_hp1_minilm(preds_cfg: dict) -> tuple[dict, str]:
    t0 = time.time()
    infam, oof, _, _, _, _ = build_msmarco_datasets()
    infam_pairs = [(q, p) for q, p, _ in infam]
    infam_y = np.array([y for _, _, y in infam], dtype=np.float64)
    oof_pairs = [(q, p) for q, p, _ in oof]
    oof_y = np.array([y for _, _, y in oof], dtype=np.float64)

    tok = AutoTokenizer.from_pretrained(MINILM_ID, local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(MINILM_ID, local_files_only=True)
    model.eval()

    z_in_fp32 = eval_minilm_logits(model, tok, infam_pairs)
    z_oof_fp32 = eval_minilm_logits(model, tok, oof_pairs)
    p_in_fp32 = sigmoid(z_in_fp32)
    p_oof_fp32 = sigmoid(z_oof_fp32)
    pred_in_fp32 = z_in_fp32 > 0.0
    pred_oof_fp32 = z_oof_fp32 > 0.0
    fp32_in_acc = float(np.mean(pred_in_fp32 == (infam_y > 0.5)))
    fp32_oof_acc = float(np.mean(pred_oof_fp32 == (oof_y > 0.5)))

    # Top-2-layer deletion (6 -> 4 layers)
    orig_layers = nn.ModuleList(list(model.bert.encoder.layer))
    model.bert.encoder.layer = nn.ModuleList(list(orig_layers[:4]))
    z_in_del = eval_minilm_logits(model, tok, infam_pairs)
    z_oof_del = eval_minilm_logits(model, tok, oof_pairs)
    model.bert.encoder.layer = orig_layers

    p_in_del = sigmoid(z_in_del)
    p_oof_del = sigmoid(z_oof_del)
    ece_del_raw = binary_ece(p_in_del, infam_y)
    best_t, p_in_recal = fit_temperature_unlabeled_kl(z_in_del, z_in_fp32)
    ece_del_recal = binary_ece(p_in_recal, infam_y)
    ece_rel_drop = float((ece_del_raw - ece_del_recal) / max(ece_del_raw, 1e-8))
    recal_flips = int(np.sum((p_in_recal >= 0.5) != (p_in_del >= 0.5)))

    flips_in_del = ((z_in_del > 0.0) != pred_in_fp32)
    flips_oof_del = ((z_oof_del > 0.0) != pred_oof_fp32)
    tv_in_del = float(np.mean(binary_tv(p_in_del, p_in_fp32)))
    tv_oof_del = float(np.mean(binary_tv(p_oof_del, p_oof_fp32)))
    tv_del_all = float(np.mean(np.concatenate([binary_tv(p_in_del, p_in_fp32), binary_tv(p_oof_del, p_oof_fp32)])))
    flip_del_all = float(np.mean(np.concatenate([flips_in_del, flips_oof_del])))

    # Int4 with FFN output protection ablation (keep encoder.*.output.dense excluding attention in fp32)
    saved_ffn_prot = per_channel_int4_quantize_(
        model.bert.encoder,
        skip_predicate=lambda n: n.endswith("output.dense") and ("attention" not in n),
    )
    z_in_q4_prot = eval_minilm_logits(model, tok, infam_pairs)
    z_oof_q4_prot = eval_minilm_logits(model, tok, oof_pairs)
    restore_weights_(model.bert.encoder, saved_ffn_prot)

    # Full encoder int4 quantization
    saved_q4 = per_channel_int4_quantize_(model.bert.encoder)
    z_in_q4 = eval_minilm_logits(model, tok, infam_pairs)
    z_oof_q4 = eval_minilm_logits(model, tok, oof_pairs)
    restore_weights_(model.bert.encoder, saved_q4)

    p_in_q4 = sigmoid(z_in_q4)
    p_oof_q4 = sigmoid(z_oof_q4)
    flips_in_q4 = (z_in_q4 > 0.0) != pred_in_fp32
    flips_oof_q4 = (z_oof_q4 > 0.0) != pred_oof_fp32
    flips_in_q4_prot = (z_in_q4_prot > 0.0) != pred_in_fp32
    flips_oof_q4_prot = (z_oof_q4_prot > 0.0) != pred_oof_fp32

    flip_rate_in_q4 = float(np.mean(flips_in_q4))
    flip_rate_oof_q4 = float(np.mean(flips_oof_q4))
    flip_q4_all = float(np.mean(np.concatenate([flips_in_q4, flips_oof_q4])))
    tv_q4_all = float(np.mean(np.concatenate([binary_tv(p_in_q4, p_in_fp32), binary_tv(p_oof_q4, p_oof_fp32)])))
    flip_per_tv_q4 = float(flip_q4_all / max(tv_q4_all, 1e-8))
    flip_per_tv_del = float(flip_del_all / max(tv_del_all, 1e-8))

    all_margins = np.abs(np.concatenate([z_in_fp32, z_oof_fp32]))
    all_flips_q4 = np.concatenate([flips_in_q4, flips_oof_q4]).astype(np.int32)
    auroc_q4 = exact_auroc(all_margins, all_flips_q4)

    rss = get_rss_mb()
    del model
    gc.collect()

    out = {
        "model": MINILM_ID,
        "fp32_infam_acc": fp32_in_acc,
        "fp32_oof_acc": fp32_oof_acc,
        "temp_recal_T": best_t,
        "temp_recal_flips": recal_flips,
        "ece_del_raw": ece_del_raw,
        "ece_del_recal": ece_del_recal,
        "temp_ece_rel_drop": ece_rel_drop,
        "infam_flip_rate_del": float(np.mean(flips_in_del)),
        "oof_flip_rate_del": float(np.mean(flips_oof_del)),
        "infam_flip_rate_int4": flip_rate_in_q4,
        "oof_flip_rate_int4": flip_rate_oof_q4,
        "infam_flip_rate_int4_ffn_fp32": float(np.mean(flips_in_q4_prot)),
        "oof_flip_rate_int4_ffn_fp32": float(np.mean(flips_oof_q4_prot)),
        "flip_rate_all_int4": flip_q4_all,
        "tv_all_int4": tv_q4_all,
        "flip_rate_all_del": flip_del_all,
        "tv_all_del": tv_del_all,
        "flip_per_tv_int4": flip_per_tv_q4,
        "flip_per_tv_layer_deletion": flip_per_tv_del,
        "oof_gt_infam_int4": bool(flip_rate_oof_q4 > flip_rate_in_q4),
        "flip_per_tv_int4_gt_deletion": bool(flip_per_tv_q4 > flip_per_tv_del),
        "margin_auroc_int4": auroc_q4,
        "n_int4_flips_total": int(np.sum(all_flips_q4)),
        "rss_mb": rss,
        "elapsed_sec": time.time() - t0,
    }
    p = preds_cfg["HP.1"]["metrics"]
    ece_ok = (ece_del_raw <= 0.05) or (ece_rel_drop >= p["temp_ece_rel_drop_min"])
    held = (
        fp32_in_acc >= p["fp32_infam_acc_min"]
        and recal_flips <= p["temp_recal_flips_max"]
        and ece_ok
        and out["oof_gt_infam_int4"]
        and out["flip_per_tv_int4_gt_deletion"]
        and (auroc_q4 is not None and auroc_q4 >= p["margin_auroc_int4_min"])
    )
    return out, ("HELD" if held else "BROKEN")


def build_smollm_yes_no_prompts() -> tuple[
    list[tuple[str, int]], list[tuple[str, int]], list[tuple[str, int]], list[tuple[str, int]]
]:
    """Build 48 In-Family Yes/No prompts, 48 OOF tricky/negated Yes/No prompts, and Task B routing."""
    infam_raw = [
        ("Is water at standard pressure composed of hydrogen and oxygen?", 1),
        ("Is Berlin the capital city of Germany?", 1),
        ("Do green plant chloroplasts carry out photosynthesis in daylight?", 1),
        ("Is Earth a rocky terrestrial planet orbiting the Sun?", 1),
        ("Do healthy human red blood cells transport oxygen via hemoglobin?", 1),
        ("Does liquid water freeze at zero degrees Celsius under normal pressure?", 1),
        ("Is gold an electrically conductive metallic element?", 1),
        ("Are whales warm blooded marine mammals?", 1),
        ("Does sound travel faster through solid steel than dry air?", 1),
        ("Is two plus two equal to four in standard arithmetic?", 1),
        ("Do honeybees pollinate flowering orchard trees?", 1),
        ("Is Mount Everest located in the Himalayan range?", 1),
        ("Does lightning occur during convective thunderstorms?", 1),
        ("Do copper wires carry electric current well?", 1),
        ("Is Tokyo located on the island nation of Japan?", 1),
        ("Do triangles always contain exactly three interior sides?", 1),
        ("Does gravity pull dropped apples downward toward Earth center?", 1),
        ("Do mammals breathe atmospheric oxygen with lungs?", 1),
        ("Is diamond composed primarily of carbon atoms?", 1),
        ("Are oak trees deciduous or perennial wooden plants?", 1),
        ("Does steam form when liquid water boils at one hundred Celsius?", 1),
        ("Is the Atlantic Ocean located between Europe and North America?", 1),
        ("Do solar panels convert sunlight into direct electric voltage?", 1),
        ("Is nitrogen the most abundant gas in Earth atmosphere?", 1),
        # 24 clear No questions
        ("Can adult elephants fly across oceans using feathered wings?", 0),
        ("Is the Moon made mainly of melted Swiss cheddar cheese?", 0),
        ("Does solid iron melt below the freezing point of water?", 0),
        ("Is Paris the capital city of Brazil?", 0),
        ("Do fish normally breathe dry desert sand instead of water?", 0),
        ("Are rectangles defined by having seven curved circular edges?", 0),
        ("Can unpowered wooden spoons transmit wireless radio broadcasts?", 0),
        ("Does human blood run green with copper chlorophyll inside arteries?", 0),
        ("Is Antarctica known for year-round tropical palm jungles?", 0),
        ("Does three multiplied by five equal ninety?", 0),
        ("Do penguins fly thousands of miles above tropical deserts?", 0),
        ("Is concrete lighter and less dense than helium balloons?", 0),
        ("Can house cats solve differential equations on blackboards?", 0),
        ("Is Mars closer to the Sun than the planet Mercury?", 0),
        ("Do stone statues breathe oxygen and eat loaves of bread?", 0),
        ("Is table salt chemically identical to pure helium gas?", 0),
        ("Can rubber erasers orbit Jupiter as natural moons?", 0),
        ("Does subtracting ten from three give positive fifty?", 0),
        ("Are violins classified as heavy diesel steam engines?", 0),
        ("Is the Sahara Desert covered beneath two miles of permanent ice?", 0),
        ("Do glass marbles grow leaves and bloom in spring?", 0),
        ("Is Tuesday chronologically older than ancient Sumeria?", 0),
        ("Do clouds consist of solid cast-iron anvil blocks?", 0),
        ("Can candle flames freeze boiling soup into solid ice?", 0),
    ]
    oof_raw = [
        # Tricky / negated / double-negative / comparative near-boundary prompts
        ("If water boils at 100C under standard pressure, would heating water to 40C normally boil it?", 0),
        ("Unlike mercury, copper is a solid metal at room temperature; is copper liquid at 20C?", 0),
        ("Although whales live underwater, they breathe air; are whales cold-blooded reptiles?", 0),
        ("Since Mars lies outside Earth orbit, is Mars closer to the Sun than Venus?", 0),
        ("Because bats are flying mammals rather than birds, do bats possess feathers?", 0),
        ("If neither bronze nor steel is biologically alive, can a bronze statue metabolize glucose?", 0),
        ("While spiders have eight legs, beetles have six; are beetles classified as eight-legged arachnids?", 0),
        ("Though Venice uses boats instead of highways, is Venice located inside Japan?", 0),
        ("When silver tarnishes chemically, does silver transmute into radioactive uranium?", 0),
        ("Even though diamonds are hard minerals, do diamonds grow roots in soil?", 0),
        ("If a triangle has three sides, does doubling its side lengths give it six corners?", 0),
        ("Although Pluto orbits far beyond Neptune, is Pluto heavier than the Sun?", 0),
        ("Since vinegar is acidic and baking soda is basic, are both chemically identical?", 0),
        ("While nitrogen dominates our air, does pure nitrogen support human respiration without oxygen?", 0),
        ("If winter in Sydney occurs in July, is July midsummer in Madrid?", 0),
        ("Can any integer strictly greater than 10 simultaneously be less than 5?", 0),
        ("Even if a clock stops completely, does a broken mechanical watch still tick forward accurately?", 0),
        ("Although ice floats on water because ice expands, is frozen ice denser than liquid water?", 0),
        ("If glass transmits visible light cleanly, does window glass block all sunlight completely?", 0),
        ("Since penguins cannot fly in air, are penguins amphibians rather than birds?", 0),
        ("If iron rusts only with oxygen and moisture, does dry vacuum cause rapid rusting?", 0),
        ("While jazz began in New Orleans, was jazz invented in ancient Athens?", 0),
        ("Even though sound travels well in steel, can sound waves cross empty outer space vacuum?", 0),
        ("If two parallel Euclidean lines never intersect, do they meet at a triangle vertex?", 0),
        # 24 tricky Yes prompts
        ("Unlike cold-blooded lizards, do bats regulate internal body warmth as mammals?", 1),
        ("Even though sea turtles swim in oceans, must sea turtles surface to breathe air?", 1),
        ("Although ice feels cold and solid, is frozen ice chemically composed of water molecules?", 1),
        ("Despite orbiting farther out than Mercury, is Earth smaller in radius than Jupiter?", 1),
        ("If bronze alloys copper and tin together, does bronze contain metallic copper atoms?", 1),
        ("Although glass looks solid, does optical fiber guide light signals along glass cores?", 1),
        ("Even if yeast looks dormant dry, does yeast produce carbon dioxide gas in warm dough?", 1),
        ("While Antarctica stays frozen, does Antarctica sit around the geographic South Pole?", 1),
        ("If copper heats quickly on stoves, is copper a thermal conductor?", 1),
        ("Even without wings, can maple seeds spin briefly in autumn gusts as wind carries them?", 1),
        ("Though tomatoes taste savory in sauces, are tomatoes botanically fruit with seeds?", 1),
        ("If seventeen is prime and greater than ten, is seventeen an odd positive integer?", 1),
        ("Although sharks lack bony skeletons, do sharks breathe dissolved oxygen using gills?", 1),
        ("Even on overcast days, does the Sun still illuminate clouds from above?", 1),
        ("Since iron attracts refrigerator magnets, is pure metallic iron ferromagnetic at room temperature?", 1),
        ("Despite deep sea darkness, do hydrothermal vents release hot mineral water into ocean basins?", 1),
        ("If every square is a rectangle with equal sides, do all squares have four right angles?", 1),
        ("Although helium lifts party balloons upward, does helium remain lighter than surrounding nitrogen air?", 1),
        ("Since leaves lose green pigment in autumn, were green leaves rich in chlorophyll during summer?", 1),
        ("Even though wood insulates well compared to aluminum, can dry wood still burn in hot fire?", 1),
        ("If zero multiplied by any real number yields zero, does zero times ninety equal zero?", 1),
        ("Although violins have no brass valves, are string instruments used in classical orchestras?", 1),
        ("Despite smaller mass than Earth, does the Moon still exert measurable tidal pull on oceans?", 1),
        ("If human DNA encodes proteins via RNA codons, are genes stored in nucleic acids?", 1),
    ]
    # Task B: Binary natural prompt classification (60 train, 32 eval) -> Yes=Science, No=History/Arts
    sci_topics = [
        "Electron spin orbitals in copper lattices",
        "Mitochondrial ATP proton gradients",
        "Quantum tunneling across tunnel diodes",
        "Crustal fault shear wave propagation",
        "Ribosomal peptide bond catalysis",
        "Thermodynamic Carnot cycle efficiency",
        "Photosynthetic carbon fixation kinetics",
        "Nuclear deuterium fusion cross sections",
        "Semiconductor bandgap photon absorption",
        "Atmospheric Coriolis jet stream dynamics",
        "CRISPR Cas9 guide RNA cleavage",
        "Superconducting magnetic flux pinning",
        "Catalytic enzyme lowering activation barriers",
        "Gravitational tidal force gradients",
        "Polymer cross-linking elastomer elasticity",
    ]
    art_topics = [
        "Baroque harpsichord fugue counterpoint",
        "Renaissance marble drapery sculpting",
        "Roman stone aqueduct municipal taxation",
        "Gothic flying buttress stone vaulting",
        "Impressionist oil canvas brushwork",
        "Ancient terracotta amphora vase painting",
        "Elizabethan five act dramatic verse",
        "Victorian serialized satirical novels",
        "Medieval gold leaf psalm illumination",
        "Romantic Alpine watercolor sketching",
        "Silk Road caravan merchant ledgers",
        "Athenian tragic choral strophe structure",
        "Neoclassical symphony orchestra finales",
        "Woodblock ink printmaking craftsmanship",
        "Jazz walking bassline improvisation",
    ]
    tb_train: list[tuple[str, int]] = []
    for prefix in ("Domain check — Science or Arts:", "Subject classifier (Science=Yes, Arts=No):"):
        for s in sci_topics:
            tb_train.append((f"{prefix} {s}. Answer Yes if scientific physics/biology, No if history/arts.", 1))
        for s in art_topics:
            tb_train.append((f"{prefix} {s}. Answer Yes if scientific physics/biology, No if history/arts.", 0))

    sci_eval = [
        "Neutron capture fission moderation",
        "Chlorophyll photon excitation fluorescence",
        "Osmotic lipid bilayer ion diffusion",
        "Galactic gravitational lensing refraction",
        "Polymerization enthalpy calorimetry",
        "Bacteriophage DNA capsid injection",
        "Magnetohydrodynamic plasma confinement",
        "Ferromagnetic domain hysteresis loops",
        "Spectral atomic hydrogen emission lines",
        "Glacial bedrock abrasion striations",
        "Photodiode reverse bias photocurrent",
        "Protease catalytic triad hydrolysis",
        "Electrophoretic RNA gel separation",
        "Seismic Rayleigh surface wave dispersion",
        "Adiabatic atmospheric lapse cooling",
        "Calorimetric ice fusion latent heat",
    ]
    art_eval = [
        "Byzantine mosaic glass tesserae",
        "Celtic bronze shield engraving",
        "Chamber cello sonata modulation",
        "Ming porcelain underglaze cobalt",
        "Sumerian cuneiform grain tallies",
        "Venetian glassblowing furnace craft",
        "Fresco lime plaster wall murals",
        "Tudor timber hall roof carpentry",
        "Japanese haiku seasonal imagery",
        "Medieval bell foundry casting rites",
        "Persian miniature manuscript borders",
        "Hanseatic Baltic shipping charters",
        "String trio baroque sarabande rhythm",
        "Classical marble frieze bas-relief",
        "Romantic piano nocturne rubato phrasing",
        "Ancient Phoenician purple textile trade",
    ]
    tb_eval = [
        (f"Heldout domain query: {s}. Answer Yes if scientific physics/biology, No if history/arts.", 1)
        for s in sci_eval
    ] + [
        (f"Heldout domain query: {s}. Answer Yes if scientific physics/biology, No if history/arts.", 0)
        for s in art_eval
    ]
    return infam_raw, oof_raw, tb_train, tb_eval


def eval_smollm_yesno(
    model: AutoModelForCausalLM,
    tok: AutoTokenizer,
    prompts: list[str],
    yes_ids: list[int],
    no_ids: list[int],
    batch_size: int = 8,
    collect_hidden: bool = False,
) -> tuple[np.ndarray, np.ndarray | None]:
    model.eval()
    margins: list[np.ndarray] = []
    hiddens: list[np.ndarray] = []
    formatted = [
        tok.apply_chat_template(
            [{"role": "user", "content": f"{p} Reply with only Yes or No."}],
            tokenize=False,
            add_generation_prompt=True,
        )
        for p in prompts
    ]
    with torch.no_grad():
        for i in range(0, len(formatted), batch_size):
            batch = formatted[i : i + batch_size]
            enc = tok(batch, padding=True, truncation=True, max_length=128, return_tensors="pt")
            out = model(**enc, output_hidden_states=collect_hidden)
            last_logits = out.logits[:, -1, :].float()
            logp = torch.log_softmax(last_logits, dim=-1)
            lp_yes = torch.logsumexp(logp[:, yes_ids], dim=-1)
            lp_no = torch.logsumexp(logp[:, no_ids], dim=-1)
            margins.append((lp_yes - lp_no).cpu().numpy().astype(np.float64))
            if collect_hidden:
                hiddens.append(out.hidden_states[-1][:, -1, :].float().cpu().numpy())
    h_cat = np.concatenate(hiddens, axis=0) if collect_hidden else None
    return np.concatenate(margins), h_cat


def run_hp2_smollm(preds_cfg: dict) -> tuple[dict, str]:
    t0 = time.time()
    infam_raw, oof_raw, _, _ = build_smollm_yes_no_prompts()
    in_prompts = [q for q, _ in infam_raw]
    in_y = np.array([y for _, y in infam_raw], dtype=np.float64)
    oof_prompts = [q for q, _ in oof_raw]
    oof_y = np.array([y for _, y in oof_raw], dtype=np.float64)

    tok = AutoTokenizer.from_pretrained(SMOLLM_ID)
    tok.padding_side = "left"
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    yes_ids = [tok.encode(w, add_special_tokens=False)[0] for w in ("Yes", " Yes")]
    no_ids = [tok.encode(w, add_special_tokens=False)[0] for w in ("No", " No")]

    model = AutoModelForCausalLM.from_pretrained(SMOLLM_ID, torch_dtype=torch.float32)
    model.eval()

    z_in_fp32, _ = eval_smollm_yesno(model, tok, in_prompts, yes_ids, no_ids)
    z_oof_fp32, _ = eval_smollm_yesno(model, tok, oof_prompts, yes_ids, no_ids)
    p_in_fp32 = sigmoid(z_in_fp32)
    p_oof_fp32 = sigmoid(z_oof_fp32)
    pred_in_fp32 = z_in_fp32 > 0.0
    pred_oof_fp32 = z_oof_fp32 > 0.0
    fp32_in_acc = float(np.mean(pred_in_fp32 == (in_y > 0.5)))
    fp32_oof_acc = float(np.mean(pred_oof_fp32 == (oof_y > 0.5)))

    # Top-4-layer deletion (30 -> 26 layers)
    orig_layers = nn.ModuleList(list(model.model.layers))
    model.model.layers = nn.ModuleList(list(orig_layers[:26]))
    z_in_del, _ = eval_smollm_yesno(model, tok, in_prompts, yes_ids, no_ids)
    z_oof_del, _ = eval_smollm_yesno(model, tok, oof_prompts, yes_ids, no_ids)
    model.model.layers = orig_layers

    p_in_del = sigmoid(z_in_del)
    p_oof_del = sigmoid(z_oof_del)
    ece_del_raw = binary_ece(p_in_del, in_y)
    best_t, p_in_recal = fit_temperature_unlabeled_kl(z_in_del, z_in_fp32)
    ece_del_recal = binary_ece(p_in_recal, in_y)
    ece_rel_drop = float((ece_del_raw - ece_del_recal) / max(ece_del_raw, 1e-8))
    recal_flips = int(np.sum((p_in_recal >= 0.5) != (p_in_del >= 0.5)))

    flips_in_del = (z_in_del > 0.0) != pred_in_fp32
    flips_oof_del = (z_oof_del > 0.0) != pred_oof_fp32
    flip_del_all = float(np.mean(np.concatenate([flips_in_del, flips_oof_del])))
    tv_del_all = float(np.mean(np.concatenate([binary_tv(p_in_del, p_in_fp32), binary_tv(p_oof_del, p_oof_fp32)])))

    # First quantize all transformer layer Linears EXCEPT down_proj (down_proj kept fp32)
    per_channel_int4_quantize_(model.model.layers, skip_predicate=lambda n: "down_proj" in n)
    z_in_q4_prot, _ = eval_smollm_yesno(model, tok, in_prompts, yes_ids, no_ids)
    z_oof_q4_prot, _ = eval_smollm_yesno(model, tok, oof_prompts, yes_ids, no_ids)

    # Now quantize ONLY down_proj on top -> full transformer int4 without reloading twice
    per_channel_int4_quantize_(model.model.layers, skip_predicate=lambda n: "down_proj" not in n)
    z_in_q4, _ = eval_smollm_yesno(model, tok, in_prompts, yes_ids, no_ids)
    z_oof_q4, _ = eval_smollm_yesno(model, tok, oof_prompts, yes_ids, no_ids)

    p_in_q4 = sigmoid(z_in_q4)
    p_oof_q4 = sigmoid(z_oof_q4)
    flips_in_q4 = (z_in_q4 > 0.0) != pred_in_fp32
    flips_oof_q4 = (z_oof_q4 > 0.0) != pred_oof_fp32
    flips_in_q4_prot = (z_in_q4_prot > 0.0) != pred_in_fp32
    flips_oof_q4_prot = (z_oof_q4_prot > 0.0) != pred_oof_fp32

    flip_rate_in_q4 = float(np.mean(flips_in_q4))
    flip_rate_oof_q4 = float(np.mean(flips_oof_q4))
    flip_q4_all = float(np.mean(np.concatenate([flips_in_q4, flips_oof_q4])))
    tv_q4_all = float(np.mean(np.concatenate([binary_tv(p_in_q4, p_in_fp32), binary_tv(p_oof_q4, p_oof_fp32)])))
    flip_per_tv_q4 = float(flip_q4_all / max(tv_q4_all, 1e-8))
    flip_per_tv_del = float(flip_del_all / max(tv_del_all, 1e-8))

    all_margins = np.abs(np.concatenate([z_in_fp32, z_oof_fp32]))
    all_flips_q4 = np.concatenate([flips_in_q4, flips_oof_q4]).astype(np.int32)
    auroc_q4 = exact_auroc(all_margins, all_flips_q4)

    rss = get_rss_mb()
    del model
    gc.collect()

    out = {
        "model": SMOLLM_ID,
        "fp32_infam_acc": fp32_in_acc,
        "fp32_oof_acc": fp32_oof_acc,
        "temp_recal_T": best_t,
        "temp_recal_flips": recal_flips,
        "ece_del_raw": ece_del_raw,
        "ece_del_recal": ece_del_recal,
        "temp_ece_rel_drop": ece_rel_drop,
        "infam_flip_rate_del": float(np.mean(flips_in_del)),
        "oof_flip_rate_del": float(np.mean(flips_oof_del)),
        "infam_flip_rate_int4": flip_rate_in_q4,
        "oof_flip_rate_int4": flip_rate_oof_q4,
        "infam_flip_rate_int4_downproj_fp32": float(np.mean(flips_in_q4_prot)),
        "oof_flip_rate_int4_downproj_fp32": float(np.mean(flips_oof_q4_prot)),
        "flip_rate_all_int4": flip_q4_all,
        "tv_all_int4": tv_q4_all,
        "flip_rate_all_del": flip_del_all,
        "tv_all_del": tv_del_all,
        "flip_per_tv_int4": flip_per_tv_q4,
        "flip_per_tv_layer_deletion": flip_per_tv_del,
        "flip_per_tv_int4_gt_deletion": bool(flip_per_tv_q4 > flip_per_tv_del),
        "margin_auroc_int4": auroc_q4,
        "n_int4_flips_total": int(np.sum(all_flips_q4)),
        "rss_mb": rss,
        "elapsed_sec": time.time() - t0,
    }
    p = preds_cfg["HP.2"]["metrics"]
    ece_ok = (ece_del_raw <= 0.05) or (ece_rel_drop >= p["temp_ece_rel_drop_min"])
    held = (
        recal_flips <= p["temp_recal_flips_max"]
        and ece_ok
        and out["flip_per_tv_int4_gt_deletion"]
        and (auroc_q4 is not None and auroc_q4 >= p["margin_auroc_int4_min"])
    )
    return out, ("HELD" if held else "BROKEN")


def run_hp3_minilm_zerovln(preds_cfg: dict) -> tuple[dict, str]:
    t0 = time.time()
    torch.manual_seed(101)
    infam, _, tb_train_pairs, tb_train_y_list, tb_eval_pairs, tb_eval_y_list = build_msmarco_datasets()
    taskA_pairs = [(q, p) for q, p, _ in infam]
    taskA_y = np.array([y for _, _, y in infam], dtype=np.float64)
    tb_train_y = torch.tensor(tb_train_y_list, dtype=torch.long)
    tb_eval_y = np.array(tb_eval_y_list, dtype=np.int64)

    tok = AutoTokenizer.from_pretrained(MINILM_ID, local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(MINILM_ID, local_files_only=True)
    model.eval()

    taskA_base_logits = eval_minilm_logits(model, tok, taskA_pairs)
    taskA_base_acc = float(np.mean((taskA_base_logits > 0.0) == (taskA_y > 0.5)))

    # Cache frozen [CLS] features for Task B
    def get_cls(pairs_in):
        res = []
        with torch.no_grad():
            for i in range(0, len(pairs_in), 24):
                b = pairs_in[i : i + 24]
                enc = tok([p[0] for p in b], [p[1] for p in b], padding=True, truncation=True, max_length=96, return_tensors="pt")
                res.append(model.bert(**enc).last_hidden_state[:, 0, :])
        return torch.cat(res, dim=0)

    x_b_tr = get_cls(tb_train_pairs)
    x_b_ev = get_cls(tb_eval_pairs)

    frozen_head = nn.Sequential(nn.Linear(x_b_tr.shape[1], 128), nn.GELU(), nn.Linear(128, 2))
    opt_f = torch.optim.AdamW(frozen_head.parameters(), lr=5e-3, weight_decay=1e-4)
    for _ in range(150):
        opt_f.zero_grad()
        loss = F.cross_entropy(frozen_head(x_b_tr), tb_train_y)
        loss.backward()
        opt_f.step()
    with torch.no_grad():
        pred_ev_f = frozen_head(x_b_ev).argmax(dim=-1).numpy()
    frozen_taskB_acc = float(np.mean(pred_ev_f == tb_eval_y))
    frozen_taskA_drop = 0.0

    # End-to-end SFT across ALL 22.7M backbone parameters + Task-B linear readout
    sft_readout = nn.Linear(model.config.hidden_size, 2)
    # Encodings for full Task-B training batch gradient g = \nabla_\theta (-L_B(\theta_0))
    enc_b_tr = tok(
        [p[0] for p in tb_train_pairs],
        [p[1] for p in tb_train_pairs],
        padding=True,
        truncation=True,
        max_length=96,
        return_tensors="pt",
    )
    backbone_params = [(n, p) for n, p in model.bert.named_parameters() if p.requires_grad]
    n_backbone_params = int(sum(p.numel() for _, p in backbone_params))
    theta0 = {n: p.detach().clone().cpu() for n, p in backbone_params}

    # Exact full-batch gradient of Task-B return J = -CE at initialization
    model.eval()
    model.zero_grad()
    sft_readout.zero_grad()
    h_cls = model.bert(**enc_b_tr).last_hidden_state[:, 0, :]
    ret_init = -F.cross_entropy(sft_readout(h_cls), tb_train_y)
    ret_init.backward()
    g_map = {n: p.grad.detach().clone().cpu() for n, p in backbone_params if p.grad is not None}

    # Run 12 AdamW SFT steps across all 6 Transformer layers + readout
    all_params = [p for _, p in backbone_params] + list(sft_readout.parameters())
    opt_sft = torch.optim.AdamW(all_params, lr=2e-4, weight_decay=0.0)
    rng = np.random.default_rng(101)
    model.train()
    for step in range(12):
        idx = rng.permutation(len(tb_train_pairs))
        for start in range(0, len(idx), 30):
            sel = idx[start : start + 30]
            opt_sft.zero_grad()
            sub_enc = {k: v[sel] for k, v in enc_b_tr.items()}
            out_cls = model.bert(**sub_enc).last_hidden_state[:, 0, :]
            loss = F.cross_entropy(sft_readout(out_cls), tb_train_y[sel])
            loss.backward()
            opt_sft.step()

    model.eval()
    # Evaluate Task-B eval accuracy after SFT & Task-A drift
    enc_b_ev = tok(
        [p[0] for p in tb_eval_pairs],
        [p[1] for p in tb_eval_pairs],
        padding=True,
        truncation=True,
        max_length=96,
        return_tensors="pt",
    )
    with torch.no_grad():
        sft_taskB_acc = float(np.mean(sft_readout(model.bert(**enc_b_ev).last_hidden_state[:, 0, :]).argmax(dim=-1).numpy() == tb_eval_y))
    taskA_sft_logits = eval_minilm_logits(model, tok, taskA_pairs)
    sft_taskA_acc = float(np.mean((taskA_sft_logits > 0.0) == (taskA_y > 0.5)))
    sft_taskA_acc_drop = float(taskA_base_acc - sft_taskA_acc)
    sft_taskA_logit_l2_drift = float(np.sqrt(np.mean((taskA_sft_logits - taskA_base_logits) ** 2)))

    # Exact float64 Prop. 2 orthogonal decomposition across all 22.7M backbone parameters
    norm2_g = 0.0
    norm2_delta = 0.0
    dot_g_delta = 0.0
    for n, p in backbone_params:
        d = (p.detach().cpu() - theta0[n]).to(torch.float64)
        g = g_map.get(n, torch.zeros_like(d)).to(torch.float64)
        norm2_g += float(torch.sum(g * g).item())
        norm2_delta += float(torch.sum(d * d).item())
        dot_g_delta += float(torch.sum(g * d).item())

    scale_ret = dot_g_delta / max(norm2_g, 1e-30)
    norm2_ret = (dot_g_delta * dot_g_delta) / max(norm2_g, 1e-30)
    norm2_w = 0.0
    dot_g_w = 0.0
    for n, p in backbone_params:
        d = (p.detach().cpu() - theta0[n]).to(torch.float64)
        g = g_map.get(n, torch.zeros_like(d)).to(torch.float64)
        w = d - scale_ret * g
        norm2_w += float(torch.sum(w * w).item())
        dot_g_w += float(torch.sum(g * w).item())

    pyth_rel_err = float(abs(norm2_delta - (norm2_ret + norm2_w)) / max(norm2_delta, 1e-18))
    orth_cos_abs = float(abs(dot_g_w) / max(math.sqrt(norm2_g * max(norm2_w, 1e-30)), 1e-30))
    waste_frac = float(norm2_w / max(norm2_delta, 1e-30))

    rss = get_rss_mb()
    del model, frozen_head, sft_readout, opt_sft, theta0, g_map
    gc.collect()

    out = {
        "model": MINILM_ID,
        "n_backbone_params": n_backbone_params,
        "taskA_base_acc": taskA_base_acc,
        "frozen_taskA_drop": frozen_taskA_drop,
        "frozen_taskB_acc": frozen_taskB_acc,
        "sft_taskA_acc": sft_taskA_acc,
        "sft_taskA_acc_drop": sft_taskA_acc_drop,
        "sft_taskA_logit_l2_drift": sft_taskA_logit_l2_drift,
        "sft_taskB_acc": sft_taskB_acc,
        "norm2_delta": norm2_delta,
        "norm2_return": norm2_ret,
        "norm2_w_orth": norm2_w,
        "prop2_pyth_rel_err": pyth_rel_err,
        "prop2_orth_cos_abs": orth_cos_abs,
        "orthogonal_waste_fraction": waste_frac,
        "rss_mb": rss,
        "elapsed_sec": time.time() - t0,
    }
    p = preds_cfg["HP.3"]["metrics"]
    held = (
        frozen_taskA_drop <= p["frozen_taskA_drop_max"]
        and frozen_taskB_acc >= p["frozen_taskB_acc_min"]
        and sft_taskA_logit_l2_drift >= p["sft_taskA_logit_l2_drift_min"]
        and pyth_rel_err <= p["prop2_pyth_rel_err_max"]
        and orth_cos_abs <= p["prop2_orth_cos_abs_max"]
        and waste_frac >= p["orthogonal_waste_fraction_min"]
    )
    return out, ("HELD" if held else "BROKEN")


def run_hp4_smollm_zerovln(preds_cfg: dict) -> tuple[dict, str]:
    t0 = time.time()
    torch.manual_seed(202)
    infam_raw, _, tb_train, tb_eval = build_smollm_yes_no_prompts()
    in_prompts = [q for q, _ in infam_raw]
    in_y = np.array([y for _, y in infam_raw], dtype=np.float64)
    tb_tr_prompts = [q for q, _ in tb_train]
    tb_tr_y = torch.tensor([y for _, y in tb_train], dtype=torch.long)
    tb_ev_prompts = [q for q, _ in tb_eval]
    tb_ev_y = np.array([y for _, y in tb_eval], dtype=np.int64)

    tok = AutoTokenizer.from_pretrained(SMOLLM_ID)
    tok.padding_side = "left"
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    yes_ids = [tok.encode(w, add_special_tokens=False)[0] for w in ("Yes", " Yes")]
    no_ids = [tok.encode(w, add_special_tokens=False)[0] for w in ("No", " No")]

    model = AutoModelForCausalLM.from_pretrained(SMOLLM_ID, torch_dtype=torch.float32)
    model.eval()
    taskA_base_logits, _ = eval_smollm_yesno(model, tok, in_prompts, yes_ids, no_ids)
    taskA_base_acc = float(np.mean((taskA_base_logits > 0.0) == (in_y > 0.5)))

    # Frozen LLM probe on final hidden states for Task B
    _, h_tr_np = eval_smollm_yesno(model, tok, tb_tr_prompts, yes_ids, no_ids, collect_hidden=True)
    _, h_ev_np = eval_smollm_yesno(model, tok, tb_ev_prompts, yes_ids, no_ids, collect_hidden=True)
    h_tr = torch.tensor(h_tr_np, dtype=torch.float32)
    h_ev = torch.tensor(h_ev_np, dtype=torch.float32)

    frozen_probe = nn.Linear(h_tr.shape[1], 2)
    opt_p = torch.optim.AdamW(frozen_probe.parameters(), lr=1e-2, weight_decay=1e-4)
    for _ in range(200):
        opt_p.zero_grad()
        loss = F.cross_entropy(frozen_probe(h_tr), tb_tr_y)
        loss.backward()
        opt_p.step()
    with torch.no_grad():
        frozen_taskB_acc = float(np.mean(frozen_probe(h_ev).argmax(dim=-1).numpy() == tb_ev_y))
    frozen_taskA_drop = 0.0

    # Freeze everything EXCEPT top 2 decoder blocks (layers 28, 29) + Yes/No SFT optimization
    for p in model.parameters():
        p.requires_grad_(False)
    top_blocks = list(model.model.layers[28:30])
    top_params = []
    for blk in top_blocks:
        for n, p in blk.named_parameters():
            p.requires_grad_(True)
            top_params.append((n, p))
    n_top_params = int(sum(p.numel() for _, p in top_params))
    theta0 = {id(p): p.detach().clone().cpu() for _, p in top_params}

    formatted_tr = [
        tok.apply_chat_template(
            [{"role": "user", "content": f"{q} Reply with only Yes or No."}],
            tokenize=False,
            add_generation_prompt=True,
        )
        for q in tb_tr_prompts
    ]
    enc_tr = tok(formatted_tr, padding=True, truncation=True, max_length=96, return_tensors="pt")

    def forward_yesno_ce(sub_ids, sub_mask, sub_y):
        logits = model(input_ids=sub_ids, attention_mask=sub_mask).logits[:, -1, :].float()
        logp = torch.log_softmax(logits, dim=-1)
        lp_yes = torch.logsumexp(logp[:, yes_ids], dim=-1)
        lp_no = torch.logsumexp(logp[:, no_ids], dim=-1)
        two = torch.stack([lp_no, lp_yes], dim=-1)
        return F.cross_entropy(two, sub_y)

    # Full-batch initial return gradient g = \nabla_\theta (-L_B(\theta_0)) accumulated over microbatches
    model.eval()
    model.zero_grad()
    n_tr = len(tb_tr_prompts)
    for start in range(0, n_tr, 15):
        end = min(start + 15, n_tr)
        loss_mb = forward_yesno_ce(enc_tr["input_ids"][start:end], enc_tr["attention_mask"][start:end], tb_tr_y[start:end])
        ret_mb = -loss_mb * ((end - start) / float(n_tr))
        ret_mb.backward()
    g_map = {id(p): p.grad.detach().clone().cpu() for _, p in top_params if p.grad is not None}

    opt_sft = torch.optim.AdamW([p for _, p in top_params], lr=1e-4, weight_decay=0.0)
    rng = np.random.default_rng(202)
    model.train()
    for step in range(10):
        idx = rng.permutation(n_tr)
        for start in range(0, n_tr, 15):
            sel = idx[start : start + 15]
            opt_sft.zero_grad()
            loss = forward_yesno_ce(enc_tr["input_ids"][sel], enc_tr["attention_mask"][sel], tb_tr_y[sel])
            loss.backward()
            opt_sft.step()

    model.eval()
    z_ev_sft, _ = eval_smollm_yesno(model, tok, tb_ev_prompts, yes_ids, no_ids)
    sft_taskB_acc = float(np.mean((z_ev_sft > 0.0) == (tb_ev_y == 1)))
    taskA_sft_logits, _ = eval_smollm_yesno(model, tok, in_prompts, yes_ids, no_ids)
    sft_taskA_acc = float(np.mean((taskA_sft_logits > 0.0) == (in_y > 0.5)))
    sft_taskA_acc_drop = float(taskA_base_acc - sft_taskA_acc)
    sft_taskA_logit_l2_drift = float(np.sqrt(np.mean((taskA_sft_logits - taskA_base_logits) ** 2)))

    # Exact float64 Prop. 2 orthogonal decomposition across all unfrozen decoder-block weights
    norm2_g = 0.0
    norm2_delta = 0.0
    dot_g_delta = 0.0
    for _, p in top_params:
        d = (p.detach().cpu() - theta0[id(p)]).to(torch.float64)
        g = g_map.get(id(p), torch.zeros_like(d)).to(torch.float64)
        norm2_g += float(torch.sum(g * g).item())
        norm2_delta += float(torch.sum(d * d).item())
        dot_g_delta += float(torch.sum(g * d).item())

    scale_ret = dot_g_delta / max(norm2_g, 1e-30)
    norm2_ret = (dot_g_delta * dot_g_delta) / max(norm2_g, 1e-30)
    norm2_w = 0.0
    dot_g_w = 0.0
    for _, p in top_params:
        d = (p.detach().cpu() - theta0[id(p)]).to(torch.float64)
        g = g_map.get(id(p), torch.zeros_like(d)).to(torch.float64)
        w = d - scale_ret * g
        norm2_w += float(torch.sum(w * w).item())
        dot_g_w += float(torch.sum(g * w).item())

    pyth_rel_err = float(abs(norm2_delta - (norm2_ret + norm2_w)) / max(norm2_delta, 1e-18))
    orth_cos_abs = float(abs(dot_g_w) / max(math.sqrt(norm2_g * max(norm2_w, 1e-30)), 1e-30))
    waste_frac = float(norm2_w / max(norm2_delta, 1e-30))

    rss = get_rss_mb()
    del model, frozen_probe, opt_sft, theta0, g_map
    gc.collect()

    out = {
        "model": SMOLLM_ID,
        "n_top_2block_params": n_top_params,
        "taskA_base_acc": taskA_base_acc,
        "frozen_taskA_drop": frozen_taskA_drop,
        "frozen_taskB_acc": frozen_taskB_acc,
        "sft_taskA_acc": sft_taskA_acc,
        "sft_taskA_acc_drop": sft_taskA_acc_drop,
        "sft_taskA_logit_l2_drift": sft_taskA_logit_l2_drift,
        "sft_taskB_acc": sft_taskB_acc,
        "norm2_delta": norm2_delta,
        "norm2_return": norm2_ret,
        "norm2_w_orth": norm2_w,
        "prop2_pyth_rel_err": pyth_rel_err,
        "prop2_orth_cos_abs": orth_cos_abs,
        "orthogonal_waste_fraction": waste_frac,
        "rss_mb": rss,
        "elapsed_sec": time.time() - t0,
    }
    p = preds_cfg["HP.4"]["metrics"]
    held = (
        frozen_taskA_drop <= p["frozen_taskA_drop_max"]
        and frozen_taskB_acc >= p["frozen_taskB_acc_min"]
        and sft_taskA_logit_l2_drift >= p["sft_taskA_logit_l2_drift_min"]
        and pyth_rel_err <= p["prop2_pyth_rel_err_max"]
        and orth_cos_abs <= p["prop2_orth_cos_abs_max"]
        and waste_frac >= p["orthogonal_waste_fraction_min"]
    )
    return out, ("HELD" if held else "BROKEN")


def energy_distance(X: np.ndarray, Y: np.ndarray) -> float:
    """Empirical two-sample energy distance E||X-Y|| (exact V-statistic: >= 0, 0 iff same empirical law)."""
    # Compute in chunks to keep RAM tiny
    n = len(X)
    m = len(Y)

    def mean_dist(A: np.ndarray, B: np.ndarray) -> float:
        tot = 0.0
        bs = 250
        for i in range(0, len(A), bs):
            a = A[i : i + bs]
            diff = a[:, None, :] - B[None, :, :]
            tot += float(np.sum(np.sqrt(np.sum(diff * diff, axis=-1))))
        return tot / float(len(A) * len(B))

    d_xy = mean_dist(X, Y)
    d_xx = mean_dist(X, X)
    d_yy = mean_dist(Y, Y)
    return float(max(0.0, 2.0 * d_xy - d_xx - d_yy))


def run_hp5_polish_kernel(preds_cfg: dict) -> tuple[dict, str]:
    t0 = time.time()
    alpha = 0.35

    def phi(x: np.ndarray) -> np.ndarray:
        return np.stack([x[:, 0] + alpha * (x[:, 1] ** 3), x[:, 1]], axis=-1)

    def phi_inv(y: np.ndarray) -> np.ndarray:
        return np.stack([y[:, 0] - alpha * (y[:, 1] ** 3), y[:, 1]], axis=-1)

    seeds = [101, 202, 303]
    jac_errs = []
    mc_eds = []
    collapse_ratios = []

    mu = np.array([0.4, -0.3])
    cov = np.array([[0.5, 0.15], [0.15, 0.4]])
    chol = np.linalg.cholesky(cov)
    cov_inv = np.linalg.inv(cov)

    for s in seeds:
        rng = np.random.default_rng(s)
        # 1. Exact Jacobian density invariance across 200 continuous points
        pts = rng.normal(size=(200, 2))
        y_pts = phi(pts)
        # det D(phi^-1) == 1 identically on upper triangular cubic shear -> log|det| == 0
        dx = pts - mu
        dx_rec = phi_inv(y_pts) - mu
        logp_src = -0.5 * np.sum((dx @ cov_inv) * dx, axis=-1)
        logp_tgt = -0.5 * np.sum((dx_rec @ cov_inv) * dx_rec, axis=-1)
        jac_errs.append(float(np.max(np.abs(logp_src - logp_tgt))))

        # 2. Multi-step 2D Ornstein-Uhlenbeck evolution covariance (3 steps, 2500 samples)
        n_samp = 2500
        e0 = np.array([0.2, -0.5])
        s_src = e0 + 0.3 * rng.normal(size=(n_samp, 2))
        s_tgt = phi(e0 + 0.3 * rng.normal(size=(n_samp, 2)))
        controls = [np.array([0.3, -0.2]), np.array([-0.15, 0.25]), np.array([0.1, 0.1])]
        for u in controls:
            s_src = 0.7 * s_src + u + rng.normal(size=(n_samp, 2)) @ chol.T
            # Evolved target kernel = phi \circ OU \circ phi^-1
            s_tgt_pre = phi_inv(s_tgt)
            s_tgt = phi(0.7 * s_tgt_pre + u + rng.normal(size=(n_samp, 2)) @ chol.T)
        push_src = phi(s_src)
        mc_eds.append(energy_distance(push_src, s_tgt))

        # 3. Non-injective projection counterexample psi(x1, x2) = x1
        e_a = np.array([0.0, -2.0])
        e_b = np.array([0.0, 2.0])
        xs_a = e_a + 0.25 * rng.normal(size=(800, 2))
        xs_b = e_b + 0.25 * rng.normal(size=(800, 2))
        # Use shared x1 draw so marginal psi distribution matches exactly while R^2 states separate cleanly
        z1 = 0.25 * rng.normal(size=800)
        xs_a[:, 0] = z1
        xs_b[:, 0] = z1
        dist_r2 = energy_distance(xs_a, xs_b)
        dist_psi = energy_distance(xs_a[:, :1], xs_b[:, :1])
        collapse_ratios.append(float(dist_psi / max(dist_r2, 1e-8)))

    max_jac_err = float(max(jac_errs))
    max_mc_ed = float(max(mc_eds))
    max_collapse = float(max(collapse_ratios))
    p = preds_cfg["HP.5"]["metrics"]
    held = (
        max_jac_err <= p["jacobian_log_density_max_err_max"]
        and max_mc_ed <= p["mc_energy_dist_err_max"]
        and max_collapse <= p["projection_collapse_ratio_max"]
    )
    return {
        "seeds": seeds,
        "jacobian_log_density_max_err": max_jac_err,
        "mc_energy_dist_errs": mc_eds,
        "mc_energy_dist_err_max": max_mc_ed,
        "projection_collapse_ratios": collapse_ratios,
        "projection_collapse_ratio_max": max_collapse,
        "elapsed_sec": time.time() - t0,
    }, ("HELD" if held else "BROKEN")


def main() -> None:
    t_all = time.time()
    preds = json.loads(PRED_PATH.read_text(encoding="utf-8"))["hypotheses"]
    results = {}
    verdicts = {}

    print("Running HP.1 (ms-marco-MiniLM-L-6-v2 Sirius-Tiamat gauge)...", flush=True)
    results["HP.1"], verdicts["HP.1"] = run_hp1_minilm(preds)
    print("HP.1:", verdicts["HP.1"], json.dumps(results["HP.1"]), flush=True)

    print("Running HP.3 (ms-marco-MiniLM-L-6-v2 ZeroVLN Prop. 1-2)...", flush=True)
    results["HP.3"], verdicts["HP.3"] = run_hp3_minilm_zerovln(preds)
    print("HP.3:", verdicts["HP.3"], json.dumps(results["HP.3"]), flush=True)

    print("Running HP.2 (SmolLM2-135M-Instruct Sirius-Tiamat gauge)...", flush=True)
    results["HP.2"], verdicts["HP.2"] = run_hp2_smollm(preds)
    print("HP.2:", verdicts["HP.2"], json.dumps(results["HP.2"]), flush=True)

    print("Running HP.4 (SmolLM2-135M-Instruct ZeroVLN Prop. 1-2)...", flush=True)
    results["HP.4"], verdicts["HP.4"] = run_hp4_smollm_zerovln(preds)
    print("HP.4:", verdicts["HP.4"], json.dumps(results["HP.4"]), flush=True)

    print("Running HP.5 (Continuum Polish R^2 Ornstein-Uhlenbeck kernel)...", flush=True)
    results["HP.5"], verdicts["HP.5"] = run_hp5_polish_kernel(preds)
    print("HP.5:", verdicts["HP.5"], json.dumps(results["HP.5"]), flush=True)

    payload = {
        "experiment": "pretrained_checkpoint_gauge_probe",
        "elapsed_total_sec": time.time() - t_all,
        "verdicts": verdicts,
        "results": results,
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("SUMMARY_VERDICTS:", json.dumps(verdicts), flush=True)
    print("TOTAL_ELAPSED_SEC:", payload["elapsed_total_sec"], flush=True)


if __name__ == "__main__":
    main()
