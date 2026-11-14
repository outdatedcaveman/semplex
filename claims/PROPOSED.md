# Proposed Claims (Branch `gemini/G5`)

## Proposed Claim: 4-Input Parity Requires at Least 5 Strictly Layered Threshold Neurons (Gap B3)

- **Statement:** No strictly layered threshold network (Family T / `evalLayered`) with at most 4 total neurons (hidden layers plus 1 output neuron) can compute 4-input parity (`parity4`, truth table `0x6996`), nor can any 3 linear threshold functions on 4 binary inputs determine `parity4`. Combined with a valid 5-neuron strictly layered parity construction, `parity4` has exact minimum size 5 in Family T.
- **Exact Evidence:**
  - Formal Lean 4.12.0 proofs in [`proofs/lean/Bounds.lean`](proofs/lean/Bounds.lean):
    - `CerpBounds.parity4_not_three_ltf_determined`
    - `CerpBounds.parity4_not_four_neurons`
    - Audited in [`proofs/lean/AuditBounds.lean`](proofs/lean/AuditBounds.lean): both theorems depend only on `[propext, Classical.choice, Quot.sound]` (zero `sorryAx`, zero `Lean.ofReduceBool`).
    - Method: weight regularization (`regularize_ltf`, `monotone_isRegular`), exhaustive regular canonical enumeration (`regExhaust`, `t_reg_exhaust`), $B_4$ orbit closure across 14 canonical orbits of sizes `[192, 192, 96, 96, 96, 64, 64, 32, 32, 24, 16, 16, 16, 4]` (940 non-constant canonical 4-bit LTFs plus constant `0`), stabilizer quotienting, and single/multi-bucket coordinate-sum Farkas certificates.
  - Python kernel verifier & certificate builder:
    - [`cerp/kernel_bounds.py`](cerp/kernel_bounds.py): `check_parity4_needs_5_neurons(cert) -> Verdict` (stdlib-only imports from `.kernel`), verifying monotone weight witnesses for all 15 representatives, generator closure (`neg0`, `sw01`, `sw12`, `sw23`), exhaustive $2^{16}$ 20-edge regular-poset coverage (`_REG_EDGES16`), stabilizer fixation, and all single/multi Farkas certificates.
    - [`cerp/bounds.py`](cerp/bounds.py): `parity4_five_neuron_cert()`.
    - Tested in [`tests/test_atlas_bounds.py`](tests/test_atlas_bounds.py) (`test_parity4_needs_5_neurons_certificate_and_forgeries`) and [`tests/test_bounds_differential.py`](tests/test_bounds_differential.py) (`test_parity4_five_neuron_matches_atlas_and_lean`, cross-checked against `atlas.ltfs(4)` and `_lean_not_threshold_pred`).
- **What it does NOT show:**
  - Does not lower-bound threshold circuits with skip connections or arbitrary DAG wiring (which are not modeled by `evalLayered`).
  - Does not independently re-prove the 5-neuron upper bound construction inside `Bounds.lean`.
  - Does not establish Lean-verified $\ge 5$ bounds for $n \ge 5$ parity functions.
