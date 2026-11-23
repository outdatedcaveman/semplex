import SemanticYoneda
import GroundedSemanticTransfer

/-!
# The category of grounded semantic models

Objects carry worlds, claims, reference, satisfaction, evidence, and a
soundness map. Morphisms preserve reference and satisfaction and transport
evidence. This makes semantic preservation part of the mathematical
structure rather than an informal promise.

Important boundary: the category internalizes a world parameter and its
satisfaction relation. It does not, by itself, prove that a model's World
denotes the external physical world or that its satisfaction relation is
empirically correct.
-/

namespace Cerp.GroundedSemanticCategory

open Cerp.GroundedSemanticTransfer
open Cerp.SemanticYoneda.GeneralCategory

universe u v w

/-- Structure-preserving map of grounded semantic models. -/
structure GroundedHom (M N : GroundedModel.{u,v,w}) where
  worldMap : M.World → N.World
  claimMap : M.Claim → N.Claim
  reference_commutes : ∀ c,
    worldMap (M.reference c) = N.reference (claimMap c)
  satisfaction_iff : ∀ c x,
    M.satisfies c x ↔ N.satisfies (claimMap c) (worldMap x)
  evidenceMap : ∀ c, M.Evidence c → N.Evidence (claimMap c)

namespace GroundedHom

def id (M : GroundedModel.{u,v,w}) : GroundedHom M M where
  worldMap := fun x => x
  claimMap := fun c => c
  reference_commutes := by intro c; rfl
  satisfaction_iff := by intro c x; rfl
  evidenceMap := fun _ e => e

def comp {M N K : GroundedModel.{u,v,w}}
    (f : GroundedHom M N) (g : GroundedHom N K) : GroundedHom M K where
  worldMap := g.worldMap ∘ f.worldMap
  claimMap := g.claimMap ∘ f.claimMap
  reference_commutes := by
    intro c
    change g.worldMap (f.worldMap (M.reference c)) =
      K.reference (g.claimMap (f.claimMap c))
    rw [f.reference_commutes, g.reference_commutes]
  satisfaction_iff := by
    intro c x
    exact (f.satisfaction_iff c x).trans
      (g.satisfaction_iff (f.claimMap c) (f.worldMap x))
  evidenceMap := by
    intro c e
    exact g.evidenceMap (f.claimMap c) (f.evidenceMap c e)

end GroundedHom

/-- The ordinary category underlying grounded semantic models. -/
def groundedCategory : SemCategory.{max (u + 1) (max (v + 1) (w + 1)), max u (max v w)} where
  Obj := GroundedModel.{u,v,w}
  Hom := GroundedHom
  id := GroundedHom.id
  comp := GroundedHom.comp
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

/-- Every morphism in this category transports grounded truth. -/
theorem grounded_truth_preserved {M N : GroundedModel.{u,v,w}}
    (f : GroundedHom M N) (c : M.Claim) :
    GroundedTrue M c ↔ GroundedTrue N (f.claimMap c) := by
  unfold GroundedTrue
  have h := f.satisfaction_iff c (M.reference c)
  simpa [f.reference_commutes] using h

/-- Evidence is transported, and remains sound in the target model. -/
theorem transported_evidence_sound {M N : GroundedModel.{u,v,w}}
    (f : GroundedHom M N) (c : M.Claim) (e : M.Evidence c) :
    N.satisfies (f.claimMap c) (N.reference (f.claimMap c)) := by
  have htruth := grounded_truth_preserved f c
  exact htruth.mp (M.evidence_sound c e)

/-- The all-probes profile is fully faithful on grounded models. This is
    mathematically automatic once the category and its morphisms are fixed;
    it is not a proof that the chosen category is the uniquely correct
    ontology of semantics. -/
def grounded_all_probe_reconstruction (M N : groundedCategory.Obj) :
    Cerp.HigherSemanticCore.HomBijection (groundedCategory.Hom M N)
      (ProfileNat groundedCategory M N) :=
  homEquiv groundedCategory M N

/-- Restricted probes reconstruct grounded semantic maps whenever the
    incidence cocone of those probes is dense in the grounded category. -/
def grounded_restricted_reconstruction
    (P : ProbeFamily groundedCategory)
    (D : ProbeDensity groundedCategory P)
    (M N : groundedCategory.Obj) :
    Cerp.HigherSemanticCore.HomBijection (groundedCategory.Hom M N)
      (RestrictedProfileNat groundedCategory P M N) :=
  restrictedProfileHomEquiv groundedCategory P D M N

/-- Identical underlying carriers and reference data can still encode
different truth conditions; no truth-preserving semantic morphism can
identify these two models. -/
theorem truth_conditions_block_semantic_map :
    Nonempty (GroundedHom trueModel falseModel) → False := by
  intro h
  rcases h with ⟨f⟩
  have htruth := f.satisfaction_iff () ()
  exact htruth.mp True.intro

/-- Evidence soundness does not imply evidence completeness: a true claim
may have no evidence object at all. -/
theorem soundness_does_not_imply_completeness :
    GroundedTrue trueWithoutEvidence () ∧
      ¬ Nonempty (trueWithoutEvidence.Evidence ()) := by
  exact true_without_evidence_countermodel

end Cerp.GroundedSemanticCategory
