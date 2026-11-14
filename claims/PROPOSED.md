# Proposed Claims — Branch `gemini/G2` (Gap B1)

Do not assign `Pnnn` IDs or modify `claims/REGISTER.md` on this branch; Claude merges and assigns IDs.

- **Proposed claim (BTree LRAT checker soundness in Lean 4 kernel):**
  `Cerp.checkLratT_unsat` establishes that if the structural-recursion binary-tree LRAT checker `Cerp.checkLratT` accepts a well-formed CNF `cs` and hint-indexed trace `Ls`, then `cs` has no satisfying Boolean assignment (`∀ σ, cnfSat σ cs = false`), proved in `proofs/lean/Cerp.lean` under axioms `[propext, Quot.sound]` (`0` `sorryAx`).

- **Proposed claim (Direct PB BDD Tseitin miter soundness & kernel `by decide` equivalence for `xor4`):**
  `Cerp.tseitinTNetMiterPB_lrat_unsat_implies_equiv` proves that direct pseudo-Boolean BDD Tseitin encoding (`pbEncodeSym`, without exponential `O(2^d)` `pbToExpr` Shannon expansion) plus `checkLratT` LRAT refutation implies `∀ σ, evalTNet n ns σ = eval σ e` under axioms `[propext, Classical.choice, Quot.sound]` (`0` `sorryAx`, `0` `Lean.ofReduceBool`). Together with backward cone-of-influence hint trimming and lemma pruning in `cerp/sat.py::rup_to_lrat`, kernel `by decide` certification now succeeds in `5.25 s` on `xor3` (57 clauses vs 173, 22 vars vs 73) and `15.68 s` on `xor4` (120 clauses vs 431, 42 vars vs 176), down from `245.30 s` (`xor3`) and timeout (`xor4`).
