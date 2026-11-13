# Experiment tree (spikes 11–31)

Each node is a spike. A child builds on what its parent established; siblings are co-equal options of one decision. Nodes with verdicts are **frozen**: never edited, only branched from. Statuses as of 2026-11-12. Reports: `experiments/SPIKE_NN_REPORT.md`.

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
              ├ 23  distance-matched choice test (from 19 arm 1)     frozen: symmetry and information both steer single steps
              ├ 25  less strict CSP at low labels (from 19 arm 2)    frozen: certificates fail at power; anisotropic smoothness
              └ 26  lawful completion of algebra; Curie transfer (C8(c), from 14 and 20)   frozen: Curie transfers (β = −1.85); lawful 9.6× chance
```

Spike 26 builds on two parents: the Curie estimator of 14 and the selection/building contrast of 20. It hangs under 19 because 19 is their nearest common resolved node.
