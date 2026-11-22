# Source Triage & Utilization Matrix (2026-11-22)

Complete 4-tier evaluation of all **49 entries** supplied on 2026-11-22 across **Semplex** (formal & empirical Master Principle), **Synesism**, **Egon / Mouseion / AI-Ensemble**, and **Background / Skip**, correcting malformed URLs (`arxivb.org` → `arxiv.org`, `hhttps://` → `https://`) and noting duplicate links (`#5` and `#38` are the same work).

---

## Tier 1 — Immediate Semplex Action (Formalized in Lean &/or Tested Empirically Now)

| # | Source (Corrected) | Title / Topic | Target | Action Taken on `gemini/master-principle-ghsrt` |
|---:|---|---|---|---|
| 3 | Frobenius structures & monoid laws | Frobenius monoids in CQM / 2D TQFT / linear logic ($\Delta\circ\mu = (\mu\otimes \mathrm{id})(\mathrm{id}\otimes \Delta) = (\mathrm{id}\otimes \mu)(\Delta\otimes \mathrm{id})$) | Semplex | **Formalized** in `MasterPrincipleGHSRT.lean` (`frobMul_assoc`, `frob_law_left`, `frob_law_right`, `frob_special`, `s3_frob_noncommutative`) and numerically audited to `< 1e-12` on `S3`, `D4`, `A4`. |
| 11 | `https://arxiv.org/abs/2608.26631v1` | *Quantales as formal concept lattices* (Lili Shen, Xiaojuan Zhao) | Semplex | **Formalized** Galois concept quantale (`ConceptQuantale`: `cMul_assoc`, `cMul_one`, `one_cMul`, `cMul_sSup_left/right`, `cMul_le_iff_le_resRight/Left`) + numerically verified finite residuation. |
| 5 & 38 | `https://www.alphaxiv.org/abs/2611.jepa-latent-maps-content-geometry` & `https://cdn.agenticlearning.ai/25c41dcbc4b7a11e/content-geometry-tradeoff-2026.pdf` | *The Content–Geometry Tradeoff in World Models: When JEPA Learns Latent Maps* (Mengye Ren, Ying Wang, Christopher Hoang, Yilun Kuang, Yann LeCun) | Semplex | **Tested directly** in `master_principle_ghsrt.py` Arm 2 (`jepa_sg` vs `jepa_svreg` vs `jepa_slow_svreg`) against `G_gm_heat(λ)` and `X_kl_gm(λ)` on dual-timescale monoids. (`#5` = alphaXiv landing page, `#38` = 34-page PDF.) |
| 23 | `https://arxiv.org/abs/2611.21596` | *SADL: On the Demand-Supply Geometry of Representation Collapse* (Junhan Sun et al.) | Semplex | **Tested directly** in Arm 2 (`jepa_sadl`: encoder pairwise-difference supply vs projector demand) alongside `SVReg` and `Slow SVReg`. |
| 17 | `https://arxiv.org/abs/2611.11020` | *Unified Factored Representations Resist Catastrophic Forgetting* (Joel Lehman, Kenneth O. Stanley) | Semplex | **Tested directly** in Arm 1 Phase-2 (`retention_keep` / `forgetting_drop` comparing `UFR` homomorphic `U(d)` vs `FER` lookup `U(d)`). |
| 43 | `https://arxiv.org/abs/2611.11862` | *Are UFOs Real? Introducing Unified Factored Organizers* | Semplex | **Paired benchmark with #17:** directly isolates whether low-loss `cayley_unitary_fer` learns a fractured table vs true homomorphism `UFR`. |
| 46 | `https://arxiv.org/abs/2611.24032` | *Test-Time Symmetrization: Scaling Laws for Model-Agnostic Learning under Structure* (Behrooz Tahmasebi, Melanie Weber) | Semplex | **Tested directly** in Arm 1 (`ordered_gru` / `joint_bouquet_gru` evaluated over `K ∈ {1, 2, 4, 8, 16}` random gauge-conjugation + cyclic-shift rewritings). |
| 26 | `https://github.com/galilai-group/counterfactual-WM` | *Counterfactual World Models* (action-counterfactual JEPAs) | Semplex | **Operationalized** as the 2-step composition consistency signal (`||U_a U_b - U_{ab}||_F^2`) grounding dynamic homomorphism learning in Arm 1. |

---

## Tier 2 — High-Value Queue Next (Semplex & Synesism Math/Theory)

| # | Source | Title / Topic | Target | Planned Integration |
|---:|---|---|---|---|
| 15 | `https://arxiv.org/abs/2610.12426` | *Lyapunov spectrum of random neural networks* (David G. Clark) | Semplex | Connect minimum-norm tangent-space response function cleanly to heat-filtered Gramians `W_c(λ), W_o(λ)` in continuous RNN regimes. |
| 31 | `https://eccc.weizmann.ac.il/report/2026/323/` | *NL = UL* (William Hoza, Nov 2026) | Semplex | Apply `O(log(wn))`-seed min-isolating weights to deterministic tie-breaking of spanning trees in bounded-width graphs (`ConstructiveTree`). |
| 6 | `https://arxiv.org/abs/2605.10878` | *Minimum Neural Weight Norm = Kolmogorov Complexity* | Semplex | Charter / complexity bridge linking constant-precision looped weight norms to minimal semantic description length (`FOUNDATIONS.md`). |
| 4 | `https://arxiv.org/abs/2602.15029` | *Symmetry in language statistics shapes the geometry of model representations* (Dhruva Karkada et al.) | Semplex | Prior-art citation showing statistical translation symmetry generates circular/manifold codes (explaining Fourier rings & gauge representations). |
| 16 | `https://arxiv.org/abs/2611.10501` | *Sampling Is Not Curiosity: Why LLM Agents Should Investigate* (Alfonso Amayuelas et al.) | Semplex / Egon | Sharpens Task 143 distinction between passive observational probes and active interventional probes (`SemanticGroundingBridge`). |
| 20 | `https://arxiv.org/abs/2511.10971` | *ERMoE: Eigen-Reparameterized Mixture-of-Experts* | Semplex | Spectral alignment between router logits and expert internal eigenbases; candidate for multi-expert gauge routing probes. |
| 27 | `https://arxiv.org/abs/2608.11746` | *Epiplexity Guided Data Selection and Generation for OOD Generalization* | Semplex / Egon | Structural-information data valuation for training OOD circuit composition; complements `UFR` inductive bias. |
| 29 | `https://arxiv.org/abs/2606.07166` | *Cyclic proofs in the equational version of Primitive recursive arithmetic* | Synesism / Semplex | Non-automata structural cyclic proof theory; relevant to Synesism `P0` induction & loop coherence. |
| 32 | `https://github.com/leanprover/con-leche` | *con-leche: external Lean checker with consistency proof* | Synesism / Semplex | Trusted-kernel verification baseline for external proof auditing alongside Lean 4 + LRAT. |
| 39 | `https://arxiv.org/abs/1609.07152` | *Input Convex Neural Networks* (Amos, Xu, Kolter) | Semplex | Foundational prior-art citation for convexity in variational energy minimization (`kl_free_energy_trace_convex`). |
| 40 | `https://arxiv.org/abs/2202.00665` | *Tutorial on amortized optimization* (Brandon Amos) | Semplex | Prior-art citation for framing forward neural encoders as amortized free-energy/Riccati solvers. |
| 45 | `"The contingent HOD dichotomy"` | *The contingent HOD dichotomy* (Joel David Hamkins, Bokai Yao) | Synesism | Direct ATLAS comparative case (`Ultimate L` vs generic-multiverse closeness to `HOD` under forcing invariance). |
| 49 | `https://writings.stephenwolfram.com/2022/03/the-physicalization-of-metamathematics-and-its-implications-for-the-foundations-of-mathematics/` | *The Physicalization of Metamathematics...* (Stephen Wolfram) | Synesism / Semplex | Philosophical & multiway-graph precedent (observer-relative slices of ruliad vs grounded probe profiles). |
| 34 | `https://youtu.be/EY0nrb7AXJs` | *Agency & Intelligence Across Scales* (Michael Levin, Karl Friston, Chis-Ciure) | Semplex / Synesism | Active Inference / Markov-blanket conceptual synthesis with `Matrix-KL` variational free energy. |

---

## Tier 3 — Route to Egon / AI-Ensemble / Synesism / Cross-Domain Systems

| # | Source | Title / Topic | Target | Recommended Routing via Egon Mind |
|---:|---|---|---|---|
| 1 | `https://arxiv.org/abs/2611.18856` | *Self-Improvement Memory Enables Continual Recursive Self-Improvement* (SIM) | Egon (`ai-ensemble/ledger`) | Directly maps onto Egon's `ledger/autoresearch.py` to persist why harness edits worked/failed across benchmarks and models. |
| 48 | `https://arxiv.org/abs/2611.24357` | *Semantic Context Handoff with On-Demand Evidence* (SCH) | Egon (`Context Broker v2`) | State–evidence separation (`+6.9` Pass@1 with `-43%` tokens); aligns cleanly with `SemanticFibrations` + capsule memory. |
| 42 | `https://arxiv.org/abs/2611.25123` | *Forget Freely, Grep Later: Lossless, Index-Free Memory* (GrepMem) | Egon / Memory | Validates Egon append-only timeline + regex recall (`timeline.db`) against lossy auto-summarization. |
| 44 | `https://github.com/VectifyAI/PageIndex` | *PageIndex: Vectorless, Reasoning-based RAG* | Mouseion / Egon | Candidate tree-structured document indexer for Mouseion full-text PDFs instead of flat chunking alone. |
| 28 | `https://github.com/y5ez3g/facadecode` | *Facade Code: multi-agent VS Code orchestrator* | AI-Ensemble | Inspect patterns for cross-CLI orchestration UX; compare against `ai-ensemble` / Egon orchestrator. |
| 9 | `https://github.com/PufferAI/PufferLib/blob/5.0/SKILL_ISSUES.md` | PufferLib engineering / refactoring guide | Coding Practice | Useful code-hygiene reference: inline once-used helpers, preserve determinism, cut indirection. |
| 47 | `https://arxiv.org/abs/2611.24347` | *automodel: A Skill for Agentic Model Discovery* | Egon Skills | Pattern for packaging iterative scientific/ML hypothesis-search loops as agent skills. |
| 19 | `https://www.alphaxiv.org/abs/2611.composable-soft-prompt-distillation` | *Composable Soft-Prompt Distillation of RL Experts* | AI-Ensemble / Future | Modular adapter composition across continually arriving domain experts. |
| 25 | `https://github.com/csinva/weight-space-programming-autoresearch` | *Interpretable weight-space programming* | Semplex / Interp | Human/agent-written interpretable weight modules; shares spirit with exact compiled circuits. |
| 2 | `https://www.science.org/doi/10.1126/sciadv.aej5555` | *Cross-domain neural representations across language and mathematics* (*Science Advances* 2026) | Synesism / Cognitive | Empirical fMRI evidence distinguishing shared vs domain-specific representations across language & math. |
| 7 | `https://iopscience.iop.org/article/10.1088/3050-287X/aeb27b` | *Reading and steering representations of materials-science mechanisms* (M. J. Buehler 2026) | Semplex / Interp | Constitutive directional laws encoded in state transitions + causal activation steering. |
| 10 | `https://arxiv.org/abs/2611.24598` *(fixed from `arxivb.org`)* | *Chain-of-Thought Hidden States Reveal Task-Solving Directions for Direct Answers* | Interp / Inference | Single pre-generation state rotation recovers CoT gains at 1/10 tokens (geodesic shortcut in representation space). |
| 22 | `https://hyperthink-llm.github.io/` | *HyperThink: Text-to-Parameter Hypernetworks for Efficient Reasoning* | Semplex / Fast Weights | Amortizing reasoning into generated parameters relates to task-conditioned dynamical maps. |
| 37 | `https://academic.oup.com/brain/advance-article/doi/10.1093/brain/awag325/9016667` *(fixed from `hhttps://`)* | *The hippocampus as a latent diffusion engine...* (*Brain* 2026) | Synesism / Bio-Memory | Generative latent-diffusion view of biological memory consolidation & dysfunction. |

---

## Tier 4 — Background / Skip for Current Master Principle Campaign

| # | Source | Title / Topic | Reason for Skipping Now |
|---:|---|---|---|
| 8 | `https://link.aps.org/pdf/10.1103/PhysRevLett.116.178101` | *Untangling Knots Via Reaction-Diffusion Dynamics* (Maucher & Sutcliffe 2016) | Rich PDE analogy for topology-preserving simplification, not needed for discrete finite monoid / GHSRT core. |
| 12 | `https://github.com/suayptalha/neural-ecosystem-atlas` | *Neural Ecosystem Atlas* (`Qwen3.5-0.8B` pairwise block ablations) | Exploratory mechanistic case study; useful background, orthogonal to theorem/operator benchmarks. |
| 13 | `https://arxiv.org/abs/2611.24980` | *DL101 The Representation Capability of Neural Network Models* | Textbook UAT survey (Cybenko/Hornik/Leshno); already baseline background. |
| 14 | `https://github.com/rohitgandikota/vlm-planning` | *How VLMs Plan What's Next* (`arXiv:2611.21600`) | Vision-language attention lookahead study; domain-specific VLM mechanics. |
| 18 | `https://aclanthology.org/2026.findings-emnlp.2039/` | *Iterative Natural Logic Verification for Multi-hop QA* | Applied NLP pipeline for multi-hop QA verification. |
| 21 | `https://github.com/camail-official/LoReS` | *Quantizing recurrent language models is easier than you think* (`arXiv:2611.01864`) | Systems/KV-state low-bit quantization technique; not core theory right now. |
| 24 | `https://www.alphaxiv.org/abs/2611.13378` | *Looping Deeper Without Growing the KV Cache* | Serving/memory optimization for looped encoder-decoders. |
| 30 | `https://github.com/SqueezeAILab/2DSD` | *2DSD: Two-Dimensional Speculative Decoding for Looped LLMs* | Inference-speed decoding engineering for looped LLMs. |
| 33 | `https://arxiv.org/abs/2611.26627` *(fixed from `arxivb.org`)* | *RL Post-Training in Diffusion Transformers Is Activation Steering* | Diffusion-transformer post-training mechanics; outside finite monoid/GHSRT scope. |
| 35 | `https://www.alphaxiv.org/abs/2611.feedback-shortcut-speculative-decoding` | *Feedback Shortcut: Speculative Decoding for Latent Feedback Transformers* | Draft/verify serving speedups for recurrent Transformers. |
| 36 | `https://arxiv.org/abs/2611.24301v1` | *LoopCache: Accelerating Long-Context Self-Speculative Decoding* | KV-cache wave scheduling for looped Transformers. |
| 41 | `https://arxiv.org/abs/2605.06548` | *Continuous Latent Diffusion Language Model* (`Cola DLM`) | Non-autoregressive latent text diffusion architecture. |

---

## Summary Accounting
- **49 user prompt items checked (`1–49`)** = **48 distinct works** (`#5` and `#38` point to the same paper by Ren & LeCun 2026).
- **8 entries (7 distinct works)** integrated directly into the **Lean 4 formalization & 48-run empirical campaign** on `gemini/master-principle-ghsrt`.
- **14 entries** queued into Semplex/Synesism formal & literature roadmap (`charter/REFERENCES.md` candidates).
- **14 entries** routed cleanly via Egon Mind to Egon / Mouseion / AI-Ensemble / Synesism without distracting the Semplex Master Principle track.
- **12 entries** triaged as Background/Skip.
