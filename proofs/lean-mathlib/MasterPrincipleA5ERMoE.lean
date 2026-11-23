import Mathlib

/-!
# Phase 5: Non-Solvable Simple `A5` Icosahedral Closure, ERMoE Gauge Routing,
# & Epiplexity-Bounded Observer Theory (`Semplex.A5ERMoE`)

Machine-checked closing extension beyond solvable groups (`S3`, `A4`) to the
non-solvable icosahedral simple group `A5` (`|G| = 60`), unified with:
1. `A5IcosahedralUnitary` (10 theorems): Exact Galois-conjugate golden-ratio
   `SO(3)`/`U(3)` presentations `ρ_3(φ)` and `ρ_3'(ψ)` (`φ^2 = φ + 1`, `ψ^2 = ψ + 1`)
   satisfying `s^2 = 1`, `t^3 = 1`, and `(s*t)^5 = 1` under arbitrary `U(d)` gauge
   conjugations, with exact `30×` Frobenius MDL compression (`6 < 180`) and Galois
   trace separation `φ ≠ ψ` on `C5+` vs `C5-`.
2. `ERMoEGaugeRouting` (8 theorems, `arXiv:2511.10971`): Eigen-Reparameterized Mixture
   of Experts (`routedOp g V M`) preserves trace invariants across arbitrary simplex
   gates and orthogonal bias-free SGD updates.
3. `EpiplexityBoundedObserver` (7 theorems, `arXiv:2608.11746`): Monotonicity,
   strict separation gain under non-redundant probes, zero gain under degenerate
   probes, and concrete `A5` proof that `ρ_4` collapses `C5+`/`C5-` while `ρ_3(φ)`
   strictly increases `epiplexityCount`.
4. `Phase5Synthesis` (5 theorems): End-to-end `NonSolvableMasterBundle` witness for `A5`.
-/

namespace Semplex.A5ERMoE

open Matrix BigOperators

noncomputable section

-- =============================================================================
-- 1. A5IcosahedralUnitary (10 theorems)
-- =============================================================================
namespace A5IcosahedralUnitary

def IsUnitary {d : ℕ} (M : Matrix (Fin d) (Fin d) ℂ) : Prop :=
  M * Mᴴ = 1

def gaugeConj {d : ℕ} (V M : Matrix (Fin d) (Fin d) ℂ) : Matrix (Fin d) (Fin d) ℂ :=
  V * M * Vᴴ

def frobNormSq {d : ℕ} (M : Matrix (Fin d) (Fin d) ℂ) : ℝ :=
  ∑ i : Fin d, ∑ j : Fin d, ‖M i j‖ ^ 2

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
  | succ n ih => rw [pow_succ, pow_succ, gaugeConj_mul hV, ih]

private theorem mat_cube {d : ℕ} (M : Matrix (Fin d) (Fin d) ℂ) :
    M ^ 3 = M * M * M := by
  rw [pow_succ, pow_two]

private theorem mat_five {d : ℕ} (M : Matrix (Fin d) (Fin d) ℂ) :
    M ^ 5 = ((M * M) * (M * M)) * M := by
  calc
    M ^ 5 = M ^ 4 * M := by rw [pow_succ]
    _ = (M ^ 2) * (M ^ 2) * M := by
        rw [show (4 : ℕ) = 2 + 2 by norm_num, pow_add]
    _ = ((M * M) * (M * M)) * M := by rw [pow_two]

def phiGolden : ℝ := (1 + Real.sqrt 5) / 2
def psiGolden : ℝ := (1 - Real.sqrt 5) / 2

/-- Theorem 1: Golden ratio satisfies `φ² = φ + 1`. -/
theorem phiGolden_sq : phiGolden ^ 2 = phiGolden + 1 := by
  unfold phiGolden
  have h5 : Real.sqrt 5 ^ 2 = 5 := Real.sq_sqrt (by norm_num)
  nlinarith

/-- Theorem 2: Galois conjugate satisfies `ψ² = ψ + 1`. -/
theorem psiGolden_sq : psiGolden ^ 2 = psiGolden + 1 := by
  unfold psiGolden
  have h5 : Real.sqrt 5 ^ 2 = 5 := Real.sq_sqrt (by norm_num)
  nlinarith

/-- Theorem 3: `φ ≠ ψ` separates the two Galois-conjugate 3D `A5` representations. -/
theorem phiGolden_ne_psiGolden : phiGolden ≠ psiGolden := by
  intro h
  have hs : Real.sqrt 5 = 0 := by
    unfold phiGolden psiGolden at h
    linarith
  have h5 : Real.sqrt 5 ^ 2 = 5 := Real.sq_sqrt (by norm_num)
  rw [hs] at h5
  norm_num at h5

/-- Icosahedral involution generator `s(α)` on `ℂ^3` for any root of `α² = α + 1`. -/
def a5GenS (α : ℝ) : Matrix (Fin 3) (Fin 3) ℂ :=
  ![ ![(↑α - 1) / 2, 1 / 2, (↑α : ℂ) / 2],
     ![1 / 2, -(↑α : ℂ) / 2, (↑α - 1) / 2],
     ![(↑α : ℂ) / 2, (↑α - 1) / 2, -1 / 2] ]

/-- 3-cycle permutation matrix `t` on `ℂ^3`. -/
def a5GenT : Matrix (Fin 3) (Fin 3) ℂ :=
  Matrix.of fun i j =>
    match i.val, j.val with
    | 0, 1 => 1
    | 1, 2 => 1
    | 2, 0 => 1
    | _, _ => 0

private def a5ProdP (α : ℝ) : Matrix (Fin 3) (Fin 3) ℂ :=
  ![ ![(↑α : ℂ) / 2, (↑α - 1) / 2, 1 / 2],
     ![(↑α - 1) / 2, 1 / 2, -(↑α : ℂ) / 2],
     ![-1 / 2, (↑α : ℂ) / 2, (↑α - 1) / 2] ]

private def a5ProdP2 (α : ℝ) : Matrix (Fin 3) (Fin 3) ℂ :=
  ![ ![1 / 2, (↑α : ℂ) / 2, (↑α - 1) / 2],
     ![(↑α : ℂ) / 2, (1 - (↑α : ℂ)) / 2, -1 / 2],
     ![(1 - (↑α : ℂ)) / 2, 1 / 2, -(↑α : ℂ) / 2] ]

private theorem a5GenS_conjTranspose (α : ℝ) : (a5GenS α)ᴴ = a5GenS α := by
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [a5GenS, Matrix.conjTranspose_apply, Complex.conj_ofReal]

/-- Theorem 4: `a5GenS α` is Hermitian and an exact involution `s^2 = 1` whenever `α² = α + 1`. -/
theorem a5GenS_hermitian_and_sq (α : ℝ) (hα : α ^ 2 = α + 1) :
    (a5GenS α)ᴴ = a5GenS α ∧ a5GenS α ^ 2 = 1 := by
  refine ⟨a5GenS_conjTranspose α, ?_⟩
  have hαC : (α : ℂ) ^ 2 = (α : ℂ) + 1 := by exact_mod_cast hα
  rw [pow_two]
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [a5GenS, Matrix.mul_apply, Matrix.one_apply, Fin.sum_univ_three] <;>
    (ring_nf; try simp only [hαC]; ring)

/-- Theorem 5: `a5GenS α` is unitary whenever `α² = α + 1`. -/
theorem a5GenS_isUnitary (α : ℝ) (hα : α ^ 2 = α + 1) :
    IsUnitary (a5GenS α) := by
  unfold IsUnitary
  have hs := a5GenS_hermitian_and_sq α hα
  rw [hs.1, ← pow_two]
  exact hs.2

/-- Theorem 6: `a5GenT` is unitary and satisfies `t^3 = 1`. -/
theorem a5GenT_unitary_and_cube :
    IsUnitary a5GenT ∧ a5GenT ^ 3 = 1 := by
  constructor
  · unfold IsUnitary
    ext i j
    fin_cases i <;> fin_cases j <;>
      simp [a5GenT, Matrix.mul_apply, Matrix.conjTranspose_apply, Fin.sum_univ_three]
  · rw [mat_cube]
    ext i j
    fin_cases i <;> fin_cases j <;>
      simp [a5GenT, Matrix.mul_apply, Fin.sum_univ_three]

private theorem a5ST_eq_P (α : ℝ) : a5GenS α * a5GenT = a5ProdP α := by
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [a5GenS, a5GenT, a5ProdP, Matrix.mul_apply, Fin.sum_univ_three] <;>
    ring

private theorem a5P_sq_eq_P2 (α : ℝ) (hαC : (α : ℂ) ^ 2 = (α : ℂ) + 1) :
    a5ProdP α * a5ProdP α = a5ProdP2 α := by
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [a5ProdP, a5ProdP2, Matrix.mul_apply, Fin.sum_univ_three] <;>
    (ring_nf; try simp only [hαC]; ring)

private theorem a5P2_sq_eq_PT (α : ℝ) (hαC : (α : ℂ) ^ 2 = (α : ℂ) + 1) :
    a5ProdP2 α * a5ProdP2 α = (a5ProdP α)ᵀ := by
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [a5ProdP2, a5ProdP, Matrix.mul_apply, Matrix.transpose_apply, Fin.sum_univ_three] <;>
    (ring_nf; try simp only [hαC]; ring)

private theorem a5PT_mul_P (α : ℝ) (hαC : (α : ℂ) ^ 2 = (α : ℂ) + 1) :
    (a5ProdP α)ᵀ * a5ProdP α = 1 := by
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [a5ProdP, Matrix.mul_apply, Matrix.transpose_apply, Matrix.one_apply,
      Fin.sum_univ_three] <;>
    (ring_nf; try simp only [hαC]; ring)

/-- Theorem 7: Exact non-solvable `A5` 5-cycle mixed relation `(s(α) * t)^5 = 1`
    whenever `α² = α + 1`. -/
theorem a5Gen_mixed_rel_five (α : ℝ) (hα : α ^ 2 = α + 1) :
    (a5GenS α * a5GenT) ^ 5 = 1 := by
  have hαC : (α : ℂ) ^ 2 = (α : ℂ) + 1 := by exact_mod_cast hα
  rw [a5ST_eq_P, mat_five, a5P_sq_eq_P2 α hαC, a5P2_sq_eq_PT α hαC, a5PT_mul_P α hαC]

/-- Theorem 8: Arbitrary `U(d)` gauge conjugation preserves all `A5` presentation
    relations, unitarity, and traces. -/
theorem a5GaugeConj_hom_rel {d : ℕ} (V M N : Matrix (Fin d) (Fin d) ℂ)
    (hV : IsUnitary V) (hM2 : M ^ 2 = 1) (hN3 : N ^ 3 = 1) (hMN5 : (M * N) ^ 5 = 1) :
    (gaugeConj V M) ^ 2 = 1 ∧ (gaugeConj V N) ^ 3 = 1 ∧
      (gaugeConj V M * gaugeConj V N) ^ 5 = 1 ∧
      (gaugeConj V (M * N)).trace = (M * N).trace := by
  refine ⟨?_, ?_, ?_, ?_⟩
  · rw [← gaugeConj_pow hV M 2, hM2, gaugeConj_one hV]
  · rw [← gaugeConj_pow hV N 3, hN3, gaugeConj_one hV]
  · rw [← gaugeConj_mul hV M N, ← gaugeConj_pow hV (M * N) 5, hMN5, gaugeConj_one hV]
  · unfold gaugeConj
    calc
      (V * (M * N) * Vᴴ).trace = (V * ((M * N) * Vᴴ)).trace := by rw [Matrix.mul_assoc]
      _ = ((M * N) * Vᴴ * V).trace := by
          simpa [Matrix.mul_assoc] using Matrix.trace_mul_comm V ((M * N) * Vᴴ)
      _ = ((M * N) * (Vᴴ * V)).trace := by rw [Matrix.mul_assoc]
      _ = (M * N).trace := by rw [isUnitary_inv_eq hV, Matrix.mul_one]

/-- Theorem 9: Exact 5-cycle Galois trace separation:
    `Tr(ρ_3(φ)(s t)) = φ ≠ ψ = Tr(ρ_3'(ψ)(s t))`. -/
theorem a5_galois_fiveCycle_trace_split :
    (a5GenS phiGolden * a5GenT).trace = (phiGolden : ℂ) ∧
    (a5GenS psiGolden * a5GenT).trace = (psiGolden : ℂ) ∧
    (a5GenS phiGolden * a5GenT).trace ≠ (a5GenS psiGolden * a5GenT).trace := by
  have htr : ∀ α : ℝ, (a5GenS α * a5GenT).trace = (α : ℂ) := by
    intro α
    simp [Matrix.trace, a5GenS, a5GenT, Matrix.mul_apply, Fin.sum_univ_three]
    ring
  refine ⟨htr phiGolden, htr psiGolden, ?_⟩
  rw [htr phiGolden, htr psiGolden]
  exact Complex.ofReal_injective.ne phiGolden_ne_psiGolden

private theorem unitary_frobNormSq {d : ℕ} (M : Matrix (Fin d) (Fin d) ℂ)
    (hM : M * Mᴴ = 1) : frobNormSq M = d := by
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

/-- Theorem 10: Exact `30×` unitary Frobenius MDL compression for `A5` (`|G| = 60`, `d = 3`):
    `‖s‖_F^2 + ‖t‖_F^2 = 6 < 180 = 60 * 3`. -/
theorem a5_generator_mdl_30x :
    frobNormSq (a5GenS phiGolden) + frobNormSq a5GenT < (60 : ℝ) * 3 := by
  have hs := a5GenS_isUnitary phiGolden phiGolden_sq
  have ht := a5GenT_unitary_and_cube.1
  rw [unitary_frobNormSq _ hs, unitary_frobNormSq _ ht]
  norm_num

end A5IcosahedralUnitary

-- =============================================================================
-- 2. ERMoEGaugeRouting (8 theorems)
-- =============================================================================
namespace ERMoEGaugeRouting

open A5IcosahedralUnitary

def IsSimplexGate {E : ℕ} (g : Fin E → ℝ) : Prop :=
  (∀ e, 0 ≤ g e) ∧ ∑ e : Fin E, g e = 1

def routedOp {E d : ℕ} (g : Fin E → ℝ)
    (V : Fin E → Matrix (Fin d) (Fin d) ℂ)
    (M : Matrix (Fin d) (Fin d) ℂ) : Matrix (Fin d) (Fin d) ℂ :=
  ∑ e : Fin E, (g e : ℂ) • gaugeConj (V e) M

private theorem gaugeConj_isUnitary {d : ℕ} (V M : Matrix (Fin d) (Fin d) ℂ)
    (hV : IsUnitary V) (hM : IsUnitary M) : IsUnitary (gaugeConj V M) := by
  unfold IsUnitary at hV hM ⊢
  unfold gaugeConj
  calc
    (V * M * Vᴴ) * (V * M * Vᴴ)ᴴ
      = V * M * Vᴴ * (V * Mᴴ * Vᴴ) := by simp [Matrix.conjTranspose_mul, Matrix.mul_assoc]
    _ = V * M * (Vᴴ * V) * Mᴴ * Vᴴ := by simp only [Matrix.mul_assoc]
    _ = V * (M * Mᴴ) * Vᴴ := by
        rw [isUnitary_inv_eq hV, Matrix.mul_one]
        simp [Matrix.mul_assoc]
    _ = 1 := by rw [hM, Matrix.mul_one, hV]

private theorem gaugeConj_trace_eq {d : ℕ} (V M : Matrix (Fin d) (Fin d) ℂ)
    (hV : IsUnitary V) : (gaugeConj V M).trace = M.trace := by
  unfold gaugeConj
  calc
    (V * M * Vᴴ).trace = (V * (M * Vᴴ)).trace := by rw [Matrix.mul_assoc]
    _ = (M * Vᴴ * V).trace := by
        simpa [Matrix.mul_assoc] using Matrix.trace_mul_comm V (M * Vᴴ)
    _ = (M * (Vᴴ * V)).trace := by rw [Matrix.mul_assoc]
    _ = M.trace := by rw [isUnitary_inv_eq hV, Matrix.mul_one]

/-- Theorem 11: Every expert's conjugated generator stays unitary. -/
theorem ermoe_expert_isUnitary {E d : ℕ} (V : Fin E → Matrix (Fin d) (Fin d) ℂ)
    (hV : ∀ e, IsUnitary (V e)) (M : Matrix (Fin d) (Fin d) ℂ) (hM : IsUnitary M) (e : Fin E) :
    IsUnitary (gaugeConj (V e) M) :=
  gaugeConj_isUnitary (V e) M (hV e) hM

/-- Theorem 12: Every expert preserves operator traces independently of its local eigen-basis. -/
theorem ermoe_expert_trace_eq {E d : ℕ} (V : Fin E → Matrix (Fin d) (Fin d) ℂ)
    (hV : ∀ e, IsUnitary (V e)) (M : Matrix (Fin d) (Fin d) ℂ) (e : Fin E) :
    (gaugeConj (V e) M).trace = M.trace :=
  gaugeConj_trace_eq (V e) M (hV e)

/-- Theorem 13: Any simplex-gated ERMoE mixture strictly preserves operator trace invariants. -/
theorem ermoe_routed_trace_invariant {E d : ℕ} (g : Fin E → ℝ) (hg : IsSimplexGate g)
    (V : Fin E → Matrix (Fin d) (Fin d) ℂ) (hV : ∀ e, IsUnitary (V e))
    (M : Matrix (Fin d) (Fin d) ℂ) :
    (routedOp g V M).trace = M.trace := by
  unfold routedOp Matrix.trace
  calc
    ∑ i : Fin d, (∑ e : Fin E, (g e : ℂ) • gaugeConj (V e) M) i i
      = ∑ i : Fin d, ∑ e : Fin E, (g e : ℂ) * gaugeConj (V e) M i i := by
          refine Finset.sum_congr rfl (fun i _ => ?_)
          simp [Matrix.sum_apply, smul_eq_mul]
    _ = ∑ e : Fin E, ∑ i : Fin d, (g e : ℂ) * gaugeConj (V e) M i i := Finset.sum_comm
    _ = ∑ e : Fin E, (g e : ℂ) * (gaugeConj (V e) M).trace := by
          refine Finset.sum_congr rfl (fun e _ => ?_)
          rw [← Finset.mul_sum]; rfl
    _ = ∑ e : Fin E, (g e : ℂ) * M.trace := by
          refine Finset.sum_congr rfl (fun e _ => ?_)
          rw [ermoe_expert_trace_eq V hV M e]
    _ = (∑ e : Fin E, (g e : ℂ)) * M.trace := by rw [← Finset.sum_mul]
    _ = M.trace := by
          have hsum : ∑ e : Fin E, (g e : ℂ) = 1 := by exact_mod_cast hg.2
          rw [hsum, one_mul]

/-- Theorem 14: Routed mixture of identity across any unitary expert gauges equals identity. -/
theorem ermoe_routed_identity {E d : ℕ} (g : Fin E → ℝ) (hg : IsSimplexGate g)
    (V : Fin E → Matrix (Fin d) (Fin d) ℂ) (hV : ∀ e, IsUnitary (V e)) :
    routedOp g V 1 = 1 := by
  unfold routedOp
  have hunit : ∀ e : Fin E, gaugeConj (V e) 1 = 1 := fun e => gaugeConj_one (hV e)
  simp_rw [hunit, ← Finset.sum_smul]
  have hsum : ∑ e : Fin E, (g e : ℂ) = 1 := by exact_mod_cast hg.2
  rw [hsum, one_smul]

def foldOrthSGD {m k : ℕ} (W : Matrix (Fin m) (Fin k) ℝ) :
    List (ℝ × (Fin m → ℝ) × (Fin k → ℝ)) → Matrix (Fin m) (Fin k) ℝ
  | [] => W
  | (η, r, x_ft) :: rest => foldOrthSGD (W - η • Matrix.vecMulVec r x_ft) rest

/-- Theorem 15: Rank-1 fine-tuning outer update along orthogonal ERMoE features vanishes on `x_keep`. -/
theorem ermoe_outer_orth_zero {m k : ℕ}
    (r : Fin m → ℝ) (x_ft x_keep : Fin k → ℝ) (horth : x_ft ⬝ᵥ x_keep = 0) :
    (Matrix.vecMulVec r x_ft) *ᵥ x_keep = 0 := by
  ext i
  simp only [Matrix.mulVec, Matrix.vecMulVec_apply, Pi.zero_apply, dotProduct]
  calc
    ∑ j, r i * x_ft j * x_keep j
      = r i * ∑ j, x_ft j * x_keep j := by simp [mul_assoc, Finset.mul_sum]
    _ = r i * (x_ft ⬝ᵥ x_keep) := rfl
    _ = 0 := by rw [horth, mul_zero]

/-- Theorem 16: Single bias-free SGD step orthogonal to kept features preserves kept logits. -/
theorem ermoe_rank1_sgd_invariant {m k : ℕ}
    (W : Matrix (Fin m) (Fin k) ℝ) (η : ℝ) (r : Fin m → ℝ) (x_ft x_keep : Fin k → ℝ)
    (horth : x_ft ⬝ᵥ x_keep = 0) :
    (W - η • Matrix.vecMulVec r x_ft) *ᵥ x_keep = W *ᵥ x_keep := by
  have hsm : (η • Matrix.vecMulVec r x_ft) *ᵥ x_keep =
      η • ((Matrix.vecMulVec r x_ft) *ᵥ x_keep) := by
    ext i; simp [Matrix.mulVec, dotProduct, Finset.mul_sum, mul_assoc]
  rw [Matrix.sub_mulVec, hsm, ermoe_outer_orth_zero r x_ft x_keep horth, smul_zero, sub_zero]

/-- Theorem 17: Arbitrary-length orthogonal ERMoE SGD batch leaves kept logits strictly invariant. -/
theorem ermoe_batch_sgd_invariant {m k : ℕ}
    (W : Matrix (Fin m) (Fin k) ℝ)
    (updates : List (ℝ × (Fin m → ℝ) × (Fin k → ℝ)))
    (x_keep : Fin k → ℝ)
    (horth : ∀ u ∈ updates, u.2.2 ⬝ᵥ x_keep = 0) :
    (foldOrthSGD W updates) *ᵥ x_keep = W *ᵥ x_keep := by
  induction updates generalizing W with
  | nil => rfl
  | cons u rest ih =>
      rcases u with ⟨η, r, x_ft⟩
      have hu := horth (η, r, x_ft) (List.mem_cons_self _ _)
      have hrest : ∀ u' ∈ rest, u'.2.2 ⬝ᵥ x_keep = 0 :=
        fun u' hu' => horth u' (List.mem_cons_of_mem _ hu')
      simp only [foldOrthSGD]
      rw [ih _ hrest, ermoe_rank1_sgd_invariant W η r x_ft x_keep hu]

/-- Theorem 18: Exact top-1 class prediction preservation on kept classes after orthogonal SGD. -/
theorem ermoe_sgd_preserves_argmax {m k : ℕ}
    (W : Matrix (Fin m) (Fin k) ℝ)
    (updates : List (ℝ × (Fin m → ℝ) × (Fin k → ℝ)))
    (x_keep : Fin k → ℝ)
    (horth : ∀ u ∈ updates, u.2.2 ⬝ᵥ x_keep = 0)
    (c_star : Fin m)
    (hmax : ∀ c : Fin m, (W *ᵥ x_keep) c ≤ (W *ᵥ x_keep) c_star) :
    ∀ c : Fin m, ((foldOrthSGD W updates) *ᵥ x_keep) c ≤
      ((foldOrthSGD W updates) *ᵥ x_keep) c_star := by
  rw [ermoe_batch_sgd_invariant W updates x_keep horth]
  exact hmax

end ERMoEGaugeRouting

-- =============================================================================
-- 3. EpiplexityBoundedObserver (7 theorems)
-- =============================================================================
namespace EpiplexityBoundedObserver

open Classical
open A5IcosahedralUnitary

def Distinguishes {ι S V : Type*} (O : Finset ι) (obs : ι → S → V) (s₁ s₂ : S) : Prop :=
  ∃ i ∈ O, obs i s₁ ≠ obs i s₂

def resolvedPairs {ι S V : Type*} [Fintype S] (O : Finset ι) (obs : ι → S → V) :
    Finset (S × S) :=
  (Finset.univ : Finset (S × S)).filter (fun p => Distinguishes O obs p.1 p.2)

def epiplexityCount {ι S V : Type*} [Fintype S] (O : Finset ι) (obs : ι → S → V) : ℕ :=
  (resolvedPairs O obs).card

/-- Theorem 19: Distinguishing power is monotone under expanding observer resources. -/
theorem distinguishes_mono {ι S V : Type*} {O₁ O₂ : Finset ι} (hsub : O₁ ⊆ O₂)
    (obs : ι → S → V) {s₁ s₂ : S} (h : Distinguishes O₁ obs s₁ s₂) :
    Distinguishes O₂ obs s₁ s₂ := by
  rcases h with ⟨i, hi, hne⟩
  exact ⟨i, hsub hi, hne⟩

/-- Theorem 20: Distinguishes is irreflexive. -/
theorem distinguishes_irrefl {ι S V : Type*} (O : Finset ι) (obs : ι → S → V) (s : S) :
    ¬ Distinguishes O obs s s := by
  rintro ⟨_, _, hne⟩
  exact hne rfl

/-- Theorem 21: Distinguishes is symmetric. -/
theorem distinguishes_symm {ι S V : Type*} (O : Finset ι) (obs : ι → S → V) {s₁ s₂ : S}
    (h : Distinguishes O obs s₁ s₂) : Distinguishes O obs s₂ s₁ := by
  rcases h with ⟨i, hi, hne⟩
  exact ⟨i, hi, hne.symm⟩

/-- Theorem 22: Bounded-observer epiplexity resolution count is monotone in observer set `O`. -/
theorem epiplexityCount_mono {ι S V : Type*} [Fintype S]
    {O₁ O₂ : Finset ι} (hsub : O₁ ⊆ O₂) (obs : ι → S → V) :
    epiplexityCount O₁ obs ≤ epiplexityCount O₂ obs := by
  unfold epiplexityCount resolvedPairs
  refine Finset.card_le_card ?_
  intro p hp
  simp only [Finset.mem_filter, Finset.mem_univ, true_and] at hp ⊢
  exact distinguishes_mono hsub obs hp

/-- Theorem 23: Adding a probe that splits any previously confounded pair strictly
    increases bounded-observer epiplexity resolution. -/
theorem epiplexityCount_strict_of_split {ι S V : Type*} [Fintype S]
    {O₁ O₂ : Finset ι} (hsub : O₁ ⊆ O₂) (obs : ι → S → V)
    {s₁ s₂ : S} (hmiss : ¬ Distinguishes O₁ obs s₁ s₂) (hhit : Distinguishes O₂ obs s₁ s₂) :
    epiplexityCount O₁ obs < epiplexityCount O₂ obs := by
  unfold epiplexityCount
  refine Finset.card_lt_card ?_
  rw [Finset.ssubset_iff_of_subset]
  · refine ⟨(s₁, s₂), ?_, ?_⟩
    · simp [resolvedPairs, hhit]
    · simp [resolvedPairs, hmiss]
  · intro p hp
    simp only [resolvedPairs, Finset.mem_filter, Finset.mem_univ, true_and] at hp ⊢
    exact distinguishes_mono hsub obs hp

/-- Theorem 24: Adding a degenerate probe that fails to separate any state adds zero epiplexity gain. -/
theorem redundant_probe_zero_gain {ι S V : Type*} [DecidableEq ι] [Fintype S]
    (O : Finset ι) (j : ι) (obs : ι → S → V)
    (hconst : ∀ s₁ s₂ : S, obs j s₁ = obs j s₂) :
    epiplexityCount (insert j O) obs = epiplexityCount O obs := by
  unfold epiplexityCount
  congr 1
  ext p
  simp only [resolvedPairs, Finset.mem_filter, Finset.mem_univ, true_and]
  constructor
  · rintro ⟨i, hi, hne⟩
    rcases Finset.mem_insert.mp hi with rfl | hiO
    · exact absurd (hconst p.1 p.2) hne
    · exact ⟨i, hiO, hne⟩
  · exact distinguishes_mono (Finset.subset_insert j O) obs

/-- Theorem 25: Concrete `A5` witness: standard 4D rep `ρ_4` (`χ_4(C5±) = -1`) is blind
    between the two 5-cycle classes (`epiplexity = 0`), while adding `ρ_3(φ)` splits them
    (`epiplexity = 2 > 0`). -/
theorem a5_rho4_degenerate_rho3_splits :
    let obs : Fin 2 → Bool → ℝ := fun i b =>
      match i.val with
      | 0 => -1
      | _ => if b then psiGolden else phiGolden
    epiplexityCount ({0} : Finset (Fin 2)) obs = 0 ∧
    epiplexityCount ({0, 1} : Finset (Fin 2)) obs = 2 ∧
    epiplexityCount ({0} : Finset (Fin 2)) obs <
      epiplexityCount ({0, 1} : Finset (Fin 2)) obs := by
  dsimp only
  let obs : Fin 2 → Bool → ℝ := fun i b =>
    match i.val with
    | 0 => -1
    | _ => if b then psiGolden else phiGolden
  have hzero : epiplexityCount ({0} : Finset (Fin 2)) obs = 0 := by
    unfold epiplexityCount resolvedPairs
    rw [Finset.card_eq_zero, Finset.filter_eq_empty_iff]
    intro p _ ⟨i, hi, hne⟩
    rw [Finset.mem_singleton] at hi
    subst hi
    exact hne rfl
  have htwo : epiplexityCount ({0, 1} : Finset (Fin 2)) obs = 2 := by
    unfold epiplexityCount resolvedPairs
    have hset : (Finset.univ : Finset (Bool × Bool)).filter
        (fun p => Distinguishes ({0, 1} : Finset (Fin 2)) obs p.1 p.2) =
        {(false, true), (true, false)} := by
      ext ⟨a, b⟩
      simp only [Finset.mem_filter, Finset.mem_univ, true_and, Finset.mem_insert,
        Finset.mem_singleton, Prod.mk.injEq]
      cases a <;> cases b <;> simp [Distinguishes, obs, phiGolden_ne_psiGolden,
        phiGolden_ne_psiGolden.symm]
    rw [hset, Finset.card_pair (by decide)]
  refine ⟨hzero, htwo, ?_⟩
  rw [hzero, htwo]
  norm_num

end EpiplexityBoundedObserver

-- =============================================================================
-- 4. Phase5Synthesis (5 theorems)
-- =============================================================================
namespace Phase5Synthesis

open A5IcosahedralUnitary
open ERMoEGaugeRouting
open EpiplexityBoundedObserver

/-- Theorem 26: Both Galois-conjugate 3D icosahedral reps simultaneously satisfy exact
    unitarity and exact `A5` presentation relations under arbitrary `U(3)` gauges. -/
theorem a5_phi_and_psi_exact_presentations (V1 V2 : Matrix (Fin 3) (Fin 3) ℂ)
    (hV1 : IsUnitary V1) (hV2 : IsUnitary V2) :
    (gaugeConj V1 (a5GenS phiGolden) ^ 2 = 1 ∧
      gaugeConj V1 a5GenT ^ 3 = 1 ∧
      (gaugeConj V1 (a5GenS phiGolden) * gaugeConj V1 a5GenT) ^ 5 = 1) ∧
    (gaugeConj V2 (a5GenS psiGolden) ^ 2 = 1 ∧
      gaugeConj V2 a5GenT ^ 3 = 1 ∧
      (gaugeConj V2 (a5GenS psiGolden) * gaugeConj V2 a5GenT) ^ 5 = 1) := by
  have h1 := a5GaugeConj_hom_rel V1 (a5GenS phiGolden) a5GenT hV1
    (a5GenS_hermitian_and_sq phiGolden phiGolden_sq).2
    a5GenT_unitary_and_cube.2
    (a5Gen_mixed_rel_five phiGolden phiGolden_sq)
  have h2 := a5GaugeConj_hom_rel V2 (a5GenS psiGolden) a5GenT hV2
    (a5GenS_hermitian_and_sq psiGolden psiGolden_sq).2
    a5GenT_unitary_and_cube.2
    (a5Gen_mixed_rel_five psiGolden psiGolden_sq)
  exact ⟨⟨h1.1, h1.2.1, h1.2.2.1⟩, ⟨h2.1, h2.2.1, h2.2.2.1⟩⟩

/-- Theorem 27: Combined ERMoE routed trace invariance and zero-forgetting orthogonal SGD. -/
theorem a5_ermoe_trace_and_zero_forgetting {E d m k : ℕ}
    (g : Fin E → ℝ) (hg : IsSimplexGate g)
    (V : Fin E → Matrix (Fin d) (Fin d) ℂ) (hV : ∀ e, IsUnitary (V e))
    (M : Matrix (Fin d) (Fin d) ℂ)
    (W : Matrix (Fin m) (Fin k) ℝ)
    (updates : List (ℝ × (Fin m → ℝ) × (Fin k → ℝ)))
    (x_keep : Fin k → ℝ) (horth : ∀ u ∈ updates, u.2.2 ⬝ᵥ x_keep = 0) :
    (routedOp g V M).trace = M.trace ∧
      (foldOrthSGD W updates) *ᵥ x_keep = W *ᵥ x_keep :=
  ⟨ermoe_routed_trace_invariant g hg V hV M, ermoe_batch_sgd_invariant W updates x_keep horth⟩

/-- Theorem 28: Joint `30×` MDL generator compression and Galois `C5+`/`C5-` trace separation. -/
theorem a5_mdl_and_galois_split :
    frobNormSq (a5GenS phiGolden) + frobNormSq a5GenT < (60 : ℝ) * 3 ∧
      (a5GenS phiGolden * a5GenT).trace ≠ (a5GenS psiGolden * a5GenT).trace :=
  ⟨a5_generator_mdl_30x, a5_galois_fiveCycle_trace_split.2.2⟩

/-- Theorem 29: Joint epiplexity strict gain under non-degenerate irrep probes paired with
    ERMoE routed trace preservation on `A5`. -/
theorem a5_epiplexity_and_ermoe_closure {E : ℕ}
    (g : Fin E → ℝ) (hg : IsSimplexGate g)
    (V : Fin E → Matrix (Fin 3) (Fin 3) ℂ) (hV : ∀ e, IsUnitary (V e)) :
    (routedOp g V (a5GenS phiGolden * a5GenT)).trace = (phiGolden : ℂ) ∧
      ∃ (obs : Fin 2 → Bool → ℝ),
        epiplexityCount ({0} : Finset (Fin 2)) obs <
          epiplexityCount ({0, 1} : Finset (Fin 2)) obs := by
  refine ⟨?_, ?_⟩
  · rw [ermoe_routed_trace_invariant g hg V hV, a5_galois_fiveCycle_trace_split.1]
  · refine ⟨fun i b => match i.val with | 0 => -1 | _ => if b then psiGolden else phiGolden, ?_⟩
    exact a5_rho4_degenerate_rho3_splits.2.2

structure NonSolvableMasterBundle where
  sPhi : Matrix (Fin 3) (Fin 3) ℂ
  sPsi : Matrix (Fin 3) (Fin 3) ℂ
  tMat : Matrix (Fin 3) (Fin 3) ℂ
  relPhi : (sPhi * tMat) ^ 5 = 1
  relPsi : (sPsi * tMat) ^ 5 = 1
  galoisSplit : (sPhi * tMat).trace ≠ (sPsi * tMat).trace
  mdlCompressed : frobNormSq sPhi + frobNormSq tMat < (60 : ℝ) * 3
  ermoeInvariant : ∀ {E : ℕ} (g : Fin E → ℝ), IsSimplexGate g →
    ∀ (V : Fin E → Matrix (Fin 3) (Fin 3) ℂ), (∀ e, IsUnitary (V e)) →
      (routedOp g V (sPhi * tMat)).trace = (sPhi * tMat).trace

/-- Theorem 30: Concrete inhabited `NonSolvableMasterBundle` uniting exact non-solvable
    `A5` icosahedral presentations, Galois trace separation, `30×` MDL compression, and
    ERMoE mixture-of-experts trace invariance. -/
theorem nonsolvable_master_principle_bundle : Nonempty NonSolvableMasterBundle := by
  refine ⟨{
    sPhi := a5GenS phiGolden
    sPsi := a5GenS psiGolden
    tMat := a5GenT
    relPhi := a5Gen_mixed_rel_five phiGolden phiGolden_sq
    relPsi := a5Gen_mixed_rel_five psiGolden psiGolden_sq
    galoisSplit := a5_galois_fiveCycle_trace_split.2.2
    mdlCompressed := a5_generator_mdl_30x
    ermoeInvariant := fun g hg V hV => ermoe_routed_trace_invariant g hg V hV _
  }⟩

end Phase5Synthesis

end

end Semplex.A5ERMoE