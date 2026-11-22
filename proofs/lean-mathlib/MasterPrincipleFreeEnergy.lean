/-
  Mathlib formalization for the Exponential Heat-Filtered Kubo-Ando &
  Quantum Relative-Entropy (Matrix-KL) Free-Energy Master Principle
  (`gemini/master-principle-free-energy`).

  Proves for arbitrary finite-dimensional real symmetric / SPD operators
  with ZERO commutativity assumptions between `Wc`, `Wo`, `G0`, and `L`:
  1. Basis-independent spectral functional calculus (`spectral_apply_eq_of_eq`),
     symmetric matrix exponential/logarithm (`symmExp`, `symmLog`) inverse pair,
     uniqueness of SPD square roots (`posDef_sq_eq_iff`), and semigroup laws for
     `heatOp hL t`.
  2. Exact Heat-Filtered Kubo-Ando Variational Theorem (`heat_filtered_kubo_ando_riccati`):
     `G_gm_heat(lam) = exp(-lam L / 2) G0 exp(-lam L / 2)` is SPD and equals the unique
     global minimizer `Wc(lam) # Wo(lam)` of the heat-filtered primal variational objective
     `Tr((E⁻¹ Wc⁻¹ E⁻¹) X) + Tr((E Wo E) X⁻¹)`.
  3. Exact Exponential Fluctuation-Dissipation & Log-Partition Convexity:
     monotonicity & strict monotonicity of raw kinetic cost `Tr(L G_gm_heat(lam))` and
     normalized kinetic ratio `Tr(L G_gm_heat(lam)) / Tr(G_gm_heat(lam))`, plus
     midpoint log-convexity `Z((lam1 + lam2)/2)^2 ≤ Z(lam1) * Z(lam2)`.
  4. Quantum Relative-Entropy (Matrix-KL / Klein Inequality) Free-Energy Theorem:
     nonnegativity and strict zero-characterization of `D_KL(X || Y)`, global unique
     minimizer `X_kl(lam) = exp(log G0 - lam L)` of `D_KL(X || G0) + lam Tr(L X)`,
     exact variational fluctuation-dissipation monotonicity, convexity of
     `lam ↦ X_kl(lam).trace`, plus exact coincidence with `G_gm_heat(lam)` when `[G0, L] = 0`.

  Isolated in `proofs/lean-mathlib/` so `proofs/lean/` remains core Lean 4.
-/
import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Data.Fintype.BigOperators
import Mathlib.Data.Matrix.Basic
import Mathlib.Data.Real.Basic
import Mathlib.LinearAlgebra.Matrix.DotProduct
import Mathlib.LinearAlgebra.Matrix.PosDef
import Mathlib.LinearAlgebra.Matrix.Spectrum
import Mathlib.LinearAlgebra.Matrix.Symmetric
import Mathlib.LinearAlgebra.Matrix.Trace
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Positivity
import Mathlib.Tactic.Ring

open scoped BigOperators Matrix

namespace MasterPrincipleFreeEnergy

noncomputable section
set_option linter.unusedSectionVars false

section BasicHelpers

variable {ι : Type*} [Fintype ι] [DecidableEq ι]

private theorem isHermitian_transpose_eq {H : Matrix ι ι ℝ} (hH : H.IsHermitian) : Hᵀ = H := by
  simpa [Matrix.IsHermitian, Matrix.conjTranspose_eq_transpose_of_trivial] using hH

private theorem isHermitian_of_transpose_eq {H : Matrix ι ι ℝ} (hH : Hᵀ = H) : H.IsHermitian := by
  rw [Matrix.IsHermitian, Matrix.conjTranspose_eq_transpose_of_trivial]
  exact hH

theorem isHermitian_smul {H : Matrix ι ι ℝ} (hH : H.IsHermitian) (r : ℝ) :
    (r • H).IsHermitian := by
  apply isHermitian_of_transpose_eq
  rw [Matrix.transpose_smul, isHermitian_transpose_eq hH]

theorem isHermitian_sub {A B : Matrix ι ι ℝ} (hA : A.IsHermitian) (hB : B.IsHermitian) :
    (A - B).IsHermitian := by
  apply isHermitian_of_transpose_eq
  rw [Matrix.transpose_sub, isHermitian_transpose_eq hA, isHermitian_transpose_eq hB]

theorem isHermitian_conj (Q : Matrix ι ι ℝ) (d : ι → ℝ) :
    (Q * Matrix.diagonal d * Qᵀ).IsHermitian := by
  apply isHermitian_of_transpose_eq
  simp only [Matrix.transpose_mul, Matrix.transpose_transpose, Matrix.diagonal_transpose,
    Matrix.mul_assoc]

theorem diag_mul_diag_fn (a b : ι → ℝ) :
    Matrix.diagonal a * Matrix.diagonal b = Matrix.diagonal (fun i => a i * b i) := by
  ext i j
  by_cases hij : i = j
  · subst hij; simp
  · simp [hij]

private theorem smul_diagonal_fn (r : ℝ) (d : ι → ℝ) :
    r • Matrix.diagonal d = Matrix.diagonal (fun i => r * d i) := by
  ext i j
  by_cases hij : i = j
  · subst hij; simp [smul_eq_mul]
  · simp [hij]

private theorem sub_diagonal_fn (a b : ι → ℝ) :
    Matrix.diagonal a - Matrix.diagonal b = Matrix.diagonal (fun i => a i - b i) := by
  ext i j
  by_cases hij : i = j
  · subst hij; simp
  · simp [hij]

private theorem conj_diag_smul (Q : Matrix ι ι ℝ) (d : ι → ℝ) (r : ℝ) :
    r • (Q * Matrix.diagonal d * Qᵀ) = Q * Matrix.diagonal (fun i => r * d i) * Qᵀ := by
  rw [← Matrix.smul_mul, ← Matrix.mul_smul, smul_diagonal_fn]

private theorem conj_diag_sub (Q : Matrix ι ι ℝ) (a b : ι → ℝ) :
    Q * Matrix.diagonal a * Qᵀ - Q * Matrix.diagonal b * Qᵀ =
      Q * Matrix.diagonal (fun i => a i - b i) * Qᵀ := by
  rw [← Matrix.sub_mul, ← Matrix.mul_sub, sub_diagonal_fn]

theorem posDef_diagonal {d : ι → ℝ} (hd : ∀ i, 0 < d i) :
    (Matrix.diagonal d).PosDef := by
  refine ⟨isHermitian_of_transpose_eq (Matrix.diagonal_transpose d), ?_⟩
  intro x hx
  have hx0 : ∃ i₀ : ι, x i₀ ≠ 0 := by
    by_contra h
    push_neg at h
    exact hx (funext h)
  rcases hx0 with ⟨i₀, hi₀⟩
  have hsq_pos : 0 < d i₀ * (x i₀) ^ 2 := mul_pos (hd i₀) (sq_pos_of_ne_zero hi₀)
  have hsum : Matrix.dotProduct (star x) ((Matrix.diagonal d) *ᵥ x) =
      ∑ i : ι, d i * (x i) ^ 2 := by
    simp only [star_trivial, Matrix.dotProduct, Matrix.mulVec_diagonal]
    refine Finset.sum_congr rfl fun i _ => by ring
  rw [hsum]
  exact lt_of_lt_of_le hsq_pos
    (Finset.single_le_sum (fun i _ => mul_nonneg (hd i).le (sq_nonneg (x i))) (Finset.mem_univ i₀))

theorem posDef_congruence {M R Rinv : Matrix ι ι ℝ} (hM : M.PosDef) (h1 : R * Rinv = 1) :
    (R * M * Rᵀ).PosDef := by
  have hMs := isHermitian_transpose_eq hM.isHermitian
  have hHerm : (R * M * Rᵀ).IsHermitian := by
    apply isHermitian_of_transpose_eq
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

theorem frobNormSq_eq_sum_sq {p q : Type*} [Fintype p] [Fintype q] (M : Matrix p q ℝ) :
    (Mᵀ * M).trace = ∑ i : p, ∑ j : q, (M i j) ^ 2 := by
  unfold Matrix.trace Matrix.diag
  simp only [Matrix.mul_apply, Matrix.transpose_apply]
  rw [Finset.sum_comm]
  refine Finset.sum_congr rfl fun i _ => ?_
  refine Finset.sum_congr rfl fun j _ => ?_
  ring

theorem frobNormSq_nonneg {p q : Type*} [Fintype p] [Fintype q] (M : Matrix p q ℝ) :
    0 ≤ (Mᵀ * M).trace := by
  rw [frobNormSq_eq_sum_sq]
  exact Finset.sum_nonneg fun i _ => Finset.sum_nonneg fun j _ => sq_nonneg (M i j)

theorem frobNormSq_eq_zero_iff {p q : Type*} [Fintype p] [Fintype q] (M : Matrix p q ℝ) :
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

end BasicHelpers

section SpectralCalculus

variable {ι : Type*} [Fintype ι] [DecidableEq ι]

private def eigU {H : Matrix ι ι ℝ} (hH : H.IsHermitian) : Matrix ι ι ℝ :=
  (hH.eigenvectorUnitary : Matrix ι ι ℝ)

private theorem eigU_transpose_mul {H : Matrix ι ι ℝ} (hH : H.IsHermitian) :
    (eigU hH)ᵀ * eigU hH = 1 := by
  simpa [eigU, Matrix.star_eq_conjTranspose, Matrix.conjTranspose_eq_transpose_of_trivial] using
    unitary.coe_star_mul_self hH.eigenvectorUnitary

private theorem eigU_mul_transpose {H : Matrix ι ι ℝ} (hH : H.IsHermitian) :
    eigU hH * (eigU hH)ᵀ = 1 := by
  simpa [eigU, Matrix.star_eq_conjTranspose, Matrix.conjTranspose_eq_transpose_of_trivial] using
    unitary.coe_mul_star_self hH.eigenvectorUnitary

private theorem spectral_decomp {H : Matrix ι ι ℝ} (hH : H.IsHermitian) :
    H = eigU hH * Matrix.diagonal hH.eigenvalues * (eigU hH)ᵀ := by
  have hs := hH.spectral_theorem
  simpa [eigU, Function.comp_def, RCLike.ofReal_real_eq_id, Matrix.star_eq_conjTranspose,
    Matrix.conjTranspose_eq_transpose_of_trivial] using hs

/-- Basis-independence of symmetric spectral functional calculus:
    whenever two orthonormal eigenbases represent the same matrix,
    applying ANY function `f : ℝ → ℝ` to the spectrum produces the same operator. -/
theorem spectral_apply_eq_of_eq
    {U V : Matrix ι ι ℝ} (a b : ι → ℝ) (f : ℝ → ℝ)
    (hUtU : Uᵀ * U = 1) (hUUt : U * Uᵀ = 1)
    (hVtV : Vᵀ * V = 1) (hVVt : V * Vᵀ = 1)
    (hEq : U * Matrix.diagonal a * Uᵀ = V * Matrix.diagonal b * Vᵀ) :
    U * Matrix.diagonal (fun i => f (a i)) * Uᵀ =
      V * Matrix.diagonal (fun j => f (b j)) * Vᵀ := by
  let W : Matrix ι ι ℝ := Uᵀ * V
  have hdiag : Matrix.diagonal a * W = W * Matrix.diagonal b := by
    calc Matrix.diagonal a * (Uᵀ * V)
        = (Uᵀ * U) * Matrix.diagonal a * (Uᵀ * V) := by rw [hUtU, Matrix.one_mul]
      _ = Uᵀ * (U * Matrix.diagonal a * Uᵀ) * V := by simp only [Matrix.mul_assoc]
      _ = Uᵀ * (V * Matrix.diagonal b * Vᵀ) * V := by rw [hEq]
      _ = (Uᵀ * V) * Matrix.diagonal b * (Vᵀ * V) := by simp only [Matrix.mul_assoc]
      _ = W * Matrix.diagonal b := by rw [hVtV, Matrix.mul_one]
  have hdiag_f : Matrix.diagonal (fun i => f (a i)) * W =
      W * Matrix.diagonal (fun j => f (b j)) := by
    ext i j
    have hij := congrArg (fun M : Matrix ι ι ℝ => M i j) hdiag
    simp only [Matrix.mul_apply, Matrix.diagonal_apply] at hij ⊢
    simp only [ite_mul, zero_mul, Finset.sum_ite_eq, Finset.mem_univ, ↓reduceIte,
      mul_ite, mul_zero, Finset.sum_ite_eq'] at hij ⊢
    by_cases hw : W i j = 0
    · simp [hw]
    · have hab : a i = b j := by
        have hsub : (a i - b j) * W i j = 0 := by linarith
        exact sub_eq_zero.mp ((mul_eq_zero.mp hsub).resolve_right hw)
      rw [hab, mul_comm]
  calc U * Matrix.diagonal (fun i => f (a i)) * Uᵀ
      = U * Matrix.diagonal (fun i => f (a i)) * Uᵀ * (V * Vᵀ) := by rw [hVVt, Matrix.mul_one]
    _ = U * (Matrix.diagonal (fun i => f (a i)) * W) * Vᵀ := by
          simp only [W, Matrix.mul_assoc]
    _ = U * (W * Matrix.diagonal (fun j => f (b j))) * Vᵀ := by rw [hdiag_f]
    _ = (U * Uᵀ) * V * Matrix.diagonal (fun j => f (b j)) * Vᵀ := by
          simp only [W, Matrix.mul_assoc]
    _ = V * Matrix.diagonal (fun j => f (b j)) * Vᵀ := by rw [hUUt, Matrix.one_mul]

/-- Real symmetric matrix exponential via spectral decomposition. -/
def symmExp {H : Matrix ι ι ℝ} (hH : H.IsHermitian) : Matrix ι ι ℝ :=
  eigU hH * Matrix.diagonal (fun i => Real.exp (hH.eigenvalues i)) * (eigU hH)ᵀ

/-- Real SPD matrix logarithm via spectral decomposition. -/
def symmLog {P : Matrix ι ι ℝ} (hP : P.PosDef) : Matrix ι ι ℝ :=
  eigU hP.isHermitian * Matrix.diagonal (fun i => Real.log (hP.isHermitian.eigenvalues i)) *
    (eigU hP.isHermitian)ᵀ

/-- Semigroup heat damping operator `exp(t L)` for a symmetric matrix `L`. -/
def heatOp {L : Matrix ι ι ℝ} (hL : L.IsHermitian) (t : ℝ) : Matrix ι ι ℝ :=
  eigU hL * Matrix.diagonal (fun i => Real.exp (t * hL.eigenvalues i)) * (eigU hL)ᵀ

theorem symmExp_isHermitian {H : Matrix ι ι ℝ} (hH : H.IsHermitian) :
    (symmExp hH).IsHermitian :=
  isHermitian_conj _ _

theorem symmExp_posDef {H : Matrix ι ι ℝ} (hH : H.IsHermitian) :
    (symmExp hH).PosDef :=
  posDef_congruence (posDef_diagonal fun _ => Real.exp_pos _) (eigU_mul_transpose hH)

theorem symmLog_isHermitian {P : Matrix ι ι ℝ} (hP : P.PosDef) :
    (symmLog hP).IsHermitian :=
  isHermitian_conj _ _

theorem symmExp_of_diag {H Q : Matrix ι ι ℝ} (hH : H.IsHermitian) (μ : ι → ℝ)
    (hQtQ : Qᵀ * Q = 1) (hQQt : Q * Qᵀ = 1)
    (hEq : H = Q * Matrix.diagonal μ * Qᵀ) :
    symmExp hH = Q * Matrix.diagonal (fun i => Real.exp (μ i)) * Qᵀ :=
  spectral_apply_eq_of_eq hH.eigenvalues μ Real.exp
    (eigU_transpose_mul hH) (eigU_mul_transpose hH) hQtQ hQQt
    ((spectral_decomp hH).symm.trans hEq)

theorem symmLog_of_diag {P Q : Matrix ι ι ℝ} (hP : P.PosDef) (g : ι → ℝ)
    (hQtQ : Qᵀ * Q = 1) (hQQt : Q * Qᵀ = 1)
    (hEq : P = Q * Matrix.diagonal g * Qᵀ) :
    symmLog hP = Q * Matrix.diagonal (fun i => Real.log (g i)) * Qᵀ :=
  spectral_apply_eq_of_eq hP.isHermitian.eigenvalues g Real.log
    (eigU_transpose_mul hP.isHermitian) (eigU_mul_transpose hP.isHermitian) hQtQ hQQt
    ((spectral_decomp hP.isHermitian).symm.trans hEq)

theorem symmExp_symmLog {P : Matrix ι ι ℝ} (hP : P.PosDef) :
    symmExp (symmLog_isHermitian hP) = P := by
  rw [symmExp_of_diag (symmLog_isHermitian hP)
    (fun i => Real.log (hP.isHermitian.eigenvalues i))
    (eigU_transpose_mul hP.isHermitian) (eigU_mul_transpose hP.isHermitian) rfl]
  have hdiag : Matrix.diagonal (fun i => Real.exp (Real.log (hP.isHermitian.eigenvalues i))) =
      Matrix.diagonal hP.isHermitian.eigenvalues := by
    ext i j
    by_cases hij : i = j
    · subst hij; simp [Real.exp_log (hP.eigenvalues_pos i)]
    · simp [hij]
  rw [hdiag]
  exact (spectral_decomp hP.isHermitian).symm

theorem symmLog_symmExp {H : Matrix ι ι ℝ} (hH : H.IsHermitian) :
    symmLog (symmExp_posDef hH) = H := by
  rw [symmLog_of_diag (symmExp_posDef hH)
    (fun i => Real.exp (hH.eigenvalues i))
    (eigU_transpose_mul hH) (eigU_mul_transpose hH) rfl]
  have hdiag : Matrix.diagonal (fun i => Real.log (Real.exp (hH.eigenvalues i))) =
      Matrix.diagonal hH.eigenvalues := by
    ext i j
    by_cases hij : i = j
    · subst hij; simp [Real.log_exp]
    · simp [hij]
  rw [hdiag]
  exact (spectral_decomp hH).symm

theorem heatOp_eq_symmExp {L : Matrix ι ι ℝ} (hL : L.IsHermitian) (t : ℝ) :
    heatOp hL t = symmExp (isHermitian_smul hL t) := by
  have hsmul : t • L = eigU hL * Matrix.diagonal (fun i => t * hL.eigenvalues i) * (eigU hL)ᵀ := by
    conv_lhs => rw [spectral_decomp hL]
    exact conj_diag_smul (eigU hL) hL.eigenvalues t
  exact (symmExp_of_diag (isHermitian_smul hL t) (fun i => t * hL.eigenvalues i)
    (eigU_transpose_mul hL) (eigU_mul_transpose hL) hsmul).symm

theorem heatOp_isHermitian {L : Matrix ι ι ℝ} (hL : L.IsHermitian) (t : ℝ) :
    (heatOp hL t).IsHermitian :=
  isHermitian_conj _ _

theorem heatOp_transpose {L : Matrix ι ι ℝ} (hL : L.IsHermitian) (t : ℝ) :
    (heatOp hL t)ᵀ = heatOp hL t :=
  isHermitian_transpose_eq (heatOp_isHermitian hL t)

theorem heatOp_posDef {L : Matrix ι ι ℝ} (hL : L.IsHermitian) (t : ℝ) :
    (heatOp hL t).PosDef :=
  posDef_congruence (posDef_diagonal fun _ => Real.exp_pos _) (eigU_mul_transpose hL)

theorem heatOp_zero {L : Matrix ι ι ℝ} (hL : L.IsHermitian) :
    heatOp hL 0 = 1 := by
  unfold heatOp
  have h1 : Matrix.diagonal (fun i : ι => Real.exp (0 * hL.eigenvalues i)) = 1 := by
    ext i j
    by_cases hij : i = j
    · subst hij; simp
    · simp [hij]
  rw [h1, Matrix.mul_one, eigU_mul_transpose hL]

theorem heatOp_add {L : Matrix ι ι ℝ} (hL : L.IsHermitian) (s t : ℝ) :
    heatOp hL s * heatOp hL t = heatOp hL (s + t) := by
  unfold heatOp
  calc eigU hL * Matrix.diagonal (fun i => Real.exp (s * hL.eigenvalues i)) * (eigU hL)ᵀ *
        (eigU hL * Matrix.diagonal (fun i => Real.exp (t * hL.eigenvalues i)) * (eigU hL)ᵀ)
      = eigU hL * (Matrix.diagonal (fun i => Real.exp (s * hL.eigenvalues i)) *
          ((eigU hL)ᵀ * eigU hL) * Matrix.diagonal (fun i => Real.exp (t * hL.eigenvalues i))) *
          (eigU hL)ᵀ := by simp only [Matrix.mul_assoc]
    _ = eigU hL * (Matrix.diagonal (fun i => Real.exp (s * hL.eigenvalues i)) *
          Matrix.diagonal (fun i => Real.exp (t * hL.eigenvalues i))) * (eigU hL)ᵀ := by
          rw [eigU_transpose_mul hL, Matrix.mul_one]
    _ = eigU hL * Matrix.diagonal (fun i => Real.exp ((s + t) * hL.eigenvalues i)) * (eigU hL)ᵀ := by
          rw [diag_mul_diag_fn]
          have hfn : (fun i => Real.exp (s * hL.eigenvalues i) * Real.exp (t * hL.eigenvalues i)) =
              fun i => Real.exp ((s + t) * hL.eigenvalues i) := by
            ext i
            rw [← Real.exp_add]
            ring_nf
          rw [hfn]

theorem heatOp_mul_neg {L : Matrix ι ι ℝ} (hL : L.IsHermitian) (t : ℝ) :
    heatOp hL t * heatOp hL (-t) = 1 := by
  rw [heatOp_add hL t (-t), add_neg_cancel, heatOp_zero hL]

theorem heatOp_neg_mul {L : Matrix ι ι ℝ} (hL : L.IsHermitian) (t : ℝ) :
    heatOp hL (-t) * heatOp hL t = 1 := by
  rw [heatOp_add hL (-t) t, neg_add_cancel, heatOp_zero hL]

theorem posDef_sq_eq_iff {P Q : Matrix ι ι ℝ} (hP : P.PosDef) (hQ : Q.PosDef) :
    P * P = Q * Q ↔ P = Q := by
  constructor
  · intro hsq
    have hP_sq : P * P = eigU hP.isHermitian *
        Matrix.diagonal (fun i => (hP.isHermitian.eigenvalues i) ^ 2) * (eigU hP.isHermitian)ᵀ := by
      conv_lhs => rw [spectral_decomp hP.isHermitian]
      calc (eigU hP.isHermitian * Matrix.diagonal hP.isHermitian.eigenvalues *
            (eigU hP.isHermitian)ᵀ) * (eigU hP.isHermitian *
            Matrix.diagonal hP.isHermitian.eigenvalues * (eigU hP.isHermitian)ᵀ)
          = eigU hP.isHermitian * (Matrix.diagonal hP.isHermitian.eigenvalues *
              ((eigU hP.isHermitian)ᵀ * eigU hP.isHermitian) *
              Matrix.diagonal hP.isHermitian.eigenvalues) * (eigU hP.isHermitian)ᵀ := by
                simp only [Matrix.mul_assoc]
        _ = eigU hP.isHermitian * (Matrix.diagonal hP.isHermitian.eigenvalues *
              Matrix.diagonal hP.isHermitian.eigenvalues) * (eigU hP.isHermitian)ᵀ := by
                rw [eigU_transpose_mul hP.isHermitian, Matrix.mul_one]
        _ = _ := by
              rw [diag_mul_diag_fn]
              congr 2
              ext i j
              by_cases hij : i = j <;> simp [hij, sq]
    have hQ_sq : Q * Q = eigU hQ.isHermitian *
        Matrix.diagonal (fun i => (hQ.isHermitian.eigenvalues i) ^ 2) * (eigU hQ.isHermitian)ᵀ := by
      conv_lhs => rw [spectral_decomp hQ.isHermitian]
      calc (eigU hQ.isHermitian * Matrix.diagonal hQ.isHermitian.eigenvalues *
            (eigU hQ.isHermitian)ᵀ) * (eigU hQ.isHermitian *
            Matrix.diagonal hQ.isHermitian.eigenvalues * (eigU hQ.isHermitian)ᵀ)
          = eigU hQ.isHermitian * (Matrix.diagonal hQ.isHermitian.eigenvalues *
              ((eigU hQ.isHermitian)ᵀ * eigU hQ.isHermitian) *
              Matrix.diagonal hQ.isHermitian.eigenvalues) * (eigU hQ.isHermitian)ᵀ := by
                simp only [Matrix.mul_assoc]
        _ = eigU hQ.isHermitian * (Matrix.diagonal hQ.isHermitian.eigenvalues *
              Matrix.diagonal hQ.isHermitian.eigenvalues) * (eigU hQ.isHermitian)ᵀ := by
                rw [eigU_transpose_mul hQ.isHermitian, Matrix.mul_one]
        _ = _ := by
              rw [diag_mul_diag_fn]
              congr 2
              ext i j
              by_cases hij : i = j <;> simp [hij, sq]
    have hroot := spectral_apply_eq_of_eq
      (fun i => (hP.isHermitian.eigenvalues i) ^ 2)
      (fun i => (hQ.isHermitian.eigenvalues i) ^ 2) Real.sqrt
      (eigU_transpose_mul hP.isHermitian) (eigU_mul_transpose hP.isHermitian)
      (eigU_transpose_mul hQ.isHermitian) (eigU_mul_transpose hQ.isHermitian)
      (hP_sq.symm.trans (hsq.trans hQ_sq))
    have hdp : Matrix.diagonal (fun i => Real.sqrt ((hP.isHermitian.eigenvalues i) ^ 2)) =
        Matrix.diagonal hP.isHermitian.eigenvalues := by
      ext i j
      by_cases hij : i = j
      · subst hij; simp [Real.sqrt_sq (hP.eigenvalues_pos i).le]
      · simp [hij]
    have hdq : Matrix.diagonal (fun i => Real.sqrt ((hQ.isHermitian.eigenvalues i) ^ 2)) =
        Matrix.diagonal hQ.isHermitian.eigenvalues := by
      ext i j
      by_cases hij : i = j
      · subst hij; simp [Real.sqrt_sq (hQ.eigenvalues_pos i).le]
      · simp [hij]
    rw [hdp, hdq] at hroot
    calc P = eigU hP.isHermitian * Matrix.diagonal hP.isHermitian.eigenvalues *
            (eigU hP.isHermitian)ᵀ := spectral_decomp hP.isHermitian
      _ = eigU hQ.isHermitian * Matrix.diagonal hQ.isHermitian.eigenvalues *
            (eigU hQ.isHermitian)ᵀ := hroot
      _ = Q := (spectral_decomp hQ.isHermitian).symm
  · rintro rfl; rfl

end SpectralCalculus

section HeatFilteredKuboAndo

variable {ι : Type*} [Fintype ι] [DecidableEq ι]

private theorem variational_trace_identity_local
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
        = (R_X * (R_Aᵀ * R_A * R_Xᵀ)).trace := by simp only [Matrix.mul_assoc]
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
  have hE : ((R_A * R_Xᵀ - Uᵀ * R_B * R_Xinv)ᵀ * (R_A * R_Xᵀ - Uᵀ * R_B * R_Xinv)).trace =
      (R_X * R_Aᵀ * (R_A * R_Xᵀ)).trace - (R_X * R_Aᵀ * (Uᵀ * R_B * R_Xinv)).trace -
      (R_Xinvᵀ * R_Bᵀ * U * (R_A * R_Xᵀ)).trace +
      (R_Xinvᵀ * R_Bᵀ * U * (Uᵀ * R_B * R_Xinv)).trace := by
    simp only [Matrix.transpose_sub, Matrix.transpose_mul, Matrix.transpose_transpose,
      Matrix.sub_mul, Matrix.mul_sub, Matrix.trace_sub, Matrix.trace_add, Matrix.mul_assoc]
    ring
  rw [hE, h1, h2, h3, h4]
  ring

private theorem exists_posDef_sqrt_local {P : Matrix ι ι ℝ} (hP : P.PosDef) :
    ∃ S Sinv : Matrix ι ι ℝ, S.PosDef ∧ S * S = P ∧ S * Sinv = 1 ∧ Sinv * S = 1 := by
  let U := eigU hP.isHermitian
  have hsu := eigU_transpose_mul hP.isHermitian
  have hus := eigU_mul_transpose hP.isHermitian
  have hspec := spectral_decomp hP.isHermitian
  let d : ι → ℝ := fun i => Real.sqrt (hP.isHermitian.eigenvalues i)
  let dinv : ι → ℝ := fun i => (Real.sqrt (hP.isHermitian.eigenvalues i))⁻¹
  have hd_pos : ∀ i, 0 < d i := fun i => Real.sqrt_pos.mpr (hP.eigenvalues_pos i)
  let S : Matrix ι ι ℝ := U * Matrix.diagonal d * Uᵀ
  let Sinv : Matrix ι ι ℝ := U * Matrix.diagonal dinv * Uᵀ
  refine ⟨S, Sinv, posDef_congruence (posDef_diagonal hd_pos) hus, ?_, ?_, ?_⟩
  · calc S * S
        = U * (Matrix.diagonal d * (Uᵀ * U) * Matrix.diagonal d) * Uᵀ := by
            simp only [S, Matrix.mul_assoc]
      _ = U * (Matrix.diagonal d * Matrix.diagonal d) * Uᵀ := by rw [hsu, Matrix.mul_one]
      _ = U * Matrix.diagonal hP.isHermitian.eigenvalues * Uᵀ := by
            rw [diag_mul_diag_fn]
            congr 2
            ext i j
            by_cases hij : i = j
            · subst hij; simp [d, Real.mul_self_sqrt (hP.eigenvalues_pos i).le]
            · simp [hij]
      _ = P := hspec.symm
  · calc S * Sinv
        = U * (Matrix.diagonal d * (Uᵀ * U) * Matrix.diagonal dinv) * Uᵀ := by
            simp only [S, Sinv, Matrix.mul_assoc]
      _ = U * (Matrix.diagonal d * Matrix.diagonal dinv) * Uᵀ := by rw [hsu, Matrix.mul_one]
      _ = U * (1 : Matrix ι ι ℝ) * Uᵀ := by
            rw [diag_mul_diag_fn]
            have hid : Matrix.diagonal (fun i => d i * dinv i) = 1 := by
              ext i j
              by_cases hij : i = j
              · subst hij; simp [d, dinv, (hd_pos i).ne']
              · simp [hij]
            rw [hid]
      _ = 1 := by rw [Matrix.mul_one]; exact hus
  · calc Sinv * S
        = U * (Matrix.diagonal dinv * (Uᵀ * U) * Matrix.diagonal d) * Uᵀ := by
            simp only [S, Sinv, Matrix.mul_assoc]
      _ = U * (Matrix.diagonal dinv * Matrix.diagonal d) * Uᵀ := by rw [hsu, Matrix.mul_one]
      _ = U * (1 : Matrix ι ι ℝ) * Uᵀ := by
            rw [diag_mul_diag_fn]
            have hid : Matrix.diagonal (fun i => dinv i * d i) = 1 := by
              ext i j
              by_cases hij : i = j
              · subst hij; simp [d, dinv, (hd_pos i).ne']
              · simp [hij]
            rw [hid]
      _ = 1 := by rw [Matrix.mul_one]; exact hus

private theorem posDef_riccati_unique_minimizer
    {A B G : Matrix ι ι ℝ} (hA : A.PosDef) (hB : B.PosDef) (hG : G.PosDef)
    (hRic : G * A * G = B) :
    ∃ G_inv : Matrix ι ι ℝ, G * G_inv = 1 ∧
      ∀ (R_X R_Xinv : Matrix ι ι ℝ), R_Xinv * R_X = 1 →
        (A * G).trace + (B * G_inv).trace ≤
          (A * (R_Xᵀ * R_X)).trace + (B * (R_Xinv * R_Xinvᵀ)).trace ∧
        ((A * (R_Xᵀ * R_X)).trace + (B * (R_Xinv * R_Xinvᵀ)).trace =
          (A * G).trace + (B * G_inv).trace → R_Xᵀ * R_X = G) := by
  rcases exists_posDef_sqrt_local hG with ⟨S_G, S_Ginv, hSG_pd, hSG_sq, hSG1, hSG2⟩
  rcases exists_posDef_sqrt_local hA with ⟨R_A, R_Ainv, hRA_pd, hRA_sq, hRA1, hRA2⟩
  rcases exists_posDef_sqrt_local hB with ⟨R_B, _, hRB_pd, hRB_sq, _, _⟩
  have hSG_sym := isHermitian_transpose_eq hSG_pd.isHermitian
  have hRA_sym := isHermitian_transpose_eq hRA_pd.isHermitian
  have hRB_sym := isHermitian_transpose_eq hRB_pd.isHermitian
  have hA_fac : A = R_Aᵀ * R_A := by rw [hRA_sym, hRA_sq]
  have hB_fac : B = R_Bᵀ * R_B := by rw [hRB_sym, hRB_sq]
  let P : Matrix ι ι ℝ := R_A * G * R_Aᵀ
  have hP_pd : P.PosDef := posDef_congruence hG hRA1
  have hmid_pd : (R_A * B * R_Aᵀ).PosDef := posDef_congruence hB hRA1
  rcases exists_posDef_sqrt_local hmid_pd with ⟨M, Minv, hM_pd, hM_sq, hM1, hM2⟩
  have hPM_sq : P * P = M * M := by
    calc P * P
        = R_A * G * (R_Aᵀ * R_A) * G * R_Aᵀ := by simp only [P, Matrix.mul_assoc]
      _ = R_A * (G * A * G) * R_Aᵀ := by rw [← hA_fac]; simp only [Matrix.mul_assoc]
      _ = R_A * B * R_Aᵀ := by rw [hRic]
      _ = M * M := hM_sq.symm
  have hP_eq_M : P = M := (posDef_sq_eq_iff hP_pd hM_pd).mp hPM_sq
  have hMinv_sym : Minvᵀ = Minv := by
    have hM_sym := isHermitian_transpose_eq hM_pd.isHermitian
    have hm1T : M * Minvᵀ = 1 := by
      calc M * Minvᵀ = Mᵀ * Minvᵀ := by rw [hM_sym]
        _ = (Minv * M)ᵀ := (Matrix.transpose_mul Minv M).symm
        _ = 1 := by rw [hM2, Matrix.transpose_one]
    calc Minvᵀ = 1 * Minvᵀ := (Matrix.one_mul _).symm
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
      _ = (Minv * M) * (M * Minv) := by
            rw [← hM_sq]; simp only [Matrix.mul_assoc]
      _ = 1 := by rw [hM2, hM1, Matrix.one_mul]
  have hUorth : U * Uᵀ = 1 := Matrix.mul_eq_one_comm.mp hUtU
  have hUM : Uᵀ * (R_B * R_Aᵀ) = M := by
    calc Uᵀ * (R_B * R_Aᵀ)
        = Minvᵀ * (R_A * (R_Bᵀ * R_B) * R_Aᵀ) := by
            simp only [U, Matrix.transpose_mul, Matrix.transpose_transpose, Matrix.mul_assoc]
      _ = Minv * (R_A * B * R_Aᵀ) := by rw [hMinv_sym, ← hB_fac]
      _ = (Minv * M) * M := by rw [← hM_sq, Matrix.mul_assoc]
      _ = M := by rw [hM2, Matrix.one_mul]
  let G_inv : Matrix ι ι ℝ := S_Ginv * S_Ginvᵀ
  have hGinv_sym : S_Ginvᵀ = S_Ginv := by
    have hm1T : S_G * S_Ginvᵀ = 1 := by
      calc S_G * S_Ginvᵀ = S_Gᵀ * S_Ginvᵀ := by rw [hSG_sym]
        _ = (S_Ginv * S_G)ᵀ := (Matrix.transpose_mul S_Ginv S_G).symm
        _ = 1 := by rw [hSG2, Matrix.transpose_one]
    calc S_Ginvᵀ = 1 * S_Ginvᵀ := (Matrix.one_mul _).symm
      _ = (S_Ginv * S_G) * S_Ginvᵀ := by rw [hSG2]
      _ = S_Ginv * (S_G * S_Ginvᵀ) := Matrix.mul_assoc _ _ _
      _ = S_Ginv := by rw [hm1T, Matrix.mul_one]
  have hGGinv : G * G_inv = 1 := by
    calc G * (S_Ginv * S_Ginvᵀ)
        = (S_G * S_G) * (S_Ginv * S_Ginv) := by rw [hSG_sq, hGinv_sym]
      _ = S_G * (S_G * S_Ginv) * S_Ginv := by simp only [Matrix.mul_assoc]
      _ = 1 := by rw [hSG1, Matrix.mul_one, hSG1]
  have hG_obj : (A * G).trace + (B * G_inv).trace = 2 * M.trace := by
    have hA_tr : (A * G).trace = M.trace := by
      rw [← hP_eq_M]
      calc (A * G).trace
          = ((R_Aᵀ * R_A) * G).trace := by rw [hA_fac]
        _ = (R_Aᵀ * (R_A * G)).trace := by simp only [Matrix.mul_assoc]
        _ = ((R_A * G) * R_Aᵀ).trace := Matrix.trace_mul_comm _ _
        _ = P.trace := rfl
    have hB_tr : (B * G_inv).trace = M.trace := by
      calc (B * G_inv).trace
          = ((G * A * G) * G_inv).trace := by rw [hRic]
        _ = (G * A * (G * G_inv)).trace := by simp only [Matrix.mul_assoc]
        _ = (G * A).trace := by rw [hGGinv, Matrix.mul_one]
        _ = (A * G).trace := Matrix.trace_mul_comm _ _
        _ = M.trace := hA_tr
    rw [hA_tr, hB_tr]; ring
  refine ⟨G_inv, hGGinv, fun R_X R_Xinv hXinv => ?_⟩
  have hid := variational_trace_identity_local R_A R_B R_X R_Xinv U M hXinv hUorth hUM
  dsimp only at hid
  rw [← hA_fac, ← hB_fac] at hid
  rw [hG_obj]
  constructor
  · have hnn := frobNormSq_nonneg (R_A * R_Xᵀ - Uᵀ * R_B * R_Xinv)
    linarith
  · intro heq
    have hzero : ((R_A * R_Xᵀ - Uᵀ * R_B * R_Xinv)ᵀ *
        (R_A * R_Xᵀ - Uᵀ * R_B * R_Xinv)).trace = 0 := by linarith
    have hE0 : R_A * R_Xᵀ - Uᵀ * R_B * R_Xinv = 0 := (frobNormSq_eq_zero_iff _).mp hzero
    have hEq1 : R_A * R_Xᵀ = Uᵀ * R_B * R_Xinv := sub_eq_zero.mp hE0
    have hRX_eq : R_A * (R_Xᵀ * R_X) = Uᵀ * R_B := by
      calc R_A * (R_Xᵀ * R_X)
          = (R_A * R_Xᵀ) * R_X := (Matrix.mul_assoc _ _ _).symm
        _ = (Uᵀ * R_B * R_Xinv) * R_X := by rw [hEq1]
        _ = Uᵀ * R_B * (R_Xinv * R_X) := Matrix.mul_assoc _ _ _
        _ = Uᵀ * R_B := by rw [hXinv, Matrix.mul_one]
    have hRAinvT : R_Aᵀ * R_Ainvᵀ = 1 := by
      calc R_Aᵀ * R_Ainvᵀ = (R_Ainv * R_A)ᵀ := (Matrix.transpose_mul _ _).symm
        _ = 1 := by rw [hRA2, Matrix.transpose_one]
    have hG_eq : R_A * G = Uᵀ * R_B := by
      calc R_A * G
          = (R_A * G * R_Aᵀ) * R_Ainvᵀ := by
              rw [Matrix.mul_assoc, Matrix.mul_assoc, hRAinvT, Matrix.mul_one]
        _ = M * R_Ainvᵀ := by change P * R_Ainvᵀ = _; rw [hP_eq_M]
        _ = (Uᵀ * (R_B * R_Aᵀ)) * R_Ainvᵀ := by rw [hUM]
        _ = Uᵀ * R_B * (R_Aᵀ * R_Ainvᵀ) := by simp only [Matrix.mul_assoc]
        _ = Uᵀ * R_B := by rw [hRAinvT, Matrix.mul_one]
    calc R_Xᵀ * R_X
        = (R_Ainv * R_A) * (R_Xᵀ * R_X) := by rw [hRA2, Matrix.one_mul]
      _ = R_Ainv * (R_A * (R_Xᵀ * R_X)) := Matrix.mul_assoc _ _ _
      _ = R_Ainv * (R_A * G) := by rw [hRX_eq, hG_eq]
      _ = (R_Ainv * R_A) * G := (Matrix.mul_assoc _ _ _).symm
      _ = G := by rw [hRA2, Matrix.one_mul]

/-- **Exact Heat-Filtered Kubo-Ando Variational Theorem**:
    If `G0` is the unpenalized Kubo-Ando geometric mean `Wc # Wo` solving `G0 Wc⁻¹ G0 = Wo`,
    and `L` is ANY symmetric damping matrix (zero commutativity assumed), then
    `G_gm_heat(lam) = exp(-lam L / 2) G0 exp(-lam L / 2)` is SPD, solves
    `G_gm_heat(lam) * Wc(lam)⁻¹ * G_gm_heat(lam) = Wo(lam)` where `Wc(lam) = E Wc E` and
    `Wo(lam) = E Wo E` (`E = exp(-lam L / 2)`), and is the UNIQUE global minimizer of
    `Tr(Wc(lam)⁻¹ X) + Tr(Wo(lam) X⁻¹)`. -/
theorem heat_filtered_kubo_ando_riccati
    {G0 Wc Wc_inv Wo L : Matrix ι ι ℝ}
    (hG0 : G0.PosDef) (hWc_inv : Wc_inv.PosDef) (hWo : Wo.PosDef) (hL : L.IsHermitian)
    (hWc_pair : Wc * Wc_inv = 1) (hG0_ric : G0 * Wc_inv * G0 = Wo) (lam : ℝ) :
    let E := heatOp hL (-lam / 2)
    let Einv := heatOp hL (lam / 2)
    let A_lam := Einv * Wc_inv * Einv
    let B_lam := E * Wo * E
    let G_lam := E * G0 * E
    G_lam.PosDef ∧
    (E * Wc * E) * A_lam = 1 ∧
    G_lam * A_lam * G_lam = B_lam ∧
    ∃ (G_inv : Matrix ι ι ℝ), G_lam * G_inv = 1 ∧
      ∀ (R_X R_Xinv : Matrix ι ι ℝ), R_Xinv * R_X = 1 →
        (A_lam * G_lam).trace + (B_lam * G_inv).trace ≤
          (A_lam * (R_Xᵀ * R_X)).trace + (B_lam * (R_Xinv * R_Xinvᵀ)).trace ∧
        ((A_lam * (R_Xᵀ * R_X)).trace + (B_lam * (R_Xinv * R_Xinvᵀ)).trace =
          (A_lam * G_lam).trace + (B_lam * G_inv).trace → R_Xᵀ * R_X = G_lam) := by
  dsimp only
  have hE_Einv : heatOp hL (-lam / 2) * heatOp hL (lam / 2) = 1 := by
    rw [heatOp_add hL, show -lam / 2 + lam / 2 = 0 by ring, heatOp_zero hL]
  have hEinv_E : heatOp hL (lam / 2) * heatOp hL (-lam / 2) = 1 := by
    rw [heatOp_add hL, show lam / 2 + -lam / 2 = 0 by ring, heatOp_zero hL]
  have hG_pd : (heatOp hL (-lam / 2) * G0 * heatOp hL (-lam / 2)).PosDef := by
    have h := posDef_congruence hG0 hE_Einv
    simpa [heatOp_transpose hL (-lam / 2)] using h
  have hA_pd : (heatOp hL (lam / 2) * Wc_inv * heatOp hL (lam / 2)).PosDef := by
    have h := posDef_congruence hWc_inv hEinv_E
    simpa [heatOp_transpose hL (lam / 2)] using h
  have hB_pd : (heatOp hL (-lam / 2) * Wo * heatOp hL (-lam / 2)).PosDef := by
    have h := posDef_congruence hWo hE_Einv
    simpa [heatOp_transpose hL (-lam / 2)] using h
  have hWA : (heatOp hL (-lam / 2) * Wc * heatOp hL (-lam / 2)) *
      (heatOp hL (lam / 2) * Wc_inv * heatOp hL (lam / 2)) = 1 := by
    calc (heatOp hL (-lam / 2) * Wc * heatOp hL (-lam / 2)) *
          (heatOp hL (lam / 2) * Wc_inv * heatOp hL (lam / 2))
        = heatOp hL (-lam / 2) * Wc * (heatOp hL (-lam / 2) * heatOp hL (lam / 2)) *
            Wc_inv * heatOp hL (lam / 2) := by simp only [Matrix.mul_assoc]
      _ = heatOp hL (-lam / 2) * (Wc * Wc_inv) * heatOp hL (lam / 2) := by
            rw [hE_Einv, Matrix.mul_one]; simp only [Matrix.mul_assoc]
      _ = heatOp hL (-lam / 2) * heatOp hL (lam / 2) := by rw [hWc_pair, Matrix.mul_one]
      _ = 1 := hE_Einv
  have hRic : (heatOp hL (-lam / 2) * G0 * heatOp hL (-lam / 2)) *
      (heatOp hL (lam / 2) * Wc_inv * heatOp hL (lam / 2)) *
      (heatOp hL (-lam / 2) * G0 * heatOp hL (-lam / 2)) =
      heatOp hL (-lam / 2) * Wo * heatOp hL (-lam / 2) := by
    calc (heatOp hL (-lam / 2) * G0 * heatOp hL (-lam / 2)) *
          (heatOp hL (lam / 2) * Wc_inv * heatOp hL (lam / 2)) *
          (heatOp hL (-lam / 2) * G0 * heatOp hL (-lam / 2))
        = heatOp hL (-lam / 2) * G0 * (heatOp hL (-lam / 2) * heatOp hL (lam / 2)) *
            Wc_inv * (heatOp hL (lam / 2) * heatOp hL (-lam / 2)) *
            G0 * heatOp hL (-lam / 2) := by simp only [Matrix.mul_assoc]
      _ = heatOp hL (-lam / 2) * (G0 * Wc_inv * G0) * heatOp hL (-lam / 2) := by
            rw [hE_Einv, hEinv_E]; simp only [Matrix.mul_assoc, Matrix.mul_one, Matrix.one_mul]
      _ = heatOp hL (-lam / 2) * Wo * heatOp hL (-lam / 2) := by rw [hG0_ric]
  exact ⟨hG_pd, hWA, hRic, posDef_riccati_unique_minimizer hA_pd hB_pd hG_pd hRic⟩

end HeatFilteredKuboAndo

section ExponentialFluctuationDissipation

variable {ι : Type*} [Fintype ι] [DecidableEq ι]

private theorem trace_orth_diag_sandwich
    {U : Matrix ι ι ℝ} (A : Matrix ι ι ℝ) (d : ι → ℝ) :
    ((U * Matrix.diagonal d * Uᵀ) * A).trace = ∑ i : ι, (Uᵀ * A * U) i i * d i := by
  have hcomm : ((U * Matrix.diagonal d * Uᵀ) * A).trace =
      (Matrix.diagonal d * (Uᵀ * A * U)).trace := by
    calc ((U * Matrix.diagonal d * Uᵀ) * A).trace
        = (U * (Matrix.diagonal d * (Uᵀ * A))).trace := by simp only [Matrix.mul_assoc]
      _ = ((Matrix.diagonal d * (Uᵀ * A)) * U).trace := Matrix.trace_mul_comm _ _
      _ = (Matrix.diagonal d * (Uᵀ * A * U)).trace := by simp only [Matrix.mul_assoc]
  rw [hcomm]
  unfold Matrix.trace Matrix.diag
  refine Finset.sum_congr rfl fun i _ => ?_
  simp only [Matrix.mul_apply, Matrix.diagonal_apply, ite_mul, zero_mul, Finset.sum_ite_eq,
    Finset.mem_univ, ↓reduceIte]
  ring

theorem posDef_orth_diag_pos {G0 Q : Matrix ι ι ℝ} (hG0 : G0.PosDef) (hQ : Qᵀ * Q = 1) (i : ι) :
    0 < (Qᵀ * G0 * Q) i i := by
  let e : ι → ℝ := Pi.single i (1 : ℝ)
  have hcol : Q *ᵥ e ≠ 0 := by
    intro hzero
    have heq := congrArg (fun v => (Qᵀ *ᵥ v) i) hzero
    dsimp only at heq
    rw [Matrix.mulVec_mulVec, hQ, Matrix.one_mulVec, Matrix.mulVec_zero] at heq
    simp [e] at heq
  have hdot : (Qᵀ * G0 * Q) i i =
      Matrix.dotProduct (star (Q *ᵥ e)) (G0 *ᵥ (Q *ᵥ e)) := by
    have he_eq : (Qᵀ * G0 * Q) i i = Matrix.dotProduct e ((Qᵀ * G0 * Q) *ᵥ e) := by
      simp [e, Matrix.dotProduct, Matrix.mulVec, Pi.single_apply]
    rw [he_eq]
    simp only [star_trivial]
    calc Matrix.dotProduct e ((Qᵀ * G0 * Q) *ᵥ e)
        = Matrix.dotProduct e (Qᵀ *ᵥ (G0 *ᵥ (Q *ᵥ e))) := by
            simp only [Matrix.mulVec_mulVec, Matrix.mul_assoc]
      _ = Matrix.dotProduct (e ᵥ* Qᵀ) (G0 *ᵥ (Q *ᵥ e)) := Matrix.dotProduct_mulVec _ _ _
      _ = Matrix.dotProduct (Q *ᵥ e) (G0 *ᵥ (Q *ᵥ e)) := by
            rw [← Matrix.mulVec_transpose, Matrix.transpose_transpose]
  rw [hdot]
  exact hG0.2 _ hcol

/-- Partition trace `Z(lam) = Tr(exp(-lam L / 2) G0 exp(-lam L / 2))` equals `∑ w_i exp(-lam μ_i)`. -/
theorem trace_gm_heat_eq_sum {G0 L : Matrix ι ι ℝ} (hL : L.IsHermitian) (lam : ℝ) :
    let E := heatOp hL (-lam / 2)
    (E * G0 * E).trace =
      ∑ i : ι, ((eigU hL)ᵀ * G0 * eigU hL) i i * Real.exp (-lam * hL.eigenvalues i) := by
  dsimp only
  let E := heatOp hL (-lam / 2)
  calc (E * G0 * E).trace
      = ((E * E) * G0).trace := by rw [Matrix.trace_mul_comm, ← Matrix.mul_assoc]
    _ = (heatOp hL (-lam) * G0).trace := by
          have hadd : E * E = heatOp hL (-lam) := by
            rw [heatOp_add hL]
            have hr : -lam / 2 + -lam / 2 = -lam := by ring
            rw [hr]
          rw [hadd]
    _ = ∑ i : ι, ((eigU hL)ᵀ * G0 * eigU hL) i i *
          Real.exp (-lam * hL.eigenvalues i) :=
          trace_orth_diag_sandwich G0 _

/-- Kinetic trace `Tr(L exp(-lam L / 2) G0 exp(-lam L / 2))` equals `∑ w_i μ_i exp(-lam μ_i)`. -/
theorem trace_L_gm_heat_eq_sum {G0 L : Matrix ι ι ℝ} (hL : L.IsHermitian) (lam : ℝ) :
    let E := heatOp hL (-lam / 2)
    (L * (E * G0 * E)).trace =
      ∑ i : ι, ((eigU hL)ᵀ * G0 * eigU hL) i i *
        hL.eigenvalues i * Real.exp (-lam * hL.eigenvalues i) := by
  dsimp only
  let E := heatOp hL (-lam / 2)
  have hEL : E * L * E = eigU hL *
      Matrix.diagonal (fun i => hL.eigenvalues i * Real.exp (-lam * hL.eigenvalues i)) *
      (eigU hL)ᵀ := by
    have hLspec := spectral_decomp hL
    calc E * L * E
        = eigU hL * Matrix.diagonal (fun i => Real.exp ((-lam / 2) * hL.eigenvalues i)) *
            ((eigU hL)ᵀ * eigU hL) * Matrix.diagonal hL.eigenvalues * ((eigU hL)ᵀ * eigU hL) *
            Matrix.diagonal (fun i => Real.exp ((-lam / 2) * hL.eigenvalues i)) * (eigU hL)ᵀ := by
              conv_lhs => rw [hLspec]
              simp only [E, heatOp, Matrix.mul_assoc]
      _ = eigU hL * (Matrix.diagonal (fun i => Real.exp ((-lam / 2) * hL.eigenvalues i)) *
            Matrix.diagonal hL.eigenvalues *
            Matrix.diagonal (fun i => Real.exp ((-lam / 2) * hL.eigenvalues i))) * (eigU hL)ᵀ := by
              rw [eigU_transpose_mul hL, Matrix.mul_one, Matrix.mul_one]
              simp only [Matrix.mul_assoc]
      _ = eigU hL *
            Matrix.diagonal (fun i => hL.eigenvalues i * Real.exp (-lam * hL.eigenvalues i)) *
            (eigU hL)ᵀ := by
              rw [diag_mul_diag_fn, diag_mul_diag_fn]
              congr 2
              ext i j
              by_cases hij : i = j
              · subst hij
                simp only [Matrix.diagonal_apply_eq]
                calc Real.exp (-lam / 2 * hL.eigenvalues i) * hL.eigenvalues i *
                      Real.exp (-lam / 2 * hL.eigenvalues i)
                    = hL.eigenvalues i * (Real.exp (-lam / 2 * hL.eigenvalues i) *
                        Real.exp (-lam / 2 * hL.eigenvalues i)) := by ring
                  _ = hL.eigenvalues i * Real.exp (-lam * hL.eigenvalues i) := by
                        rw [← Real.exp_add]; congr 2; ring
              · simp [hij]
  calc (L * (E * G0 * E)).trace
      = (E * L * E * G0).trace := by
          rw [← Matrix.mul_assoc, Matrix.trace_mul_comm]
          simp only [Matrix.mul_assoc]
    _ = ∑ i : ι, ((eigU hL)ᵀ * G0 * eigU hL) i i *
          (hL.eigenvalues i * Real.exp (-lam * hL.eigenvalues i)) := by
          rw [hEL]; exact trace_orth_diag_sandwich G0 _
    _ = ∑ i : ι, ((eigU hL)ᵀ * G0 * eigU hL) i i *
          hL.eigenvalues i * Real.exp (-lam * hL.eigenvalues i) :=
          Finset.sum_congr rfl fun i _ => by ring

theorem gm_heat_raw_kinetic_antitone
    {G0 L : Matrix ι ι ℝ} (hG0 : G0.PosDef) (hL : L.IsHermitian)
    (hLpsd : ∀ i, 0 ≤ hL.eigenvalues i)
    {lam₁ lam₂ : ℝ} (hlam : lam₁ ≤ lam₂) :
    (L * (heatOp hL (-lam₂ / 2) * G0 * heatOp hL (-lam₂ / 2))).trace ≤
      (L * (heatOp hL (-lam₁ / 2) * G0 * heatOp hL (-lam₁ / 2))).trace := by
  rw [trace_L_gm_heat_eq_sum hL, trace_L_gm_heat_eq_sum hL]
  refine Finset.sum_le_sum fun i _ => ?_
  have hw := (posDef_orth_diag_pos hG0 (eigU_transpose_mul hL) i).le
  have hexp : Real.exp (-lam₂ * hL.eigenvalues i) ≤ Real.exp (-lam₁ * hL.eigenvalues i) :=
    Real.exp_le_exp.mpr (by nlinarith [hLpsd i])
  exact mul_le_mul_of_nonneg_left hexp (mul_nonneg hw (hLpsd i))

theorem gm_heat_raw_kinetic_strictAnti
    {G0 L : Matrix ι ι ℝ} (hG0 : G0.PosDef) (hL : L.IsHermitian)
    (hLpsd : ∀ i, 0 ≤ hL.eigenvalues i) (hLpos : ∃ i, 0 < hL.eigenvalues i)
    {lam₁ lam₂ : ℝ} (hlam : lam₁ < lam₂) :
    (L * (heatOp hL (-lam₂ / 2) * G0 * heatOp hL (-lam₂ / 2))).trace <
      (L * (heatOp hL (-lam₁ / 2) * G0 * heatOp hL (-lam₁ / 2))).trace := by
  rcases hLpos with ⟨i₀, hi₀⟩
  rw [trace_L_gm_heat_eq_sum hL, trace_L_gm_heat_eq_sum hL]
  refine Finset.sum_lt_sum (fun i _ => ?_) ⟨i₀, Finset.mem_univ i₀, ?_⟩
  · have hw := (posDef_orth_diag_pos hG0 (eigU_transpose_mul hL) i).le
    have hexp : Real.exp (-lam₂ * hL.eigenvalues i) ≤ Real.exp (-lam₁ * hL.eigenvalues i) :=
      Real.exp_le_exp.mpr (by nlinarith [hLpsd i])
    exact mul_le_mul_of_nonneg_left hexp (mul_nonneg hw (hLpsd i))
  · have hw0 := posDef_orth_diag_pos hG0 (eigU_transpose_mul hL) i₀
    have hexp : Real.exp (-lam₂ * hL.eigenvalues i₀) < Real.exp (-lam₁ * hL.eigenvalues i₀) :=
      Real.exp_lt_exp.mpr (by nlinarith)
    exact mul_lt_mul_of_pos_left hexp (mul_pos hw0 hi₀)

private theorem gibbs_ratio_diff_id (a μ g : ι → ℝ) :
    2 * ((∑ i : ι, a i * g i * μ i) * (∑ j : ι, a j) -
      (∑ i : ι, a i * μ i) * (∑ j : ι, a j * g j)) =
      ∑ i : ι, ∑ j : ι, a i * a j * (μ i - μ j) * (g i - g j) := by
  have hL : (∑ i : ι, a i * g i * μ i) * (∑ j : ι, a j) -
      (∑ i : ι, a i * μ i) * (∑ j : ι, a j * g j) =
      ∑ i : ι, ∑ j : ι, a i * a j * (g i * μ i - μ i * g j) := by
    rw [Finset.sum_mul, Finset.sum_mul]
    simp only [Finset.mul_sum, ← Finset.sum_sub_distrib]
    refine Finset.sum_congr rfl fun i _ => Finset.sum_congr rfl fun j _ => by ring
  have hSwap : ∑ i : ι, ∑ j : ι, a i * a j * (g i * μ i - μ i * g j) =
      ∑ i : ι, ∑ j : ι, a j * a i * (g j * μ j - μ j * g i) :=
    Finset.sum_comm
  have hAdd : ∑ i : ι, ∑ j : ι, a i * a j * (g i * μ i - μ i * g j) +
      ∑ i : ι, ∑ j : ι, a j * a i * (g j * μ j - μ j * g i) =
      ∑ i : ι, ∑ j : ι, a i * a j * (μ i - μ j) * (g i - g j) := by
    simp only [← Finset.sum_add_distrib]
    refine Finset.sum_congr rfl fun i _ => Finset.sum_congr rfl fun j _ => by ring
  linarith

/-- Normalized kinetic ratio `Tr(L G_gm_heat(lam)) / Tr(G_gm_heat(lam))` is antitone
    in `lam` for ANY SPD `G0` and symmetric `L`, with zero commutativity assumptions. -/
theorem gm_heat_norm_kinetic_antitone
    {G0 L : Matrix ι ι ℝ} (hG0 : G0.PosDef) (hL : L.IsHermitian)
    {lam₁ lam₂ : ℝ} (hlam : lam₁ ≤ lam₂) :
    let G₁ := heatOp hL (-lam₁ / 2) * G0 * heatOp hL (-lam₁ / 2)
    let G₂ := heatOp hL (-lam₂ / 2) * G0 * heatOp hL (-lam₂ / 2)
    (L * G₂).trace / G₂.trace ≤ (L * G₁).trace / G₁.trace := by
  dsimp only
  by_cases hne : Nonempty ι
  · rw [trace_L_gm_heat_eq_sum hL lam₁, trace_L_gm_heat_eq_sum hL lam₂,
      trace_gm_heat_eq_sum hL lam₁, trace_gm_heat_eq_sum hL lam₂]
    let w : ι → ℝ := fun i => ((eigU hL)ᵀ * G0 * eigU hL) i i
    let μ : ι → ℝ := hL.eigenvalues
    let a : ι → ℝ := fun i => w i * Real.exp (-lam₁ * μ i)
    let g : ι → ℝ := fun i => Real.exp (-(lam₂ - lam₁) * μ i)
    have ha_pos : ∀ i, 0 < a i := fun i =>
      mul_pos (posDef_orth_diag_pos hG0 (eigU_transpose_mul hL) i) (Real.exp_pos _)
    rcases hne with ⟨i₀⟩
    have hden₁ : 0 < ∑ i : ι, a i :=
      Finset.sum_pos (fun i _ => ha_pos i) ⟨i₀, Finset.mem_univ i₀⟩
    have hden₂ : 0 < ∑ i : ι, w i * Real.exp (-lam₂ * μ i) :=
      Finset.sum_pos (fun i _ => mul_pos (posDef_orth_diag_pos hG0 (eigU_transpose_mul hL) i)
        (Real.exp_pos _)) ⟨i₀, Finset.mem_univ i₀⟩
    have heq_den₂ : (∑ i : ι, w i * Real.exp (-lam₂ * μ i)) = ∑ i : ι, a i * g i := by
      refine Finset.sum_congr rfl fun i _ => ?_
      change w i * Real.exp (-lam₂ * μ i) = w i * Real.exp (-lam₁ * μ i) * Real.exp (-(lam₂ - lam₁) * μ i)
      rw [mul_assoc, ← Real.exp_add]
      congr 2; ring
    have heq_num₂ : (∑ i : ι, w i * μ i * Real.exp (-lam₂ * μ i)) = ∑ i : ι, a i * g i * μ i := by
      refine Finset.sum_congr rfl fun i _ => ?_
      change w i * μ i * Real.exp (-lam₂ * μ i) =
        w i * Real.exp (-lam₁ * μ i) * Real.exp (-(lam₂ - lam₁) * μ i) * μ i
      have hexp : Real.exp (-lam₁ * μ i) * Real.exp (-(lam₂ - lam₁) * μ i) =
          Real.exp (-lam₂ * μ i) := by
        rw [← Real.exp_add]; congr 1; ring
      calc w i * μ i * Real.exp (-lam₂ * μ i)
          = w i * (Real.exp (-lam₁ * μ i) * Real.exp (-(lam₂ - lam₁) * μ i)) * μ i := by
              rw [hexp]; ring
        _ = _ := by ring
    have heq_num₁ : (∑ i : ι, w i * μ i * Real.exp (-lam₁ * μ i)) = ∑ i : ι, a i * μ i := by
      refine Finset.sum_congr rfl fun i _ => ?_; change _ = w i * Real.exp (-lam₁ * μ i) * μ i; ring
    rw [heq_num₂, heq_num₁]
    rw [heq_den₂] at hden₂ ⊢
    change (∑ i : ι, a i * g i * μ i) / (∑ i : ι, a i * g i) ≤ (∑ i : ι, a i * μ i) / (∑ i : ι, a i)
    rw [div_le_div_iff hden₂ hden₁]
    have hnonpos : ∑ i : ι, ∑ j : ι, a i * a j * (μ i - μ j) * (g i - g j) ≤ 0 := by
      refine Finset.sum_nonpos fun i _ => Finset.sum_nonpos fun j _ => ?_
      have haa : 0 ≤ a i * a j := mul_nonneg (ha_pos i).le (ha_pos j).le
      have hterm : (μ i - μ j) * (g i - g j) ≤ 0 := by
        rcases le_total (μ i) (μ j) with hμ | hμ
        · exact mul_nonpos_of_nonpos_of_nonneg (sub_nonpos.mpr hμ)
            (sub_nonneg.mpr (Real.exp_le_exp.mpr (by nlinarith)))
        · exact mul_nonpos_of_nonneg_of_nonpos (sub_nonneg.mpr hμ)
            (sub_nonpos.mpr (Real.exp_le_exp.mpr (by nlinarith)))
      calc a i * a j * (μ i - μ j) * (g i - g j)
          = (a i * a j) * ((μ i - μ j) * (g i - g j)) := by ring
        _ ≤ 0 := mul_nonpos_of_nonneg_of_nonpos haa hterm
    linarith [gibbs_ratio_diff_id a μ g]
  · haveI : IsEmpty ι := not_nonempty_iff.mp hne
    simp [Matrix.trace]

/-- Strict decrease of the normalized kinetic ratio whenever `L` has at least two distinct eigenvalues. -/
theorem gm_heat_norm_kinetic_strictAnti
    {G0 L : Matrix ι ι ℝ} (hG0 : G0.PosDef) (hL : L.IsHermitian)
    (hdist : ∃ i j : ι, hL.eigenvalues i ≠ hL.eigenvalues j)
    {lam₁ lam₂ : ℝ} (hlam : lam₁ < lam₂) :
    let G₁ := heatOp hL (-lam₁ / 2) * G0 * heatOp hL (-lam₁ / 2)
    let G₂ := heatOp hL (-lam₂ / 2) * G0 * heatOp hL (-lam₂ / 2)
    (L * G₂).trace / G₂.trace < (L * G₁).trace / G₁.trace := by
  dsimp only
  rcases hdist with ⟨i₀, j₀, hij⟩
  rw [trace_L_gm_heat_eq_sum hL lam₁, trace_L_gm_heat_eq_sum hL lam₂,
    trace_gm_heat_eq_sum hL lam₁, trace_gm_heat_eq_sum hL lam₂]
  let w : ι → ℝ := fun i => ((eigU hL)ᵀ * G0 * eigU hL) i i
  let μ : ι → ℝ := hL.eigenvalues
  let a : ι → ℝ := fun i => w i * Real.exp (-lam₁ * μ i)
  let g : ι → ℝ := fun i => Real.exp (-(lam₂ - lam₁) * μ i)
  have ha_pos : ∀ i, 0 < a i := fun i =>
    mul_pos (posDef_orth_diag_pos hG0 (eigU_transpose_mul hL) i) (Real.exp_pos _)
  have hden₁ : 0 < ∑ i : ι, a i :=
    Finset.sum_pos (fun i _ => ha_pos i) ⟨i₀, Finset.mem_univ i₀⟩
  have hden₂ : 0 < ∑ i : ι, w i * Real.exp (-lam₂ * μ i) :=
    Finset.sum_pos (fun i _ => mul_pos (posDef_orth_diag_pos hG0 (eigU_transpose_mul hL) i)
      (Real.exp_pos _)) ⟨i₀, Finset.mem_univ i₀⟩
  have heq_den₂ : (∑ i : ι, w i * Real.exp (-lam₂ * μ i)) = ∑ i : ι, a i * g i := by
    refine Finset.sum_congr rfl fun i _ => ?_
    change w i * Real.exp (-lam₂ * μ i) = w i * Real.exp (-lam₁ * μ i) * Real.exp (-(lam₂ - lam₁) * μ i)
    rw [mul_assoc, ← Real.exp_add]; congr 2; ring
  have heq_num₂ : (∑ i : ι, w i * μ i * Real.exp (-lam₂ * μ i)) = ∑ i : ι, a i * g i * μ i := by
    refine Finset.sum_congr rfl fun i _ => ?_
    change w i * μ i * Real.exp (-lam₂ * μ i) =
      w i * Real.exp (-lam₁ * μ i) * Real.exp (-(lam₂ - lam₁) * μ i) * μ i
    have hexp : Real.exp (-lam₁ * μ i) * Real.exp (-(lam₂ - lam₁) * μ i) =
        Real.exp (-lam₂ * μ i) := by rw [← Real.exp_add]; congr 1; ring
    calc w i * μ i * Real.exp (-lam₂ * μ i)
        = w i * (Real.exp (-lam₁ * μ i) * Real.exp (-(lam₂ - lam₁) * μ i)) * μ i := by
            rw [hexp]; ring
      _ = _ := by ring
  have heq_num₁ : (∑ i : ι, w i * μ i * Real.exp (-lam₁ * μ i)) = ∑ i : ι, a i * μ i := by
    refine Finset.sum_congr rfl fun i _ => ?_; change _ = w i * Real.exp (-lam₁ * μ i) * μ i; ring
  rw [heq_num₂, heq_num₁]
  rw [heq_den₂] at hden₂ ⊢
  change (∑ i : ι, a i * g i * μ i) / (∑ i : ι, a i * g i) < (∑ i : ι, a i * μ i) / (∑ i : ι, a i)
  rw [div_lt_div_iff hden₂ hden₁]
  have hterm_le : ∀ i j : ι, a i * a j * (μ i - μ j) * (g i - g j) ≤ 0 := fun i j => by
    have haa : 0 ≤ a i * a j := mul_nonneg (ha_pos i).le (ha_pos j).le
    have hterm : (μ i - μ j) * (g i - g j) ≤ 0 := by
      rcases le_total (μ i) (μ j) with hμ | hμ
      · exact mul_nonpos_of_nonpos_of_nonneg (sub_nonpos.mpr hμ)
          (sub_nonneg.mpr (Real.exp_le_exp.mpr (by nlinarith)))
      · exact mul_nonpos_of_nonneg_of_nonpos (sub_nonneg.mpr hμ)
          (sub_nonpos.mpr (Real.exp_le_exp.mpr (by nlinarith)))
    calc a i * a j * (μ i - μ j) * (g i - g j)
        = (a i * a j) * ((μ i - μ j) * (g i - g j)) := by ring
      _ ≤ 0 := mul_nonpos_of_nonneg_of_nonpos haa hterm
  have hneg_pair : a i₀ * a j₀ * (μ i₀ - μ j₀) * (g i₀ - g j₀) < 0 := by
    have haa : 0 < a i₀ * a j₀ := mul_pos (ha_pos i₀) (ha_pos j₀)
    have hterm : (μ i₀ - μ j₀) * (g i₀ - g j₀) < 0 := by
      rcases lt_or_gt_of_ne hij with hμ | hμ
      · have hgij : g j₀ < g i₀ := Real.exp_lt_exp.mpr (by nlinarith)
        exact mul_neg_of_neg_of_pos (sub_neg.mpr hμ) (sub_pos.mpr hgij)
      · have hgij : g i₀ < g j₀ := Real.exp_lt_exp.mpr (by nlinarith)
        exact mul_neg_of_pos_of_neg (sub_pos.mpr hμ) (sub_neg.mpr hgij)
    calc a i₀ * a j₀ * (μ i₀ - μ j₀) * (g i₀ - g j₀)
        = (a i₀ * a j₀) * ((μ i₀ - μ j₀) * (g i₀ - g j₀)) := by ring
      _ < 0 := mul_neg_of_pos_of_neg haa hterm
  have hrow_strict : ∑ j : ι, a i₀ * a j * (μ i₀ - μ j) * (g i₀ - g j) < 0 := by
    simpa [Finset.sum_const_zero] using
      Finset.sum_lt_sum (fun j _ => hterm_le i₀ j) ⟨j₀, Finset.mem_univ j₀, by simpa using hneg_pair⟩
  have hdouble_lt : ∑ i : ι, ∑ j : ι, a i * a j * (μ i - μ j) * (g i - g j) < 0 := by
    simpa [Finset.sum_const_zero] using
      Finset.sum_lt_sum (fun i _ => Finset.sum_nonpos fun j _ => hterm_le i j)
        ⟨i₀, Finset.mem_univ i₀, by simpa using hrow_strict⟩
  linarith [gibbs_ratio_diff_id a μ g]

/-- Exact midpoint log-convexity of the partition trace `Z(lam) = Tr(G_gm_heat(lam))`. -/
theorem gm_heat_partition_midpoint_log_convex
    {G0 L : Matrix ι ι ℝ} (hG0 : G0.PosDef) (hL : L.IsHermitian) (lam₁ lam₂ : ℝ) :
    let Z : ℝ → ℝ := fun t => (heatOp hL (-t / 2) * G0 * heatOp hL (-t / 2)).trace
    Z ((lam₁ + lam₂) / 2) ^ 2 ≤ Z lam₁ * Z lam₂ := by
  dsimp only
  rw [trace_gm_heat_eq_sum hL, trace_gm_heat_eq_sum hL, trace_gm_heat_eq_sum hL]
  let w : ι → ℝ := fun i => ((eigU hL)ᵀ * G0 * eigU hL) i i
  let μ : ι → ℝ := hL.eigenvalues
  let u : ι → ℝ := fun i => Real.sqrt (w i) * Real.exp (-lam₁ * μ i / 2)
  let v : ι → ℝ := fun i => Real.sqrt (w i) * Real.exp (-lam₂ * μ i / 2)
  have hu2 : (∑ i : ι, w i * Real.exp (-lam₁ * μ i)) = ∑ i : ι, u i ^ 2 := by
    refine Finset.sum_congr rfl fun i _ => ?_
    have hw := (posDef_orth_diag_pos hG0 (eigU_transpose_mul hL) i).le
    calc w i * Real.exp (-lam₁ * μ i)
        = (Real.sqrt (w i)) ^ 2 * (Real.exp (-lam₁ * μ i / 2) * Real.exp (-lam₁ * μ i / 2)) := by
            rw [Real.sq_sqrt hw, ← Real.exp_add]; congr 2; ring
      _ = u i ^ 2 := by ring
  have hv2 : (∑ i : ι, w i * Real.exp (-lam₂ * μ i)) = ∑ i : ι, v i ^ 2 := by
    refine Finset.sum_congr rfl fun i _ => ?_
    have hw := (posDef_orth_diag_pos hG0 (eigU_transpose_mul hL) i).le
    calc w i * Real.exp (-lam₂ * μ i)
        = (Real.sqrt (w i)) ^ 2 * (Real.exp (-lam₂ * μ i / 2) * Real.exp (-lam₂ * μ i / 2)) := by
            rw [Real.sq_sqrt hw, ← Real.exp_add]; congr 2; ring
      _ = v i ^ 2 := by ring
  have huv : (∑ i : ι, w i * Real.exp (-((lam₁ + lam₂) / 2) * μ i)) = ∑ i : ι, u i * v i := by
    refine Finset.sum_congr rfl fun i _ => ?_
    have hw := (posDef_orth_diag_pos hG0 (eigU_transpose_mul hL) i).le
    calc w i * Real.exp (-((lam₁ + lam₂) / 2) * μ i)
        = (Real.sqrt (w i)) ^ 2 * (Real.exp (-lam₁ * μ i / 2) * Real.exp (-lam₂ * μ i / 2)) := by
            rw [Real.sq_sqrt hw, ← Real.exp_add]; congr 2; ring
      _ = u i * v i := by ring
  rw [hu2, hv2, huv]
  have hcs_id : 2 * ((∑ i : ι, u i ^ 2) * (∑ j : ι, v j ^ 2) - (∑ i : ι, u i * v i) ^ 2) =
      ∑ i : ι, ∑ j : ι, (u i * v j - u j * v i) ^ 2 := by
    have h1 : (∑ i : ι, u i ^ 2) * (∑ j : ι, v j ^ 2) =
        ∑ i : ι, ∑ j : ι, (u i * v j) ^ 2 := by
      rw [Finset.sum_mul]
      refine Finset.sum_congr rfl fun i _ => ?_
      rw [Finset.mul_sum]
      refine Finset.sum_congr rfl fun j _ => by ring
    have h2 : (∑ i : ι, u i * v i) ^ 2 = ∑ i : ι, ∑ j : ι, (u i * v j) * (u j * v i) := by
      rw [sq, Finset.sum_mul]
      refine Finset.sum_congr rfl fun i _ => ?_
      rw [Finset.mul_sum]
      refine Finset.sum_congr rfl fun j _ => by ring
    have h3 : (∑ i : ι, ∑ j : ι, (u j * v i) ^ 2) = ∑ i : ι, ∑ j : ι, (u i * v j) ^ 2 :=
      Finset.sum_comm
    calc 2 * ((∑ i : ι, u i ^ 2) * (∑ j : ι, v j ^ 2) - (∑ i : ι, u i * v i) ^ 2)
        = (∑ i : ι, ∑ j : ι, (u i * v j) ^ 2) + (∑ i : ι, ∑ j : ι, (u j * v i) ^ 2) -
            2 * ∑ i : ι, ∑ j : ι, (u i * v j) * (u j * v i) := by rw [h1, h2, h3]; ring
      _ = ∑ i : ι, ∑ j : ι, ((u i * v j) ^ 2 + (u j * v i) ^ 2 - 2 * ((u i * v j) * (u j * v i))) := by
            simp only [Finset.mul_sum, Finset.sum_add_distrib, Finset.sum_sub_distrib]
      _ = ∑ i : ι, ∑ j : ι, (u i * v j - u j * v i) ^ 2 :=
            Finset.sum_congr rfl fun i _ => Finset.sum_congr rfl fun j _ => by ring
  have hnonneg : 0 ≤ ∑ i : ι, ∑ j : ι, (u i * v j - u j * v i) ^ 2 :=
    Finset.sum_nonneg fun i _ => Finset.sum_nonneg fun j _ => sq_nonneg _
  linarith

end ExponentialFluctuationDissipation

section QuantumRelativeEntropyFreeEnergy

variable {ι : Type*} [Fintype ι] [DecidableEq ι]

/-- Scalar Bregman / KL divergence `x log x - x log y - x + y ≥ 0` for `x, y > 0`. -/
theorem kl_scalar_nonneg {x y : ℝ} (hx : 0 < x) (hy : 0 < y) :
    0 ≤ x * Real.log x - x * Real.log y - x + y := by
  have hexp := Real.add_one_le_exp (Real.log y - Real.log x)
  rw [Real.exp_sub, Real.exp_log hy, Real.exp_log hx] at hexp
  have hmul := mul_le_mul_of_nonneg_left hexp hx.le
  have hxy : x * (y / x) = y := mul_div_cancel₀ y hx.ne'
  rw [hxy] at hmul
  linarith

/-- Strict scalar KL characterization: `x log x - x log y - x + y = 0 ↔ x = y`. -/
theorem kl_scalar_eq_zero_iff {x y : ℝ} (hx : 0 < x) (hy : 0 < y) :
    x * Real.log x - x * Real.log y - x + y = 0 ↔ x = y := by
  constructor
  · intro heq
    by_contra hne
    have hlog_ne : Real.log y - Real.log x ≠ 0 := by
      intro hdiff
      have hlog : Real.log y = Real.log x := sub_eq_zero.mp hdiff
      have := congrArg Real.exp hlog
      rw [Real.exp_log hy, Real.exp_log hx] at this
      exact hne this.symm
    have hstrict := Real.add_one_lt_exp hlog_ne
    rw [Real.exp_sub, Real.exp_log hy, Real.exp_log hx] at hstrict
    have hmul := mul_lt_mul_of_pos_left hstrict hx
    have hxy : x * (y / x) = y := mul_div_cancel₀ y hx.ne'
    rw [hxy] at hmul
    linarith
  · rintro rfl; ring

/-- Von Neumann / Umegaki Matrix KL Divergence (Quantum Relative Entropy):
    `D_KL(X || Y) = Tr(X log X - X log Y - X + Y)`. -/
def matrixKL {X Y : Matrix ι ι ℝ} (hX : X.PosDef) (hY : Y.PosDef) : ℝ :=
  (X * symmLog hX - X * symmLog hY - X + Y).trace

private theorem trace_prod_orth_diags
    {U V : Matrix ι ι ℝ} (a b : ι → ℝ) :
    ((U * Matrix.diagonal a * Uᵀ) * (V * Matrix.diagonal b * Vᵀ)).trace =
      ∑ i : ι, ∑ j : ι, ((Uᵀ * V) i j) ^ 2 * (a i * b j) := by
  let Q := Uᵀ * V
  have hcomm : ((U * Matrix.diagonal a * Uᵀ) * (V * Matrix.diagonal b * Vᵀ)).trace =
      (Matrix.diagonal a * Q * Matrix.diagonal b * Qᵀ).trace := by
    calc ((U * Matrix.diagonal a * Uᵀ) * (V * Matrix.diagonal b * Vᵀ)).trace
        = (U * (Matrix.diagonal a * (Uᵀ * V) * Matrix.diagonal b * Vᵀ)).trace := by
            simp only [Matrix.mul_assoc]
      _ = ((Matrix.diagonal a * (Uᵀ * V) * Matrix.diagonal b * Vᵀ) * U).trace :=
            Matrix.trace_mul_comm _ _
      _ = (Matrix.diagonal a * Q * Matrix.diagonal b * Qᵀ).trace := by
            simp only [Q, Matrix.transpose_mul, Matrix.transpose_transpose, Matrix.mul_assoc]
  rw [hcomm]
  unfold Matrix.trace Matrix.diag
  calc ∑ i : ι, (Matrix.diagonal a * Q * Matrix.diagonal b * Qᵀ) i i
      = ∑ i : ι, ∑ j : ι, (Matrix.diagonal a * Q * Matrix.diagonal b) i j * Qᵀ j i := by
          refine Finset.sum_congr rfl fun i _ => ?_
          rw [Matrix.mul_apply]
    _ = ∑ i : ι, ∑ j : ι, (Q i j) ^ 2 * (a i * b j) := by
          refine Finset.sum_congr rfl fun i _ => Finset.sum_congr rfl fun j _ => ?_
          simp only [Matrix.mul_assoc, Matrix.mul_apply, Matrix.diagonal_apply,
            ite_mul, zero_mul, Finset.sum_ite_eq, Finset.mem_univ, ↓reduceIte,
            mul_ite, mul_zero, Finset.sum_ite_eq', Matrix.transpose_apply]
          ring

private theorem matrixKL_eq_double_sum {X Y : Matrix ι ι ℝ} (hX : X.PosDef) (hY : Y.PosDef) :
    let U := eigU hX.isHermitian
    let V := eigU hY.isHermitian
    let Q := Uᵀ * V
    let x := hX.isHermitian.eigenvalues
    let y := hY.isHermitian.eigenvalues
    matrixKL hX hY =
      ∑ i : ι, ∑ j : ι, (Q i j) ^ 2 * (x i * Real.log (x i) - x i * Real.log (y j) - x i + y j) := by
  dsimp only
  let U := eigU hX.isHermitian
  let V := eigU hY.isHermitian
  let Q := Uᵀ * V
  let x := hX.isHermitian.eigenvalues
  let y := hY.isHermitian.eigenvalues
  have hQQt : Q * Qᵀ = 1 := by
    calc (Uᵀ * V) * (Uᵀ * V)ᵀ
        = Uᵀ * (V * Vᵀ) * U := by
            simp only [Matrix.transpose_mul, Matrix.transpose_transpose, Matrix.mul_assoc]
      _ = 1 := by rw [eigU_mul_transpose hY.isHermitian, Matrix.mul_one, eigU_transpose_mul hX.isHermitian]
  have hQtQ : Qᵀ * Q = 1 := by
    calc (Uᵀ * V)ᵀ * (Uᵀ * V)
        = Vᵀ * (U * Uᵀ) * V := by
            simp only [Matrix.transpose_mul, Matrix.transpose_transpose, Matrix.mul_assoc]
      _ = 1 := by rw [eigU_mul_transpose hX.isHermitian, Matrix.mul_one, eigU_transpose_mul hY.isHermitian]
  have hrow1 : ∀ i, ∑ j : ι, (Q i j) ^ 2 = 1 := fun i => by
    have hii := congrArg (fun M : Matrix ι ι ℝ => M i i) hQQt
    simpa [Matrix.mul_apply, Matrix.transpose_apply, sq] using hii
  have hcol1 : ∀ j, ∑ i : ι, (Q i j) ^ 2 = 1 := fun j => by
    have hjj := congrArg (fun M : Matrix ι ι ℝ => M j j) hQtQ
    simpa [Matrix.mul_apply, Matrix.transpose_apply, sq] using hjj
  have hXspec : X = U * Matrix.diagonal x * Uᵀ := spectral_decomp hX.isHermitian
  have hYspec : Y = V * Matrix.diagonal y * Vᵀ := spectral_decomp hY.isHermitian
  have hLogX : symmLog hX = U * Matrix.diagonal (fun i => Real.log (x i)) * Uᵀ := rfl
  have hLogY : symmLog hY = V * Matrix.diagonal (fun j => Real.log (y j)) * Vᵀ := rfl
  have hTr1 : (X * symmLog hX).trace = ∑ i : ι, ∑ j : ι, (Q i j) ^ 2 * (x i * Real.log (x i)) := by
    rw [hLogX, hXspec, trace_prod_orth_diags x (fun i => Real.log (x i)),
      eigU_transpose_mul hX.isHermitian]
    calc ∑ i : ι, ∑ j : ι, ((1 : Matrix ι ι ℝ) i j) ^ 2 * (x i * Real.log (x j))
        = ∑ i : ι, x i * Real.log (x i) := by
            refine Finset.sum_congr rfl fun i _ => ?_
            simp [Matrix.one_apply]
      _ = ∑ i : ι, (∑ j : ι, (Q i j) ^ 2) * (x i * Real.log (x i)) :=
            Finset.sum_congr rfl fun i _ => by rw [hrow1 i, one_mul]
      _ = ∑ i : ι, ∑ j : ι, (Q i j) ^ 2 * (x i * Real.log (x i)) :=
            Finset.sum_congr rfl fun i _ => Finset.sum_mul ..
  have hTr2 : (X * symmLog hY).trace = ∑ i : ι, ∑ j : ι, (Q i j) ^ 2 * (x i * Real.log (y j)) := by
    rw [hLogY, hXspec]
    exact trace_prod_orth_diags x (fun j => Real.log (y j))
  have hTrX : X.trace = ∑ i : ι, ∑ j : ι, (Q i j) ^ 2 * x i := by
    have htr : X.trace = ((U * Matrix.diagonal x * Uᵀ) *
        (U * Matrix.diagonal (fun _ : ι => (1 : ℝ)) * Uᵀ)).trace := by
      have hid : U * Matrix.diagonal (fun _ : ι => (1 : ℝ)) * Uᵀ = 1 := by
        simp [Matrix.diagonal_one, eigU_mul_transpose hX.isHermitian]
      rw [hid, Matrix.mul_one, ← hXspec]
    rw [htr, trace_prod_orth_diags x (fun _ => (1 : ℝ)), eigU_transpose_mul hX.isHermitian]
    calc ∑ i : ι, ∑ j : ι, ((1 : Matrix ι ι ℝ) i j) ^ 2 * (x i * 1)
        = ∑ i : ι, x i := Finset.sum_congr rfl fun i _ => by simp [Matrix.one_apply]
      _ = ∑ i : ι, (∑ j : ι, (Q i j) ^ 2) * x i :=
            Finset.sum_congr rfl fun i _ => by rw [hrow1 i, one_mul]
      _ = ∑ i : ι, ∑ j : ι, (Q i j) ^ 2 * x i :=
            Finset.sum_congr rfl fun i _ => Finset.sum_mul ..
  have hTrY : Y.trace = ∑ i : ι, ∑ j : ι, (Q i j) ^ 2 * y j := by
    have htr : Y.trace = ((V * Matrix.diagonal (fun _ : ι => (1 : ℝ)) * Vᵀ) *
        (V * Matrix.diagonal y * Vᵀ)).trace := by
      have hid : V * Matrix.diagonal (fun _ : ι => (1 : ℝ)) * Vᵀ = 1 := by
        simp [Matrix.diagonal_one, eigU_mul_transpose hY.isHermitian]
      rw [hid, Matrix.one_mul, ← hYspec]
    rw [htr, trace_prod_orth_diags (fun _ => (1 : ℝ)) y, eigU_transpose_mul hY.isHermitian]
    calc ∑ i : ι, ∑ j : ι, ((1 : Matrix ι ι ℝ) i j) ^ 2 * (1 * y j)
        = ∑ j : ι, y j := by
            rw [Finset.sum_comm]
            refine Finset.sum_congr rfl fun j _ => by simp [Matrix.one_apply]
      _ = ∑ j : ι, (∑ i : ι, (Q i j) ^ 2) * y j :=
            Finset.sum_congr rfl fun j _ => by rw [hcol1 j, one_mul]
      _ = ∑ j : ι, ∑ i : ι, (Q i j) ^ 2 * y j :=
            Finset.sum_congr rfl fun j _ => Finset.sum_mul ..
      _ = ∑ i : ι, ∑ j : ι, (Q i j) ^ 2 * y j := Finset.sum_comm
  unfold matrixKL
  rw [Matrix.trace_add, Matrix.trace_sub, Matrix.trace_sub, hTr1, hTr2, hTrX, hTrY]
  simp only [← Finset.sum_add_distrib, ← Finset.sum_sub_distrib]
  refine Finset.sum_congr rfl fun i _ => Finset.sum_congr rfl fun j _ => by ring

/-- **Klein's Inequality (Nonnegativity of Quantum Relative Entropy)**:
    `D_KL(X || Y) ≥ 0` for all arbitrary non-commuting SPD matrices `X, Y`. -/
theorem klein_inequality_nonneg {X Y : Matrix ι ι ℝ} (hX : X.PosDef) (hY : Y.PosDef) :
    0 ≤ matrixKL hX hY := by
  rw [matrixKL_eq_double_sum hX hY]
  exact Finset.sum_nonneg fun i _ => Finset.sum_nonneg fun j _ =>
    mul_nonneg (sq_nonneg _) (kl_scalar_nonneg (hX.eigenvalues_pos i) (hY.eigenvalues_pos j))

/-- **Zero Characterization of Klein's Inequality**: `D_KL(X || Y) = 0 ↔ X = Y`. -/
theorem klein_inequality_eq_iff {X Y : Matrix ι ι ℝ} (hX : X.PosDef) (hY : Y.PosDef) :
    matrixKL hX hY = 0 ↔ X = Y := by
  constructor
  · intro heq
    rw [matrixKL_eq_double_sum hX hY] at heq
    let U := eigU hX.isHermitian
    let V := eigU hY.isHermitian
    let Q := Uᵀ * V
    let x := hX.isHermitian.eigenvalues
    let y := hY.isHermitian.eigenvalues
    have hrow0 : ∀ i ∈ (Finset.univ : Finset ι),
        ∑ j : ι, (Q i j) ^ 2 * (x i * Real.log (x i) - x i * Real.log (y j) - x i + y j) = 0 :=
      (Finset.sum_eq_zero_iff_of_nonneg fun i _ => Finset.sum_nonneg fun j _ =>
        mul_nonneg (sq_nonneg _) (kl_scalar_nonneg (hX.eigenvalues_pos i) (hY.eigenvalues_pos j))).mp heq
    have hterm0 : ∀ i j : ι,
        (Q i j) ^ 2 * (x i * Real.log (x i) - x i * Real.log (y j) - x i + y j) = 0 := fun i j =>
      (Finset.sum_eq_zero_iff_of_nonneg fun j' _ =>
        mul_nonneg (sq_nonneg _) (kl_scalar_nonneg (hX.eigenvalues_pos i) (hY.eigenvalues_pos j'))).mp
        (hrow0 i (Finset.mem_univ i)) j (Finset.mem_univ j)
    have hcomm_diag : Matrix.diagonal x * Q = Q * Matrix.diagonal y := by
      ext i j
      simp only [Matrix.mul_apply, Matrix.diagonal_apply, ite_mul, zero_mul,
        Finset.sum_ite_eq, Finset.mem_univ, ↓reduceIte, mul_ite, mul_zero, Finset.sum_ite_eq']
      by_cases hq : Q i j = 0
      · simp [hq]
      · have hkl : x i * Real.log (x i) - x i * Real.log (y j) - x i + y j = 0 :=
          (mul_eq_zero.mp (hterm0 i j)).resolve_left (pow_ne_zero 2 hq)
        have hxy : x i = y j :=
          (kl_scalar_eq_zero_iff (hX.eigenvalues_pos i) (hY.eigenvalues_pos j)).mp hkl
        change x i * Q i j = Q i j * y j
        rw [hxy, mul_comm]
    calc X = U * Matrix.diagonal x * Uᵀ := spectral_decomp hX.isHermitian
      _ = U * (Matrix.diagonal x * Q) * Vᵀ := by
            simp only [Q, Matrix.mul_assoc]; rw [eigU_mul_transpose hY.isHermitian, Matrix.mul_one]
      _ = U * (Q * Matrix.diagonal y) * Vᵀ := by rw [hcomm_diag]
      _ = V * Matrix.diagonal y * Vᵀ := by
            simp only [Q, ← Matrix.mul_assoc, eigU_mul_transpose hX.isHermitian, Matrix.one_mul]
      _ = Y := (spectral_decomp hY.isHermitian).symm
  · rintro rfl
    unfold matrixKL
    simp [Matrix.trace]

/-- Exponential KL Free-Energy Minimizer `X_kl(lam) = exp(log G0 - lam L)`. -/
def klMinimizer {G0 L : Matrix ι ι ℝ} (hG0 : G0.PosDef) (hL : L.IsHermitian) (lam : ℝ) :
    Matrix ι ι ℝ :=
  symmExp (isHermitian_sub (symmLog_isHermitian hG0) (isHermitian_smul hL lam))

theorem klMinimizer_posDef {G0 L : Matrix ι ι ℝ} (hG0 : G0.PosDef) (hL : L.IsHermitian) (lam : ℝ) :
    (klMinimizer hG0 hL lam).PosDef :=
  symmExp_posDef _

/-- **Exact Matrix-KL (Quantum Relative-Entropy) Free-Energy Completion Identity**:
    `D_KL(X || G0) + lam Tr(L X) = D_KL(X || X_kl(lam)) + Tr(G0) - Tr(X_kl(lam))`
    valid for arbitrary non-commuting SPD `G0, X` and symmetric `L`. -/
theorem kl_free_energy_identity
    {G0 L X : Matrix ι ι ℝ} (hG0 : G0.PosDef) (hL : L.IsHermitian) (hX : X.PosDef) (lam : ℝ) :
    matrixKL hX hG0 + lam * (L * X).trace =
      matrixKL hX (klMinimizer_posDef hG0 hL lam) + G0.trace - (klMinimizer hG0 hL lam).trace := by
  have hlog : symmLog (klMinimizer_posDef hG0 hL lam) = symmLog hG0 - lam • L := by
    unfold klMinimizer
    exact symmLog_symmExp _
  unfold matrixKL
  rw [hlog]
  have hcomm : (L * X).trace = (X * L).trace := Matrix.trace_mul_comm L X
  have hsmul : (X * (lam • L)).trace = lam * (X * L).trace := by
    rw [Matrix.mul_smul, Matrix.trace_smul, smul_eq_mul]
  rw [hcomm]
  simp only [Matrix.mul_sub, Matrix.trace_add, Matrix.trace_sub, hsmul]
  ring

/-- **Global Unique Minimizer Theorem for Quantum Relative-Entropy Free Energy**:
    `X_kl(lam) = exp(log G0 - lam L)` strictly uniquely minimizes `D_KL(X || G0) + lam Tr(L X)`
    across all SPD `X`, without assuming `[G0, L] = 0`. -/
theorem kl_free_energy_unique_minimizer
    {G0 L : Matrix ι ι ℝ} (hG0 : G0.PosDef) (hL : L.IsHermitian) (lam : ℝ) :
    let Xkl := klMinimizer hG0 hL lam
    let hXkl := klMinimizer_posDef hG0 hL lam
    ∀ {X : Matrix ι ι ℝ} (hX : X.PosDef),
      matrixKL hXkl hG0 + lam * (L * Xkl).trace ≤ matrixKL hX hG0 + lam * (L * X).trace ∧
      (matrixKL hX hG0 + lam * (L * X).trace = matrixKL hXkl hG0 + lam * (L * Xkl).trace →
        X = Xkl) := by
  dsimp only
  intro X hX
  have hidX := kl_free_energy_identity hG0 hL hX lam
  have hidOpt := kl_free_energy_identity hG0 hL (klMinimizer_posDef hG0 hL lam) lam
  have hzero : matrixKL (klMinimizer_posDef hG0 hL lam) (klMinimizer_posDef hG0 hL lam) = 0 :=
    (klein_inequality_eq_iff _ _).mpr rfl
  have hopt_val : matrixKL (klMinimizer_posDef hG0 hL lam) hG0 + lam * (L * klMinimizer hG0 hL lam).trace =
      G0.trace - (klMinimizer hG0 hL lam).trace := by
    rw [hidOpt, hzero]; ring
  have hnn := klein_inequality_nonneg hX (klMinimizer_posDef hG0 hL lam)
  constructor
  · linarith [hopt_val, hidX, hnn]
  · intro heq
    have hkl0 : matrixKL hX (klMinimizer_posDef hG0 hL lam) = 0 := by linarith [hopt_val, hidX, heq]
    exact (klein_inequality_eq_iff hX (klMinimizer_posDef hG0 hL lam)).mp hkl0

/-- Variational fluctuation-dissipation for Matrix-KL: `Tr(L X_kl(lam))` is antitone in `lam`. -/
theorem kl_free_energy_kinetic_antitone
    {G0 L : Matrix ι ι ℝ} (hG0 : G0.PosDef) (hL : L.IsHermitian)
    {lam₁ lam₂ : ℝ} (hlam : lam₁ ≤ lam₂) :
    (L * klMinimizer hG0 hL lam₂).trace ≤ (L * klMinimizer hG0 hL lam₁).trace := by
  set X₁ := klMinimizer hG0 hL lam₁
  set X₂ := klMinimizer hG0 hL lam₂
  set hX₁ := klMinimizer_posDef hG0 hL lam₁
  set hX₂ := klMinimizer_posDef hG0 hL lam₂
  have h1 := (kl_free_energy_unique_minimizer hG0 hL lam₁ hX₂).1
  have h2 := (kl_free_energy_unique_minimizer hG0 hL lam₂ hX₁).1
  change matrixKL hX₁ hG0 + lam₁ * (L * X₁).trace ≤ matrixKL hX₂ hG0 + lam₁ * (L * X₂).trace at h1
  change matrixKL hX₂ hG0 + lam₂ * (L * X₂).trace ≤ matrixKL hX₁ hG0 + lam₂ * (L * X₁).trace at h2
  have hdiff : (lam₂ - lam₁) * ((L * X₂).trace - (L * X₁).trace) ≤ 0 := by linarith
  rcases eq_or_lt_of_le hlam with rfl | hlt
  · exact le_rfl
  · have hpos : 0 < lam₂ - lam₁ := sub_pos.mpr hlt
    linarith [nonpos_of_mul_nonpos_right hdiff hpos]

private theorem symmLog_congr {A B : Matrix ι ι ℝ} (hA : A.PosDef) (hB : B.PosDef)
    (hab : A = B) : symmLog hA = symmLog hB := by
  subst hab; rfl

private theorem kl_opt_val_eq {G0 L : Matrix ι ι ℝ} (hG0 : G0.PosDef) (hL : L.IsHermitian) (lam : ℝ) :
    matrixKL (klMinimizer_posDef hG0 hL lam) hG0 + lam * (L * klMinimizer hG0 hL lam).trace =
      G0.trace - (klMinimizer hG0 hL lam).trace := by
  have h := kl_free_energy_identity hG0 hL (klMinimizer_posDef hG0 hL lam) lam
  have h0 : matrixKL (klMinimizer_posDef hG0 hL lam) (klMinimizer_posDef hG0 hL lam) = 0 :=
    (klein_inequality_eq_iff _ _).mpr rfl
  rw [h, h0]; ring

/-- Strict decrease of Matrix-KL kinetic energy whenever `L ≠ 0` and `lam₁ < lam₂`. -/
theorem kl_free_energy_kinetic_strictAnti
    {G0 L : Matrix ι ι ℝ} (hG0 : G0.PosDef) (hL : L.IsHermitian) (hLne : L ≠ 0)
    {lam₁ lam₂ : ℝ} (hlam : lam₁ < lam₂) :
    (L * klMinimizer hG0 hL lam₂).trace < (L * klMinimizer hG0 hL lam₁).trace := by
  set X₁ := klMinimizer hG0 hL lam₁
  set X₂ := klMinimizer hG0 hL lam₂
  set hX₁ := klMinimizer_posDef hG0 hL lam₁
  set hX₂ := klMinimizer_posDef hG0 hL lam₂
  have hXne : X₂ ≠ X₁ := by
    intro heq
    have hlog1 : symmLog hX₁ = symmLog hG0 - lam₁ • L := by
      dsimp [X₁, hX₁, klMinimizer]; exact symmLog_symmExp _
    have hlog2 : symmLog hX₂ = symmLog hG0 - lam₂ • L := by
      dsimp [X₂, hX₂, klMinimizer]; exact symmLog_symmExp _
    have heq_log : symmLog hX₂ = symmLog hX₁ := symmLog_congr hX₂ hX₁ heq
    have hlogs : symmLog hG0 - lam₂ • L = symmLog hG0 - lam₁ • L := by
      rw [← hlog2, ← hlog1, heq_log]
    have hsmul : (lam₂ - lam₁) • L = 0 := by
      rw [sub_smul]
      have : lam₂ • L = lam₁ • L := by
        have h := congrArg (fun M => symmLog hG0 - M) hlogs
        simpa [sub_sub_cancel] using h
      exact sub_eq_zero.mpr this
    rcases smul_eq_zero.mp hsmul with hcoef | hL0
    · linarith
    · exact hLne hL0
  have h1 := kl_free_energy_unique_minimizer hG0 hL lam₁ hX₂
  have h2 := kl_free_energy_unique_minimizer hG0 hL lam₂ hX₁
  have hs1 : matrixKL hX₁ hG0 + lam₁ * (L * X₁).trace <
      matrixKL hX₂ hG0 + lam₁ * (L * X₂).trace :=
    lt_of_le_of_ne h1.1 (fun heq => hXne (h1.2 heq.symm))
  have hdiff : (lam₂ - lam₁) * ((L * X₂).trace - (L * X₁).trace) < 0 := by linarith [hs1, h2.1]
  have hpos : 0 < lam₂ - lam₁ := sub_pos.mpr hlam
  linarith [neg_of_mul_neg_right hdiff hpos.le]

/-- Concavity of the Matrix-KL free-energy value function `G0.trace - X_kl(lam).trace`
    (equivalently, convexity of `lam ↦ X_kl(lam).trace` on `ℝ`). -/
theorem kl_free_energy_trace_convex
    {G0 L : Matrix ι ι ℝ} (hG0 : G0.PosDef) (hL : L.IsHermitian)
    {lam₁ lam₂ t : ℝ} (ht0 : 0 ≤ t) (ht1 : t ≤ 1) :
    (klMinimizer hG0 hL ((1 - t) * lam₁ + t * lam₂)).trace ≤
      (1 - t) * (klMinimizer hG0 hL lam₁).trace + t * (klMinimizer hG0 hL lam₂).trace := by
  let lam := (1 - t) * lam₁ + t * lam₂
  have hidLam := kl_opt_val_eq hG0 hL lam
  have hv1 : G0.trace - (klMinimizer hG0 hL lam₁).trace ≤
      matrixKL (klMinimizer_posDef hG0 hL lam) hG0 + lam₁ * (L * klMinimizer hG0 hL lam).trace := by
    rw [← kl_opt_val_eq hG0 hL lam₁]
    exact (kl_free_energy_unique_minimizer hG0 hL lam₁ (klMinimizer_posDef hG0 hL lam)).1
  have hv2 : G0.trace - (klMinimizer hG0 hL lam₂).trace ≤
      matrixKL (klMinimizer_posDef hG0 hL lam) hG0 + lam₂ * (L * klMinimizer hG0 hL lam).trace := by
    rw [← kl_opt_val_eq hG0 hL lam₂]
    exact (kl_free_energy_unique_minimizer hG0 hL lam₂ (klMinimizer_posDef hG0 hL lam)).1
  have hm1 := mul_le_mul_of_nonneg_left hv1 (sub_nonneg.mpr ht1)
  have hm2 := mul_le_mul_of_nonneg_left hv2 ht0
  have hcomb : (1 - t) * (G0.trace - (klMinimizer hG0 hL lam₁).trace) +
      t * (G0.trace - (klMinimizer hG0 hL lam₂).trace) ≤
      (1 - t) * (matrixKL (klMinimizer_posDef hG0 hL lam) hG0 +
        lam₁ * (L * klMinimizer hG0 hL lam).trace) +
      t * (matrixKL (klMinimizer_posDef hG0 hL lam) hG0 +
        lam₂ * (L * klMinimizer hG0 hL lam).trace) := add_le_add hm1 hm2
  have hright : (1 - t) * (matrixKL (klMinimizer_posDef hG0 hL lam) hG0 +
        lam₁ * (L * klMinimizer hG0 hL lam).trace) +
      t * (matrixKL (klMinimizer_posDef hG0 hL lam) hG0 +
        lam₂ * (L * klMinimizer hG0 hL lam).trace) =
      G0.trace - (klMinimizer hG0 hL lam).trace := by
    rw [← hidLam]
    dsimp only [lam]
    ring
  rw [hright] at hcomb
  linarith

/-- **Commuting Limit Coincidence**: Whenever `G0` and `L` share an orthonormal eigenbasis `Q`,
    `X_kl(lam)` equals `G_gm_heat(lam) = exp(-lam L / 2) G0 exp(-lam L / 2)` identically.
    Divergence between them (`Tr(G_gm_heat) - Tr(X_kl)`) measures pure non-commutativity `[G0, L] ≠ 0`. -/
theorem commuting_kl_eq_gm_heat
    {G0 L Q : Matrix ι ι ℝ} (hG0 : G0.PosDef) (hL : L.IsHermitian) (g μ : ι → ℝ)
    (hg_pos : ∀ i, 0 < g i)
    (hQtQ : Qᵀ * Q = 1) (hQQt : Q * Qᵀ = 1)
    (hG0eq : G0 = Q * Matrix.diagonal g * Qᵀ)
    (hLeq : L = Q * Matrix.diagonal μ * Qᵀ) (lam : ℝ) :
    klMinimizer hG0 hL lam = heatOp hL (-lam / 2) * G0 * heatOp hL (-lam / 2) := by
  have hlogG0 : symmLog hG0 = Q * Matrix.diagonal (fun i => Real.log (g i)) * Qᵀ :=
    symmLog_of_diag hG0 g hQtQ hQQt hG0eq
  have hsmulL : lam • L = Q * Matrix.diagonal (fun i => lam * μ i) * Qᵀ := by
    rw [hLeq]; exact conj_diag_smul Q μ lam
  have hsub : symmLog hG0 - lam • L =
      Q * Matrix.diagonal (fun i => Real.log (g i) - lam * μ i) * Qᵀ := by
    rw [hlogG0, hsmulL]; exact conj_diag_sub Q _ _
  have hKL : klMinimizer hG0 hL lam =
      Q * Matrix.diagonal (fun i => Real.exp (Real.log (g i) - lam * μ i)) * Qᵀ := by
    unfold klMinimizer
    exact symmExp_of_diag _ _ hQtQ hQQt hsub
  have hE : heatOp hL (-lam / 2) =
      Q * Matrix.diagonal (fun i => Real.exp ((-lam / 2) * μ i)) * Qᵀ := by
    rw [heatOp_eq_symmExp hL]
    have hsmul : (-lam / 2) • L = Q * Matrix.diagonal (fun i => (-lam / 2) * μ i) * Qᵀ := by
      rw [hLeq]; exact conj_diag_smul Q μ (-lam / 2)
    exact symmExp_of_diag (isHermitian_smul hL (-lam / 2)) _ hQtQ hQQt hsmul
  have hdiag_eq : Matrix.diagonal (fun i => Real.exp (Real.log (g i) - lam * μ i)) =
      Matrix.diagonal (fun i => Real.exp (-lam / 2 * μ i)) *
        Matrix.diagonal g * Matrix.diagonal (fun i => Real.exp (-lam / 2 * μ i)) := by
    rw [diag_mul_diag_fn, diag_mul_diag_fn]
    ext i j
    by_cases hij : i = j
    · subst hij
      simp only [Matrix.diagonal_apply_eq]
      rw [Real.exp_sub, Real.exp_log (hg_pos i), div_eq_mul_inv, ← Real.exp_neg]
      have he : Real.exp (-lam / 2 * μ i) * Real.exp (-lam / 2 * μ i) =
          Real.exp (-(lam * μ i)) := by
        rw [← Real.exp_add]; congr 1; ring
      rw [← he]
      ring
    · simp [hij]
  rw [hKL, hE, hG0eq, hdiag_eq]
  simp only [Matrix.mul_assoc]
  rw [← Matrix.mul_assoc (Qᵀ) Q _, hQtQ, Matrix.one_mul]
  rw [← Matrix.mul_assoc (Qᵀ) Q _, hQtQ, Matrix.one_mul]

end QuantumRelativeEntropyFreeEnergy

end
end MasterPrincipleFreeEnergy
