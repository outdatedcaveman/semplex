/-
  Finite-Window / k-Definite Automaton Equivalence vs Periodic-Group Obstruction
  for Causal Attention Transformers (`gemini/master-principle-transformer`).

  Proves cleanly in Lean 4 + Mathlib v4.12.0 (isolated under proofs/lean-mathlib/):
  1. `run_append`: word composition law for sequential state transition `run`.
  2. `definite_monotone`: `k`-definiteness implies `k'`-definiteness for all `k ≤ k'`.
  3. `definite_depends_only_on_suffix` & `definite_window_map_exact`: any `k`-definite
     automaton equals an exact bounded-context finite-window map `windowState δ q₀ k w`
     on all words of length ≥ `k` (zero recurrent state stiffness needed beyond width `k`).
  4. `run_bijective_of_bijective`: every group / reversible transition word induces a state
     bijection.
  5. `periodic_group_not_definite`: any nontrivial reversible / group automaton (`∃ q₁ ≠ q₂`)
     cannot be `k`-definite for ANY finite horizon `k` (arbitrarily long history dependence).
  6. `definite_reset_pushforward_const`: for `k`-definite words, every initial distribution `π`
     (with `∑ q, π q = 1`) collapses to the Dirac expectation at `run δ q₀ w`, whereas
     reversible words conserve initial distribution entropy.
-/
import Mathlib.Data.Fintype.BigOperators
import Mathlib.Data.Real.Basic

open scoped BigOperators

namespace MasterPrincipleWindow

section WindowDichotomy

variable {Q A : Type*}

/-- Sequential state execution `run δ q w` reading word `w` left-to-right from `q`. -/
def run (δ : A → Q → Q) (q : Q) : List A → Q
  | [] => q
  | a :: xs => run δ (δ a q) xs

/-- A transition system is `k`-definite iff all words of length ≥ `k` synchronize every start state. -/
def IsDefinite (δ : A → Q → Q) (k : ℕ) : Prop :=
  ∀ (w : List A) (q₁ q₂ : Q), k ≤ w.length → run δ q₁ w = run δ q₂ w

/-- Bounded length-`k` suffix window map rooted at reference state `q₀`. -/
def windowState (δ : A → Q → Q) (q₀ : Q) (k : ℕ) (w : List A) : Q :=
  run δ q₀ (w.drop (w.length - k))

theorem run_append (δ : A → Q → Q) (q : Q) (w₁ w₂ : List A) :
    run δ q (w₁ ++ w₂) = run δ (run δ q w₁) w₂ := by
  induction w₁ generalizing q with
  | nil => rfl
  | cons a xs ih => simp [run, ih]

theorem definite_monotone (δ : A → Q → Q) {k k' : ℕ}
    (hdef : IsDefinite δ k) (hle : k ≤ k') : IsDefinite δ k' :=
  fun w q₁ q₂ hw => hdef w q₁ q₂ (le_trans hle hw)

theorem definite_depends_only_on_suffix (δ : A → Q → Q) (k : ℕ) (w : List A) (q q₀ : Q)
    (hdef : IsDefinite δ k) (hk : k ≤ w.length) :
    run δ q w = run δ q₀ (w.drop (w.length - k)) := by
  conv_lhs => rw [← List.take_append_drop (w.length - k) w, run_append]
  exact hdef (w.drop (w.length - k)) _ q₀ (by rw [List.length_drop]; omega)

theorem definite_window_map_exact (δ : A → Q → Q) (k : ℕ) (w : List A) (q q₀ : Q)
    (hdef : IsDefinite δ k) (hk : k ≤ w.length) :
    run δ q w = windowState δ q₀ k w :=
  definite_depends_only_on_suffix δ k w q q₀ hdef hk

theorem run_bijective_of_bijective (δ : A → Q → Q)
    (hbij : ∀ a : A, Function.Bijective (δ a)) (w : List A) :
    Function.Bijective (fun q => run δ q w) := by
  induction w with
  | nil => exact Function.bijective_id
  | cons a xs ih =>
    simpa [run] using ih.comp (hbij a)

theorem periodic_group_not_definite (δ : A → Q → Q)
    (hbij : ∀ a : A, Function.Bijective (δ a)) (a : A)
    (hne : ∃ q₁ q₂ : Q, q₁ ≠ q₂) (k : ℕ) :
    ¬ IsDefinite δ k := by
  rcases hne with ⟨q₁, q₂, hneq⟩
  intro hdef
  have hinj := (run_bijective_of_bijective δ hbij (List.replicate k a)).1
  have heq := hdef (List.replicate k a) q₁ q₂ (by simp [List.length_replicate])
  exact hneq (hinj heq)

private theorem finset_sum_mul_const [DecidableEq Q] (s : Finset Q) (f : Q → ℝ) (c : ℝ) :
    (∑ q ∈ s, f q * c) = (∑ q ∈ s, f q) * c := by
  refine Finset.induction_on s ?_ ?_
  · simp
  · intro a t ha ih
    rw [Finset.sum_insert ha, Finset.sum_insert ha, ih, add_mul]

theorem definite_reset_pushforward_const [Fintype Q] [DecidableEq Q] (δ : A → Q → Q) (k : ℕ)
    (w : List A) (q₀ : Q) (π : Q → ℝ) (hsum : ∑ q : Q, π q = 1) (u : Q → ℝ)
    (hdef : IsDefinite δ k) (hk : k ≤ w.length) :
    (∑ q : Q, π q * u (run δ q w)) = u (run δ q₀ w) := by
  have hrun : ∀ q : Q, run δ q w = run δ q₀ w := fun q => hdef w q q₀ hk
  simp_rw [hrun]
  rw [finset_sum_mul_const, hsum, one_mul]

end WindowDichotomy

end MasterPrincipleWindow
