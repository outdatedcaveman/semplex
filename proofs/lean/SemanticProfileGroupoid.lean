import SemanticYoneda
import SemanticModuliFiber

namespace Cerp.SemanticProfileGroupoid

open Cerp.HigherSemanticCore
open Cerp.SemanticYoneda

universe u v

def profileIdentity (G : Groupoid) (x : G.Obj) : ProfileNat G x x where
  app := fun _ f => f
  natural := by intro p q u f; rfl

def profileCompose (G : Groupoid) {x y z : G.Obj}
    (eta : ProfileNat G x y) (theta : ProfileNat G y z) :
    ProfileNat G x z where
  app := fun p f => theta.app p (eta.app p f)
  natural := by
    intro p q u f
    calc
      theta.app q (eta.app q (G.comp u f)) =
          theta.app q (G.comp u (eta.app p f)) := by
            rw [eta.natural u f]
      _ = G.comp u (theta.app p (eta.app p f)) :=
            theta.natural u (eta.app p f)

def profileInverse (G : Groupoid) {x y : G.Obj}
    (eta : ProfileNat G x y) : ProfileNat G y x :=
  represent G (G.inv (recover G eta))

theorem profileCompose_id_left (G : Groupoid) {x y : G.Obj}
    (eta : ProfileNat G x y) :
    profileCompose G (profileIdentity G x) eta = eta := by
  apply ProfileNat.ext
  funext p f
  rfl

theorem profileCompose_id_right (G : Groupoid) {x y : G.Obj}
    (eta : ProfileNat G x y) :
    profileCompose G eta (profileIdentity G y) = eta := by
  apply ProfileNat.ext
  funext p f
  rfl

theorem profileCompose_represent (G : Groupoid) {x y z : G.Obj}
    (g : G.Hom x y) (h : G.Hom y z) :
    profileCompose G (represent G g) (represent G h) =
      represent G (G.comp g h) := by
  apply ProfileNat.ext
  funext p f
  change G.comp (G.comp f g) h = G.comp f (G.comp g h)
  exact G.assoc f g h

theorem profileInverse_comp_left (G : Groupoid) {x y : G.Obj}
    (eta : ProfileNat G x y) :
    profileCompose G (profileInverse G eta) eta =
      profileIdentity G y := by
  apply ProfileNat.ext
  funext p f
  let g := recover G eta
  have heta := represent_recover G eta
  have hvalue :
      eta.app p (G.comp f (G.inv g)) =
        G.comp (G.comp f (G.inv g)) g := by
    have h := congrArg (fun tau : ProfileNat G x y =>
      tau.app p (G.comp f (G.inv g))) heta
    exact h.symm
  change eta.app p (G.comp f (G.inv g)) = f
  calc
    eta.app p (G.comp f (G.inv g)) =
        G.comp (G.comp f (G.inv g)) g := hvalue
    _ = G.comp f (G.comp (G.inv g) g) := G.assoc _ _ _
    _ = G.comp f (G.id y) := by rw [G.inv_left]
    _ = f := G.comp_id f

theorem profileInverse_comp_right (G : Groupoid) {x y : G.Obj}
    (eta : ProfileNat G x y) :
    profileCompose G eta (profileInverse G eta) =
      profileIdentity G x := by
  apply ProfileNat.ext
  funext p f
  let g := recover G eta
  have heta := represent_recover G eta
  have hvalue :
      eta.app p f = G.comp f g := by
    have h := congrArg (fun tau : ProfileNat G x y => tau.app p f) heta
    exact h.symm
  change G.comp (eta.app p f) (G.inv g) = f
  calc
    G.comp (eta.app p f) (G.inv g) =
        G.comp (G.comp f g) (G.inv g) := by rw [hvalue]
    _ = G.comp f (G.comp g (G.inv g)) := G.assoc _ _ _
    _ = G.comp f (G.id x) := by rw [G.inv_right]
    _ = f := G.comp_id f

/-- The groupoid of all-probe profiles. Objects are represented objects;
    arrows are natural transformations between their complete response
    profiles. -/
def profileGroupoid (G : Groupoid) : Groupoid where
  Obj := G.Obj
  Hom := fun x y => ProfileNat G x y
  id := profileIdentity G
  comp := profileCompose G
  inv := profileInverse G
  id_comp := by intro a b eta; exact profileCompose_id_left G eta
  comp_id := by intro a b eta; exact profileCompose_id_right G eta
  assoc := by
    intro a b c d eta theta kappa
    apply ProfileNat.ext
    funext p f
    rfl
  inv_left := by
    intro a b eta
    exact profileInverse_comp_left G eta
  inv_right := by
    intro a b eta
    exact profileInverse_comp_right G eta

/-- The Yoneda representation functor into the groupoid of response profiles. -/
def profileYonedaFunctor (G : Groupoid) :
    GroupoidFunctor G (profileGroupoid G) where
  obj := fun x => x
  map := fun f => represent G f
  map_id := by
    intro x
    apply ProfileNat.ext
    funext p f
    change G.comp f (G.id x) = f
    exact G.comp_id f
  map_comp := by
    intro x y z f g
    exact (profileCompose_represent G f g).symm

/-- The all-probes groupoid-valued Yoneda representation is an equivalence. -/
def profileYonedaEquivalence (G : Groupoid) :
    GroupoidEquivalence G (profileGroupoid G) where
  functor := profileYonedaFunctor G
  homEquiv := fun x y => homEquiv G x y
  homEquiv_map := by intro x y f; rfl
  essentiallySurjective := by
    intro y
    exact ⟨y, ⟨profileIdentity G y⟩⟩

/-- Consequently, the moduli groupoid of systems equipped with an
    equivalence to a fixed complete all-probe profile is contractible. -/
theorem all_probe_profile_moduli_contractible (G : Groupoid) (x : G.Obj) :
    Cerp.SemanticModuliFiber.FiberContractible
      (profileYonedaEquivalence G) x :=
  Cerp.SemanticModuliFiber.equivalence_has_contractible_fibers
    (profileYonedaEquivalence G) x

end Cerp.SemanticProfileGroupoid
