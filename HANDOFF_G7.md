# HANDOFF G7 — Gap D3: Full-Text Prior-Art & 8-Area Literature Audit

**Branch:** `gemini/G7` (cut cleanly from `262281e`)
**Scope:** Complete `charter/PRIOR_ART.md` §4 reading queue + 8 extended literature areas (`charter/LITERATURE_REVIEW.md` §5, `charter/PRIOR_ART.md` §1/§4/§5, `claims/PROPOSED.md`). No frozen files (`THEORY.md` §5, `claims/GAPS.json`, `claims/REGISTER.md` statuses, `experiments/FROZEN.json`) were modified, and no `Pnnn` claim IDs were assigned.

---

## ⚠️ Papers Already Containing or Anticipating Our Results

The following papers, verified in full LaTeX source or section reads during `G7`, already contain, anticipate, or tightly bound core semplex results. **Do not claim novelty over these without the narrowed scope in `claims/PROPOSED.md`:**

1. **Bayes-Sufficient Representations Strictly Anticipate `R1` (`THEORY §2`, `P031`) — Sevetlidis, `arXiv:2606.04045` (Full text)**
   - **Finding:** Under an almost-surely unique Bayes action, Bayes-sufficient representations are *precisely* refinements of the Bayes quotient, and minimal Bayes-sufficient representations are unique up to `\sigma`-equivalence (`templateArxiv.tex` Abstract L74; `thm:bayes-quotient-main` L205–223; `cor:minimal-unique-app` L841–849).
   - **Surviving novelty:** Finite Boolean conflict-hypergraph minimal-hitting-set duality + solver-certified threshold circuit synthesis + Lean 4 checking.
2. **Computational Mechanics Strictly Anticipates `P028`, `P031`, `R1` on Processes & Transducers — Shalizi & Crutchfield `arXiv:cond-mat/9907176`, Barnett & Crutchfield `arXiv:1412.2690`, Rosas, Boyd & Baltieri `arXiv:2504.04608` (all Full text)**
   - **Finding:** `\epsilon`-machines and `\epsilon`-transducers establish maximal prescience, minimal conditional statistical complexity, and uniqueness up to isomorphism (`cmppss-arxiv.tex` L80–83, L1579, L1646; `et1.tex` L1806, L1924, L1962; `2504.04608/main.tex` `theo:Predictive Transducer Coarse-Graining` L803). `2504.04608` also proves non-uniqueness of generic minimal world-model transducers (`Abstract` L148), paralleling `P029`/`P144`.
3. **Independent Co-Discovery of Blocking-Set / MHS Duality (`P004`, `P027`, `THEORY §3.2`) — Hadad, Katz & Bassan, `arXiv:2602.16823` / ICLR 2026 (Full text)**
   - **Finding:** `iclr2026_conference.tex` `lem:blocking_sets_equivalence` (L2786–2791) and `mhs_main_theorem_appendix` (L2806–2829) independently publish the exact equivalence between monotone blocking sets and circuit faithfulness, with the minimum hitting set yielding a cardinally minimal faithful circuit.
   - **Differentiation:** `2602.16823` prunes existing continuous DNNs; semplex synthesizes globally minimum Boolean threshold circuits on care sets and verifies proofs inside Lean 4.
4. **Unconstrained `R2` Refuted by Nonlinear Alignment Triviality — Sutter, Minder, Hofmann & Pimentel `arXiv:2507.08802` (Full text); Tightened by Zaghw, Brendel & Reizinger `arXiv:2610.18155` (Full text)**
   - **Finding:** `2507.08802` (`theorem:existing_causalmap_for_any_algorithm`, `main.tex` L579–581) proves *any* layer-injective, output-surjective task-solving network can be mapped to *any* compatible algorithm with arbitrary alignment maps. `2610.18155` (`thm:maximality`, `theory.tex` L115–121) shows constructive abstraction preservation holds iff `$T=\sigma\circ D$` (block permutation × block-diagonal invertible map).
   - **Also on `P144`:** `Cifuentes arXiv:2608.20428` (Full text) proves additive `\varepsilon`-reduction composition (`\varepsilon_1+\varepsilon_2`, `prop:compose_approx_homo`) and Bayesian predictive-residual stability (`thm:predictive-residual-stability`), parallel to `queryApprox_comp`.
5. **`H45.4` / `P155`–`P159` (`R3`) Directly Anticipated Under Label Noise — Mingard et al. `arXiv:2006.15191`, Manoj & Srebro `arXiv:2302.07263`, Harel et al. `arXiv:2410.19092`, Chatterjee & Sudijono `arXiv:2409.12446` (all Full text)**
   - **Finding:** `2006.15191` (`appendices.tex` §E L724–726) already shows GP beating SGD under 20% label noise (`"\varepsilon_{G,GP}=5.80\%"` vs `"\varepsilon_{G,SGD}=13.4\%"`, target mass `99.3%` vs `24.3%`). `2302.07263` and `2410.19092` prove tempered overfitting bounds `1-2^{-H(\eta)}` and `2\eta(1-\eta)` for minimal/MDL interpolators; `2409.12446` proves `C\rho + O(1/n)` (while explicitly omitting gradient dynamics in §7).
   - **Unforced/early-stopped regimes (`Gap A8`):** `Boursier & Flammarion 2410.02348` (`thm:noconvergence`) shows unforced small-init GF avoids noise interpolation above `n >= \Theta(d^3\log d)`, and `Boncoraglio & Zdeborová 2610.33846` derives the exact critical kernel angle `\gamma_c(\varepsilon)`.
6. **`Theorem 15` (`P069`) Subsumed by Equivariance Theory — Yang & Ziyin `arXiv:2512.21447`, Ziyin et al. `arXiv:2502.05300` (both Full text)**
   - **Finding:** `2512.21447` (`thm:main-discrete` L321–342) and `2502.05300` (`theo: complexity` L363–365) already prove general discrete/continuous gradient & Hessian equivariance and reduced-parameter symmetry dynamics. `P069` (`gemini/G1`) is an input-symmetry instantiation mechanized in Lean. Quantitative Curie orbit exponents (`Gap A3`) remain open.
7. **`C15'` (`P094`, `P111`) & `C18` (`P121`) Restricted by Optimizer & Feature-Quality Caveats — Das et al. `arXiv:2605.29152`, Göring et al. `arXiv:2507.19680` (both Full text)**
   - **Finding:** `2605.29152` shows initialization-scale sensitivity (`26.5` pp under low-LR SGD at 5,000 epochs) is erased (`|\Delta|=0.0` pp) by Adam or tuned SGD+WD. `2507.19680` shows scalar kernel feature-learning norms (`S_{NT}`, `S_{CK}`, `\Delta_{NT}`) decouple from feature quality and fail to distinguish true vs shuffled labels at `\gamma=0.01`.
   - **Also on `P152` timing:** `Zhang, Saxe & Latham 2512.20607` and `Abbe et al. 2302.11055` (both Full text) partly anticipate early-to-late complexity progression via saddle-to-saddle and leap transitions.
8. **`Gap B2` Clarified: `2410.19092` Does NOT Give Lower Bounds & SoS Faces `\Omega(s^{1-\epsilon})` Barrier — Harel et al. `2410.19092` (Full text), Austrin & Risse `arXiv:2311.12994` (Abstract + sections)**
   - **Finding:** `2410.19092` `thm: partial fctn net cxty` (`01_main.tex` L410–431) proves an *upper* bound (existence of a depth-14 threshold net), NOT a lower-bound certificate. Meanwhile `2311.12994` (`abstract.tex` L3–6) proves Sum-of-Squares requires degree `\Omega(s^{1-\epsilon})` to certify Boolean circuit lower bounds (`s > \poly(n)`), blocking generic SDP/LP approaches and validating symmetry- and structure-driven Lean bounds (`gemini/G3`, `gemini/G5`).
9. **Automata Shortcuts Explain Finite-Horizon Isomers Failing Interventions (`R2`, `Gap A9`/`A10`, `P045`) & Symmetry-Belief Emergence Published — Liu et al. `arXiv:2210.10749` (Full text), Rosas `10.1126/sciadv.aeh0773` / `arXiv:2512.00984`**
   - **Finding:** `2210.10749` proves Transformers simulate any semiautomaton of horizon `T` in `O(\log T)` depth and any solvable semiautomaton in `O(1)` Krohn–Rhodes depth (`thm:shortcut-log-depth`, `thm:shortcut-const-depth`, `thm:barrington-lower-bound`), demonstrating how shallow shortcut isomers match on fixed `T` (`P045`) while failing OOD / causal state interventions (`R2`). Meanwhile `10.1126/sciadv.aeh0773` (*Science Advances*, Nov 13, 2026) publishes the journal expansion of `2512.00984` extending symmetry-subgroup emergence to autonomous hierarchies of partial-access Bayesian beliefs.
   - **Supplemental baselines & negative controls (see `claims/PROPOSED.md` §9):** `CRAM` (`2611.17309`, Potts energy descent for pairwise constraints), `WSP-Gym` (random weight-table edits `37.6%` tie LLM edits `38%` on `Qwen3.5-0.8B`), `2611.14418` / `2611.14413` (`P137` bit escalation & `P077`/`G4` $C_4$ cyclic orbit averaging), and Downey & Melnikov (Springer 2026, `Theorem A` / `Theorem B`) + Montalbán (`CSTpart1.pdf`) on effective Stone duality barriers for infinite frames (`P008`, `P009`).

---

## Read-Depth Inventory (`charter/LITERATURE_REVIEW.md` §5, lines 142–201)

Recorded **60 rows** in `charter/LITERATURE_REVIEW.md` §5 spanning **64 distinct works** (four rows pair two closely coupled references: `Blumer et al. 1987 + 1989` on line 187, `Hirahara, Ilango & Loff 2507.10426 + Hirahara & Ilango FOCS 2025` on line 191, `Montalbán 2019 + Downey & Melnikov 2026` on line 198, and `Marathe et al. 2609.12303 + Lin et al. 2611.16267` on line 201):

| Read Level | Count (Works) | Coverage |
|---|---:|---|
| `Full text` | **32** | All 21 arXiv papers in `PRIOR_ART.md` §4 (`2606.04045`–`2610.33846`) + 3 computational mechanics papers (`cond-mat/9907176`, `1412.2690`, `2504.04608`) + 8 supplemental works (`2210.10749`, `2611.17309`, `2611.14418`, `2611.14413`, `WSP-Gym`, `2601.06002`, `2609.12303`, `2611.16267`) |
| `Abstract + sections` | **18** | `2402.09090`, `2512.02193`, `2512.00984` / `10.1126/sciadv.aeh0773`, `2602.02385`, `2001.10387`, `1810.06986`, `2307.14855`, `2304.01481`, `1805.08651`, `2102.11107`, `1812.03789`, `1906.11583`, `2211.12270`, `2508.11214`, `1710.09806`, `2311.12994`, Montalbán `CSTpart1.pdf`, Downey & Melnikov (Springer 2026) |
| `Partial LaTeX source` | **1** | `2507.10426` (`01_preamble.tex`, `main.tex` L37–205) |
| `Abstract only` | **4** | `Pow 2026` (`10.68852/pf-261114.000002`), `Blumer et al. 1989`, `Kearns & Vazirani 1994`, `alphaXiv:2611.latent-feedback-transformers-scaling-law` |
| `Metadata only` (paywalled, no Crossref abstract) | **9** | `Ganter & Wille 1999`, `Pawlak 1982`, `Skowron & Rauszer 1992`, `Pawlak & Skowron 2007`, `Angluin 1987`, `Harnad 1990`, `Blumer et al. 1987`, `Hirahara & Ilango FOCS 2025`, `Ilango 2020` |
| **Total** | **64** | Across **60 rows** in `charter/LITERATURE_REVIEW.md` §5 |

Also corrected several misattributions from earlier index notes while checking primary sources: `2307.14855` (Victor Iwaniack, not Telle), `2211.12270` (Massidda, Geiger, Icard, Bacciu, not Zennaro), `2602.16473` (Jiang, Hague, Rümmer, Lin, not Yao), `1710.09806` (Allender, Grochow, van Melkebeek, Moore, Morgan), `2311.12994` (Austrin & Risse, not Atserias/Müller/Tzameret), and `2507.10426` (Hirahara, Ilango & Loff on deterministic communication complexity; separate from `Hirahara & Ilango` FOCS 2025 MCSP).

---

## Resolution Summary: `PRIOR_ART.md` §4, 8 Extended Areas & Supplemental Batch

- **`charter/PRIOR_ART.md` §1 & §4 updated:** Upgraded read levels to `(R)` across §1 verdicts, resolved all §4 queue rows (`Full text` / `Metadata only`), and added **§5 (Extended 8-area literature sweep + supplemental audit)** covering: (1) computational mechanics & emergent macro-models (`10.1126/sciadv.aeh0773`), (2) rough sets / FCA / active automata, (3) symbol & vector grounding / nonlinear ICA identifiability, (4) formal & approximate causal abstraction, (5) PAC/Occam & MCSP/SoS hardness, and (6) automata shortcut isomers (`2210.10749`), Potts energy descent (`2611.17309`), weight-space controls (`WSP-Gym`, `2611.14418`, `2611.14413`), and infinite-frame computable structure theory (Downey & Melnikov 2026, Montalbán `CSTpart1.pdf`).
- **`claims/PROPOSED.md` created:** Documents **9** concrete claim/boundary proposals (no `Pnnn` IDs assigned) for `R1`, `P004`/`P027`, `R2`/`Gap A9`–`A10`, `R3`/`H45.4`/`Gap A8`, `C15'`/`C18`/`C19'`, `Theorem 15`/`P069`, `Gap B2`, `Gap C1`/`P146`, and supplemental baselines/shortcuts/controls (§9), each with exact quoted evidence and explicit limits on what it does *not* establish.

---

## Rule 7 Verification (`gemini/G7`)

`cerp.register check` and `cerp.status --check` re-ran and passed (`EXIT:0`) after the final supplemental literature edits; `pytest` and the Lean 4 audits ran after zero code/`*.lean` changes (only markdown literature/proposal docs were added afterwards) using `$env:TEMP\semplex_extras_venv\Scripts\python.exe` and Lean 4.12 (`C:\Users\bruno\.elan\bin`):

1. **`python -m cerp.register check` & `git diff -w claims/LEDGER_CHECK.md` (re-run after final doc edits):**
   - Output: `0 problem(s), 37 status note(s); report: claims\LEDGER_CHECK.md` (`REG_EXIT:0`)
   - `git diff -w claims/LEDGER_CHECK.md`: empty (`DIFF_W_LEN:0`); restored via `git checkout -- claims/LEDGER_CHECK.md`.
2. **`python -m cerp.status --check` (re-run after final doc edits):** `STATUS_EXIT:0`.
3. **`& "$env:TEMP\semplex_extras_venv\Scripts\python.exe" -m pytest -q -k "not test_search_keeps_a_working_rule_working"`:**
   - Output: `153 passed, 1 deselected in 469.70s (0:07:49)` (`PYTEST_EXIT:0`).
   - Excluded test note: `tests/test_localrules.py::test_search_keeps_a_working_rule_working` is the pre-existing `262281e` non-deterministic initialization failure (`P149` pure-backprop init variance), diagnosed and fixed deterministically over a 5-seed batch on isolated sibling branch `origin/gemini/G6` (`4b0f36a`).
4. **Lean 4.12 compilation to `$env:TEMP\semplex_lean_olean` & axiom audits (`Cerp.lean`, `Theory.lean`, `Bounds.lean`, `Audit.lean`, `AuditTheory.lean`, `AuditBounds.lean`):**
   - Output: `SUMMARY rcs=(0,0,0,0,0,0) dt=63.05s leftover_olean=0`.
   - Every audited theorem depends only on `{}` or a subset of `[propext, Classical.choice, Quot.sound]`, with zero `sorryAx` and zero `Lean.ofReduceBool`.
