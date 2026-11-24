import Mathlib

/-!
# Semigroup, Wreath Cascade, Contractive Attention & Kan Nerve Bridge (`Semplex.SemigroupClosure`)

Extends the Master Principle from solvable and non-solvable finite groups and continuous
Lie symmetries (`SO(3)`) to non-invertible Krohn-Rhodes reset semigroups (`U_2`, `G ≀ U_2`),
contractive Transformer simplex attention with orthogonal subspace retention, and the strict
2-horn separation between monoid/semigroup quasi-categories (`Λ²₁`) and group/path Kan nerves.
-/

namespace Semplex.SemigroupClosure

open Matrix BigOperators

noncomputable section

-- =============================================================================
-- 1. FlipFlopResetMonoid (8 theorems)
-- =============================================================================
namespace FlipFlopResetMonoid

/-- Non-invertible 3-element flip-flop reset monoid `U_2 = {id, r0, r1}`. -/
inductive U2 : Type
  | id
  | r0
  | r1
  deriving DecidableEq

/-- Left-zero reset composition (latest transition `a` applied after prefix `b`). -/
def u2Mul : U2 → U2 → U2
  | .id, y => y
  | .r0, _ => .r0
  | .r1, _ => .r1

/-- Canonical 2x2 column-stochastic contraction representation of `U_2` over `ℝ`. -/
def u2Mat : U2 → Matrix (Fin 2) (Fin 2) ℝ
  | .id =>
      Matrix.of fun i j =>
        if i = j then 1 else 0
  | .r0 =>
      Matrix.of fun i _ =>
        if i = 0 then 1 else 0
  | .r1 =>
      Matrix.of fun i _ =>
        if i = 1 then 1 else 0

/-- Theorem 1: `u2Mul` is associative. -/
theorem u2Mul_assoc (a b c : U2) : u2Mul (u2Mul a b) c = u2Mul a (u2Mul b c) := by
  cases a <;> rfl

/-- Theorem 2: `u2Mat` is a strict multiplicative homomorphism `(U_2, u2Mul) → M_2(ℝ)`. -/
theorem u2Mat_mul (a b : U2) : u2Mat (u2Mul a b) = u2Mat a * u2Mat b := by
  cases a <;> cases b <;>
    · ext i j
      fin_cases i <;> fin_cases j <;>
        simp [u2Mul, u2Mat, Matrix.mul_apply, Fin.sum_univ_two]

/-- Theorem 3: Every element of `U_2` is idempotent under matrix multiplication. -/
theorem u2Mat_idempotent (a : U2) : u2Mat a * u2Mat a = u2Mat a := by
  cases a <;>
    · ext i j
      fin_cases i <;> fin_cases j <;>
        simp [u2Mat, Matrix.mul_apply, Fin.sum_univ_two]

/-- Theorem 4: Both reset operators `r0`, `r1` are singular (`det = 0`). -/
theorem u2Mat_reset_det_zero : (u2Mat .r0).det = 0 ∧ (u2Mat .r1).det = 0 := by
  simp [u2Mat, Matrix.det_fin_two]

/-- Theorem 5: Neither reset matrix `r0` nor `r1` is invertible in `GL_2(ℝ)`. -/
theorem u2Mat_reset_not_unit : (¬ IsUnit (u2Mat .r0)) ∧ (¬ IsUnit (u2Mat .r1)) := by
  have hdet0 := u2Mat_reset_det_zero
  constructor
  · rintro ⟨u, hu⟩
    have hmul : (u.val * u.inv).det = (1 : Matrix (Fin 2) (Fin 2) ℝ).det :=
      congrArg Matrix.det u.val_inv
    rw [Matrix.det_mul, Matrix.det_one, hu, hdet0.1, zero_mul] at hmul
    exact zero_ne_one hmul
  · rintro ⟨u, hu⟩
    have hmul : (u.val * u.inv).det = (1 : Matrix (Fin 2) (Fin 2) ℝ).det :=
      congrArg Matrix.det u.val_inv
    rw [Matrix.det_mul, Matrix.det_one, hu, hdet0.2, zero_mul] at hmul
    exact zero_ne_one hmul

/-- Theorem 6: Every `u2Mat a` is entrywise non-negative and column-stochastic. -/
theorem u2Mat_col_stochastic (a : U2) :
    (∀ i j, 0 ≤ u2Mat a i j) ∧ (∀ j, ∑ i : Fin 2, u2Mat a i j = 1) := by
  cases a <;> constructor
  · intro i j; fin_cases i <;> fin_cases j <;> simp [u2Mat]
  · intro j; fin_cases j <;> simp [u2Mat, Fin.sum_univ_two]
  · intro i j; fin_cases i <;> fin_cases j <;> simp [u2Mat]
  · intro j; fin_cases j <;> simp [u2Mat, Fin.sum_univ_two]
  · intro i j; fin_cases i <;> fin_cases j <;> simp [u2Mat]
  · intro j; fin_cases j <;> simp [u2Mat, Fin.sum_univ_two]

/-- Theorem 7: Each reset operator collapses all normalized simplex states to a single state. -/
theorem u2Mat_reset_collapses_simplex (p q : Fin 2 → ℝ)
    (hp : ∑ i : Fin 2, p i = 1) (hq : ∑ i : Fin 2, q i = 1) :
    u2Mat .r0 *ᵥ p = u2Mat .r0 *ᵥ q ∧ u2Mat .r1 *ᵥ p = u2Mat .r1 *ᵥ q := by
  have hp2 : p 0 + p 1 = 1 := by simpa [Fin.sum_univ_two] using hp
  have hq2 : q 0 + q 1 = 1 := by simpa [Fin.sum_univ_two] using hq
  constructor
  · ext i
    fin_cases i
    · simp [u2Mat, Matrix.mulVec, dotProduct, Fin.sum_univ_two]; linarith
    · simp [u2Mat, Matrix.mulVec, dotProduct, Fin.sum_univ_two]
  · ext i
    fin_cases i
    · simp [u2Mat, Matrix.mulVec, dotProduct, Fin.sum_univ_two]
    · simp [u2Mat, Matrix.mulVec, dotProduct, Fin.sum_univ_two]; linarith

/-- Theorem 8: Matrix traces stay invariant under orthogonal gauge conjugation and split
    resets (`Tr = 1`) from identity (`Tr = 2`). -/
theorem u2Mat_trace_gauge_invariant (V : Matrix (Fin 2) (Fin 2) ℝ)
    (hV : V * Vᵀ = 1) (a : U2) :
    (V * u2Mat a * Vᵀ).trace = (u2Mat a).trace ∧
    (u2Mat .r0).trace ≠ (u2Mat .id).trace := by
  have hVtV : Vᵀ * V = 1 := Matrix.mul_eq_one_comm.mp hV
  refine ⟨?_, ?_⟩
  · calc
      (V * u2Mat a * Vᵀ).trace = (V * (u2Mat a * Vᵀ)).trace := by rw [Matrix.mul_assoc]
      _ = (u2Mat a * Vᵀ * V).trace := by
          simpa [Matrix.mul_assoc] using Matrix.trace_mul_comm V (u2Mat a * Vᵀ)
      _ = (u2Mat a * (Vᵀ * V)).trace := by rw [Matrix.mul_assoc]
      _ = (u2Mat a).trace := by rw [hVtV, Matrix.mul_one]
  · simp [u2Mat, Matrix.trace, Fin.sum_univ_two]

end FlipFlopResetMonoid

-- =============================================================================
-- 2. KrohnRhodesWreathCascade (7 theorems)
-- =============================================================================
namespace KrohnRhodesWreathCascade

/-- Wreath-product cascade tokens `G ≀ U_2`: coupled group transitions or reset. -/
inductive KRToken (G : Type*) : Type _
  | step (g0 g1 : G)
  | reset (b' : Bool)

/-- Single causal transition of `G ≀ U_2` on state `(g, mode) ∈ G × Bool`. -/
def krStep {G : Type*} [Group G] (tok : KRToken G) (st : G × Bool) : G × Bool :=
  match tok with
  | .step g0 g1 => (if st.2 then g1 * st.1 else g0 * st.1, st.2)
  | .reset b' => (1, b')

/-- Run a sequence of wreath tokens left-to-right from `st`. -/
def krRun {G : Type*} [Group G] (w : List (KRToken G)) (st : G × Bool) : G × Bool :=
  w.foldl (fun s tok => krStep tok s) st

/-- Theorem 9: Wreath word execution factors homomorphically over concatenation. -/
theorem krRun_append {G : Type*} [Group G]
    (w₁ w₂ : List (KRToken G)) (st : G × Bool) :
    krRun (w₁ ++ w₂) st = krRun w₂ (krRun w₁ st) := by
  simp [krRun, List.foldl_append]

/-- Theorem 10: A reset token `KRToken.reset b'` erases arbitrary history prefix `w₁`
    and arbitrary prior states `st₁, st₂`. -/
theorem krRun_reset_erases_prefix {G : Type*} [Group G]
    (w₁ w₂ : List (KRToken G)) (b' : Bool) (st₁ st₂ : G × Bool) :
    krRun (w₁ ++ [KRToken.reset b'] ++ w₂) st₁ =
    krRun (w₁ ++ [KRToken.reset b'] ++ w₂) st₂ := by
  simp [krRun, List.foldl_append, krStep]

/-- Theorem 11: Pure unitary/group step sequences without resets preserve invertibility
    along each mode fiber. -/
theorem krRun_pure_steps_invertible {G : Type*} [Group G]
    (steps : List (G × G)) (b : Bool) :
    Function.Injective (fun g : G =>
      (krRun (steps.map fun p => KRToken.step p.1 p.2) (g, b)).1) := by
  induction steps generalizing b with
  | nil =>
      intro g₁ g₂ h
      simpa [krRun] using h
  | cons hd tl ih =>
      intro g₁ g₂ h
      simp only [List.map_cons, krRun, List.foldl_cons, krStep] at h
      have h' :
          (krRun (tl.map fun p => KRToken.step p.1 p.2) (if b then hd.2 * g₁ else hd.1 * g₁, b)).1 =
          (krRun (tl.map fun p => KRToken.step p.1 p.2) (if b then hd.2 * g₂ else hd.1 * g₂, b)).1 :=
        h
      have hinj := ih b h'
      by_cases hb : b
      · simp only [hb, ↓reduceIte] at hinj
        exact mul_left_cancel hinj
      · simp only [hb, Bool.false_eq_true, ↓reduceIte] at hinj
        exact mul_left_cancel hinj

/-- Theorem 12: For any nontrivial group `G`, a reset transition in `G ≀ U_2` is
    strictly non-injective. -/
theorem krAction_not_injective {G : Type*} [Group G] [Nontrivial G] (b' : Bool) :
    ¬ Function.Injective (fun st : G × Bool => krStep (KRToken.reset b') st) := by
  intro hinj
  obtain ⟨g, hg⟩ := exists_ne (1 : G)
  have heq : krStep (KRToken.reset b') (g, b') = krStep (KRToken.reset b') (1, b') := by
    simp [krStep]
  have hst := hinj heq
  exact hg (congrArg Prod.fst hst)

/-- Theorem 13: Exact L1 simplex distance collapses to zero after a reset transition. -/
theorem kr_reset_l1_contraction (p q : Fin 2 → ℝ)
    (hp : ∑ i : Fin 2, p i = 1) (hq : ∑ i : Fin 2, q i = 1) :
    ∑ i : Fin 2,
      |(FlipFlopResetMonoid.u2Mat .r0 *ᵥ p) i - (FlipFlopResetMonoid.u2Mat .r0 *ᵥ q) i| = 0 := by
  have hcol := (FlipFlopResetMonoid.u2Mat_reset_collapses_simplex p q hp hq).1
  simp [hcol]

/-- Theorem 14: Mode-routed ERMoE trace remains invariant under arbitrary independent
    unitary gauges `(V₀, V₁)` on each wreath fiber. -/
theorem kr_wreath_trace_gauge_invariant {d : ℕ}
    (V₀ M₀ V₁ M₁ : Matrix (Fin d) (Fin d) ℂ)
    (hV0 : V₀ * V₀ᴴ = 1) (hV1 : V₁ * V₁ᴴ = 1) (b : Bool) :
    (if b then (V₁ * M₁ * V₁ᴴ).trace else (V₀ * M₀ * V₀ᴴ).trace) =
    (if b then M₁.trace else M₀.trace) := by
  have triv (V M : Matrix (Fin d) (Fin d) ℂ) (hV : V * Vᴴ = 1) :
      (V * M * Vᴴ).trace = M.trace := by
    have hVtV : Vᴴ * V = 1 := Matrix.mul_eq_one_comm.mp hV
    calc
      (V * M * Vᴴ).trace = (V * (M * Vᴴ)).trace := by rw [Matrix.mul_assoc]
      _ = (M * Vᴴ * V).trace := by
          simpa [Matrix.mul_assoc] using Matrix.trace_mul_comm V (M * Vᴴ)
      _ = (M * (Vᴴ * V)).trace := by rw [Matrix.mul_assoc]
      _ = M.trace := by rw [hVtV, Matrix.mul_one]
  by_cases hb : b
  · simp [hb, triv V₁ M₁ hV1]
  · simp [hb, triv V₀ M₀ hV0]

/-- Theorem 15: Factored wreath cascade MDL `(2 * d + 2)` beats full `G ≀ U_2`
    regular bank `(3 * n * d)` whenever `d ≥ 1` and `n ≥ 2`. -/
theorem kr_cascade_mdl_compression (n d : ℕ) (hd : 1 ≤ d) (hn : 2 ≤ n) :
    (2 * d + 2 : ℝ) < (3 * n * d : ℝ) := by
  have hd_r : (1 : ℝ) ≤ d := by exact_mod_cast hd
  have hn_r : (2 : ℝ) ≤ n := by exact_mod_cast hn
  nlinarith

end KrohnRhodesWreathCascade

-- =============================================================================
-- 3. ContractiveTransformerAttention (7 theorems)
-- =============================================================================
namespace ContractiveTransformerAttention

/-- Exact causal softmax attention weights over a finite context of length `n`. -/
def softmaxWeight {n : ℕ} [NeZero n] (s : Fin n → ℝ) (i : Fin n) : ℝ :=
  Real.exp (s i) / ∑ j : Fin n, Real.exp (s j)

/-- Theorem 16: Every softmax attention weight is strictly positive. -/
theorem softmaxWeight_pos {n : ℕ} [NeZero n] (s : Fin n → ℝ) (i : Fin n) :
    0 < softmaxWeight s i := by
  unfold softmaxWeight
  have hden : 0 < ∑ j : Fin n, Real.exp (s j) :=
    Finset.sum_pos (fun j _ => Real.exp_pos (s j)) Finset.univ_nonempty
  exact div_pos (Real.exp_pos (s i)) hden

/-- Theorem 17: Softmax attention weights form a convex simplex distribution (`∑ w = 1`). -/
theorem softmaxWeight_sum_one {n : ℕ} [NeZero n] (s : Fin n → ℝ) :
    ∑ i : Fin n, softmaxWeight s i = 1 := by
  unfold softmaxWeight
  have hden : (∑ j : Fin n, Real.exp (s j)) ≠ 0 := by
    exact ne_of_gt (Finset.sum_pos (fun j _ => Real.exp_pos (s j)) Finset.univ_nonempty)
  rw [← Finset.sum_div, div_self hden]

/-- Theorem 18: Convex attention mixing preserves uniform scalar norm bounds. -/
theorem convex_attention_norm_le {n : ℕ} (w : Fin n → ℝ)
    (hw0 : ∀ i, 0 ≤ w i) (hw1 : ∑ i : Fin n, w i = 1)
    (v : Fin n → ℝ) (B : ℝ) (hv : ∀ i, |v i| ≤ B) :
    |∑ i : Fin n, w i * v i| ≤ B := by
  calc
    |∑ i : Fin n, w i * v i| ≤ ∑ i : Fin n, |w i * v i| := Finset.abs_sum_le_sum_abs _ _
    _ = ∑ i : Fin n, w i * |v i| := by
        refine Finset.sum_congr rfl (fun i _ => ?_)
        rw [abs_mul, abs_of_nonneg (hw0 i)]
    _ ≤ ∑ i : Fin n, w i * B := by
        refine Finset.sum_le_sum (fun i _ => ?_)
        exact mul_le_mul_of_nonneg_left (hv i) (hw0 i)
    _ = B := by rw [← Finset.sum_mul, hw1, one_mul]

/-- Theorem 19: Convex attention is non-expansive (`L_∞` contraction ≤ 1) on value differences. -/
theorem convex_attention_contraction_diff {n : ℕ} (w : Fin n → ℝ)
    (hw0 : ∀ i, 0 ≤ w i) (hw1 : ∑ i : Fin n, w i = 1)
    (v₁ v₂ : Fin n → ℝ) (B : ℝ) (hv : ∀ i, |v₁ i - v₂ i| ≤ B) :
    |(∑ i : Fin n, w i * v₁ i) - (∑ i : Fin n, w i * v₂ i)| ≤ B := by
  have hsub :
      (∑ i : Fin n, w i * v₁ i) - (∑ i : Fin n, w i * v₂ i) =
      ∑ i : Fin n, w i * (v₁ i - v₂ i) := by
    rw [← Finset.sum_sub_distrib]
    refine Finset.sum_congr rfl (fun i _ => by ring)
  rw [hsub]
  exact convex_attention_norm_le w hw0 hw1 (fun i => v₁ i - v₂ i) B hv

/-- Theorem 20: An idempotent subspace projector `P` annihilates `1 - P` on both sides. -/
theorem orth_projector_complement_zero {k : ℕ} (P : Matrix (Fin k) (Fin k) ℝ)
    (hP : P * P = P) :
    P * (1 - P) = 0 ∧ (1 - P) * P = 0 := by
  constructor <;> simp [mul_sub, sub_mul, hP]

/-- Theorem 21: Projecting Transformer readout updates through `I - P_keep` produces
    identically zero logit drift on every kept representation `h ∈ im(P_keep)`. -/
theorem transformer_orth_readout_sgd_zero_drift {m k : ℕ}
    (W G : Matrix (Fin m) (Fin k) ℝ) (P : Matrix (Fin k) (Fin k) ℝ)
    (h_keep : Fin k → ℝ) (η : ℝ) (hmem : P *ᵥ h_keep = h_keep) :
    (W - η • (G * (1 - P))) *ᵥ h_keep = W *ᵥ h_keep := by
  have hcomp : (1 - P) *ᵥ h_keep = 0 := by
    rw [Matrix.sub_mulVec, Matrix.one_mulVec, hmem, sub_self]
  have hzero : (G * (1 - P)) *ᵥ h_keep = 0 := by
    rw [← Matrix.mulVec_mulVec, hcomp, Matrix.mulVec_zero]
  have hzero_smul : (η • (G * (1 - P))) *ᵥ h_keep = 0 := by
    let M : Matrix (Fin m) (Fin k) ℝ := G * (1 - P)
    have hM : M *ᵥ h_keep = 0 := hzero
    ext i
    have hi : ∑ j : Fin k, M i j * h_keep j = 0 := by
      simpa [Matrix.mulVec, dotProduct] using congrFun hM i
    change (∑ j : Fin k, (η * M i j) * h_keep j) = 0
    calc
      ∑ j : Fin k, (η * M i j) * h_keep j
        = η * ∑ j : Fin k, M i j * h_keep j := by
            rw [Finset.mul_sum]
            refine Finset.sum_congr rfl (fun j _ => by ring)
      _ = η * 0 := by rw [hi]
      _ = 0 := mul_zero η
  rw [Matrix.sub_mulVec, hzero_smul, sub_zero]

/-- Theorem 22: Each rank-1 feature `φᵀ Σ⁻¹ φ = q > 0` yields strictly positive
    D-optimal log-determinant epiplexity gain `0 < log(1 + q / λ)`. -/
theorem d_optimal_rank1_det_gain {lam q : ℝ} (hlam : 0 < lam) (hq : 0 < q) :
    0 < Real.log (1 + q / lam) := by
  have hq_lam : 0 < q / lam := div_pos hq hlam
  exact Real.log_pos (lt_add_of_pos_right 1 hq_lam)

end ContractiveTransformerAttention

-- =============================================================================
-- 4. HigherSimplicialKanBridge (6 theorems)
-- =============================================================================
namespace HigherSimplicialKanBridge

/-- Theorem 23: Every monoid nerve fills every inner 2-horn `Λ²₁`. -/
theorem monoid_nerve_inner_horn_exists {M : Type*} [Monoid M] (f g : M) :
    ∃ h : M, f * g = h :=
  ⟨f * g, rfl⟩

/-- Theorem 24: Every group nerve fills every left outer 2-horn `Λ²₀`. -/
theorem group_nerve_outer_horn_left_exists {G : Type*} [Group G] (f h : G) :
    ∃ g : G, f * g = h :=
  ⟨f⁻¹ * h, by group⟩

/-- Theorem 25: Every group nerve fills every right outer 2-horn `Λ²₂`. -/
theorem group_nerve_outer_horn_right_exists {G : Type*} [Group G] (g h : G) :
    ∃ f : G, f * g = h :=
  ⟨h * g⁻¹, by group⟩

/-- Theorem 26: The flip-flop reset monoid `U_2` fills every inner 2-horn `Λ²₁`. -/
theorem u2_nerve_inner_horn_exists (f g : FlipFlopResetMonoid.U2) :
    ∃ h : FlipFlopResetMonoid.U2, FlipFlopResetMonoid.u2Mul f g = h :=
  ⟨FlipFlopResetMonoid.u2Mul f g, rfl⟩

/-- Theorem 27: The flip-flop reset monoid `U_2` refutes the left outer 2-horn `Λ²₀`. -/
theorem u2_nerve_outer_horn_left_fails :
    ∃ f h : FlipFlopResetMonoid.U2, ¬ ∃ g : FlipFlopResetMonoid.U2,
      FlipFlopResetMonoid.u2Mul f g = h := by
  refine ⟨.r0, .id, ?_⟩
  rintro ⟨g, hg⟩
  cases g <;> simp [FlipFlopResetMonoid.u2Mul] at hg

/-- Theorem 28: The flip-flop reset monoid `U_2` refutes the right outer 2-horn `Λ²₂`. -/
theorem u2_nerve_outer_horn_right_fails :
    ∃ g h : FlipFlopResetMonoid.U2, ¬ ∃ f : FlipFlopResetMonoid.U2,
      FlipFlopResetMonoid.u2Mul f g = h := by
  refine ⟨.r0, .id, ?_⟩
  rintro ⟨f, hf⟩
  cases f <;> simp [FlipFlopResetMonoid.u2Mul] at hf

end HigherSimplicialKanBridge

end
end Semplex.SemigroupClosure
