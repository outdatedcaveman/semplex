# Literature & Repository Integration Synthesis (2026-11-24)

This synthesis maps all 24 external manuscripts, journal articles, news reports, and open-source repositories reviewed alongside the Semplex–Synesism Master Principle closure (`gemini/master-principle-nitty-gritties`) onto formalized Lean 4 / Mathlib v4.12.0 / Cubical Agda 2.9.0 theorems and pre-registered empirical probes (`HNG.1`–`HNG.4`).

> **arXiv Interoperability Attribution:** All 16 arXiv preprint metadata records below were retrieved via the arXiv API (`https://info.arxiv.org/help/api/index.html`). Thank you to arXiv for use of its open access interoperability.

---

## 1. Thematic Mapping to the Semplex–Synesism Architecture

| Architecture Pillar | Core Semplex–Synesism Objects | Primary Literature / Repo Connections |
|---|---|---|
| **Symmetry Orbit Completeness, Bispectrum & Test-Time Invariance** | `G_rep -> G_prof`, `SemEquiv`, `ker(Obs_P)`, orbit averaging (`HNG.4`) | `geometric-intelligence/bispectrum`, `arXiv:2611.24032` (Tahmasebi & Weber), `arXiv:2611.19717` (German & Newton) |
| **External Grounding, Provenance & Framing Separation** | `PhysicalReference`, `ContextualSystem <-> ContextualRing`, `hallucination_fails_grounding` | `arXiv:2611.27016` (LEVER), PNAS Nov 2026 Zero-One System ID, `arXiv:2611.26935` (Self-Similar Language Information) |
| **Cohomological / Čech Descent & Filling Obstructions** | `CechNerveRingBridge.lean`, `HigherCechDescent.agda`, `ObstructionExactSequence.lean` | `arXiv:2611.27018` (Cheng ReLU Arithmetic Obstructions), `arXiv:2606.07166` (Shamkanov Cyclic PRA), Remmen `PRL 127.241602` |
| **Measurable Contraction, Dissipation & Non-Linear Dynamics** | `MeasurableDobrushinContraction.lean` (`measureTV`, `kernelDobrushinBound`), `HNG.2` | `arXiv:2611.26215` (Decoherence in Quantum Reservoirs), `arXiv:2611.29390` (Variational Liquid-Vapor), `S0005109823006507` (Extremum Seeking), SBM (`tullebulle.github.io/projects/sbm/`) |
| **Resource-Bounded Budgeted Probing, Memory & Frozen-Spine Adaptation** | `Budget <= B`, `MeMo`/frozen-backprop separation, `HNG.1` (`>=1B` gauge-tube sensitivity) | `arXiv:2605.15156` (MeMo), `arXiv:2611.26906` (BudgetPV), `arXiv:2611.27068` (DM-PRM), `arXiv:2508.16817` (DEER), `arXiv:2606.06479` (SMT), `arXiv:2605.06548` (Cola DLM), `qlabs-eng/noise`, `Louiealbp/DLMST`, `arXiv:2611.24980`, `arXiv:2611.25964`, `s41593-026-02517-4` |

---

## 2. Detailed Inventory (All 24 Sources)

### A. Sixteen arXiv Preprints (Metadata via arXiv API)

1. **`arXiv:2605.15156v2` (`https://arxiv.org/abs/2605.15156`, 2026-05-14)** — *MeMo: Memory as a Model* (Ryan Wei Heng Quek et al.).
   - **Core Finding:** Factors long-term adaptive parametric memory into a dedicated auxiliary module while keeping base backbone weights strictly frozen.
   - **Semplex–Synesism Tie-In:** Directly aligns with return-only / frozen-backbone orthogonal adaptation (`HQS.4`, zero regression on Task A) and modular `ContextualRing` patching (`CechNerveRingBridge.lean`) where an external module absorbs updates without mutating base gauge fibers.

2. **`arXiv:2611.26215v1` (`https://arxiv.org/abs/2611.26215`, 2026-11-19)** — *To predict or to persist: how decoherence shapes learning in a spin-qubit quantum reservoir* (Nikolaos Petropoulos, Elena Blokhina).
   - **Core Finding:** Studies how Markovian dephasing/dissipation shapes fading-memory contractions vs persistence across single- and two-qubit readouts.
   - **Semplex–Synesism Tie-In:** Sharpens the operational trade-off inside `MeasurableDobrushinContraction.lean`: contractive `c < 1` stabilizes horizon errors (`measurable_dobrushin_horizon_stability`) at the cost of exponential attenuation `c^T d_0` of initial-state memory, whereas `c -> 1` preserves long-horizon state discrimination (`nonexpansive_horizon_bound`).

3. **`arXiv:2611.24980v1` (`https://arxiv.org/abs/2611.24980`, 2026-11-17)** — *DL101 The Representation Capability of Neural Network Models* (Fernando Berzal).
   - **Core Finding:** Synthesizes universal approximation criteria (Cybenko/Funahashi/Hornik/Leshno) for non-polynomial activations.
   - **Semplex–Synesism Tie-In:** Confirms that expressive capacity in width/depth alone is non-unique up to representation isotropy; uniqueness requires external anchoring (`ae_product_anchor_kernel_inter`) rather than approximation expressivity alone.

4. **`arXiv:2611.25964v1` (`https://arxiv.org/abs/2611.25964`, 2026-11-19)** — *A New Quantum Algorithm Framework for Integer Order Entropy Estimation* (Zongxing Xiong).
   - **Core Finding:** Establishes query-complexity bounds for integer-order (`k >= 2`) Rényi entropy estimation.
   - **Semplex–Synesism Tie-In:** Complementarity to `budget`-indexed classical operational profiles (`MonotoneRepMap`, `Budget <= B`): finite resource bounds determine which moments/observables distinguish underlying states.

5. **`arXiv:2611.26906v1` (`https://arxiv.org/abs/2611.26906`, 2026-11-19)** — *Budget-Aware Predict-and-Verify Theorem Proving with Heterogeneous LLM Solvers (BudgetPV)* (Wei Jiang et al.).
   - **Core Finding:** Allocates verification compute dynamically across heterogeneous formal solvers under explicit budget constraints.
   - **Semplex–Synesism Tie-In:** Operational realization of heterogeneous budgeted probing across distinct representation solvers (`MonotoneRepMap` cost scaling `c'(g a) <= scale * c(a)`).

6. **`arXiv:2611.26935v1` (`https://arxiv.org/abs/2611.26935`, 2026-11-20)** — *Self-similar Organization of Information in Language* (Leon Lufkin, Cutter Dawes, Kamesh Krishnamurthy).
   - **Core Finding:** Demonstrates multi-scale self-similar distribution of predictive information along natural-language histories.
   - **Semplex–Synesism Tie-In:** Explains empirically why multi-scale Hankel/context-window profiles carry predictive signal across horizons, motivating our arbitrary-depth measurable kernel composition (`measurable_dobrushin_comp`) and `>=1B` multi-layer sensitivity sweep (`HNG.1`).

7. **`arXiv:2611.29390v1` (`https://arxiv.org/abs/2611.29390`, 2026-11-22)** — *Thermodynamically consistent variational formulation and structure-preserving FEM for non-isothermal liquid-vapor flows* (Junkai Wang et al.).
   - **Core Finding:** Enforces entropy/thermodynamic structural conservation across discrete variational finite-element patch discretizations.
   - **Semplex–Synesism Tie-In:** Mirrors structure-preserving gluing over overlapping local patches (`partition_of_unity_glues_overlaps` in `CechNerveRingBridge.lean`), preventing spurious numerical dissipation/creation at patch overlaps.

8. **`arXiv:2606.07166v1` (`https://arxiv.org/abs/2606.07166`, 2026-06-05)** — *Cyclic proofs in the equational version of Primitive recursive arithmetic* (Daniyar Shamkanov).
   - **Core Finding:** Constructs an infinite-branch structural cyclic proof calculus without finite-automata side-conditions.
   - **Semplex–Synesism Tie-In:** Connects directly to cycle monodromy / `H^1` gluing (`ObstructionExactSequence.lean`, `cech_specker_c4_obstruction`): cyclic derivations must satisfy a global progress/trivial-holonomy condition to descend to well-founded global objects.

9. **`arXiv:2611.24032v1` (`https://arxiv.org/abs/2611.24032`, 2026-11-18)** — *Test-Time Symmetrization: Scaling Laws for Model-Agnostic Learning under Structure* (Behrooz Tahmasebi, Melanie Weber).
   - **Core Finding:** Proves sample-complexity / MSE scaling gains from test-time orbit averaging `|G|^{-1} sum_{g in G} f_hat(g . x)` over representation relabelings without changing training architecture.
   - **Semplex–Synesism Tie-In:** Directly tested in `HNG.4` (`sym_orbit_variance_max`, `sym_mse_ratio`): averaging across a discrete gauge group orbit eliminates internal gauge-orbit variance while preserving true invariant signal.

10. **`arXiv:2611.19717v1` (`https://arxiv.org/abs/2611.19717`, 2026-11-15)** — *Fixed Points as Programs: Finite Symmetry and One-Shot State-Gate Duality in the Misty-State Calculus* (Dan-Adrian German, Tony Newton).
    - **Core Finding:** Encodes programs as finite unitary group orbit clouds with state-gate duality.
    - **Semplex–Synesism Tie-In:** Finite-group orbit representation resonates with our `CausalCoalgebra` automorphism groupoid (`boolFlipPath!=refl`, `BGClassifyingSpace.agda`), while our Lean/Agda formalization additionally handles partial anchor stabilization and continuous measurable orbits.

11. **`arXiv:2605.06548v1` (`https://arxiv.org/abs/2605.06548`, 2026-05-07)** — *Continuous Latent Diffusion Language Model (Cola DLM)* (Hongcan Guo et al.).
    - **Core Finding:** Replaces discrete token-by-token diffusion with continuous latent Markov denoising dynamics.
    - **Semplex–Synesism Tie-In:** Reinforces the necessity of generalizing finite-state Dobrushin contractions (`[Fintype α]`) to arbitrary continuous measurable Markov kernels (`MeasurableDobrushinContraction.lean`) for continuous-latent sequence models.

12. **`arXiv:2611.27016v1` (`https://arxiv.org/abs/2611.27016`, 2026-11-20)** — *Same Facts, Different Decision: Fact-Invariant Manipulation and Provenance-Based Defense in Typed Decision Models (LEVER)* (Yujie Wang et al.).
    - **Core Finding:** Demonstrates that framing manipulations holding fixed internal structural facts still invert downstream model decisions unless defended via explicit external provenance.
    - **Semplex–Synesism Tie-In:** Direct empirical parallel to `ContextualRingDescent.hallucination_fails_grounding` and `CechNerveRingBridge.contextualSystem_hallucination_separation`: internal coalgebra isomorphism without external physical provenance does not preserve truth.

13. **`arXiv:2611.27018v1` (`https://arxiv.org/abs/2611.27018`, 2026-11-20)** — *Integral Multipliers and Arithmetic Obstructions for Two-Hidden-Layer ReLU Maxima* (Pengcheng Cheng).
    - **Core Finding:** Identifies sharp cohomological / integer-multiplier filling obstructions in piecewise-linear two-layer neural function spaces.
    - **Semplex–Synesism Tie-In:** Direct finite-neural analog of local compatibility failing global realization (`cech_specker_c4_obstruction`, `FiberObstructionSequence.agda`, `HigherCechDescent.agda` higher-horn vs global coherence separation).

14. **`arXiv:2508.16817v4` (`https://arxiv.org/abs/2508.16817`, 2025-08-22)** — *Predictability Enables Parallelization of Nonlinear State Space Models* (Xavier Gonzalez et al.).
    - **Core Finding:** Uses fixed-point parallel Newton/Picard solvers (DEER/DeepPCR) over nonlinear state-space recurrences; convergence relies on local Jacobian/Lipschitz contractivity along trajectories.
    - **Semplex–Synesism Tie-In:** Connects temporal contraction (`measurable_dobrushin_horizon_stability`) to parallelizable trajectory solving: contractive recurrences guarantee uniform fixed-point error bounds across sequence length.

15. **`arXiv:2606.06479v3` (`https://arxiv.org/abs/2606.06479`, 2026-06-04)** — *Pretraining Recurrent Networks without Recurrence (Supervised Memory Training, SMT)* (Akarsh Kumar, Phillip Isola).
    - **Core Finding:** Decouples state-memory readout supervision from sequential backpropagation through time.
    - **Semplex–Synesism Tie-In:** Consistent with Hankel/Markov readout separability: once sufficient state-space realizations are sampled across reachable trajectories (`ReachableOutcome`), transition dynamics can be reconstructed without unrolling full gradient histories.

16. **`arXiv:2611.27068v1` (`https://arxiv.org/abs/2611.27068`, 2026-11-20)** — *Decision Models Are General-Purpose Process Reward Models (DM-PRM)* (Jiajun Fan et al.).
    - **Core Finding:** Repurposes trajectory-level decision models as step-wise process evaluators over partial execution traces.
    - **Semplex–Synesism Tie-In:** Operationalizes local step-level consistency checks (`Cech1`/`Cech2` compatibility and one-step stability `measurable_dobrushin_one_step_stability`) as process constraints guaranteeing global trajectory quality.

---

### B. Three Open-Source Repositories

17. **`geometric-intelligence/bispectrum` (`https://github.com/geometric-intelligence/bispectrum`)** — *Fast, exact, lossless symmetry invariants for PyTorch* (NeurIPS 2026).
    - **Relevance:** Computes group bispectra yielding complete (lossless up to orbit) polynomial invariants on finite cyclic/dihedral and continuous groups—eliminating the phase-blindness of second-order power spectra (`HNG.4` explicit `(sig_plus, sig_minus)` separator).
    - **Demarcation:** Provides constructive harmonic invariants per fixed symmetry group `G`; Semplex adds coalgebraic causal dynamics equivalence (`SemEquiv`), `ker W` gauge-tube perturbation bounds, and cohomological gluing obstructions across heterogeneous patched charts.

18. **`qlabs-eng/noise` (`https://github.com/qlabs-eng/noise`)** — *Speedrun for pretraining without backpropagation*.
    - **Relevance:** Evaluates zeroth-order / forward-only weight perturbations at scale, highlighting directional finite-difference estimators as low-memory probes of weight sensitivity (`HNG.1` directional derivative `Gamma_mod` using `eps=0.25` without `.backward()`).

19. **`Louiealbp/DLMST` (`https://github.com/Louiealbp/DLMST`)** — *Deterministic linear-time MST / comparison-complexity tooling*.
    - **Relevance:** Emphasizes minimal spanning tree selection (`H^1` cycle-basis extraction on a context graph): choosing a spanning tree yields canonical trivializing gauges (`strict_descent_unique_gluing`) while non-tree chords measure genuine holonomy obstructions (`cech_specker_c4_obstruction`).

---

### C. Five Journal, News & Workshop Resources

20. **Grant N. Remmen (2021), *Amplitudes and the Riemann Zeta Function*, `Phys. Rev. Lett. 127, 241602` (`https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.127.241602`, `arXiv:2108.07820`).**
    - **Relevance:** Maps physical consistency axioms cleanly onto analytic obstructions: locality <-> meromorphicity, real mass spectrum <-> Riemann Hypothesis poles, unitarity <-> positivity. Serves as a conceptual touchstone for how structural consistency conditions cut down global moduli (`non_congruent_dynamics_fails_descent`).

21. **Timilehin Ogunmowo & Shigeki Watanabe (2026-11-23), *Presynaptic functional organization by phase separation*, *Nature Neuroscience* (`https://www.nature.com/articles/s41593-026-02517-4`).**
    - **Relevance:** Biological witness of physical compartment/patch organization via liquid-liquid phase separation, motivating spatially localized overlapping contextual domains (`ContextualRing`, `partition_of_unity_glues_overlaps`) rather than monolithic homogeneous global compartments.

22. ***100 years of extremum seeking: A survey*, *Automatica* (`https://www.sciencedirect.com/science/article/pii/S0005109823006507`, DOI `10.1016/j.automatica.2023.111481`).**
    - **Relevance:** Classic model-free sinusoidal/dither directional derivative probing of unknown black-box objectives parallels `HNG.1`'s model-agnostic finite-difference `Gamma_mod` sensitivity probe under zero backward-pass memory.

23. ***A zero-one law for one-shot system identification*, PNAS (Nov 2026) via Phys.org (`https://phys.org/news/2026-11-random-shot-mathematical-proof-physical.html`).**
    - **Relevance:** Establishes a sharp generic 0–1 phase transition for single-trajectory system identifiability from generic probes—closely bounding Semplex's generic external-profile adequacy vs adversarial indistinguishable gauge kernels (`ContinuumKernelCovariance` `fun x => |x|` counterexample and `extra_affordable_probe_breaks_forward_preservation`).

24. ***Scalable Beckmann Maps (SBM) Improve One-step Generation* (`https://tullebulle.github.io/projects/sbm/`).**
    - **Relevance:** Replaces multi-step CFG diffusion trajectories with divergence-constrained conservative Beckmann transport currents, connecting directly to pushforward measure transport (`ContinuumKernelCovariance`, `variable_jacobian_density_pushforward`) and measurable TV contraction (`MeasurableDobrushinContraction.lean`).

---

## 3. Closest Prior Work & Originality Demarcation

- **Closest prior work:**
  - *Categorical / coalgebraic causal abstractions:* Lorenz & Tull (`arXiv:2602.16612v1`) for discrete fixed-signature type alignments (cf. `research/LORENZ_TULL_2026_PRIOR_ART_AND_ORIGINALITY.md`).
  - *Test-time & harmonic orbit invariants:* `geometric-intelligence/bispectrum` (NeurIPS 2026) and Tahmasebi & Weber (`arXiv:2611.24032v1`) for orbit completeness and symmetrization variance bounds.
  - *Fact-invariant provenance & integer obstructions:* LEVER (`arXiv:2611.27016v1`) and Cheng (`arXiv:2611.27018v1`).
- **Original synthesis contributed here:**
  Unifying (i) bi-directional constructive `ContextualSystem <-> ContextualRing` effective Čech descent and weighted partition-of-unity overlap exactness (`CechNerveRingBridge.lean`), (ii) arbitrary-level Cubical Agda `--cubical=full` presheaf coherence preserving non-reflexive isotropy (`HigherCechDescent.agda`), and (iii) Mathlib measurable-space Jordan-decomposition Dobrushin contraction & composition submultiplicativity (`MeasurableDobrushinContraction.lean`), cross-validated directly against pre-registered neural quantization (`HNG.1`), continuous kernels (`HNG.2`), Čech gluing (`HNG.3`), and bispectrum/symmetrization (`HNG.4`).
