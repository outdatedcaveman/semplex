import SemanticFibrations
import SemanticYoneda

/-!
# Category of relationally grounded semiosis models

This category uses the richer existing semantic fibration schema:
reference is a relation (not assumed functional), signs express claims
relative to contexts, satisfaction is distinct from aboutness, and
evidence is indexed by sign/context/world.
-/

namespace Cerp.GroundedSemiosisCategory

open Cerp.SemanticFibrations
open Cerp.SemanticYoneda.GeneralCategory

universe u v w x

structure GroundedSemiosisHom
    (M N : GroundedSemiosis.{u,v,w,x}) where
  worldMap : M.World -> N.World
  signMap : M.Sign -> N.Sign
  claimMap : M.Claim -> N.Claim
  contextMap : M.Context -> N.Context
  refers_iff : forall s world,
    M.refers s world <->
      N.refers (signMap s) (worldMap world)
  expresses_commutes : forall s context,
    claimMap (M.expresses s context) =
      N.expresses (signMap s) (contextMap context)
  satisfies_iff : forall claim world,
    M.satisfies claim world <->
      N.satisfies (claimMap claim) (worldMap world)
  evidenceMap : forall s context world,
    M.Evidence s context world ->
      N.Evidence (signMap s) (contextMap context) (worldMap world)

namespace GroundedSemiosisHom

def id (M : GroundedSemiosis.{u,v,w,x}) : GroundedSemiosisHom M M where
  worldMap := fun w => w
  signMap := fun s => s
  claimMap := fun c => c
  contextMap := fun c => c
  refers_iff := by intro s w; rfl
  expresses_commutes := by intro s c; rfl
  satisfies_iff := by intro c w; rfl
  evidenceMap := fun _ _ _ ev => ev

def comp {M N K : GroundedSemiosis.{u,v,w,x}}
    (f : GroundedSemiosisHom M N)
    (g : GroundedSemiosisHom N K) : GroundedSemiosisHom M K where
  worldMap := g.worldMap ∘ f.worldMap
  signMap := g.signMap ∘ f.signMap
  claimMap := g.claimMap ∘ f.claimMap
  contextMap := g.contextMap ∘ f.contextMap
  refers_iff := by
    intro s w
    exact (f.refers_iff s w).trans
      (g.refers_iff (f.signMap s) (f.worldMap w))
  expresses_commutes := by
    intro s c
    change g.claimMap (f.claimMap (M.expresses s c)) =
      K.expresses (g.signMap (f.signMap s))
        (g.contextMap (f.contextMap c))
    rw [f.expresses_commutes, g.expresses_commutes]
  satisfies_iff := by
    intro c w
    exact (f.satisfies_iff c w).trans
      (g.satisfies_iff (f.claimMap c) (f.worldMap w))
  evidenceMap := by
    intro s c w ev
    exact g.evidenceMap (f.signMap s) (f.contextMap c)
      (f.worldMap w) (f.evidenceMap s c w ev)

end GroundedSemiosisHom

/-- The category of relationally grounded semiosis models. -/
def groundedSemiosisCategory :
    SemCategory.{max (u + 1) (max (v + 1) (max (w + 1) (x + 1))),
      max u (max v (max w x))} where
  Obj := GroundedSemiosis.{u,v,w,x}
  Hom := GroundedSemiosisHom
  id := GroundedSemiosisHom.id
  comp := GroundedSemiosisHom.comp
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

/-- Content truth is preserved and reflected independently of reference. -/
theorem content_truth_iff {M N : GroundedSemiosis.{u,v,w,x}}
    (f : GroundedSemiosisHom M N) (s : M.Sign)
    (c : M.Context) (world : M.World) :
    ContentTrue M s c world <->
      ContentTrue N (f.signMap s) (f.contextMap c) (f.worldMap world) := by
  unfold ContentTrue
  have hs := f.satisfies_iff (M.expresses s c) world
  simpa [f.expresses_commutes] using hs

/-- Aboutness/reference is preserved and reflected separately. -/
theorem reference_iff {M N : GroundedSemiosis.{u,v,w,x}}
    (f : GroundedSemiosisHom M N) (s : M.Sign) (world : M.World) :
    M.refers s world <->
      N.refers (f.signMap s) (f.worldMap world) :=
  f.refers_iff s world

/-- Grounded assertion truth (aboutness AND content satisfaction) is
    invariant under every morphism of this category. -/
theorem assertion_truth_iff {M N : GroundedSemiosis.{u,v,w,x}}
    (f : GroundedSemiosisHom M N) (s : M.Sign)
    (c : M.Context) (world : M.World) :
    GroundedAssertionTrue M s c world <->
      GroundedAssertionTrue N (f.signMap s)
        (f.contextMap c) (f.worldMap world) := by
  unfold GroundedAssertionTrue
  constructor
  · intro h
    exact ⟨f.refers_iff s world |>.mp h.1,
      (content_truth_iff f s c world).mp h.2⟩
  · intro h
    exact ⟨f.refers_iff s world |>.mpr h.1,
      (content_truth_iff f s c world).mpr h.2⟩

/-- Evidence maps preserve soundness, without assuming completeness. -/
theorem evidence_transport_sound {M N : GroundedSemiosis.{u,v,w,x}}
    (f : GroundedSemiosisHom M N) (s : M.Sign)
    (c : M.Context) (world : M.World)
    (href : M.refers s world) (ev : M.Evidence s c world) :
    N.satisfies (N.expresses (f.signMap s) (f.contextMap c))
      (f.worldMap world) := by
  have hsound := M.evidence_sound s c world href ev
  have htarget := f.satisfies_iff (M.expresses s c) world
  simpa [f.expresses_commutes] using htarget.mp hsound

/-- All-probe reconstruction for the richer relational/contextual/evidential
    category. -/
def all_probe_reconstruction (M N : groundedSemiosisCategory.Obj) :
    Cerp.HigherSemanticCore.HomBijection
      (groundedSemiosisCategory.Hom M N)
      (ProfileNat groundedSemiosisCategory M N) :=
  homEquiv groundedSemiosisCategory M N

end Cerp.GroundedSemiosisCategory
