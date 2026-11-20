# G18 Handoff — Lean Proof of the Predictive-Kernel Identity (`FOUNDATIONS.md` §11.4)

- **Branch:** `gemini/G18` (base commit `7be53461c70c14ed261843975fd7428a18e02f31`)
- **Target:** Formalize both parts of `charter/FOUNDATIONS.md` §11.4 in `proofs/lean-mathlib/` (Lean `4.12.0` + Mathlib `v4.12.0`), leaving `proofs/lean/` untouched (`git diff proofs/lean/` empty):
  1. Counting identity: `#{w : w⁻¹xw ∈ H} = |H| · #{gH : x · gH = gH}`.
  2. Expectation identity for one-hot left-coset readout `o`: `E_w ⟨o(gw), o(hw)⟩ = χ_perm(g⁻¹h) / [G : H]`.
- **Files added/changed:**
  - `proofs/lean-mathlib/PredictiveKernel.lean` — exact counting and expectation proofs (`Subgroup`, `QuotientGroup`, `MulAction`, `Fintype.card`, `Real`).
  - `proofs/lean-mathlib/AuditPredictiveKernel.lean` — `#print axioms` audit script for every exported declaration.
  - `proofs/lean-mathlib/lakefile.toml` — added `[[lean_lib]] name = "PredictiveKernel"` and added `"PredictiveKernel"` to `defaultTargets`.
  - `claims/PROPOSED.md` — appended Section 11 (`G18`, no `Pnnn` IDs assigned; `THEORY.md` §5, `claims/GAPS.json`, `claims/REGISTER.md`, and `experiments/FROZEN.json` untouched).

## Exact Lean Statements Proved (`proofs/lean-mathlib/PredictiveKernel.lean`)

1. **Counting identity (`card_conj_mem_eq_card_mul_fixedCosets` and `card_filter_conj_mem_eq`):**
   ```lean
   theorem card_conj_mem_eq_card_mul_fixedCosets {G : Type*} [Group G] [Fintype G]
       (H : Subgroup G) (x : G) :
       Fintype.card {w : G // w⁻¹ * x * w ∈ H} =
         Fintype.card H * Fintype.card {q : G ⧸ H // x • q = q}

   theorem card_filter_conj_mem_eq {G : Type*} [Group G] [Fintype G]
       (H : Subgroup G) (x : G) :
       (Finset.univ.filter fun w : G => w⁻¹ * x * w ∈ H).card =
         Fintype.card H * (Finset.univ.filter fun q : G ⧸ H => x • q = q).card
   ```

2. **Expectation form for one-hot coset readout (`predictive_kernel_coset_expectation` and `card_quotient` corollary):**
   ```lean
   noncomputable def cosetOneHot {G : Type*} [Group G] (H : Subgroup G) (g : G) : G ⧸ H → ℝ :=
     fun q => if (g : G ⧸ H) = q then 1 else 0

   noncomputable def cosetInner {G : Type*} [Group G] [Fintype G] (H : Subgroup G)
       (u v : G ⧸ H → ℝ) : ℝ :=
     ∑ q : G ⧸ H, u q * v q

   noncomputable def permChar {G : Type*} [Group G] [Fintype G] (H : Subgroup G) (x : G) : ℝ :=
     (Fintype.card {q : G ⧸ H // x • q = q} : ℝ)

   theorem predictive_kernel_coset_expectation {G : Type*} [Group G] [Fintype G]
       (H : Subgroup G) (g h : G) :
       (1 / (Fintype.card G : ℝ)) *
           ∑ w : G, cosetInner H (cosetOneHot H (g * w)) (cosetOneHot H (h * w)) =
         permChar H (g⁻¹ * h) / (H.index : ℝ)

   theorem predictive_kernel_coset_expectation_card_quotient {G : Type*} [Group G] [Fintype G]
       (H : Subgroup G) (g h : G) :
       (1 / (Fintype.card G : ℝ)) *
           ∑ w : G, cosetInner H (cosetOneHot H (g * w)) (cosetOneHot H (h * w)) =
         permChar H (g⁻¹ * h) / (Fintype.card (G ⧸ H) : ℝ)
   ```

No weakening or extra assumptions are used: `[Group G]`, `[Fintype G]`, `H : Subgroup G`, and `x, g, h : G` are completely general.

## Exact Verification & Axiom Audit Outputs

- **Mathlib build & audit (`lake` + pinned `mathlib4` `v4.12.0` prebuilt cache, `.lake/` removed prior to commit):**
  - `lake build PredictiveKernel` -> `exit 0` in `71.01s` (`✔ [898/899] Built PredictiveKernel`).
  - `lake env lean AuditPredictiveKernel.lean` -> `exit 0` in `31.96s`.
  - Every declaration (`conj_mem_iff_smul_coset_eq`, `card_conj_mem_eq_card_mul_fixedCosets`, `card_filter_conj_mem_eq`, `cosetInner_cosetOneHot_eq`, `predictive_kernel_coset_expectation`, `predictive_kernel_coset_expectation_card_quotient`) depends only on `[propext, Classical.choice, Quot.sound]`.
- **Rule 7 checks (verified on final code/data state):**
  - `python -m cerp.register check` -> `0 problem(s), 46 status note(s)` (`exit 0`, `git diff -w claims/LEDGER_CHECK.md` empty).
  - `python -m cerp.status --check` -> `exit 0`.
  - `SEMPLEX_LEAN_TIMEOUT=900 python -m pytest -q` -> `167 passed in 1238.76s (0:20:38)` (`exit 0`).
  - Standalone Lean `v4.12.0` compile & audit (`.olean` built in `$env:TEMP` and deleted, `LEFTOVER_OLEAN=0`, `bad_axioms=False`, `[propext, Classical.choice, Quot.sound]` max):
    - `Cerp.lean` (`51.55s`), `Audit.lean` (`1.83s`) — `exit 0`
    - `Theory.lean` (`23.94s`), `AuditTheory.lean` (`1.99s`) — `exit 0`
    - `Bounds.lean` (`516.11s`), `AuditBounds.lean` (`1.67s`) — `exit 0`
    - `Inference.lean` (`1.91s`), `AuditInference.lean` (`0.78s`) — `exit 0`
    - `Closure.lean` (`0.93s`), `AuditClosure.lean` (`0.78s`) — `exit 0`
  - `git diff proofs/lean/` empty; `proofs/lean-mathlib/.lake/` absent before commit.
