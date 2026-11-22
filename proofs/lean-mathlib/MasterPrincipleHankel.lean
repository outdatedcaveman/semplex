/-
  Mathlib formalization for the Non-Commuting Trace Fluctuation-Dissipation,
  Concatenated Interface-Gram / Hankel Variational Balancing, and Contractive
  SSM Lag-Decay identities (`gemini/master-principle-hankel`).

  Isolated in `proofs/lean-mathlib/` so `proofs/lean/` remains core Lean 4.
-/
import Mathlib.Analysis.SpecialFunctions.ExpDeriv
import Mathlib.Analysis.Calculus.Deriv.Inv
import Mathlib.Analysis.Calculus.MeanValue
import Mathlib.Data.Fintype.BigOperators
import Mathlib.Data.Matrix.Basic
import Mathlib.LinearAlgebra.Matrix.Trace
import Mathlib.LinearAlgebra.Matrix.Spectrum
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Positivity
import Mathlib.Tactic.Ring

open scoped BigOperators Matrix

namespace MasterPrincipleHankel

noncomputable section
set_option linter.unusedSectionVars false

section ScalarDirichletFD

variable {ι : Type*} [Fintype ι]

/-- Partition function `Z(λ) = ∑ i, w i * exp (-λ * μ i)`. -/
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
  have hid := lagrange_var_identity q μ
  have hsum_nonneg : 0 ≤ ∑ i : ι, ∑ j : ι, q i * q j * (μ i - μ j) ^ 2 :=
    Finset.sum_nonneg fun i _ =>
      Finset.sum_nonneg fun j _ =>
        mul_nonneg (mul_nonneg (hq i) (hq j)) (sq_nonneg _)
  linarith only [hid, hsum_nonneg]

private theorem var_num_pos_of_pos_terms (q μ : ι → ℝ) (hq : ∀ i, 0 ≤ q i)
    (i0 j0 : ι) (hi0 : 0 < q i0) (hj0 : 0 < q j0) (hne : μ i0 ≠ μ j0) :
    0 < (∑ i : ι, q i * (μ i) ^ 2) * (∑ i : ι, q i) - (∑ i : ι, q i * μ i) ^ 2 := by
  have hid := lagrange_var_identity q μ
  have hdiff_pos : 0 < (μ i0 - μ j0) ^ 2 := sq_pos_of_ne_zero (sub_ne_zero.mpr hne)
  have hterm_pos : 0 < q i0 * q j0 * (μ i0 - μ j0) ^ 2 :=
    mul_pos (mul_pos hi0 hj0) hdiff_pos
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
  linarith only [hid, hsum_pos]

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
  unfold dirichletVar dirichletMoment2 dirichletFlow dirichletMoment1
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

end ScalarDirichletFD

section NonCommutingMatrixFD

variable {n : Type*} [Fintype n] [DecidableEq n]

/-- Orthogonal eigenvector matrix of a real Hermitian/symmetric matrix `L`. -/
def unitaryMat {L : Matrix n n ℝ} (hL : L.IsHermitian) : Matrix n n ℝ :=
  (hL.eigenvectorUnitary : Matrix n n ℝ)

/-- Half-step matrix exponential `exp(-λ/2 * L)` via spectral diagonalization. -/
def heatHalf {L : Matrix n n ℝ} (hL : L.IsHermitian) (lam : ℝ) : Matrix n n ℝ :=
  unitaryMat hL * Matrix.diagonal (fun i => Real.exp (-(lam / 2) * hL.eigenvalues i)) *
    star (unitaryMat hL)

/-- Full matrix exponential `exp(-λ * L)` via spectral diagonalization. -/
def heatFull {L : Matrix n n ℝ} (hL : L.IsHermitian) (lam : ℝ) : Matrix n n ℝ :=
  unitaryMat hL * Matrix.diagonal (fun i => Real.exp (-lam * hL.eigenvalues i)) *
    star (unitaryMat hL)

/-- Non-commuting two-sided Master Operator `G(λ) = exp(-λ/2 L) W exp(-λ/2 L)`. -/
def matG {L : Matrix n n ℝ} (hL : L.IsHermitian) (W : Matrix n n ℝ) (lam : ℝ) : Matrix n n ℝ :=
  heatHalf hL lam * W * heatHalf hL lam

/-- Diagonal weight `(Uᵀ W U)_{i,i}` in the eigenbasis of `L` (no commutativity assumed). -/
def diagWeight {L : Matrix n n ℝ} (hL : L.IsHermitian) (W : Matrix n n ℝ) (i : n) : ℝ :=
  (star (unitaryMat hL) * W * unitaryMat hL) i i

/-- Normalized matrix Dirichlet energy `Tr(L G(λ)) / Tr(G(λ))`. -/
def matNormDirichlet {L : Matrix n n ℝ} (hL : L.IsHermitian) (W : Matrix n n ℝ) (lam : ℝ) : ℝ :=
  Matrix.trace (L * matG hL W lam) / Matrix.trace (matG hL W lam)

/-- Boltzmann-weighted eigenvalue variance of `L` under state `G(λ) / Tr G(λ)`. -/
def matDirichletVar {L : Matrix n n ℝ} (hL : L.IsHermitian) (W : Matrix n n ℝ) (lam : ℝ) : ℝ :=
  dirichletVar (diagWeight hL W) hL.eigenvalues lam

private theorem diagonal_mul_diagonal {α : Type*} [Fintype α] [DecidableEq α] (a b : α → ℝ) :
    Matrix.diagonal a * Matrix.diagonal b = Matrix.diagonal (fun i => a i * b i) := by
  ext i j
  by_cases hij : i = j
  · subst hij
    simp [Matrix.mul_apply, Matrix.diagonal_apply]
  · simp [Matrix.mul_apply, Matrix.diagonal_apply, hij]

private theorem trace_diagonal_mul (d : n → ℝ) (M : Matrix n n ℝ) :
    Matrix.trace (Matrix.diagonal d * M) = ∑ i : n, d i * M i i := by
  unfold Matrix.trace
  refine Finset.sum_congr rfl fun i _ => ?_
  simp [Matrix.diag_apply, Matrix.mul_apply, Matrix.diagonal_apply]

theorem diagWeight_eq_quadForm {L : Matrix n n ℝ} (hL : L.IsHermitian) (W : Matrix n n ℝ) (i : n) :
    diagWeight hL W i = Matrix.dotProduct (fun r => unitaryMat hL r i) (W *ᵥ fun r => unitaryMat hL r i) := by
  unfold diagWeight Matrix.dotProduct Matrix.mulVec
  simp only [Matrix.mul_apply, Matrix.star_apply, star_trivial]
  have hr : ∀ k : n,
      (∑ x : n, unitaryMat hL x i * W x k) * unitaryMat hL k i =
        ∑ x : n, unitaryMat hL x i * (W x k * unitaryMat hL k i) := by
    intro k
    rw [Finset.sum_mul]
    refine Finset.sum_congr rfl fun x _ => by ring
  simp_rw [hr]
  rw [Finset.sum_comm]
  refine Finset.sum_congr rfl fun x _ => ?_
  unfold Matrix.dotProduct
  rw [← Finset.mul_sum]

theorem diagWeight_nonneg {L : Matrix n n ℝ} (hL : L.IsHermitian) (W : Matrix n n ℝ)
    (hW : ∀ x : n → ℝ, 0 ≤ Matrix.dotProduct x (W *ᵥ x)) (i : n) :
    0 ≤ diagWeight hL W i := by
  rw [diagWeight_eq_quadForm]
  exact hW (fun r => unitaryMat hL r i)

private theorem trace_conj_diagonal (d : n → ℝ) (U W : Matrix n n ℝ) :
    Matrix.trace ((U * Matrix.diagonal d * star U) * W) =
      Matrix.trace (Matrix.diagonal d * (star U * W * U)) := by
  calc
    Matrix.trace ((U * Matrix.diagonal d * star U) * W)
        = Matrix.trace (U * ((Matrix.diagonal d * star U) * W)) := by
          simp only [Matrix.mul_assoc]
    _ = Matrix.trace (((Matrix.diagonal d * star U) * W) * U) := by
          rw [Matrix.trace_mul_comm]
    _ = Matrix.trace (Matrix.diagonal d * (star U * W * U)) := by
          simp only [Matrix.mul_assoc]

theorem heatHalf_mul_self {L : Matrix n n ℝ} (hL : L.IsHermitian) (lam : ℝ) :
    heatHalf hL lam * heatHalf hL lam = heatFull hL lam := by
  unfold heatHalf heatFull
  have hsu : star (unitaryMat hL) * unitaryMat hL = 1 :=
    unitary.coe_star_mul_self hL.eigenvectorUnitary
  have hassoc : ∀ M : Matrix n n ℝ, star (unitaryMat hL) * (unitaryMat hL * M) = M := by
    intro M
    rw [← Matrix.mul_assoc, hsu, Matrix.one_mul]
  calc
    (unitaryMat hL * Matrix.diagonal (fun i => Real.exp (-(lam / 2) * hL.eigenvalues i)) *
        star (unitaryMat hL)) *
      (unitaryMat hL * Matrix.diagonal (fun i => Real.exp (-(lam / 2) * hL.eigenvalues i)) *
        star (unitaryMat hL))
        = unitaryMat hL *
            (Matrix.diagonal (fun i => Real.exp (-(lam / 2) * hL.eigenvalues i)) *
              (star (unitaryMat hL) *
                (unitaryMat hL *
                  (Matrix.diagonal (fun i => Real.exp (-(lam / 2) * hL.eigenvalues i)) *
                    star (unitaryMat hL))))) := by
          simp only [Matrix.mul_assoc]
    _ = unitaryMat hL *
          ((Matrix.diagonal (fun i => Real.exp (-(lam / 2) * hL.eigenvalues i)) *
            Matrix.diagonal (fun i => Real.exp (-(lam / 2) * hL.eigenvalues i))) *
            star (unitaryMat hL)) := by
          rw [hassoc]
          simp only [Matrix.mul_assoc]
    _ = unitaryMat hL * Matrix.diagonal (fun i => Real.exp (-lam * hL.eigenvalues i)) *
          star (unitaryMat hL) := by
          rw [diagonal_mul_diagonal]
          simp only [← Matrix.mul_assoc]
          congr 2
          ext i j
          by_cases hij : i = j
          · subst hij
            simp only [Matrix.diagonal_apply_eq, ← Real.exp_add]
            congr 1
            ring
          · simp [Matrix.diagonal_apply_ne _ hij]

private theorem heatHalf_mul_L_mul_heatHalf {L : Matrix n n ℝ} (hL : L.IsHermitian) (lam : ℝ) :
    heatHalf hL lam * L * heatHalf hL lam =
      unitaryMat hL *
        Matrix.diagonal (fun i => hL.eigenvalues i * Real.exp (-lam * hL.eigenvalues i)) *
        star (unitaryMat hL) := by
  have hspec : L = unitaryMat hL * Matrix.diagonal hL.eigenvalues * star (unitaryMat hL) := by
    have hs := hL.spectral_theorem
    simpa [unitaryMat, Function.comp_def, RCLike.ofReal_real_eq_id] using hs
  have hsu : star (unitaryMat hL) * unitaryMat hL = 1 :=
    unitary.coe_star_mul_self hL.eigenvectorUnitary
  have hassoc : ∀ M : Matrix n n ℝ, star (unitaryMat hL) * (unitaryMat hL * M) = M := by
    intro M
    rw [← Matrix.mul_assoc, hsu, Matrix.one_mul]
  have h0 : heatHalf hL lam * L * heatHalf hL lam =
      heatHalf hL lam * (unitaryMat hL * Matrix.diagonal hL.eigenvalues * star (unitaryMat hL)) *
        heatHalf hL lam :=
    congrArg (fun X => heatHalf hL lam * X * heatHalf hL lam) hspec
  rw [h0]
  unfold heatHalf
  calc
    (unitaryMat hL * Matrix.diagonal (fun i => Real.exp (-(lam / 2) * hL.eigenvalues i)) *
        star (unitaryMat hL)) *
      (unitaryMat hL * Matrix.diagonal hL.eigenvalues * star (unitaryMat hL)) *
      (unitaryMat hL * Matrix.diagonal (fun i => Real.exp (-(lam / 2) * hL.eigenvalues i)) *
        star (unitaryMat hL))
        = unitaryMat hL *
            (Matrix.diagonal (fun i => Real.exp (-(lam / 2) * hL.eigenvalues i)) *
              (star (unitaryMat hL) *
                (unitaryMat hL *
                  (Matrix.diagonal hL.eigenvalues *
                    (star (unitaryMat hL) *
                      (unitaryMat hL *
                        (Matrix.diagonal (fun i => Real.exp (-(lam / 2) * hL.eigenvalues i)) *
                          star (unitaryMat hL)))))))) := by
          simp only [Matrix.mul_assoc]
    _ = unitaryMat hL *
          ((Matrix.diagonal (fun i => Real.exp (-(lam / 2) * hL.eigenvalues i)) *
            Matrix.diagonal hL.eigenvalues *
            Matrix.diagonal (fun i => Real.exp (-(lam / 2) * hL.eigenvalues i))) *
            star (unitaryMat hL)) := by
          rw [hassoc, hassoc]
          simp only [Matrix.mul_assoc]
    _ = unitaryMat hL *
          Matrix.diagonal (fun i => hL.eigenvalues i * Real.exp (-lam * hL.eigenvalues i)) *
          star (unitaryMat hL) := by
          rw [diagonal_mul_diagonal, diagonal_mul_diagonal]
          simp only [← Matrix.mul_assoc]
          congr 2
          ext i j
          by_cases hij : i = j
          · subst hij
            simp only [Matrix.diagonal_apply_eq]
            have hexp :
                Real.exp (-(lam / 2) * hL.eigenvalues i) * hL.eigenvalues i *
                    Real.exp (-(lam / 2) * hL.eigenvalues i) =
                  hL.eigenvalues i *
                    (Real.exp (-(lam / 2) * hL.eigenvalues i) *
                      Real.exp (-(lam / 2) * hL.eigenvalues i)) := by ring
            rw [hexp, ← Real.exp_add]
            congr 2
            ring
          · simp [Matrix.diagonal_apply_ne _ hij]

/-- Exact eigenbasis trace expansion of `Tr(G(λ))` WITHOUT assuming `[L, W] = 0`. -/
theorem trace_matG_eq_dirichletFlow {L : Matrix n n ℝ} (hL : L.IsHermitian)
    (W : Matrix n n ℝ) (lam : ℝ) :
    Matrix.trace (matG hL W lam) = dirichletFlow (diagWeight hL W) hL.eigenvalues lam := by
  unfold matG
  rw [Matrix.trace_mul_comm (heatHalf hL lam * W) (heatHalf hL lam), ← Matrix.mul_assoc,
    heatHalf_mul_self hL lam]
  unfold heatFull
  rw [trace_conj_diagonal]
  rw [trace_diagonal_mul]
  unfold dirichletFlow
  refine Finset.sum_congr rfl fun i _ => mul_comm _ _

/-- Exact eigenbasis trace expansion of `Tr(L G(λ))` WITHOUT assuming `[L, W] = 0`. -/
theorem trace_mul_matG_eq_moment1 {L : Matrix n n ℝ} (hL : L.IsHermitian)
    (W : Matrix n n ℝ) (lam : ℝ) :
    Matrix.trace (L * matG hL W lam) = dirichletMoment1 (diagWeight hL W) hL.eigenvalues lam := by
  unfold matG
  have hcyc :
      Matrix.trace (L * (heatHalf hL lam * W * heatHalf hL lam)) =
        Matrix.trace ((heatHalf hL lam * L * heatHalf hL lam) * W) := by
    calc
      Matrix.trace (L * (heatHalf hL lam * W * heatHalf hL lam))
          = Matrix.trace ((L * heatHalf hL lam * W) * heatHalf hL lam) := by
            simp only [Matrix.mul_assoc]
      _ = Matrix.trace (heatHalf hL lam * (L * heatHalf hL lam * W)) := by
            rw [Matrix.trace_mul_comm]
      _ = Matrix.trace ((heatHalf hL lam * L * heatHalf hL lam) * W) := by
            simp only [Matrix.mul_assoc]
  rw [hcyc, heatHalf_mul_L_mul_heatHalf hL lam, trace_conj_diagonal, trace_diagonal_mul]
  unfold diagWeight dirichletMoment1
  refine Finset.sum_congr rfl fun i _ => by ring

theorem matNormDirichlet_eq_scalar {L : Matrix n n ℝ} (hL : L.IsHermitian) (W : Matrix n n ℝ) :
    matNormDirichlet hL W = normDirichlet (diagWeight hL W) hL.eigenvalues := by
  funext lam
  unfold matNormDirichlet normDirichlet
  rw [trace_mul_matG_eq_moment1, trace_matG_eq_dirichletFlow]

/-- Non-commuting Matrix Fluctuation-Dissipation Theorem: `d/dλ (Tr(L G)/Tr(G)) = -Var_λ(L)`. -/
theorem matNormDirichlet_hasDerivAt_neg_var {L : Matrix n n ℝ} (hL : L.IsHermitian)
    (W : Matrix n n ℝ) (hW : ∀ x : n → ℝ, 0 ≤ Matrix.dotProduct x (W *ᵥ x))
    (hpos : ∃ i : n, 0 < diagWeight hL W i) (lam : ℝ) :
    HasDerivAt (matNormDirichlet hL W) (-matDirichletVar hL W lam) lam := by
  rw [matNormDirichlet_eq_scalar hL W]
  exact normDirichlet_hasDerivAt_neg_var (diagWeight hL W) hL.eigenvalues
    (diagWeight_nonneg hL W hW) hpos lam

/-- Strict monotonicity of matrix Dirichlet roughness for general non-commuting PSD `W`. -/
theorem matNormDirichlet_strictAnti {L : Matrix n n ℝ} (hL : L.IsHermitian)
    (W : Matrix n n ℝ) (hW : ∀ x : n → ℝ, 0 ≤ Matrix.dotProduct x (W *ᵥ x))
    (htwo : ∃ i j : n, 0 < diagWeight hL W i ∧ 0 < diagWeight hL W j ∧
      hL.eigenvalues i ≠ hL.eigenvalues j) :
    StrictAnti (matNormDirichlet hL W) := by
  rw [matNormDirichlet_eq_scalar hL W]
  exact normDirichlet_strictAnti (diagWeight hL W) hL.eigenvalues
    (diagWeight_nonneg hL W hW) htwo

/-- Unique inverse-temperature identifiability of `λ` from observed `Tr(L G(λ)) / Tr(G(λ))`. -/
theorem matLambda_unique_of_dirichlet {L : Matrix n n ℝ} (hL : L.IsHermitian)
    (W : Matrix n n ℝ) (hW : ∀ x : n → ℝ, 0 ≤ Matrix.dotProduct x (W *ᵥ x))
    (htwo : ∃ i j : n, 0 < diagWeight hL W i ∧ 0 < diagWeight hL W j ∧
      hL.eigenvalues i ≠ hL.eigenvalues j)
    {lam₁ lam₂ : ℝ} (heq : matNormDirichlet hL W lam₁ = matNormDirichlet hL W lam₂) :
    lam₁ = lam₂ :=
  (matNormDirichlet_strictAnti hL W hW htwo).injective heq

end NonCommutingMatrixFD

section HankelInterfaceGram

variable {p m f : Type*} [Fintype p] [Fintype m] [Fintype f]
variable [DecidableEq p] [DecidableEq m] [DecidableEq f]

/-- Concatenated past-plus-future feature matrix `Φ = [Aᵀ | B]`. -/
def concatInterface (A : Matrix p m ℝ) (B : Matrix m f ℝ) : Matrix m (p ⊕ f) ℝ :=
  Matrix.of fun i => Sum.elim (Aᵀ i) (B i)

/-- The additive sum `W_c + W_o = Aᵀ A + B Bᵀ` is the exact Gram matrix `Φ Φᵀ` of `[Aᵀ | B]`. -/
theorem concat_interface_gram (A : Matrix p m ℝ) (B : Matrix m f ℝ) :
    concatInterface A B * (concatInterface A B)ᵀ = Aᵀ * A + B * Bᵀ := by
  ext i j
  simp only [concatInterface, Matrix.mul_apply, Matrix.transpose_apply, Matrix.add_apply,
    Matrix.of_apply, Fintype.sum_sum_type, Sum.elim_inl, Sum.elim_inr]

/-- Exact quadratic form of `W_c + W_o`: sum of past and future response energies. -/
theorem interface_sum_quadForm_eq (A : Matrix p m ℝ) (B : Matrix m f ℝ) (v : m → ℝ) :
    Matrix.dotProduct v ((Aᵀ * A + B * Bᵀ) *ᵥ v) =
      (∑ i : p, (A *ᵥ v) i ^ 2) + ∑ j : f, (Bᵀ *ᵥ v) j ^ 2 := by
  have h1 : Matrix.dotProduct v ((Aᵀ * A) *ᵥ v) = ∑ i : p, (A *ᵥ v) i ^ 2 := by
    calc
      Matrix.dotProduct v ((Aᵀ * A) *ᵥ v)
          = Matrix.dotProduct v (Aᵀ *ᵥ (A *ᵥ v)) := by rw [Matrix.mulVec_mulVec]
      _ = Matrix.dotProduct (v ᵥ* Aᵀ) (A *ᵥ v) := by rw [Matrix.dotProduct_mulVec]
      _ = Matrix.dotProduct (A *ᵥ v) (A *ᵥ v) := by rw [Matrix.vecMul_transpose]
      _ = ∑ i : p, (A *ᵥ v) i ^ 2 := by
          unfold Matrix.dotProduct
          refine Finset.sum_congr rfl fun i _ => (sq _).symm
  have h2 : Matrix.dotProduct v ((B * Bᵀ) *ᵥ v) = ∑ j : f, (Bᵀ *ᵥ v) j ^ 2 := by
    calc
      Matrix.dotProduct v ((B * Bᵀ) *ᵥ v)
          = Matrix.dotProduct v (B *ᵥ (Bᵀ *ᵥ v)) := by rw [Matrix.mulVec_mulVec]
      _ = Matrix.dotProduct (v ᵥ* B) (Bᵀ *ᵥ v) := by rw [Matrix.dotProduct_mulVec]
      _ = Matrix.dotProduct (Bᵀ *ᵥ v) (Bᵀ *ᵥ v) := by
          rw [← Matrix.transpose_transpose B, Matrix.vecMul_transpose, Matrix.transpose_transpose]
      _ = ∑ j : f, (Bᵀ *ᵥ v) j ^ 2 := by
          unfold Matrix.dotProduct
          refine Finset.sum_congr rfl fun j _ => (sq _).symm
  rw [Matrix.add_mulVec, Matrix.dotProduct_add, h1, h2]

theorem interface_sum_quadForm_nonneg (A : Matrix p m ℝ) (B : Matrix m f ℝ) (v : m → ℝ) :
    0 ≤ Matrix.dotProduct v ((Aᵀ * A + B * Bᵀ) *ᵥ v) := by
  rw [interface_sum_quadForm_eq]
  positivity

/-- A vector lies in the nullspace of `W_c + W_o` iff it annihilates both `A` and `Bᵀ`. -/
theorem interface_sum_quadForm_eq_zero_iff (A : Matrix p m ℝ) (B : Matrix m f ℝ) (v : m → ℝ) :
    Matrix.dotProduct v ((Aᵀ * A + B * Bᵀ) *ᵥ v) = 0 ↔ A *ᵥ v = 0 ∧ Bᵀ *ᵥ v = 0 := by
  rw [interface_sum_quadForm_eq]
  have hA_nn : 0 ≤ ∑ i : p, (A *ᵥ v) i ^ 2 := Finset.sum_nonneg fun i _ => sq_nonneg _
  have hB_nn : 0 ≤ ∑ j : f, (Bᵀ *ᵥ v) j ^ 2 := Finset.sum_nonneg fun j _ => sq_nonneg _
  constructor
  · intro hsum
    have hA0 : (∑ i : p, (A *ᵥ v) i ^ 2) = 0 := by linarith
    have hB0 : (∑ j : f, (Bᵀ *ᵥ v) j ^ 2) = 0 := by linarith
    rw [Finset.sum_eq_zero_iff_of_nonneg (fun i _ => sq_nonneg _)] at hA0
    rw [Finset.sum_eq_zero_iff_of_nonneg (fun j _ => sq_nonneg _)] at hB0
    exact ⟨funext fun i => sq_eq_zero_iff.mp (hA0 i (Finset.mem_univ i)),
      funext fun j => sq_eq_zero_iff.mp (hB0 j (Finset.mem_univ j))⟩
  · rintro ⟨hA, hB⟩
    simp [hA, hB]

/-- Spike 22 collapse: if centered prior Gramian `W_c = Aᵀ A = 0`, then `A = 0`, Hankel
    `H = A B = 0`, and `W_c W_o = 0`, whereas `W_c + W_o = W_o` remains intact. -/
theorem hankel_collapse_of_wc_zero (A : Matrix p m ℝ) (B : Matrix m f ℝ) (hWc : Aᵀ * A = 0) :
    A = 0 ∧ A * B = 0 ∧ (Aᵀ * A) * (B * Bᵀ) = 0 ∧ Aᵀ * A + B * Bᵀ = B * Bᵀ := by
  have htr : Matrix.trace (Aᵀ * A) = 0 := by simp [hWc]
  have hsum : (∑ j : m, ∑ i : p, A i j ^ 2) = 0 := by
    calc
      (∑ j : m, ∑ i : p, A i j ^ 2)
          = ∑ j : m, ∑ i : p, Aᵀ j i * A i j := by
            refine Finset.sum_congr rfl fun j _ => Finset.sum_congr rfl fun i _ => ?_
            simp [Matrix.transpose_apply, sq]
      _ = Matrix.trace (Aᵀ * A) := by
            unfold Matrix.trace
            refine Finset.sum_congr rfl fun j _ => ?_
            simp [Matrix.diag_apply, Matrix.mul_apply]
      _ = 0 := htr
  rw [Finset.sum_eq_zero_iff_of_nonneg (fun j _ => Finset.sum_nonneg fun i _ => sq_nonneg _)] at hsum
  have hA : A = 0 := by
    ext i j
    have hj := hsum j (Finset.mem_univ j)
    rw [Finset.sum_eq_zero_iff_of_nonneg (fun i' _ => sq_nonneg _)] at hj
    exact sq_eq_zero_iff.mp (hj i (Finset.mem_univ i))
  refine ⟨hA, ?_, ?_, ?_⟩
  · simp [hA]
  · simp [hWc]
  · simp [hWc]

/-- Squared Frobenius norm of Hankel `H = A B` equals the balanced product trace `Tr(W_c W_o)`. -/
theorem trace_hankel_eq_trace_wc_wo (A : Matrix p m ℝ) (B : Matrix m f ℝ) :
    Matrix.trace ((A * B)ᵀ * (A * B)) = Matrix.trace ((Aᵀ * A) * (B * Bᵀ)) := by
  calc
    Matrix.trace ((A * B)ᵀ * (A * B))
        = Matrix.trace (Bᵀ * (Aᵀ * (A * B))) := by
          rw [Matrix.transpose_mul, Matrix.mul_assoc]
    _ = Matrix.trace ((Aᵀ * (A * B)) * Bᵀ) := by rw [Matrix.trace_mul_comm]
    _ = Matrix.trace ((Aᵀ * A) * (B * Bᵀ)) := by simp only [Matrix.mul_assoc]

/-- Trace AM-GM inequality between balanced product and additive sum of squares. -/
theorem trace_wc_wo_am_gm (Wc Wo : Matrix m m ℝ) (hWc : Wcᵀ = Wc) (hWo : Woᵀ = Wo) :
    2 * Matrix.trace (Wc * Wo) ≤ Matrix.trace (Wc * Wc) + Matrix.trace (Wo * Wo) ∧
      (2 * Matrix.trace (Wc * Wo) = Matrix.trace (Wc * Wc) + Matrix.trace (Wo * Wo) ↔ Wc = Wo) := by
  have hsq : Matrix.trace ((Wc - Wo)ᵀ * (Wc - Wo)) =
      ∑ j : m, ∑ i : m, (Wc i j - Wo i j) ^ 2 := by
    unfold Matrix.trace
    refine Finset.sum_congr rfl fun j _ => ?_
    simp only [Matrix.diag_apply, Matrix.mul_apply, Matrix.transpose_apply, Matrix.sub_apply]
    refine Finset.sum_congr rfl fun i _ => ?_
    ring
  have hexp : Matrix.trace ((Wc - Wo)ᵀ * (Wc - Wo)) =
      Matrix.trace (Wc * Wc) + Matrix.trace (Wo * Wo) - 2 * Matrix.trace (Wc * Wo) := by
    have hT : (Wc - Wo)ᵀ = Wc - Wo := by rw [Matrix.transpose_sub, hWc, hWo]
    rw [hT, Matrix.sub_mul, Matrix.mul_sub, Matrix.mul_sub]
    simp only [Matrix.trace_sub, Matrix.trace_mul_comm Wo Wc]
    ring
  have hsum_nn : 0 ≤ ∑ j : m, ∑ i : m, (Wc i j - Wo i j) ^ 2 :=
    Finset.sum_nonneg fun j _ => Finset.sum_nonneg fun i _ => sq_nonneg _
  constructor
  · linarith
  · constructor
    · intro heq
      have hzero : (∑ j : m, ∑ i : m, (Wc i j - Wo i j) ^ 2) = 0 := by linarith
      rw [Finset.sum_eq_zero_iff_of_nonneg (fun j _ => Finset.sum_nonneg fun i _ => sq_nonneg _)] at hzero
      ext i j
      have hj := hzero j (Finset.mem_univ j)
      rw [Finset.sum_eq_zero_iff_of_nonneg (fun i' _ => sq_nonneg _)] at hj
      have hij : Wc i j - Wo i j = 0 := sq_eq_zero_iff.mp (hj i (Finset.mem_univ i))
      linarith
    · intro hEq
      subst hEq
      ring

private theorem trace_conj_orth_left (U : Matrix p p ℝ) (A : Matrix p m ℝ) (hU : U * Uᵀ = 1) :
    Matrix.trace ((Uᵀ * A) * (Uᵀ * A)ᵀ) = Matrix.trace (Aᵀ * A) := by
  calc
    Matrix.trace ((Uᵀ * A) * (Uᵀ * A)ᵀ)
        = Matrix.trace ((Uᵀ * A) * (Aᵀ * U)) := by rw [Matrix.transpose_mul, Matrix.transpose_transpose]
    _ = Matrix.trace ((Uᵀ * (A * Aᵀ)) * U) := by simp only [Matrix.mul_assoc]
    _ = Matrix.trace (U * (Uᵀ * (A * Aᵀ))) := by rw [Matrix.trace_mul_comm]
    _ = Matrix.trace ((U * Uᵀ) * (A * Aᵀ)) := by rw [Matrix.mul_assoc]
    _ = Matrix.trace (A * Aᵀ) := by rw [hU, Matrix.one_mul]
    _ = Matrix.trace (Aᵀ * A) := by rw [Matrix.trace_mul_comm]

private theorem trace_conj_orth_right (V : Matrix f f ℝ) (B : Matrix m f ℝ) (hV : V * Vᵀ = 1) :
    Matrix.trace ((B * V)ᵀ * (B * V)) = Matrix.trace (B * Bᵀ) := by
  calc
    Matrix.trace ((B * V)ᵀ * (B * V))
        = Matrix.trace ((Vᵀ * Bᵀ) * (B * V)) := by rw [Matrix.transpose_mul]
    _ = Matrix.trace ((Vᵀ * (Bᵀ * B)) * V) := by simp only [Matrix.mul_assoc]
    _ = Matrix.trace (V * (Vᵀ * (Bᵀ * B))) := by rw [Matrix.trace_mul_comm]
    _ = Matrix.trace ((V * Vᵀ) * (Bᵀ * B)) := by rw [Matrix.mul_assoc]
    _ = Matrix.trace (Bᵀ * B) := by rw [hV, Matrix.one_mul]
    _ = Matrix.trace (B * Bᵀ) := by rw [Matrix.trace_mul_comm]

private theorem entry_mul_le_half_sum_sq_gram (M : Matrix p m ℝ) (N : Matrix m f ℝ)
    (r : p) (c : f) :
    2 * (M * N) r c ≤ (M * Mᵀ) r r + (Nᵀ * N) c c := by
  simp only [Matrix.mul_apply, Matrix.transpose_apply]
  have hpt : ∀ j : m, 2 * (M r j * N j c) ≤ M r j * M r j + N j c * N j c := by
    intro j
    nlinarith [sq_nonneg (M r j - N j c)]
  have hsum : (∑ j : m, 2 * (M r j * N j c)) ≤
      ∑ j : m, (M r j * M r j + N j c * N j c) :=
    Finset.sum_le_sum fun j _ => hpt j
  rw [← Finset.mul_sum, Finset.sum_add_distrib] at hsum
  exact hsum

/-- Variational Hankel nuclear-norm bound: for any orthogonal frames `U, V` (`U Uᵀ = 1`, `V Vᵀ = 1`)
    and any injective pairings `e : Fin k ↪ p`, `g : Fin k ↪ f`, the singular-value sum of `H = A B`
    satisfies `∑ t, (Uᵀ H V)_{e(t), g(t)} ≤ (1 / 2) * Tr(W_c + W_o)`, with equality at balanced
    realization `W_c = W_o`. -/
theorem variational_nuclear_norm_bound
    (A : Matrix p m ℝ) (B : Matrix m f ℝ)
    (U : Matrix p p ℝ) (V : Matrix f f ℝ)
    (hU : U * Uᵀ = 1) (hV : V * Vᵀ = 1)
    {k : ℕ} (e : Fin k ↪ p) (g : Fin k ↪ f) :
    ∑ t : Fin k, (Uᵀ * (A * B) * V) (e t) (g t) ≤
      (1 / 2 : ℝ) * Matrix.trace (Aᵀ * A + B * Bᵀ) := by
  set M : Matrix p m ℝ := Uᵀ * A
  set N : Matrix m f ℝ := B * V
  have hMN : Uᵀ * (A * B) * V = M * N := by
    simp only [M, N, Matrix.mul_assoc]
  rw [hMN]
  have hterm : ∀ t : Fin k, 2 * (M * N) (e t) (g t) ≤ (M * Mᵀ) (e t) (e t) + (Nᵀ * N) (g t) (g t) :=
    fun t => entry_mul_le_half_sum_sq_gram M N (e t) (g t)
  have hsum1 : (∑ t : Fin k, 2 * (M * N) (e t) (g t)) ≤
      (∑ t : Fin k, (M * Mᵀ) (e t) (e t)) + ∑ t : Fin k, (Nᵀ * N) (g t) (g t) := by
    rw [← Finset.sum_add_distrib]
    exact Finset.sum_le_sum fun t _ => hterm t
  have hM_nn : ∀ r : p, 0 ≤ (M * Mᵀ) r r := by
    intro r
    simp only [Matrix.mul_apply, Matrix.transpose_apply]
    exact Finset.sum_nonneg fun j _ => mul_self_nonneg (M r j)
  have hN_nn : ∀ c : f, 0 ≤ (Nᵀ * N) c c := by
    intro c
    simp only [Matrix.mul_apply, Matrix.transpose_apply]
    exact Finset.sum_nonneg fun j _ => mul_self_nonneg (N j c)
  have hM_le : (∑ t : Fin k, (M * Mᵀ) (e t) (e t)) ≤ Matrix.trace (M * Mᵀ) := by
    calc
      (∑ t : Fin k, (M * Mᵀ) (e t) (e t))
          = ∑ r ∈ Finset.univ.map e, (M * Mᵀ) r r :=
            (Finset.sum_map Finset.univ e (fun r => (M * Mᵀ) r r)).symm
      _ ≤ ∑ r : p, (M * Mᵀ) r r :=
            Finset.sum_le_sum_of_subset_of_nonneg (Finset.subset_univ _) (fun r _ _ => hM_nn r)
      _ = Matrix.trace (M * Mᵀ) := rfl
  have hN_le : (∑ t : Fin k, (Nᵀ * N) (g t) (g t)) ≤ Matrix.trace (Nᵀ * N) := by
    calc
      (∑ t : Fin k, (Nᵀ * N) (g t) (g t))
          = ∑ c ∈ Finset.univ.map g, (Nᵀ * N) c c :=
            (Finset.sum_map Finset.univ g (fun c => (Nᵀ * N) c c)).symm
      _ ≤ ∑ c : f, (Nᵀ * N) c c :=
            Finset.sum_le_sum_of_subset_of_nonneg (Finset.subset_univ _) (fun c _ _ => hN_nn c)
      _ = Matrix.trace (Nᵀ * N) := rfl
  have htrM : Matrix.trace (M * Mᵀ) = Matrix.trace (Aᵀ * A) := trace_conj_orth_left U A hU
  have htrN : Matrix.trace (Nᵀ * N) = Matrix.trace (B * Bᵀ) := trace_conj_orth_right V B hV
  rw [← Finset.mul_sum] at hsum1
  rw [Matrix.trace_add]
  linarith

end HankelInterfaceGram

section ContractiveSSM

/-- Lag weight `ρ^(2t)` generated by isotropic scalar-pole linear recurrence `h_t = ρ h_{t-1} + u_t`. -/
theorem contractive_ssm_lag_weight (ρ : ℝ) (t : ℕ) :
    (ρ ^ t) ^ 2 = (ρ ^ 2) ^ t := by
  rw [← pow_mul, ← pow_mul, mul_comm]

/-- Finite-horizon geometric sum identity for the derived contractive discount factor `γ_c = ρ²`. -/
theorem contractive_ssm_geom_sum (ρ : ℝ) (T : ℕ) :
    (∑ t ∈ Finset.range T, (ρ ^ 2) ^ t) * (1 - ρ ^ 2) = 1 - (ρ ^ 2) ^ T := by
  induction T with
  | zero =>
      simp
  | succ k ih =>
      rw [Finset.sum_range_succ, add_mul, ih]
      ring

end ContractiveSSM

end

end MasterPrincipleHankel
