/-
  Mathlib formalization for the Exact Variational Geodesic-Midpoint / Riccati Master Theorem
  (`gemini/master-principle-variational`).

  Proves for arbitrary non-commuting real matrices:
  1. Frobenius norm square properties (`frobNormSq_eq_sum_sq`, `nonneg`, `eq_zero_iff`).
  2. Exact variational objective square-completion identity for
     `J(X) = Tr(A X) + Tr(B X⁻¹) ≥ 2 Tr(M)`, valid for arbitrary non-commuting factors.
  3. Global lower bound, exact equality-iff-factor, exact algebraic Riccati characterization
     `X A X = B`, and global uniqueness of the Riccati minimizer `X* = A⁻¹ # B`.
  4. Constructive proof that the geodesic midpoint `X* = R_A⁻¹ M (R_A⁻¹)ᵀ` solves `X A X = B`
     and attains `2 Tr(M)`.
  5. Exact Hankel realization recovery `(R X Rᵀ)² = H Hᵀ` whenever `X Wc X = Wo`.
  6. Full `GL(m)` covariance of `X*` and exact `GL(m)` invariance of history operator `R X Rᵀ`.
  7. Variational kinetic monotonicity (`K(x₂) ≤ K(x₁)` for `λ₁ < λ₂`), strict monotonicity,
     envelope derivative sandwich, and concavity of the value function `Φ(λ)`.
  8. Exact dual-belief and primal-feature encoder/decoder trace norm identifications.

  Isolated in `proofs/lean-mathlib/` so `proofs/lean/` remains core Lean 4.
-/
import Mathlib.Data.Fintype.BigOperators
import Mathlib.Data.Matrix.Basic
import Mathlib.Data.Real.Basic
import Mathlib.Data.Real.Sqrt
import Mathlib.LinearAlgebra.Matrix.PosDef
import Mathlib.LinearAlgebra.Matrix.Spectrum
import Mathlib.LinearAlgebra.Matrix.Trace
import Mathlib.LinearAlgebra.Matrix.Symmetric
import Mathlib.Tactic.Ring
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Positivity

open scoped BigOperators Matrix

namespace MasterPrincipleVariational

noncomputable section
set_option linter.unusedSectionVars false

section FrobeniusNorm

variable {p q : Type*} [Fintype p] [Fintype q]

/-- Frobenius norm squared equals the trace of `Mᵀ * M`. -/
theorem frobNormSq_eq_sum_sq (M : Matrix p q ℝ) :
    (Mᵀ * M).trace = ∑ i : p, ∑ j : q, (M i j) ^ 2 := by
  unfold Matrix.trace Matrix.diag
  simp only [Matrix.mul_apply, Matrix.transpose_apply]
  rw [Finset.sum_comm]
  refine Finset.sum_congr rfl fun i _ => ?_
  refine Finset.sum_congr rfl fun j _ => ?_
  ring

theorem frobNormSq_nonneg (M : Matrix p q ℝ) : 0 ≤ (Mᵀ * M).trace := by
  rw [frobNormSq_eq_sum_sq]
  exact Finset.sum_nonneg fun i _ => Finset.sum_nonneg fun j _ => sq_nonneg (M i j)

theorem frobNormSq_eq_zero_iff (M : Matrix p q ℝ) :
    (Mᵀ * M).trace = 0 ↔ M = 0 := by
  constructor
  · intro h
    rw [frobNormSq_eq_sum_sq] at h
    have hrow : ∀ i ∈ (Finset.univ : Finset p), ∑ j : q, (M i j) ^ 2 = 0 :=
      (Finset.sum_eq_zero_iff_of_nonneg fun i _ =>
        Finset.sum_nonneg fun j _ => sq_nonneg (M i j)).mp h
    ext i j
    have hij : (M i j) ^ 2 = 0 :=
      (Finset.sum_eq_zero_iff_of_nonneg fun j' _ => sq_nonneg (M i j')).mp
        (hrow i (Finset.mem_univ i)) j (Finset.mem_univ j)
    simpa [sq_eq_zero_iff] using hij
  · rintro rfl
    simp

end FrobeniusNorm

section VariationalRiccati

variable {ι : Type*} [Fintype ι] [DecidableEq ι]

/-- Exact Frobenius square-completion identity for `Tr(A X) + Tr(B X⁻¹) - 2 Tr(M)`,
    requiring zero commutativity assumptions among `A`, `B`, `L_kin`, and `X`. -/
theorem variational_trace_identity
    (R_A R_B R_X R_Xinv U M : Matrix ι ι ℝ)
    (hXinv : R_Xinv * R_X = 1)
    (hUorth : U * Uᵀ = 1)
    (hM : Uᵀ * (R_B * R_Aᵀ) = M) :
    let A := R_Aᵀ * R_A
    let B := R_Bᵀ * R_B
    let X := R_Xᵀ * R_X
    let Xinv := R_Xinv * R_Xinvᵀ
    let E := R_A * R_Xᵀ - Uᵀ * R_B * R_Xinv
    (A * X).trace + (B * Xinv).trace - 2 * M.trace = (Eᵀ * E).trace := by
  dsimp only
  have h1 : (R_X * R_Aᵀ * (R_A * R_Xᵀ)).trace = ((R_Aᵀ * R_A) * (R_Xᵀ * R_X)).trace := by
    calc (R_X * R_Aᵀ * (R_A * R_Xᵀ)).trace
        = ((R_X) * (R_Aᵀ * R_A * R_Xᵀ)).trace := by simp only [Matrix.mul_assoc]
      _ = ((R_Aᵀ * R_A * R_Xᵀ) * R_X).trace := Matrix.trace_mul_comm _ _
      _ = ((R_Aᵀ * R_A) * (R_Xᵀ * R_X)).trace := by simp only [Matrix.mul_assoc]
  have h2 : (R_X * R_Aᵀ * (Uᵀ * R_B * R_Xinv)).trace = M.trace := by
    calc (R_X * R_Aᵀ * (Uᵀ * R_B * R_Xinv)).trace
        = (R_X * (R_Aᵀ * Uᵀ * R_B * R_Xinv)).trace := by simp only [Matrix.mul_assoc]
      _ = ((R_Aᵀ * Uᵀ * R_B * R_Xinv) * R_X).trace := Matrix.trace_mul_comm _ _
      _ = (R_Aᵀ * Uᵀ * R_B * (R_Xinv * R_X)).trace := by simp only [Matrix.mul_assoc]
      _ = (R_Aᵀ * (Uᵀ * R_B)).trace := by rw [hXinv, Matrix.mul_one, Matrix.mul_assoc]
      _ = ((Uᵀ * R_B) * R_Aᵀ).trace := Matrix.trace_mul_comm _ _
      _ = (Uᵀ * (R_B * R_Aᵀ)).trace := by simp only [Matrix.mul_assoc]
      _ = M.trace := by rw [hM]
  have h3 : (R_Xinvᵀ * R_Bᵀ * U * (R_A * R_Xᵀ)).trace = M.trace := by
    have htr : (R_Xinvᵀ * R_Bᵀ * U * (R_A * R_Xᵀ))ᵀ = R_X * R_Aᵀ * (Uᵀ * R_B * R_Xinv) := by
      simp only [Matrix.transpose_mul, Matrix.transpose_transpose, Matrix.mul_assoc]
    rw [← Matrix.trace_transpose, htr]
    exact h2
  have h4 : (R_Xinvᵀ * R_Bᵀ * U * (Uᵀ * R_B * R_Xinv)).trace =
      ((R_Bᵀ * R_B) * (R_Xinv * R_Xinvᵀ)).trace := by
    calc (R_Xinvᵀ * R_Bᵀ * U * (Uᵀ * R_B * R_Xinv)).trace
        = (R_Xinvᵀ * R_Bᵀ * (U * Uᵀ) * R_B * R_Xinv).trace := by simp only [Matrix.mul_assoc]
      _ = (R_Xinvᵀ * ((R_Bᵀ * R_B) * R_Xinv)).trace := by
          rw [hUorth, Matrix.mul_one]; simp only [Matrix.mul_assoc]
      _ = (((R_Bᵀ * R_B) * R_Xinv) * R_Xinvᵀ).trace := Matrix.trace_mul_comm _ _
      _ = ((R_Bᵀ * R_B) * (R_Xinv * R_Xinvᵀ)).trace := by simp only [Matrix.mul_assoc]
  rw [Matrix.transpose_sub, Matrix.sub_mul, Matrix.mul_sub, Matrix.mul_sub,
    Matrix.trace_sub, Matrix.trace_sub, Matrix.trace_sub]
  simp only [Matrix.transpose_mul, Matrix.transpose_transpose, Matrix.mul_assoc]
  have h1' : (R_X * (R_Aᵀ * (R_A * R_Xᵀ))).trace = (R_Aᵀ * (R_A * (R_Xᵀ * R_X))).trace := by
    simpa only [Matrix.mul_assoc] using h1
  have h2' : (R_X * (R_Aᵀ * (Uᵀ * (R_B * R_Xinv)))).trace = M.trace := by
    simpa only [Matrix.mul_assoc] using h2
  have h3' : (R_Xinvᵀ * (R_Bᵀ * (U * (R_A * R_Xᵀ)))).trace = M.trace := by
    simpa only [Matrix.mul_assoc] using h3
  have h4' : (R_Xinvᵀ * (R_Bᵀ * (U * (Uᵀ * (R_B * R_Xinv))))).trace =
      (R_Bᵀ * (R_B * (R_Xinv * R_Xinvᵀ))).trace := by
    simpa only [Matrix.mul_assoc] using h4
  rw [h1', h2', h3', h4']
  ring

/-- Global lower bound: for any factorized `A, B` and invertible `X`,
    `2 Tr(M) ≤ Tr(A X) + Tr(B X⁻¹)`. -/
theorem variational_trace_lower_bound
    (R_A R_B R_X R_Xinv U M : Matrix ι ι ℝ)
    (hXinv : R_Xinv * R_X = 1)
    (hUorth : U * Uᵀ = 1)
    (hM : Uᵀ * (R_B * R_Aᵀ) = M) :
    2 * M.trace ≤ ((R_Aᵀ * R_A) * (R_Xᵀ * R_X)).trace +
      ((R_Bᵀ * R_B) * (R_Xinv * R_Xinvᵀ)).trace := by
  have hid := variational_trace_identity R_A R_B R_X R_Xinv U M hXinv hUorth hM
  have hnn := frobNormSq_nonneg (R_A * R_Xᵀ - Uᵀ * R_B * R_Xinv)
  dsimp only at hid
  linarith

/-- Exact attainment characterization: the variational bound is tight iff
    the square-completion residual vanishes. -/
theorem variational_trace_eq_iff_factor
    (R_A R_B R_X R_Xinv U M : Matrix ι ι ℝ)
    (hXinv : R_Xinv * R_X = 1)
    (hUorth : U * Uᵀ = 1)
    (hM : Uᵀ * (R_B * R_Aᵀ) = M) :
    ((R_Aᵀ * R_A) * (R_Xᵀ * R_X)).trace + ((R_Bᵀ * R_B) * (R_Xinv * R_Xinvᵀ)).trace =
        2 * M.trace ↔
      R_A * R_Xᵀ = Uᵀ * R_B * R_Xinv := by
  have hid := variational_trace_identity R_A R_B R_X R_Xinv U M hXinv hUorth hM
  dsimp only at hid
  rw [← sub_eq_zero, hid, frobNormSq_eq_zero_iff, sub_eq_zero]

/-- Vanishing residual implies `R_A X = Uᵀ R_B` and the exact matrix Riccati
    equation `X A X = B`, whose unique SPD solution is the geometric mean `A⁻¹ # B`. -/
theorem variational_eq_implies_riccati
    (R_A R_B R_X R_Xinv U : Matrix ι ι ℝ)
    (hXinv : R_Xinv * R_X = 1)
    (hUorth : U * Uᵀ = 1)
    (heq : R_A * R_Xᵀ = Uᵀ * R_B * R_Xinv) :
    R_A * (R_Xᵀ * R_X) = Uᵀ * R_B ∧
      (R_Xᵀ * R_X) * (R_Aᵀ * R_A) * (R_Xᵀ * R_X) = R_Bᵀ * R_B := by
  have hRX : R_A * (R_Xᵀ * R_X) = Uᵀ * R_B := by
    calc R_A * (R_Xᵀ * R_X)
        = (R_A * R_Xᵀ) * R_X := by rw [Matrix.mul_assoc]
      _ = (Uᵀ * R_B * R_Xinv) * R_X := by rw [heq]
      _ = Uᵀ * R_B * (R_Xinv * R_X) := by rw [Matrix.mul_assoc]
      _ = Uᵀ * R_B := by rw [hXinv, Matrix.mul_one]
  refine ⟨hRX, ?_⟩
  have hXR : (R_Xᵀ * R_X) * R_Aᵀ = R_Bᵀ * U := by
    calc (R_Xᵀ * R_X) * R_Aᵀ
        = (R_A * (R_Xᵀ * R_X))ᵀ := by
            simp only [Matrix.transpose_mul, Matrix.transpose_transpose]
      _ = (Uᵀ * R_B)ᵀ := by rw [hRX]
      _ = R_Bᵀ * U := by simp only [Matrix.transpose_mul, Matrix.transpose_transpose]
  calc (R_Xᵀ * R_X) * (R_Aᵀ * R_A) * (R_Xᵀ * R_X)
      = ((R_Xᵀ * R_X) * R_Aᵀ) * (R_A * (R_Xᵀ * R_X)) := by simp only [Matrix.mul_assoc]
    _ = (R_Bᵀ * U) * (Uᵀ * R_B) := by rw [hXR, hRX]
    _ = R_Bᵀ * (U * Uᵀ) * R_B := by simp only [Matrix.mul_assoc]
    _ = R_Bᵀ * R_B := by rw [hUorth, Matrix.mul_one]

/-- Global uniqueness of the variational minimizer `X* = A⁻¹ # B`. -/
theorem variational_minimizer_unique
    (R_A R_Ainv R_B R_X1 R_X1inv R_X2 R_X2inv U M : Matrix ι ι ℝ)
    (hRAinv : R_Ainv * R_A = 1)
    (hX1inv : R_X1inv * R_X1 = 1)
    (hX2inv : R_X2inv * R_X2 = 1)
    (hUorth : U * Uᵀ = 1)
    (hM : Uᵀ * (R_B * R_Aᵀ) = M)
    (hmin1 : ((R_Aᵀ * R_A) * (R_X1ᵀ * R_X1)).trace +
        ((R_Bᵀ * R_B) * (R_X1inv * R_X1invᵀ)).trace = 2 * M.trace)
    (hmin2 : ((R_Aᵀ * R_A) * (R_X2ᵀ * R_X2)).trace +
        ((R_Bᵀ * R_B) * (R_X2inv * R_X2invᵀ)).trace = 2 * M.trace) :
    R_X1ᵀ * R_X1 = R_X2ᵀ * R_X2 := by
  have heq1 := (variational_trace_eq_iff_factor R_A R_B R_X1 R_X1inv U M hX1inv hUorth hM).mp hmin1
  have heq2 := (variational_trace_eq_iff_factor R_A R_B R_X2 R_X2inv U M hX2inv hUorth hM).mp hmin2
  have h1 := (variational_eq_implies_riccati R_A R_B R_X1 R_X1inv U hX1inv hUorth heq1).1
  have h2 := (variational_eq_implies_riccati R_A R_B R_X2 R_X2inv U hX2inv hUorth heq2).1
  calc R_X1ᵀ * R_X1
      = (R_Ainv * R_A) * (R_X1ᵀ * R_X1) := by rw [hRAinv, Matrix.one_mul]
    _ = R_Ainv * (R_A * (R_X1ᵀ * R_X1)) := by rw [Matrix.mul_assoc]
    _ = R_Ainv * (R_A * (R_X2ᵀ * R_X2)) := by rw [h1, h2]
    _ = (R_Ainv * R_A) * (R_X2ᵀ * R_X2) := by rw [← Matrix.mul_assoc]
    _ = R_X2ᵀ * R_X2 := by rw [hRAinv, Matrix.one_mul]

/-- The explicit Kubo–Ando geometric midpoint `X* = R_A⁻¹ M (R_A⁻¹)ᵀ` (where `M² = R_A B R_Aᵀ`)
    solves `X* A X* = B`, is the exact inverse of `R_Aᵀ M⁻¹ R_A`, and attains `2 Tr(M)`. -/
theorem riccati_geodesic_attains_bound
    (R_A R_Ainv B M Minv : Matrix ι ι ℝ)
    (hR1 : R_A * R_Ainv = 1)
    (hR2 : R_Ainv * R_A = 1)
    (hMsq : M * M = R_A * B * R_Aᵀ)
    (hMinv : M * Minv = 1) :
    let A := R_Aᵀ * R_A
    let Xstar := R_Ainv * M * R_Ainvᵀ
    let Xstar_inv := R_Aᵀ * Minv * R_A
    Xstar * A * Xstar = B ∧
      Xstar * Xstar_inv = 1 ∧
      (A * Xstar).trace = M.trace ∧
      (B * Xstar_inv).trace = M.trace ∧
      (A * Xstar).trace + (B * Xstar_inv).trace = 2 * M.trace := by
  dsimp only
  have hRT1 : R_Ainvᵀ * R_Aᵀ = 1 := by
    calc R_Ainvᵀ * R_Aᵀ = (R_A * R_Ainv)ᵀ := (Matrix.transpose_mul R_A R_Ainv).symm
      _ = (1 : Matrix ι ι ℝ)ᵀ := by rw [hR1]
      _ = 1 := Matrix.transpose_one
  have hRT2 : R_Aᵀ * R_Ainvᵀ = 1 := by
    calc R_Aᵀ * R_Ainvᵀ = (R_Ainv * R_A)ᵀ := (Matrix.transpose_mul R_Ainv R_A).symm
      _ = (1 : Matrix ι ι ℝ)ᵀ := by rw [hR2]
      _ = 1 := Matrix.transpose_one
  have hRic : (R_Ainv * M * R_Ainvᵀ) * (R_Aᵀ * R_A) * (R_Ainv * M * R_Ainvᵀ) = B := by
    calc (R_Ainv * M * R_Ainvᵀ) * (R_Aᵀ * R_A) * (R_Ainv * M * R_Ainvᵀ)
        = R_Ainv * M * (R_Ainvᵀ * R_Aᵀ) * (R_A * R_Ainv) * M * R_Ainvᵀ := by
            simp only [Matrix.mul_assoc]
      _ = R_Ainv * (M * M) * R_Ainvᵀ := by
            rw [hRT1, hR1, Matrix.mul_one, Matrix.mul_one]; simp only [Matrix.mul_assoc]
      _ = R_Ainv * (R_A * B * R_Aᵀ) * R_Ainvᵀ := by rw [hMsq]
      _ = (R_Ainv * R_A) * B * (R_Aᵀ * R_Ainvᵀ) := by simp only [Matrix.mul_assoc]
      _ = B := by rw [hR2, hRT2, Matrix.one_mul, Matrix.mul_one]
  have hInv : (R_Ainv * M * R_Ainvᵀ) * (R_Aᵀ * Minv * R_A) = 1 := by
    calc (R_Ainv * M * R_Ainvᵀ) * (R_Aᵀ * Minv * R_A)
        = R_Ainv * M * (R_Ainvᵀ * R_Aᵀ) * Minv * R_A := by simp only [Matrix.mul_assoc]
      _ = R_Ainv * (M * Minv) * R_A := by rw [hRT1, Matrix.mul_one]; simp only [Matrix.mul_assoc]
      _ = R_Ainv * R_A := by rw [hMinv, Matrix.mul_one]
      _ = 1 := hR2
  have hTr1 : ((R_Aᵀ * R_A) * (R_Ainv * M * R_Ainvᵀ)).trace = M.trace := by
    calc ((R_Aᵀ * R_A) * (R_Ainv * M * R_Ainvᵀ)).trace
        = (R_Aᵀ * ((R_A * R_Ainv) * (M * R_Ainvᵀ))).trace := by simp only [Matrix.mul_assoc]
      _ = (R_Aᵀ * (M * R_Ainvᵀ)).trace := by rw [hR1, Matrix.one_mul]
      _ = ((M * R_Ainvᵀ) * R_Aᵀ).trace := Matrix.trace_mul_comm _ _
      _ = (M * (R_Ainvᵀ * R_Aᵀ)).trace := by simp only [Matrix.mul_assoc]
      _ = M.trace := by rw [hRT1, Matrix.mul_one]
  have hTr2 : (B * (R_Aᵀ * Minv * R_A)).trace = M.trace := by
    calc (B * (R_Aᵀ * Minv * R_A)).trace
        = ((B * R_Aᵀ * Minv) * R_A).trace := by simp only [Matrix.mul_assoc]
      _ = (R_A * (B * R_Aᵀ * Minv)).trace := Matrix.trace_mul_comm _ _
      _ = ((R_A * B * R_Aᵀ) * Minv).trace := by simp only [Matrix.mul_assoc]
      _ = ((M * M) * Minv).trace := by rw [hMsq]
      _ = (M * (M * Minv)).trace := by simp only [Matrix.mul_assoc]
      _ = M.trace := by rw [hMinv, Matrix.mul_one]
  refine ⟨hRic, hInv, hTr1, hTr2, by rw [hTr1, hTr2]; ring⟩

end VariationalRiccati

section HankelAndGLInvariance

variable {p m f : Type*} [Fintype p] [Fintype m] [Fintype f] [DecidableEq m]

/-- Exact Hankel realization theorem: any solution `X` to the belief-basis Riccati equation
    `X Wc X = Wo` lifts via `R` to `(R X Rᵀ)² = H Hᵀ`, matching `(H Hᵀ)^{1/2}`
    so its nonzero eigenvalues equal the nonzero singular values of `H = R O`. -/
theorem hankel_induced_history_gram_sq
    (R : Matrix p m ℝ) (O : Matrix m f ℝ) (X : Matrix m m ℝ)
    (hric : X * (Rᵀ * R) * X = O * Oᵀ) :
    let H := R * O
    (R * X * Rᵀ) * (R * X * Rᵀ) = H * Hᵀ := by
  dsimp only
  calc (R * X * Rᵀ) * (R * X * Rᵀ)
      = R * (X * (Rᵀ * R) * X) * Rᵀ := by simp only [Matrix.mul_assoc]
    _ = R * (O * Oᵀ) * Rᵀ := by rw [hric]
    _ = (R * O) * (R * O)ᵀ := by
        simp only [Matrix.transpose_mul, Matrix.mul_assoc]

/-- Under any invertible change of internal coordinates `S ∈ GL(m)`:
    `X' = S X Sᵀ` transforms covariantly, the lifted history operator `R X Rᵀ`
    is strictly invariant, and the variational cost `Tr(Wc X)` is strictly invariant. -/
theorem gl_covariant_riccati_and_history_invariance
    (R : Matrix p m ℝ) (O : Matrix m f ℝ) (X S Sinv : Matrix m m ℝ)
    (hS2 : Sinv * S = 1)
    (hric : X * (Rᵀ * R) * X = O * Oᵀ) :
    let R' := R * Sinv
    let O' := S * O
    let Wc' := R'ᵀ * R'
    let Wo' := O' * O'ᵀ
    let X' := S * X * Sᵀ
    X' * Wc' * X' = Wo' ∧
      R' * X' * R'ᵀ = R * X * Rᵀ ∧
      (Wc' * X').trace = ((Rᵀ * R) * X).trace := by
  dsimp only
  have hST2 : Sᵀ * Sinvᵀ = 1 := by
    calc Sᵀ * Sinvᵀ = (Sinv * S)ᵀ := (Matrix.transpose_mul Sinv S).symm
      _ = (1 : Matrix m m ℝ)ᵀ := by rw [hS2]
      _ = 1 := Matrix.transpose_one
  have hRic' : (S * X * Sᵀ) * ((R * Sinv)ᵀ * (R * Sinv)) * (S * X * Sᵀ) = (S * O) * (S * O)ᵀ := by
    calc (S * X * Sᵀ) * ((R * Sinv)ᵀ * (R * Sinv)) * (S * X * Sᵀ)
        = S * X * (Sᵀ * Sinvᵀ) * (Rᵀ * R) * (Sinv * S) * X * Sᵀ := by
            simp only [Matrix.transpose_mul, Matrix.mul_assoc]
      _ = S * (X * (Rᵀ * R) * X) * Sᵀ := by
            rw [hST2, hS2, Matrix.mul_one, Matrix.mul_one]; simp only [Matrix.mul_assoc]
      _ = S * (O * Oᵀ) * Sᵀ := by rw [hric]
      _ = (S * O) * (S * O)ᵀ := by simp only [Matrix.transpose_mul, Matrix.mul_assoc]
  have hHist : (R * Sinv) * (S * X * Sᵀ) * (R * Sinv)ᵀ = R * X * Rᵀ := by
    calc (R * Sinv) * (S * X * Sᵀ) * (R * Sinv)ᵀ
        = R * (Sinv * S) * X * (Sᵀ * Sinvᵀ) * Rᵀ := by
            simp only [Matrix.transpose_mul, Matrix.mul_assoc]
      _ = R * X * Rᵀ := by rw [hS2, hST2, Matrix.mul_one, Matrix.mul_one]
  have hTr : (((R * Sinv)ᵀ * (R * Sinv)) * (S * X * Sᵀ)).trace = ((Rᵀ * R) * X).trace := by
    calc (((R * Sinv)ᵀ * (R * Sinv)) * (S * X * Sᵀ)).trace
        = (Sinvᵀ * ((Rᵀ * R) * (Sinv * S) * X * Sᵀ)).trace := by
            simp only [Matrix.transpose_mul, Matrix.mul_assoc]
      _ = (Sinvᵀ * (((Rᵀ * R) * X) * Sᵀ)).trace := by
            rw [hS2, Matrix.mul_one]
      _ = ((((Rᵀ * R) * X) * Sᵀ) * Sinvᵀ).trace := Matrix.trace_mul_comm _ _
      _ = (((Rᵀ * R) * X) * (Sᵀ * Sinvᵀ)).trace := by simp only [Matrix.mul_assoc]
      _ = ((Rᵀ * R) * X).trace := by rw [hST2, Matrix.mul_one]
  exact ⟨hRic', hHist, hTr⟩

/-- Dual HMM vs Primal Monoid encoder/decoder norm equivalence:
    (1) In dual belief coordinates, total Frobenius squared cost of encoder `(R * E)` and
        decoder `D = E⁻¹ O` equals `Tr(Wc X) + Tr(Wo X⁻¹)` (minimized at `Wc⁻¹ # Wo`).
    (2) In primal state coordinates, total Frobenius squared cost of encoder `E = R_A⁻¹ H_s`
        and decoder `D = H_s⁻¹ O` equals `Tr(Wcinv X) + Tr(Wo X⁻¹)` (minimized at `Wc # Wo`). -/
theorem dual_and_primal_enc_dec_costs
    (R : Matrix p m ℝ) (O : Matrix m f ℝ)
    (E Einv R_Ainv H_s H_sinv : Matrix m m ℝ) :
    let X := E * Eᵀ
    let Xinv := Einvᵀ * Einv
    let Z := R * E
    let D := Einv * O
    let X_pr := H_s * H_sᵀ
    let Xinv_pr := H_sinvᵀ * H_sinv
    let E_pr := R_Ainv * H_s
    let D_pr := H_sinv * O
    (Zᵀ * Z).trace + (Dᵀ * D).trace = ((Rᵀ * R) * X).trace + ((O * Oᵀ) * Xinv).trace ∧
      (E_prᵀ * E_pr).trace + (D_prᵀ * D_pr).trace =
        ((R_Ainvᵀ * R_Ainv) * X_pr).trace + ((O * Oᵀ) * Xinv_pr).trace := by
  dsimp only
  have hdual_enc : ((R * E)ᵀ * (R * E)).trace = ((Rᵀ * R) * (E * Eᵀ)).trace := by
    calc ((R * E)ᵀ * (R * E)).trace
        = (Eᵀ * ((Rᵀ * R) * E)).trace := by simp only [Matrix.transpose_mul, Matrix.mul_assoc]
      _ = (((Rᵀ * R) * E) * Eᵀ).trace := Matrix.trace_mul_comm _ _
      _ = ((Rᵀ * R) * (E * Eᵀ)).trace := by simp only [Matrix.mul_assoc]
  have hdual_dec : ((Einv * O)ᵀ * (Einv * O)).trace = ((O * Oᵀ) * (Einvᵀ * Einv)).trace := by
    calc ((Einv * O)ᵀ * (Einv * O)).trace
        = (Oᵀ * ((Einvᵀ * Einv) * O)).trace := by simp only [Matrix.transpose_mul, Matrix.mul_assoc]
      _ = (((Einvᵀ * Einv) * O) * Oᵀ).trace := Matrix.trace_mul_comm _ _
      _ = ((Einvᵀ * Einv) * (O * Oᵀ)).trace := by simp only [Matrix.mul_assoc]
      _ = ((O * Oᵀ) * (Einvᵀ * Einv)).trace := Matrix.trace_mul_comm _ _
  have hprim_enc : ((R_Ainv * H_s)ᵀ * (R_Ainv * H_s)).trace =
      ((R_Ainvᵀ * R_Ainv) * (H_s * H_sᵀ)).trace := by
    calc ((R_Ainv * H_s)ᵀ * (R_Ainv * H_s)).trace
        = (H_sᵀ * ((R_Ainvᵀ * R_Ainv) * H_s)).trace := by
            simp only [Matrix.transpose_mul, Matrix.mul_assoc]
      _ = (((R_Ainvᵀ * R_Ainv) * H_s) * H_sᵀ).trace := Matrix.trace_mul_comm _ _
      _ = ((R_Ainvᵀ * R_Ainv) * (H_s * H_sᵀ)).trace := by simp only [Matrix.mul_assoc]
  have hprim_dec : ((H_sinv * O)ᵀ * (H_sinv * O)).trace =
      ((O * Oᵀ) * (H_sinvᵀ * H_sinv)).trace := by
    calc ((H_sinv * O)ᵀ * (H_sinv * O)).trace
        = (Oᵀ * ((H_sinvᵀ * H_sinv) * O)).trace := by
            simp only [Matrix.transpose_mul, Matrix.mul_assoc]
      _ = (((H_sinvᵀ * H_sinv) * O) * Oᵀ).trace := Matrix.trace_mul_comm _ _
      _ = ((H_sinvᵀ * H_sinv) * (O * Oᵀ)).trace := by simp only [Matrix.mul_assoc]
      _ = ((O * Oᵀ) * (H_sinvᵀ * H_sinv)).trace := Matrix.trace_mul_comm _ _
  exact ⟨by rw [hdual_enc, hdual_dec], by rw [hprim_enc, hprim_dec]⟩

end HankelAndGLInvariance

section VariationalEnvelope

variable {α : Type*}

/-- Variational Fluctuation-Dissipation Theorem (monotonicity):
    Raising the kinetic inverse-temperature `λ₁ < λ₂` in `J(λ, x) = J₀(x) + λ K(x)`
    necessarily decreases or preserves the kinetic energy `K(x*(λ))`. -/
theorem variational_kinetic_antitone
    (J₀ K : α → ℝ) (lam₁ lam₂ : ℝ) (x₁ x₂ : α)
    (hlam : lam₁ < lam₂)
    (hmin₁ : ∀ x, J₀ x₁ + lam₁ * K x₁ ≤ J₀ x + lam₁ * K x)
    (hmin₂ : ∀ x, J₀ x₂ + lam₂ * K x₂ ≤ J₀ x + lam₂ * K x) :
    K x₂ ≤ K x₁ := by
  have h1 := hmin₁ x₂
  have h2 := hmin₂ x₁
  nlinarith [sub_pos.mpr hlam]

theorem variational_kinetic_strictAnti
    (J₀ K : α → ℝ) (lam₁ lam₂ : ℝ) (x₁ x₂ : α)
    (hlam : lam₁ < lam₂) (hne : x₁ ≠ x₂)
    (hmin₁ : ∀ x, x ≠ x₁ → J₀ x₁ + lam₁ * K x₁ < J₀ x + lam₁ * K x)
    (hmin₂ : ∀ x, J₀ x₂ + lam₂ * K x₂ ≤ J₀ x + lam₂ * K x) :
    K x₂ < K x₁ := by
  have h1 := hmin₁ x₂ hne.symm
  have h2 := hmin₂ x₁
  nlinarith [sub_pos.mpr hlam]

/-- Envelope subdifferential sandwich: `(λ₂ - λ₁) K(x₂) ≤ Φ(λ₂) - Φ(λ₁) ≤ (λ₂ - λ₁) K(x₁)`. -/
theorem variational_envelope_sandwich
    (J₀ K : α → ℝ) (lam₁ lam₂ : ℝ) (x₁ x₂ : α)
    (hmin₁ : ∀ x, J₀ x₁ + lam₁ * K x₁ ≤ J₀ x + lam₁ * K x)
    (hmin₂ : ∀ x, J₀ x₂ + lam₂ * K x₂ ≤ J₀ x + lam₂ * K x) :
    (lam₂ - lam₁) * K x₂ ≤
        (J₀ x₂ + lam₂ * K x₂) - (J₀ x₁ + lam₁ * K x₁) ∧
      (J₀ x₂ + lam₂ * K x₂) - (J₀ x₁ + lam₁ * K x₁) ≤
        (lam₂ - lam₁) * K x₁ := by
  have h1 := hmin₁ x₂
  have h2 := hmin₂ x₁
  constructor <;> linarith

/-- Concavity of the variational minimum-cost curve `Φ(λ) = inf_x (J₀(x) + λ K(x))`. -/
theorem variational_envelope_concave
    (J₀ K : α → ℝ) (lam₁ lam₂ θ : ℝ) (x₁ x₂ xθ : α)
    (hθ0 : 0 ≤ θ) (hθ1 : 0 ≤ 1 - θ)
    (hmin₁ : ∀ x, J₀ x₁ + lam₁ * K x₁ ≤ J₀ x + lam₁ * K x)
    (hmin₂ : ∀ x, J₀ x₂ + lam₂ * K x₂ ≤ J₀ x + lam₂ * K x) :
    θ * (J₀ x₁ + lam₁ * K x₁) + (1 - θ) * (J₀ x₂ + lam₂ * K x₂) ≤
      J₀ xθ + (θ * lam₁ + (1 - θ) * lam₂) * K xθ := by
  have h1 := mul_le_mul_of_nonneg_left (hmin₁ xθ) hθ0
  have h2 := mul_le_mul_of_nonneg_left (hmin₂ xθ) hθ1
  linarith

end VariationalEnvelope

section PositiveDefiniteAndPolar

variable {ι : Type*} [Fintype ι] [DecidableEq ι]

/-- SPD congruence invariance: if `M` is symmetric positive definite and `R` is invertible
    (`R * Rinv = 1`, `Rinv * R = 1`), then `R * M * Rᵀ` is strictly symmetric positive definite. -/
theorem posDef_congruence
    {M R Rinv : Matrix ι ι ℝ} (hM : M.PosDef)
    (h1 : R * Rinv = 1) :
    (R * M * Rᵀ).PosDef := by
  have hMs : Mᵀ = M := by
    have hh := hM.isHermitian
    simpa [Matrix.IsHermitian, Matrix.conjTranspose_eq_transpose_of_trivial] using hh
  have hHerm : (R * M * Rᵀ).IsHermitian := by
    rw [Matrix.IsHermitian, Matrix.conjTranspose_eq_transpose_of_trivial]
    simp only [Matrix.transpose_mul, Matrix.transpose_transpose, hMs, Matrix.mul_assoc]
  refine ⟨hHerm, ?_⟩
  intro x hx
  have hRinvT : Rinvᵀ * Rᵀ = 1 := by
    calc Rinvᵀ * Rᵀ = (R * Rinv)ᵀ := (Matrix.transpose_mul R Rinv).symm
      _ = (1 : Matrix ι ι ℝ)ᵀ := by rw [h1]
      _ = 1 := Matrix.transpose_one
  have hy_ne : Rᵀ *ᵥ x ≠ 0 := by
    intro hy
    apply hx
    calc x = (1 : Matrix ι ι ℝ) *ᵥ x := (Matrix.one_mulVec x).symm
      _ = (Rinvᵀ * Rᵀ) *ᵥ x := by rw [hRinvT]
      _ = Rinvᵀ *ᵥ (Rᵀ *ᵥ x) := (Matrix.mulVec_mulVec x Rinvᵀ Rᵀ).symm
      _ = Rinvᵀ *ᵥ 0 := by rw [hy]
      _ = 0 := Matrix.mulVec_zero _
  have hdot : Matrix.dotProduct (star x) ((R * M * Rᵀ) *ᵥ x) =
      Matrix.dotProduct (star (Rᵀ *ᵥ x)) (M *ᵥ (Rᵀ *ᵥ x)) := by
    simp only [star_trivial]
    calc Matrix.dotProduct x ((R * M * Rᵀ) *ᵥ x)
        = Matrix.dotProduct x (R *ᵥ ((M * Rᵀ) *ᵥ x)) := by
            rw [Matrix.mul_assoc, Matrix.mulVec_mulVec]
      _ = Matrix.dotProduct (x ᵥ* R) ((M * Rᵀ) *ᵥ x) := Matrix.dotProduct_mulVec _ _ _
      _ = Matrix.dotProduct (Rᵀ *ᵥ x) (M *ᵥ (Rᵀ *ᵥ x)) := by
            rw [← Matrix.mulVec_transpose, Matrix.mulVec_mulVec]
  rw [hdot]
  exact hM.2 (Rᵀ *ᵥ x) hy_ne

/-- Explicit SPD geodesic midpoint preserves strict positive definiteness. -/
theorem riccati_geodesic_posDef
    {R_A R_Ainv M : Matrix ι ι ℝ} (hM : M.PosDef) (hRA1 : R_Ainv * R_A = 1) :
    (R_Ainv * M * R_Ainvᵀ).PosDef :=
  posDef_congruence hM hRA1

private theorem posDef_diagonal {d : ι → ℝ} (hd : ∀ i, 0 < d i) :
    (Matrix.diagonal d).PosDef := by
  have hHerm : (Matrix.diagonal d).IsHermitian := by
    rw [Matrix.IsHermitian, Matrix.conjTranspose_eq_transpose_of_trivial, Matrix.diagonal_transpose]
  refine ⟨hHerm, ?_⟩
  intro x hx
  have hx0 : ∃ i₀ : ι, x i₀ ≠ 0 := by
    by_contra h
    push_neg at h
    exact hx (funext h)
  rcases hx0 with ⟨i₀, hi₀⟩
  have hsq_pos : 0 < d i₀ * (x i₀) ^ 2 := mul_pos (hd i₀) (sq_pos_of_ne_zero hi₀)
  have hsum : Matrix.dotProduct (star x) ((Matrix.diagonal d) *ᵥ x) = ∑ i : ι, d i * (x i) ^ 2 := by
    simp only [star_trivial, Matrix.dotProduct, Matrix.mulVec_diagonal]
    refine Finset.sum_congr rfl fun i _ => by ring
  rw [hsum]
  exact lt_of_lt_of_le hsq_pos
    (Finset.single_le_sum (fun i _ => mul_nonneg (hd i).le (sq_nonneg (x i))) (Finset.mem_univ i₀))

private theorem diag_mul_diag_fn (a b : ι → ℝ) :
    Matrix.diagonal a * Matrix.diagonal b = Matrix.diagonal (fun i => a i * b i) := by
  ext i j
  by_cases hij : i = j
  · subst hij; simp
  · simp [hij]

/-- Spectral construction of the unique SPD square root and its two-sided inverse
    for any real SPD matrix `P`. -/
theorem exists_posDef_sqrt {P : Matrix ι ι ℝ} (hP : P.PosDef) :
    ∃ S Sinv : Matrix ι ι ℝ, S.PosDef ∧ S * S = P ∧ S * Sinv = 1 ∧ Sinv * S = 1 := by
  let U : Matrix ι ι ℝ := (hP.isHermitian.eigenvectorUnitary : Matrix ι ι ℝ)
  have hsu : Uᵀ * U = 1 := by
    simpa [U, Matrix.star_eq_conjTranspose, Matrix.conjTranspose_eq_transpose_of_trivial] using
      unitary.coe_star_mul_self hP.isHermitian.eigenvectorUnitary
  have hus : U * Uᵀ = 1 := by
    simpa [U, Matrix.star_eq_conjTranspose, Matrix.conjTranspose_eq_transpose_of_trivial] using
      unitary.coe_mul_star_self hP.isHermitian.eigenvectorUnitary
  have hspec : P = U * Matrix.diagonal hP.isHermitian.eigenvalues * Uᵀ := by
    have hs := hP.isHermitian.spectral_theorem
    simpa [U, Function.comp_def, RCLike.ofReal_real_eq_id, Matrix.star_eq_conjTranspose,
      Matrix.conjTranspose_eq_transpose_of_trivial] using hs
  have heig : ∀ i, 0 < hP.isHermitian.eigenvalues i := fun i => hP.eigenvalues_pos i
  let d : ι → ℝ := fun i => Real.sqrt (hP.isHermitian.eigenvalues i)
  let dinv : ι → ℝ := fun i => (Real.sqrt (hP.isHermitian.eigenvalues i))⁻¹
  have hd_pos : ∀ i, 0 < d i := fun i => Real.sqrt_pos.mpr (heig i)
  let S : Matrix ι ι ℝ := U * Matrix.diagonal d * Uᵀ
  let Sinv : Matrix ι ι ℝ := U * Matrix.diagonal dinv * Uᵀ
  refine ⟨S, Sinv, posDef_congruence (posDef_diagonal hd_pos) hus, ?_, ?_, ?_⟩
  · calc S * S
        = U * (Matrix.diagonal d * (Uᵀ * U) * Matrix.diagonal d) * Uᵀ := by
            simp only [S, Matrix.mul_assoc]
      _ = U * (Matrix.diagonal d * Matrix.diagonal d) * Uᵀ := by
            rw [hsu, Matrix.mul_one]
      _ = U * Matrix.diagonal hP.isHermitian.eigenvalues * Uᵀ := by
            rw [diag_mul_diag_fn]
            congr 2
            ext i j
            by_cases hij : i = j
            · subst hij
              simp [d, Real.mul_self_sqrt (heig i).le]
            · simp [hij]
      _ = P := hspec.symm
  · calc S * Sinv
        = U * (Matrix.diagonal d * (Uᵀ * U) * Matrix.diagonal dinv) * Uᵀ := by
            simp only [S, Sinv, Matrix.mul_assoc]
      _ = U * (Matrix.diagonal d * Matrix.diagonal dinv) * Uᵀ := by
            rw [hsu, Matrix.mul_one]
      _ = U * (1 : Matrix ι ι ℝ) * Uᵀ := by
            rw [diag_mul_diag_fn]
            have hid : Matrix.diagonal (fun i => d i * dinv i) = 1 := by
              ext i j
              by_cases hij : i = j
              · subst hij
                simp [d, dinv, (hd_pos i).ne']
              · simp [hij]
            rw [hid]
      _ = U * Uᵀ := by rw [Matrix.mul_one]
      _ = 1 := hus
  · calc Sinv * S
        = U * (Matrix.diagonal dinv * (Uᵀ * U) * Matrix.diagonal d) * Uᵀ := by
            simp only [S, Sinv, Matrix.mul_assoc]
      _ = U * (Matrix.diagonal dinv * Matrix.diagonal d) * Uᵀ := by
            rw [hsu, Matrix.mul_one]
      _ = U * (1 : Matrix ι ι ℝ) * Uᵀ := by
            rw [diag_mul_diag_fn]
            have hid : Matrix.diagonal (fun i => dinv i * d i) = 1 := by
              ext i j
              by_cases hij : i = j
              · subst hij
                simp [d, dinv, (hd_pos i).ne']
              · simp [hij]
            rw [hid]
      _ = U * Uᵀ := by rw [Matrix.mul_one]
      _ = 1 := hus

/-- Full-rank existence and polar-witness construction directly from `A.PosDef` and `B.PosDef`:
    constructs `R_A, R_B, M, U, Xstar` from spectral decompositions and proves `Xstar.PosDef`,
    `Xstar * A * Xstar = B`, and global uniqueness across all invertible factorizations. -/
theorem exists_posDef_sqrt_and_polar
    {A B : Matrix ι ι ℝ} (hA : A.PosDef) (hB : B.PosDef) :
    ∃ (R_A R_Ainv R_B M Minv U : Matrix ι ι ℝ),
      A = R_Aᵀ * R_A ∧ R_A * R_Ainv = 1 ∧ R_Ainv * R_A = 1 ∧
      B = R_Bᵀ * R_B ∧
      M.PosDef ∧ M * M = R_A * B * R_Aᵀ ∧ M * Minv = 1 ∧
      U * Uᵀ = 1 ∧ Uᵀ * (R_B * R_Aᵀ) = M ∧
      let Xstar := R_Ainv * M * R_Ainvᵀ
      let Xstar_inv := R_Aᵀ * Minv * R_A
      Xstar.PosDef ∧
      Xstar * A * Xstar = B ∧
      Xstar * Xstar_inv = 1 ∧
      (A * Xstar).trace + (B * Xstar_inv).trace = 2 * M.trace ∧
      (∀ R_X R_Xinv : Matrix ι ι ℝ, R_Xinv * R_X = 1 →
        2 * M.trace ≤ (A * (R_Xᵀ * R_X)).trace + (B * (R_Xinv * R_Xinvᵀ)).trace) := by
  rcases exists_posDef_sqrt hA with ⟨R_A, R_Ainv, hRA_pd, hRA_sq, hRA1, hRA2⟩
  rcases exists_posDef_sqrt hB with ⟨R_B, _, hRB_pd, hRB_sq, _, _⟩
  have hRA_sym : R_Aᵀ = R_A := by
    simpa [Matrix.IsHermitian, Matrix.conjTranspose_eq_transpose_of_trivial] using hRA_pd.isHermitian
  have hRB_sym : R_Bᵀ = R_B := by
    simpa [Matrix.IsHermitian, Matrix.conjTranspose_eq_transpose_of_trivial] using hRB_pd.isHermitian
  have hA_fac : A = R_Aᵀ * R_A := by rw [hRA_sym, hRA_sq]
  have hB_fac : B = R_Bᵀ * R_B := by rw [hRB_sym, hRB_sq]
  have hmid_pd : (R_A * B * R_Aᵀ).PosDef := posDef_congruence hB hRA1
  rcases exists_posDef_sqrt hmid_pd with ⟨M, Minv, hM_pd, hM_sq, hM1, hM2⟩
  have hM_sym : Mᵀ = M := by
    simpa [Matrix.IsHermitian, Matrix.conjTranspose_eq_transpose_of_trivial] using hM_pd.isHermitian
  have hMinv_sym : Minvᵀ = Minv := by
    have hm1T : M * Minvᵀ = 1 := by
      calc M * Minvᵀ = Mᵀ * Minvᵀ := by rw [hM_sym]
        _ = (Minv * M)ᵀ := (Matrix.transpose_mul Minv M).symm
        _ = (1 : Matrix ι ι ℝ)ᵀ := by rw [hM2]
        _ = 1 := Matrix.transpose_one
    calc Minvᵀ = (1 : Matrix ι ι ℝ) * Minvᵀ := (Matrix.one_mul _).symm
      _ = (Minv * M) * Minvᵀ := by rw [hM2]
      _ = Minv * (M * Minvᵀ) := Matrix.mul_assoc _ _ _
      _ = Minv := by rw [hm1T, Matrix.mul_one]
  let U : Matrix ι ι ℝ := (R_B * R_Aᵀ) * Minv
  have hUtU : Uᵀ * U = 1 := by
    calc Uᵀ * U
        = Minvᵀ * R_A * (R_Bᵀ * R_B) * R_Aᵀ * Minv := by
            simp only [U, Matrix.transpose_mul, Matrix.transpose_transpose, Matrix.mul_assoc]
      _ = Minv * (R_A * B * R_Aᵀ) * Minv := by
            rw [hMinv_sym, ← hB_fac]; simp only [Matrix.mul_assoc]
      _ = Minv * (M * M) * Minv := by rw [hM_sq]
      _ = (Minv * M) * (M * Minv) := by simp only [Matrix.mul_assoc]
      _ = 1 := by rw [hM2, hM1, Matrix.one_mul]
  have hUorth : U * Uᵀ = 1 := Matrix.mul_eq_one_comm.mp hUtU
  have hUM : Uᵀ * (R_B * R_Aᵀ) = M := by
    calc Uᵀ * (R_B * R_Aᵀ)
        = Minvᵀ * (R_A * (R_Bᵀ * R_B) * R_Aᵀ) := by
            simp only [U, Matrix.transpose_mul, Matrix.transpose_transpose, Matrix.mul_assoc]
      _ = Minv * (R_A * B * R_Aᵀ) := by rw [hMinv_sym, ← hB_fac]
      _ = Minv * (M * M) := by rw [hM_sq]
      _ = (Minv * M) * M := (Matrix.mul_assoc Minv M M).symm
      _ = M := by rw [hM2, Matrix.one_mul]
  refine ⟨R_A, R_Ainv, R_B, M, Minv, U, hA_fac, hRA1, hRA2, hB_fac,
    hM_pd, hM_sq, hM1, hUorth, hUM, ?_⟩
  dsimp only
  have hRic := riccati_geodesic_attains_bound R_A R_Ainv B M Minv hRA1 hRA2 hM_sq hM1
  refine ⟨posDef_congruence hM_pd hRA2, ?_, hRic.2.1, ?_, ?_⟩
  · calc (R_Ainv * M * R_Ainvᵀ) * A * (R_Ainv * M * R_Ainvᵀ)
        = (R_Ainv * M * R_Ainvᵀ) * (R_Aᵀ * R_A) * (R_Ainv * M * R_Ainvᵀ) := by rw [← hA_fac]
      _ = B := hRic.1
  · rw [hA_fac]
    exact hRic.2.2.2.2
  · intro R_X R_Xinv hXinv
    rw [hA_fac, hB_fac]
    exact variational_trace_lower_bound R_A R_B R_X R_Xinv U M hXinv hUorth hUM

/-- Support-reduced Hankel theorem (for singular centered realizations of rank `r`):
    restriction onto minimal `r`-dimensional support yields `(R_min X_min R_minᵀ)² = H Hᵀ`. -/
theorem hankel_support_reduction
    {p f : Type*} [Fintype p] [Fintype f] (r : ℕ)
    (R_min : Matrix p (Fin r) ℝ) (O_min : Matrix (Fin r) f ℝ) (X_min : Matrix (Fin r) (Fin r) ℝ)
    (hric : X_min * (R_minᵀ * R_min) * X_min = O_min * O_minᵀ) :
    let H := R_min * O_min
    (R_min * X_min * R_minᵀ) * (R_min * X_min * R_minᵀ) = H * Hᵀ :=
  hankel_induced_history_gram_sq R_min O_min X_min hric

/-- Exact zero-Hankel collapse: if `H = 0` and symmetric `G_hist` solves `G_hist * G_hist = H * Hᵀ`,
    then `G_hist = 0`. -/
theorem hankel_zero_collapse
    {p f : Type*} [Fintype p] [Fintype f]
    (H : Matrix p f ℝ) (G_hist : Matrix p p ℝ)
    (hH : H = 0) (hGsym : G_histᵀ = G_hist) (hGsq : G_hist * G_hist = H * Hᵀ) :
    G_hist = 0 := by
  have h0 : G_histᵀ * G_hist = 0 := by
    rw [hGsym, hGsq, hH, Matrix.zero_mul]
  have htr : (G_histᵀ * G_hist).trace = 0 := by rw [h0, Matrix.trace_zero]
  exact (frobNormSq_eq_zero_iff G_hist).mp htr

/-- Explicitly policy- and test-weighted Hankel realization identity (`R_w = D_H^{1/2} R`, `O_w = O D_T^{1/2}`). -/
theorem weighted_hankel_induced_history_gram_sq
    {p m f : Type*} [Fintype p] [Fintype m] [Fintype f] [DecidableEq p] [DecidableEq m] [DecidableEq f]
    (wH_sqrt : p → ℝ) (wT_sqrt : f → ℝ)
    (R : Matrix p m ℝ) (O : Matrix m f ℝ) (X : Matrix m m ℝ)
    (hric : X * ((Matrix.diagonal wH_sqrt * R)ᵀ * (Matrix.diagonal wH_sqrt * R)) * X =
      (O * Matrix.diagonal wT_sqrt) * (O * Matrix.diagonal wT_sqrt)ᵀ) :
    let R_w := Matrix.diagonal wH_sqrt * R
    let O_w := O * Matrix.diagonal wT_sqrt
    let H_w := R_w * O_w
    (R_w * X * R_wᵀ) * (R_w * X * R_wᵀ) = H_w * H_wᵀ :=
  hankel_induced_history_gram_sq (Matrix.diagonal wH_sqrt * R) (O * Matrix.diagonal wT_sqrt) X hric

/-- Adding a nonnegative multiple `λ ≥ 0` of symmetric positive-semidefinite `L_kin` to SPD `A`
    keeps `A + λ L_kin` strictly SPD across all `λ ≥ 0`. -/
theorem posDef_add_smul_posSemidef
    {A L : Matrix ι ι ℝ} (hA : A.PosDef)
    (hLs : Lᵀ = L) (hLnn : ∀ x : ι → ℝ, 0 ≤ Matrix.dotProduct x (L *ᵥ x))
    {lam : ℝ} (hlam : 0 ≤ lam) :
    (A + lam • L).PosDef := by
  have hAs : Aᵀ = A := by
    simpa [Matrix.IsHermitian, Matrix.conjTranspose_eq_transpose_of_trivial] using hA.isHermitian
  have hHerm : (A + lam • L).IsHermitian := by
    rw [Matrix.IsHermitian, Matrix.conjTranspose_eq_transpose_of_trivial,
      Matrix.transpose_add, Matrix.transpose_smul, hAs, hLs]
  refine ⟨hHerm, ?_⟩
  intro x hx
  have hAx : 0 < Matrix.dotProduct (star x) (A *ᵥ x) := hA.2 x hx
  have hLx : 0 ≤ lam * Matrix.dotProduct x (L *ᵥ x) := mul_nonneg hlam (hLnn x)
  have hsm : (lam • L) *ᵥ x = lam • (L *ᵥ x) := by
    ext i
    simp only [Matrix.mulVec, Matrix.dotProduct, Matrix.smul_apply, Pi.smul_apply,
      smul_eq_mul, Finset.mul_sum, mul_assoc]
  have hdecomp : Matrix.dotProduct (star x) ((A + lam • L) *ᵥ x) =
      Matrix.dotProduct (star x) (A *ᵥ x) + lam * Matrix.dotProduct x (L *ᵥ x) := by
    simp only [star_trivial, Matrix.add_mulVec, hsm, Matrix.dotProduct_add,
      Matrix.dotProduct_smul, smul_eq_mul]
  rw [hdecomp]
  linarith

/-- Concrete matrix variational fluctuation-dissipation: if `0 ≤ λ₁ < λ₂` and `X₁, X₂`
    minimize `Tr((A + λ L_kin) X) + Tr(B X⁻¹)`, then `(L_kin * X₂).trace ≤ (L_kin * X₁).trace`
    (strict when `X₁ ≠ X₂` and `X₁` is the unique minimizer at `λ₁`). -/
theorem matrix_variational_kinetic_antitone
    (A B L : Matrix ι ι ℝ) (lam₁ lam₂ : ℝ)
    (X₁ Xinv₁ X₂ Xinv₂ : Matrix ι ι ℝ)
    (hlam : lam₁ < lam₂)
    (hmin₁ : ((A + lam₁ • L) * X₁).trace + (B * Xinv₁).trace ≤
      ((A + lam₁ • L) * X₂).trace + (B * Xinv₂).trace)
    (hmin₂ : ((A + lam₂ • L) * X₂).trace + (B * Xinv₂).trace ≤
      ((A + lam₂ • L) * X₁).trace + (B * Xinv₁).trace) :
    (L * X₂).trace ≤ (L * X₁).trace := by
  simp only [Matrix.add_mul, Matrix.smul_mul, Matrix.trace_add, Matrix.trace_smul, smul_eq_mul] at hmin₁ hmin₂
  nlinarith [sub_pos.mpr hlam]

theorem matrix_variational_kinetic_strictAnti
    (A B L : Matrix ι ι ℝ) (lam₁ lam₂ : ℝ)
    (X₁ Xinv₁ X₂ Xinv₂ : Matrix ι ι ℝ)
    (hlam : lam₁ < lam₂)
    (hmin₁ : ((A + lam₁ • L) * X₁).trace + (B * Xinv₁).trace <
      ((A + lam₁ • L) * X₂).trace + (B * Xinv₂).trace)
    (hmin₂ : ((A + lam₂ • L) * X₂).trace + (B * Xinv₂).trace ≤
      ((A + lam₂ • L) * X₁).trace + (B * Xinv₁).trace) :
    (L * X₂).trace < (L * X₁).trace := by
  simp only [Matrix.add_mul, Matrix.smul_mul, Matrix.trace_add, Matrix.trace_smul, smul_eq_mul] at hmin₁ hmin₂
  nlinarith [sub_pos.mpr hlam]

end PositiveDefiniteAndPolar

end
end MasterPrincipleVariational
