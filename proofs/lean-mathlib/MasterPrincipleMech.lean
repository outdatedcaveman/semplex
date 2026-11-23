/-
  Mechanistic Fluctuation-Dissipation & Leaky Inertia Identities for the Master Principle:
    G(lam) = P_perp * exp(-lam/2 * L) * W * exp(-lam/2 * L) * P_perp
  Proves in Mathlib v4.12.0 (isolated under proofs/lean-mathlib/):
  1. `dirichletFlow_hasDerivAt`: d/dlam Tr(exp(-lam * L) * W) = - Tr(L * exp(-lam * L) * W).
  2. `dirichletFlow_gram_eq_sandwich`: exact equivalence between the two-sided heat sandwich
     and the exponentially reweighted eigenmode trace `dirichletFlow w μ lam`.
  3. `dirichletVar_nonneg`, `dirichletVar_pos_of_two_modes`: Lagrange variance determinant identity
     and strict positivity whenever two modes have positive weight and distinct Dirichlet energies.
  4. `normDirichlet_hasDerivAt_neg_var`: fluctuation-dissipation theorem
     `d/dlam ⟨μ⟩_lam = - Var_lam(μ)`.
  5. `normDirichlet_strictAnti` & `lambda_unique_of_dirichlet`: normalized Dirichlet energy strictly
     decreases in `lam`, so empirical `kin_norm` uniquely identifies `lam_emp`.
  6. `leaky_step_displacement_sq`: step-inertia factor `alpha` scales per-step state variance
     proportionally to `alpha^2`, establishing monotone Dirichlet attenuation as `alpha -> 0+`.
-/
import Mathlib.Analysis.SpecialFunctions.ExpDeriv
import Mathlib.Analysis.Calculus.Deriv.Inv
import Mathlib.Analysis.Calculus.MeanValue
import Mathlib.Data.Fintype.BigOperators
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Positivity
import Mathlib.Tactic.Ring

open scoped BigOperators

namespace MasterPrincipleMech

noncomputable section

section FluctuationDissipation

variable {ι : Type*} [Fintype ι]

/-- Partition function / unnormalized trace flow `Z(λ) = ∑ i, w i * exp (-λ * μ i)`. -/
def dirichletFlow (w μ : ι → ℝ) (lam : ℝ) : ℝ :=
  ∑ i : ι, w i * Real.exp (-lam * μ i)

/-- First weighted Dirichlet moment `S₁(λ) = ∑ i, w i * μ i * exp (-λ * μ i)`. -/
def dirichletMoment1 (w μ : ι → ℝ) (lam : ℝ) : ℝ :=
  ∑ i : ι, w i * μ i * Real.exp (-lam * μ i)

/-- Second weighted Dirichlet moment `S₂(λ) = ∑ i, w i * (μ i)^2 * exp (-λ * μ i)`. -/
def dirichletMoment2 (w μ : ι → ℝ) (lam : ℝ) : ℝ :=
  ∑ i : ι, w i * (μ i) ^ 2 * Real.exp (-lam * μ i)

/-- Normalized Dirichlet energy `⟨μ⟩_λ = S₁(λ) / Z(λ)`. -/
def normDirichlet (w μ : ι → ℝ) (lam : ℝ) : ℝ :=
  dirichletMoment1 w μ lam / dirichletFlow w μ lam

/-- Boltzmann-weighted Dirichlet variance `Var_λ(μ) = (S₂ Z - S₁²) / Z²`. -/
def dirichletVar (w μ : ι → ℝ) (lam : ℝ) : ℝ :=
  (dirichletMoment2 w μ lam * dirichletFlow w μ lam - (dirichletMoment1 w μ lam) ^ 2) /
    (dirichletFlow w μ lam) ^ 2

private theorem hasDerivAt_exp_neg_mul (c μ_i lam : ℝ) :
    HasDerivAt (fun x => c * Real.exp (-x * μ_i)) (-c * μ_i * Real.exp (-lam * μ_i)) lam := by
  have h1 : HasDerivAt (fun x : ℝ => -x * μ_i) (-1 * μ_i) lam :=
    (hasDerivAt_id lam).neg.mul_const μ_i
  have h2 : HasDerivAt (fun x : ℝ => Real.exp (-x * μ_i)) (Real.exp (-lam * μ_i) * (-1 * μ_i)) lam :=
    (Real.hasDerivAt_exp (-lam * μ_i)).comp lam h1
  convert h2.const_mul c using 1
  ring

theorem dirichletFlow_hasDerivAt (w μ : ι → ℝ) (lam : ℝ) :
    HasDerivAt (dirichletFlow w μ) (-dirichletMoment1 w μ lam) lam := by
  unfold dirichletFlow dirichletMoment1
  have hterm : ∀ i ∈ (Finset.univ : Finset ι),
      HasDerivAt (fun x => w i * Real.exp (-x * μ i)) (-(w i * μ i * Real.exp (-lam * μ i))) lam := by
    intro i _
    convert hasDerivAt_exp_neg_mul (w i) (μ i) lam using 1
    ring
  convert HasDerivAt.sum hterm using 1
  rw [Finset.sum_neg_distrib]

theorem dirichletMoment1_hasDerivAt (w μ : ι → ℝ) (lam : ℝ) :
    HasDerivAt (dirichletMoment1 w μ) (-dirichletMoment2 w μ lam) lam := by
  unfold dirichletMoment1 dirichletMoment2
  have hterm : ∀ i ∈ (Finset.univ : Finset ι),
      HasDerivAt (fun x => w i * μ i * Real.exp (-x * μ i))
        (-(w i * (μ i) ^ 2 * Real.exp (-lam * μ i))) lam := by
    intro i _
    convert hasDerivAt_exp_neg_mul (w i * μ i) (μ i) lam using 1
    ring
  convert HasDerivAt.sum hterm using 1
  rw [Finset.sum_neg_distrib]

theorem dirichletFlow_gram_eq_sandwich (w μ : ι → ℝ) (lam : ℝ) :
    (∑ i : ι, Real.exp (-(lam / 2) * μ i) * w i * Real.exp (-(lam / 2) * μ i)) =
      dirichletFlow w μ lam := by
  unfold dirichletFlow
  refine Finset.sum_congr rfl fun i _ => ?_
  calc
    Real.exp (-(lam / 2) * μ i) * w i * Real.exp (-(lam / 2) * μ i)
        = w i * (Real.exp (-(lam / 2) * μ i) * Real.exp (-(lam / 2) * μ i)) := by ring
    _ = w i * Real.exp (-(lam / 2) * μ i + -(lam / 2) * μ i) := by rw [← Real.exp_add]
    _ = w i * Real.exp (-lam * μ i) := by
          congr 2
          ring

private theorem lagrange_var_identity (q μ : ι → ℝ) :
    2 * ((∑ i : ι, q i * (μ i) ^ 2) * (∑ i : ι, q i) - (∑ i : ι, q i * μ i) ^ 2) =
      ∑ i : ι, ∑ j : ι, q i * q j * (μ i - μ j) ^ 2 := by
  have hexp : ∀ i j : ι,
      q i * q j * (μ i - μ j) ^ 2 =
        (q i * (μ i) ^ 2) * q j + q i * (q j * (μ j) ^ 2) - 2 * ((q i * μ i) * (q j * μ j)) := by
    intro i j
    ring
  simp_rw [hexp, Finset.sum_sub_distrib, Finset.sum_add_distrib]
  simp_rw [← Finset.mul_sum, ← Finset.sum_mul]
  ring

private theorem var_num_nonneg_of_terms (q μ : ι → ℝ) (hq : ∀ i, 0 ≤ q i) :
    0 ≤ (∑ i : ι, q i * (μ i) ^ 2) * (∑ i : ι, q i) - (∑ i : ι, q i * μ i) ^ 2 := by
  have hlag := lagrange_var_identity q μ
  have hsum_nn : 0 ≤ ∑ i : ι, ∑ j : ι, q i * q j * (μ i - μ j) ^ 2 :=
    Finset.sum_nonneg fun i _ => Finset.sum_nonneg fun j _ =>
      mul_nonneg (mul_nonneg (hq i) (hq j)) (sq_nonneg _)
  linarith

private theorem var_num_pos_of_pos_terms (q μ : ι → ℝ) (hq : ∀ i, 0 ≤ q i)
    (i0 j0 : ι) (hi0 : 0 < q i0) (hj0 : 0 < q j0) (hne : μ i0 ≠ μ j0) :
    0 < (∑ i : ι, q i * (μ i) ^ 2) * (∑ i : ι, q i) - (∑ i : ι, q i * μ i) ^ 2 := by
  have hlag := lagrange_var_identity q μ
  have hterm_pos : 0 < q i0 * q j0 * (μ i0 - μ j0) ^ 2 := by
    have hsq : 0 < (μ i0 - μ j0) ^ 2 := sq_pos_of_ne_zero (sub_ne_zero.mpr hne)
    positivity
  have hinner_le : q i0 * q j0 * (μ i0 - μ j0) ^ 2 ≤
      ∑ j : ι, q i0 * q j * (μ i0 - μ j) ^ 2 :=
    Finset.single_le_sum (f := fun j => q i0 * q j * (μ i0 - μ j) ^ 2)
      (fun j _ => mul_nonneg (mul_nonneg (hq i0) (hq j)) (sq_nonneg _))
      (Finset.mem_univ j0)
  have houter_le : (∑ j : ι, q i0 * q j * (μ i0 - μ j) ^ 2) ≤
      ∑ i : ι, ∑ j : ι, q i * q j * (μ i - μ j) ^ 2 :=
    Finset.single_le_sum (f := fun i => ∑ j : ι, q i * q j * (μ i - μ j) ^ 2)
      (fun i _ => Finset.sum_nonneg fun j _ =>
        mul_nonneg (mul_nonneg (hq i) (hq j)) (sq_nonneg _))
      (Finset.mem_univ i0)
  have hsum_pos : 0 < ∑ i : ι, ∑ j : ι, q i * q j * (μ i - μ j) ^ 2 :=
    lt_of_lt_of_le hterm_pos (le_trans hinner_le houter_le)
  linarith

theorem dirichletVar_nonneg (w μ : ι → ℝ) (hw : ∀ i, 0 ≤ w i) (lam : ℝ) :
    0 ≤ dirichletVar w μ lam := by
  unfold dirichletVar dirichletMoment2 dirichletFlow dirichletMoment1
  have hq : ∀ i, 0 ≤ w i * Real.exp (-lam * μ i) :=
    fun i => mul_nonneg (hw i) (Real.exp_pos _).le
  have hnum := var_num_nonneg_of_terms (fun i => w i * Real.exp (-lam * μ i)) μ hq
  have h1 : (∑ i : ι, w i * (μ i) ^ 2 * Real.exp (-lam * μ i)) =
      ∑ i : ι, (w i * Real.exp (-lam * μ i)) * (μ i) ^ 2 :=
    Finset.sum_congr rfl fun i _ => by ring
  have h2 : (∑ i : ι, w i * μ i * Real.exp (-lam * μ i)) =
      ∑ i : ι, (w i * Real.exp (-lam * μ i)) * μ i :=
    Finset.sum_congr rfl fun i _ => by ring
  rw [h1, h2]
  exact div_nonneg hnum (sq_nonneg _)

theorem dirichletFlow_pos (w μ : ι → ℝ) (hw : ∀ i, 0 ≤ w i) (hpos : ∃ i, 0 < w i) (lam : ℝ) :
    0 < dirichletFlow w μ lam := by
  rcases hpos with ⟨i0, hi0⟩
  unfold dirichletFlow
  have hle : w i0 * Real.exp (-lam * μ i0) ≤ ∑ i : ι, w i * Real.exp (-lam * μ i) :=
    Finset.single_le_sum (f := fun i => w i * Real.exp (-lam * μ i))
      (fun i _ => mul_nonneg (hw i) (Real.exp_pos (-lam * μ i)).le)
      (Finset.mem_univ i0)
  exact lt_of_lt_of_le (mul_pos hi0 (Real.exp_pos _)) hle

theorem dirichletVar_pos_of_two_modes (w μ : ι → ℝ) (hw : ∀ i, 0 ≤ w i)
    (htwo : ∃ i j : ι, 0 < w i ∧ 0 < w j ∧ μ i ≠ μ j) (lam : ℝ) :
    0 < dirichletVar w μ lam := by
  rcases htwo with ⟨i0, j0, hi0, hj0, hne⟩
  have hZ : 0 < dirichletFlow w μ lam := dirichletFlow_pos w μ hw ⟨i0, hi0⟩ lam
  have hq : ∀ i, 0 ≤ w i * Real.exp (-lam * μ i) :=
    fun i => mul_nonneg (hw i) (Real.exp_pos _).le
  have hnum := var_num_pos_of_pos_terms (fun i => w i * Real.exp (-lam * μ i)) μ hq i0 j0
    (mul_pos hi0 (Real.exp_pos _)) (mul_pos hj0 (Real.exp_pos _)) hne
  unfold dirichletVar dirichletMoment2 dirichletMoment1
  have h1 : (∑ i : ι, w i * (μ i) ^ 2 * Real.exp (-lam * μ i)) =
      ∑ i : ι, (w i * Real.exp (-lam * μ i)) * (μ i) ^ 2 :=
    Finset.sum_congr rfl fun i _ => by ring
  have h2 : (∑ i : ι, w i * μ i * Real.exp (-lam * μ i)) =
      ∑ i : ι, (w i * Real.exp (-lam * μ i)) * μ i :=
    Finset.sum_congr rfl fun i _ => by ring
  rw [h1, h2]
  exact div_pos hnum (sq_pos_of_pos hZ)

theorem normDirichlet_hasDerivAt_neg_var (w μ : ι → ℝ) (hw : ∀ i, 0 ≤ w i)
    (hpos : ∃ i, 0 < w i) (lam : ℝ) :
    HasDerivAt (normDirichlet w μ) (-dirichletVar w μ lam) lam := by
  have hZne : dirichletFlow w μ lam ≠ 0 := (dirichletFlow_pos w μ hw hpos lam).ne'
  have hdiv := (dirichletMoment1_hasDerivAt w μ lam).div (dirichletFlow_hasDerivAt w μ lam) hZne
  convert hdiv using 1
  unfold dirichletVar
  field_simp [hZne]
  ring

theorem normDirichlet_strictAnti (w μ : ι → ℝ) (hw : ∀ i, 0 ≤ w i)
    (htwo : ∃ i j : ι, 0 < w i ∧ 0 < w j ∧ μ i ≠ μ j) :
    StrictAnti (normDirichlet w μ) := by
  rcases htwo with ⟨i0, j0, hi0, hj0, hne⟩
  refine strictAnti_of_deriv_neg fun x => ?_
  have hd := normDirichlet_hasDerivAt_neg_var w μ hw ⟨i0, hi0⟩ x
  rw [hd.deriv]
  exact neg_lt_zero.mpr (dirichletVar_pos_of_two_modes w μ hw ⟨i0, j0, hi0, hj0, hne⟩ x)

theorem lambda_unique_of_dirichlet (w μ : ι → ℝ) (hw : ∀ i, 0 ≤ w i)
    (htwo : ∃ i j : ι, 0 < w i ∧ 0 < w j ∧ μ i ≠ μ j) {lam₁ lam₂ : ℝ}
    (heq : normDirichlet w μ lam₁ = normDirichlet w μ lam₂) :
    lam₁ = lam₂ :=
  (normDirichlet_strictAnti w μ hw htwo).injective heq

end FluctuationDissipation

section LeakyInertia

variable {D : Type*} [Fintype D]

/-- Pointwise LeakyRNN update `(1 - α) h + α u` scales squared step displacement by `α²`. -/
theorem leaky_step_displacement_sq (π h u : D → ℝ) (α : ℝ) :
    (∑ d : D, π d * (((1 - α) * h d + α * u d) - h d) ^ 2) =
      α ^ 2 * ∑ d : D, π d * (u d - h d) ^ 2 := by
  have hpt : ∀ d : D, π d * (((1 - α) * h d + α * u d) - h d) ^ 2 = α ^ 2 * (π d * (u d - h d) ^ 2) := by
    intro d
    ring
  simp_rw [hpt, ← Finset.mul_sum]

end LeakyInertia

end

end MasterPrincipleMech
