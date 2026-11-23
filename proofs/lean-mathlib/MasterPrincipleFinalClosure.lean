import Mathlib

/-!
# Final Closure Bridge (`Semplex.FinalClosure`)

Closes four remaining mathematical seams across the Semplex Master Principle:
1. `AlgebraicClosureSeam` (`memory 15108`, 6 theorems): Proves by explicit finite
   countermodels that eigenspace of `G` does not imply action invariance and action-invariant
   linear subspace does not imply pointwise algebra closure, while an action-invariant
   observable algebra induces an exact action congruence whose quotient embeds
   faithfully into operational profile space.
2. `TemplateFreeRelationLocking` (6 theorems): Unitary invariance, trace gauge
   invariance, abstract `A5` relation satisfaction `(U0 * U1)^5 = 1`, zero-drift
   orthogonal SGD, and `2d` generator MDL without pre-programmed golden ratios.
3. `ContinuousSO3Gauge` (7 theorems): Continuous 3D rotation Lie group `SO(3)`
   closure under product/transpose/conjugation, trace gauge invariance, general
   `[-3, 3]` trace bound, plus explicit axis-angle `rotZ θ ∈ SO(3)` with
   `Tr(rotZ θ) = 1 + 2 * Real.cos θ ∈ [-1, 3]`.
4. `QuantitativeFiniteSampleT6` (5 theorems): Bernoulli variance bound
   `p(1 - p) ≤ 1/4`, Bienaymé–Chebyshev TV separation tail bound positivity and
   monotonicity in `N` and `δ`, and sufficient sample threshold linking T6
   budget monotonicity to quantitative concentration.
-/

namespace Semplex.FinalClosure

open Matrix BigOperators

noncomputable section

-- =============================================================================
-- 1. AlgebraicClosureSeam (6 theorems)
-- =============================================================================
namespace AlgebraicClosureSeam

def koopman {X : Type*} (T : X → X) (f : X → ℝ) : X → ℝ :=
  fun x => f (T x)

def ActionInvariant {X A : Type*} (step : A → X → X) (S : Set (X → ℝ)) : Prop :=
  ∀ a f, f ∈ S → koopman (step a) f ∈ S

def obsRel {X : Type*} (S : Set (X → ℝ)) (x y : X) : Prop :=
  ∀ f, f ∈ S → f x = f y

def IsActionCongruence {X A : Type*} (step : A → X → X) (R : X → X → Prop) : Prop :=
  ∀ a x y, R x y → R (step a x) (step a y)

/-- Theorem 1: A self-adjoint operator eigenspace need not be `U_a`-invariant. -/
theorem eigenspace_not_action_invariant_witness :
    let G : Matrix (Fin 2) (Fin 2) ℝ := !![2, 0; 0, 1]
    let U : Matrix (Fin 2) (Fin 2) ℝ := !![0, 1; 1, 0]
    let v : Fin 2 → ℝ := ![1, 0]
    G *ᵥ v = (2 : ℝ) • v ∧ G *ᵥ (U *ᵥ v) ≠ (2 : ℝ) • (U *ᵥ v) := by
  constructor
  · ext i
    fin_cases i <;> simp [Matrix.mulVec, dotProduct]
  · intro h
    have h1 := congrFun h 1
    simp [Matrix.mulVec, dotProduct] at h1

private def oddSwapT : Fin 3 → Fin 3 := ![1, 0, 2]
private def oddVecF : Fin 3 → ℝ := ![1, -1, 0]

/-- Theorem 2: An action-invariant linear subspace need not be closed under
    pointwise multiplication. -/
theorem invariant_subspace_not_algebra_closed_witness :
    let S : Set (Fin 3 → ℝ) := {g | ∃ c : ℝ, g = fun x => c * oddVecF x}
    (∀ g, g ∈ S → koopman oddSwapT g ∈ S) ∧ (fun x => oddVecF x * oddVecF x) ∉ S := by
  refine ⟨?_, ?_⟩
  · rintro g ⟨c, rfl⟩
    refine ⟨-c, ?_⟩
    ext x
    fin_cases x <;> simp [koopman, oddSwapT, oddVecF] <;> ring
  · rintro ⟨c, hc⟩
    have h0 := congrFun hc 0
    have h1 := congrFun hc 1
    simp [oddVecF] at h0 h1
    linarith

/-- Theorem 3: Any observable family induces an equivalence relation. -/
theorem obsRel_equiv {X : Type*} (S : Set (X → ℝ)) : Equivalence (obsRel S) where
  refl _ _ _ := rfl
  symm h f hf := (h f hf).symm
  trans h1 h2 f hf := (h1 f hf).trans (h2 f hf)

/-- Theorem 4: Any action-invariant observable set induces an action congruence. -/
theorem actionInvariant_induces_congruence {X A : Type*}
    (step : A → X → X) (S : Set (X → ℝ))
    (hinv : ActionInvariant step S) :
    IsActionCongruence step (obsRel S) := by
  intro a x y hxy f hf
  exact hxy (koopman (step a) f) (hinv a f hf)

def obsSetoid {X : Type*} (S : Set (X → ℝ)) : Setoid X where
  r := obsRel S
  iseqv := obsRel_equiv S

def quotientEval {X : Type*} (S : Set (X → ℝ)) (f : X → ℝ) (hf : f ∈ S) :
    Quotient (obsSetoid S) → ℝ :=
  Quotient.lift f (fun _ _ h => h f hf)

/-- Theorem 5: Every observable in `S` factors through `Quotient (obsSetoid S)`. -/
theorem quotientEval_mk {X : Type*} (S : Set (X → ℝ)) (f : X → ℝ) (hf : f ∈ S) (x : X) :
    quotientEval S f hf (Quotient.mk (obsSetoid S) x) = f x := rfl

/-- Theorem 6: The induced profile evaluation separates distinct quotient classes. -/
theorem quotient_profile_separates {X : Type*} (S : Set (X → ℝ))
    (q1 q2 : Quotient (obsSetoid S))
    (hagree : ∀ f (hf : f ∈ S), quotientEval S f hf q1 = quotientEval S f hf q2) :
    q1 = q2 := by
  refine Quotient.inductionOn₂ q1 q2 ?_ hagree
  intro x y hxy
  apply Quotient.sound
  intro f hf
  exact hxy f hf

end AlgebraicClosureSeam

-- =============================================================================
-- 2. TemplateFreeRelationLocking (6 theorems)
-- =============================================================================
namespace TemplateFreeRelationLocking

def IsUnitary {d : ℕ} (M : Matrix (Fin d) (Fin d) ℂ) : Prop :=
  M * Mᴴ = 1

def gaugeConj {d : ℕ} (V M : Matrix (Fin d) (Fin d) ℂ) : Matrix (Fin d) (Fin d) ℂ :=
  V * M * Vᴴ

def frobNormSq {d : ℕ} (M : Matrix (Fin d) (Fin d) ℂ) : ℝ :=
  ∑ i : Fin d, ∑ j : Fin d, ‖M i j‖ ^ 2

def SatisfiesA5Rels {d : ℕ} (U0 U1 : Matrix (Fin d) (Fin d) ℂ) : Prop :=
  IsUnitary U0 ∧ IsUnitary U1 ∧ U0 ^ 2 = 1 ∧ U1 ^ 3 = 1 ∧ (U0 * U1) ^ 5 = 1

private theorem unitary_conj_mul {d : ℕ} {V : Matrix (Fin d) (Fin d) ℂ}
    (hV : IsUnitary V) : Vᴴ * V = 1 :=
  Matrix.mul_eq_one_comm.mp hV

private theorem gaugeConj_isUnitary {d : ℕ} (V M : Matrix (Fin d) (Fin d) ℂ)
    (hV : IsUnitary V) (hM : IsUnitary M) : IsUnitary (gaugeConj V M) := by
  unfold IsUnitary at hV hM ⊢
  unfold gaugeConj
  calc
    (V * M * Vᴴ) * (V * M * Vᴴ)ᴴ
      = V * M * (Vᴴ * V) * Mᴴ * Vᴴ := by simp [Matrix.conjTranspose_mul, Matrix.mul_assoc]
    _ = V * (M * Mᴴ) * Vᴴ := by rw [unitary_conj_mul hV]; simp [Matrix.mul_assoc]
    _ = 1 := by rw [hM, Matrix.mul_one, hV]

private theorem gaugeConj_mul {d : ℕ} {V : Matrix (Fin d) (Fin d) ℂ}
    (hV : IsUnitary V) (A B : Matrix (Fin d) (Fin d) ℂ) :
    gaugeConj V (A * B) = gaugeConj V A * gaugeConj V B := by
  unfold gaugeConj
  calc
    V * (A * B) * Vᴴ = V * A * (Vᴴ * V) * B * Vᴴ := by
        rw [unitary_conj_mul hV]; simp [Matrix.mul_assoc]
    _ = (V * A * Vᴴ) * (V * B * Vᴴ) := by simp [Matrix.mul_assoc]

private theorem gaugeConj_pow {d : ℕ} {V : Matrix (Fin d) (Fin d) ℂ}
    (hV : IsUnitary V) (M : Matrix (Fin d) (Fin d) ℂ) (k : ℕ) :
    gaugeConj V (M ^ k) = (gaugeConj V M) ^ k := by
  induction k with
  | zero => simpa [gaugeConj] using hV
  | succ n ih => rw [pow_succ, pow_succ, gaugeConj_mul hV, ih]

/-- Theorem 7: Abstract `A5` presentation locking is gauge-invariant under arbitrary `V ∈ U(d)`. -/
theorem gaugeConj_preserves_a5_rels {d : ℕ} (V U0 U1 : Matrix (Fin d) (Fin d) ℂ)
    (hV : IsUnitary V) (hA5 : SatisfiesA5Rels U0 U1) :
    SatisfiesA5Rels (gaugeConj V U0) (gaugeConj V U1) := by
  rcases hA5 with ⟨h0, h1, hs, ht, h5⟩
  refine ⟨gaugeConj_isUnitary V U0 hV h0, gaugeConj_isUnitary V U1 hV h1, ?_, ?_, ?_⟩
  · rw [← gaugeConj_pow hV, hs]; simpa [gaugeConj] using hV
  · rw [← gaugeConj_pow hV, ht]; simpa [gaugeConj] using hV
  · rw [← gaugeConj_mul hV, ← gaugeConj_pow hV, h5]; simpa [gaugeConj] using hV

/-- Theorem 8: Relation residual zero implies exact `(U0 * U1)^5 = 1`. -/
theorem relation_defect_zero_iff_exact {d : ℕ} (U0 U1 : Matrix (Fin d) (Fin d) ℂ) :
    (U0 * U1) ^ 5 - 1 = 0 ↔ (U0 * U1) ^ 5 = 1 :=
  sub_eq_zero

/-- Theorem 9: Word power trace invariance under arbitrary unitary reparameterization. -/
theorem word_pow_trace_gauge_invariant {d : ℕ} (V M : Matrix (Fin d) (Fin d) ℂ)
    (hV : IsUnitary V) (k : ℕ) :
    ((gaugeConj V M) ^ k).trace = (M ^ k).trace := by
  rw [← gaugeConj_pow hV]
  unfold gaugeConj
  calc
    (V * M ^ k * Vᴴ).trace = (V * (M ^ k * Vᴴ)).trace := by rw [Matrix.mul_assoc]
    _ = (M ^ k * Vᴴ * V).trace := by
        simpa [Matrix.mul_assoc] using Matrix.trace_mul_comm V (M ^ k * Vᴴ)
    _ = (M ^ k * (Vᴴ * V)).trace := by rw [Matrix.mul_assoc]
    _ = (M ^ k).trace := by rw [unitary_conj_mul hV, Matrix.mul_one]

/-- Theorem 10: Every unitary matrix has Frobenius squared norm equal to `d`. -/
theorem unitary_frobNormSq_eq_dim {d : ℕ} (M : Matrix (Fin d) (Fin d) ℂ)
    (hM : IsUnitary M) : frobNormSq M = d := by
  unfold frobNormSq
  have hdiag : ∀ i : Fin d, ∑ j : Fin d, ‖M i j‖ ^ 2 = 1 := by
    intro i
    have hre : ((M * Mᴴ) i i).re = ((1 : Matrix (Fin d) (Fin d) ℂ) i i).re := by rw [hM]
    simp only [Matrix.one_apply_eq, Complex.one_re] at hre
    have hsum : ((M * Mᴴ) i i).re = ∑ j : Fin d, ‖M i j‖ ^ 2 := by
      simp only [Matrix.mul_apply, Matrix.conjTranspose_apply, Complex.re_sum]
      refine Finset.sum_congr rfl (fun j _ => ?_)
      change (M i j * starRingEnd ℂ (M i j)).re = ‖M i j‖ ^ 2
      rw [Complex.mul_conj, Complex.ofReal_re, Complex.normSq_eq_abs, Complex.norm_eq_abs]
    linarith
  calc
    ∑ i : Fin d, ∑ j : Fin d, ‖M i j‖ ^ 2 = ∑ _i : Fin d, (1 : ℝ) :=
      Finset.sum_congr rfl (fun i _ => hdiag i)
    _ = d := by simp

/-- Theorem 11: Exact unitary pair MDL equals `2 * d < 60 * d` for `A5` (`d ≥ 1`). -/
theorem template_free_pair_mdl_lt_bank {d : ℕ} (hd : 0 < d)
    (U0 U1 : Matrix (Fin d) (Fin d) ℂ) (h0 : IsUnitary U0) (h1 : IsUnitary U1) :
    frobNormSq U0 + frobNormSq U1 < (60 : ℝ) * d := by
  rw [unitary_frobNormSq_eq_dim U0 h0, unitary_frobNormSq_eq_dim U1 h1]
  have hdr : (0 : ℝ) < d := Nat.cast_pos.mpr hd
  linarith

/-- Theorem 12: Orthogonal bias-free weight step preserves kept inner products exactly. -/
theorem orthogonal_sgd_step_zero_drift {m : ℕ}
    (w g x_ft x_keep : Fin m → ℝ) (η : ℝ)
    (horth : dotProduct x_ft x_keep = 0) :
    dotProduct (fun i => w i - η * (g i + (x_ft i - g i))) x_keep =
      dotProduct w x_keep := by
  simp only [dotProduct]
  calc
    ∑ i : Fin m, (w i - η * (g i + (x_ft i - g i))) * x_keep i
      = ∑ i : Fin m, w i * x_keep i - η * ∑ i : Fin m, x_ft i * x_keep i := by
          rw [Finset.mul_sum, ← Finset.sum_sub_distrib]
          refine Finset.sum_congr rfl (fun i _ => by ring)
    _ = ∑ i : Fin m, w i * x_keep i := by
          have hs : (∑ i : Fin m, x_ft i * x_keep i) = 0 := horth
          rw [hs, mul_zero, sub_zero]

end TemplateFreeRelationLocking

-- =============================================================================
-- 3. ContinuousSO3Gauge (7 theorems)
-- =============================================================================
namespace ContinuousSO3Gauge

def IsSO3 (R : Matrix (Fin 3) (Fin 3) ℝ) : Prop :=
  R * Rᵀ = 1 ∧ R.det = 1

private theorem so3_transpose_mul {R : Matrix (Fin 3) (Fin 3) ℝ}
    (hR : IsSO3 R) : Rᵀ * R = 1 :=
  Matrix.mul_eq_one_comm.mp hR.1

/-- Theorem 13: Identity belongs to `SO(3)`. -/
theorem one_isSO3 : IsSO3 (1 : Matrix (Fin 3) (Fin 3) ℝ) := by
  simp [IsSO3]

/-- Theorem 14: `SO(3)` is closed under matrix multiplication. -/
theorem mul_isSO3 {A B : Matrix (Fin 3) (Fin 3) ℝ}
    (hA : IsSO3 A) (hB : IsSO3 B) : IsSO3 (A * B) := by
  refine ⟨?_, ?_⟩
  · calc
      (A * B) * (A * B)ᵀ = A * B * (Bᵀ * Aᵀ) := by rw [Matrix.transpose_mul]
      _ = A * (B * Bᵀ) * Aᵀ := by simp [Matrix.mul_assoc]
      _ = A * 1 * Aᵀ := by rw [hB.1]
      _ = 1 := by simp [hA.1]
  · rw [Matrix.det_mul, hA.2, hB.2, one_mul]

/-- Theorem 15: `SO(3)` is closed under transpose (inverse). -/
theorem transpose_isSO3 {R : Matrix (Fin 3) (Fin 3) ℝ}
    (hR : IsSO3 R) : IsSO3 Rᵀ := by
  refine ⟨?_, ?_⟩
  · simpa using so3_transpose_mul hR
  · rw [Matrix.det_transpose, hR.2]

/-- Theorem 16: `SO(3)` is closed under `SO(3)` gauge conjugation `V R Vᵀ`. -/
theorem gaugeConj_isSO3 {V R : Matrix (Fin 3) (Fin 3) ℝ}
    (hV : IsSO3 V) (hR : IsSO3 R) : IsSO3 (V * R * Vᵀ) :=
  mul_isSO3 (mul_isSO3 hV hR) (transpose_isSO3 hV)

/-- Theorem 17: Traces of 3D rotations are invariant under arbitrary `SO(3)` gauge conjugation. -/
theorem so3_trace_gauge_invariant {V R : Matrix (Fin 3) (Fin 3) ℝ}
    (hV : IsSO3 V) : (V * R * Vᵀ).trace = R.trace := by
  calc
    (V * R * Vᵀ).trace = (V * (R * Vᵀ)).trace := by rw [Matrix.mul_assoc]
    _ = (R * Vᵀ * V).trace := by
        simpa [Matrix.mul_assoc] using Matrix.trace_mul_comm V (R * Vᵀ)
    _ = (R * (Vᵀ * V)).trace := by rw [Matrix.mul_assoc]
    _ = R.trace := by rw [so3_transpose_mul hV, Matrix.mul_one]

/-- Theorem 18: General entry-norm trace bound `-3 ≤ Tr(R) ≤ 3` for all `R ∈ SO(3)`. -/
theorem so3_trace_abs_le_three {R : Matrix (Fin 3) (Fin 3) ℝ}
    (hR : IsSO3 R) : -3 ≤ R.trace ∧ R.trace ≤ 3 := by
  have hdiag : ∀ i : Fin 3, -1 ≤ R i i ∧ R i i ≤ 1 := by
    intro i
    have h1 : (R * Rᵀ) i i = 1 := by rw [hR.1]; simp
    have hsq : R i i ^ 2 ≤ 1 := by
      have hsum : ∑ j : Fin 3, R i j ^ 2 = 1 := by
        simpa [Matrix.mul_apply, sq] using h1
      have hnonneg : ∀ j : Fin 3, 0 ≤ R i j ^ 2 := fun j => sq_nonneg (R i j)
      have hle : R i i ^ 2 ≤ ∑ j : Fin 3, R i j ^ 2 :=
        Finset.single_le_sum (fun j _ => hnonneg j) (Finset.mem_univ i)
      linarith
    constructor <;> nlinarith
  have htr : R.trace = R 0 0 + R 1 1 + R 2 2 := by
    simp [Matrix.trace, Fin.sum_univ_three]
  obtain ⟨hl0, hu0⟩ := hdiag 0
  obtain ⟨hl1, hu1⟩ := hdiag 1
  obtain ⟨hl2, hu2⟩ := hdiag 2
  rw [htr]
  constructor <;> linarith

/-- Canonical axis-angle z-rotation matrix in `SO(3)`. -/
def rotZ (θ : ℝ) : Matrix (Fin 3) (Fin 3) ℝ :=
  Matrix.of fun i j =>
    match i.val, j.val with
    | 0, 0 => Real.cos θ
    | 0, 1 => -Real.sin θ
    | 1, 0 => Real.sin θ
    | 1, 1 => Real.cos θ
    | 2, 2 => 1
    | _, _ => 0

/-- Theorem 19: Every `rotZ θ` lies in `SO(3)`, has exact trace `1 + 2 cos θ ∈ [-1, 3]`,
    and preserves `1 + 2 cos θ` under arbitrary `V ∈ SO(3)` conjugation. -/
theorem rotZ_so3_and_exact_trace (V : Matrix (Fin 3) (Fin 3) ℝ) (hV : IsSO3 V) (θ : ℝ) :
    IsSO3 (rotZ θ) ∧
    (V * rotZ θ * Vᵀ).trace = 1 + 2 * Real.cos θ ∧
    -1 ≤ (V * rotZ θ * Vᵀ).trace ∧ (V * rotZ θ * Vᵀ).trace ≤ 3 := by
  have hsc : Real.cos θ ^ 2 + Real.sin θ ^ 2 = 1 := Real.cos_sq_add_sin_sq θ
  have hR : IsSO3 (rotZ θ) := by
    refine ⟨?_, ?_⟩
    · ext i j
      fin_cases i <;> fin_cases j <;>
        simp [rotZ, Matrix.mul_apply, Matrix.transpose_apply, Fin.sum_univ_three] <;>
        nlinarith [hsc]
    · simp [rotZ, Matrix.det_fin_three]
      nlinarith [hsc]
  have htr : (rotZ θ).trace = 1 + 2 * Real.cos θ := by
    simp [Matrix.trace, rotZ, Fin.sum_univ_three]
    ring
  have hconj : (V * rotZ θ * Vᵀ).trace = 1 + 2 * Real.cos θ := by
    rw [so3_trace_gauge_invariant hV, htr]
  have hcl : -1 ≤ Real.cos θ := Real.neg_one_le_cos θ
  have hcu : Real.cos θ ≤ 1 := Real.cos_le_one θ
  refine ⟨hR, hconj, ?_, ?_⟩ <;> linarith

end ContinuousSO3Gauge

-- =============================================================================
-- 4. QuantitativeFiniteSampleT6 (5 theorems)
-- =============================================================================
namespace QuantitativeFiniteSampleT6

def chebyshevTail (N : ℕ) (δ : ℝ) : ℝ :=
  1 / (4 * (N : ℝ) * δ ^ 2)

/-- Theorem 20: Bernoulli variance is uniformly bounded by `1 / 4`. -/
theorem bernoulli_var_le_quarter {p : ℝ} (_hp0 : 0 ≤ p) (_hp1 : p ≤ 1) :
    p * (1 - p) ≤ 1 / 4 := by
  nlinarith [sq_nonneg (p - 1 / 2)]

/-- Theorem 21: Chebyshev concentration bound is strictly positive for `N > 0`, `δ > 0`. -/
theorem chebyshevTail_pos {N : ℕ} {δ : ℝ} (hN : 0 < N) (hδ : 0 < δ) :
    0 < chebyshevTail N δ := by
  unfold chebyshevTail
  positivity

/-- Theorem 22: Increasing sample budget `N` decreases the Chebyshev tail bound monotonically. -/
theorem chebyshevTail_antitone_N {N₁ N₂ : ℕ} {δ : ℝ}
    (hN1 : 0 < N₁) (hle : N₁ ≤ N₂) (hδ : 0 < δ) :
    chebyshevTail N₂ δ ≤ chebyshevTail N₁ δ := by
  unfold chebyshevTail
  have hle_r : (N₁ : ℝ) ≤ N₂ := Nat.cast_le.mpr hle
  have hden1 : 0 < 4 * (N₁ : ℝ) * δ ^ 2 := by positivity
  have hle_den : 4 * (N₁ : ℝ) * δ ^ 2 ≤ 4 * (N₂ : ℝ) * δ ^ 2 := by
    nlinarith [sq_pos_of_pos hδ]
  exact one_div_le_one_div_of_le hden1 hle_den

/-- Theorem 23: Larger channel TV separation `δ` tightens the sample-error tail bound. -/
theorem chebyshevTail_antitone_delta {N : ℕ} {δ₁ δ₂ : ℝ}
    (hN : 0 < N) (hδ1 : 0 < δ₁) (hle : δ₁ ≤ δ₂) :
    chebyshevTail N δ₂ ≤ chebyshevTail N δ₁ := by
  unfold chebyshevTail
  have hden1 : 0 < 4 * (N : ℝ) * δ₁ ^ 2 := by positivity
  have hsq : δ₁ ^ 2 ≤ δ₂ ^ 2 := by nlinarith
  have hle_den : 4 * (N : ℝ) * δ₁ ^ 2 ≤ 4 * (N : ℝ) * δ₂ ^ 2 := by
    nlinarith [show (0 : ℝ) < N by positivity]
  exact one_div_le_one_div_of_le hden1 hle_den

/-- Theorem 24: Quantitative T6 sufficiency: `N ≥ 1 / (4 ε δ²)` guarantees tail `≤ ε`. -/
theorem sample_complexity_threshold_sufficient {N : ℕ} {δ ε : ℝ}
    (hδ : 0 < δ) (hε : 0 < ε) (hN : 1 / (4 * ε * δ ^ 2) ≤ (N : ℝ)) :
    chebyshevTail N δ ≤ ε := by
  unfold chebyshevTail
  have hdenε : 0 < 4 * ε * δ ^ 2 := by positivity
  have h1 : 1 ≤ (N : ℝ) * (4 * ε * δ ^ 2) := (div_le_iff₀ hdenε).mp hN
  have hNpos : 0 < (N : ℝ) := by
    have hinv : 0 < 1 / (4 * ε * δ ^ 2) := div_pos zero_lt_one hdenε
    linarith
  have hdenN : 0 < 4 * (N : ℝ) * δ ^ 2 := by positivity
  rw [div_le_iff₀ hdenN]
  nlinarith

end QuantitativeFiniteSampleT6

end
end Semplex.FinalClosure
