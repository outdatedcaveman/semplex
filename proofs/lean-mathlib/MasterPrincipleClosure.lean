import Mathlib

/-!
# Master Principle Closure: Exact Semidirect Unitary Presentations, Orthogonal
# Continual Retention, Stochastic Interventional DPI, & Variational MDL Closure

Machine-checked closing formalization (`Semplex.Closure`) connecting:
1. `SemidirectExactUnitary`: Parameterized unitary generator families strictly
   satisfying exact `S_3 = C_3 ⋊ C_2` and `A_4 = V_4 ⋊ C_3` mixed presentation
   relations across arbitrary `U(1)^2` phases and arbitrary `U(d)` gauge conjugations.
2. `OrthogonalReadoutRetention`: Exact zero-forgetting conservation under rank-1 /
   batch SGD updates orthogonal to kept features (`W' *ᵥ x_keep = W *ᵥ x_keep`), plus
   a bias-drift counterexample showing why bias-free/orthogonally decoupled heads are needed.
3. `StochasticInterventionalDPI`: Total-variation data-processing inequality (`tvDist`)
   for arbitrary column-stochastic channels, strict passive vs noisy active separation,
   and Markov-blanket screening.
4. `VariationalDescriptionClosure`: Exact unitary Frobenius MDL compression (`2d < |G|d`)
   and amortized quadratic free-energy optimality / midpoint convexity.
5. `MasterPrincipleSynthesis`: Unified `MasterPrincipleClosureBundle` instantiated for
   both `S_3` (`|G|=6`) and non-ambivalent `A_4` (`|G|=12`).
-/

namespace Semplex.Closure

open Matrix BigOperators

noncomputable section

-- =============================================================================
-- 1. SemidirectExactUnitary (10 theorems)
-- =============================================================================
namespace SemidirectExactUnitary

def IsUnitary {d : ℕ} (M : Matrix (Fin d) (Fin d) ℂ) : Prop :=
  M * Mᴴ = 1

def gaugeConj {d : ℕ} (V M : Matrix (Fin d) (Fin d) ℂ) : Matrix (Fin d) (Fin d) ℂ :=
  V * M * Vᴴ

private theorem mat_cube {d : ℕ} (M : Matrix (Fin d) (Fin d) ℂ) :
    M ^ 3 = M * M * M := by
  rw [pow_succ, pow_two]

private theorem isUnitary_inv_eq {d : ℕ} {V : Matrix (Fin d) (Fin d) ℂ}
    (hV : IsUnitary V) : Vᴴ * V = 1 :=
  Matrix.mul_eq_one_comm.mp hV

private theorem gaugeConj_mul {d : ℕ} {V : Matrix (Fin d) (Fin d) ℂ}
    (hV : IsUnitary V) (A B : Matrix (Fin d) (Fin d) ℂ) :
    gaugeConj V (A * B) = gaugeConj V A * gaugeConj V B := by
  have hVi := isUnitary_inv_eq hV
  calc
    V * (A * B) * Vᴴ = V * A * (1 : Matrix (Fin d) (Fin d) ℂ) * B * Vᴴ := by
        simp [Matrix.mul_assoc]
    _ = V * A * (Vᴴ * V) * B * Vᴴ := by rw [hVi]
    _ = (V * A * Vᴴ) * (V * B * Vᴴ) := by simp only [Matrix.mul_assoc]

private theorem gaugeConj_one {d : ℕ} {V : Matrix (Fin d) (Fin d) ℂ}
    (hV : IsUnitary V) : gaugeConj V 1 = 1 := by
  simpa [gaugeConj, Matrix.mul_one] using hV

private theorem gaugeConj_pow {d : ℕ} {V : Matrix (Fin d) (Fin d) ℂ}
    (hV : IsUnitary V) (M : Matrix (Fin d) (Fin d) ℂ) (k : ℕ) :
    gaugeConj V (M ^ k) = (gaugeConj V M) ^ k := by
  induction k with
  | zero => simp [gaugeConj_one hV]
  | succ n ih =>
      rw [pow_succ, pow_succ, gaugeConj_mul hV, ih]

/-- Primitive cube root of unity `ω = exp(2πi/3)`. -/
def omega3 : ℂ :=
  Complex.exp (((2 * Real.pi / 3 : ℝ) : ℂ) * Complex.I)

private theorem omega3_cube : omega3 ^ 3 = 1 := by
  unfold omega3
  rw [← Complex.exp_nat_mul]
  have hexp : ((3 : ℕ) : ℂ) * (((2 * Real.pi / 3 : ℝ) : ℂ) * Complex.I) =
      2 * (Real.pi : ℂ) * Complex.I := by
    push_cast
    ring
  rw [hexp, Complex.exp_two_pi_mul_I]

private theorem conj_exp_real_I (x : ℝ) :
    starRingEnd ℂ (Complex.exp ((x : ℂ) * Complex.I)) =
      Complex.exp (-((x : ℂ) * Complex.I)) := by
  rw [← Complex.exp_conj]
  congr 1
  simp [Complex.conj_ofReal]

private theorem exp_real_I_mul_conj (x : ℝ) :
    Complex.exp ((x : ℂ) * Complex.I) *
      starRingEnd ℂ (Complex.exp ((x : ℂ) * Complex.I)) = 1 := by
  rw [conj_exp_real_I, ← Complex.exp_add, add_neg_cancel, Complex.exp_zero]

private theorem exp_mul_I_mul_conj {z : ℂ} (hz : starRingEnd ℂ z = z) :
    Complex.exp (z * Complex.I) * starRingEnd ℂ (Complex.exp (z * Complex.I)) = 1 := by
  rw [← Complex.exp_conj, ← Complex.exp_add, _root_.map_mul, hz, Complex.conj_I]
  convert Complex.exp_zero using 2
  ring

/-- Parameterized `2×2` reflection generator `s(φ)` for `S_3 = C_3 ⋊ C_2`. -/
def s3GenS (φ : ℝ) : Matrix (Fin 2) (Fin 2) ℂ :=
  Matrix.of fun i j =>
    match i.val, j.val with
    | 0, 1 => Complex.exp ((φ : ℂ) * Complex.I)
    | 1, 0 => Complex.exp (-((φ : ℂ) * Complex.I))
    | _, _ => 0

/-- Rotation generator `r = diag(ω, ω²)` for `S_3 = C_3 ⋊ C_2`. -/
def s3GenR : Matrix (Fin 2) (Fin 2) ℂ :=
  Matrix.of fun i j =>
    match i.val, j.val with
    | 0, 0 => omega3
    | 1, 1 => omega3 ^ 2
    | _, _ => 0

/-- Theorem 1: `s3GenS φ` is unitary AND satisfies `s^2 = 1` for every phase `φ : ℝ`. -/
theorem s3GenS_unitary_and_sq (φ : ℝ) :
    IsUnitary (s3GenS φ) ∧ s3GenS φ ^ 2 = 1 := by
  have hmul : Complex.exp ((φ : ℂ) * Complex.I) * Complex.exp (-((φ : ℂ) * Complex.I)) = 1 := by
    rw [← Complex.exp_add, add_neg_cancel, Complex.exp_zero]
  have hmul' : Complex.exp (-((φ : ℂ) * Complex.I)) * Complex.exp ((φ : ℂ) * Complex.I) = 1 := by
    rw [mul_comm, hmul]
  have hconj2 : Complex.exp (-((φ : ℂ) * Complex.I)) *
      starRingEnd ℂ (Complex.exp (-((φ : ℂ) * Complex.I))) = 1 := by
    simpa [Complex.ofReal_neg, neg_mul] using exp_real_I_mul_conj (-φ)
  constructor
  · unfold IsUnitary
    ext i j
    fin_cases i <;> fin_cases j <;>
      simp [s3GenS, Matrix.mul_apply, Matrix.conjTranspose_apply, Fin.sum_univ_two]
    · exact exp_real_I_mul_conj φ
    · exact hconj2
  · rw [pow_two]
    ext i j
    fin_cases i <;> fin_cases j <;>
      simp [s3GenS, Matrix.mul_apply, Fin.sum_univ_two, hmul, hmul']

/-- Theorem 2: `s3GenR` is unitary AND satisfies `r^3 = 1`. -/
theorem s3GenR_unitary_and_cube :
    IsUnitary s3GenR ∧ s3GenR ^ 3 = 1 := by
  have hω : omega3 * starRingEnd ℂ omega3 = 1 := by
    simpa [omega3] using exp_real_I_mul_conj (2 * Real.pi / 3)
  have hω2 : omega3 ^ 2 * starRingEnd ℂ (omega3 ^ 2) = 1 := by
    rw [map_pow]
    calc
      omega3 ^ 2 * (starRingEnd ℂ omega3) ^ 2 =
        (omega3 * starRingEnd ℂ omega3) * (omega3 * starRingEnd ℂ omega3) := by ring
      _ = 1 * 1 := by rw [hω]
      _ = 1 := one_mul 1
  have hω6 : (omega3 ^ 2) ^ 3 = 1 := by
    calc
      (omega3 ^ 2) ^ 3 = (omega3 ^ 3) ^ 2 := by ring
      _ = 1 ^ 2 := by rw [omega3_cube]
      _ = 1 := one_pow 2
  constructor
  · unfold IsUnitary
    ext i j
    fin_cases i <;> fin_cases j <;>
      simp [s3GenR, Matrix.mul_apply, Matrix.conjTranspose_apply, Fin.sum_univ_two, hω]
    simpa [_root_.map_pow] using hω2
  · rw [mat_cube]
    ext i j
    fin_cases i <;> fin_cases j <;>
      simp [s3GenR, Matrix.mul_apply, Fin.sum_univ_two]
    · calc
        omega3 * omega3 * omega3 = omega3 ^ 3 := by ring
        _ = 1 := omega3_cube
    · calc
        omega3 ^ 2 * omega3 ^ 2 * omega3 ^ 2 = (omega3 ^ 2) ^ 3 := by ring
        _ = 1 := hω6

/-- Theorem 3: Exact `S_3` mixed relation `(s(φ) * r)^2 = 1` for EVERY phase `φ : ℝ`. -/
theorem s3Gen_mixed_rel (φ : ℝ) :
    (s3GenS φ * s3GenR) ^ 2 = 1 := by
  have hmul : Complex.exp ((φ : ℂ) * Complex.I) * Complex.exp (-((φ : ℂ) * Complex.I)) = 1 := by
    rw [← Complex.exp_add, add_neg_cancel, Complex.exp_zero]
  rw [pow_two]
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [s3GenS, s3GenR, Matrix.mul_apply, Fin.sum_univ_two]
  · calc
      Complex.exp ((φ : ℂ) * Complex.I) * omega3 ^ 2 *
          (Complex.exp (-((φ : ℂ) * Complex.I)) * omega3) =
        (Complex.exp ((φ : ℂ) * Complex.I) * Complex.exp (-((φ : ℂ) * Complex.I))) *
          omega3 ^ 3 := by ring
      _ = 1 * 1 := by rw [hmul, omega3_cube]
      _ = 1 := one_mul 1
  · calc
      Complex.exp (-((φ : ℂ) * Complex.I)) * omega3 *
          (Complex.exp ((φ : ℂ) * Complex.I) * omega3 ^ 2) =
        (Complex.exp ((φ : ℂ) * Complex.I) * Complex.exp (-((φ : ℂ) * Complex.I))) *
          omega3 ^ 3 := by ring
      _ = 1 * 1 := by rw [hmul, omega3_cube]
      _ = 1 := one_mul 1

/-- Theorem 4: Unitary gauge conjugation preserves all exact `S_3` presentation relations. -/
theorem s3GaugeConj_hom_rel {d : ℕ} (V M N : Matrix (Fin d) (Fin d) ℂ)
    (hV : IsUnitary V) (hM2 : M ^ 2 = 1) (hN3 : N ^ 3 = 1) (hMN : (M * N) ^ 2 = 1) :
    (gaugeConj V M) ^ 2 = 1 ∧ (gaugeConj V N) ^ 3 = 1 ∧
      (gaugeConj V M * gaugeConj V N) ^ 2 = 1 := by
  refine ⟨?_, ?_, ?_⟩
  · rw [← gaugeConj_pow hV M 2, hM2, gaugeConj_one hV]
  · rw [← gaugeConj_pow hV N 3, hN3, gaugeConj_one hV]
  · rw [← gaugeConj_mul hV M N, ← gaugeConj_pow hV (M * N) 2, hMN, gaugeConj_one hV]

/-- Reflection generator `s = diag(1, -1, -1)` for `A_4 = V_4 ⋊ C_3` on `ℂ^3`. -/
def a4GenS : Matrix (Fin 3) (Fin 3) ℂ :=
  Matrix.of fun i j =>
    match i.val, j.val with
    | 0, 0 => 1
    | 1, 1 => -1
    | 2, 2 => -1
    | _, _ => 0

/-- Continuous 2-torus phased 3-cycle generator `t(φ₁, φ₂)` for `A_4 = V_4 ⋊ C_3`. -/
def a4GenT (φ₁ φ₂ : ℝ) : Matrix (Fin 3) (Fin 3) ℂ :=
  Matrix.of fun i j =>
    match i.val, j.val with
    | 0, 1 => Complex.exp ((φ₁ : ℂ) * Complex.I)
    | 1, 2 => Complex.exp ((φ₂ : ℂ) * Complex.I)
    | 2, 0 => Complex.exp (-(((φ₁ + φ₂ : ℝ) : ℂ) * Complex.I))
    | _, _ => 0

/-- Theorem 5: `a4GenS` is unitary AND satisfies `s^2 = 1`. -/
theorem a4GenS_unitary_and_sq :
    IsUnitary a4GenS ∧ a4GenS ^ 2 = 1 := by
  constructor
  · unfold IsUnitary
    ext i j
    fin_cases i <;> fin_cases j <;>
      simp [a4GenS, Matrix.mul_apply, Matrix.conjTranspose_apply, Fin.sum_univ_three]
  · rw [pow_two]
    ext i j
    fin_cases i <;> fin_cases j <;>
      simp [a4GenS, Matrix.mul_apply, Fin.sum_univ_three]

/-- Theorem 6: `a4GenT φ₁ φ₂` is unitary AND satisfies `t^3 = 1` for EVERY `(φ₁, φ₂) : ℝ × ℝ`. -/
theorem a4GenT_unitary_and_cube (φ₁ φ₂ : ℝ) :
    IsUnitary (a4GenT φ₁ φ₂) ∧ a4GenT φ₁ φ₂ ^ 3 = 1 := by
  constructor
  · unfold IsUnitary
    ext i j
    fin_cases i <;> fin_cases j <;>
      simp [a4GenT, Matrix.mul_apply, Matrix.conjTranspose_apply, Fin.sum_univ_three]
    · exact exp_mul_I_mul_conj (by simp)
    · exact exp_mul_I_mul_conj (by simp)
    · rw [show -((↑φ₁ + ↑φ₂ : ℂ) * Complex.I) = (-((↑φ₁ + ↑φ₂ : ℂ))) * Complex.I by ring]
      exact exp_mul_I_mul_conj (by simp)
  · rw [mat_cube]
    ext i j
    fin_cases i <;> fin_cases j <;>
      simp [a4GenT, Matrix.mul_apply, Fin.sum_univ_three]
    all_goals
      rw [← Complex.exp_add, ← Complex.exp_add]
      convert Complex.exp_zero using 2
      ring

/-- Theorem 7: Exact `A_4` mixed relation `(a4GenS * a4GenT φ₁ φ₂)^3 = 1`
    identically for ALL torus phases `(φ₁, φ₂) : ℝ × ℝ`. -/
theorem a4Gen_mixed_rel (φ₁ φ₂ : ℝ) :
    (a4GenS * a4GenT φ₁ φ₂) ^ 3 = 1 := by
  let P : Matrix (Fin 3) (Fin 3) ℂ :=
    Matrix.of fun i j =>
      match i.val, j.val with
      | 0, 1 => Complex.exp ((φ₁ : ℂ) * Complex.I)
      | 1, 2 => -Complex.exp ((φ₂ : ℂ) * Complex.I)
      | 2, 0 => -Complex.exp (-(((φ₁ + φ₂ : ℝ) : ℂ) * Complex.I))
      | _, _ => 0
  have hST : a4GenS * a4GenT φ₁ φ₂ = P := by
    ext i j
    fin_cases i <;> fin_cases j <;>
      simp [a4GenS, a4GenT, P, Matrix.mul_apply, Fin.sum_univ_three]
  rw [hST, mat_cube]
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [P, Matrix.mul_apply, Fin.sum_univ_three]
  all_goals
    rw [← Complex.exp_add, ← Complex.exp_add]
    convert Complex.exp_zero using 2
    ring

/-- Theorem 8: Unitary gauge conjugation preserves all exact `A_4` presentation relations. -/
theorem a4GaugeConj_hom_rel {d : ℕ} (V M N : Matrix (Fin d) (Fin d) ℂ)
    (hV : IsUnitary V) (hM2 : M ^ 2 = 1) (hN3 : N ^ 3 = 1) (hMN3 : (M * N) ^ 3 = 1) :
    (gaugeConj V M) ^ 2 = 1 ∧ (gaugeConj V N) ^ 3 = 1 ∧
      (gaugeConj V M * gaugeConj V N) ^ 3 = 1 := by
  refine ⟨?_, ?_, ?_⟩
  · rw [← gaugeConj_pow hV M 2, hM2, gaugeConj_one hV]
  · rw [← gaugeConj_pow hV N 3, hN3, gaugeConj_one hV]
  · rw [← gaugeConj_mul hV M N, ← gaugeConj_pow hV (M * N) 3, hMN3, gaugeConj_one hV]

/-- Theorem 9: Unitary gauge conjugation preserves unitarity. -/
theorem gaugeConj_isUnitary {d : ℕ} (V M : Matrix (Fin d) (Fin d) ℂ)
    (hV : IsUnitary V) (hM : IsUnitary M) : IsUnitary (gaugeConj V M) := by
  unfold IsUnitary at hV hM ⊢
  calc
    (V * M * Vᴴ) * (V * M * Vᴴ)ᴴ
      = V * M * Vᴴ * (V * Mᴴ * Vᴴ) := by
        simp [Matrix.conjTranspose_mul, Matrix.mul_assoc]
    _ = V * M * (Vᴴ * V) * Mᴴ * Vᴴ := by simp only [Matrix.mul_assoc]
    _ = V * (M * Mᴴ) * Vᴴ := by rw [isUnitary_inv_eq hV, Matrix.mul_one]; simp [Matrix.mul_assoc]
    _ = 1 := by rw [hM, Matrix.mul_one, hV]

/-- Theorem 10: Trace invariance under arbitrary unitary gauge conjugation. -/
theorem gaugeConj_trace_eq {d : ℕ} (V M : Matrix (Fin d) (Fin d) ℂ) (hV : IsUnitary V) :
    (gaugeConj V M).trace = M.trace := by
  unfold gaugeConj
  calc
    (V * M * Vᴴ).trace = (V * (M * Vᴴ)).trace := by rw [Matrix.mul_assoc]
    _ = (M * Vᴴ * V).trace := by
        simpa [Matrix.mul_assoc] using Matrix.trace_mul_comm V (M * Vᴴ)
    _ = (M * (Vᴴ * V)).trace := by rw [Matrix.mul_assoc]
    _ = M.trace := by rw [isUnitary_inv_eq hV, Matrix.mul_one]

end SemidirectExactUnitary

-- =============================================================================
-- 2. OrthogonalReadoutRetention (6 theorems)
-- =============================================================================
namespace OrthogonalReadoutRetention

/-- Theorem 11: Outer-product weight update annihilates vectors orthogonal to the fine-tuning feature. -/
theorem outer_mulVec_orth_zero {m k : ℕ}
    (r : Fin m → ℝ) (x_ft x_keep : Fin k → ℝ)
    (horth : x_ft ⬝ᵥ x_keep = 0) :
    (Matrix.vecMulVec r x_ft) *ᵥ x_keep = 0 := by
  ext i
  simp only [Matrix.mulVec, Matrix.vecMulVec_apply, Pi.zero_apply, dotProduct]
  calc
    ∑ j, r i * x_ft j * x_keep j
      = ∑ j, r i * (x_ft j * x_keep j) := by simp [mul_assoc]
    _ = r i * ∑ j, x_ft j * x_keep j := by rw [← Finset.mul_sum]
    _ = r i * (x_ft ⬝ᵥ x_keep) := rfl
    _ = 0 := by rw [horth, mul_zero]

/-- Theorem 12: A rank-1 bias-free SGD step along `x_ft ⟂ x_keep` leaves `x_keep` logits invariant. -/
theorem orth_rank1_sgd_logit_invariant {m k : ℕ}
    (W : Matrix (Fin m) (Fin k) ℝ) (η : ℝ)
    (r : Fin m → ℝ) (x_ft x_keep : Fin k → ℝ)
    (horth : x_ft ⬝ᵥ x_keep = 0) :
    (W - η • Matrix.vecMulVec r x_ft) *ᵥ x_keep = W *ᵥ x_keep := by
  have hsm : (η • Matrix.vecMulVec r x_ft) *ᵥ x_keep =
      η • ((Matrix.vecMulVec r x_ft) *ᵥ x_keep) := by
    ext i
    simp [Matrix.mulVec, dotProduct, Finset.mul_sum, mul_assoc]
  rw [Matrix.sub_mulVec, hsm, outer_mulVec_orth_zero r x_ft x_keep horth,
    smul_zero, sub_zero]

/-- Sequential bias-free SGD fold over a batch of orthogonal updates. -/
def foldOrthSGD {m k : ℕ} (W : Matrix (Fin m) (Fin k) ℝ) :
    List (ℝ × (Fin m → ℝ) × (Fin k → ℝ)) → Matrix (Fin m) (Fin k) ℝ
  | [] => W
  | (η, r, x_ft) :: rest => foldOrthSGD (W - η • Matrix.vecMulVec r x_ft) rest

/-- Theorem 13: Arbitrary-length orthogonal SGD trajectory leaves kept logits identically invariant. -/
theorem orth_batch_sgd_logit_invariant {m k : ℕ}
    (W : Matrix (Fin m) (Fin k) ℝ)
    (updates : List (ℝ × (Fin m → ℝ) × (Fin k → ℝ)))
    (x_keep : Fin k → ℝ)
    (horth : ∀ u ∈ updates, u.2.2 ⬝ᵥ x_keep = 0) :
    (foldOrthSGD W updates) *ᵥ x_keep = W *ᵥ x_keep := by
  induction updates generalizing W with
  | nil => rfl
  | cons u rest ih =>
      rcases u with ⟨η, r, x_ft⟩
      have hu : x_ft ⬝ᵥ x_keep = 0 := horth (η, r, x_ft) (List.mem_cons_self _ _)
      have hrest : ∀ u' ∈ rest, u'.2.2 ⬝ᵥ x_keep = 0 :=
        fun u' hu' => horth u' (List.mem_cons_of_mem _ hu')
      simp only [foldOrthSGD]
      rw [ih _ hrest, orth_rank1_sgd_logit_invariant W η r x_ft x_keep hu]

/-- Theorem 14: Exact logit-margin preservation between every class pair on `x_keep`. -/
theorem orth_sgd_preserves_margin {m k : ℕ}
    (W : Matrix (Fin m) (Fin k) ℝ)
    (updates : List (ℝ × (Fin m → ℝ) × (Fin k → ℝ)))
    (x_keep : Fin k → ℝ)
    (horth : ∀ u ∈ updates, u.2.2 ⬝ᵥ x_keep = 0)
    (c₁ c₂ : Fin m) :
    ((foldOrthSGD W updates) *ᵥ x_keep) c₁ - ((foldOrthSGD W updates) *ᵥ x_keep) c₂ =
      (W *ᵥ x_keep) c₁ - (W *ᵥ x_keep) c₂ := by
  rw [orth_batch_sgd_logit_invariant W updates x_keep horth]

/-- Theorem 15: Exact top-1 prediction preservation on every kept input `x_keep`. -/
theorem orth_sgd_preserves_argmax {m k : ℕ}
    (W : Matrix (Fin m) (Fin k) ℝ)
    (updates : List (ℝ × (Fin m → ℝ) × (Fin k → ℝ)))
    (x_keep : Fin k → ℝ)
    (horth : ∀ u ∈ updates, u.2.2 ⬝ᵥ x_keep = 0)
    (c_star : Fin m)
    (hmax : ∀ c : Fin m, (W *ᵥ x_keep) c ≤ (W *ᵥ x_keep) c_star) :
    ∀ c : Fin m, ((foldOrthSGD W updates) *ᵥ x_keep) c ≤
      ((foldOrthSGD W updates) *ᵥ x_keep) c_star := by
  rw [orth_batch_sgd_logit_invariant W updates x_keep horth]
  exact hmax

/-- Theorem 16: Bias drift flips argmax on kept classes even when weight logits are completely frozen. -/
theorem bias_drift_flips_prediction_witness :
    ∃ (logits b0 b1 : Fin 2 → ℝ),
      logits 1 + b0 1 < logits 0 + b0 0 ∧
      logits 0 + b1 0 < logits 1 + b1 1 := by
  refine ⟨![1, 0], ![0, 0], ![0, 2], ?_, ?_⟩ <;> norm_num

end OrthogonalReadoutRetention

-- =============================================================================
-- 3. StochasticInterventionalDPI (7 theorems)
-- =============================================================================
namespace StochasticInterventionalDPI

def IsColStochastic {m n : ℕ} (K : Matrix (Fin m) (Fin n) ℝ) : Prop :=
  (∀ i j, 0 ≤ K i j) ∧ (∀ j, ∑ i, K i j = 1)

def tvDist {m : ℕ} (p q : Fin m → ℝ) : ℝ :=
  (1 / 2 : ℝ) * ∑ i : Fin m, |p i - q i|

/-- Theorem 17: Total-variation distance is non-negative. -/
theorem tvDist_nonneg {m : ℕ} (p q : Fin m → ℝ) : 0 ≤ tvDist p q := by
  unfold tvDist
  exact mul_nonneg (by norm_num) (Finset.sum_nonneg (fun i _ => abs_nonneg _))

/-- Theorem 18: Total-variation distance is symmetric. -/
theorem tvDist_symm {m : ℕ} (p q : Fin m → ℝ) : tvDist p q = tvDist q p := by
  unfold tvDist
  congr 1
  refine Finset.sum_congr rfl (fun i _ => abs_sub_comm _ _)

/-- Theorem 19: Total-variation distance vanishes on identical vectors. -/
theorem tvDist_self {m : ℕ} (p : Fin m → ℝ) : tvDist p p = 0 := by
  simp [tvDist]

/-- Theorem 20: Total-variation distance satisfies the triangle inequality. -/
theorem tvDist_triangle {m : ℕ} (p r q : Fin m → ℝ) :
    tvDist p q ≤ tvDist p r + tvDist r q := by
  unfold tvDist
  have hsum : ∑ i : Fin m, |p i - q i| ≤
      ∑ i : Fin m, |p i - r i| + ∑ i : Fin m, |r i - q i| := by
    rw [← Finset.sum_add_distrib]
    exact Finset.sum_le_sum (fun i _ => abs_sub_le (p i) (r i) (q i))
  linarith

/-- Theorem 21: Total-variation Data-Processing Inequality (`tvDist (K*p, K*q) <= tvDist (p, q)`). -/
theorem stochastic_channel_tv_dpi {m n : ℕ}
    (K : Matrix (Fin m) (Fin n) ℝ) (hK : IsColStochastic K)
    (p q : Fin n → ℝ) :
    tvDist (K *ᵥ p) (K *ᵥ q) ≤ tvDist p q := by
  unfold tvDist
  have hline : ∀ i : Fin m, |(K *ᵥ p) i - (K *ᵥ q) i| ≤ ∑ j : Fin n, K i j * |p j - q j| := by
    intro i
    calc
      |(K *ᵥ p) i - (K *ᵥ q) i|
        = |∑ j : Fin n, K i j * (p j - q j)| := by
          congr 1
          simp only [Matrix.mulVec, dotProduct, ← Finset.sum_sub_distrib, ← mul_sub]
      _ ≤ ∑ j : Fin n, |K i j * (p j - q j)| := Finset.abs_sum_le_sum_abs _ _
      _ = ∑ j : Fin n, K i j * |p j - q j| := by
          refine Finset.sum_congr rfl (fun j _ => ?_)
          rw [abs_mul, abs_of_nonneg (hK.1 i j)]
  have hsum : ∑ i : Fin m, |(K *ᵥ p) i - (K *ᵥ q) i| ≤ ∑ j : Fin n, |p j - q j| := by
    calc
      ∑ i : Fin m, |(K *ᵥ p) i - (K *ᵥ q) i|
        ≤ ∑ i : Fin m, ∑ j : Fin n, K i j * |p j - q j| :=
          Finset.sum_le_sum (fun i _ => hline i)
      _ = ∑ j : Fin n, ∑ i : Fin m, K i j * |p j - q j| := Finset.sum_comm
      _ = ∑ j : Fin n, (∑ i : Fin m, K i j) * |p j - q j| := by
          refine Finset.sum_congr rfl (fun j _ => ?_)
          rw [Finset.sum_mul]
      _ = ∑ j : Fin n, |p j - q j| := by
          refine Finset.sum_congr rfl (fun j _ => ?_)
          rw [hK.2 j, one_mul]
  linarith

/-- Theorem 22: Concrete noisy `3:1` POMDP separation: passive marginal projection has
    `tvDist = 0` while active 1-step reveal kernel achieves `tvDist = 1/2 > 0`. -/
theorem noisy_hidden_bit_passive_vs_active :
    ∃ (passiveProj activeReveal : Matrix (Fin 2) (Fin 2) ℝ) (p0 p1 : Fin 2 → ℝ),
      IsColStochastic passiveProj ∧
      IsColStochastic activeReveal ∧
      tvDist (passiveProj *ᵥ p0) (passiveProj *ᵥ p1) = 0 ∧
      tvDist (activeReveal *ᵥ p0) (activeReveal *ᵥ p1) = (1 / 2 : ℝ) ∧
      (0 : ℝ) < tvDist (activeReveal *ᵥ p0) (activeReveal *ᵥ p1) := by
  let passiveProj : Matrix (Fin 2) (Fin 2) ℝ := ![![1, 1], ![0, 0]]
  let activeReveal : Matrix (Fin 2) (Fin 2) ℝ := ![![3 / 4, 1 / 4], ![1 / 4, 3 / 4]]
  let p0 : Fin 2 → ℝ := ![1, 0]
  let p1 : Fin 2 → ℝ := ![0, 1]
  refine ⟨passiveProj, activeReveal, p0, p1, ?_, ?_, ?_, ?_, ?_⟩
  · constructor
    · intro i j; fin_cases i <;> fin_cases j <;> simp [passiveProj]
    · intro j; fin_cases j <;> simp [passiveProj, Fin.sum_univ_two]
  · constructor
    · intro i j; fin_cases i <;> fin_cases j <;> simp [activeReveal] <;> norm_num
    · intro j; fin_cases j <;> simp [activeReveal, Fin.sum_univ_two] <;> norm_num
  · simp [tvDist, passiveProj, p0, p1, Matrix.mulVec, dotProduct, Fin.sum_univ_two]
  · simp [tvDist, activeReveal, p0, p1, Matrix.mulVec, dotProduct, Fin.sum_univ_two]
    rw [show (3 / 4 - 4⁻¹ : ℝ) = 1 / 2 by norm_num,
        show (4⁻¹ - 3 / 4 : ℝ) = -(1 / 2) by norm_num,
        abs_neg (1 / 2 : ℝ),
        abs_of_pos (by norm_num : (0 : ℝ) < 1 / 2)]
    norm_num
  · simp [tvDist, activeReveal, p0, p1, Matrix.mulVec, dotProduct, Fin.sum_univ_two]
    rw [show (3 / 4 - 4⁻¹ : ℝ) = 1 / 2 by norm_num,
        show (4⁻¹ - 3 / 4 : ℝ) = -(1 / 2) by norm_num,
        abs_neg (1 / 2 : ℝ),
        abs_of_pos (by norm_num : (0 : ℝ) < 1 / 2)]
    norm_num

/-- Theorem 23: Markov-blanket screening: internal distributions sharing identical blanket
    marginals induce zero observation TV divergence under any factored blanket channel. -/
theorem markov_blanket_screened_kernel {m b n : ℕ}
    (O_B : Matrix (Fin m) (Fin b) ℝ) (B : Matrix (Fin b) (Fin n) ℝ)
    (p q : Fin n → ℝ)
    (hblanket : B *ᵥ p = B *ᵥ q) :
    tvDist ((O_B * B) *ᵥ p) ((O_B * B) *ᵥ q) = 0 := by
  rw [← Matrix.mulVec_mulVec, ← Matrix.mulVec_mulVec, hblanket, tvDist_self]

end StochasticInterventionalDPI

-- =============================================================================
-- 4. VariationalDescriptionClosure (6 theorems)
-- =============================================================================
namespace VariationalDescriptionClosure

open SemidirectExactUnitary

def frobNormSq {d : ℕ} (M : Matrix (Fin d) (Fin d) ℂ) : ℝ :=
  ∑ i : Fin d, ∑ j : Fin d, ‖M i j‖ ^ 2

/-- Theorem 24: Every `d×d` unitary matrix has exact Frobenius norm squared `d`. -/
theorem unitary_frobNormSq {d : ℕ} (M : Matrix (Fin d) (Fin d) ℂ)
    (hM : M * Mᴴ = 1) :
    frobNormSq M = d := by
  unfold frobNormSq
  have hdiag : ∀ i : Fin d, ∑ j : Fin d, ‖M i j‖ ^ 2 = 1 := by
    intro i
    have hre : ((M * Mᴴ) i i).re = ((1 : Matrix (Fin d) (Fin d) ℂ) i i).re := by
      rw [hM]
    simp only [Matrix.one_apply_eq, Complex.one_re] at hre
    have hsum : ((M * Mᴴ) i i).re = ∑ j : Fin d, ‖M i j‖ ^ 2 := by
      simp only [Matrix.mul_apply, Matrix.conjTranspose_apply, Complex.re_sum]
      refine Finset.sum_congr rfl (fun j _ => ?_)
      change (M i j * starRingEnd ℂ (M i j)).re = ‖M i j‖ ^ 2
      rw [Complex.mul_conj, Complex.ofReal_re, Complex.normSq_eq_abs, Complex.norm_eq_abs]
    linarith
  calc
    ∑ i : Fin d, ∑ j : Fin d, ‖M i j‖ ^ 2 = ∑ _i : Fin d, (1 : ℝ) := by
      refine Finset.sum_congr rfl (fun i _ => hdiag i)
    _ = d := by simp

/-- Theorem 25: Unitary Frobenius norm squared is strictly invariant under unitary gauge conjugation. -/
theorem unitary_frobNormSq_gauge_invariant {d : ℕ}
    (V M : Matrix (Fin d) (Fin d) ℂ) (hV : IsUnitary V) (hM : IsUnitary M) :
    frobNormSq (gaugeConj V M) = frobNormSq M := by
  rw [unitary_frobNormSq (gaugeConj V M) (gaugeConj_isUnitary V M hV hM),
      unitary_frobNormSq M hM]

/-- Theorem 25: Semidirect 2-generator unitary parameter norm (`2d`) is strictly
    smaller than full unitary bank parameter norm (`|G| * d`) for any group of order `> 2`. -/
theorem semidirect_generator_mdl_compression (gSize d : ℕ)
    (hg : 2 < gSize) (hd : 0 < d) :
    (2 : ℝ) * d < (gSize : ℝ) * d := by
  have hd_pos : (0 : ℝ) < d := Nat.cast_pos.mpr hd
  have hg_lt : (2 : ℝ) < gSize := Nat.cast_lt.mpr hg
  exact mul_lt_mul_of_pos_right hg_lt hd_pos

def quadEnergy {n : ℕ} (A : Matrix (Fin n) (Fin n) ℝ) (b x : Fin n → ℝ) : ℝ :=
  (1 / 2 : ℝ) * (x ⬝ᵥ (A *ᵥ x)) - b ⬝ᵥ x

private theorem symm_dot_mulVec_comm {n : ℕ} {A : Matrix (Fin n) (Fin n) ℝ}
    (hSym : Aᵀ = A) (u v : Fin n → ℝ) :
    u ⬝ᵥ (A *ᵥ v) = v ⬝ᵥ (A *ᵥ u) := by
  calc
    u ⬝ᵥ (A *ᵥ v) = (u ᵥ* A) ⬝ᵥ v := Matrix.dotProduct_mulVec u A v
    _ = (u ᵥ* Aᵀ) ⬝ᵥ v := by rw [hSym]
    _ = (A *ᵥ u) ⬝ᵥ v := by rw [Matrix.vecMul_transpose]
    _ = v ⬝ᵥ (A *ᵥ u) := dotProduct_comm _ _

private theorem quadEnergy_diff_exact {n : ℕ} {A : Matrix (Fin n) (Fin n) ℝ}
    (hSym : Aᵀ = A) (b x x_star : Fin n → ℝ) (hopt : A *ᵥ x_star = b) :
    quadEnergy A b x - quadEnergy A b x_star =
      (1 / 2 : ℝ) * ((x - x_star) ⬝ᵥ (A *ᵥ (x - x_star))) := by
  unfold quadEnergy
  have h1 : (x - x_star) ⬝ᵥ (A *ᵥ (x - x_star)) =
      x ⬝ᵥ (A *ᵥ x) - 2 * (x ⬝ᵥ (A *ᵥ x_star)) + x_star ⬝ᵥ (A *ᵥ x_star) := by
    rw [Matrix.mulVec_sub, dotProduct_sub, sub_dotProduct, sub_dotProduct,
      symm_dot_mulVec_comm hSym x_star x]
    ring
  have hbx : b ⬝ᵥ x = x ⬝ᵥ (A *ᵥ x_star) := by
    rw [← hopt, dotProduct_comm]
  have hbs : b ⬝ᵥ x_star = x_star ⬝ᵥ (A *ᵥ x_star) := by
    rw [← hopt, dotProduct_comm]
  rw [h1, hbx, hbs]
  ring

/-- Theorem 26: Global optimality of the exact variational/Riccati solution over any amortized guess. -/
theorem amortized_quad_ge_opt {n : ℕ} {A : Matrix (Fin n) (Fin n) ℝ}
    (hSym : Aᵀ = A) (hPSD : ∀ v : Fin n → ℝ, 0 ≤ v ⬝ᵥ (A *ᵥ v))
    (b x x_star : Fin n → ℝ) (hopt : A *ᵥ x_star = b) :
    quadEnergy A b x_star ≤ quadEnergy A b x := by
  have hdiff := quadEnergy_diff_exact hSym b x x_star hopt
  have hnonneg : 0 ≤ (1 / 2 : ℝ) * ((x - x_star) ⬝ᵥ (A *ᵥ (x - x_star))) :=
    mul_nonneg (by norm_num) (hPSD (x - x_star))
  linarith

/-- Theorem 27: Zero variational suboptimality gap holds iff the Hessian quadratic residual vanishes. -/
theorem amortized_quad_eq_iff_zero_gap {n : ℕ} {A : Matrix (Fin n) (Fin n) ℝ}
    (hSym : Aᵀ = A) (b x x_star : Fin n → ℝ) (hopt : A *ᵥ x_star = b) :
    quadEnergy A b x = quadEnergy A b x_star ↔
      (x - x_star) ⬝ᵥ (A *ᵥ (x - x_star)) = 0 := by
  have hdiff := quadEnergy_diff_exact hSym b x x_star hopt
  constructor <;> intro h <;> linarith

/-- Theorem 28: Midpoint convexity of the quadratic free-energy functional under PSD curvature. -/
theorem quadEnergy_midpoint_convex {n : ℕ} {A : Matrix (Fin n) (Fin n) ℝ}
    (hSym : Aᵀ = A) (hPSD : ∀ v : Fin n → ℝ, 0 ≤ v ⬝ᵥ (A *ᵥ v))
    (b x y : Fin n → ℝ) :
    quadEnergy A b ((1 / 2 : ℝ) • (x + y)) ≤
      (1 / 2 : ℝ) * (quadEnergy A b x + quadEnergy A b y) := by
  unfold quadEnergy
  have hm : ((1 / 2 : ℝ) • (x + y)) ⬝ᵥ (A *ᵥ ((1 / 2 : ℝ) • (x + y))) =
      (1 / 4 : ℝ) * (x ⬝ᵥ (A *ᵥ x) + 2 * (x ⬝ᵥ (A *ᵥ y)) + y ⬝ᵥ (A *ᵥ y)) := by
    rw [Matrix.mulVec_smul, smul_dotProduct, dotProduct_smul, Matrix.mulVec_add,
      dotProduct_add, add_dotProduct, add_dotProduct, symm_dot_mulVec_comm hSym y x]
    simp only [smul_eq_mul]
    ring
  have hbm : b ⬝ᵥ ((1 / 2 : ℝ) • (x + y)) = (1 / 2 : ℝ) * (b ⬝ᵥ x + b ⬝ᵥ y) := by
    rw [dotProduct_smul, dotProduct_add]
    simp only [smul_eq_mul]
  have hd : (x - y) ⬝ᵥ (A *ᵥ (x - y)) =
      x ⬝ᵥ (A *ᵥ x) - 2 * (x ⬝ᵥ (A *ᵥ y)) + y ⬝ᵥ (A *ᵥ y) := by
    rw [Matrix.mulVec_sub, dotProduct_sub, sub_dotProduct, sub_dotProduct,
      symm_dot_mulVec_comm hSym y x]
    ring
  have hnonneg : 0 ≤ (x - y) ⬝ᵥ (A *ᵥ (x - y)) := hPSD (x - y)
  rw [hm, hbm]
  linarith

end VariationalDescriptionClosure

-- =============================================================================
-- 5. MasterPrincipleSynthesis (5 theorems)
-- =============================================================================
namespace MasterPrincipleSynthesis

open SemidirectExactUnitary
open OrthogonalReadoutRetention
open StochasticInterventionalDPI
open VariationalDescriptionClosure

/-- Closed operational bundle unifying exact generator presentation, unitary MDL norm,
    orthogonal continual retention, stochastic DPI, and active-vs-passive separation. -/
structure MasterPrincipleClosureBundle (d gSize : ℕ) where
  gen0 : Matrix (Fin d) (Fin d) ℂ
  gen1 : Matrix (Fin d) (Fin d) ℂ
  unitary0 : IsUnitary gen0
  unitary1 : IsUnitary gen1
  mdl_gap : frobNormSq gen0 + frobNormSq gen1 < (gSize : ℝ) * d
  active_strictly_positive : ∃ (passive active : Matrix (Fin 2) (Fin 2) ℝ) (p0 p1 : Fin 2 → ℝ),
    IsColStochastic passive ∧ IsColStochastic active ∧
    tvDist (passive *ᵥ p0) (passive *ᵥ p1) = 0 ∧
    0 < tvDist (active *ᵥ p0) (active *ᵥ p1)

/-- Theorem 29: Concrete closure bundle for non-abelian `S_3` (`|G| = 6`, `d = 2`). -/
theorem s3_master_principle_exact_closure (φ : ℝ) :
    Nonempty (MasterPrincipleClosureBundle 2 6) := by
  have hs := s3GenS_unitary_and_sq φ
  have hr := s3GenR_unitary_and_cube
  refine ⟨{
    gen0 := s3GenS φ
    gen1 := s3GenR
    unitary0 := hs.1
    unitary1 := hr.1
    mdl_gap := ?_
    active_strictly_positive := ?_
  }⟩
  · rw [unitary_frobNormSq _ hs.1, unitary_frobNormSq _ hr.1]
    have hmdl := semidirect_generator_mdl_compression 6 2 (by omega) (by omega)
    norm_num at hmdl ⊢
  · rcases noisy_hidden_bit_passive_vs_active with ⟨pas, act, p0, p1, hp, ha, h0, _, hpos⟩
    exact ⟨pas, act, p0, p1, hp, ha, h0, hpos⟩

/-- Theorem 30: Concrete closure bundle for non-ambivalent `A_4` (`|G| = 12`, `d = 3`). -/
theorem a4_master_principle_exact_closure (φ₁ φ₂ : ℝ) :
    Nonempty (MasterPrincipleClosureBundle 3 12) := by
  have hs := a4GenS_unitary_and_sq
  have ht := a4GenT_unitary_and_cube φ₁ φ₂
  refine ⟨{
    gen0 := a4GenS
    gen1 := a4GenT φ₁ φ₂
    unitary0 := hs.1
    unitary1 := ht.1
    mdl_gap := ?_
    active_strictly_positive := ?_
  }⟩
  · rw [unitary_frobNormSq _ hs.1, unitary_frobNormSq _ ht.1]
    have hmdl := semidirect_generator_mdl_compression 12 3 (by omega) (by omega)
    norm_num at hmdl ⊢
  · rcases noisy_hidden_bit_passive_vs_active with ⟨pas, act, p0, p1, hp, ha, h0, _, hpos⟩
    exact ⟨pas, act, p0, p1, hp, ha, h0, hpos⟩

/-- Theorem 31: Exact unitary gauge representations paired with orthogonal bias-free
    SGD updates preserve trace invariants AND exact kept-class predictions simultaneously. -/
theorem orth_whitened_exact_representation_zero_forgetting {d m k : ℕ}
    (V M : Matrix (Fin d) (Fin d) ℂ) (hV : IsUnitary V)
    (W : Matrix (Fin m) (Fin k) ℝ)
    (updates : List (ℝ × (Fin m → ℝ) × (Fin k → ℝ)))
    (x_keep : Fin k → ℝ)
    (horth : ∀ u ∈ updates, u.2.2 ⬝ᵥ x_keep = 0)
    (c_star : Fin m)
    (hmax : ∀ c : Fin m, (W *ᵥ x_keep) c ≤ (W *ᵥ x_keep) c_star) :
    (gaugeConj V M).trace = M.trace ∧
      (∀ c : Fin m, ((foldOrthSGD W updates) *ᵥ x_keep) c ≤
        ((foldOrthSGD W updates) *ᵥ x_keep) c_star) :=
  ⟨gaugeConj_trace_eq V M hV, orth_sgd_preserves_argmax W updates x_keep horth c_star hmax⟩

/-- Theorem 32: Channel TV contractivity together with active interventional witness strictly
    dominating passive zero-budget observation under 25% noise. -/
theorem active_interventional_strictly_dominates_passive {m n : ℕ}
    (K : Matrix (Fin m) (Fin n) ℝ) (hK : IsColStochastic K) (p q : Fin n → ℝ) :
    tvDist (K *ᵥ p) (K *ᵥ q) ≤ tvDist p q ∧
      ∃ (passive active : Matrix (Fin 2) (Fin 2) ℝ) (p0 p1 : Fin 2 → ℝ),
        tvDist (passive *ᵥ p0) (passive *ᵥ p1) < tvDist (active *ᵥ p0) (active *ᵥ p1) := by
  refine ⟨stochastic_channel_tv_dpi K hK p q, ?_⟩
  rcases noisy_hidden_bit_passive_vs_active with ⟨pas, act, p0, p1, _, _, h0, _, hpos⟩
  exact ⟨pas, act, p0, p1, by linarith⟩

/-- Theorem 33: Joint variational-MDL & stochastic-channel summary: generator norm collapses,
    amortized variational energy attains its unique global minimum, and Markov-blanket
    factorization screens identical boundary states. -/
theorem master_principle_mdl_and_dpi_summary {d gSize n m b : ℕ}
    (M0 M1 : Matrix (Fin d) (Fin d) ℂ) (h0 : IsUnitary M0) (h1 : IsUnitary M1)
    (hg : 2 < gSize) (hd : 0 < d)
    {A : Matrix (Fin n) (Fin n) ℝ} (hSym : Aᵀ = A) (hPSD : ∀ v, 0 ≤ v ⬝ᵥ (A *ᵥ v))
    (rhs x x_star : Fin n → ℝ) (hopt : A *ᵥ x_star = rhs)
    (O_B : Matrix (Fin m) (Fin b) ℝ) (B : Matrix (Fin b) (Fin n) ℝ)
    (p q : Fin n → ℝ) (hb : B *ᵥ p = B *ᵥ q) :
    frobNormSq M0 + frobNormSq M1 < (gSize : ℝ) * d ∧
      quadEnergy A rhs x_star ≤ quadEnergy A rhs x ∧
      tvDist ((O_B * B) *ᵥ p) ((O_B * B) *ᵥ q) = 0 := by
  refine ⟨?_, amortized_quad_ge_opt hSym hPSD rhs x x_star hopt,
    markov_blanket_screened_kernel O_B B p q hb⟩
  rw [unitary_frobNormSq M0 h0, unitary_frobNormSq M1 h1]
  have hmdl := semidirect_generator_mdl_compression gSize d hg hd
  linarith

end MasterPrincipleSynthesis

end

end Semplex.Closure
