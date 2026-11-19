# Experiment tree (spikes 11–42)

Each node is a spike. A child builds on what its parent established; siblings are co-equal options of one decision. Nodes with verdicts are **frozen**: never edited, only branched from. Statuses as of 2026-11-13. Reports: `experiments/SPIKE_NN_REPORT.md`.

```
11  volume at the circuit level                           frozen: volume fails for mechanisms
└ 12  width invariance under AdamW                        frozen: core invariant to width
  └ 13  margins and t* containment                        frozen: margins weak
    └ 14  Curie bias (orbit mass ∝ |orbit|^β)            frozen: β ≈ −2…−6
      ├ 15  transfer to modular addition                  frozen: transfer failed; inheritance held
      └ 16  kernel-limit account                          frozen: inheritance ≈ kernel limit; no-transfer lemma
        └ 17  bias is unit-level; CSP introduced          frozen
          └ 18  symmetric subspaces attract; CSP gains    frozen: decoys accepted
            └ 19  universal semiring measure; calibrated CSP; attraction before settling   frozen
              ├ 20  selection vs building; MI tilt        frozen: tilt constant (tanh); ReLU none
              │ └ 21  tilt over training; ratchet ablation           frozen: starts at 0, locks in by step 100; not a w₂ ratchet
              │   └ 22  leaky ReLU, movement (C10)                   frozen: C10 refuted
              │     └ 24  oddness vs saturation (C11)                frozen: both broken; homogeneity singled out
              │       └ 27  positive homogeneity (C12)               frozen: C12 refuted
              │         └ 28  indicator alignment (C13), prospective  frozen: all three held
              │           └ 29  trained-scale R²; tilt vs generalization  frozen: tilt anti-correlates with held-out accuracy
              │             └ 30  initial-kernel account of generalization   frozen: kernel prior + positive learning update; 29's cost is a confound
              │               └ 31  Walsh-degree spectral bias (C16)          frozen: C16 refuted; spectrum matching wins; balanced-accuracy caveat
              │                 └ 32  exact init-prior Bayes posterior (SLT)  frozen: describes nets best; nets beat it 24/24
              │                   └ 33  feature learning vs tilt (C18)        frozen: feature learning necessary; tilt not shown to carry the gain
              │                     └ 34  compiler as prior (Occam, C19)        frozen: competitive but coarse at n = 4; not where training moves
              │                       └ 35  compiler at n = 6, certified Occam   frozen: priors separate; nets move toward Occam (exploratory)
              │                         └ 36  replication + lazy-regime width arm   frozen: replicated 4/4; widening moves back toward the kernel
              │                           ├ 43  when: kernel-smoothed target first, Occam later? (H-J)   frozen: two phases held; Occam from step ~30
              │                           ├ 44  depth: do three-layer nets side with Occam more? (H-K)   frozen: H-K refuted at matched params
              │                           └ 45  external validity: 4 other target classes + 4 real datasets   frozen: holds on clean classes; refuted on real data
              │                             └ 46  exact cost–error frontier under label noise (C20′)   frozen: dose–response held; C20′ not supported
              │                           ├ 47  constrained collapse: hidden layer onto a minimum circuit's cells (C21; uses census G9)   frozen: C21 refuted
              │                           ├ 48  scale: the Occam pull at n = 8 and 10 (uses compile_partial, G3)   frozen: persists, shrinks with n at fixed labels per dimension; 0.94 with more data
              │                           │ └ 49  consensus law: nets output what every minimum circuit agrees on (C22)   frozen: adherence 0.98–0.99, invariant; kernel edge small in sparse cells
              │                           │   └ 50  graded consensus: share of minimum circuits vs share of seeds (C23)   frozen: graded part held; single-net prediction 0.91–0.93
              │                           │     └ 51  nets as rational nonmonotonic logic: Cut, Cautious and Rational Monotony (C24)   frozen: cumulative ≈95%, Rational Monotony 85%, stubborn
              ├ 23  distance-matched choice test (from 19 arm 1)     frozen: symmetry and information both steer single steps
              ├ 25  less strict CSP at low labels (from 19 arm 2)    frozen: certificates fail at power; anisotropic smoothness
              └ 26  lawful completion of algebra; Curie transfer (C8(c), from 14 and 20)   frozen: Curie transfers (β = −1.85); lawful 9.6× chance
```

Spike 26 builds on two parents: the Curie estimator of 14 and the selection/building contrast of 20. It hangs under 19 because 19 is their nearest common resolved node.

## Second track: Gemini on `master` (spikes 37–42), merged 2026-11-13

Run in parallel by Gemini from the Spike 10c state; renumbered at the merge (original numbers in quotes). None was pre-registered, so every verdict is exploratory. These nodes are on the compiler / Lean / real-data front, not on the generalization basin above.

```
10c  rule search fixed (shared root)
├ 37 ("11")  volume within an element (H-B, n=3); width compression (H-D)    exploratory: r = 0.67; 86–89% clean or coarser
├ 38 ("12")  CSIR causal-circuit distillation                                 demonstration
│ └ 40 ("14")  PlayTennis, Breast Cancer case studies                         exploratory: small kernel-verified circuits
├ 39 ("13")  C1 statistical lift; XOR6 grokking (H-C); n=5 depth-3 (H-E)      exploratory: 0/48 rejections; H-C negative
└ 41 ("15")  Ur-Compiler benchmarks                                           exploratory: 0.23–0.66× flat-BDD gates
  └ 42 ("16")  scaling: n=16 SAT-CEGAR, width coarsening at n=8, XOR6, LRAT net checker   exploratory; Lean wall at pbToExpr O(2^d)
```

## Third track: concepts from human judgment

```
52  canonical form of a moral concept (Moral Machine pilot)   frozen: no verdict (24 cells < 40); exploratory: single weighted rule
53  symmetry group → concept geometry (C29): 14 models' weights + THINGS-fMRI   frozen: circles held; tensor row broken (additive); shared grain finer than taxonomy
├ 54  semantic products in Neuronpedia sparse codes                        frozen: H54.3 broken (additive, structured residue); H54.1–2 neither
├ 55  justice as person-permutation invariance (C30)                         frozen: H55.1 broken (verdict readable in 2/7); C30 untested
│ └ 56  C30 with the models' own verdicts (6 small models, CPU)           frozen: H56.2–4 held (names 3–5% of verdict variance); H56.1 neither

## Fourth track: the atlas and periodic table of concepts (FOUNDATIONS §9)

```
57  closure (C32) and economy (C31) on Krohn–Rhodes automata (GRUs)        frozen: H57.3–4 held; H57.1, H57.2 broken; H57.5 neither; probe: minimal automaton exact
├ 58  causal power (interventions), characters, topology, cost incl. A5     frozen: H58.1–3, H58.6 held; H58.4 neither (A5 → χ4); H58.5 broken
├ 59  semantic primes as lexical elements (14 models' weights)              frozen: H59.1–2 broken; H59.3 held but non-specific (control)
├ 60  readout representation (C31') vs minimal faithful; GRU vs transformer  frozen: H60.2, H60.6 held; H60.1, H60.5 broken; → C31''
├ 61  data-driven lexical atoms across 14 models                             frozen: H61.1 neither, H61.2 broken; shape shared, axes not
├ 62  sufficiency law C31''' prospective (5 new readouts)                    frozen: H62.1–3 broken; predictive-state kernel matches
├ 63  4-layer transformer + curriculum on S4, A5                             frozen: H63.3 held (same geometry); H63.1 neither; H63.2 broken
├ 64  holonomy of model-to-model alignments (sheaf reading)                  frozen: H64.1 broken (no obstruction; common frame); H64.2 held
├ 65  continuous: S^2 vs RP^2 tracking                                       frozen: no verdict (fit); exploratory C36 (double cover)
├ 66  predictive-state law, formal (extension pairs, Z6 mod 3, S4_6)        frozen: H66.1–2 broken (degenerate readout); H66.3 held (2-part discarded)
├ 68  C34 in context with tied control                                       frozen: H68.1–3 held
├ 69  C37 formal: predictive structure (tau) fixed beforehand, 17 automata   frozen: H69.3 held (leading component); H69.1–2, 4, 6 broken; H69.5, 7 neither
├ 70  S^2 vs RP^2 redesigned (passable guard)                              frozen: H70.1, 2, 4 held (double cover, C36); H70.3 neither
├ 71  energy vs AGF vs orbit; emergence order; whitened geometry           frozen: H71.4, 6 held (multiplicity decides); H71.2, 3, 5, 7 broken; H71.1, 8 neither
├ 72  input encoding decides the cover (C38)                               frozen: H72.3 broken (cover survives degree-2 input); H72.4 held; H72.1-2 no verdict (A5 fit)
├ 73  smoothness pull (C40); A5 icosahedral letters repaired              frozen: H73.4 held; H73.3 broken (C38 refuted); H73.2 neither; post hoc C41 gated smoothness
├ 74  gated smoothness (C41) prospective                                  frozen: H74.3 held (dihedral ties, cosine only); H74.1-2 neither: seed lottery
├ 75  substrate independence: GRU, Hankel spectral, reservoir, ES          frozen: H75.1-4 held (laws hold for adaptive learners; reservoir shows neither)
├ 76  energy as variational principle (width, noise, acquisition order)   frozen: H76.1-4 broken; pressure selects the smoothest letter action (post hoc C42)
├ 77  Gibbs selection with one exchange rate (C43), frozen params          frozen: H77.1-3 held (98% on new automata; pressure raises the rate)
├ 78  loopholes of C43: learners, unselected automata, frequency, rival     frozen: H78.1-3, 5, 6 held; H78.4 neither (cost not usage-weighted)
└ 79  last loopholes: non-abelian unselected, transformer, ES, derived cost frozen: H79.3 held; H79.1 neither; H79.2 no verdict; H79.4 broken (0.4%)
```
```
