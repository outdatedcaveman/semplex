import GroundedSemiosisCategory
import OperationalInstitutionBridge

/-!
# Contravariant coarse-graining morphisms for grounded semiosis

Separates biconditional embeddings (`Cerp.GroundedSemiosisCategory.GroundedSemiosisHom`)
from resource-refinement / budget coarse-graining morphisms (`GroundedSemiosisCoarseGraining`),
where syntax/claims map covariantly (`b1 <= b2`) while model worlds/referents map
contravariantly (`forgetReferent : ReferentSpace P b2 -> ReferentSpace P b1`), satisfying
institutional satisfaction invariance.
-/

namespace Cerp.GroundedSemiosisCoarseGraining

open Cerp.SemanticFibrations
open Cerp.SemanticYoneda.GeneralCategory
open Cerp.OperationalSemioticScaffold
open Cerp.InterventionGrounding
open Cerp.OperationalReference
open Cerp.OperationalSatisfaction
open Cerp.OperationalInstitutionBridge

universe u v w x y

/-- Institutional coarse-graining morphism between grounded semiosis models:
    signs, claims, and contexts refine covariantly (`M -> N`), while world/referent
    models reduce contravariantly (`N.World -> M.World`). -/
structure GroundedSemiosisCoarseGraining
    (M N : GroundedSemiosis.{u,v,w,x}) where
  signMap : M.Sign → N.Sign
  claimMap : M.Claim → N.Claim
  contextMap : M.Context → N.Context
  worldReduct : N.World → M.World
  expresses_commutes : ∀ s c,
    claimMap (M.expresses s c) = N.expresses (signMap s) (contextMap c)
  refers_reduct : ∀ s w,
    M.refers s (worldReduct w) → N.refers (signMap s) w
  satisfies_reduct_iff : ∀ cl w,
    M.satisfies cl (worldReduct w) ↔ N.satisfies (claimMap cl) w
  evidenceMap : ∀ s c w,
    M.Evidence s c (worldReduct w) → N.Evidence (signMap s) (contextMap c) w

namespace GroundedSemiosisCoarseGraining

def id (M : GroundedSemiosis.{u,v,w,x}) : GroundedSemiosisCoarseGraining M M where
  signMap := fun s => s
  claimMap := fun c => c
  contextMap := fun c => c
  worldReduct := fun w => w
  expresses_commutes := by intro _ _; rfl
  refers_reduct := by intro _ _ h; exact h
  satisfies_reduct_iff := by intro _ _; rfl
  evidenceMap := fun _ _ _ ev => ev

def comp {M N K : GroundedSemiosis.{u,v,w,x}}
    (f : GroundedSemiosisCoarseGraining M N)
    (g : GroundedSemiosisCoarseGraining N K) :
    GroundedSemiosisCoarseGraining M K where
  signMap := g.signMap ∘ f.signMap
  claimMap := g.claimMap ∘ f.claimMap
  contextMap := g.contextMap ∘ f.contextMap
  worldReduct := f.worldReduct ∘ g.worldReduct
  expresses_commutes := by
    intro s c
    change g.claimMap (f.claimMap (M.expresses s c)) =
      K.expresses (g.signMap (f.signMap s)) (g.contextMap (f.contextMap c))
    rw [f.expresses_commutes, g.expresses_commutes]
  refers_reduct := by
    intro s w h
    exact g.refers_reduct (f.signMap s) w (f.refers_reduct s (g.worldReduct w) h)
  satisfies_reduct_iff := by
    intro cl w
    exact (f.satisfies_reduct_iff cl (g.worldReduct w)).trans
      (g.satisfies_reduct_iff (f.claimMap cl) w)
  evidenceMap := by
    intro s c w ev
    exact g.evidenceMap (f.signMap s) (f.contextMap c) w
      (f.evidenceMap s c (g.worldReduct w) ev)

end GroundedSemiosisCoarseGraining

/-- Category of grounded semiosis models equipped with contravariant coarse-graining morphisms. -/
def groundedSemiosisCoarseCategory :
    SemCategory.{max (u + 1) (max (v + 1) (max (w + 1) (x + 1))),
      max u (max v (max w x))} where
  Obj := GroundedSemiosis.{u,v,w,x}
  Hom := GroundedSemiosisCoarseGraining
  id := GroundedSemiosisCoarseGraining.id
  comp := GroundedSemiosisCoarseGraining.comp
  id_comp := by
    intro M N f
    cases f
    rfl
  comp_id := by
    intro M N f
    cases f
    rfl
  assoc := by
    intro A B C D f g h
    cases f
    cases g
    cases h
    rfl

theorem coarse_content_truth_iff {M N : GroundedSemiosis.{u,v,w,x}}
    (f : GroundedSemiosisCoarseGraining M N)
    (s : M.Sign) (c : M.Context) (w : N.World) :
    ContentTrue M s c (f.worldReduct w) ↔
      ContentTrue N (f.signMap s) (f.contextMap c) w := by
  unfold ContentTrue
  have hs := f.satisfies_reduct_iff (M.expresses s c) w
  simpa [f.expresses_commutes] using hs

theorem coarse_grounded_assertion_mp {M N : GroundedSemiosis.{u,v,w,x}}
    (f : GroundedSemiosisCoarseGraining M N)
    (s : M.Sign) (c : M.Context) (w : N.World)
    (h : GroundedAssertionTrue M s c (f.worldReduct w)) :
    GroundedAssertionTrue N (f.signMap s) (f.contextMap c) w :=
  ⟨f.refers_reduct s w h.1, (coarse_content_truth_iff f s c w).mp h.2⟩

theorem coarse_evidence_sound {M N : GroundedSemiosis.{u,v,w,x}}
    (f : GroundedSemiosisCoarseGraining M N)
    (s : M.Sign) (c : M.Context) (w : N.World)
    (href : M.refers s (f.worldReduct w))
    (ev : M.Evidence s c (f.worldReduct w)) :
    N.satisfies (N.expresses (f.signMap s) (f.contextMap c)) w := by
  have hsound := M.evidence_sound s c (f.worldReduct w) href ev
  exact (coarse_content_truth_iff f s c w).mp hsound

/-- Package any budgeted intervention protocol into a `GroundedSemiosis` model whose
    world domain is the budget-quotiented referent space `ReferentSpace P budget`. -/
def operationalGroundedSemiosis
    {S : OperationalScaffold.{u,v,w,x,y}}
    (P : InterventionProtocol S) (budget : Nat) : GroundedSemiosis.{u,u,u,0} where
  World := ReferentSpace P budget
  Sign := ObservableClaim P budget
  Claim := ObservableClaim P budget
  Context := PUnit
  refers := fun _ _ => True
  expresses := fun cl _ => cl
  satisfies := fun cl q => satisfaction P budget cl q
  Evidence := fun cl _ q => PLift (satisfaction P budget cl q)
  evidence_sound := fun _ _ _ _ h => h.down

/-- Every budget inclusion `b1 <= b2` induces an exact contravariant coarse-graining
    morphism whose institutional satisfaction condition holds by `satisfaction_forget`. -/
def budgetRefinementCoarseGraining
    {S : OperationalScaffold.{u,v,w,x,y}}
    (P : InterventionProtocol S) {b1 b2 : Nat} (hle : b1 ≤ b2) :
    GroundedSemiosisCoarseGraining
      (operationalGroundedSemiosis P b1)
      (operationalGroundedSemiosis P b2) where
  signMap := refineClaim P hle
  claimMap := refineClaim P hle
  contextMap := fun c => c
  worldReduct := forgetReferent P hle
  expresses_commutes := by intro _ _; rfl
  refers_reduct := by intro _ _ h; exact h
  satisfies_reduct_iff := by
    intro cl q
    exact (satisfaction_forget P hle cl q).symm
  evidenceMap := by
    intro cl _ q ev
    exact PLift.up ((satisfaction_forget P hle cl q).mpr ev.down)

/-- Strict separation witness: on `revealProtocol`, budget coarse-graining `0 <= 1`
    collapses two distinct budget-1 referent classes onto the same budget-0 class,
    showing coarse-graining is genuinely non-invertible. -/
theorem reveal_budget_coarseGraining_not_injective_reduct :
    ∃ q1 q2 : (operationalGroundedSemiosis revealProtocol 1).World,
      q1 ≠ q2 ∧
      (budgetRefinementCoarseGraining revealProtocol (Nat.zero_le 1)).worldReduct q1 =
        (budgetRefinementCoarseGraining revealProtocol (Nat.zero_le 1)).worldReduct q2 := by
  let q1 : ReferentSpace revealProtocol 1 :=
    Quotient.mk (worldSetoid revealProtocol 1) (false, false)
  let q2 : ReferentSpace revealProtocol 1 :=
    Quotient.mk (worldSetoid revealProtocol 1) (true, false)
  refine ⟨q1, q2, hidden_referents_separate_at_one, ?_⟩
  change forgetReferent revealProtocol (Nat.zero_le 1) q1 =
    forgetReferent revealProtocol (Nat.zero_le 1) q2
  simp only [q1, q2, forgetReferent_mk]
  exact hidden_referents_coincide_at_zero

end Cerp.GroundedSemiosisCoarseGraining
