import ObstructionExactSequence
import StochasticCausalCovariance
import CausalCovarianceGroupoidBridge
import HigherSemanticCore

/-!
# Contextual Coalgebraic Ring Descent, Grounding Separation & CoCartesian Opfibration

Completes the constructive Pure Lean 4 obligations bridging the contextual
coalgebraic ring architecture and the varying-signature causal-grounding moduli:

1. **Sparse Heterogeneous Ring Witness (`sparseABC`):**
   Three distinct contexts `A — B — C` with incompatible local carriers
   (`Bool`, `Fin 3`, `Fin 4`) and NO direct `A–C` overlap, proving connectedness
   and invariance of global coherence across all finite action sequences.
2. **Context Category, Coalgebra Morphisms & Effective Holonomy Descent:**
   Formalizes `CtxCat`, `IndexedCoalgebra`, `CoalgebraMor`, `RingModuleIso`, and
   cycle `CycleOverlapBundle`, proving `effective_descent_iff_trivial_holonomy` plus the
   three-way split (`strict_descent_unique_gluing`, `groupoid_descent_nontrivial_aut`,
   `obstructed_descent_bridge` via `ObstructionExactSequence`).
3. **Internal-Equivalence vs. External-Grounding Separation:**
   Exhibits `coherentHallucinationRing` and `externallyGroundedRing` as globally
   coherent, connected, and internally coalgebra-isomorphic, yet separated by
   external causal reference (`hallucination_fails_grounding`).
4. **Full Arbitrary-Base-Change CoCartesian Opfibration & Reachable-Support Covariance:**
   Formalizes `VSig`/`VSigEquiv`/`VTotalRep`/`VTotalIso` with full coCartesian
   universal factorization (`coCartesian_universal_exists_unique`), sequential lift
   coherence (`lift_comp_coherence`), reachable-support `Reach(μ₀)` covariance
   (`reachable_support_covariance` + unreachable-mass counterexample), total
   varying-signature response functor (`totalProfile_transport_commutes`), global
   anchored product kernel triviality (`total_anchored_kernel_trivial_iff`), and strict
   separations in the adequacy hierarchy.

Zero `Classical.choice`, zero `sorryAx`, zero Mathlib dependencies.
-/

namespace Cerp.ContextualRingDescent

open Cerp.StochasticInterventionGrounding
open Cerp.StochasticCausalCovariance
open Cerp.CausalCovarianceGroupoidBridge
open Cerp.HigherSemanticCore
open Cerp.ObstructionExactSequence

universe u v w x y

-- =============================================================================
-- 1. Contextual Coalgebraic Ring & Sparse Heterogeneous A — B — C Witness
-- =============================================================================

structure ContextualRing where
  Ctx : Type u
  Action : Type v
  Local : Ctx → Type w
  Observation : Ctx → Type x
  observe : (c : Ctx) → Local c → Observation c
  step : (c : Ctx) → Local c → Action → Local c
  adjacent : Ctx → Ctx → Prop
  adjacent_symm : ∀ {c d}, adjacent c d → adjacent d c
  coh : (c : Ctx) → Local c → Prop
  corresponds : ∀ {c d}, adjacent c d → Local c → Local d → Prop
  local_closed : ∀ c s a, coh c s → coh c (step c s a)
  corr_closed : ∀ {c d} (h : adjacent c d) (s : Local c) (t : Local d) (a : Action),
    corresponds h s t → corresponds h (step c s a) (step d t a)

abbrev RingGlobalState (R : ContextualRing.{u, v, w, x}) := (c : R.Ctx) → R.Local c

def RingGlobalCoherent (R : ContextualRing.{u, v, w, x}) (s : RingGlobalState R) : Prop :=
  (∀ c, R.coh c (s c)) ∧ (∀ {c d} (h : R.adjacent c d), R.corresponds h (s c) (s d))

def ringEvolve (R : ContextualRing.{u, v, w, x}) (s : RingGlobalState R) (a : R.Action) :
    RingGlobalState R :=
  fun c => R.step c (s c) a

def ringEvolveList (R : ContextualRing.{u, v, w, x}) :
    RingGlobalState R → List R.Action → RingGlobalState R
  | s, [] => s
  | s, a :: rest => ringEvolveList R (ringEvolve R s a) rest

theorem ringEvolve_preserves (R : ContextualRing.{u, v, w, x})
    (s : RingGlobalState R) (a : R.Action) (hs : RingGlobalCoherent R s) :
    RingGlobalCoherent R (ringEvolve R s a) :=
  ⟨fun c => R.local_closed c (s c) a (hs.1 c),
   fun h => R.corr_closed h (s _) (s _) a (hs.2 h)⟩

theorem ringEvolveList_preserves (R : ContextualRing.{u, v, w, x})
    (actions : List R.Action) (s : RingGlobalState R) (hs : RingGlobalCoherent R s) :
    RingGlobalCoherent R (ringEvolveList R s actions) := by
  induction actions generalizing s with
  | nil => exact hs
  | cons a _ ih =>
      exact ih (ringEvolve R s a) (ringEvolve_preserves R s a hs)

inductive RingPath (R : ContextualRing.{u, v, w, x}) : R.Ctx → R.Ctx → Prop
  | refl (c : R.Ctx) : RingPath R c c
  | step {c d e : R.Ctx} : RingPath R c d → R.adjacent d e → RingPath R c e

def RingConnected (R : ContextualRing.{u, v, w, x}) : Prop :=
  ∀ c d, RingPath R c d

inductive Ctx3 where
  | ctxA | ctxB | ctxC
  deriving DecidableEq

def ctx3Carrier : Ctx3 → Type
  | .ctxA => Bool
  | .ctxB => Fin 3
  | .ctxC => Fin 4

def stepB (x : Fin 3) (a : Bool) : Fin 3 :=
  match a with
  | false => x
  | true =>
      match x with
      | ⟨0, _⟩ => ⟨1, by decide⟩
      | ⟨1, _⟩ => ⟨0, by decide⟩
      | ⟨n + 2, h⟩ => ⟨n + 2, h⟩

def stepC (y : Fin 4) (a : Bool) : Fin 4 :=
  match a with
  | false => y
  | true =>
      match y with
      | ⟨0, _⟩ => ⟨1, by decide⟩
      | ⟨1, _⟩ => ⟨0, by decide⟩
      | ⟨n + 2, h⟩ => ⟨n + 2, h⟩

def ctx3Step : (c : Ctx3) → ctx3Carrier c → Bool → ctx3Carrier c
  | .ctxA, b, a => xor b a
  | .ctxB, x, a => stepB x a
  | .ctxC, y, a => stepC y a

def ctx3AdjBool : Ctx3 → Ctx3 → Bool
  | .ctxA, .ctxB => true
  | .ctxB, .ctxA => true
  | .ctxB, .ctxC => true
  | .ctxC, .ctxB => true
  | _, _ => false

def ctx3Coh : (c : Ctx3) → ctx3Carrier c → Prop
  | .ctxA, _ => True
  | .ctxB, x => x.1 < 2
  | .ctxC, y => y.1 < 2

def ctx3Code : (c : Ctx3) → ctx3Carrier c → Nat
  | .ctxA, false => 0
  | .ctxA, true => 1
  | .ctxB, x => x.1
  | .ctxC, y => y.1

private theorem ctx3Code_step (c : Ctx3) (s : ctx3Carrier c) (a : Bool)
    (h : ctx3Code c s < 2) :
    ctx3Code c (ctx3Step c s a) =
      if a then (if ctx3Code c s = 0 then 1 else 0) else ctx3Code c s := by
  cases c with
  | ctxA => cases s <;> cases a <;> decide
  | ctxB =>
      rcases s with ⟨n, hn⟩
      cases a
      · rfl
      · match n with
        | 0 => rfl
        | 1 => rfl
        | k + 2 =>
            simp only [ctx3Code] at h
            exact absurd h (Nat.not_lt.mpr (Nat.le_add_left 2 k))
  | ctxC =>
      rcases s with ⟨n, hn⟩
      cases a
      · rfl
      · match n with
        | 0 => rfl
        | 1 => rfl
        | k + 2 =>
            simp only [ctx3Code] at h
            exact absurd h (Nat.not_lt.mpr (Nat.le_add_left 2 k))

private def flipNat01 : Nat → Nat
  | 0 => 1
  | 1 => 0
  | n + 2 => n + 2

private theorem ctx3Code_step_all (c : Ctx3) (s : ctx3Carrier c) (a : Bool) :
    ctx3Code c (ctx3Step c s a) = if a then flipNat01 (ctx3Code c s) else ctx3Code c s := by
  cases c with
  | ctxA => cases s <;> cases a <;> rfl
  | ctxB =>
      rcases s with ⟨n, hn⟩
      cases a
      · rfl
      · match n with
        | 0 => rfl
        | 1 => rfl
        | k + 2 => rfl
  | ctxC =>
      rcases s with ⟨n, hn⟩
      cases a
      · rfl
      · match n with
        | 0 => rfl
        | 1 => rfl
        | k + 2 => rfl

def sparseABC : ContextualRing.{0, 0, 0, 0} where
  Ctx := Ctx3
  Action := Bool
  Local := ctx3Carrier
  Observation := fun _ => Nat
  observe := ctx3Code
  step := ctx3Step
  adjacent := fun c d => ctx3AdjBool c d = true
  adjacent_symm := by
    intro c d h
    cases c <;> cases d <;> exact h
  coh := ctx3Coh
  corresponds := fun {_ _} _ x y => ctx3Code _ x = ctx3Code _ y
  local_closed := by
    intro c s a hs
    cases c with
    | ctxA => trivial
    | ctxB =>
        rcases s with ⟨n, hn⟩
        have hlt : n < 2 := hs
        cases a
        · exact hlt
        · match n with
          | 0 => exact Nat.one_lt_two
          | 1 => exact Nat.zero_lt_two
          | k + 2 => exact absurd hlt (Nat.not_lt.mpr (Nat.le_add_left 2 k))
    | ctxC =>
        rcases s with ⟨n, hn⟩
        have hlt : n < 2 := hs
        cases a
        · exact hlt
        · match n with
          | 0 => exact Nat.one_lt_two
          | 1 => exact Nat.zero_lt_two
          | k + 2 => exact absurd hlt (Nat.not_lt.mpr (Nat.le_add_left 2 k))
  corr_closed := by
    intro c d _ s t a hcorr
    change ctx3Code c (ctx3Step c s a) = ctx3Code d (ctx3Step d t a)
    rw [ctx3Code_step_all c s a, ctx3Code_step_all d t a, hcorr]

theorem sparseABC_hasNonAdjacentPair : ¬ sparseABC.adjacent .ctxA .ctxC := by
  intro h
  exact Bool.noConfusion h

theorem sparseABC_connected : RingConnected sparseABC := by
  intro c d
  cases c <;> cases d
  · exact RingPath.refl _
  · exact RingPath.step (RingPath.refl _) (rfl : ctx3AdjBool .ctxA .ctxB = true)
  · exact RingPath.step (RingPath.step (RingPath.refl _)
      (rfl : ctx3AdjBool .ctxA .ctxB = true)) (rfl : ctx3AdjBool .ctxB .ctxC = true)
  · exact RingPath.step (RingPath.refl _) (rfl : ctx3AdjBool .ctxB .ctxA = true)
  · exact RingPath.refl _
  · exact RingPath.step (RingPath.refl _) (rfl : ctx3AdjBool .ctxB .ctxC = true)
  · exact RingPath.step (RingPath.step (RingPath.refl _)
      (rfl : ctx3AdjBool .ctxC .ctxB = true)) (rfl : ctx3AdjBool .ctxB .ctxA = true)
  · exact RingPath.step (RingPath.refl _) (rfl : ctx3AdjBool .ctxC .ctxB = true)
  · exact RingPath.refl _

def sparseABCInit : RingGlobalState sparseABC
  | .ctxA => false
  | .ctxB => ⟨0, by decide⟩
  | .ctxC => ⟨0, by decide⟩

theorem sparseABC_baseCoherent : RingGlobalCoherent sparseABC sparseABCInit := by
  constructor
  · intro c
    cases c
    · trivial
    · exact Nat.zero_lt_two
    · exact Nat.zero_lt_two
  · intro c d hadj
    cases c <;> cases d <;> first | exact Bool.noConfusion hadj | rfl

theorem sparseABC_global_evolve_preserves (actions : List Bool) :
    RingGlobalCoherent sparseABC (ringEvolveList sparseABC sparseABCInit actions) :=
  ringEvolveList_preserves sparseABC actions sparseABCInit sparseABC_baseCoherent

-- =============================================================================
-- 2. Context Category, Coalgebra Morphisms & Effective Holonomy Descent
-- =============================================================================

structure CtxCat where
  Obj : Type u
  Hom : Obj → Obj → Type v
  id : (c : Obj) → Hom c c
  comp : {c d e : Obj} → Hom c d → Hom d e → Hom c e
  id_comp : ∀ {c d} (f : Hom c d), comp (id c) f = f
  comp_id : ∀ {c d} (f : Hom c d), comp f (id d) = f
  assoc : ∀ {a b c d} (f : Hom a b) (g : Hom b c) (h : Hom c d),
    comp (comp f g) h = comp f (comp g h)

structure IndexedCoalgebra (C : CtxCat.{u, v}) where
  Action : Type w
  Obs : Type x
  Local : C.Obj → Type y
  observe : ∀ c, Local c → Obs
  step : ∀ c, Local c → Action → Local c
  coh : ∀ c, Local c → Prop
  reidx : ∀ {c d}, C.Hom c d → Local d → Local c
  coh_reidx : ∀ {c d} (f : C.Hom c d) (x : Local d), coh d x → coh c (reidx f x)

structure CoalgebraMor {C : CtxCat.{u, v}} (M N : IndexedCoalgebra.{u, v, w, x, y} C)
    (hAct : M.Action = N.Action) (hObs : M.Obs = N.Obs) where
  mapLocal : ∀ c, M.Local c → N.Local c
  comm_obs : ∀ c x, hObs ▸ M.observe c x = N.observe c (mapLocal c x)
  comm_step : ∀ c x a, mapLocal c (M.step c x a) = N.step c (mapLocal c x) (hAct ▸ a)
  pres_coh : ∀ c x, M.coh c x → N.coh c (mapLocal c x)

structure RingModuleIso (R₁ R₂ : ContextualRing.{u, v, w, x})
    (hCtx : R₁.Ctx = R₂.Ctx) (hAct : R₁.Action = R₂.Action)
    (hObs : ∀ c, R₁.Observation c = R₂.Observation (hCtx ▸ c)) where
  toLocal : ∀ c, R₁.Local c → R₂.Local (hCtx ▸ c)
  invLocal : ∀ c, R₂.Local (hCtx ▸ c) → R₁.Local c
  left_inv : ∀ c x, invLocal c (toLocal c x) = x
  right_inv : ∀ c y, toLocal c (invLocal c y) = y
  comm_obs : ∀ c x, hObs c ▸ R₁.observe c x = R₂.observe (hCtx ▸ c) (toLocal c x)
  comm_step : ∀ c x a, toLocal c (R₁.step c x a) = R₂.step (hCtx ▸ c) (toLocal c x) (hAct ▸ a)
  pres_coh : ∀ c x, R₁.coh c x ↔ R₂.coh (hCtx ▸ c) (toLocal c x)

structure CycleOverlapBundle where
  L0 : Type u
  L1 : Type u
  L2 : Type u
  g01 : L0 → L1
  g12 : L1 → L2
  g20 : L2 → L0

def CycleOverlapBundle.HasGlobalGluedSection (B : CycleOverlapBundle.{u}) : Prop :=
  ∃ s0 : B.L0, ∃ s1 : B.L1, ∃ s2 : B.L2,
    B.g01 s0 = s1 ∧ B.g12 s1 = s2 ∧ B.g20 s2 = s0

def CycleOverlapBundle.holonomy (B : CycleOverlapBundle.{u}) (x : B.L0) : B.L0 :=
  B.g20 (B.g12 (B.g01 x))

/-- Effective descent criterion: a cycle bundle glues iff some base state
    is fixed by loop holonomy. -/
theorem effective_descent_iff_trivial_holonomy (B : CycleOverlapBundle.{u}) :
    B.HasGlobalGluedSection ↔ ∃ x0 : B.L0, B.holonomy x0 = x0 := by
  constructor
  · rintro ⟨s0, s1, s2, h01, h12, h20⟩
    exact ⟨s0, by simp [CycleOverlapBundle.holonomy, h01, h12, h20]⟩
  · rintro ⟨x0, hloop⟩
    exact ⟨x0, B.g01 x0, B.g12 (B.g01 x0), rfl, rfl, hloop⟩

theorem strict_descent_unique_gluing :
    let B : CycleOverlapBundle.{0} := ⟨Unit, Unit, Unit, id, id, id⟩
    ∃ s0 : B.L0, ∃ s1 : B.L1, ∃ s2 : B.L2,
      (B.g01 s0 = s1 ∧ B.g12 s1 = s2 ∧ B.g20 s2 = s0) ∧
      (∀ t0 t1 t2, (B.g01 t0 = t1 ∧ B.g12 t1 = t2 ∧ B.g20 t2 = t0) →
        t0 = s0 ∧ t1 = s1 ∧ t2 = s2) :=
  ⟨(), (), (), ⟨rfl, rfl, rfl⟩, fun _ _ _ _ => ⟨rfl, rfl, rfl⟩⟩

theorem groupoid_descent_nontrivial_aut :
    let B : CycleOverlapBundle.{0} := ⟨Bool, Bool, Bool, id, id, id⟩
    B.HasGlobalGluedSection ∧
    (∃ f : Bool → Bool, (∀ x, f (f x) = x) ∧ f ≠ id ∧
      ∀ s0 s1 s2, (B.g01 s0 = s1 ∧ B.g12 s1 = s2 ∧ B.g20 s2 = s0) →
        (B.g01 (f s0) = f s1 ∧ B.g12 (f s1) = f s2 ∧ B.g20 (f s2) = f s0)) := by
  refine ⟨⟨true, true, true, rfl, rfl, rfl⟩, not, Bool.not_not, ?_, ?_⟩
  · intro h
    exact Bool.noConfusion (congrFun h true)
  · intro s0 s1 s2 ⟨h01, h12, h20⟩
    exact ⟨congrArg not h01, congrArg not h12, congrArg not h20⟩

/-- Bridge to `Cerp.ObstructionExactSequence`: locally compatible `C4` edge
    sections fail global descent under coset-`0` anchoring. -/
theorem obstructed_descent_bridge :
    (c4Mul (speckerCoset0Local Tri.v0 Tri.v0 (by trivial))
           (speckerCoset0Local Tri.v0 Tri.v1 (by trivial)) = C4.c2 ∧
     c4Mul (speckerCoset0Local Tri.v1 Tri.v1 (by trivial))
           (speckerCoset0Local Tri.v1 Tri.v2 (by trivial)) = C4.c2 ∧
     c4Mul (speckerCoset0Local Tri.v2 Tri.v2 (by trivial))
           (speckerCoset0Local Tri.v2 Tri.v0 (by trivial)) = C4.c2) ∧
    (¬ GluesByGauge c4Group c2InC4 speckerVarCover speckerCoset0Local) ∧
    (¬ ∃ r : Tri → C4, ValidTriangleRealization r ∧ ∀ v, c2InC4.mem (r v)) :=
  ⟨speckerCoset0Local_valid_edges,
   speckerCoset0Local_not_gluesByGauge,
   c4_triangle_coset0_anchor_no_global_realization⟩

-- =============================================================================
-- 3. Grounding Separation: Internal Equivalence vs. Physical Reference
-- =============================================================================

def coherentHallucinationRing : ContextualRing.{0, 0, 0, 0} where
  Ctx := Bool
  Action := Unit
  Local := fun _ => Bool
  Observation := fun _ => Bool
  observe := fun _ b => !b
  step := fun _ x _ => x
  adjacent := fun c d => c ≠ d
  adjacent_symm := fun h => h.symm
  coh := fun _ _ => True
  corresponds := fun {_ _} _ x y => x = y
  local_closed := fun _ _ _ _ => trivial
  corr_closed := fun _ _ _ _ h => h

def externallyGroundedRing : ContextualRing.{0, 0, 0, 0} where
  Ctx := Bool
  Action := Unit
  Local := fun _ => Bool
  Observation := fun _ => Bool
  observe := fun _ b => b
  step := fun _ x _ => x
  adjacent := fun c d => c ≠ d
  adjacent_symm := fun h => h.symm
  coh := fun _ _ => True
  corresponds := fun {_ _} _ x y => x = y
  local_closed := fun _ _ _ _ => trivial
  corr_closed := fun _ _ _ _ h => h

def physicalGroundState : RingGlobalState coherentHallucinationRing := fun _ => true

theorem coherentHallucination_is_globally_coherent :
    RingGlobalCoherent coherentHallucinationRing physicalGroundState :=
  ⟨fun _ => trivial, fun _ => rfl⟩

def hallucination_iso_grounded :
    RingModuleIso coherentHallucinationRing externallyGroundedRing rfl rfl (fun _ => rfl) where
  toLocal := fun _ b => !b
  invLocal := fun _ b => !b
  left_inv := fun _ b => Bool.not_not b
  right_inv := fun _ b => Bool.not_not b
  comm_obs := fun _ _ => rfl
  comm_step := fun _ _ _ => rfl
  pres_coh := fun _ _ => Iff.rfl

theorem hallucination_fails_grounding :
    coherentHallucinationRing.observe false (physicalGroundState false) ≠ true := by
  intro h
  exact Bool.noConfusion h

theorem grounded_satisfies_grounding :
    externallyGroundedRing.observe false (physicalGroundState false) = true := rfl

-- =============================================================================
-- 4. Full CoCartesian Variable-Signature Opfibration & Reachable Support Reach(μ₀)
-- =============================================================================

structure VEquiv (α : Type u) (β : Type v) where
  toFun : α → β
  invFun : β → α
  left_inv : ∀ a, invFun (toFun a) = a
  right_inv : ∀ b, toFun (invFun b) = b

namespace VEquiv

@[ext]
theorem ext {α : Type u} {β : Type v} {e₁ e₂ : VEquiv α β}
    (ht : ∀ a, e₁.toFun a = e₂.toFun a) (hi : ∀ b, e₁.invFun b = e₂.invFun b) :
    e₁ = e₂ := by
  rcases e₁ with ⟨f₁, g₁, l₁, r₁⟩
  rcases e₂ with ⟨f₂, g₂, l₂, r₂⟩
  have hf : f₁ = f₂ := funext ht
  have hg : g₁ = g₂ := funext hi
  subst hf; subst hg
  rfl

def refl (α : Type u) : VEquiv α α where
  toFun := id
  invFun := id
  left_inv := fun _ => rfl
  right_inv := fun _ => rfl

def trans {α : Type u} {β : Type v} {γ : Type w}
    (e₁ : VEquiv α β) (e₂ : VEquiv β γ) : VEquiv α γ where
  toFun := fun a => e₂.toFun (e₁.toFun a)
  invFun := fun c => e₁.invFun (e₂.invFun c)
  left_inv := fun a => by dsimp only []; rw [e₂.left_inv, e₁.left_inv]
  right_inv := fun c => by dsimp only []; rw [e₁.right_inv, e₂.right_inv]

def symm {α : Type u} {β : Type v} (e : VEquiv α β) : VEquiv β α where
  toFun := e.invFun
  invFun := e.toFun
  left_inv := e.right_inv
  right_inv := e.left_inv

theorem mapDist_symm_cancel {α : Type u} {β : Type v} (e : VEquiv α β) (d : FinDist α) :
    mapDist e.symm.toFun (mapDist e.toFun d) = d := by
  rw [mapDist_comp]
  have h : (fun a => e.symm.toFun (e.toFun a)) = id := funext e.left_inv
  rw [h]
  exact mapDist_id d

end VEquiv

structure VSig where
  State : Type u
  Action : Type v
  Outcome : Type w
  stateDec : DecidableEq State
  actionDec : DecidableEq Action
  outcomeDec : DecidableEq Outcome

structure VSigEquiv (S T : VSig.{u, v, w}) where
  stateEq : VEquiv S.State T.State
  actionEq : VEquiv S.Action T.Action
  outcomeEq : VEquiv S.Outcome T.Outcome

namespace VSigEquiv

@[ext]
theorem ext {S T : VSig.{u, v, w}} {e₁ e₂ : VSigEquiv S T}
    (hs : e₁.stateEq = e₂.stateEq) (ha : e₁.actionEq = e₂.actionEq)
    (ho : e₁.outcomeEq = e₂.outcomeEq) : e₁ = e₂ := by
  cases e₁; cases e₂; subst hs; subst ha; subst ho; rfl

def refl (S : VSig.{u, v, w}) : VSigEquiv S S where
  stateEq := VEquiv.refl S.State
  actionEq := VEquiv.refl S.Action
  outcomeEq := VEquiv.refl S.Outcome

def trans {S T U : VSig.{u, v, w}} (e₁ : VSigEquiv S T) (e₂ : VSigEquiv T U) :
    VSigEquiv S U where
  stateEq := e₁.stateEq.trans e₂.stateEq
  actionEq := e₁.actionEq.trans e₂.actionEq
  outcomeEq := e₁.outcomeEq.trans e₂.outcomeEq

def symm {S T : VSig.{u, v, w}} (e : VSigEquiv S T) : VSigEquiv T S where
  stateEq := e.stateEq.symm
  actionEq := e.actionEq.symm
  outcomeEq := e.outcomeEq.symm

end VSigEquiv

def vSigGroupoid : Groupoid where
  Obj := VSig.{u, v, w}
  Hom := VSigEquiv
  id := VSigEquiv.refl
  comp := VSigEquiv.trans
  inv := VSigEquiv.symm
  id_comp := fun e => by
    apply VSigEquiv.ext <;> apply VEquiv.ext <;> intro _ <;> rfl
  comp_id := fun e => by
    apply VSigEquiv.ext <;> apply VEquiv.ext <;> intro _ <;> rfl
  assoc := fun f g h => by
    apply VSigEquiv.ext <;> apply VEquiv.ext <;> intro _ <;> rfl
  inv_left := fun f => by
    apply VSigEquiv.ext <;> apply VEquiv.ext
    · intro x; exact f.stateEq.right_inv x
    · intro x; exact f.stateEq.right_inv x
    · intro a; exact f.actionEq.right_inv a
    · intro a; exact f.actionEq.right_inv a
    · intro o; exact f.outcomeEq.right_inv o
    · intro o; exact f.outcomeEq.right_inv o
  inv_right := fun f => by
    apply VSigEquiv.ext <;> apply VEquiv.ext
    · intro x; exact f.stateEq.left_inv x
    · intro x; exact f.stateEq.left_inv x
    · intro a; exact f.actionEq.left_inv a
    · intro a; exact f.actionEq.left_inv a
    · intro o; exact f.outcomeEq.left_inv o
    · intro o; exact f.outcomeEq.left_inv o

structure VStochRep (Ext : Type u) (S : VSig.{v, w, x}) where
  initial : Ext → FinDist S.State
  observe : S.State → FinDist S.Outcome
  evolve : S.State → S.Action → FinDist S.State
  cost : S.Action → Nat
  obsRowMass : Nat
  evolveRowMass : Nat
  initial_pos : ∀ e, 0 < totalWeight (initial e)
  obsRowMass_pos : 0 < obsRowMass
  evolveRowMass_pos : 0 < evolveRowMass
  obs_mass : ∀ s, totalWeight (observe s) = obsRowMass
  evolve_mass : ∀ s a, totalWeight (evolve s a) = evolveRowMass

def transportVStochRep {Ext : Type u} {S T : VSig.{v, w, x}}
    (e : VSigEquiv S T) (M : VStochRep Ext S) : VStochRep Ext T where
  initial := fun ext => mapDist e.stateEq.toFun (M.initial ext)
  observe := fun t => mapDist e.outcomeEq.toFun (M.observe (e.stateEq.invFun t))
  evolve := fun t b => mapDist e.stateEq.toFun (M.evolve (e.stateEq.invFun t) (e.actionEq.invFun b))
  cost := fun b => M.cost (e.actionEq.invFun b)
  obsRowMass := M.obsRowMass
  evolveRowMass := M.evolveRowMass
  initial_pos := fun ext => by rw [totalWeight_mapDist]; exact M.initial_pos ext
  obsRowMass_pos := M.obsRowMass_pos
  evolveRowMass_pos := M.evolveRowMass_pos
  obs_mass := fun t => by rw [totalWeight_mapDist]; exact M.obs_mass _
  evolve_mass := fun t b => by rw [totalWeight_mapDist]; exact M.evolve_mass _ _

structure VTotalRep (Ext : Type u) where
  sig : VSig.{v, w, x}
  model : VStochRep Ext sig

structure VTotalIso {Ext : Type u} (M N : VTotalRep Ext) where
  base : VSigEquiv M.sig N.sig
  initial_pres : ∀ ext,
    letI := N.sig.stateDec
    distEq (mapDist base.stateEq.toFun (M.model.initial ext)) (N.model.initial ext)
  observe_pres : ∀ s,
    letI := N.sig.outcomeDec
    distEq (mapDist base.outcomeEq.toFun (M.model.observe s)) (N.model.observe (base.stateEq.toFun s))
  evolve_pres : ∀ s a,
    letI := N.sig.stateDec
    distEq (mapDist base.stateEq.toFun (M.model.evolve s a))
           (N.model.evolve (base.stateEq.toFun s) (base.actionEq.toFun a))
  cost_pres : ∀ a, N.model.cost (base.actionEq.toFun a) = M.model.cost a

theorem VTotalIso.ext {Ext : Type u} {M N : VTotalRep Ext}
    {h₁ h₂ : VTotalIso M N} (hb : h₁.base = h₂.base) : h₁ = h₂ := by
  cases h₁; cases h₂; subst hb; rfl

theorem distEq_map_vequiv {α : Type u} {β : Type v}
    [DecidableEq α] [DecidableEq β]
    (e : VEquiv α β) {d₁ d₂ : FinDist α} (h : distEq d₁ d₂) :
    distEq (mapDist e.toFun d₁) (mapDist e.toFun d₂) :=
  channel_map_preserves_distEq e.toFun h

private theorem mapDist_id' {α : Type u} (d : FinDist α) : mapDist id d = d :=
  mapDist_id d

namespace VTotalIso

def refl {Ext : Type u} (M : VTotalRep Ext) : VTotalIso M M where
  base := VSigEquiv.refl M.sig
  initial_pres := fun ext => by
    letI := M.sig.stateDec
    dsimp [VSigEquiv.refl, VEquiv.refl]
    rw [mapDist_id']
    intro _; rfl
  observe_pres := fun s => by
    letI := M.sig.outcomeDec
    dsimp [VSigEquiv.refl, VEquiv.refl]
    rw [mapDist_id']
    intro _; rfl
  evolve_pres := fun s a => by
    letI := M.sig.stateDec
    dsimp [VSigEquiv.refl, VEquiv.refl]
    rw [mapDist_id']
    intro _; rfl
  cost_pres := fun _ => rfl

def trans {Ext : Type u} {M N K : VTotalRep Ext}
    (h₁ : VTotalIso M N) (h₂ : VTotalIso N K) : VTotalIso M K where
  base := VSigEquiv.trans h₁.base h₂.base
  initial_pres := fun ext => by
    letI := N.sig.stateDec; letI := K.sig.stateDec
    dsimp [VSigEquiv.trans, VEquiv.trans]
    rw [← mapDist_comp h₂.base.stateEq.toFun h₁.base.stateEq.toFun]
    exact distEq_trans_of_pos (by rw [totalWeight_mapDist]; exact N.model.initial_pos ext)
      (distEq_map_vequiv h₂.base.stateEq (h₁.initial_pres ext)) (h₂.initial_pres ext)
  observe_pres := fun s => by
    letI := N.sig.outcomeDec; letI := K.sig.outcomeDec
    dsimp [VSigEquiv.trans, VEquiv.trans]
    rw [← mapDist_comp h₂.base.outcomeEq.toFun h₁.base.outcomeEq.toFun]
    exact distEq_trans_of_pos
      (by rw [totalWeight_mapDist, N.model.obs_mass]; exact N.model.obsRowMass_pos)
      (distEq_map_vequiv h₂.base.outcomeEq (h₁.observe_pres s))
      (h₂.observe_pres (h₁.base.stateEq.toFun s))
  evolve_pres := fun s a => by
    letI := N.sig.stateDec; letI := K.sig.stateDec
    dsimp [VSigEquiv.trans, VEquiv.trans]
    rw [← mapDist_comp h₂.base.stateEq.toFun h₁.base.stateEq.toFun]
    exact distEq_trans_of_pos
      (by rw [totalWeight_mapDist, N.model.evolve_mass]; exact N.model.evolveRowMass_pos)
      (distEq_map_vequiv h₂.base.stateEq (h₁.evolve_pres s a))
      (h₂.evolve_pres (h₁.base.stateEq.toFun s) (h₁.base.actionEq.toFun a))
  cost_pres := fun a => by
    dsimp only [VSigEquiv.trans, VEquiv.trans]
    rw [h₂.cost_pres, h₁.cost_pres]

def symm {Ext : Type u} {M N : VTotalRep Ext} (h : VTotalIso M N) : VTotalIso N M where
  base := VSigEquiv.symm h.base
  initial_pres := fun ext => by
    letI := M.sig.stateDec; letI := N.sig.stateDec
    have hm := distEq_map_vequiv h.base.stateEq.symm (h.initial_pres ext)
    have hsym := fun x => (hm x).symm
    change distEq (mapDist h.base.stateEq.symm.toFun (N.model.initial ext))
      (mapDist h.base.stateEq.symm.toFun (mapDist h.base.stateEq.toFun (M.model.initial ext))) at hsym
    rw [VEquiv.mapDist_symm_cancel] at hsym
    exact hsym
  observe_pres := fun t => by
    letI := M.sig.outcomeDec; letI := N.sig.outcomeDec
    have hm := distEq_map_vequiv h.base.outcomeEq.symm (h.observe_pres (h.base.stateEq.invFun t))
    have hsym := fun x => (hm x).symm
    change distEq (mapDist h.base.outcomeEq.symm.toFun (N.model.observe (h.base.stateEq.toFun (h.base.stateEq.invFun t))))
      (mapDist h.base.outcomeEq.symm.toFun (mapDist h.base.outcomeEq.toFun (M.model.observe (h.base.stateEq.invFun t)))) at hsym
    rw [h.base.stateEq.right_inv, VEquiv.mapDist_symm_cancel] at hsym
    exact hsym
  evolve_pres := fun t b => by
    letI := M.sig.stateDec; letI := N.sig.stateDec
    have hm := distEq_map_vequiv h.base.stateEq.symm
      (h.evolve_pres (h.base.stateEq.invFun t) (h.base.actionEq.invFun b))
    have hsym := fun x => (hm x).symm
    change distEq (mapDist h.base.stateEq.symm.toFun
        (N.model.evolve (h.base.stateEq.toFun (h.base.stateEq.invFun t))
          (h.base.actionEq.toFun (h.base.actionEq.invFun b))))
      (mapDist h.base.stateEq.symm.toFun (mapDist h.base.stateEq.toFun
        (M.model.evolve (h.base.stateEq.invFun t) (h.base.actionEq.invFun b)))) at hsym
    rw [h.base.stateEq.right_inv, h.base.actionEq.right_inv, VEquiv.mapDist_symm_cancel] at hsym
    exact hsym
  cost_pres := fun b => by
    dsimp only [VSigEquiv.symm, VEquiv.symm]
    have hc := h.cost_pres (h.base.actionEq.invFun b)
    rw [h.base.actionEq.right_inv] at hc
    exact hc.symm

end VTotalIso

def vTotalGroupoid (Ext : Type u) : Groupoid where
  Obj := VTotalRep.{u, v, w, x} Ext
  Hom := VTotalIso.{u, v, w, x}
  id := VTotalIso.refl
  comp := VTotalIso.trans
  inv := VTotalIso.symm
  id_comp := fun f => VTotalIso.ext ((vSigGroupoid).id_comp f.base)
  comp_id := fun f => VTotalIso.ext ((vSigGroupoid).comp_id f.base)
  assoc := fun f g h => VTotalIso.ext ((vSigGroupoid).assoc f.base g.base h.base)
  inv_left := fun f => VTotalIso.ext ((vSigGroupoid).inv_left f.base)
  inv_right := fun f => VTotalIso.ext ((vSigGroupoid).inv_right f.base)

def vLift {Ext : Type u} {S T : VSig.{v, w, x}} (e : VSigEquiv S T) (M : VStochRep Ext S) :
    VTotalIso ⟨S, M⟩ ⟨T, transportVStochRep e M⟩ where
  base := e
  initial_pres := fun _ => by letI := T.stateDec; intro _; rfl
  observe_pres := fun s => by
    letI := T.outcomeDec
    dsimp [transportVStochRep]
    rw [e.stateEq.left_inv]
    intro _; rfl
  evolve_pres := fun s a => by
    letI := T.stateDec
    dsimp [transportVStochRep]
    rw [e.stateEq.left_inv, e.actionEq.left_inv]
    intro _; rfl
  cost_pres := fun a => by dsimp [transportVStochRep]; rw [e.actionEq.left_inv]

/-- Arbitrary-base-change CoCartesian universal property: for any lift `vLift e M`
    over `e : S ≃ T` and any total arrow `h : (S, M) ≅ (U, K)` whose base factors as
    `f ∘ e`, there exists a UNIQUE total arrow `u : (T, transport e M) ≅ (U, K)` over `f`
    satisfying `vLift e M ≫ u = h`. -/
theorem coCartesian_universal_exists_unique {Ext : Type u}
    {S T U : VSig.{v, w, x}} (M : VStochRep Ext S) (K : VStochRep Ext U)
    (e : VSigEquiv S T) (f : VSigEquiv T U)
    (h : VTotalIso ⟨S, M⟩ ⟨U, K⟩)
    (hbase : VSigEquiv.trans e f = h.base) :
    ∃ u : VTotalIso ⟨T, transportVStochRep e M⟩ ⟨U, K⟩,
      u.base = f ∧
      VTotalIso.trans (vLift e M) u = h ∧
      (∀ u' : VTotalIso ⟨T, transportVStochRep e M⟩ ⟨U, K⟩,
        u'.base = f → VTotalIso.trans (vLift e M) u' = h → u' = u) := by
  letI := U.stateDec
  letI := U.outcomeDec
  have hsEq : ∀ s, f.stateEq.toFun (e.stateEq.toFun s) = h.base.stateEq.toFun s := fun s =>
    congrArg (fun b : VSigEquiv S U => b.stateEq.toFun s) hbase
  have haEq : ∀ a, f.actionEq.toFun (e.actionEq.toFun a) = h.base.actionEq.toFun a := fun a =>
    congrArg (fun b : VSigEquiv S U => b.actionEq.toFun a) hbase
  have hoEq : ∀ o, f.outcomeEq.toFun (e.outcomeEq.toFun o) = h.base.outcomeEq.toFun o := fun o =>
    congrArg (fun b : VSigEquiv S U => b.outcomeEq.toFun o) hbase
  let u : VTotalIso ⟨T, transportVStochRep e M⟩ ⟨U, K⟩ :=
    { base := f
      initial_pres := fun ext => by
        letI := U.stateDec
        dsimp [transportVStochRep]
        rw [mapDist_comp]
        have hfun : (fun a => f.stateEq.toFun (e.stateEq.toFun a)) = h.base.stateEq.toFun := funext hsEq
        rw [hfun]
        exact h.initial_pres ext
      observe_pres := fun t => by
        letI := U.outcomeDec
        dsimp [transportVStochRep]
        rw [mapDist_comp]
        have hfun : (fun a => f.outcomeEq.toFun (e.outcomeEq.toFun a)) = h.base.outcomeEq.toFun := funext hoEq
        have ho := h.observe_pres (e.stateEq.invFun t)
        have hst : h.base.stateEq.toFun (e.stateEq.invFun t) = f.stateEq.toFun t := by
          rw [← hsEq (e.stateEq.invFun t), e.stateEq.right_inv]
        rw [hst] at ho
        rw [hfun]
        exact ho
      evolve_pres := fun t b => by
        letI := U.stateDec
        dsimp [transportVStochRep]
        rw [mapDist_comp]
        have hfun : (fun a => f.stateEq.toFun (e.stateEq.toFun a)) = h.base.stateEq.toFun := funext hsEq
        have hev := h.evolve_pres (e.stateEq.invFun t) (e.actionEq.invFun b)
        have hst : h.base.stateEq.toFun (e.stateEq.invFun t) = f.stateEq.toFun t := by
          rw [← hsEq (e.stateEq.invFun t), e.stateEq.right_inv]
        have hac : h.base.actionEq.toFun (e.actionEq.invFun b) = f.actionEq.toFun b := by
          rw [← haEq (e.actionEq.invFun b), e.actionEq.right_inv]
        rw [hst, hac] at hev
        rw [hfun]
        exact hev
      cost_pres := fun b => by
        dsimp [transportVStochRep]
        have hc := h.cost_pres (e.actionEq.invFun b)
        have hac : h.base.actionEq.toFun (e.actionEq.invFun b) = f.actionEq.toFun b := by
          rw [← haEq (e.actionEq.invFun b), e.actionEq.right_inv]
        rw [hac] at hc
        exact hc }
  refine ⟨u, rfl, VTotalIso.ext hbase, ?_⟩
  intro u' hbu' _
  exact VTotalIso.ext hbu'

def seqCoherenceIso {Ext : Type u} {S T U : VSig.{v, w, x}}
    (e : VSigEquiv S T) (f : VSigEquiv T U) (M : VStochRep Ext S) :
    VTotalIso ⟨U, transportVStochRep (VSigEquiv.trans e f) M⟩
              ⟨U, transportVStochRep f (transportVStochRep e M)⟩ where
  base := VSigEquiv.refl U
  initial_pres := fun ext => by
    letI := U.stateDec
    dsimp [transportVStochRep, VSigEquiv.refl, VEquiv.refl, VSigEquiv.trans, VEquiv.trans]
    rw [mapDist_id', ← mapDist_comp]
    intro _; rfl
  observe_pres := fun u => by
    letI := U.outcomeDec
    dsimp [transportVStochRep, VSigEquiv.refl, VEquiv.refl, VSigEquiv.trans, VEquiv.trans]
    rw [mapDist_id', ← mapDist_comp]
    intro _; rfl
  evolve_pres := fun u c => by
    letI := U.stateDec
    dsimp [transportVStochRep, VSigEquiv.refl, VEquiv.refl, VSigEquiv.trans, VEquiv.trans]
    rw [mapDist_id', ← mapDist_comp]
    intro _; rfl
  cost_pres := fun _ => rfl

theorem lift_comp_coherence {Ext : Type u} {S T U : VSig.{v, w, x}}
    (e : VSigEquiv S T) (f : VSigEquiv T U) (M : VStochRep Ext S) :
    VTotalIso.trans (vLift e M) (vLift f (transportVStochRep e M)) =
    VTotalIso.trans (vLift (VSigEquiv.trans e f) M) (seqCoherenceIso e f M) := by
  apply VTotalIso.ext
  apply VSigEquiv.ext <;> apply VEquiv.ext <;> intro _ <;> rfl

-- -----------------------------------------------------------------------------
-- 4b. Reachable-Support Reach(μ₀) Weakening (Answering Spike 40)
-- -----------------------------------------------------------------------------

def inSupp {α : Type u} (a : α) (d : FinDist α) : Prop :=
  ∃ w, (a, w) ∈ d ∧ 0 < w

theorem weightOf_eq_zero_of_not_inSupp {α : Type u} [DecidableEq α]
    {a : α} {d : FinDist α} (h : ¬ inSupp a d) : weightOf a d = 0 := by
  induction d with
  | nil => rfl
  | cons p rest ih =>
      rcases p with ⟨b, w⟩
      have hrest : ¬ inSupp a rest := fun ⟨w', hm, hw'⟩ =>
        h ⟨w', List.mem_cons_of_mem _ hm, hw'⟩
      have ihz := ih hrest
      simp only [weightOf, ihz, Nat.add_zero]
      by_cases hba : b = a
      · subst hba
        by_cases hw : 0 < w
        · exfalso; exact h ⟨w, List.mem_cons_self _ _, hw⟩
        · have hw0 : w = 0 := Nat.eq_zero_of_not_pos hw
          simp [hw0]
      · simp [hba]

theorem totalWeight_bindDist_of_pred {α : Type u} {β : Type v}
    (d : FinDist α) (k : α → FinDist β) (P : α → Prop) (row : Nat)
    (hd : ∀ a, inSupp a d → P a)
    (hk : ∀ a, P a → totalWeight (k a) = row) :
    totalWeight (bindDist d k) = totalWeight d * row := by
  induction d with
  | nil => simp [bindDist, totalWeight]
  | cons p rest ih =>
      rcases p with ⟨a, w⟩
      have hrest : ∀ x, inSupp x rest → P x := fun x hx =>
        hd x (by rcases hx with ⟨w', hm, hw'⟩; exact ⟨w', List.mem_cons_of_mem _ hm, hw'⟩)
      have ihr := ih hrest
      simp only [bindDist, totalWeight_append, totalWeight_scale, totalWeight, Nat.add_mul, ihr]
      by_cases hw : 0 < w
      · have hPa : P a := hd a ⟨w, List.mem_cons_self _ _, hw⟩
        rw [hk a hPa]
      · have hw0 : w = 0 := Nat.eq_zero_of_not_pos hw
        simp [hw0]

private def vSumOn {α : Type u} : List α → (α → Nat) → Nat
  | [], _ => 0
  | x :: xs, g => g x + vSumOn xs g

private theorem vSumOn_zero {α : Type u} (xs : List α) : vSumOn xs (fun _ => 0) = 0 := by
  induction xs with
  | nil => rfl
  | cons _ rest ih => simp [vSumOn, ih]

private theorem vSumOn_eq {α : Type u} (xs : List α) {g h : α → Nat}
    (heq : ∀ x ∈ xs, g x = h x) : vSumOn xs g = vSumOn xs h := by
  induction xs with
  | nil => rfl
  | cons y ys ih =>
      simp only [vSumOn, heq y (List.mem_cons_self _ _),
        ih (fun z hz => heq z (List.mem_cons_of_mem _ hz))]

private theorem vSumOn_add {α : Type u} (xs : List α) (g h : α → Nat) :
    vSumOn xs (fun x => g x + h x) = vSumOn xs g + vSumOn xs h := by
  induction xs with
  | nil => rfl
  | cons y ys ih =>
      simp only [vSumOn, ih]
      rw [Nat.add_assoc, Nat.add_assoc]
      congr 1
      rw [← Nat.add_assoc, Nat.add_comm (h y), Nat.add_assoc]

private theorem vSumOn_mul_right {α : Type u} (xs : List α) (g : α → Nat) (c : Nat) :
    vSumOn xs g * c = vSumOn xs (fun x => g x * c) := by
  induction xs with
  | nil => simp [vSumOn]
  | cons y ys ih => simp only [vSumOn, Nat.add_mul, ih]

private theorem vSumOn_mul_left {α : Type u} (xs : List α) (c : Nat) (g : α → Nat) :
    c * vSumOn xs g = vSumOn xs (fun x => c * g x) := by
  induction xs with
  | nil => simp [vSumOn]
  | cons y ys ih => simp only [vSumOn, Nat.mul_add, ih]

private theorem vSumOn_indicator {α : Type u} [DecidableEq α]
    (xs : List α) (hnodup : xs.Nodup) {x : α} (hx : x ∈ xs) (c : Nat) :
    vSumOn xs (fun a => if x = a then c else 0) = c := by
  induction xs with
  | nil => cases hx
  | cons y ys ih =>
      rw [List.nodup_cons] at hnodup
      rcases List.mem_cons.mp hx with rfl | hrest
      · have h0 : vSumOn ys (fun a => if x = a then c else 0) = 0 := by
          rw [vSumOn_eq ys (h := fun _ => 0) (fun a ha => by
            have hne : x ≠ a := fun heq => hnodup.1 (heq ▸ ha)
            simp [hne])]
          exact vSumOn_zero ys
        simp [vSumOn, h0]
      · have hne : x ≠ y := fun heq => hnodup.1 (heq ▸ hrest)
        simp [vSumOn, hne, ih hnodup.2 hrest]

private theorem weightOf_scale {α : Type u} [DecidableEq α]
    (a : α) (w : Nat) (d : FinDist α) :
    weightOf a (d.map (fun p => (p.1, w * p.2))) = w * weightOf a d := by
  induction d with
  | nil => simp [weightOf]
  | cons p rest ih =>
      rcases p with ⟨b, wp⟩
      simp only [List.map_cons, weightOf, ih]
      by_cases hba : b = a
      · simp [hba, Nat.mul_add]
      · simp [hba]

private theorem weightOf_append {α : Type u} [DecidableEq α]
    (a : α) (d₁ d₂ : FinDist α) :
    weightOf a (d₁ ++ d₂) = weightOf a d₁ + weightOf a d₂ := by
  induction d₁ with
  | nil => simp [weightOf]
  | cons p rest ih =>
      rcases p with ⟨b, w⟩
      change (if b = a then w else 0) + weightOf a (rest ++ d₂) =
        ((if b = a then w else 0) + weightOf a rest) + weightOf a d₂
      rw [ih, Nat.add_assoc]

private theorem weightOf_bindDist_eq_sumOn {α : Type u} {β : Type v}
    [DecidableEq α] [DecidableEq β]
    (xs : List α) (hnodup : xs.Nodup)
    (d : FinDist α) (k : α → FinDist β) (b : β)
    (hcov : ∀ p ∈ d, p.1 ∈ xs) :
    weightOf b (bindDist d k) = vSumOn xs (fun a => weightOf a d * weightOf b (k a)) := by
  induction d with
  | nil =>
      simp only [bindDist, weightOf]
      rw [vSumOn_eq xs (h := fun _ => 0) (fun _ _ => Nat.zero_mul _), vSumOn_zero]
  | cons p rest ih =>
      rcases p with ⟨x, w⟩
      have hx : x ∈ xs := hcov (x, w) (List.mem_cons_self _ _)
      have ih' := ih (fun q hq => hcov q (List.mem_cons_of_mem _ hq))
      simp only [bindDist, weightOf_append, weightOf_scale, ih']
      have hsplit : vSumOn xs (fun a => ((if x = a then w else 0) + weightOf a rest) * weightOf b (k a)) =
          vSumOn xs (fun a => if x = a then w * weightOf b (k x) else 0) +
          vSumOn xs (fun a => weightOf a rest * weightOf b (k a)) := by
        rw [← vSumOn_add]
        apply vSumOn_eq
        intro a _
        by_cases hxa : x = a
        · subst hxa; simp [Nat.add_mul]
        · simp [hxa]
      have hpoint : vSumOn xs (fun a => weightOf a ((x, w) :: rest) * weightOf b (k a)) =
          vSumOn xs (fun a => ((if x = a then w else 0) + weightOf a rest) * weightOf b (k a)) :=
        vSumOn_eq xs fun _ _ => rfl
      rw [hpoint, hsplit, vSumOn_indicator xs hnodup hx]

private def vDedup {α : Type u} [DecidableEq α] : List α → List α
  | [] => []
  | x :: xs => if x ∈ xs then vDedup xs else x :: vDedup xs

private theorem mem_vDedup {α : Type u} [DecidableEq α] (x : α) (xs : List α) :
    x ∈ vDedup xs ↔ x ∈ xs := by
  induction xs with
  | nil => simp [vDedup]
  | cons y ys ih =>
      dsimp [vDedup]
      by_cases hy : y ∈ ys
      · simp only [hy, ↓reduceIte, List.mem_cons]
        exact ⟨fun h => Or.inr (ih.mp h), fun h => match h with | Or.inl rfl => ih.mpr hy | Or.inr hm => ih.mpr hm⟩
      · simp only [hy, ↓reduceIte, List.mem_cons, ih]

private theorem nodup_vDedup {α : Type u} [DecidableEq α] (xs : List α) :
    (vDedup xs).Nodup := by
  induction xs with
  | nil => simp [vDedup]
  | cons y ys ih =>
      dsimp [vDedup]
      by_cases hy : y ∈ ys
      · simp [hy, ih]
      · simp only [hy, ↓reduceIte, List.nodup_cons]
        exact ⟨fun hm => hy ((mem_vDedup y ys).mp hm), ih⟩

private theorem weightOf_mapDist_eqv {α : Type u} {β : Type v}
    [DecidableEq α] [DecidableEq β]
    (e : VEquiv α β) (d : FinDist α) (a : α) :
    weightOf (e.toFun a) (mapDist e.toFun d) = weightOf a d :=
  weightOf_mapDist_inj e.toFun (fun x y h => by
    have := congrArg e.invFun h
    rwa [e.left_inv, e.left_inv] at this) a d

private theorem inSupp_of_wpos {α : Type u} [DecidableEq α]
    {a : α} {d : FinDist α} (hw : 0 < weightOf a d) : inSupp a d := by
  induction d with
  | nil => simp [weightOf] at hw
  | cons p rest ih =>
      rcases p with ⟨b, w⟩
      simp only [weightOf] at hw
      by_cases hba : b = a
      · subst hba
        by_cases hw0 : 0 < w
        · exact ⟨w, List.mem_cons_self _ _, hw0⟩
        · rw [Nat.eq_zero_of_not_pos hw0] at hw
          simp only [↓reduceIte, Nat.zero_add] at hw
          rcases ih hw with ⟨w', hm, hw'⟩
          exact ⟨w', List.mem_cons_of_mem _ hm, hw'⟩
      · simp only [hba, ↓reduceIte, Nat.zero_add] at hw
        rcases ih hw with ⟨w', hm, hw'⟩
        exact ⟨w', List.mem_cons_of_mem _ hm, hw'⟩

/-- Constructive support-relative bind congruence: equal outer distributions (`distEq`)
    and equal normalized kernels ONLY on the actual positive-weight support yield equal
    mixed distributions, even if states outside `inSupp` have disparate or zero row masses. -/
theorem bindDist_distEq_on_support {α : Type u} {β : Type v} {γ : Type w} {δ : Type x}
    [DecidableEq α] [DecidableEq β] [DecidableEq γ] [DecidableEq δ]
    (eα : VEquiv α β) (eγ : VEquiv γ δ)
    (d₁ : FinDist α) (d₂ : FinDist β)
    (k₁ : α → FinDist γ) (k₂ : β → FinDist δ)
    (P₁ : α → Prop) (P₂ : β → Prop)
    (row₁ row₂ : Nat)
    (ht₁ : 0 < totalWeight d₁) (ht₂ : 0 < totalWeight d₂)
    (hd : distEq (mapDist eα.toFun d₁) d₂)
    (hsupp₁ : ∀ a, inSupp a d₁ → P₁ a)
    (hsupp₂ : ∀ b, inSupp b d₂ → P₂ b)
    (hmass₁ : ∀ a, P₁ a → totalWeight (k₁ a) = row₁)
    (hmass₂ : ∀ b, P₂ b → totalWeight (k₂ b) = row₂)
    (hker : ∀ a, P₁ a → P₂ (eα.toFun a) →
      distEq (mapDist eγ.toFun (k₁ a)) (k₂ (eα.toFun a))) :
    distEq (mapDist eγ.toFun (bindDist d₁ k₁)) (bindDist d₂ k₂) := by
  rw [mapDist_bindDist]
  have htw₁ : totalWeight (bindDist d₁ (fun a => mapDist eγ.toFun (k₁ a))) =
      totalWeight d₁ * row₁ :=
    totalWeight_bindDist_of_pred d₁ (fun a => mapDist eγ.toFun (k₁ a)) P₁ row₁
      hsupp₁ (fun a ha => by rw [totalWeight_mapDist]; exact hmass₁ a ha)
  have htw₂ : totalWeight (bindDist d₂ k₂) = totalWeight d₂ * row₂ :=
    totalWeight_bindDist_of_pred d₂ k₂ P₂ row₂ hsupp₂ hmass₂
  let xs := vDedup (d₁.map Prod.fst ++ (mapDist eα.invFun d₂).map Prod.fst)
  have hnodup : xs.Nodup := nodup_vDedup _
  have hcov₁ : ∀ p ∈ d₁, p.1 ∈ xs := fun p hp =>
    (mem_vDedup p.1 _).mpr (List.mem_append_left _ (List.mem_map_of_mem Prod.fst hp))
  have hcov₂' : ∀ p ∈ mapDist eα.invFun d₂, p.1 ∈ xs := fun p hp =>
    (mem_vDedup p.1 _).mpr (List.mem_append_right _ (List.mem_map_of_mem Prod.fst hp))
  intro c
  have hbw₁ := weightOf_bindDist_eq_sumOn xs hnodup d₁ (fun a => mapDist eγ.toFun (k₁ a)) c hcov₁
  have hbw₂_map := weightOf_bindDist_eq_sumOn xs hnodup (mapDist eα.invFun d₂) (fun a => k₂ (eα.toFun a)) c hcov₂'
  have hbind₂ : bindDist d₂ k₂ = bindDist (mapDist eα.invFun d₂) (fun a => k₂ (eα.toFun a)) := by
    rw [bindDist_mapDist]
    apply bindDist_congr d₂
    intro b; rw [eα.right_inv]
  rw [htw₁, htw₂, hbind₂, hbw₂_map, hbw₁]
  rw [vSumOn_mul_right, vSumOn_mul_right]
  apply vSumOn_eq
  intro a _
  have hw2 : weightOf a (mapDist eα.invFun d₂) = weightOf (eα.toFun a) d₂ := by
    have := weightOf_mapDist_eqv eα.symm d₂ (eα.toFun a)
    dsimp [VEquiv.symm] at this
    rwa [eα.left_inv] at this
  rw [hw2]
  have houter := hd (eα.toFun a)
  rw [weightOf_mapDist_eqv, totalWeight_mapDist] at houter
  by_cases hw1 : 0 < weightOf a d₁
  · by_cases hw2 : 0 < weightOf (eα.toFun a) d₂
    · have hs1 : inSupp a d₁ := inSupp_of_wpos hw1
      have hs2 : inSupp (eα.toFun a) d₂ := inSupp_of_wpos hw2
      have hker_a := hker a (hsupp₁ a hs1) (hsupp₂ _ hs2) c
      rw [totalWeight_mapDist, hmass₁ a (hsupp₁ a hs1), hmass₂ (eα.toFun a) (hsupp₂ _ hs2)] at hker_a
      calc
        weightOf a d₁ * weightOf c (mapDist eγ.toFun (k₁ a)) * (totalWeight d₂ * row₂)
            = (weightOf a d₁ * totalWeight d₂) * (weightOf c (mapDist eγ.toFun (k₁ a)) * row₂) := by ac_rfl
        _ = (weightOf (eα.toFun a) d₂ * totalWeight d₁) * (weightOf c (k₂ (eα.toFun a)) * row₁) := by
              rw [houter, hker_a]
        _ = (weightOf (eα.toFun a) d₂ * weightOf c (k₂ (eα.toFun a))) * (totalWeight d₁ * row₁) := by ac_rfl
    · have hz2 : weightOf (eα.toFun a) d₂ = 0 := Nat.eq_zero_of_not_pos hw2
      rw [hz2, Nat.zero_mul] at houter
      have hz1 : weightOf a d₁ = 0 := (Nat.mul_eq_zero.mp houter).resolve_right (Nat.ne_of_gt ht₂)
      simp [hz1, hz2]
  · have hz1 : weightOf a d₁ = 0 := Nat.eq_zero_of_not_pos hw1
    rw [hz1, Nat.zero_mul] at houter
    have hz2 : weightOf (eα.toFun a) d₂ = 0 := (Nat.mul_eq_zero.mp houter.symm).resolve_right (Nat.ne_of_gt ht₁)
    simp [hz1, hz2]

structure OpenMarkovModel (Ext : Type u) (S : VSig.{v, w, x}) where
  initial : Ext → FinDist S.State
  observe : S.State → FinDist S.Outcome
  evolve : S.State → S.Action → FinDist S.State
  cost : S.Action → Nat
  initial_pos : ∀ ext, 0 < totalWeight (initial ext)

inductive ReachableState {Ext : Type u} {S : VSig.{v, w, x}}
    (M : OpenMarkovModel Ext S) (ext : Ext) : S.State → Prop
  | init {s : S.State} : inSupp s (M.initial ext) → ReachableState M ext s
  | step {s s' : S.State} (a : S.Action) :
      ReachableState M ext s → inSupp s' (M.evolve s a) → ReachableState M ext s'

def ReachableUniform {Ext : Type u} {S : VSig.{v, w, x}}
    (M : OpenMarkovModel Ext S) (ext : Ext) (obsMass evMass : Nat) : Prop :=
  0 < obsMass ∧ 0 < evMass ∧
  (∀ s, ReachableState M ext s → totalWeight (M.observe s) = obsMass) ∧
  (∀ s a, ReachableState M ext s → totalWeight (M.evolve s a) = evMass)

def openTrace {Ext : Type u} {S : VSig.{v, w, x}} (M : OpenMarkovModel Ext S) :
    List S.Action → FinDist S.State → FinDist (List S.Outcome)
  | [], d => bindDist d fun s => mapDist (fun o => [o]) (M.observe s)
  | a :: rest, d =>
      bindDist d fun s =>
        bindDist (M.observe s) fun o =>
          bindDist (M.evolve s a) fun s' =>
            mapDist (fun ts => o :: ts) (openTrace M rest (dirac s'))

theorem totalWeight_bindDist_pos_on_supp {α : Type u} {β : Type v}
    (d : FinDist α) (k : α → FinDist β)
    (hd : 0 < totalWeight d)
    (hk : ∀ a, inSupp a d → 0 < totalWeight (k a)) :
    0 < totalWeight (bindDist d k) := by
  induction d with
  | nil => simp [totalWeight] at hd
  | cons p rest ih =>
      rcases p with ⟨a, w⟩
      simp only [bindDist, totalWeight_append, totalWeight_scale]
      simp only [totalWeight] at hd
      by_cases hw : 0 < w
      · have hkpos := hk a ⟨w, List.mem_cons_self _ _, hw⟩
        have hmul : 0 < w * totalWeight (k a) := Nat.mul_pos hw hkpos
        exact Nat.add_pos_left hmul _
      · have hrest : 0 < totalWeight rest := by
          rwa [Nat.eq_zero_of_not_pos hw, Nat.zero_add] at hd
        have hkrest : ∀ x, inSupp x rest → 0 < totalWeight (k x) := fun x hx =>
          hk x (by rcases hx with ⟨w', hm, hw'⟩; exact ⟨w', List.mem_cons_of_mem _ hm, hw'⟩)
        have hrec := ih hrest hkrest
        exact Nat.add_pos_right _ hrec

theorem openTrace_pos_on_reach {Ext : Type u} {S : VSig.{v, w, x}}
    (M : OpenMarkovModel Ext S) (ext : Ext) (obsMass evMass : Nat)
    (hunif : ReachableUniform M ext obsMass evMass)
    (actions : List S.Action) (d : FinDist S.State)
    (hdPos : 0 < totalWeight d)
    (hdSupp : ∀ s, inSupp s d → ReachableState M ext s) :
    0 < totalWeight (openTrace M actions d) := by
  rcases hunif with ⟨hobs, hev, hmObs, hmEv⟩
  induction actions generalizing d with
  | nil =>
      simp only [openTrace]
      rw [totalWeight_bindDist_of_pred d _ (ReachableState M ext) obsMass hdSupp
        (fun s hs => by rw [totalWeight_mapDist]; exact hmObs s hs)]
      exact Nat.mul_pos hdPos hobs
  | cons a rest ih =>
      simp only [openTrace]
      refine totalWeight_bindDist_pos_on_supp d _ hdPos ?_
      intro s hs
      have hRs := hdSupp s hs
      refine totalWeight_bindDist_pos_on_supp (M.observe s) _ (by rw [hmObs s hRs]; exact hobs) ?_
      intro _ _
      refine totalWeight_bindDist_pos_on_supp (M.evolve s a) _ (by rw [hmEv s a hRs]; exact hev) ?_
      intro s' hs'
      rw [totalWeight_mapDist]
      exact ih (dirac s') (by rw [totalWeight_dirac]; exact Nat.zero_lt_one) (fun x hx => by
        rcases hx with ⟨w, hm, _⟩
        simp only [dirac, List.mem_cons, List.not_mem_nil, or_false] at hm
        have hxs' : x = s' := congrArg Prod.fst hm
        rw [hxs']
        exact ReachableState.step a hRs hs')

def ListMapVEquiv {α : Type u} {β : Type v} (e : VEquiv α β) :
    VEquiv (List α) (List β) where
  toFun := List.map e.toFun
  invFun := List.map e.invFun
  left_inv := fun xs => by
    induction xs with
    | nil => rfl
    | cons x rest ih => simp [List.map, e.left_inv, ih]
  right_inv := fun ys => by
    induction ys with
    | nil => rfl
    | cons y rest ih => simp [List.map, e.right_inv, ih]

theorem totalWeight_openTrace_of_pred {Ext : Type u} {S : VSig.{v, w, x}}
    (M : OpenMarkovModel Ext S) (ext : Ext) (obsMass evMass : Nat)
    (hunif : ReachableUniform M ext obsMass evMass)
    (actions : List S.Action) (d : FinDist S.State)
    (hdSupp : ∀ s, inSupp s d → ReachableState M ext s) :
    totalWeight (openTrace M actions d) =
      totalWeight d * ((obsMass * evMass) ^ actions.length * obsMass) := by
  rcases hunif with ⟨_, _, hmObs, hmEv⟩
  induction actions generalizing d with
  | nil =>
      simp only [openTrace, List.length_nil, Nat.pow_zero, Nat.one_mul]
      exact totalWeight_bindDist_of_pred d _ (ReachableState M ext) obsMass hdSupp
        (fun s hs => by rw [totalWeight_mapDist]; exact hmObs s hs)
  | cons a rest ih =>
      simp only [openTrace, List.length_cons]
      let innerMass := (obsMass * evMass) ^ rest.length * obsMass
      have hmid : ∀ s, ReachableState M ext s →
          totalWeight (bindDist (M.observe s) fun o =>
            bindDist (M.evolve s a) fun s' =>
              mapDist (fun ts => o :: ts) (openTrace M rest (dirac s'))) =
          obsMass * (evMass * innerMass) := by
        intro s hs
        rw [totalWeight_bindDist_of_pred (M.observe s) _ (fun _ => True) (evMass * innerMass)
          (fun _ _ => trivial) ?_]
        · rw [hmObs s hs]
        · intro _ _
          rw [totalWeight_bindDist_of_pred (M.evolve s a) _ (ReachableState M ext) innerMass
            (fun s' hs' => ReachableState.step a hs hs') ?_]
          · rw [hmEv s a hs]
          · intro s' hs'
            rw [totalWeight_mapDist]
            have ihs := ih (dirac s') (fun x hx => by
              rcases hx with ⟨w, hm, _⟩
              simp only [dirac, List.mem_cons, List.not_mem_nil, or_false] at hm
              have hxs' : x = s' := congrArg Prod.fst hm
              rw [hxs']; exact hs')
            simpa [totalWeight_dirac, innerMass] using ihs
      rw [totalWeight_bindDist_of_pred d _ (ReachableState M ext)
        (obsMass * (evMass * innerMass)) hdSupp hmid]
      have hpow : (obsMass * evMass) ^ (rest.length + 1) * obsMass =
          obsMass * (evMass * innerMass) := by
        dsimp [innerMass]
        rw [Nat.pow_succ]
        ac_rfl
      rw [hpow]

private theorem openTrace_covariant_aux {Ext : Type u} {S T : VSig.{v, w, x}}
    (M₁ : OpenMarkovModel Ext S) (M₂ : OpenMarkovModel Ext T)
    (base : VSigEquiv S T) (ext : Ext) (obs₁ ev₁ obs₂ ev₂ : Nat)
    (hu₁ : ReachableUniform M₁ ext obs₁ ev₁)
    (hu₂ : ReachableUniform M₂ ext obs₂ ev₂)
    (hobs : ∀ s, ReachableState M₁ ext s → ReachableState M₂ ext (base.stateEq.toFun s) →
      letI := T.outcomeDec
      distEq (mapDist base.outcomeEq.toFun (M₁.observe s)) (M₂.observe (base.stateEq.toFun s)))
    (hev : ∀ s a, ReachableState M₁ ext s → ReachableState M₂ ext (base.stateEq.toFun s) →
      letI := T.stateDec
      distEq (mapDist base.stateEq.toFun (M₁.evolve s a)) (M₂.evolve (base.stateEq.toFun s) (base.actionEq.toFun a)))
    (actions : List S.Action) (d₁ : FinDist S.State) (d₂ : FinDist T.State)
    (hd₁ : 0 < totalWeight d₁) (hd₂ : 0 < totalWeight d₂)
    (hs₁ : ∀ s, inSupp s d₁ → ReachableState M₁ ext s)
    (hs₂ : ∀ t, inSupp t d₂ → ReachableState M₂ ext t)
    (hdEq : letI := T.stateDec; distEq (mapDist base.stateEq.toFun d₁) d₂) :
    letI := T.outcomeDec
    distEq (mapDist (List.map base.outcomeEq.toFun) (openTrace M₁ actions d₁))
           (openTrace M₂ (actions.map base.actionEq.toFun) d₂) := by
  letI := S.stateDec; letI := S.outcomeDec
  letI := T.stateDec; letI := T.outcomeDec
  have hobs1 := hu₁.1; have hev1 := hu₁.2.1; have hmObs1 := hu₁.2.2.1; have hmEv1 := hu₁.2.2.2
  have hobs2 := hu₂.1; have hev2 := hu₂.2.1; have hmObs2 := hu₂.2.2.1; have hmEv2 := hu₂.2.2.2
  induction actions generalizing d₁ d₂ with
  | nil =>
      simp only [List.map_nil, openTrace]
      exact bindDist_distEq_on_support base.stateEq (ListMapVEquiv base.outcomeEq)
        d₁ d₂ (fun s => mapDist (fun o => [o]) (M₁.observe s))
        (fun t => mapDist (fun o => [o]) (M₂.observe t))
        (ReachableState M₁ ext) (ReachableState M₂ ext) obs₁ obs₂ hd₁ hd₂ hdEq hs₁ hs₂
        (fun s hs => by rw [totalWeight_mapDist]; exact hmObs1 s hs)
        (fun t ht => by rw [totalWeight_mapDist]; exact hmObs2 t ht)
        (fun s hRs1 hRs2 => by
          dsimp only [ListMapVEquiv]
          rw [mapDist_comp]
          have hfn : (fun a => List.map base.outcomeEq.toFun [a]) =
              (fun a => [base.outcomeEq.toFun a]) := rfl
          rw [hfn, ← mapDist_comp (fun o => [o]) base.outcomeEq.toFun (M₁.observe s)]
          exact channel_map_preserves_distEq (fun o => [o]) (hobs s hRs1 hRs2))
  | cons a rest ih =>
      simp only [List.map_cons, openTrace]
      let m₁ := (obs₁ * ev₁) ^ rest.length * obs₁
      let m₂ := (obs₂ * ev₂) ^ rest.length * obs₂
      have hmMass₁ : ∀ s, ReachableState M₁ ext s →
          totalWeight (bindDist (M₁.observe s) fun o =>
            bindDist (M₁.evolve s a) fun s' =>
              mapDist (fun ts => o :: ts) (openTrace M₁ rest (dirac s'))) = obs₁ * (ev₁ * m₁) := by
        intro s hs
        rw [totalWeight_bindDist_of_pred (M₁.observe s) _ (fun _ => True) (ev₁ * m₁) (fun _ _ => trivial) ?_]
        · rw [hmObs1 s hs]
        · intro _ _
          rw [totalWeight_bindDist_of_pred (M₁.evolve s a) _ (ReachableState M₁ ext) m₁
            (fun s' hs' => ReachableState.step a hs hs') ?_]
          · rw [hmEv1 s a hs]
          · intro s' hs'
            rw [totalWeight_mapDist, totalWeight_openTrace_of_pred M₁ ext obs₁ ev₁ hu₁ rest (dirac s')
              (fun x hx => by
                rcases hx with ⟨w, hm, _⟩
                simp only [dirac, List.mem_cons, List.not_mem_nil, or_false] at hm
                have hxs' : x = s' := congrArg Prod.fst hm
                rw [hxs']; exact hs')]
            simp [totalWeight_dirac, m₁]
      have hmMass₂ : ∀ t, ReachableState M₂ ext t →
          totalWeight (bindDist (M₂.observe t) fun o' =>
            bindDist (M₂.evolve t (base.actionEq.toFun a)) fun t' =>
              mapDist (fun ts => o' :: ts) (openTrace M₂ (rest.map base.actionEq.toFun) (dirac t'))) =
          obs₂ * (ev₂ * m₂) := by
        intro t ht
        rw [totalWeight_bindDist_of_pred (M₂.observe t) _ (fun _ => True) (ev₂ * m₂) (fun _ _ => trivial) ?_]
        · rw [hmObs2 t ht]
        · intro _ _
          rw [totalWeight_bindDist_of_pred (M₂.evolve t (base.actionEq.toFun a)) _ (ReachableState M₂ ext) m₂
            (fun t' ht' => ReachableState.step (base.actionEq.toFun a) ht ht') ?_]
          · rw [hmEv2 t (base.actionEq.toFun a) ht]
          · intro t' ht'
            rw [totalWeight_mapDist, totalWeight_openTrace_of_pred M₂ ext obs₂ ev₂ hu₂
              (rest.map base.actionEq.toFun) (dirac t')
              (fun x hx => by
                rcases hx with ⟨w, hm, _⟩
                simp only [dirac, List.mem_cons, List.not_mem_nil, or_false] at hm
                have hxt' : x = t' := congrArg Prod.fst hm
                rw [hxt']; exact ht')]
            simp [totalWeight_dirac, List.length_map, m₂]
      refine bindDist_distEq_on_support base.stateEq (ListMapVEquiv base.outcomeEq)
        d₁ d₂
        (fun s => bindDist (M₁.observe s) fun o =>
          bindDist (M₁.evolve s a) fun s' =>
            mapDist (fun ts => o :: ts) (openTrace M₁ rest (dirac s')))
        (fun t => bindDist (M₂.observe t) fun o' =>
          bindDist (M₂.evolve t (base.actionEq.toFun a)) fun t' =>
            mapDist (fun ts => o' :: ts) (openTrace M₂ (rest.map base.actionEq.toFun) (dirac t')))
        (ReachableState M₁ ext) (ReachableState M₂ ext)
        (obs₁ * (ev₁ * m₁)) (obs₂ * (ev₂ * m₂)) hd₁ hd₂ hdEq hs₁ hs₂ hmMass₁ hmMass₂ ?_
      intro s hs₁' hs₂'
      refine bindDist_distEq_on_support base.outcomeEq (ListMapVEquiv base.outcomeEq)
        (M₁.observe s) (M₂.observe (base.stateEq.toFun s))
        (fun o => bindDist (M₁.evolve s a) fun s' =>
          mapDist (fun ts => o :: ts) (openTrace M₁ rest (dirac s')))
        (fun o' => bindDist (M₂.evolve (base.stateEq.toFun s) (base.actionEq.toFun a)) fun t' =>
          mapDist (fun ts => o' :: ts) (openTrace M₂ (rest.map base.actionEq.toFun) (dirac t')))
        (fun _ => True) (fun _ => True) (ev₁ * m₁) (ev₂ * m₂)
        (by rw [hmObs1 s hs₁']; exact hobs1)
        (by rw [hmObs2 (base.stateEq.toFun s) hs₂']; exact hobs2)
        (hobs s hs₁' hs₂') (fun _ _ => trivial) (fun _ _ => trivial)
        (fun _ _ => by
          rw [totalWeight_bindDist_of_pred (M₁.evolve s a) _ (ReachableState M₁ ext) m₁
            (fun s' hs' => ReachableState.step a hs₁' hs') (fun s' hs' => by
              rw [totalWeight_mapDist, totalWeight_openTrace_of_pred M₁ ext obs₁ ev₁ hu₁ rest (dirac s')
                (fun x hx => by
                  rcases hx with ⟨w, hm, _⟩
                  simp only [dirac, List.mem_cons, List.not_mem_nil, or_false] at hm
                  have hxs' : x = s' := congrArg Prod.fst hm
                  rw [hxs']; exact hs')]
              simp [totalWeight_dirac, m₁]), hmEv1 s a hs₁'])
        (fun _ _ => by
          rw [totalWeight_bindDist_of_pred (M₂.evolve (base.stateEq.toFun s) (base.actionEq.toFun a)) _
            (ReachableState M₂ ext) m₂ (fun t' ht' => ReachableState.step _ hs₂' ht') (fun t' ht' => by
              rw [totalWeight_mapDist, totalWeight_openTrace_of_pred M₂ ext obs₂ ev₂ hu₂
                (rest.map base.actionEq.toFun) (dirac t')
                (fun x hx => by
                  rcases hx with ⟨w, hm, _⟩
                  simp only [dirac, List.mem_cons, List.not_mem_nil, or_false] at hm
                  have hxt' : x = t' := congrArg Prod.fst hm
                  rw [hxt']; exact ht')]
              simp [totalWeight_dirac, List.length_map, m₂]), hmEv2 _ _ hs₂'])
        ?_
      intro o _ _
      refine bindDist_distEq_on_support base.stateEq (ListMapVEquiv base.outcomeEq)
        (M₁.evolve s a) (M₂.evolve (base.stateEq.toFun s) (base.actionEq.toFun a))
        (fun s' => mapDist (fun ts => o :: ts) (openTrace M₁ rest (dirac s')))
        (fun t' => mapDist (fun ts => base.outcomeEq.toFun o :: ts)
          (openTrace M₂ (rest.map base.actionEq.toFun) (dirac t')))
        (ReachableState M₁ ext) (ReachableState M₂ ext) m₁ m₂
        (by rw [hmEv1 s a hs₁']; exact hev1)
        (by rw [hmEv2 _ _ hs₂']; exact hev2)
        (hev s a hs₁' hs₂')
        (fun s' hs' => ReachableState.step a hs₁' hs')
        (fun t' ht' => ReachableState.step _ hs₂' ht')
        (fun s' hs' => by
          rw [totalWeight_mapDist, totalWeight_openTrace_of_pred M₁ ext obs₁ ev₁ hu₁ rest (dirac s')
            (fun x hx => by
              rcases hx with ⟨w, hm, _⟩
              simp only [dirac, List.mem_cons, List.not_mem_nil, or_false] at hm
              have hxs' : x = s' := congrArg Prod.fst hm
              rw [hxs']; exact hs')]
          simp [totalWeight_dirac, m₁])
        (fun t' ht' => by
          rw [totalWeight_mapDist, totalWeight_openTrace_of_pred M₂ ext obs₂ ev₂ hu₂
            (rest.map base.actionEq.toFun) (dirac t')
            (fun x hx => by
              rcases hx with ⟨w, hm, _⟩
              simp only [dirac, List.mem_cons, List.not_mem_nil, or_false] at hm
              have hxt' : x = t' := congrArg Prod.fst hm
              rw [hxt']; exact ht')]
          simp [totalWeight_dirac, List.length_map, m₂])
        ?_
      intro s' hRs' hRt'
      dsimp only [ListMapVEquiv]
      rw [mapDist_comp]
      have hfn : (fun a_1 => List.map base.outcomeEq.toFun (o :: a_1)) =
          (fun a_1 => base.outcomeEq.toFun o :: List.map base.outcomeEq.toFun a_1) := rfl
      rw [hfn, ← mapDist_comp (fun ts => base.outcomeEq.toFun o :: ts)
        (List.map base.outcomeEq.toFun) (openTrace M₁ rest (dirac s'))]
      refine channel_map_preserves_distEq (fun ts => base.outcomeEq.toFun o :: ts) ?_
      exact ih (dirac s') (dirac (base.stateEq.toFun s'))
        (by rw [totalWeight_dirac]; exact Nat.zero_lt_one)
        (by rw [totalWeight_dirac]; exact Nat.zero_lt_one)
        (fun x hx => by
          rcases hx with ⟨w, hm, _⟩
          simp only [dirac, List.mem_cons, List.not_mem_nil, or_false] at hm
          have hxs' : x = s' := congrArg Prod.fst hm
          rw [hxs']; exact hRs')
        (fun y hy => by
          rcases hy with ⟨w, hm, _⟩
          simp only [dirac, List.mem_cons, List.not_mem_nil, or_false] at hm
          have hyt' : y = base.stateEq.toFun s' := congrArg Prod.fst hm
          rw [hyt']; exact hRt')
        (fun _ => rfl)

theorem reachable_support_covariance {Ext : Type u} {S T : VSig.{v, w, x}}
    (M₁ : OpenMarkovModel Ext S) (M₂ : OpenMarkovModel Ext T)
    (base : VSigEquiv S T) (ext : Ext) (obs₁ ev₁ obs₂ ev₂ : Nat)
    (hu₁ : ReachableUniform M₁ ext obs₁ ev₁)
    (hu₂ : ReachableUniform M₂ ext obs₂ ev₂)
    (hinit : letI := T.stateDec; distEq (mapDist base.stateEq.toFun (M₁.initial ext)) (M₂.initial ext))
    (hobs : ∀ s, ReachableState M₁ ext s → ReachableState M₂ ext (base.stateEq.toFun s) →
      letI := T.outcomeDec
      distEq (mapDist base.outcomeEq.toFun (M₁.observe s)) (M₂.observe (base.stateEq.toFun s)))
    (hev : ∀ s a, ReachableState M₁ ext s → ReachableState M₂ ext (base.stateEq.toFun s) →
      letI := T.stateDec
      distEq (mapDist base.stateEq.toFun (M₁.evolve s a)) (M₂.evolve (base.stateEq.toFun s) (base.actionEq.toFun a)))
    (actions : List S.Action) :
    letI := T.outcomeDec
    distEq (mapDist (List.map base.outcomeEq.toFun) (openTrace M₁ actions (M₁.initial ext)))
           (openTrace M₂ (actions.map base.actionEq.toFun) (M₂.initial ext)) :=
  openTrace_covariant_aux M₁ M₂ base ext obs₁ ev₁ obs₂ ev₂ hu₁ hu₂ hobs hev actions
    (M₁.initial ext) (M₂.initial ext) (M₁.initial_pos ext) (M₂.initial_pos ext)
    (fun _ => ReachableState.init) (fun _ => ReachableState.init) hinit

def reachSig : VSig.{0, 0, 0} where
  State := Bool
  Action := Unit
  Outcome := Bool
  stateDec := inferInstance
  actionDec := inferInstance
  outcomeDec := inferInstance

def nonUniformUnreachModelA : OpenMarkovModel Unit reachSig where
  initial := fun _ => [(false, 1)]
  observe := fun | true => [(true, 1), (false, 2)] | false => [(false, 1)]
  evolve := fun | true, _ => [(true, 3)] | false, _ => [(false, 1)]
  cost := fun _ => 1
  initial_pos := fun _ => Nat.zero_lt_one

def uniformReachModelB : OpenMarkovModel Unit reachSig where
  initial := fun _ => [(false, 1)]
  observe := fun _ => [(false, 1)]
  evolve := fun _ _ => [(false, 1)]
  cost := fun _ => 1
  initial_pos := fun _ => Nat.zero_lt_one

theorem unreachable_mass_violation_still_covariant :
    (totalWeight (nonUniformUnreachModelA.observe true) ≠
       totalWeight (nonUniformUnreachModelA.observe false)) ∧
    (∀ actions : List Unit,
      letI : DecidableEq reachSig.Outcome := reachSig.outcomeDec
      distEq (mapDist (List.map id) (openTrace nonUniformUnreachModelA actions (nonUniformUnreachModelA.initial ())))
             (openTrace uniformReachModelB (actions.map id) (uniformReachModelB.initial ()))) := by
  constructor
  · intro h
    have heq : (3 : Nat) = 1 := h
    cases heq
  · intro actions
    have hReach : ∀ s, ReachableState nonUniformUnreachModelA () s → s = false := by
      intro s hs
      induction hs with
      | init hi =>
          rcases hi with ⟨w, hm, _⟩
          simp only [nonUniformUnreachModelA, List.mem_cons, List.not_mem_nil, or_false] at hm
          exact congrArg Prod.fst hm
      | step _ _ hs' ih =>
          rw [ih] at hs'
          rcases hs' with ⟨w, hm, _⟩
          simp only [nonUniformUnreachModelA, List.mem_cons, List.not_mem_nil, or_false] at hm
          exact congrArg Prod.fst hm
    have hu1 : ReachableUniform nonUniformUnreachModelA () 1 1 :=
      ⟨Nat.zero_lt_one, Nat.zero_lt_one,
       fun s hs => by rw [hReach s hs]; rfl,
       fun s _ hs => by rw [hReach s hs]; rfl⟩
    have hu2 : ReachableUniform uniformReachModelB () 1 1 :=
      ⟨Nat.zero_lt_one, Nat.zero_lt_one, fun _ _ => rfl, fun _ _ _ => rfl⟩
    letI : DecidableEq reachSig.Outcome := reachSig.outcomeDec
    letI : DecidableEq reachSig.State := reachSig.stateDec
    have hcov := reachable_support_covariance nonUniformUnreachModelA uniformReachModelB
      (VSigEquiv.refl reachSig) () 1 1 1 1 hu1 hu2
      (fun _ => by dsimp [VSigEquiv.refl, VEquiv.refl, nonUniformUnreachModelA, uniformReachModelB]; rfl)
      (fun s hs _ _ => by
        rw [hReach s hs]
        dsimp [VSigEquiv.refl, VEquiv.refl, nonUniformUnreachModelA, uniformReachModelB]; rfl)
      (fun s _ hs _ _ => by
        rw [hReach s hs]
        dsimp [VSigEquiv.refl, VEquiv.refl, nonUniformUnreachModelA, uniformReachModelB]; rfl)
      actions
    simpa [VSigEquiv.refl, VEquiv.refl] using hcov

-- =============================================================================
-- 5. Total Varying-Signature Response-Profile Functor & Global Anchor Kernel
-- =============================================================================

def VStochRep.toOpen {Ext : Type u} {S : VSig.{v, w, x}} (M : VStochRep Ext S) :
    OpenMarkovModel Ext S where
  initial := M.initial
  observe := M.observe
  evolve := M.evolve
  cost := M.cost
  initial_pos := M.initial_pos

def vTrace {Ext : Type u} {S : VSig.{v, w, x}} (M : VStochRep Ext S)
    (actions : List S.Action) (ext : Ext) : FinDist (List S.Outcome) :=
  openTrace M.toOpen actions (M.initial ext)

theorem vTrace_pos {Ext : Type u} {S : VSig.{v, w, x}} (M : VStochRep Ext S)
    (actions : List S.Action) (ext : Ext) :
    0 < totalWeight (vTrace M actions ext) :=
  openTrace_pos_on_reach M.toOpen ext M.obsRowMass M.evolveRowMass
    ⟨M.obsRowMass_pos, M.evolveRowMass_pos, fun s _ => M.obs_mass s, fun s a _ => M.evolve_mass s a⟩
    actions (M.initial ext) (M.initial_pos ext) (fun _ hx => ReachableState.init hx)

structure VProfileObj (Ext : Type u) where
  Action : Type w
  Outcome : Type x
  actionDec : DecidableEq Action
  outcomeDec : DecidableEq Outcome
  cost : Action → Nat
  eval : Ext → List Action → FinDist (List Outcome)
  eval_pos : ∀ ext actions, 0 < totalWeight (eval ext actions)

structure VProfileIso {Ext : Type u} (P Q : VProfileObj.{u, w, x} Ext) where
  actionEq : VEquiv P.Action Q.Action
  outcomeEq : VEquiv P.Outcome Q.Outcome
  cost_pres : ∀ a, Q.cost (actionEq.toFun a) = P.cost a
  law_pres : ∀ ext actions,
    letI := Q.outcomeDec
    distEq (mapDist (List.map outcomeEq.toFun) (P.eval ext actions))
           (Q.eval ext (actions.map actionEq.toFun))

theorem VProfileIso.ext {Ext : Type u} {P Q : VProfileObj.{u, w, x} Ext}
    {f g : VProfileIso P Q} (ha : f.actionEq = g.actionEq) (ho : f.outcomeEq = g.outcomeEq) :
    f = g := by
  cases f; cases g; subst ha; subst ho; rfl

private theorem list_map_cancel {α : Type u} {β : Type v} (f : α → β) (g : β → α)
    (h : ∀ x, g (f x) = x) (xs : List α) : List.map g (List.map f xs) = xs := by
  induction xs with
  | nil => rfl
  | cons a rest ih => simp [List.map, h a, ih]

namespace VProfileIso

def refl {Ext : Type u} (P : VProfileObj.{u, w, x} Ext) : VProfileIso P P where
  actionEq := VEquiv.refl P.Action
  outcomeEq := VEquiv.refl P.Outcome
  cost_pres := fun _ => rfl
  law_pres := fun ext actions => by
    letI := P.outcomeDec
    dsimp only [VEquiv.refl]
    rw [show (List.map (id : P.Outcome → P.Outcome)) = id from funext List.map_id,
        mapDist_id', List.map_id]
    intro _; rfl

def trans {Ext : Type u} {P Q R : VProfileObj.{u, w, x} Ext}
    (f : VProfileIso P Q) (g : VProfileIso Q R) : VProfileIso P R where
  actionEq := f.actionEq.trans g.actionEq
  outcomeEq := f.outcomeEq.trans g.outcomeEq
  cost_pres := fun a => by dsimp [VEquiv.trans]; rw [g.cost_pres, f.cost_pres]
  law_pres := fun ext actions => by
    letI := Q.outcomeDec; letI := R.outcomeDec
    have hf := channel_map_preserves_distEq (List.map g.outcomeEq.toFun) (f.law_pres ext actions)
    have hg := g.law_pres ext (actions.map f.actionEq.toFun)
    rw [mapDist_comp, show (fun xs => List.map g.outcomeEq.toFun (List.map f.outcomeEq.toFun xs)) =
        List.map (f.outcomeEq.trans g.outcomeEq).toFun from funext fun xs => by
          clear hf hg
          induction xs with
          | nil => rfl
          | cons o os ih => simp [VEquiv.trans, ih]] at hf
    rw [show actions.map (f.actionEq.trans g.actionEq).toFun =
        (actions.map f.actionEq.toFun).map g.actionEq.toFun from by
          clear hf hg
          induction actions with
          | nil => rfl
          | cons a as ih => simp [VEquiv.trans, ih]]
    exact distEq_trans_of_pos
      (by rw [totalWeight_mapDist]; exact Q.eval_pos ext (actions.map f.actionEq.toFun)) hf hg

def symm {Ext : Type u} {P Q : VProfileObj.{u, w, x} Ext} (f : VProfileIso P Q) :
    VProfileIso Q P where
  actionEq := f.actionEq.symm
  outcomeEq := f.outcomeEq.symm
  cost_pres := fun b => by
    dsimp [VEquiv.symm]
    have hc := f.cost_pres (f.actionEq.invFun b)
    rw [f.actionEq.right_inv] at hc
    exact hc.symm
  law_pres := fun ext actionsQ => by
    letI := P.outcomeDec; letI := Q.outcomeDec
    let actionsP := actionsQ.map f.actionEq.invFun
    have hmapA : actionsP.map f.actionEq.toFun = actionsQ :=
      list_map_cancel f.actionEq.invFun f.actionEq.toFun f.actionEq.right_inv actionsQ
    have hl := channel_map_preserves_distEq (List.map f.outcomeEq.invFun) (f.law_pres ext actionsP)
    rw [hmapA, mapDist_comp] at hl
    have hid : (fun xs => List.map f.outcomeEq.invFun (List.map f.outcomeEq.toFun xs)) = id :=
      funext (list_map_cancel f.outcomeEq.toFun f.outcomeEq.invFun f.outcomeEq.left_inv)
    rw [hid, mapDist_id'] at hl
    intro ts
    exact (hl ts).symm

end VProfileIso

def vTotalProfileGroupoid (Ext : Type u) : Groupoid where
  Obj := VProfileObj.{u, w, x} Ext
  Hom := VProfileIso
  id := VProfileIso.refl
  comp := VProfileIso.trans
  inv := VProfileIso.symm
  id_comp := fun _ => VProfileIso.ext
    (VEquiv.ext (fun _ => rfl) (fun _ => rfl))
    (VEquiv.ext (fun _ => rfl) (fun _ => rfl))
  comp_id := fun _ => VProfileIso.ext
    (VEquiv.ext (fun _ => rfl) (fun _ => rfl))
    (VEquiv.ext (fun _ => rfl) (fun _ => rfl))
  assoc := fun _ _ _ => VProfileIso.ext
    (VEquiv.ext (fun _ => rfl) (fun _ => rfl))
    (VEquiv.ext (fun _ => rfl) (fun _ => rfl))
  inv_left := fun f => VProfileIso.ext
    (VEquiv.ext (fun a => f.actionEq.right_inv a) (fun a => f.actionEq.right_inv a))
    (VEquiv.ext (fun o => f.outcomeEq.right_inv o) (fun o => f.outcomeEq.right_inv o))
  inv_right := fun f => VProfileIso.ext
    (VEquiv.ext (fun a => f.actionEq.left_inv a) (fun a => f.actionEq.left_inv a))
    (VEquiv.ext (fun o => f.outcomeEq.left_inv o) (fun o => f.outcomeEq.left_inv o))

def totalProfileObj {Ext : Type u} (M : VTotalRep.{u, v, w, x} Ext) : VProfileObj.{u, w, x} Ext where
  Action := M.sig.Action
  Outcome := M.sig.Outcome
  actionDec := M.sig.actionDec
  outcomeDec := M.sig.outcomeDec
  cost := M.model.cost
  eval := fun ext actions => vTrace M.model actions ext
  eval_pos := fun ext actions => vTrace_pos M.model actions ext

def totalProfileFunctor (Ext : Type u) :
    GroupoidFunctor (vTotalGroupoid.{u, v, w, x} Ext) (vTotalProfileGroupoid.{u, w, x} Ext) where
  obj := @totalProfileObj.{u, v, w, x} Ext
  map := fun {M N} h =>
    { actionEq := h.base.actionEq
      outcomeEq := h.base.outcomeEq
      cost_pres := h.cost_pres
      law_pres := fun ext actions =>
        reachable_support_covariance M.model.toOpen N.model.toOpen h.base ext
          M.model.obsRowMass M.model.evolveRowMass N.model.obsRowMass N.model.evolveRowMass
          ⟨M.model.obsRowMass_pos, M.model.evolveRowMass_pos,
           fun s _ => M.model.obs_mass s, fun s a _ => M.model.evolve_mass s a⟩
          ⟨N.model.obsRowMass_pos, N.model.evolveRowMass_pos,
           fun t _ => N.model.obs_mass t, fun t b _ => N.model.evolve_mass t b⟩
          (h.initial_pres ext) (fun s _ _ => h.observe_pres s)
          (fun s a _ _ => h.evolve_pres s a) actions }
  map_id := fun _ => VProfileIso.ext rfl rfl
  map_comp := fun _ _ => VProfileIso.ext rfl rfl

theorem totalProfile_transport_commutes {Ext : Type u}
    {S T : VSig.{v, w, x}} (e : VSigEquiv S T) (M : VStochRep Ext S)
    (ext : Ext) (actions : List S.Action) :
    letI := T.outcomeDec
    distEq (mapDist (List.map e.outcomeEq.toFun) (vTrace M actions ext))
           (vTrace (transportVStochRep e M) (actions.map e.actionEq.toFun) ext) :=
  ((totalProfileFunctor.{u, v, w, x} Ext).map (vLift.{u, v, w, x} e M)).law_pres ext actions

def CalibratedTotalLoop {Ext : Type u} (M : VTotalRep.{u, v, w, x} Ext)
    (h : VTotalIso M M) : Prop :=
  h.base.actionEq = VEquiv.refl M.sig.Action ∧ h.base.outcomeEq = VEquiv.refl M.sig.Outcome

def GlobalAnchorFixes {Ext Anchor : Type u}
    (κA : (M : VTotalRep.{u, v, w, x} Ext) → M.sig.State → Anchor)
    (M : VTotalRep.{u, v, w, x} Ext) (h : VTotalIso M M) : Prop :=
  ∀ s, κA M (h.base.stateEq.toFun s) = κA M s

theorem total_anchored_kernel_trivial_iff {Ext Anchor : Type u}
    (κA : (M : VTotalRep.{u, v, w, x} Ext) → M.sig.State → Anchor)
    (M : VTotalRep.{u, v, w, x} Ext) :
    (¬ ∃ h : VTotalIso M M,
      h ≠ VTotalIso.refl M ∧ CalibratedTotalLoop M h ∧ GlobalAnchorFixes κA M h) ↔
    (∀ h : VTotalIso M M,
      h ≠ VTotalIso.refl M →
      CalibratedTotalLoop M h →
      ¬ GlobalAnchorFixes κA M h) := by
  constructor
  · intro hno h hne hcal hfix
    exact hno ⟨h, hne, hcal, hfix⟩
  · rintro hcontra ⟨h, hne, hcal, hfix⟩
    exact hcontra h hne hcal hfix

theorem total_anchored_kernel_injective_eq_refl {Ext Anchor : Type u}
    (κA : (M : VTotalRep.{u, v, w, x} Ext) → M.sig.State → Anchor)
    (M : VTotalRep.{u, v, w, x} Ext)
    (hinj : ∀ s₁ s₂, κA M s₁ = κA M s₂ → s₁ = s₂)
    (h : VTotalIso M M)
    (hcal : CalibratedTotalLoop M h)
    (hfix : GlobalAnchorFixes κA M h) :
    h = VTotalIso.refl M := by
  have hto : ∀ s, h.base.stateEq.toFun s = s := fun s => hinj _ _ (hfix s)
  have hinv : ∀ s, h.base.stateEq.invFun s = s := fun s => by
    have hs := h.base.stateEq.left_inv s
    rwa [hto s] at hs
  have heq : h.base.stateEq = VEquiv.refl M.sig.State :=
    VEquiv.ext hto hinv
  exact VTotalIso.ext (VSigEquiv.ext heq hcal.1 hcal.2)

-- =============================================================================
-- 6. Strict One-Way Adequacy Hierarchy Separations
-- =============================================================================

def IsIsotropyFaithful (F : GroupoidFunctor G H) : Prop :=
  ∀ a (f g : G.Hom a a), F.map f = F.map g → f = g

def IsFaithful (F : GroupoidFunctor G H) : Prop :=
  ∀ a b (f g : G.Hom a b), F.map f = F.map g → f = g

def IsFull (F : GroupoidFunctor G H) : Prop :=
  ∀ a b (k : H.Hom (F.obj a) (F.obj b)), ∃ f : G.Hom a b, F.map f = k

def IsEssentiallySurjective (F : GroupoidFunctor G H) : Prop :=
  ∀ y : H.Obj, ∃ x : G.Obj, Nonempty (H.Hom (F.obj x) y)

def discreteTwoGroupoid : Groupoid.{0, 0} where
  Obj := Bool
  Hom := fun a b => PLift (a = b)
  id := fun _ => ⟨rfl⟩
  comp := fun f g => ⟨f.down.trans g.down⟩
  inv := fun f => ⟨f.down.symm⟩
  id_comp := fun _ => rfl
  comp_id := fun _ => rfl
  assoc := fun _ _ _ => rfl
  inv_left := fun _ => rfl
  inv_right := fun _ => rfl

def indiscreteTwoGroupoid : Groupoid.{0, 0} where
  Obj := Bool
  Hom := fun _ _ => Unit
  id := fun _ => ()
  comp := fun _ _ => ()
  inv := fun _ => ()
  id_comp := fun _ => rfl
  comp_id := fun _ => rfl
  assoc := fun _ _ _ => rfl
  inv_left := fun _ => rfl
  inv_right := fun _ => rfl

def discToIndiscFunctor : GroupoidFunctor discreteTwoGroupoid indiscreteTwoGroupoid where
  obj := id
  map := fun _ => ()
  map_id := fun _ => rfl
  map_comp := fun _ _ => rfl

def discToTrivialFunctor : GroupoidFunctor discreteTwoGroupoid trivialAutomorphismGroupoid where
  obj := fun _ => ()
  map := fun _ => ()
  map_id := fun _ => rfl
  map_comp := fun _ _ => rfl

def trivialToDiscFunctor : GroupoidFunctor trivialAutomorphismGroupoid discreteTwoGroupoid where
  obj := fun _ => false
  map := fun _ => ⟨rfl⟩
  map_id := fun _ => rfl
  map_comp := fun _ _ => rfl

theorem faithful_not_full :
    IsIsotropyFaithful discToIndiscFunctor ∧
    IsFaithful discToIndiscFunctor ∧
    ¬ IsFull discToIndiscFunctor := by
  refine ⟨fun _ ⟨_⟩ ⟨_⟩ _ => rfl, fun _ _ ⟨_⟩ ⟨_⟩ _ => rfl, ?_⟩
  intro hfull
  obtain ⟨⟨heq⟩, _⟩ := hfull false true ()
  exact Bool.noConfusion heq

theorem faithful_collapses_nonIso_objects :
    IsFaithful discToTrivialFunctor ∧
    IsEssentiallySurjective discToTrivialFunctor ∧
    ¬ IsFull discToTrivialFunctor ∧
    (¬ Nonempty (discreteTwoGroupoid.Hom false true) ∧
      Nonempty (trivialAutomorphismGroupoid.Hom
        (discToTrivialFunctor.obj false) (discToTrivialFunctor.obj true))) := by
  refine ⟨fun _ _ ⟨_⟩ ⟨_⟩ _ => rfl, fun _ => ⟨false, ⟨()⟩⟩, ?_, ?_, ⟨()⟩⟩
  · intro hfull
    obtain ⟨⟨heq⟩, _⟩ := hfull false true ()
    exact Bool.noConfusion heq
  · rintro ⟨⟨heq⟩⟩
    exact Bool.noConfusion heq

theorem fullFaithful_not_essSurj :
    IsFaithful trivialToDiscFunctor ∧
    IsFull trivialToDiscFunctor ∧
    ¬ IsEssentiallySurjective trivialToDiscFunctor := by
  refine ⟨fun _ _ f g _ => by cases f; cases g; rfl, fun _ _ ⟨_⟩ => ⟨(), rfl⟩, ?_⟩
  intro hess
  obtain ⟨_, ⟨⟨heq⟩⟩⟩ := hess true
  exact Bool.noConfusion heq

end Cerp.ContextualRingDescent
