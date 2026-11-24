import GroundedRelativeDensity
import SemanticModuliFiber

/-!
# Grounded moduli fibers

A fully faithful external realization, together with relative density of
operational probes on its image, induces an equivalence from the external
groupoid to its operational response-profile groupoid. Therefore every
homotopy fiber over an in-image profile is contractible.

This is the strict 1-groupoid moduli theorem. It is not yet the
(∞,1)-categorical mapping-space theorem.
-/

namespace Cerp.GroundedModuliFiber

open Cerp.HigherSemanticCore
open Cerp.SemanticYoneda.GeneralCategory
open Cerp.GroundedRelativeDensity
open Cerp.SemanticModuliFiber

universe u v

def asSemCategory (G : Groupoid) : SemCategory where
  Obj := G.Obj
  Hom := G.Hom
  id := G.id
  comp := G.comp
  id_comp := G.id_comp
  comp_id := G.comp_id
  assoc := G.assoc

def profileRepresent
    (E : Groupoid) (C : SemCategory)
    (R : SemFunctor (asSemCategory E) C) (P : ProbeFamily C)
    {x y : E.Obj} (f : E.Hom x y) :
    RestrictedProfileNat C P (R.obj x) (R.obj y) :=
  restrictedRepresent C P (R.map f)

def profileRecover
    (E : Groupoid) (C : SemCategory)
    (R : SemFunctor (asSemCategory E) C) (P : ProbeFamily C)
    (FF : FullyFaithfulRealization (asSemCategory E) C R)
    (D : RelativeProbeDensity (asSemCategory E) C R P)
    {x y : E.Obj}
    (eta : RestrictedProfileNat C P (R.obj x) (R.obj y)) :
    E.Hom x y :=
  (FF.homEquiv x y).invFun (D.lift eta)

theorem profileRecover_represent
    (E : Groupoid) (C : SemCategory)
    (R : SemFunctor (asSemCategory E) C) (P : ProbeFamily C)
    (FF : FullyFaithfulRealization (asSemCategory E) C R)
    (D : RelativeProbeDensity (asSemCategory E) C R P)
    {x y : E.Obj} (f : E.Hom x y) :
    profileRecover E C R P FF D (profileRepresent E C R P f) = f :=
  (groundedProfileHomEquiv (asSemCategory E) C R P FF D x y).left_inv f

theorem profileRepresent_recover
    (E : Groupoid) (C : SemCategory)
    (R : SemFunctor (asSemCategory E) C) (P : ProbeFamily C)
    (FF : FullyFaithfulRealization (asSemCategory E) C R)
    (D : RelativeProbeDensity (asSemCategory E) C R P)
    {x y : E.Obj}
    (eta : RestrictedProfileNat C P (R.obj x) (R.obj y)) :
    profileRepresent E C R P
      (profileRecover E C R P FF D eta) = eta :=
  (groundedProfileHomEquiv (asSemCategory E) C R P FF D x y).right_inv eta

def profileIdentity
    (E : Groupoid) (C : SemCategory)
    (R : SemFunctor (asSemCategory E) C) (P : ProbeFamily C)
    (x : E.Obj) :
    RestrictedProfileNat C P (R.obj x) (R.obj x) :=
  profileRepresent E C R P (E.id x)

def profileCompose
    (E : Groupoid) (C : SemCategory)
    (R : SemFunctor (asSemCategory E) C) (P : ProbeFamily C)
    (FF : FullyFaithfulRealization (asSemCategory E) C R)
    (D : RelativeProbeDensity (asSemCategory E) C R P)
    {x y z : E.Obj}
    (eta : RestrictedProfileNat C P (R.obj x) (R.obj y))
    (theta : RestrictedProfileNat C P (R.obj y) (R.obj z)) :
    RestrictedProfileNat C P (R.obj x) (R.obj z) :=
  profileRepresent E C R P
    (E.comp (profileRecover E C R P FF D eta)
      (profileRecover E C R P FF D theta))

def profileInverse
    (E : Groupoid) (C : SemCategory)
    (R : SemFunctor (asSemCategory E) C) (P : ProbeFamily C)
    (FF : FullyFaithfulRealization (asSemCategory E) C R)
    (D : RelativeProbeDensity (asSemCategory E) C R P)
    {x y : E.Obj}
    (eta : RestrictedProfileNat C P (R.obj x) (R.obj y)) :
    RestrictedProfileNat C P (R.obj y) (R.obj x) :=
  profileRepresent E C R P
    (E.inv (profileRecover E C R P FF D eta))

theorem profileRecover_identity
    (E : Groupoid) (C : SemCategory)
    (R : SemFunctor (asSemCategory E) C) (P : ProbeFamily C)
    (FF : FullyFaithfulRealization (asSemCategory E) C R)
    (D : RelativeProbeDensity (asSemCategory E) C R P)
    (x : E.Obj) :
    profileRecover E C R P FF D (profileIdentity E C R P x) = E.id x := by
  unfold profileIdentity
  exact profileRecover_represent E C R P FF D (E.id x)

theorem profileRecover_compose
    (E : Groupoid) (C : SemCategory)
    (R : SemFunctor (asSemCategory E) C) (P : ProbeFamily C)
    (FF : FullyFaithfulRealization (asSemCategory E) C R)
    (D : RelativeProbeDensity (asSemCategory E) C R P)
    {x y z : E.Obj}
    (eta : RestrictedProfileNat C P (R.obj x) (R.obj y))
    (theta : RestrictedProfileNat C P (R.obj y) (R.obj z)) :
    profileRecover E C R P FF D (profileCompose E C R P FF D eta theta) =
      E.comp (profileRecover E C R P FF D eta)
        (profileRecover E C R P FF D theta) := by
  unfold profileCompose
  exact profileRecover_represent E C R P FF D _

theorem profileRecover_inverse
    (E : Groupoid) (C : SemCategory)
    (R : SemFunctor (asSemCategory E) C) (P : ProbeFamily C)
    (FF : FullyFaithfulRealization (asSemCategory E) C R)
    (D : RelativeProbeDensity (asSemCategory E) C R P)
    {x y : E.Obj}
    (eta : RestrictedProfileNat C P (R.obj x) (R.obj y)) :
    profileRecover E C R P FF D (profileInverse E C R P FF D eta) =
      E.inv (profileRecover E C R P FF D eta) := by
  unfold profileInverse
  exact profileRecover_represent E C R P FF D _

def groundedProfileGroupoid
    (E : Groupoid) (C : SemCategory)
    (R : SemFunctor (asSemCategory E) C) (P : ProbeFamily C)
    (FF : FullyFaithfulRealization (asSemCategory E) C R)
    (D : RelativeProbeDensity (asSemCategory E) C R P) : Groupoid where
  Obj := E.Obj
  Hom := fun x y => RestrictedProfileNat C P (R.obj x) (R.obj y)
  id := profileIdentity E C R P
  comp := profileCompose E C R P FF D
  inv := profileInverse E C R P FF D
  id_comp := by
    intro x y eta
    calc
      profileCompose E C R P FF D (profileIdentity E C R P x) eta =
          profileRepresent E C R P
            (E.comp (profileRecover E C R P FF D
              (profileIdentity E C R P x))
              (profileRecover E C R P FF D eta)) := rfl
      _ = profileRepresent E C R P
            (E.comp (E.id x) (profileRecover E C R P FF D eta)) := by
              rw [profileRecover_identity E C R P FF D x]
      _ = profileRepresent E C R P (profileRecover E C R P FF D eta) := by
              rw [E.id_comp]
      _ = eta := profileRepresent_recover E C R P FF D eta
  comp_id := by
    intro x y eta
    calc
      profileCompose E C R P FF D eta (profileIdentity E C R P y) =
          profileRepresent E C R P
            (E.comp (profileRecover E C R P FF D eta)
              (profileRecover E C R P FF D
                (profileIdentity E C R P y))) := rfl
      _ = profileRepresent E C R P
            (E.comp (profileRecover E C R P FF D eta) (E.id y)) := by
              rw [profileRecover_identity E C R P FF D y]
      _ = profileRepresent E C R P (profileRecover E C R P FF D eta) := by
              rw [E.comp_id]
      _ = eta := profileRepresent_recover E C R P FF D eta
  assoc := by
    intro w x y z eta theta kappa
    calc
      profileCompose E C R P FF D
          (profileCompose E C R P FF D eta theta) kappa =
        profileRepresent E C R P
          (E.comp
            (profileRecover E C R P FF D
              (profileCompose E C R P FF D eta theta))
            (profileRecover E C R P FF D kappa)) := rfl
      _ = profileRepresent E C R P
          (E.comp
            (E.comp (profileRecover E C R P FF D eta)
              (profileRecover E C R P FF D theta))
            (profileRecover E C R P FF D kappa)) := by
              rw [profileRecover_compose E C R P FF D eta theta]
      _ = profileRepresent E C R P
          (E.comp (profileRecover E C R P FF D eta)
            (E.comp (profileRecover E C R P FF D theta)
              (profileRecover E C R P FF D kappa))) := by
              rw [E.assoc]
      _ = profileCompose E C R P FF D eta
          (profileCompose E C R P FF D theta kappa) := by
            change
              profileRepresent E C R P
                (E.comp (profileRecover E C R P FF D eta)
                  (E.comp (profileRecover E C R P FF D theta)
                    (profileRecover E C R P FF D kappa))) =
              profileRepresent E C R P
                (E.comp (profileRecover E C R P FF D eta)
                  (profileRecover E C R P FF D
                    (profileCompose E C R P FF D theta kappa)))
            exact congrArg
              (fun f => profileRepresent E C R P
                (E.comp (profileRecover E C R P FF D eta) f))
              (profileRecover_compose E C R P FF D theta kappa).symm
  inv_left := by
    intro x y eta
    calc
      profileCompose E C R P FF D
          (profileInverse E C R P FF D eta) eta =
        profileRepresent E C R P
          (E.comp
            (profileRecover E C R P FF D
              (profileInverse E C R P FF D eta))
            (profileRecover E C R P FF D eta)) := rfl
      _ = profileRepresent E C R P
          (E.comp (E.inv (profileRecover E C R P FF D eta))
            (profileRecover E C R P FF D eta)) := by
              rw [profileRecover_inverse E C R P FF D eta]
      _ = profileRepresent E C R P (E.id y) := by rw [E.inv_left]
      _ = profileIdentity E C R P y := rfl
  inv_right := by
    intro x y eta
    calc
      profileCompose E C R P FF D eta
          (profileInverse E C R P FF D eta) =
        profileRepresent E C R P
          (E.comp
            (profileRecover E C R P FF D eta)
            (profileRecover E C R P FF D
              (profileInverse E C R P FF D eta))) := rfl
      _ = profileRepresent E C R P
          (E.comp (profileRecover E C R P FF D eta)
            (E.inv (profileRecover E C R P FF D eta))) := by
              rw [profileRecover_inverse E C R P FF D eta]
      _ = profileRepresent E C R P (E.id x) := by rw [E.inv_right]
      _ = profileIdentity E C R P x := rfl

def groundedProfileFunctor
    (E : Groupoid) (C : SemCategory)
    (R : SemFunctor (asSemCategory E) C) (P : ProbeFamily C)
    (FF : FullyFaithfulRealization (asSemCategory E) C R)
    (D : RelativeProbeDensity (asSemCategory E) C R P) :
    GroupoidFunctor E (groundedProfileGroupoid E C R P FF D) where
  obj := fun x => x
  map := fun {x y} f => profileRepresent E C R P f
  map_id := by intro x; rfl
  map_comp := by
    intro x y z f g
    change profileRepresent E C R P (E.comp f g) =
      profileCompose E C R P FF D
        (profileRepresent E C R P f) (profileRepresent E C R P g)
    unfold profileCompose
    rw [profileRecover_represent, profileRecover_represent]

def groundedProfileEquivalence
    (E : Groupoid) (C : SemCategory)
    (R : SemFunctor (asSemCategory E) C) (P : ProbeFamily C)
    (FF : FullyFaithfulRealization (asSemCategory E) C R)
    (D : RelativeProbeDensity (asSemCategory E) C R P) :
    GroupoidEquivalence E (groundedProfileGroupoid E C R P FF D) where
  functor := groundedProfileFunctor E C R P FF D
  homEquiv := fun x y =>
    { toFun := profileRepresent E C R P
      invFun := profileRecover E C R P FF D
      left_inv := profileRecover_represent E C R P FF D
      right_inv := profileRepresent_recover E C R P FF D }
  homEquiv_map := by intro x y f; rfl
  essentiallySurjective := by
    intro y
    refine ⟨y, ?_⟩
    exact ⟨profileIdentity E C R P y⟩

theorem grounded_moduli_fiber_contractible
    (E : Groupoid) (C : SemCategory)
    (R : SemFunctor (asSemCategory E) C) (P : ProbeFamily C)
    (FF : FullyFaithfulRealization (asSemCategory E) C R)
    (D : RelativeProbeDensity (asSemCategory E) C R P)
    (x : E.Obj) :
    FiberContractible (groundedProfileEquivalence E C R P FF D) x :=
  equivalence_has_contractible_fibers
    (groundedProfileEquivalence E C R P FF D) x

end Cerp.GroundedModuliFiber


namespace Cerp.GroundedModuliFiber

open Cerp.HigherSemanticCore
open Cerp.SemanticYoneda.GeneralCategory
open Cerp.GroundedRelativeDensity

def profilePointwiseCompose
    (E : Groupoid) (C : SemCategory)
    (R : SemFunctor (asSemCategory E) C) (P : ProbeFamily C)
    {x y z : E.Obj}
    (eta : RestrictedProfileNat C P (R.obj x) (R.obj y))
    (theta : RestrictedProfileNat C P (R.obj y) (R.obj z)) :
    RestrictedProfileNat C P (R.obj x) (R.obj z) where
  app := fun p hp f => theta.app p hp (eta.app p hp f)
  natural := by
    intro p q hp hq u f
    calc
      theta.app p hp (eta.app p hp (C.comp u f)) =
          theta.app p hp (C.comp u (eta.app q hq f)) := by
            have h := eta.natural hp hq u f
            exact congrArg (theta.app p hp) h
      _ = C.comp u (theta.app q hq (eta.app q hq f)) :=
            theta.natural hp hq u (eta.app q hq f)

theorem profileCompose_is_pointwise
    (E : Groupoid) (C : SemCategory)
    (R : SemFunctor (asSemCategory E) C) (P : ProbeFamily C)
    (FF : FullyFaithfulRealization (asSemCategory E) C R)
    (D : RelativeProbeDensity (asSemCategory E) C R P)
    {x y z : E.Obj}
    (eta : RestrictedProfileNat C P (R.obj x) (R.obj y))
    (theta : RestrictedProfileNat C P (R.obj y) (R.obj z)) :
    profileCompose E C R P FF D eta theta =
      profilePointwiseCompose E C R P eta theta := by
  apply RestrictedProfileNat.ext
  funext p hp alpha
  change C.comp alpha
      (R.map (E.comp (profileRecover E C R P FF D eta)
        (profileRecover E C R P FF D theta))) =
    theta.app p hp (eta.app p hp alpha)
  have hEta :
      C.comp alpha (R.map (profileRecover E C R P FF D eta)) =
        eta.app p hp alpha :=
    congrArg (fun tau => tau.app p hp alpha)
      (profileRepresent_recover E C R P FF D eta)
  have hTheta :
      C.comp (eta.app p hp alpha)
        (R.map (profileRecover E C R P FF D theta)) =
          theta.app p hp (eta.app p hp alpha) :=
    congrArg (fun tau => tau.app p hp (eta.app p hp alpha))
      (profileRepresent_recover E C R P FF D theta)
  calc
    C.comp alpha
        (R.map (E.comp (profileRecover E C R P FF D eta)
          (profileRecover E C R P FF D theta))) =
      C.comp alpha
        (C.comp (R.map (profileRecover E C R P FF D eta))
          (R.map (profileRecover E C R P FF D theta))) :=
      congrArg (C.comp alpha)
        (R.map_comp (profileRecover E C R P FF D eta)
          (profileRecover E C R P FF D theta))
    _ = C.comp
        (C.comp alpha (R.map (profileRecover E C R P FF D eta)))
        (R.map (profileRecover E C R P FF D theta)) :=
          (C.assoc alpha _ _).symm
    _ = C.comp (eta.app p hp alpha)
        (R.map (profileRecover E C R P FF D theta)) := by rw [hEta]
    _ = theta.app p hp (eta.app p hp alpha) := hTheta

end Cerp.GroundedModuliFiber
