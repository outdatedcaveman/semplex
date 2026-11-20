/-
  Mathlib formalization for Gap C1 / Theorem 15 continuous Gaussian prior:
  Signed-permutation invariance of i.i.d. centered Gaussian product measures on `Fin n → ℝ`
  and pushforward invariance under equivariant measurable maps.

  Isolated in `proofs/lean-mathlib/` so `proofs/lean/` remains core Lean 4 (zero Mathlib dependency).
-/
import Mathlib.Probability.Distributions.Gaussian
import Mathlib.MeasureTheory.Constructions.Pi

open scoped ENNReal NNReal
open MeasureTheory ProbabilityTheory Set

namespace CerpMathlib

/-- Signed-permutation group element on `n` real coordinates, mirroring `PFT.SignedPerm` in
    `proofs/lean/Theory.lean`. -/
structure SignedPerm (n : Nat) where
  toFun : Fin n → Fin n
  invFun : Fin n → Fin n
  left_inv : ∀ i, invFun (toFun i) = i
  right_inv : ∀ i, toFun (invFun i) = i
  sgn : Fin n → Bool

def SignedPerm.toEquiv {n : Nat} (σ : SignedPerm n) : Fin n ≃ Fin n where
  toFun := σ.toFun
  invFun := σ.invFun
  left_inv := σ.left_inv
  right_inv := σ.right_inv

def SignedPerm.inv {n : Nat} (σ : SignedPerm n) : SignedPerm n where
  toFun := σ.invFun
  invFun := σ.toFun
  left_inv := σ.right_inv
  right_inv := σ.left_inv
  sgn := fun i => σ.sgn (σ.toFun i)

/-- Signed-permutation action on `Fin n → ℝ`, mirroring `PFT.actVec` over `ℝ`. -/
def actRealVec {n : Nat} (σ : SignedPerm n) (v : Fin n → ℝ) : Fin n → ℝ :=
  fun i => if σ.sgn i then -(v (σ.invFun i)) else v (σ.invFun i)

@[simp]
theorem actRealVec_left_inv {n : Nat} (σ : SignedPerm n) (v : Fin n → ℝ) :
    actRealVec (SignedPerm.inv σ) (actRealVec σ v) = v := by
  funext j
  simp only [actRealVec, SignedPerm.inv, σ.left_inv]
  cases h : σ.sgn (σ.toFun j) <;> simp [h]

@[simp]
theorem actRealVec_right_inv {n : Nat} (σ : SignedPerm n) (v : Fin n → ℝ) :
    actRealVec σ (actRealVec (SignedPerm.inv σ) v) = v := by
  funext i
  simp only [actRealVec, SignedPerm.inv, σ.right_inv]
  cases h : σ.sgn i <;> simp [h]

theorem measurable_actRealVec {n : Nat} (σ : SignedPerm n) :
    Measurable (actRealVec σ) := by
  refine measurable_pi_lambda _ fun i => ?_
  have hi : Measurable (fun v : Fin n → ℝ => v (σ.invFun i)) := measurable_pi_apply (σ.invFun i)
  by_cases h : σ.sgn i
  · simpa [actRealVec, h] using hi.neg
  · simpa [actRealVec, h] using hi

def actMeasEquiv {n : Nat} (σ : SignedPerm n) : (Fin n → ℝ) ≃ᵐ (Fin n → ℝ) where
  toFun := actRealVec σ
  invFun := actRealVec (SignedPerm.inv σ)
  left_inv := actRealVec_left_inv σ
  right_inv := actRealVec_right_inv σ
  measurable_toFun := measurable_actRealVec σ
  measurable_invFun := measurable_actRealVec (SignedPerm.inv σ)

/-- Product of `n` i.i.d. centered Gaussian measures `N(0, v)` on `Fin n → ℝ`. -/
noncomputable def gaussianProd (n : Nat) (v : ℝ≥0) : Measure (Fin n → ℝ) :=
  Measure.pi fun _ : Fin n => gaussianReal 0 v

instance instIsProbabilityMeasureGaussianProd (n : Nat) (v : ℝ≥0) :
    IsProbabilityMeasure (gaussianProd n v) := by
  unfold gaussianProd
  infer_instance

/-- A centered 1D Gaussian `N(0, v)` is invariant under negation `x ↦ -x`. -/
theorem gaussianReal_map_neg (v : ℝ≥0) :
    (gaussianReal 0 v).map Neg.neg = gaussianReal 0 v := by
  have hmul : (Neg.neg : ℝ → ℝ) = fun x => (-1 : ℝ) * x := by
    funext x
    ring
  rw [hmul, gaussianReal_map_const_mul]
  have hsq : (⟨(-1 : ℝ) ^ 2, sq_nonneg (-1 : ℝ)⟩ : ℝ≥0) = 1 := by
    ext
    norm_num
  rw [hsq, one_mul, mul_zero]

/-- Any i.i.d. product measure on `Fin n → ℝ` whose 1D marginal `μ₀` is symmetric (`μ₀.map (-·) = μ₀`)
    is invariant under every signed coordinate permutation `actRealVec σ`. -/
theorem iid_symmetric_pi_map_actRealVec {n : Nat} (μ₀ : Measure ℝ) [IsProbabilityMeasure μ₀]
    (hneg : μ₀.map Neg.neg = μ₀) (σ : SignedPerm n) :
    (Measure.pi fun _ : Fin n => μ₀).map (actRealVec σ) = Measure.pi fun _ : Fin n => μ₀ := by
  let e : (Fin n → ℝ) ≃ᵐ (Fin n → ℝ) := actMeasEquiv σ
  change (Measure.pi fun _ : Fin n => μ₀).map e = Measure.pi fun _ : Fin n => μ₀
  refine (Measure.pi_eq fun s hs => ?_).symm
  rw [e.measurableEmbedding.map_apply]
  let s' : Fin n → Set ℝ := fun j =>
    if σ.sgn (σ.toFun j) then Neg.neg ⁻¹' s (σ.toFun j) else s (σ.toFun j)
  have hpre : (e ⁻¹' Set.pi Set.univ s) = Set.pi Set.univ s' := by
    ext x
    simp only [mem_preimage, Set.mem_pi, mem_univ, forall_true_left]
    refine (σ.toEquiv.forall_congr fun j => ?_).symm
    have hinv : σ.invFun (σ.toFun j) = j := σ.left_inv j
    change (x j ∈ if σ.sgn (σ.toFun j) then Neg.neg ⁻¹' s (σ.toFun j) else s (σ.toFun j)) ↔
      (if σ.sgn (σ.toFun j) then -(x (σ.invFun (σ.toFun j))) else x (σ.invFun (σ.toFun j))) ∈
        s (σ.toFun j)
    rw [hinv]
    cases σ.sgn (σ.toFun j) <;> simp
  rw [hpre, Measure.pi_pi]
  have hcoord : ∀ j : Fin n, μ₀ (s' j) = μ₀ (s (σ.toFun j)) := by
    intro j
    dsimp only [s']
    cases h : σ.sgn (σ.toFun j)
    · simp [h]
    · simp only [h, ↓reduceIte]
      rw [← Measure.map_apply measurable_neg (hs (σ.toFun j)), hneg]
  calc
    ∏ j : Fin n, μ₀ (s' j) = ∏ j : Fin n, μ₀ (s (σ.toFun j)) := by
      refine Finset.prod_congr rfl fun j _ => hcoord j
    _ = ∏ i : Fin n, μ₀ (s i) := by
      refine Finset.prod_equiv σ.toEquiv (fun j => by simp) fun j _ => rfl

/-- Core Gap C1 theorem (part 1): the i.i.d. centered Gaussian product measure `N(0, v)^⊗n`
    on `Fin n → ℝ` is invariant under every signed coordinate permutation `actRealVec σ`. -/
theorem gaussianProd_map_actRealVec (n : Nat) (v : ℝ≥0) (σ : SignedPerm n) :
    (gaussianProd n v).map (actRealVec σ) = gaussianProd n v :=
  iid_symmetric_pi_map_actRealVec (gaussianReal 0 v) (gaussianReal_map_neg v) σ

/-- Core Gap C1 theorem (part 2): if `T : (Fin n → ℝ) → (Fin n → ℝ)` is measurable and
    equivariant under `actRealVec σ`, then the pushforward measure `(gaussianProd n v).map T`
    remains invariant under `actRealVec σ`. -/
theorem gaussianProd_pushforward_equivariant {n : Nat} (v : ℝ≥0) (σ : SignedPerm n)
    (T : (Fin n → ℝ) → (Fin n → ℝ)) (hTm : Measurable T)
    (hTeq : ∀ θ, T (actRealVec σ θ) = actRealVec σ (T θ)) :
    ((gaussianProd n v).map T).map (actRealVec σ) = (gaussianProd n v).map T := by
  rw [Measure.map_map (measurable_actRealVec σ) hTm]
  have hcomp : actRealVec σ ∘ T = T ∘ actRealVec σ := funext fun θ => (hTeq θ).symm
  rw [hcomp, ← Measure.map_map hTm (measurable_actRealVec σ), gaussianProd_map_actRealVec n v σ]

/-- General pushforward orbit invariance to any measurable codomain `C` under an equivariant
    measurable map `F : (Fin n → ℝ) → C`: matching continuous measure-theoretic version of
    `PFT.theorem15_finite_distribution_invariant`. -/
theorem gaussianProd_readout_map_invariant {n : Nat} {C : Type*} [MeasurableSpace C]
    (v : ℝ≥0) (σ : SignedPerm n) (actC : C → C) (hactC : Measurable actC)
    (F : (Fin n → ℝ) → C) (hFm : Measurable F)
    (hFeq : ∀ θ, F (actRealVec σ θ) = actC (F θ)) :
    ((gaussianProd n v).map F).map actC = (gaussianProd n v).map F := by
  rw [Measure.map_map hactC hFm]
  have hcomp : actC ∘ F = F ∘ actRealVec σ := funext fun θ => (hFeq θ).symm
  rw [hcomp, ← Measure.map_map hFm (measurable_actRealVec σ), gaussianProd_map_actRealVec n v σ]

/-- Discrete circuit-mass equality matching `P160` (`theorem15_finite_distribution_invariant`):
    for `F = fun θ => readout (iterStep step t θ)` equivariant into `(actC, invC)` on a
    measurable-singleton circuit space `C`, the pushed-forward Gaussian probability mass on
    `{actC tgt}` equals that on `{tgt}`. -/
theorem theorem15_gaussian_circuit_mass_eq {n : Nat} {C : Type*} [MeasurableSpace C]
    [MeasurableSingletonClass C] (v : ℝ≥0) (σ : SignedPerm n)
    (actC invC : C → C) (hC_left : ∀ c, invC (actC c) = c) (hactC : Measurable actC)
    (F : (Fin n → ℝ) → C) (hFm : Measurable F)
    (hFeq : ∀ θ, F (actRealVec σ θ) = actC (F θ))
    (tgt : C) :
    (gaussianProd n v).map F {actC tgt} = (gaussianProd n v).map F {tgt} := by
  have hinv : ((gaussianProd n v).map F).map actC {actC tgt} = (gaussianProd n v).map F {actC tgt} :=
    congrArg (fun m : Measure C => m {actC tgt})
      (gaussianProd_readout_map_invariant v σ actC hactC F hFm hFeq)
  rw [Measure.map_apply hactC (MeasurableSet.singleton (actC tgt))] at hinv
  have hpre : actC ⁻¹' {actC tgt} = {tgt} := by
    ext c
    simp only [mem_preimage, mem_singleton_iff]
    constructor
    · intro hc
      simpa [hC_left] using congrArg invC hc
    · intro hc
      rw [hc]
  rw [hpre] at hinv
  exact hinv.symm

/-- Iterating an equivariant measurable training step `step : (Fin n → ℝ) → (Fin n → ℝ)`
    for `t` steps preserves measurability and signed-permutation equivariance. -/
theorem measurable_iterate {α : Type*} [MeasurableSpace α] (f : α → α) (hf : Measurable f) :
    ∀ t : Nat, Measurable (Nat.iterate f t)
  | 0 => measurable_id
  | t + 1 => by
      have ih := measurable_iterate f hf t
      simpa only [Function.iterate_succ] using ih.comp hf

theorem iterate_equivariant {α : Type*} (gα : α → α) (f : α → α)
    (heq : ∀ x, f (gα x) = gα (f x)) :
    ∀ (t : Nat) (x : α), Nat.iterate f t (gα x) = gα (Nat.iterate f t x)
  | 0, _ => rfl
  | t + 1, x => by
      simp only [Function.iterate_succ_apply']
      rw [iterate_equivariant gα f heq t x, heq]

/-- Continuous Gaussian counterpart to `PFT.theorem15_finite_distribution_invariant`:
    for any measurable signed-permutation-equivariant update `step` (e.g. GD/AdamW on `ℝ^n`)
    and equivariant measurable readout `readout : (Fin n → ℝ) → C`, iterating `t` steps from
    an i.i.d. centered Gaussian prior `gaussianProd n v` yields equal probability mass on
    `{actC tgt}` and `{tgt}`. -/
theorem theorem15_gaussian_iter_circuit_mass_eq {n : Nat} {C : Type*} [MeasurableSpace C]
    [MeasurableSingletonClass C] (v : ℝ≥0) (σ : SignedPerm n)
    (actC invC : C → C) (hC_left : ∀ c, invC (actC c) = c) (hactC : Measurable actC)
    (step : (Fin n → ℝ) → (Fin n → ℝ)) (hstepm : Measurable step)
    (hstepeq : ∀ θ, step (actRealVec σ θ) = actRealVec σ (step θ))
    (readout : (Fin n → ℝ) → C) (hrm : Measurable readout)
    (hreq : ∀ θ, readout (actRealVec σ θ) = actC (readout θ))
    (t : Nat) (tgt : C) :
    (gaussianProd n v).map (fun θ => readout (Nat.iterate step t θ)) {actC tgt} =
      (gaussianProd n v).map (fun θ => readout (Nat.iterate step t θ)) {tgt} := by
  refine theorem15_gaussian_circuit_mass_eq v σ actC invC hC_left hactC
    (fun θ => readout (Nat.iterate step t θ)) (hrm.comp (measurable_iterate step hstepm t))
    (fun θ => ?_) tgt
  dsimp only
  rw [iterate_equivariant (actRealVec σ) step hstepeq t θ, hreq]

end CerpMathlib
