import HigherSemanticCore

namespace Cerp.ConnectedIsotropy

open Cerp.HigherSemanticCore

universe u v

/-- In any groupoid, inversion is involutive (derivable from the inverse laws). -/
theorem inverse_involutive (G : Groupoid) {a b : G.Obj}
    (f : G.Hom a b) : G.inv (G.inv f) = f := by
  calc
    G.inv (G.inv f) =
        G.comp (G.inv (G.inv f)) (G.id b) := (G.comp_id _).symm
    _ = G.comp (G.inv (G.inv f)) (G.comp (G.inv f) f) := by
          rw [G.inv_left]
    _ = G.comp (G.comp (G.inv (G.inv f)) (G.inv f)) f :=
          (G.assoc _ _ _).symm
    _ = G.comp (G.id a) f := by rw [G.inv_left]
    _ = f := G.id_comp _

/-- An arrow between objects transports their automorphisms by conjugation. -/
def automorphismTransport (G : Groupoid) {a b : G.Obj}
    (f : G.Hom a b) :
    HomBijection (G.Hom a a) (G.Hom b b) where
  toFun := fun h => G.comp (G.comp (G.inv f) h) f
  invFun := fun k => G.comp (G.comp f k) (G.inv f)
  left_inv := by
    intro h
    calc
      G.comp (G.comp f (G.comp (G.comp (G.inv f) h) f)) (G.inv f) =
          G.comp f (G.comp (G.comp (G.comp (G.inv f) h) f) (G.inv f)) :=
        G.assoc _ _ _
      _ = G.comp f (G.comp (G.comp (G.inv f) h) (G.comp f (G.inv f))) :=
        by rw [G.assoc]
      _ = G.comp f (G.comp (G.comp (G.inv f) h) (G.id a)) := by
        rw [G.inv_right]
      _ = G.comp f (G.comp (G.inv f) h) := by
        rw [G.comp_id (G.comp (G.inv f) h)]
      _ = G.comp (G.comp f (G.inv f)) h := (G.assoc _ _ _).symm
      _ = G.comp (G.id a) h := by rw [G.inv_right]
      _ = h := G.id_comp _
  right_inv := by
    intro k
    calc
      G.comp (G.comp (G.inv f) (G.comp (G.comp f k) (G.inv f))) f =
          G.comp (G.inv f) (G.comp (G.comp (G.comp f k) (G.inv f)) f) :=
        G.assoc _ _ _
      _ = G.comp (G.inv f) (G.comp (G.comp f k) (G.comp (G.inv f) f)) :=
        by rw [G.assoc]
      _ = G.comp (G.inv f) (G.comp (G.comp f k) (G.id b)) := by
        rw [G.inv_left]
      _ = G.comp (G.inv f) (G.comp f k) := by
        rw [G.comp_id (G.comp f k)]
      _ = G.comp (G.comp (G.inv f) f) k := (G.assoc _ _ _).symm
      _ = G.comp (G.id b) k := by rw [G.inv_left]
      _ = k := G.id_comp _

/-- Transport preserves the identity automorphism. -/
theorem automorphismTransport_map_id (G : Groupoid) {a b : G.Obj}
    (f : G.Hom a b) :
    (automorphismTransport G f).toFun (G.id a) = G.id b := by
  change G.comp (G.comp (G.inv f) (G.id a)) f = G.id b
  calc
    G.comp (G.comp (G.inv f) (G.id a)) f =
        G.comp (G.inv f) f := by rw [G.comp_id]
    _ = G.id b := G.inv_left f

/-- Isomorphic objects have equivalent isotropy/loop types. -/
theorem isomorphic_objects_have_bijective_isotropy
    (G : Groupoid) {a b : G.Obj}
    (f : G.Hom a b) :
    Nonempty (HomBijection (G.Hom a a) (G.Hom b b)) :=
  ⟨automorphismTransport G f⟩

/-- Transport along the inverse arrow is inverse to transport along f. -/
theorem inverse_transport_is_inverse
    (G : Groupoid) {a b : G.Obj} (f : G.Hom a b) :
    (automorphismTransport G f).invFun =
      (automorphismTransport G (G.inv f)).toFun := by
  funext h
  change G.comp (G.comp f h) (G.inv f) =
    G.comp (G.comp (G.inv (G.inv f)) h) (G.inv f)
  rw [inverse_involutive G f]

/-- Conjugation transport preserves composition of automorphisms. -/
theorem automorphismTransport_map_comp (G : Groupoid) {a b : G.Obj}
    (f : G.Hom a b) (h1 h2 : G.Hom a a) :
    (automorphismTransport G f).toFun (G.comp h1 h2) =
      G.comp ((automorphismTransport G f).toFun h1)
        ((automorphismTransport G f).toFun h2) := by
  change G.comp (G.comp (G.inv f) (G.comp h1 h2)) f =
    G.comp (G.comp (G.comp (G.inv f) h1) f)
      (G.comp (G.comp (G.inv f) h2) f)
  symm
  calc
    G.comp (G.comp (G.comp (G.inv f) h1) f)
        (G.comp (G.comp (G.inv f) h2) f) =
      G.comp (G.comp (G.comp (G.inv f) h1) f)
        (G.comp (G.inv f) (G.comp h2 f)) := by
          rw [G.assoc (G.inv f) h2 f]
    _ = G.comp (G.comp (G.comp (G.comp (G.inv f) h1) f) (G.inv f))
        (G.comp h2 f) := (G.assoc _ _ _).symm
    _ = G.comp (G.comp (G.comp (G.inv f) h1) (G.comp f (G.inv f)))
        (G.comp h2 f) := by
          rw [G.assoc (G.comp (G.inv f) h1) f (G.inv f)]
    _ = G.comp (G.comp (G.comp (G.inv f) h1) (G.id a))
        (G.comp h2 f) := by
          rw [G.inv_right f]
    _ = G.comp (G.comp (G.inv f) h1) (G.comp h2 f) := by
          rw [G.comp_id]
    _ = G.comp (G.inv f) (G.comp h1 (G.comp h2 f)) :=
          G.assoc (G.inv f) h1 (G.comp h2 f)
    _ = G.comp (G.inv f) (G.comp (G.comp h1 h2) f) := by
          rw [← G.assoc h1 h2 f]
    _ = G.comp (G.comp (G.inv f) (G.comp h1 h2)) f :=
          (G.assoc (G.inv f) (G.comp h1 h2) f).symm

end Cerp.ConnectedIsotropy
