# Lean proofs that need Mathlib

| File | Contents |
|---|---|
| `CerpMathlib.lean`, `AuditMathlib.lean` | Mathlib-backed CERP results and their axiom audit |
| `Selection.lean` | Identities behind the selection rule C43: `chord_sq_sum` (kinetic cost = mean ‖Rx − x‖² over an orthonormal basis = 2(d − tr R)), `fourier_laplacian` (the cost is the random-walk Laplacian eigenvalue of a Fourier mode on ℤ/n, so exp(−λc) is a heat kernel), `mediant_max` (semisimple reduction of the Harder–Narasimhan filtration: no union of blocks has a higher slope than the best block) |
| `SELECTION_CHECK_LOG.txt` | axiom audit: propext, Classical.choice, Quot.sound only |

Build: `lake exe cache get && lake build` (Lean 4.12.0, Mathlib v4.12.0). Drafts are checked with
`python -m cerp.angelic FILE.lean --project proofs/lean-mathlib --mathlib` (MathEye-style angelic checking:
failing steps become `sorry` obligations, automation closes what it can, the rest is reported as the essential set).
