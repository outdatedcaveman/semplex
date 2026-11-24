import SemanticYoneda

/-!
# Grounded relative density

The external semantic category and the operational category are distinct.
A realization functor sends external systems into operational systems.
A probe family is required to be dense only on the realized image.

If realization is fully faithful and the probes satisfy the relative
colimit universal property on realized objects, then the composite
external-to-operational-to-profile representation is fully faithful.
This is the strict 1-categorical theorem layer.
-/

namespace Cerp.GroundedRelativeDensity

open Cerp.HigherSemanticCore
open Cerp.SemanticYoneda.GeneralCategory

universe u v

/-- A structure-preserving realization from external systems to operational
    systems. -/
structure SemFunctor (E C : SemCategory) where
  obj : E.Obj -> C.Obj
  map : forall {x y : E.Obj}, E.Hom x y -> C.Hom (obj x) (obj y)
  map_id : forall x, map (E.id x) = C.id (obj x)
  map_comp : forall {x y z : E.Obj} (f : E.Hom x y) (g : E.Hom y z),
    map (E.comp f g) = C.comp (map f) (map g)

/-- Full faithfulness of the realization functor, with its hom-equivalence
    explicitly identified with the functor's action on arrows. -/
structure FullyFaithfulRealization (E C : SemCategory) (R : SemFunctor E C) where
  homEquiv : forall x y : E.Obj,
    HomBijection (E.Hom x y) (C.Hom (R.obj x) (R.obj y))
  toFun_eq_map : forall {x y : E.Obj} (f : E.Hom x y),
    (homEquiv x y).toFun f = R.map f

/-- Relative density asks for the colimit-cocone universal property only
    between objects in the image of the external realization functor. -/
structure RelativeProbeDensity
    (E C : SemCategory) (R : SemFunctor E C) (P : ProbeFamily C) where
  lift : forall {x y : E.Obj},
    RestrictedProfileNat C P (R.obj x) (R.obj y) ->
      C.Hom (R.obj x) (R.obj y)
  lift_spec : forall {x y : E.Obj}
    (eta : RestrictedProfileNat C P (R.obj x) (R.obj y))
    (p : C.Obj) (hp : P.isProbe p) (alpha : C.Hom p (R.obj x)),
    C.comp alpha (lift eta) = eta.app p hp alpha
  lift_unique : forall {x y : E.Obj}
    (eta : RestrictedProfileNat C P (R.obj x) (R.obj y))
    (m : C.Hom (R.obj x) (R.obj y)),
    (forall (p : C.Obj) (hp : P.isProbe p)
      (alpha : C.Hom p (R.obj x)),
      C.comp alpha m = eta.app p hp alpha) ->
      m = lift eta

/-- **Grounded Relative-Density Theorem (strict 1-category).**
    Fully faithful realization followed by a relatively dense operational
    probe family yields a fully faithful external response-profile map. -/
def groundedProfileHomEquiv
    (E C : SemCategory) (R : SemFunctor E C) (P : ProbeFamily C)
    (FF : FullyFaithfulRealization E C R)
    (D : RelativeProbeDensity E C R P) (x y : E.Obj) :
    HomBijection (E.Hom x y)
      (RestrictedProfileNat C P (R.obj x) (R.obj y)) where
  toFun := fun f => restrictedRepresent C P (R.map f)
  invFun := fun eta => (FF.homEquiv x y).invFun (D.lift eta)
  left_inv := by
    intro f
    have hD :
        D.lift (restrictedRepresent C P (R.map f)) = R.map f :=
      (D.lift_unique (restrictedRepresent C P (R.map f)) (R.map f)
        (by intro p _hp alpha; rfl)).symm
    calc
      (FF.homEquiv x y).invFun
          (D.lift (restrictedRepresent C P (R.map f))) =
        (FF.homEquiv x y).invFun (R.map f) :=
          congrArg (FF.homEquiv x y).invFun hD
      _ = (FF.homEquiv x y).invFun ((FF.homEquiv x y).toFun f) :=
          congrArg (FF.homEquiv x y).invFun
            (FF.toFun_eq_map f).symm
      _ = f := (FF.homEquiv x y).left_inv f
  right_inv := by
    intro eta
    let g := D.lift eta
    have hmap :
        R.map ((FF.homEquiv x y).invFun g) = g :=
      (FF.toFun_eq_map ((FF.homEquiv x y).invFun g)).symm.trans
        ((FF.homEquiv x y).right_inv g)
    have hD : restrictedRepresent C P g = eta := by
      apply RestrictedProfileNat.ext
      funext p hp alpha
      exact D.lift_spec eta p hp alpha
    have hprofile :
        restrictedRepresent C P
          (R.map ((FF.homEquiv x y).invFun g)) = eta :=
      (congrArg (restrictedRepresent C P) hmap).trans hD
    apply RestrictedProfileNat.ext
    funext p hp alpha
    exact congrArg (fun tau => tau.app p hp alpha) hprofile

/-- The composite realization/profile representation is fully faithful on
    every external hom-set. -/
def grounded_profile_representation_fully_faithful
    (E C : SemCategory) (R : SemFunctor E C) (P : ProbeFamily C)
    (FF : FullyFaithfulRealization E C R)
    (D : RelativeProbeDensity E C R P) :
    forall x y : E.Obj,
      HomBijection (E.Hom x y)
        (RestrictedProfileNat C P (R.obj x) (R.obj y)) :=
  groundedProfileHomEquiv E C R P FF D

end Cerp.GroundedRelativeDensity


namespace Cerp.GroundedRelativeDensity

open Cerp.HigherSemanticCore
open Cerp.SemanticYoneda.GeneralCategory

/-- Full faithfulness of the external realization as seen through the
    restricted operational response profiles. -/
structure ProfileFaithfulRealization
    (E C : SemCategory) (R : SemFunctor E C) (P : ProbeFamily C) where
  homEquiv : forall x y : E.Obj,
    HomBijection (E.Hom x y)
      (RestrictedProfileNat C P (R.obj x) (R.obj y))
  toFun_eq_profile : forall {x y : E.Obj} (f : E.Hom x y),
    (homEquiv x y).toFun f = restrictedRepresent C P (R.map f)

/-- Under relative probe density, full faithfulness of the external
    realization implies full faithfulness of its operational profiles. -/
def profileFaithful_of_fullyFaithful
    (E C : SemCategory) (R : SemFunctor E C) (P : ProbeFamily C)
    (FF : FullyFaithfulRealization E C R)
    (D : RelativeProbeDensity E C R P) :
    ProfileFaithfulRealization E C R P where
  homEquiv := groundedProfileHomEquiv E C R P FF D
  toFun_eq_profile := by
    intro x y f
    rfl

/-- If the relative probe family is dense, profile-level full faithfulness
    reflects back to full faithfulness of the external realization functor. -/
def fullyFaithful_of_profileFaithful
    (E C : SemCategory) (R : SemFunctor E C) (P : ProbeFamily C)
    (PF : ProfileFaithfulRealization E C R P)
    (D : RelativeProbeDensity E C R P) :
    FullyFaithfulRealization E C R where
  homEquiv := fun x y =>
    { toFun := R.map
      invFun := fun g =>
        (PF.homEquiv x y).invFun (restrictedRepresent C P g)
      left_inv := by
        intro f
        calc
          (PF.homEquiv x y).invFun (restrictedRepresent C P (R.map f)) =
              (PF.homEquiv x y).invFun ((PF.homEquiv x y).toFun f) :=
            congrArg (PF.homEquiv x y).invFun
              (PF.toFun_eq_profile f).symm
          _ = f := (PF.homEquiv x y).left_inv f
      right_inv := by
        intro g
        have hprof :
            restrictedRepresent C P
              (R.map ((PF.homEquiv x y).invFun (restrictedRepresent C P g))) =
                restrictedRepresent C P g := by
          calc
            restrictedRepresent C P
                (R.map ((PF.homEquiv x y).invFun (restrictedRepresent C P g))) =
              (PF.homEquiv x y).toFun
                ((PF.homEquiv x y).invFun (restrictedRepresent C P g)) :=
                  (PF.toFun_eq_profile _).symm
            _ = restrictedRepresent C P g :=
              (PF.homEquiv x y).right_inv _
        have hleft :
            R.map ((PF.homEquiv x y).invFun (restrictedRepresent C P g)) =
              D.lift (restrictedRepresent C P
                (R.map ((PF.homEquiv x y).invFun (restrictedRepresent C P g)))) :=
          D.lift_unique _ _ (by intro p _hp alpha; rfl)
        have hright :
            g = D.lift (restrictedRepresent C P g) :=
          D.lift_unique _ _ (by intro p _hp alpha; rfl)
        calc
          R.map ((PF.homEquiv x y).invFun (restrictedRepresent C P g)) =
              D.lift (restrictedRepresent C P
                (R.map ((PF.homEquiv x y).invFun (restrictedRepresent C P g)))) :=
            hleft
          _ = D.lift (restrictedRepresent C P g) := congrArg D.lift hprof
          _ = g := hright.symm }
  toFun_eq_map := by intro x y f; rfl

/-- **Adequacy equivalence:** on the realized image, relative density means
    that operational profiles neither add nor erase morphism-level
    distinctions. Thus the profile representation is fully faithful iff
    the underlying external realization functor is fully faithful. -/
theorem realization_profile_adequacy_iff
    (E C : SemCategory) (R : SemFunctor E C) (P : ProbeFamily C)
    (D : RelativeProbeDensity E C R P) :
    Nonempty (FullyFaithfulRealization E C R) ↔
      Nonempty (ProfileFaithfulRealization E C R P) := by
  constructor
  · rintro ⟨FF⟩
    exact ⟨profileFaithful_of_fullyFaithful E C R P FF D⟩
  · rintro ⟨PF⟩
    exact ⟨fullyFaithful_of_profileFaithful E C R P PF D⟩

end Cerp.GroundedRelativeDensity
