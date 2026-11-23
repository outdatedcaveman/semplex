import SemanticYoneda
import SemanticModuliFiber

namespace Cerp.RestrictedSemanticProfileGroupoid

open Cerp.HigherSemanticCore
open Cerp.SemanticYoneda.GeneralCategory

universe u v

def asSemCategory (G : Groupoid) : SemCategory where
  Obj := G.Obj
  Hom := G.Hom
  id := G.id
  comp := G.comp
  id_comp := G.id_comp
  comp_id := G.comp_id
  assoc := G.assoc

def restrictedIdentity (G : Groupoid) (P : ProbeFamily (asSemCategory G))
    (x : G.Obj) :
    RestrictedProfileNat (asSemCategory G) P x x :=
  restrictedRepresent (asSemCategory G) P (G.id x)

def restrictedCompose (G : Groupoid)
    (P : ProbeFamily (asSemCategory G))
    {x y z : G.Obj}
    (eta : RestrictedProfileNat (asSemCategory G) P x y)
    (theta : RestrictedProfileNat (asSemCategory G) P y z) :
    RestrictedProfileNat (asSemCategory G) P x z where
  app := fun p hp f => theta.app p hp (eta.app p hp f)
  natural := by
    intro p q hp hq u f
    calc
      theta.app p hp (eta.app p hp (G.comp u f)) =
          theta.app p hp (G.comp u (eta.app q hq f)) := by
            have hn := eta.natural hp hq u f
            simpa [asSemCategory] using congrArg (theta.app p hp) hn
      _ = G.comp u (theta.app q hq (eta.app q hq f)) := by
            have hn := theta.natural hp hq u (eta.app q hq f)
            simpa [asSemCategory] using hn

def restrictedInverse (G : Groupoid)
    (P : ProbeFamily (asSemCategory G))
    (D : ProbeDensity (asSemCategory G) P)
    {x y : G.Obj}
    (eta : RestrictedProfileNat (asSemCategory G) P x y) :
    RestrictedProfileNat (asSemCategory G) P y x :=
  restrictedRepresent (asSemCategory G) P (G.inv (D.lift eta))

def restrictedProfileGroupoid (G : Groupoid)
    (P : ProbeFamily (asSemCategory G))
    (D : ProbeDensity (asSemCategory G) P) : Groupoid where
  Obj := G.Obj
  Hom := fun x y => RestrictedProfileNat (asSemCategory G) P x y
  id := restrictedIdentity G P
  comp := restrictedCompose G P
  inv := restrictedInverse G P D
  id_comp := by
    intro a b eta
    apply RestrictedProfileNat.ext
    funext p hp f
    change eta.app p hp (G.comp f (G.id a)) = eta.app p hp f
    rw [G.comp_id]
  comp_id := by
    intro a b eta
    apply RestrictedProfileNat.ext
    funext p hp f
    change G.comp (eta.app p hp f) (G.id b) = eta.app p hp f
    rw [G.comp_id]
  assoc := by
    intro a b c d eta theta kappa
    apply RestrictedProfileNat.ext
    funext p hp f
    rfl
  inv_left := by
    intro a b eta
    apply RestrictedProfileNat.ext
    funext p hp f
    let g := D.lift eta
    have hEta :
        restrictedRepresent (asSemCategory G) P g = eta :=
      (restrictedProfileHomEquiv (asSemCategory G) P D a b).right_inv eta
    have hvalue :
        eta.app p hp (G.comp f (G.inv g)) =
          G.comp (G.comp f (G.inv g)) g := by
      have h := congrArg
        (fun tau : RestrictedProfileNat (asSemCategory G) P a b =>
          tau.app p hp (G.comp f (G.inv g))) hEta
      exact h.symm
    change eta.app p hp (G.comp f (G.inv g)) =
      G.comp f (G.id b)
    calc
      eta.app p hp (G.comp f (G.inv g)) =
          G.comp (G.comp f (G.inv g)) g := hvalue
      _ = G.comp f (G.comp (G.inv g) g) := G.assoc _ _ _
      _ = G.comp f (G.id b) := by rw [G.inv_left]
  inv_right := by
    intro a b eta
    apply RestrictedProfileNat.ext
    funext p hp f
    let g := D.lift eta
    have hEta :
        restrictedRepresent (asSemCategory G) P g = eta :=
      (restrictedProfileHomEquiv (asSemCategory G) P D a b).right_inv eta
    have hvalue : eta.app p hp f = G.comp f g := by
      have h := congrArg
        (fun tau : RestrictedProfileNat (asSemCategory G) P a b =>
          tau.app p hp f) hEta
      exact h.symm
    change G.comp (eta.app p hp f) (G.inv g) =
      G.comp f (G.id a)
    calc
      G.comp (eta.app p hp f) (G.inv g) =
          G.comp (G.comp f g) (G.inv g) := by rw [hvalue]
      _ = G.comp f (G.comp g (G.inv g)) := G.assoc _ _ _
      _ = G.comp f (G.id a) := by rw [G.inv_right]

def restrictedProfileYonedaFunctor (G : Groupoid)
    (P : ProbeFamily (asSemCategory G))
    (D : ProbeDensity (asSemCategory G) P) :
    GroupoidFunctor G (restrictedProfileGroupoid G P D) where
  obj := fun x => x
  map := fun f => restrictedRepresent (asSemCategory G) P f
  map_id := by
    intro x
    rfl
  map_comp := by
    intro x y z f g
    apply RestrictedProfileNat.ext
    funext p hp alpha
    change G.comp alpha (G.comp f g) =
      G.comp (G.comp alpha f) g
    exact (G.assoc alpha f g).symm

def restrictedProfileEquivalence (G : Groupoid)
    (P : ProbeFamily (asSemCategory G))
    (D : ProbeDensity (asSemCategory G) P) :
    GroupoidEquivalence G (restrictedProfileGroupoid G P D) where
  functor := restrictedProfileYonedaFunctor G P D
  homEquiv := fun x y => restrictedProfileHomEquiv (asSemCategory G) P D x y
  homEquiv_map := by intro x y f; rfl
  essentiallySurjective := by
    intro y
    exact ⟨y, ⟨restrictedIdentity G P y⟩⟩

/-- Dense restricted probes give a contractible moduli fiber over every
    observed response profile, including all retained isotropy. -/
theorem restricted_profile_moduli_contractible (G : Groupoid)
    (P : ProbeFamily (asSemCategory G))
    (D : ProbeDensity (asSemCategory G) P) (x : G.Obj) :
    Cerp.SemanticModuliFiber.FiberContractible
      (restrictedProfileEquivalence G P D) x :=
  Cerp.SemanticModuliFiber.equivalence_has_contractible_fibers
    (restrictedProfileEquivalence G P D) x

end Cerp.RestrictedSemanticProfileGroupoid
