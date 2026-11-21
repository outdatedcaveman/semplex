/-
  Mathlib formalization for Gap C1 / Theorem 15 continuous Gaussian prior:
  Signed-permutation invariance of i.i.d. centered Gaussian product measures on `Fin n → ℝ`
  and pushforward invariance under equivariant measurable maps.

  Isolated in `proofs/lean-mathlib/` so `proofs/lean/` remains core Lean 4 (zero Mathlib dependency).
-/
import Mathlib.Probability.Distributions.Gaussian
import Mathlib.MeasureTheory.Constructions.Pi
import Mathlib.Analysis.Calculus.Deriv.Shift
import Mathlib.Analysis.Calculus.Deriv.Add
import Mathlib.Analysis.Calculus.Deriv.Mul
import Mathlib.Analysis.Calculus.Deriv.Inv
import Mathlib.Analysis.Calculus.Deriv.Comp
import Mathlib.Analysis.SpecialFunctions.ExpDeriv
import Mathlib.Analysis.SpecialFunctions.Log.Deriv
import Mathlib.Analysis.SpecialFunctions.Trigonometric.Deriv
import Mathlib.MeasureTheory.Function.SpecialFunctions.Basic
import Mathlib.MeasureTheory.Measure.Dirac
import Mathlib.Data.Sym.Sym2

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

/-!
## G13: End-to-End Closure of Theorem 15 (Gap C1)

1. Two-layer network over `ℝ` with inputs `{−1, +1}^n`, logistic loss on Boolean `g`, and input-symmetry
   group action `liftSignedPerm n H σ outFlip` (permuting/flipping input weights and negating output
   weights/bias iff `g ∘ σ = ¬g`).
2. Step (ii): exact invariance of `logisticLoss` (`logisticLoss_invariant`), plus hidden-neuron negation
   invariance for odd activations (`hiddenFlip_logisticLoss_invariant`).
3. Equivariance & Borel measurability of the **true analytic gradient** (`trueGrad_equivariant`,
   `trueGrad_logisticLoss_eq_explicitGrad`, `measurable_trueGrad_logisticLoss`), concrete odd activation
   `tanhReal`, GD (`gdStepReal`, `runGDSchedule`), and AdamW with zero initial moments and arbitrary
   time-varying schedule (`adamwStepReal`, `runAdamWSchedule`).
4. Block-homogeneous Gaussian/symmetric initialization measure (`twoLayerInitMeasure_invariant`) and
   concrete Spikes 09–14 unoriented threshold-prefix circuit readout (`concreteCircuitReadout`), closing
   Theorem 15 with zero residual equivariance or measurability hypotheses.
-/

section G13
noncomputable section

/-- Parameter dimension `H * n + H + H + 1` for a two-layer `(W1, b1, W2, b2)` network. -/
def paramDim (n H : Nat) : Nat := H * n + H + H + 1

abbrev TwoLayerParams (n H : Nat) := Fin (paramDim n H) → ℝ

private def finOneUnitEquiv : Fin 1 ≃ Unit where
  toFun _ := ()
  invFun _ := 0
  left_inv i := Fin.ext (Nat.lt_one_iff.mp i.isLt).symm
  right_inv _ := rfl

/-- Canonical equivalence splitting `Fin (paramDim n H)` into `(W1, b1, W2, b2)`. -/
def paramBlockEquiv (n H : Nat) :
    (Fin H × Fin n) ⊕ (Fin H ⊕ (Fin H ⊕ Unit)) ≃ Fin (paramDim n H) :=
  let e1 : (Fin H × Fin n) ⊕ Fin H ≃ Fin (H * n + H) :=
    (Equiv.sumCongr finProdFinEquiv (Equiv.refl (Fin H))).trans finSumFinEquiv
  let e2 : ((Fin H × Fin n) ⊕ Fin H) ⊕ Fin H ≃ Fin (H * n + H + H) :=
    (Equiv.sumCongr e1 (Equiv.refl (Fin H))).trans finSumFinEquiv
  let e3 : (((Fin H × Fin n) ⊕ Fin H) ⊕ Fin H) ⊕ Unit ≃ Fin (paramDim n H) :=
    (Equiv.sumCongr e2 finOneUnitEquiv.symm).trans finSumFinEquiv
  (Equiv.sumAssoc (Fin H × Fin n) (Fin H) (Fin H ⊕ Unit)).symm.trans
    ((Equiv.sumAssoc ((Fin H × Fin n) ⊕ Fin H) (Fin H) Unit).symm.trans e3)

def idxW1 {n H : Nat} (h : Fin H) (j : Fin n) : Fin (paramDim n H) :=
  paramBlockEquiv n H (Sum.inl (h, j))

def idxB1 {n H : Nat} (h : Fin H) : Fin (paramDim n H) :=
  paramBlockEquiv n H (Sum.inr (Sum.inl h))

def idxW2 {n H : Nat} (h : Fin H) : Fin (paramDim n H) :=
  paramBlockEquiv n H (Sum.inr (Sum.inr (Sum.inl h)))

def idxB2 {n H : Nat} : Fin (paramDim n H) :=
  paramBlockEquiv n H (Sum.inr (Sum.inr (Sum.inr ())))

def w1 {n H : Nat} (θ : TwoLayerParams n H) (h : Fin H) (j : Fin n) : ℝ := θ (idxW1 h j)
def b1 {n H : Nat} (θ : TwoLayerParams n H) (h : Fin H) : ℝ := θ (idxB1 h)
def w2 {n H : Nat} (θ : TwoLayerParams n H) (h : Fin H) : ℝ := θ (idxW2 h)
def b2 {n H : Nat} (θ : TwoLayerParams n H) : ℝ := θ idxB2

/-- Map `Bool` to `{−1, +1} ⊂ ℝ`. -/
def boolToPM1 (b : Bool) : ℝ := if b then 1 else -1

@[simp] theorem boolToPM1_true : boolToPM1 true = 1 := rfl
@[simp] theorem boolToPM1_false : boolToPM1 false = -1 := rfl

theorem boolToPM1_not (b : Bool) : boolToPM1 (!b) = -boolToPM1 b := by
  cases b <;> norm_num

/-- Signed coordinate permutation action on Boolean hypercube inputs `Fin n → Bool`. -/
def actBool {n : Nat} (σ : SignedPerm n) (x : Fin n → Bool) : Fin n → Bool :=
  fun i => xor (σ.sgn i) (x (σ.invFun i))

@[simp]
theorem actBool_left_inv {n : Nat} (σ : SignedPerm n) (x : Fin n → Bool) :
    actBool (SignedPerm.inv σ) (actBool σ x) = x := by
  funext j
  simp only [actBool, SignedPerm.inv, σ.left_inv]
  cases σ.sgn (σ.toFun j) <;> cases x j <;> rfl

@[simp]
theorem actBool_right_inv {n : Nat} (σ : SignedPerm n) (x : Fin n → Bool) :
    actBool σ (actBool (SignedPerm.inv σ) x) = x := by
  funext i
  simp only [actBool, SignedPerm.inv, σ.right_inv]
  cases σ.sgn i <;> cases x i <;> rfl

def actBoolEquiv {n : Nat} (σ : SignedPerm n) : (Fin n → Bool) ≃ (Fin n → Bool) where
  toFun := actBool σ
  invFun := actBool (SignedPerm.inv σ)
  left_inv := actBool_left_inv σ
  right_inv := actBool_right_inv σ

/-- Input symmetry `σ` of Boolean target `g`, allowing output negation (`outFlip = true`). -/
def IsTargetSymmetry {n : Nat} (g : (Fin n → Bool) → Bool) (σ : SignedPerm n) (outFlip : Bool) : Prop :=
  ∀ x, g (actBool σ x) = xor outFlip (g x)

private def liftBlockTo {n H : Nat} (σ : SignedPerm n) :
    (Fin H × Fin n) ⊕ (Fin H ⊕ (Fin H ⊕ Unit)) → (Fin H × Fin n) ⊕ (Fin H ⊕ (Fin H ⊕ Unit))
  | Sum.inl (h, j) => Sum.inl (h, σ.toFun j)
  | Sum.inr x => Sum.inr x

private def liftBlockInv {n H : Nat} (σ : SignedPerm n) :
    (Fin H × Fin n) ⊕ (Fin H ⊕ (Fin H ⊕ Unit)) → (Fin H × Fin n) ⊕ (Fin H ⊕ (Fin H ⊕ Unit))
  | Sum.inl (h, j) => Sum.inl (h, σ.invFun j)
  | Sum.inr x => Sum.inr x

private def liftBlockSgn {n H : Nat} (σ : SignedPerm n) (outFlip : Bool) :
    (Fin H × Fin n) ⊕ (Fin H ⊕ (Fin H ⊕ Unit)) → Bool
  | Sum.inl (_, j) => σ.sgn j
  | Sum.inr (Sum.inl _) => false
  | Sum.inr (Sum.inr (Sum.inl _)) => outFlip
  | Sum.inr (Sum.inr (Sum.inr ())) => outFlip

private theorem liftBlock_left_inv {n H : Nat} (σ : SignedPerm n) :
    ∀ u, @liftBlockInv n H σ (liftBlockTo σ u) = u
  | Sum.inl (h, j) => by simp [liftBlockTo, liftBlockInv, σ.left_inv]
  | Sum.inr _ => rfl

private theorem liftBlock_right_inv {n H : Nat} (σ : SignedPerm n) :
    ∀ u, @liftBlockTo n H σ (liftBlockInv σ u) = u
  | Sum.inl (h, j) => by simp [liftBlockTo, liftBlockInv, σ.right_inv]
  | Sum.inr _ => rfl

/-- Lift an input signed permutation `(σ, outFlip)` to parameter space `Fin (paramDim n H)`. -/
def liftSignedPerm (n H : Nat) (σ : SignedPerm n) (outFlip : Bool) : SignedPerm (paramDim n H) where
  toFun i := paramBlockEquiv n H (liftBlockTo σ ((paramBlockEquiv n H).symm i))
  invFun i := paramBlockEquiv n H (liftBlockInv σ ((paramBlockEquiv n H).symm i))
  left_inv i := by simp [liftBlock_left_inv]
  right_inv i := by simp [liftBlock_right_inv]
  sgn i := liftBlockSgn σ outFlip ((paramBlockEquiv n H).symm i)

@[simp]
theorem w1_actParam {n H : Nat} (σ : SignedPerm n) (outFlip : Bool)
    (θ : TwoLayerParams n H) (h : Fin H) (j : Fin n) :
    w1 (actRealVec (liftSignedPerm n H σ outFlip) θ) h j =
      if σ.sgn j then -(w1 θ h (σ.invFun j)) else w1 θ h (σ.invFun j) := by
  simp [w1, actRealVec, liftSignedPerm, idxW1, liftBlockInv, liftBlockSgn]

@[simp]
theorem b1_actParam {n H : Nat} (σ : SignedPerm n) (outFlip : Bool)
    (θ : TwoLayerParams n H) (h : Fin H) :
    b1 (actRealVec (liftSignedPerm n H σ outFlip) θ) h = b1 θ h := by
  simp [b1, actRealVec, liftSignedPerm, idxB1, liftBlockInv, liftBlockSgn]

@[simp]
theorem w2_actParam {n H : Nat} (σ : SignedPerm n) (outFlip : Bool)
    (θ : TwoLayerParams n H) (h : Fin H) :
    w2 (actRealVec (liftSignedPerm n H σ outFlip) θ) h =
      if outFlip then -(w2 θ h) else w2 θ h := by
  simp [w2, actRealVec, liftSignedPerm, idxW2, liftBlockInv, liftBlockSgn]

@[simp]
theorem b2_actParam {n H : Nat} (σ : SignedPerm n) (outFlip : Bool)
    (θ : TwoLayerParams n H) :
    b2 (actRealVec (liftSignedPerm n H σ outFlip) θ) =
      if outFlip then -(b2 θ) else b2 θ := by
  simp [b2, actRealVec, liftSignedPerm, idxB2, liftBlockInv, liftBlockSgn]

/-- Hidden pre-activation of neuron `h` on Boolean input `x` encoded in `{−1, +1}^n`. -/
def preAct {n H : Nat} (θ : TwoLayerParams n H) (h : Fin H) (x : Fin n → Bool) : ℝ :=
  (∑ j : Fin n, w1 θ h j * boolToPM1 (x j)) + b1 θ h

/-- Output logit of the two-layer network with activation `φ : ℝ → ℝ`. -/
def logit {n H : Nat} (φ : ℝ → ℝ) (θ : TwoLayerParams n H) (x : Fin n → Bool) : ℝ :=
  (∑ h : Fin H, w2 θ h * φ (preAct θ h x)) + b2 θ

/-- Per-example logistic loss for binary target `y ∈ {false, true}` mapped to `{−1, +1}`. -/
def logisticSampleLoss (y : Bool) (z : ℝ) : ℝ :=
  Real.log (1 + Real.exp (-(boolToPM1 y * z)))

/-- Normalized full-batch logistic loss over all `2^n` Boolean inputs. -/
def logisticLoss {n H : Nat} (φ : ℝ → ℝ) (g : (Fin n → Bool) → Bool)
    (θ : TwoLayerParams n H) : ℝ :=
  ((Fintype.card (Fin n → Bool) : ℝ)⁻¹) *
    ∑ x : Fin n → Bool, logisticSampleLoss (g x) (logit φ θ x)

@[simp]
theorem preAct_actParam {n H : Nat} (σ : SignedPerm n) (outFlip : Bool)
    (θ : TwoLayerParams n H) (h : Fin H) (x : Fin n → Bool) :
    preAct (actRealVec (liftSignedPerm n H σ outFlip) θ) h (actBool σ x) = preAct θ h x := by
  unfold preAct
  rw [b1_actParam]
  congr 1
  have hterm : ∀ j : Fin n,
      w1 (actRealVec (liftSignedPerm n H σ outFlip) θ) h j * boolToPM1 (actBool σ x j) =
        w1 θ h (σ.invFun j) * boolToPM1 (x (σ.invFun j)) := by
    intro j
    rw [w1_actParam, actBool]
    cases hs : σ.sgn j <;> cases hx : x (σ.invFun j) <;> simp [hs, hx, boolToPM1]
  rw [Finset.sum_congr rfl fun j _ => hterm j]
  exact Fintype.sum_equiv σ.toEquiv.symm _ _ fun j => rfl

@[simp]
theorem logit_actParam {n H : Nat} (φ : ℝ → ℝ) (σ : SignedPerm n) (outFlip : Bool)
    (θ : TwoLayerParams n H) (x : Fin n → Bool) :
    logit φ (actRealVec (liftSignedPerm n H σ outFlip) θ) (actBool σ x) =
      if outFlip then -(logit φ θ x) else logit φ θ x := by
  unfold logit
  simp_rw [preAct_actParam, w2_actParam, b2_actParam]
  cases outFlip
  · simp
  · simp [Finset.sum_neg_distrib, neg_add_rev, add_comm]

theorem logisticSampleLoss_xor (outFlip y : Bool) (z : ℝ) :
    logisticSampleLoss (xor outFlip y) (if outFlip then -z else z) = logisticSampleLoss y z := by
  cases outFlip <;> cases y <;> simp [logisticSampleLoss, boolToPM1]

/-- **Step (ii) of Theorem 15**: For ANY activation `φ`, the full-batch logistic loss is
    strictly invariant under `liftSignedPerm n H σ outFlip` whenever `σ` is a symmetry of `g`. -/
theorem logisticLoss_invariant {n H : Nat} (φ : ℝ → ℝ)
    (g : (Fin n → Bool) → Bool) (σ : SignedPerm n) (outFlip : Bool)
    (hSym : IsTargetSymmetry g σ outFlip) (θ : TwoLayerParams n H) :
    logisticLoss φ g (actRealVec (liftSignedPerm n H σ outFlip) θ) = logisticLoss φ g θ := by
  unfold logisticLoss
  congr 1
  refine Fintype.sum_equiv (actBoolEquiv σ).symm _ _ fun x => ?_
  have hx : actBool σ ((actBoolEquiv σ).symm x) = x := actBool_right_inv σ x
  have h1 : logisticSampleLoss (g (actBool σ ((actBoolEquiv σ).symm x)))
      (logit φ (actRealVec (liftSignedPerm n H σ outFlip) θ) (actBool σ ((actBoolEquiv σ).symm x))) =
      logisticSampleLoss (g ((actBoolEquiv σ).symm x)) (logit φ θ ((actBoolEquiv σ).symm x)) := by
    rw [hSym, logit_actParam, logisticSampleLoss_xor]
  simpa [actBoolEquiv, hx] using h1

/-- Hidden-unit sign-flip symmetry: negating neuron `h0`'s `(W1[h0], b1[h0], W2[h0])` preserves
    `logit` and `logisticLoss` whenever `φ` is odd (`∀ z, φ (-z) = -φ z`). -/
private def hiddenFlipSgn {n H : Nat} (h0 : Fin H) :
    (Fin H × Fin n) ⊕ (Fin H ⊕ (Fin H ⊕ Unit)) → Bool
  | Sum.inl (h, _) => decide (h = h0)
  | Sum.inr (Sum.inl h) => decide (h = h0)
  | Sum.inr (Sum.inr (Sum.inl h)) => decide (h = h0)
  | Sum.inr (Sum.inr (Sum.inr ())) => false

def hiddenFlipSignedPerm (n H : Nat) (h0 : Fin H) : SignedPerm (paramDim n H) where
  toFun := id
  invFun := id
  left_inv _ := rfl
  right_inv _ := rfl
  sgn i := hiddenFlipSgn h0 ((paramBlockEquiv n H).symm i)

theorem hiddenFlip_logisticLoss_invariant {n H : Nat} (φ : ℝ → ℝ)
    (hOdd : ∀ z, φ (-z) = -φ z) (g : (Fin n → Bool) → Bool)
    (h0 : Fin H) (θ : TwoLayerParams n H) :
    logisticLoss φ g (actRealVec (hiddenFlipSignedPerm n H h0) θ) = logisticLoss φ g θ := by
  unfold logisticLoss
  congr 1
  refine Finset.sum_congr rfl fun x _ => ?_
  congr 1
  unfold logit
  have hb2 : b2 (actRealVec (hiddenFlipSignedPerm n H h0) θ) = b2 θ := by
    simp [b2, actRealVec, hiddenFlipSignedPerm, idxB2, hiddenFlipSgn]
  rw [hb2]
  congr 1
  refine Finset.sum_congr rfl fun h _ => ?_
  have hw2 : w2 (actRealVec (hiddenFlipSignedPerm n H h0) θ) h =
      if h = h0 then -(w2 θ h) else w2 θ h := by
    simp [w2, actRealVec, hiddenFlipSignedPerm, idxW2, hiddenFlipSgn]
  have hp : preAct (actRealVec (hiddenFlipSignedPerm n H h0) θ) h x =
      if h = h0 then -(preAct θ h x) else preAct θ h x := by
    unfold preAct
    have hb1 : b1 (actRealVec (hiddenFlipSignedPerm n H h0) θ) h =
        if h = h0 then -(b1 θ h) else b1 θ h := by
      simp [b1, actRealVec, hiddenFlipSignedPerm, idxB1, hiddenFlipSgn]
    have hw1 : ∀ j, w1 (actRealVec (hiddenFlipSignedPerm n H h0) θ) h j =
        if h = h0 then -(w1 θ h j) else w1 θ h j := by
      intro j
      simp [w1, actRealVec, hiddenFlipSignedPerm, idxW1, hiddenFlipSgn]
    by_cases heq : h = h0
    · subst heq
      simp only [↓reduceIte] at hb1 hw1 ⊢
      rw [hb1]
      have hsum : (∑ j : Fin n, w1 (actRealVec (hiddenFlipSignedPerm n H h) θ) h j * boolToPM1 (x j)) =
          -(∑ j : Fin n, w1 θ h j * boolToPM1 (x j)) := by
        rw [← Finset.sum_neg_distrib]
        refine Finset.sum_congr rfl fun j _ => ?_
        rw [hw1 j, neg_mul]
      rw [hsum]
      ring
    · simp only [heq, ↓reduceIte] at hb1 hw1 ⊢
      rw [hb1]
      congr 1
      refine Finset.sum_congr rfl fun j _ => ?_
      rw [hw1 j]
  by_cases heq : h = h0
  · subst heq
    simp [hw2, hp, hOdd]
  · simp [hw2, hp, heq]

/-- **True analytic coordinatewise gradient** of `L : (Fin d → ℝ) → ℝ` using Mathlib's `deriv`. -/
def trueGrad {d : Nat} (L : (Fin d → ℝ) → ℝ) (θ : Fin d → ℝ) : Fin d → ℝ :=
  fun i => deriv (fun t : ℝ => L (Function.update θ i t)) (θ i)

private theorem update_actRealVec {d : Nat} (σ : SignedPerm d) (θ : Fin d → ℝ)
    (i : Fin d) (t : ℝ) :
    Function.update (actRealVec σ θ) i t =
      actRealVec σ (Function.update θ (σ.invFun i) (if σ.sgn i then -t else t)) := by
  funext k
  by_cases hki : k = i
  · subst hki
    simp [actRealVec]
    cases σ.sgn k <;> simp
  · have hinv : σ.invFun k ≠ σ.invFun i := fun h => hki (by simpa [σ.right_inv] using congrArg σ.toFun h)
    simp [Function.update, hki, hinv, actRealVec]

/-- Unconditional equivariance of the true analytic gradient `trueGrad L` for any `σ`-invariant
    scalar loss `L`, proved via Mathlib's unconditional `deriv_comp_neg`. -/
theorem trueGrad_equivariant {d : Nat} (L : (Fin d → ℝ) → ℝ) (σ : SignedPerm d)
    (hLinv : ∀ θ, L (actRealVec σ θ) = L θ) (θ : Fin d → ℝ) :
    trueGrad L (actRealVec σ θ) = actRealVec σ (trueGrad L θ) := by
  funext i
  have hfun : (fun t : ℝ => L (Function.update (actRealVec σ θ) i t)) =
      fun t : ℝ => L (Function.update θ (σ.invFun i) (if σ.sgn i then -t else t)) := by
    funext t
    rw [update_actRealVec σ θ i t, hLinv]
  simp only [trueGrad, actRealVec]
  rw [hfun]
  cases hs : σ.sgn i
  · simp [hs]
  · simp only [hs, ↓reduceIte]
    simpa [hs] using (deriv_comp_neg (f := fun u => L (Function.update θ (σ.invFun i) u))
      (x := -(θ (σ.invFun i))))

/-- Explicit analytic coordinate partial derivatives and backpropagation gradient for `logisticLoss`. -/
def dPreAct {n H : Nat} (h : Fin H) (x : Fin n → Bool) (i : Fin (paramDim n H)) : ℝ :=
  match (paramBlockEquiv n H).symm i with
  | Sum.inl (h', j) => if h' = h then boolToPM1 (x j) else 0
  | Sum.inr (Sum.inl h') => if h' = h then 1 else 0
  | _ => 0

def dLogit {n H : Nat} (φ φ' : ℝ → ℝ) (θ : TwoLayerParams n H)
    (x : Fin n → Bool) (i : Fin (paramDim n H)) : ℝ :=
  (∑ h : Fin H,
    ((if i = idxW2 h then φ (preAct θ h x) else 0) +
      w2 θ h * (φ' (preAct θ h x) * dPreAct h x i))) +
  (if i = idxB2 then 1 else 0)

def dLogisticSampleLoss (y : Bool) (z dz : ℝ) : ℝ :=
  let s := boolToPM1 y
  (Real.exp (-(s * z)) / (1 + Real.exp (-(s * z)))) * (-(s * dz))

def explicitGrad {n H : Nat} (φ φ' : ℝ → ℝ) (g : (Fin n → Bool) → Bool)
    (θ : TwoLayerParams n H) : TwoLayerParams n H :=
  fun i => ((Fintype.card (Fin n → Bool) : ℝ)⁻¹) *
    ∑ x : Fin n → Bool, dLogisticSampleLoss (g x) (logit φ θ x) (dLogit φ φ' θ x i)

private theorem hasDerivAt_coord_apply {d : Nat} (θ : Fin d → ℝ) (i k : Fin d) :
    HasDerivAt (fun t : ℝ => Function.update θ i t k) (if k = i then 1 else 0) (θ i) := by
  by_cases h : k = i
  · subst h
    simpa using (hasDerivAt_id (θ k))
  · simpa [Function.update, h] using (hasDerivAt_const (θ i) (θ k))

private theorem hasDerivAt_preAct {n H : Nat} (θ : TwoLayerParams n H) (h : Fin H)
    (x : Fin n → Bool) (i : Fin (paramDim n H)) :
    HasDerivAt (fun t => preAct (Function.update θ i t) h x) (dPreAct h x i) (θ i) := by
  unfold preAct w1 b1 dPreAct
  have hsum : HasDerivAt
      (fun t => ∑ j : Fin n, Function.update θ i t (idxW1 h j) * boolToPM1 (x j))
      (∑ j : Fin n, (if idxW1 h j = i then (1 : ℝ) else 0) * boolToPM1 (x j)) (θ i) :=
    HasDerivAt.sum fun j _ => (hasDerivAt_coord_apply θ i (idxW1 h j)).mul_const _
  have hder := hsum.add (hasDerivAt_coord_apply θ i (idxB1 h))
  convert hder using 1
  cases hsym : (paramBlockEquiv n H).symm i with
  | inl hj =>
      rcases hj with ⟨h', j'⟩
      have hi : i = idxW1 h' j' := by
        simpa [idxW1] using (paramBlockEquiv n H).apply_symm_apply i |>.symm |>.trans
          (congrArg (paramBlockEquiv n H) hsym)
      subst hi
      have hjb1 : ∀ k, idxW1 h k = idxW1 h' j' ↔ (h = h' ∧ k = j') := by
        intro k
        simp [idxW1, (paramBlockEquiv n H).injective.eq_iff]
      have hb1 : idxB1 h ≠ idxW1 h' j' := by
        simp [idxB1, idxW1, (paramBlockEquiv n H).injective.eq_iff]
      simp only [hb1, ↓reduceIte, add_zero]
      by_cases hh : h' = h
      · subst hh
        rw [Finset.sum_eq_single j']
        · simp [hjb1]
        · intro k _ hk
          simp [hjb1, hk]
        · intro hmem
          exact (hmem (Finset.mem_univ j')).elim
      · have hzero : ∀ k : Fin n, idxW1 h k ≠ idxW1 h' j' := fun k hk =>
            hh ((hjb1 k).mp hk).1.symm
        simp [hzero, hh]
  | inr r =>
      rcases r with h' | r'
      · have hi : i = idxB1 h' := by
          simpa [idxB1] using (paramBlockEquiv n H).apply_symm_apply i |>.symm |>.trans
            (congrArg (paramBlockEquiv n H) hsym)
        subst hi
        have hw1ne : ∀ k : Fin n, @idxW1 n H h k ≠ idxB1 h' := by
          intro k
          simp [idxW1, idxB1, (paramBlockEquiv n H).injective.eq_iff]
        have hb1eq : @idxB1 n H h = idxB1 h' ↔ h' = h := by
          simp [idxB1, (paramBlockEquiv n H).injective.eq_iff, eq_comm]
        simp [hw1ne, hb1eq]
      · rcases r' with h' | ⟨⟩
        · have hi : i = idxW2 h' := by
            simpa [idxW2] using (paramBlockEquiv n H).apply_symm_apply i |>.symm |>.trans
              (congrArg (paramBlockEquiv n H) hsym)
          subst hi
          simp [idxW1, idxB1, idxW2, (paramBlockEquiv n H).injective.eq_iff]
        · have hi : i = idxB2 := by
            simpa [idxB2] using (paramBlockEquiv n H).apply_symm_apply i |>.symm |>.trans
              (congrArg (paramBlockEquiv n H) hsym)
          subst hi
          simp [idxW1, idxB1, idxB2, (paramBlockEquiv n H).injective.eq_iff]

private theorem hasDerivAt_logit {n H : Nat} (φ φ' : ℝ → ℝ)
    (hφd : ∀ z, HasDerivAt φ (φ' z) z)
    (θ : TwoLayerParams n H) (x : Fin n → Bool) (i : Fin (paramDim n H)) :
    HasDerivAt (fun t => logit φ (Function.update θ i t) x) (dLogit φ φ' θ x i) (θ i) := by
  unfold logit w2 b2 dLogit
  have hsum : HasDerivAt
      (fun t => ∑ h : Fin H, Function.update θ i t (idxW2 h) * φ (preAct (Function.update θ i t) h x))
      (∑ h : Fin H,
        ((if idxW2 h = i then 1 else 0) * φ (preAct θ h x) +
          θ (idxW2 h) * (φ' (preAct θ h x) * dPreAct h x i))) (θ i) := by
    refine HasDerivAt.sum fun h _ => ?_
    have hw := hasDerivAt_coord_apply θ i (idxW2 h)
    have hpre := hasDerivAt_preAct θ h x i
    have hcomp : HasDerivAt (fun t => φ (preAct (Function.update θ i t) h x))
        (φ' (preAct θ h x) * dPreAct h x i) (θ i) := by
      have hc := (hφd (preAct (Function.update θ i (θ i)) h x)).comp (θ i) hpre
      simpa [Function.update_eq_self] using hc
    have hprod := hw.mul hcomp
    rw [Function.update_eq_self] at hprod
    exact hprod
  have htot := hsum.add (hasDerivAt_coord_apply θ i idxB2)
  convert htot using 2
  · simp [eq_comm, w2]
  · simp [eq_comm]

private theorem hasDerivAt_logisticSampleLoss {y : Bool} {f : ℝ → ℝ} {z dz t0 : ℝ}
    (hf : HasDerivAt f dz t0) (hf0 : f t0 = z) :
    HasDerivAt (fun t => logisticSampleLoss y (f t)) (dLogisticSampleLoss y z dz) t0 := by
  unfold logisticSampleLoss dLogisticSampleLoss
  let s := boolToPM1 y
  have hinner : HasDerivAt (fun t => -(s * f t)) (-(s * dz)) t0 := by
    simpa using (hf.const_mul s).neg
  have hexp : HasDerivAt (fun t => Real.exp (-(s * f t)))
      (Real.exp (-(s * z)) * (-(s * dz))) t0 := by
    simpa [hf0] using (Real.hasDerivAt_exp (-(s * f t0))).comp t0 hinner
  have h1p : HasDerivAt (fun t => 1 + Real.exp (-(s * f t)))
      (Real.exp (-(s * z)) * (-(s * dz))) t0 := by
    simpa using (hasDerivAt_const t0 (1 : ℝ)).add hexp
  have hpos : 1 + Real.exp (-(s * f t0)) ≠ 0 := ne_of_gt (by positivity)
  have hlog : HasDerivAt (fun t => Real.log (1 + Real.exp (-(s * f t))))
      ((Real.exp (-(s * z)) * (-(s * dz))) / (1 + Real.exp (-(s * z)))) t0 := by
    have h1 := (Real.hasDerivAt_log hpos).comp t0 h1p
    simpa [hf0, div_eq_mul_inv, mul_comm, mul_left_comm, mul_assoc] using h1
  convert hlog using 1
  ring

theorem hasDerivAt_logisticLoss_coord {n H : Nat} (φ φ' : ℝ → ℝ)
    (hφd : ∀ z, HasDerivAt φ (φ' z) z) (g : (Fin n → Bool) → Bool)
    (θ : TwoLayerParams n H) (i : Fin (paramDim n H)) :
    HasDerivAt (fun t => logisticLoss φ g (Function.update θ i t))
      (explicitGrad φ φ' g θ i) (θ i) := by
  unfold logisticLoss explicitGrad
  refine (HasDerivAt.sum fun x _ => ?_).const_mul _
  exact hasDerivAt_logisticSampleLoss (hasDerivAt_logit φ φ' hφd θ x i)
    (congrArg (fun p => logit φ p x) (Function.update_eq_self i θ))

/-- Exact equality between `trueGrad (logisticLoss φ g)` and the closed-form backprop gradient
    `explicitGrad φ φ' g`. -/
theorem trueGrad_logisticLoss_eq_explicitGrad {n H : Nat} (φ φ' : ℝ → ℝ)
    (hφd : ∀ z, HasDerivAt φ (φ' z) z) (g : (Fin n → Bool) → Bool) :
    trueGrad (@logisticLoss n H φ g) = explicitGrad φ φ' g := by
  funext θ i
  exact (hasDerivAt_logisticLoss_coord φ φ' hφd g θ i).deriv

/-- Borel measurability of the true analytic gradient of `logisticLoss`. -/
theorem measurable_preAct {n H : Nat} (h : Fin H) (x : Fin n → Bool) :
    Measurable fun θ : TwoLayerParams n H => preAct θ h x := by
  unfold preAct w1 b1
  exact (Finset.measurable_sum _ fun j _ =>
    (measurable_pi_apply (idxW1 h j)).mul_const _).add (measurable_pi_apply (idxB1 h))

theorem measurable_logit {n H : Nat} {φ : ℝ → ℝ} (hφm : Measurable φ) (x : Fin n → Bool) :
    Measurable fun θ : TwoLayerParams n H => logit φ θ x := by
  unfold logit w2 b2
  exact (Finset.measurable_sum _ fun h _ =>
    (measurable_pi_apply (idxW2 h)).mul (hφm.comp (measurable_preAct h x))).add
      (measurable_pi_apply idxB2)

theorem measurable_explicitGrad {n H : Nat} {φ φ' : ℝ → ℝ}
    (hφm : Measurable φ) (hφ'm : Measurable φ') (g : (Fin n → Bool) → Bool) :
    Measurable (explicitGrad φ φ' g : TwoLayerParams n H → TwoLayerParams n H) := by
  refine measurable_pi_lambda _ fun i => ?_
  unfold explicitGrad dLogisticSampleLoss dLogit w2
  refine (Finset.measurable_sum _ fun x _ => ?_).const_mul _
  have hlog : Measurable fun θ : TwoLayerParams n H => logit φ θ x := measurable_logit hφm x
  have hdlog : Measurable fun θ : TwoLayerParams n H =>
      (∑ h : Fin H,
        ((if i = idxW2 h then φ (preAct θ h x) else 0) +
          θ (idxW2 h) * (φ' (preAct θ h x) * dPreAct h x i))) +
      (if i = idxB2 then 1 else 0) := by
    refine (Finset.measurable_sum _ fun h _ => ?_).add measurable_const
    have hpre : Measurable fun θ : TwoLayerParams n H => preAct θ h x := measurable_preAct h x
    have hterm1 : Measurable fun θ : TwoLayerParams n H =>
        if i = idxW2 h then φ (preAct θ h x) else (0 : ℝ) := by
      by_cases hi : i = idxW2 h
      · simp only [hi, ↓reduceIte]
        exact hφm.comp hpre
      · simp only [hi, ↓reduceIte]
        exact measurable_const
    exact hterm1.add ((measurable_pi_apply (idxW2 h)).mul ((hφ'm.comp hpre).mul_const _))
  have hexp : Measurable fun θ : TwoLayerParams n H => Real.exp (-(boolToPM1 (g x) * logit φ θ x)) :=
    Real.measurable_exp.comp ((hlog.const_mul _).neg)
  exact ((hexp.div (hexp.const_add 1)).mul ((hdlog.const_mul _).neg))

theorem measurable_trueGrad_logisticLoss {n H : Nat} {φ φ' : ℝ → ℝ}
    (hφd : ∀ z, HasDerivAt φ (φ' z) z) (hφm : Measurable φ) (hφ'm : Measurable φ')
    (g : (Fin n → Bool) → Bool) :
    Measurable (trueGrad (@logisticLoss n H φ g) : TwoLayerParams n H → TwoLayerParams n H) := by
  rw [trueGrad_logisticLoss_eq_explicitGrad φ φ' hφd g]
  exact measurable_explicitGrad hφm hφ'm g

/-- Concrete smooth odd activation `tanh x = sinh x / cosh x` with derivative `sech² x`. -/
def tanhReal (x : ℝ) : ℝ := Real.sinh x / Real.cosh x
def tanhRealDeriv (x : ℝ) : ℝ := 1 / Real.cosh x ^ 2

theorem tanhReal_odd (x : ℝ) : tanhReal (-x) = -tanhReal x := by
  simp [tanhReal, Real.sinh_neg, Real.cosh_neg, neg_div]

theorem hasDerivAt_tanhReal (x : ℝ) : HasDerivAt tanhReal (tanhRealDeriv x) x := by
  unfold tanhReal tanhRealDeriv
  have hc : Real.cosh x ≠ 0 := ne_of_gt (Real.cosh_pos x)
  have hd := (Real.hasDerivAt_sinh x).div (Real.hasDerivAt_cosh x) hc
  convert hd using 1
  have hsq : Real.cosh x ^ 2 - Real.sinh x ^ 2 = 1 := Real.cosh_sq_sub_sinh_sq x
  field_simp [hc]
  linarith [hsq]

theorem measurable_tanhReal : Measurable tanhReal :=
  Real.measurable_sinh.div Real.measurable_cosh

theorem measurable_tanhRealDeriv : Measurable tanhRealDeriv :=
  measurable_const.div (Real.measurable_cosh.pow_const 2)

/-- Full-batch gradient descent with decoupled weight decay `wd` on `Fin d → ℝ`. -/
def gdStepReal {d : Nat} (grad : (Fin d → ℝ) → (Fin d → ℝ)) (lr wd : ℝ)
    (θ : Fin d → ℝ) : Fin d → ℝ :=
  fun i => θ i - lr * (grad θ i + wd * θ i)

theorem gdStepReal_equivariant {d : Nat} (grad : (Fin d → ℝ) → (Fin d → ℝ))
    (lr wd : ℝ) (σ : SignedPerm d)
    (hgeq : ∀ θ, grad (actRealVec σ θ) = actRealVec σ (grad θ)) (θ : Fin d → ℝ) :
    gdStepReal grad lr wd (actRealVec σ θ) = actRealVec σ (gdStepReal grad lr wd θ) := by
  funext i
  simp only [gdStepReal, hgeq, actRealVec]
  cases hs : σ.sgn i
  · simp [hs]
  · simp [hs]; ring

theorem measurable_gdStepReal {d : Nat} (grad : (Fin d → ℝ) → (Fin d → ℝ))
    (hgm : Measurable grad) (lr wd : ℝ) :
    Measurable (gdStepReal grad lr wd) := by
  refine measurable_pi_lambda _ fun i => ?_
  exact (measurable_pi_apply i).sub
    (measurable_const.mul (((measurable_pi_apply i).comp hgm).add (measurable_const.mul (measurable_pi_apply i))))

def runGDSchedule {d : Nat} (grad : (Fin d → ℝ) → (Fin d → ℝ))
    (sched : Nat → ℝ × ℝ) : Nat → (Fin d → ℝ) → (Fin d → ℝ)
  | 0, θ => θ
  | t + 1, θ => gdStepReal grad (sched t).1 (sched t).2 (runGDSchedule grad sched t θ)

theorem runGDSchedule_equivariant {d : Nat} (grad : (Fin d → ℝ) → (Fin d → ℝ))
    (sched : Nat → ℝ × ℝ) (σ : SignedPerm d)
    (hgeq : ∀ θ, grad (actRealVec σ θ) = actRealVec σ (grad θ)) :
    ∀ t θ, runGDSchedule grad sched t (actRealVec σ θ) =
      actRealVec σ (runGDSchedule grad sched t θ)
  | 0, _ => rfl
  | t + 1, θ => by
      simp only [runGDSchedule]
      rw [runGDSchedule_equivariant grad sched σ hgeq t θ,
        gdStepReal_equivariant grad (sched t).1 (sched t).2 σ hgeq]

theorem measurable_runGDSchedule {d : Nat} (grad : (Fin d → ℝ) → (Fin d → ℝ))
    (hgm : Measurable grad) (sched : Nat → ℝ × ℝ) :
    ∀ t, Measurable (runGDSchedule grad sched t)
  | 0 => measurable_id
  | t + 1 => (measurable_gdStepReal grad hgm (sched t).1 (sched t).2).comp
      (measurable_runGDSchedule grad hgm sched t)

/-- AdamW hyperparameters + bias-correction reciprocals per step on `ℝ`. -/
structure AdamWCfgReal where
  lr : ℝ
  beta1 : ℝ
  beta2 : ℝ
  eps : ℝ
  wd : ℝ
  invOneMinusB1 : ℝ
  invOneMinusB2 : ℝ

abbrev AdamWState (d : Nat) := (Fin d → ℝ) × (Fin d → ℝ) × (Fin d → ℝ)

def permRealVec {d : Nat} (σ : SignedPerm d) (v : Fin d → ℝ) : Fin d → ℝ :=
  fun i => v (σ.invFun i)

def actAdamWState {d : Nat} (σ : SignedPerm d) (st : AdamWState d) : AdamWState d :=
  (actRealVec σ st.1, actRealVec σ st.2.1, permRealVec σ st.2.2)

def adamwStepReal {d : Nat} (grad : (Fin d → ℝ) → (Fin d → ℝ)) (cfg : AdamWCfgReal)
    (st : AdamWState d) : AdamWState d :=
  let θ := st.1
  let m := st.2.1
  let v := st.2.2
  let g := grad θ
  let m' : Fin d → ℝ := fun i => cfg.beta1 * m i + (1 - cfg.beta1) * g i
  let v' : Fin d → ℝ := fun i => cfg.beta2 * v i + (1 - cfg.beta2) * g i ^ 2
  let θ' : Fin d → ℝ := fun i =>
    θ i - cfg.lr * ((cfg.invOneMinusB1 * m' i) / (Real.sqrt (cfg.invOneMinusB2 * v' i) + cfg.eps) +
      cfg.wd * θ i)
  (θ', m', v')

theorem adamwStepReal_equivariant {d : Nat} (grad : (Fin d → ℝ) → (Fin d → ℝ))
    (cfg : AdamWCfgReal) (σ : SignedPerm d)
    (hgeq : ∀ θ, grad (actRealVec σ θ) = actRealVec σ (grad θ)) (st : AdamWState d) :
    adamwStepReal grad cfg (actAdamWState σ st) = actAdamWState σ (adamwStepReal grad cfg st) := by
  rcases st with ⟨θ, m, v⟩
  ext i
  · simp only [adamwStepReal, actAdamWState, permRealVec, actRealVec, hgeq]
    cases hs : σ.sgn i
    · simp [hs]
    · simp [hs]; ring_nf
  · simp only [adamwStepReal, actAdamWState, actRealVec, hgeq]
    cases hs : σ.sgn i
    · simp [hs]
    · simp [hs]; ring
  · simp only [adamwStepReal, actAdamWState, permRealVec, actRealVec, hgeq]
    cases hs : σ.sgn i <;> simp [hs]

theorem measurable_adamwStepReal {d : Nat} (grad : (Fin d → ℝ) → (Fin d → ℝ))
    (hgm : Measurable grad) (cfg : AdamWCfgReal) :
    Measurable (adamwStepReal grad cfg) := by
  unfold adamwStepReal
  have hm1 : Measurable fun st : AdamWState d => st.1 := measurable_fst
  have hm2 : Measurable fun st : AdamWState d => st.2.1 := measurable_fst.comp measurable_snd
  have hm3 : Measurable fun st : AdamWState d => st.2.2 := measurable_snd.comp measurable_snd
  have hmg : Measurable fun st : AdamWState d => grad st.1 := hgm.comp hm1
  have hm' : Measurable fun st : AdamWState d =>
      fun i => cfg.beta1 * st.2.1 i + (1 - cfg.beta1) * grad st.1 i :=
    measurable_pi_lambda _ fun i =>
      (((measurable_pi_apply i).comp hm2).const_mul _).add
        (((measurable_pi_apply i).comp hmg).const_mul _)
  have hv' : Measurable fun st : AdamWState d =>
      fun i => cfg.beta2 * st.2.2 i + (1 - cfg.beta2) * grad st.1 i ^ 2 :=
    measurable_pi_lambda _ fun i =>
      (((measurable_pi_apply i).comp hm3).const_mul _).add
        ((((measurable_pi_apply i).comp hmg).pow_const 2).const_mul _)
  have hθ' : Measurable fun st : AdamWState d => fun i =>
      st.1 i - cfg.lr *
        ((cfg.invOneMinusB1 * (cfg.beta1 * st.2.1 i + (1 - cfg.beta1) * grad st.1 i)) /
          (Real.sqrt (cfg.invOneMinusB2 * (cfg.beta2 * st.2.2 i + (1 - cfg.beta2) * grad st.1 i ^ 2)) +
            cfg.eps) + cfg.wd * st.1 i) := by
    refine measurable_pi_lambda _ fun i => ?_
    have hmi := (measurable_pi_apply i).comp hm'
    have hvi := (measurable_pi_apply i).comp hv'
    have hθi := (measurable_pi_apply i).comp hm1
    have hnum := hmi.const_mul cfg.invOneMinusB1
    have hden := ((hvi.const_mul cfg.invOneMinusB2).sqrt).add_const cfg.eps
    exact hθi.sub (((hnum.div hden).add (hθi.const_mul cfg.wd)).const_mul cfg.lr)
  exact hθ'.prod_mk (hm'.prod_mk hv')

def runAdamWState {d : Nat} (grad : (Fin d → ℝ) → (Fin d → ℝ))
    (sched : Nat → AdamWCfgReal) : Nat → AdamWState d → AdamWState d
  | 0, st => st
  | t + 1, st => adamwStepReal grad (sched t) (runAdamWState grad sched t st)

/-- Continuous AdamW trajectory initialized at `(θ, 0, 0)` (zero 1st and 2nd moment vectors). -/
def runAdamWSchedule {d : Nat} (grad : (Fin d → ℝ) → (Fin d → ℝ))
    (sched : Nat → AdamWCfgReal) (t : Nat) (θ : Fin d → ℝ) : Fin d → ℝ :=
  (runAdamWState grad sched t (θ, fun _ => 0, fun _ => 0)).1

private theorem actAdamWState_zero {d : Nat} (σ : SignedPerm d) (θ : Fin d → ℝ) :
    actAdamWState σ (θ, fun _ => 0, fun _ => 0) = (actRealVec σ θ, fun _ => 0, fun _ => 0) := by
  ext i <;> simp [actAdamWState, actRealVec, permRealVec]

private theorem runAdamWState_equivariant {d : Nat} (grad : (Fin d → ℝ) → (Fin d → ℝ))
    (sched : Nat → AdamWCfgReal) (σ : SignedPerm d)
    (hgeq : ∀ θ, grad (actRealVec σ θ) = actRealVec σ (grad θ)) :
    ∀ t st, runAdamWState grad sched t (actAdamWState σ st) =
      actAdamWState σ (runAdamWState grad sched t st)
  | 0, _ => rfl
  | t + 1, st => by
      simp only [runAdamWState]
      rw [runAdamWState_equivariant grad sched σ hgeq t st,
        adamwStepReal_equivariant grad (sched t) σ hgeq]

theorem runAdamWSchedule_equivariant {d : Nat} (grad : (Fin d → ℝ) → (Fin d → ℝ))
    (sched : Nat → AdamWCfgReal) (σ : SignedPerm d)
    (hgeq : ∀ θ, grad (actRealVec σ θ) = actRealVec σ (grad θ))
    (t : Nat) (θ : Fin d → ℝ) :
    runAdamWSchedule grad sched t (actRealVec σ θ) =
      actRealVec σ (runAdamWSchedule grad sched t θ) := by
  unfold runAdamWSchedule
  rw [← actAdamWState_zero σ θ, runAdamWState_equivariant grad sched σ hgeq t]
  rfl

theorem measurable_runAdamWState {d : Nat} (grad : (Fin d → ℝ) → (Fin d → ℝ))
    (hgm : Measurable grad) (sched : Nat → AdamWCfgReal) :
    ∀ t, Measurable (runAdamWState grad sched t)
  | 0 => measurable_id
  | t + 1 => (measurable_adamwStepReal grad hgm (sched t)).comp
      (measurable_runAdamWState grad hgm sched t)

theorem measurable_runAdamWSchedule {d : Nat} (grad : (Fin d → ℝ) → (Fin d → ℝ))
    (hgm : Measurable grad) (sched : Nat → AdamWCfgReal) (t : Nat) :
    Measurable (runAdamWSchedule grad sched t) := by
  unfold runAdamWSchedule
  have hinit : Measurable fun θ : Fin d → ℝ => (θ, (fun _ : Fin d => (0 : ℝ)), (fun _ : Fin d => (0 : ℝ))) :=
    measurable_id.prod_mk (measurable_const.prod_mk measurable_const)
  exact measurable_fst.comp ((measurable_runAdamWState grad hgm sched t).comp hinit)

/-- Block-homogeneous symmetric product measure invariance under signed coordinate permutations. -/
theorem blockSymmetricPi_map_actRealVec {d : Nat} (μ : Fin d → Measure ℝ)
    [∀ i, IsProbabilityMeasure (μ i)] (σ : SignedPerm d)
    (hPerm : ∀ i, μ (σ.invFun i) = μ i)
    (hNeg : ∀ i, σ.sgn i = true → (μ i).map Neg.neg = μ i) :
    (Measure.pi μ).map (actRealVec σ) = Measure.pi μ := by
  let e : (Fin d → ℝ) ≃ᵐ (Fin d → ℝ) := actMeasEquiv σ
  change (Measure.pi μ).map e = Measure.pi μ
  refine (Measure.pi_eq fun s hs => ?_).symm
  rw [e.measurableEmbedding.map_apply]
  let s' : Fin d → Set ℝ := fun j =>
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
  have hcoord : ∀ j : Fin d, μ j (s' j) = μ (σ.toFun j) (s (σ.toFun j)) := by
    intro j
    have hmj : μ j = μ (σ.toFun j) := by
      have hp := hPerm (σ.toFun j)
      rw [σ.left_inv] at hp
      exact hp
    dsimp only [s']
    rw [hmj]
    cases h : σ.sgn (σ.toFun j)
    · simp [h]
    · simp only [h, ↓reduceIte]
      rw [← Measure.map_apply measurable_neg (hs (σ.toFun j)), hNeg (σ.toFun j) h]
  calc
    ∏ j : Fin d, μ j (s' j) = ∏ j : Fin d, μ (σ.toFun j) (s (σ.toFun j)) := by
      refine Finset.prod_congr rfl fun j _ => hcoord j
    _ = ∏ i : Fin d, μ i (s i) := by
      refine Finset.prod_equiv σ.toEquiv (fun j => by simp) fun j _ => rfl

theorem dirac_zero_map_neg : (Measure.dirac (0 : ℝ)).map Neg.neg = Measure.dirac 0 := by
  rw [Measure.map_dirac measurable_neg]
  simp

/-- Marginal product prior for the two-layer network: `N(0, vW1)` on `W1`, `N(0, vB1)` on `b1`,
    and symmetric laws `μW2, μb2` on `W2` and `b2` (covering zero-bias Dirac and centered Gaussians). -/
def twoLayerMarginal (n H : Nat) (vW1 vB1 : ℝ≥0) (μW2 μb2 : Measure ℝ) :
    Fin (paramDim n H) → Measure ℝ :=
  fun i => match (paramBlockEquiv n H).symm i with
  | Sum.inl _ => gaussianReal 0 vW1
  | Sum.inr (Sum.inl _) => gaussianReal 0 vB1
  | Sum.inr (Sum.inr (Sum.inl _)) => μW2
  | Sum.inr (Sum.inr (Sum.inr ())) => μb2

instance instIsProbabilityMeasureTwoLayerMarginal (n H : Nat) (vW1 vB1 : ℝ≥0)
    (μW2 μb2 : Measure ℝ) [IsProbabilityMeasure μW2] [IsProbabilityMeasure μb2] :
    ∀ i, IsProbabilityMeasure (twoLayerMarginal n H vW1 vB1 μW2 μb2 i) := by
  intro i
  dsimp only [twoLayerMarginal]
  cases (paramBlockEquiv n H).symm i with
  | inl _ => infer_instance
  | inr r => cases r with
    | inl _ => infer_instance
    | inr r' => cases r' <;> infer_instance

def twoLayerInitMeasure (n H : Nat) (vW1 vB1 : ℝ≥0) (μW2 μb2 : Measure ℝ) :
    Measure (TwoLayerParams n H) :=
  Measure.pi (twoLayerMarginal n H vW1 vB1 μW2 μb2)

instance instIsProbabilityMeasureTwoLayerInitMeasure (n H : Nat) (vW1 vB1 : ℝ≥0)
    (μW2 μb2 : Measure ℝ) [IsProbabilityMeasure μW2] [IsProbabilityMeasure μb2] :
    IsProbabilityMeasure (twoLayerInitMeasure n H vW1 vB1 μW2 μb2) := by
  unfold twoLayerInitMeasure
  infer_instance

theorem twoLayerInitMeasure_invariant (n H : Nat) (vW1 vB1 : ℝ≥0)
    (μW2 μb2 : Measure ℝ) [IsProbabilityMeasure μW2] [IsProbabilityMeasure μb2]
    (hW2 : μW2.map Neg.neg = μW2) (hb2 : μb2.map Neg.neg = μb2)
    (σ : SignedPerm n) (outFlip : Bool) :
    (twoLayerInitMeasure n H vW1 vB1 μW2 μb2).map (actRealVec (liftSignedPerm n H σ outFlip)) =
      twoLayerInitMeasure n H vW1 vB1 μW2 μb2 := by
  refine blockSymmetricPi_map_actRealVec _ (liftSignedPerm n H σ outFlip) ?_ ?_
  · intro i
    dsimp only [twoLayerMarginal, liftSignedPerm]
    rw [(paramBlockEquiv n H).symm_apply_apply]
    cases (paramBlockEquiv n H).symm i with
    | inl hj => simp [liftBlockInv]
    | inr r => cases r with
      | inl _ => simp [liftBlockInv]
      | inr r' => cases r' <;> simp [liftBlockInv]
  · intro i hsgn
    dsimp only [twoLayerMarginal]
    cases hsym : (paramBlockEquiv n H).symm i with
    | inl _ => exact gaussianReal_map_neg vW1
    | inr r => cases r with
      | inl _ =>
          have : (liftSignedPerm n H σ outFlip).sgn i = false := by
            simp [liftSignedPerm, hsym, liftBlockSgn]
          exact absurd hsgn (by simp [this])
      | inr r' => cases r' with
        | inl _ => exact hW2
        | inr _ => exact hb2

/-- **Concrete Spikes 09–14 unoriented threshold-prefix circuit readout**:
    maps trained parameters to the canonical set of unoriented threshold halfspaces `Sym2 (f, !f)`
    in the shortest `|w2|`-ordered prefix of hidden units that determines the Boolean target `g`. -/
abbrev CanonHalfspace (n : Nat) := Sym2 ((Fin n → Bool) → Bool)

structure CircuitOut (n : Nat) where
  val : Option (Finset (CanonHalfspace n))
  deriving DecidableEq

instance instMeasurableSpaceCircuitOut (n : Nat) : MeasurableSpace (CircuitOut n) := ⊤
instance instDiscreteMeasurableSpaceCircuitOut (n : Nat) : DiscreteMeasurableSpace (CircuitOut n) := ⟨fun _ => trivial⟩
instance instMeasurableSingletonClassCircuitOut (n : Nat) : MeasurableSingletonClass (CircuitOut n) :=
  ⟨fun _ => trivial⟩

def actHalfspace {n : Nat} (σ : SignedPerm n) (h : CanonHalfspace n) : CanonHalfspace n :=
  Sym2.map (fun f x => f (actBool (SignedPerm.inv σ) x)) h

def actCircuitOut {n : Nat} (σ : SignedPerm n) (c : CircuitOut n) : CircuitOut n :=
  ⟨c.val.map (Finset.image (actHalfspace σ))⟩

@[simp]
theorem actCircuitOut_left_inv {n : Nat} (σ : SignedPerm n) (c : CircuitOut n) :
    actCircuitOut (SignedPerm.inv σ) (actCircuitOut σ c) = c := by
  rcases c with ⟨v⟩
  cases v with
  | none => rfl
  | some s =>
      simp only [actCircuitOut, Option.map]
      rw [CircuitOut.mk.injEq, Option.some.injEq, Finset.image_image]
      have hinv : ∀ q : CanonHalfspace n, actHalfspace (SignedPerm.inv σ) (actHalfspace σ q) = q := by
        intro q
        dsimp only [actHalfspace]
        rw [← Function.comp_apply (f := Sym2.map _) (g := Sym2.map _), ← Sym2.map_comp]
        have hid : ((fun (f : (Fin n → Bool) → Bool) (x : Fin n → Bool) =>
              f (actBool (SignedPerm.inv (SignedPerm.inv σ)) x)) ∘
            (fun (f : (Fin n → Bool) → Bool) (x : Fin n → Bool) =>
              f (actBool (SignedPerm.inv σ) x))) = id := by
          funext f x
          have hx : actBool (SignedPerm.inv σ) (actBool (SignedPerm.inv (SignedPerm.inv σ)) x) = x := by
            funext k
            simp only [actBool, SignedPerm.inv, σ.left_inv]
            cases σ.sgn (σ.toFun k) <;> cases x k <;> rfl
          exact congrArg f hx
        rw [hid, Sym2.map_id]
        rfl
      ext q
      simp only [Finset.mem_image]
      constructor
      · rintro ⟨y, hy, rfl⟩
        simpa [hinv y] using hy
      · intro hq
        exact ⟨q, hq, hinv q⟩

private def insertBy {α : Type*} (le : α → α → Bool) (a : α) : List α → List α
  | [] => [a]
  | b :: bs => if le a b then a :: b :: bs else b :: insertBy le a bs

private def sortBy {α : Type*} (le : α → α → Bool) : List α → List α
  | [] => []
  | a :: as => insertBy le a (sortBy le as)

private def isDeterminingList {n H : Nat} (g : (Fin n → Bool) → Bool)
    (cells : Fin H → (Fin n → Bool) → Bool) (ks : List (Fin H)) : Bool :=
  decide (∀ x y : Fin n → Bool, (∀ h ∈ ks, cells h x = cells h y) → g x = g y)

private def shortestDetPrefix {n H : Nat} (g : (Fin n → Bool) → Bool)
    (cells : Fin H → (Fin n → Bool) → Bool) :
    List (Fin H) → List (Fin H) → Option (List (Fin H))
  | _, [] => none
  | acc, h :: rest =>
      let acc' := acc ++ [h]
      if isDeterminingList g cells acc' then some acc' else shortestDetPrefix g cells acc' rest

/-- Canonical discrete readout signature separating parameter-dependent computations from
    combinatorial circuit extraction. -/
abbrev ReadoutSig (n H : Nat) := (Fin H → (Fin n → Bool) → Bool) × (Fin H → Fin H → Bool)

def paramReadoutSig {n H : Nat} (θ : TwoLayerParams n H) : ReadoutSig n H :=
  (fun h x => decide (0 ≤ preAct θ h x),
   fun h1 h2 => decide (|w2 θ h1| > |w2 θ h2| ∨ (|w2 θ h1| = |w2 θ h2| ∧ h1.val ≤ h2.val)))

def readoutOfSig {n H : Nat} (g : (Fin n → Bool) → Bool) (sig : ReadoutSig n H) : CircuitOut n :=
  let (cells, rankLe) := sig
  let order := sortBy (fun h1 h2 => rankLe h1 h2) (List.finRange H)
  ⟨(shortestDetPrefix g cells [] order).map fun pref =>
    pref.toFinset.image fun h => s(cells h, fun x => !cells h x)⟩

def concreteCircuitReadout {n H : Nat} (g : (Fin n → Bool) → Bool)
    (θ : TwoLayerParams n H) : CircuitOut n :=
  readoutOfSig g (paramReadoutSig θ)

private theorem isDeterminingList_equivariant {n H : Nat}
    (g : (Fin n → Bool) → Bool) (σ : SignedPerm n) (outFlip : Bool)
    (hSym : IsTargetSymmetry g σ outFlip)
    (cells : Fin H → (Fin n → Bool) → Bool) (ks : List (Fin H)) :
    isDeterminingList g (fun h x => cells h (actBool (SignedPerm.inv σ) x)) ks =
      isDeterminingList g cells ks := by
  unfold isDeterminingList
  refine decide_eq_decide.mpr ?_
  constructor
  · intro hdet x y hxy
    have hxy' : ∀ h ∈ ks, cells h (actBool (SignedPerm.inv σ) (actBool σ x)) =
        cells h (actBool (SignedPerm.inv σ) (actBool σ y)) := by
      intro h hh
      simpa using hxy h hh
    have hg := hdet (actBool σ x) (actBool σ y) hxy'
    rw [hSym x, hSym y] at hg
    cases outFlip <;> cases hx : g x <;> cases hy : g y <;> simp_all
  · intro hdet x y hxy
    have hg := hdet (actBool (SignedPerm.inv σ) x) (actBool (SignedPerm.inv σ) y) hxy
    have hx := hSym (actBool (SignedPerm.inv σ) x)
    have hy := hSym (actBool (SignedPerm.inv σ) y)
    simp only [actBool_right_inv] at hx hy
    rw [hx, hy]
    congr 1

private theorem shortestDetPrefix_equivariant {n H : Nat}
    (g : (Fin n → Bool) → Bool) (σ : SignedPerm n) (outFlip : Bool)
    (hSym : IsTargetSymmetry g σ outFlip)
    (cells : Fin H → (Fin n → Bool) → Bool) (acc rest : List (Fin H)) :
    shortestDetPrefix g (fun h x => cells h (actBool (SignedPerm.inv σ) x)) acc rest =
      shortestDetPrefix g cells acc rest := by
  induction rest generalizing acc with
  | nil => rfl
  | cons h rest ih =>
      simp only [shortestDetPrefix, isDeterminingList_equivariant g σ outFlip hSym cells]
      by_cases hdet : isDeterminingList g cells (acc ++ [h]) = true
      · simp [hdet]
      · simp [hdet, ih]

theorem concreteCircuitReadout_equivariant {n H : Nat} (g : (Fin n → Bool) → Bool)
    (σ : SignedPerm n) (outFlip : Bool) (hSym : IsTargetSymmetry g σ outFlip)
    (θ : TwoLayerParams n H) :
    concreteCircuitReadout g (actRealVec (liftSignedPerm n H σ outFlip) θ) =
      actCircuitOut σ (concreteCircuitReadout g θ) := by
  unfold concreteCircuitReadout paramReadoutSig readoutOfSig actCircuitOut
  have hcells : (fun h x => decide (0 ≤ preAct (actRealVec (liftSignedPerm n H σ outFlip) θ) h x)) =
      fun h x => decide (0 ≤ preAct θ h (actBool (SignedPerm.inv σ) x)) := by
    funext h x
    have hp : preAct (actRealVec (liftSignedPerm n H σ outFlip) θ) h x =
        preAct θ h (actBool (SignedPerm.inv σ) x) := by
      have := preAct_actParam σ outFlip θ h (actBool (SignedPerm.inv σ) x)
      simpa using this
    rw [hp]
  have hrank : (fun h1 h2 => decide
      (|w2 (actRealVec (liftSignedPerm n H σ outFlip) θ) h1| >
        |w2 (actRealVec (liftSignedPerm n H σ outFlip) θ) h2| ∨
      (|w2 (actRealVec (liftSignedPerm n H σ outFlip) θ) h1| =
        |w2 (actRealVec (liftSignedPerm n H σ outFlip) θ) h2| ∧ h1.val ≤ h2.val))) =
      fun h1 h2 => decide
        (|w2 θ h1| > |w2 θ h2| ∨ (|w2 θ h1| = |w2 θ h2| ∧ h1.val ≤ h2.val)) := by
    funext h1 h2
    have h1a : |w2 (actRealVec (liftSignedPerm n H σ outFlip) θ) h1| = |w2 θ h1| := by
      rw [w2_actParam]; cases outFlip <;> simp [abs_neg]
    have h2a : |w2 (actRealVec (liftSignedPerm n H σ outFlip) θ) h2| = |w2 θ h2| := by
      rw [w2_actParam]; cases outFlip <;> simp [abs_neg]
    rw [h1a, h2a]
  rw [hcells, hrank]
  dsimp only
  rw [shortestDetPrefix_equivariant g σ outFlip hSym (fun h x => decide (0 ≤ preAct θ h x))]
  cases shortestDetPrefix g (fun h x => decide (0 ≤ preAct θ h x)) []
      (sortBy _ (List.finRange H)) with
  | none => rfl
  | some pref =>
      simp only [Option.map, CircuitOut.mk.injEq, Option.some.injEq]
      rw [Finset.image_image]
      refine congrArg (fun fn => Finset.image fn pref.toFinset) (funext fun h => ?_)
      rfl

theorem measurable_concreteCircuitReadout {n H : Nat} (g : (Fin n → Bool) → Bool) :
    Measurable (concreteCircuitReadout g : TwoLayerParams n H → CircuitOut n) := by
  have hsig : Measurable (paramReadoutSig : TwoLayerParams n H → ReadoutSig n H) := by
    unfold paramReadoutSig
    refine Measurable.prod_mk ?_ ?_
    · refine measurable_pi_lambda _ fun h => measurable_pi_lambda _ fun x => ?_
      have hset : MeasurableSet {θ : TwoLayerParams n H | 0 ≤ preAct θ h x} :=
        measurableSet_le measurable_const (measurable_preAct h x)
      have hite : Measurable fun θ : TwoLayerParams n H =>
          if 0 ≤ preAct θ h x then (true : Bool) else false :=
        Measurable.ite hset measurable_const measurable_const
      convert hite using 1
    · refine measurable_pi_lambda _ fun h1 => measurable_pi_lambda _ fun h2 => ?_
      have hw1 : Measurable fun θ : TwoLayerParams n H => |w2 θ h1| := by
        unfold w2
        exact continuous_abs.measurable.comp (measurable_pi_apply (idxW2 h1))
      have hw2 : Measurable fun θ : TwoLayerParams n H => |w2 θ h2| := by
        unfold w2
        exact continuous_abs.measurable.comp (measurable_pi_apply (idxW2 h2))
      have hgt : MeasurableSet {θ : TwoLayerParams n H | |w2 θ h2| < |w2 θ h1|} :=
        measurableSet_lt hw2 hw1
      have heq : MeasurableSet {θ : TwoLayerParams n H | |w2 θ h1| = |w2 θ h2|} := by
        have hinter : {θ : TwoLayerParams n H | |w2 θ h1| = |w2 θ h2|} =
            {θ : TwoLayerParams n H | |w2 θ h1| ≤ |w2 θ h2|} ∩
              {θ : TwoLayerParams n H | |w2 θ h2| ≤ |w2 θ h1|} := by
          ext θ
          exact le_antisymm_iff
        rw [hinter]
        exact (measurableSet_le hw1 hw2).inter (measurableSet_le hw2 hw1)
      have hcond : MeasurableSet {θ : TwoLayerParams n H |
          |w2 θ h1| > |w2 θ h2| ∨ (|w2 θ h1| = |w2 θ h2| ∧ h1.val ≤ h2.val)} := by
        by_cases hle : h1.val ≤ h2.val
        · convert hgt.union heq using 1
          ext θ
          simp [gt_iff_lt, hle]
        · convert hgt using 1
          ext θ
          simp [gt_iff_lt, hle]
      have hite : Measurable fun θ : TwoLayerParams n H =>
          if (|w2 θ h1| > |w2 θ h2| ∨ (|w2 θ h1| = |w2 θ h2| ∧ h1.val ≤ h2.val))
          then (true : Bool) else false :=
        Measurable.ite hcond measurable_const measurable_const
      convert hite using 1
  exact (measurable_of_countable (readoutOfSig g)).comp hsig

private theorem twoLayer_pushforward_circuit_mass {n H : Nat} (vW1 vB1 : ℝ≥0)
    (μW2 μb2 : Measure ℝ) [IsProbabilityMeasure μW2] [IsProbabilityMeasure μb2]
    (hW2 : μW2.map Neg.neg = μW2) (hb2 : μb2.map Neg.neg = μb2)
    (σ : SignedPerm n) (outFlip : Bool) {C : Type*} [MeasurableSpace C] [MeasurableSingletonClass C]
    (actC invC : C → C) (hC_left : ∀ c, invC (actC c) = c) (hactC : Measurable actC)
    (F : TwoLayerParams n H → C) (hFm : Measurable F)
    (hFeq : ∀ θ, F (actRealVec (liftSignedPerm n H σ outFlip) θ) = actC (F θ))
    (tgt : C) :
    (twoLayerInitMeasure n H vW1 vB1 μW2 μb2).map F {actC tgt} =
      (twoLayerInitMeasure n H vW1 vB1 μW2 μb2).map F {tgt} := by
  have hinv : ((twoLayerInitMeasure n H vW1 vB1 μW2 μb2).map F).map actC =
      (twoLayerInitMeasure n H vW1 vB1 μW2 μb2).map F := by
    rw [Measure.map_map hactC hFm]
    have hcomp : actC ∘ F = F ∘ actRealVec (liftSignedPerm n H σ outFlip) :=
      funext fun θ => (hFeq θ).symm
    rw [hcomp, ← Measure.map_map hFm (measurable_actRealVec _),
      twoLayerInitMeasure_invariant n H vW1 vB1 μW2 μb2 hW2 hb2 σ outFlip]
  have hm : ((twoLayerInitMeasure n H vW1 vB1 μW2 μb2).map F).map actC {actC tgt} =
      (twoLayerInitMeasure n H vW1 vB1 μW2 μb2).map F {actC tgt} :=
    congrArg (fun m : Measure C => m {actC tgt}) hinv
  rw [Measure.map_apply hactC (MeasurableSet.singleton (actC tgt))] at hm
  have hpre : actC ⁻¹' {actC tgt} = {tgt} := by
    ext c
    simp only [mem_preimage, mem_singleton_iff]
    exact ⟨fun hc => by simpa [hC_left] using congrArg invC hc, fun hc => hc ▸ rfl⟩
  rw [hpre] at hm
  exact hm.symm

/-- **Full G13 Closure of Theorem 15 (AdamW + general differentiable measurable activation + concrete readout)**:
    zero residual equivariance or measurability hypotheses on training or readout. -/
theorem theorem15_twoLayer_adamw_concrete {n H : Nat}
    (φ φ' : ℝ → ℝ) (hφd : ∀ z, HasDerivAt φ (φ' z) z)
    (hφm : Measurable φ) (hφ'm : Measurable φ')
    (g : (Fin n → Bool) → Bool) (σ : SignedPerm n) (outFlip : Bool)
    (hSym : IsTargetSymmetry g σ outFlip)
    (vW1 vB1 : ℝ≥0) (μW2 μb2 : Measure ℝ) [IsProbabilityMeasure μW2] [IsProbabilityMeasure μb2]
    (hW2 : μW2.map Neg.neg = μW2) (hb2 : μb2.map Neg.neg = μb2)
    (sched : Nat → AdamWCfgReal) (t : Nat) (tgt : CircuitOut n) :
    (twoLayerInitMeasure n H vW1 vB1 μW2 μb2).map
        (fun θ => concreteCircuitReadout g (runAdamWSchedule (trueGrad (@logisticLoss n H φ g)) sched t θ))
        {actCircuitOut σ tgt} =
      (twoLayerInitMeasure n H vW1 vB1 μW2 μb2).map
        (fun θ => concreteCircuitReadout g (runAdamWSchedule (trueGrad (@logisticLoss n H φ g)) sched t θ))
        {tgt} := by
  let grad : TwoLayerParams n H → TwoLayerParams n H := trueGrad (@logisticLoss n H φ g)
  have hgm : Measurable grad := measurable_trueGrad_logisticLoss hφd hφm hφ'm g
  have hgeq : ∀ θ, grad (actRealVec (liftSignedPerm n H σ outFlip) θ) =
      actRealVec (liftSignedPerm n H σ outFlip) (grad θ) :=
    trueGrad_equivariant (@logisticLoss n H φ g) (liftSignedPerm n H σ outFlip)
      (logisticLoss_invariant φ g σ outFlip hSym)
  refine twoLayer_pushforward_circuit_mass vW1 vB1 μW2 μb2 hW2 hb2 σ outFlip
    (actCircuitOut σ) (actCircuitOut (SignedPerm.inv σ)) (actCircuitOut_left_inv σ)
    measurable_from_top
    (fun θ => concreteCircuitReadout g (runAdamWSchedule grad sched t θ))
    ((measurable_concreteCircuitReadout g).comp (measurable_runAdamWSchedule grad hgm sched t))
    (fun θ => ?_) tgt
  dsimp only
  rw [runAdamWSchedule_equivariant grad sched (liftSignedPerm n H σ outFlip) hgeq t θ,
    concreteCircuitReadout_equivariant g σ outFlip hSym]

/-- **Concrete `tanh` instantiation of Theorem 15 (AdamW)**: ONLY `IsTargetSymmetry g σ outFlip`
    and symmetric output weight laws `μW2`, `μb2` remain as hypotheses. -/
theorem theorem15_twoLayer_tanh_adamw_concrete {n H : Nat}
    (g : (Fin n → Bool) → Bool) (σ : SignedPerm n) (outFlip : Bool)
    (hSym : IsTargetSymmetry g σ outFlip)
    (vW1 vB1 : ℝ≥0) (μW2 μb2 : Measure ℝ) [IsProbabilityMeasure μW2] [IsProbabilityMeasure μb2]
    (hW2 : μW2.map Neg.neg = μW2) (hb2 : μb2.map Neg.neg = μb2)
    (sched : Nat → AdamWCfgReal) (t : Nat) (tgt : CircuitOut n) :
    (twoLayerInitMeasure n H vW1 vB1 μW2 μb2).map
        (fun θ => concreteCircuitReadout g (runAdamWSchedule (trueGrad (@logisticLoss n H tanhReal g)) sched t θ))
        {actCircuitOut σ tgt} =
      (twoLayerInitMeasure n H vW1 vB1 μW2 μb2).map
        (fun θ => concreteCircuitReadout g (runAdamWSchedule (trueGrad (@logisticLoss n H tanhReal g)) sched t θ))
        {tgt} :=
  theorem15_twoLayer_adamw_concrete tanhReal tanhRealDeriv hasDerivAt_tanhReal
    measurable_tanhReal measurable_tanhRealDeriv g σ outFlip hSym vW1 vB1 μW2 μb2 hW2 hb2 sched t tgt

/-- **Full G13 Closure of Theorem 15 (Gradient Descent + general differentiable measurable activation + concrete readout)**. -/
theorem theorem15_twoLayer_gd_concrete {n H : Nat}
    (φ φ' : ℝ → ℝ) (hφd : ∀ z, HasDerivAt φ (φ' z) z)
    (hφm : Measurable φ) (hφ'm : Measurable φ')
    (g : (Fin n → Bool) → Bool) (σ : SignedPerm n) (outFlip : Bool)
    (hSym : IsTargetSymmetry g σ outFlip)
    (vW1 vB1 : ℝ≥0) (μW2 μb2 : Measure ℝ) [IsProbabilityMeasure μW2] [IsProbabilityMeasure μb2]
    (hW2 : μW2.map Neg.neg = μW2) (hb2 : μb2.map Neg.neg = μb2)
    (sched : Nat → ℝ × ℝ) (t : Nat) (tgt : CircuitOut n) :
    (twoLayerInitMeasure n H vW1 vB1 μW2 μb2).map
        (fun θ => concreteCircuitReadout g (runGDSchedule (trueGrad (@logisticLoss n H φ g)) sched t θ))
        {actCircuitOut σ tgt} =
      (twoLayerInitMeasure n H vW1 vB1 μW2 μb2).map
        (fun θ => concreteCircuitReadout g (runGDSchedule (trueGrad (@logisticLoss n H φ g)) sched t θ))
        {tgt} := by
  let grad : TwoLayerParams n H → TwoLayerParams n H := trueGrad (@logisticLoss n H φ g)
  have hgm : Measurable grad := measurable_trueGrad_logisticLoss hφd hφm hφ'm g
  have hgeq : ∀ θ, grad (actRealVec (liftSignedPerm n H σ outFlip) θ) =
      actRealVec (liftSignedPerm n H σ outFlip) (grad θ) :=
    trueGrad_equivariant (@logisticLoss n H φ g) (liftSignedPerm n H σ outFlip)
      (logisticLoss_invariant φ g σ outFlip hSym)
  refine twoLayer_pushforward_circuit_mass vW1 vB1 μW2 μb2 hW2 hb2 σ outFlip
    (actCircuitOut σ) (actCircuitOut (SignedPerm.inv σ)) (actCircuitOut_left_inv σ)
    measurable_from_top
    (fun θ => concreteCircuitReadout g (runGDSchedule grad sched t θ))
    ((measurable_concreteCircuitReadout g).comp (measurable_runGDSchedule grad hgm sched t))
    (fun θ => ?_) tgt
  dsimp only
  rw [runGDSchedule_equivariant grad sched (liftSignedPerm n H σ outFlip) hgeq t θ,
    concreteCircuitReadout_equivariant g σ outFlip hSym]

/-- **Concrete `tanh` instantiation of Theorem 15 (Gradient Descent)**. -/
theorem theorem15_twoLayer_tanh_gd_concrete {n H : Nat}
    (g : (Fin n → Bool) → Bool) (σ : SignedPerm n) (outFlip : Bool)
    (hSym : IsTargetSymmetry g σ outFlip)
    (vW1 vB1 : ℝ≥0) (μW2 μb2 : Measure ℝ) [IsProbabilityMeasure μW2] [IsProbabilityMeasure μb2]
    (hW2 : μW2.map Neg.neg = μW2) (hb2 : μb2.map Neg.neg = μb2)
    (sched : Nat → ℝ × ℝ) (t : Nat) (tgt : CircuitOut n) :
    (twoLayerInitMeasure n H vW1 vB1 μW2 μb2).map
        (fun θ => concreteCircuitReadout g (runGDSchedule (trueGrad (@logisticLoss n H tanhReal g)) sched t θ))
        {actCircuitOut σ tgt} =
      (twoLayerInitMeasure n H vW1 vB1 μW2 μb2).map
        (fun θ => concreteCircuitReadout g (runGDSchedule (trueGrad (@logisticLoss n H tanhReal g)) sched t θ))
        {tgt} :=
  theorem15_twoLayer_gd_concrete tanhReal tanhRealDeriv hasDerivAt_tanhReal
    measurable_tanhReal measurable_tanhRealDeriv g σ outFlip hSym vW1 vB1 μW2 μb2 hW2 hb2 sched t tgt

/-- General-readout variant of G13 AdamW Theorem 15 for any alternative equivariant measurable readout. -/
theorem theorem15_twoLayer_adamw_general_readout {n H : Nat} {C : Type*}
    [MeasurableSpace C] [MeasurableSingletonClass C]
    (φ φ' : ℝ → ℝ) (hφd : ∀ z, HasDerivAt φ (φ' z) z)
    (hφm : Measurable φ) (hφ'm : Measurable φ')
    (g : (Fin n → Bool) → Bool) (σ : SignedPerm n) (outFlip : Bool)
    (hSym : IsTargetSymmetry g σ outFlip)
    (vW1 vB1 : ℝ≥0) (μW2 μb2 : Measure ℝ) [IsProbabilityMeasure μW2] [IsProbabilityMeasure μb2]
    (hW2 : μW2.map Neg.neg = μW2) (hb2 : μb2.map Neg.neg = μb2)
    (sched : Nat → AdamWCfgReal)
    (actC invC : C → C) (hC_left : ∀ c, invC (actC c) = c) (hactC : Measurable actC)
    (readout : TwoLayerParams n H → C) (hrm : Measurable readout)
    (hreq : ∀ θ, readout (actRealVec (liftSignedPerm n H σ outFlip) θ) = actC (readout θ))
    (t : Nat) (tgt : C) :
    (twoLayerInitMeasure n H vW1 vB1 μW2 μb2).map
        (fun θ => readout (runAdamWSchedule (trueGrad (@logisticLoss n H φ g)) sched t θ))
        {actC tgt} =
      (twoLayerInitMeasure n H vW1 vB1 μW2 μb2).map
        (fun θ => readout (runAdamWSchedule (trueGrad (@logisticLoss n H φ g)) sched t θ))
        {tgt} := by
  let grad : TwoLayerParams n H → TwoLayerParams n H := trueGrad (@logisticLoss n H φ g)
  have hgm : Measurable grad := measurable_trueGrad_logisticLoss hφd hφm hφ'm g
  have hgeq : ∀ θ, grad (actRealVec (liftSignedPerm n H σ outFlip) θ) =
      actRealVec (liftSignedPerm n H σ outFlip) (grad θ) :=
    trueGrad_equivariant (@logisticLoss n H φ g) (liftSignedPerm n H σ outFlip)
      (logisticLoss_invariant φ g σ outFlip hSym)
  refine twoLayer_pushforward_circuit_mass vW1 vB1 μW2 μb2 hW2 hb2 σ outFlip
    actC invC hC_left hactC
    (fun θ => readout (runAdamWSchedule grad sched t θ))
    (hrm.comp (measurable_runAdamWSchedule grad hgm sched t))
    (fun θ => ?_) tgt
  dsimp only
  rw [runAdamWSchedule_equivariant grad sched (liftSignedPerm n H σ outFlip) hgeq t θ, hreq]

end
end G13

end CerpMathlib
