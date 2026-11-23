import HigherSemanticCore

/-!
# Grounded semantic structures and transfer

Reference, satisfaction, grounded truth, and evidence are separate fields.
An isomorphism preserving this structure transports truth and evidence.
No claim is made that an equivalence of unstructured carriers entails
truth about an external target.
-/

namespace Cerp.GroundedSemanticTransfer

open Cerp.HigherSemanticCore

universe u v w

structure GroundedModel where
  World : Type u
  Claim : Type v
  reference : Claim -> World
  satisfies : Claim -> World -> Prop
  Evidence : Claim -> Type w
  evidence_sound : forall c, Evidence c -> satisfies c (reference c)

def GroundedTrue (M : GroundedModel) (c : M.Claim) : Prop :=
  M.satisfies c (M.reference c)

/-- The maps are explicit bijections; semantic fields must commute with them. -/
structure GroundedIso (M N : GroundedModel) where
  worldEquiv : HomBijection M.World N.World
  claimEquiv : HomBijection M.Claim N.Claim
  reference_commutes : forall c,
    worldEquiv.toFun (M.reference c) =
      N.reference (claimEquiv.toFun c)
  satisfaction_iff : forall c w,
    M.satisfies c w <->
      N.satisfies (claimEquiv.toFun c) (worldEquiv.toFun w)
  evidenceEquiv : forall c,
    HomBijection (M.Evidence c) (N.Evidence (claimEquiv.toFun c))

theorem groundedTruth_iff (M N : GroundedModel) (E : GroundedIso M N)
    (c : M.Claim) :
    GroundedTrue M c <-> GroundedTrue N (E.claimEquiv.toFun c) := by
  constructor
  · intro h
    have h' := (E.satisfaction_iff c (M.reference c)).mp h
    simpa [GroundedTrue, E.reference_commutes] using h'
  · intro h
    have h' : N.satisfies (E.claimEquiv.toFun c)
        (E.worldEquiv.toFun (M.reference c)) := by
      simpa [E.reference_commutes] using h
    exact (E.satisfaction_iff c (M.reference c)).mpr h'

theorem evidence_exists_iff (M N : GroundedModel) (E : GroundedIso M N)
    (c : M.Claim) :
    Nonempty (M.Evidence c) <->
      Nonempty (N.Evidence (E.claimEquiv.toFun c)) := by
  constructor
  · intro h
    rcases h with ⟨e⟩
    exact ⟨(E.evidenceEquiv c).toFun e⟩
  · intro h
    rcases h with ⟨e⟩
    exact ⟨(E.evidenceEquiv c).invFun e⟩

/-- Evidence soundness transfers because truth is preserved by the grounded
    isomorphism. Completeness is not assumed. -/
theorem transported_evidence_is_sound (M N : GroundedModel)
    (E : GroundedIso M N) (c : M.Claim) (e : M.Evidence c) :
    GroundedTrue N (E.claimEquiv.toFun c) :=
  (groundedTruth_iff M N E c).mp (M.evidence_sound c e)

def trueWithoutEvidence : GroundedModel where
  World := Unit
  Claim := Unit
  reference := fun _ => ()
  satisfies := fun _ _ => True
  Evidence := fun _ => Empty
  evidence_sound := by intro c e; cases e

theorem true_without_evidence_countermodel :
    GroundedTrue trueWithoutEvidence () /\
      (Nonempty (trueWithoutEvidence.Evidence ()) -> False) := by
  constructor
  · trivial
  · intro h
    rcases h with ⟨e⟩
    cases e

def trueModel : GroundedModel where
  World := Unit
  Claim := Unit
  reference := fun _ => ()
  satisfies := fun _ _ => True
  Evidence := fun _ => Unit
  evidence_sound := by intro c e; trivial

def falseModel : GroundedModel where
  World := Unit
  Claim := Unit
  reference := fun _ => ()
  satisfies := fun _ _ => False
  Evidence := fun _ => Empty
  evidence_sound := by intro c e; cases e

/-- Identical bare carriers and reference do not determine the satisfaction
    relation or grounded truth. -/
theorem same_carriers_do_not_determine_truth :
    GroundedTrue trueModel () /\
      (GroundedTrue falseModel () -> False) := by
  constructor
  · trivial
  · intro h
    exact h

end Cerp.GroundedSemanticTransfer
