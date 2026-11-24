import HoTTGaugeBridge

namespace Cerp.HigherSemanticCore

universe u v w x

/-- A small groupoid: objects, arrows, composition, and inverses. -/
structure Groupoid where
  Obj : Type u
  Hom : Obj -> Obj -> Type v
  id : (a : Obj) -> Hom a a
  comp : {a b c : Obj} -> Hom a b -> Hom b c -> Hom a c
  inv : {a b : Obj} -> Hom a b -> Hom b a
  id_comp : forall {a b : Obj} (f : Hom a b), comp (id a) f = f
  comp_id : forall {a b : Obj} (f : Hom a b), comp f (id b) = f
  assoc : forall {a b c d : Obj} (f : Hom a b) (g : Hom b c) (h : Hom c d),
    comp (comp f g) h = comp f (comp g h)
  inv_left : forall {a b : Obj} (f : Hom a b), comp (inv f) f = id b
  inv_right : forall {a b : Obj} (f : Hom a b), comp f (inv f) = id a

structure HomBijection (A : Type u) (B : Type v) where
  toFun : A -> B
  invFun : B -> A
  left_inv : forall a, invFun (toFun a) = a
  right_inv : forall b, toFun (invFun b) = b

/-- Fully faithful and essentially surjective functor between groupoids. -/
structure GroupoidFunctor (G : Groupoid) (H : Groupoid) where
  obj : G.Obj -> H.Obj
  map : forall {a b : G.Obj}, G.Hom a b -> H.Hom (obj a) (obj b)
  map_id : forall a, map (G.id a) = H.id (obj a)
  map_comp : forall {a b c : G.Obj} (f : G.Hom a b) (g : G.Hom b c),
    map (G.comp f g) = H.comp (map f) (map g)

/-- A groupoid equivalence preserves all hom-types, including loop spaces. -/
structure GroupoidEquivalence (G : Groupoid) (H : Groupoid) where
  functor : GroupoidFunctor G H
  homEquiv : forall a b, HomBijection (G.Hom a b)
    (H.Hom (functor.obj a) (functor.obj b))
  homEquiv_map : forall {a b} (f : G.Hom a b),
    (homEquiv a b).toFun f = functor.map f
  essentiallySurjective : forall y : H.Obj,
    exists x : G.Obj, Nonempty (H.Hom (functor.obj x) y)

def automorphismBijection (G : Groupoid) (H : Groupoid)
    (E : GroupoidEquivalence G H) (a : G.Obj) :
    HomBijection (G.Hom a a) (H.Hom (E.functor.obj a) (E.functor.obj a)) :=
  E.homEquiv a a

/-- Each probe/context returns a groupoid of admissible responses. -/
structure HigherProbeSemantics (S : Type u) (P : Type v) where
  responseGroupoid : P -> Groupoid
  response : forall p, S -> (responseGroupoid p).Obj

/-- States are equivalent when every probe's responses are isomorphic. -/
def higherSemEq {S : Type u} {P : Type v}
    (M : HigherProbeSemantics S P) (s t : S) : Prop :=
  forall p, Nonempty ((M.responseGroupoid p).Hom (M.response p s) (M.response p t))

theorem higherSemEq_refl {S : Type u} {P : Type v}
    (M : HigherProbeSemantics S P) : forall s, higherSemEq M s s := by
  intro s p
  exact ⟨(M.responseGroupoid p).id (M.response p s)⟩

theorem higherSemEq_symm {S : Type u} {P : Type v}
    (M : HigherProbeSemantics S P) {s t : S} :
    higherSemEq M s t -> higherSemEq M t s := by
  intro h p
  obtain ⟨f⟩ := h p
  exact ⟨(M.responseGroupoid p).inv f⟩

theorem higherSemEq_trans {S : Type u} {P : Type v}
    (M : HigherProbeSemantics S P) {s t r : S} :
    higherSemEq M s t -> higherSemEq M t r -> higherSemEq M s r := by
  intro hst htr p
  obtain ⟨f⟩ := hst p
  obtain ⟨g⟩ := htr p
  exact ⟨(M.responseGroupoid p).comp f g⟩

/-- Boolean xor is the group operation of the two-element automorphism group. -/
def bxor : Bool -> Bool -> Bool
  | false, b => b
  | true, false => true
  | true, true => false

@[simp] theorem bxor_false_left (b : Bool) : bxor false b = b := by cases b <;> rfl
@[simp] theorem bxor_false_right (a : Bool) : bxor a false = a := by cases a <;> rfl
@[simp] theorem bxor_self (a : Bool) : bxor a a = false := by cases a <;> rfl
theorem bxor_assoc (a b c : Bool) :
    bxor (bxor a b) c = bxor a (bxor b c) := by
  cases a <;> cases b <;> cases c <;> rfl

def twoAutomorphismGroupoid : Groupoid where
  Obj := Unit
  Hom := fun _ _ => Bool
  id := fun _ => false
  comp := fun f g => bxor f g
  inv := fun f => f
  id_comp := by intro a b f; cases f <;> rfl
  comp_id := by intro a b f; cases f <;> rfl
  assoc := by intro _ _ _ _ f g h; exact bxor_assoc f g h
  inv_left := by intro _ _ f; simp [bxor_self]
  inv_right := by intro _ _ f; simp [bxor_self]

def trivialAutomorphismGroupoid : Groupoid where
  Obj := Unit
  Hom := fun _ _ => Unit
  id := fun _ => ()
  comp := fun _ _ => ()
  inv := fun _ => ()
  id_comp := by intro a b f; cases f; rfl
  comp_id := by intro a b f; cases f; rfl
  assoc := by intro _ _ _ _ f g h; cases f; cases g; cases h; rfl
  inv_left := by intro _ _ f; cases f; rfl
  inv_right := by intro _ _ f; cases f; rfl

theorem no_bool_bijection_unit (e : HomBijection Bool Unit) : False := by
  have hinj : forall a b, e.toFun a = e.toFun b -> a = b := by
    intro a b hab
    calc
      a = e.invFun (e.toFun a) := (e.left_inv a).symm
      _ = e.invFun (e.toFun b) := congrArg e.invFun hab
      _ = b := e.left_inv b
  have hEq := Subsingleton.elim (e.toFun false) (e.toFun true)
  have hFalseTrue : false = true := hinj false true hEq
  exact Bool.noConfusion hFalseTrue

/-- Same object type does not imply groupoid equivalence: automorphisms matter. -/
theorem same_object_shadow_not_groupoid_equiv :
    Nonempty (GroupoidEquivalence twoAutomorphismGroupoid
      trivialAutomorphismGroupoid) -> False := by
  intro h
  rcases h with ⟨E⟩
  exact no_bool_bijection_unit (E.homEquiv () ())

/-- A groupoid equivalence transports an isomorphism witness forward. -/
theorem groupoidEquivalence_map_iso (G H : Groupoid)
    (E : GroupoidEquivalence G H) {a b : G.Obj}
    (h : Nonempty (G.Hom a b)) :
    Nonempty (H.Hom (E.functor.obj a) (E.functor.obj b)) := by
  obtain ⟨f⟩ := h
  exact ⟨(E.homEquiv a b).toFun f⟩

/-- Full faithfulness also reflects isomorphism witnesses. -/
theorem groupoidEquivalence_reflect_iso (G H : Groupoid)
    (E : GroupoidEquivalence G H) {a b : G.Obj}
    (h : Nonempty (H.Hom (E.functor.obj a) (E.functor.obj b))) :
    Nonempty (G.Hom a b) := by
  obtain ⟨f⟩ := h
  exact ⟨(E.homEquiv a b).invFun f⟩

theorem higherSemEq_equivalence {S : Type u} {P : Type v}
    (M : HigherProbeSemantics S P) : Equivalence (higherSemEq M) := by
  constructor
  · exact higherSemEq_refl M
  · intro s t h
    exact higherSemEq_symm M h
  · intro s t r hst htr
    exact higherSemEq_trans M hst htr


/-- A preorder of admissible contexts. The order c <= d means that c is
    at least as informative/refined as d, so responses may be restricted
    contravariantly from d to c. -/
structure ContextPreorder where
  Ctx : Type u
  le : Ctx -> Ctx -> Prop
  refl : forall c, le c c
  trans : forall {c d e}, le c d -> le d e -> le c e

/-- A strict groupoid-valued presheaf over a context preorder.

All contexts share a universe of response objects and arrows. Restriction
maps are endofunctors on that universe; context tags/validity can be encoded
in the objects themselves. The two coherence laws are stated explicitly.
-/
structure GroupoidPresheaf (C : ContextPreorder) where
  G : Groupoid
  restrictObj : forall {c d : C.Ctx}, C.le c d -> G.Obj -> G.Obj
  restrictHom : forall {c d : C.Ctx} (h : C.le c d) {x y : G.Obj},
    G.Hom x y -> G.Hom (restrictObj h x) (restrictObj h y)
  restrict_id_obj : forall c x, restrictObj (C.refl c) x = x
  restrict_id_hom : forall c {x y} (f : G.Hom x y),
    HEq (restrictHom (C.refl c) f) f
  restrict_comp_obj : forall {c d e} (hcd : C.le c d) (hde : C.le d e) x,
    restrictObj (C.trans hcd hde) x =
      restrictObj hcd (restrictObj hde x)
  restrict_comp_hom : forall {c d e} (hcd : C.le c d) (hde : C.le d e)
      {x y} (f : G.Hom x y),
    HEq (restrictHom (C.trans hcd hde) f)
      (restrictHom hcd (restrictHom hde f))

/-- A natural equivalence of groupoid-valued contextual semantics. It is
    objectwise fully faithful/essentially surjective and commutes with every
    admissible context restriction, including on arrows. -/
structure ContextualEquivalence {C : ContextPreorder}
    (M N : GroupoidPresheaf C) where
  equivalence : GroupoidEquivalence M.G N.G
  natural_obj : forall {c d : C.Ctx} (h : C.le c d) (x : M.G.Obj),
    equivalence.functor.obj (M.restrictObj h x) =
      N.restrictObj h (equivalence.functor.obj x)
  natural_hom : forall {c d : C.Ctx} (h : C.le c d) {x y : M.G.Obj}
      (f : M.G.Hom x y),
    HEq (equivalence.functor.map (M.restrictHom h f))
      (N.restrictHom h (equivalence.functor.map f))

/-- Contextual equivalence preserves the complete automorphism type of
    every response object. -/
def ContextualEquivalence.automorphisms
    {C : ContextPreorder} {M N : GroupoidPresheaf C}
    (E : ContextualEquivalence M N) (x : M.G.Obj) :
    HomBijection (M.G.Hom x x)
      (N.G.Hom (E.equivalence.functor.obj x) (E.equivalence.functor.obj x)) :=
  E.equivalence.homEquiv x x

open Cerp.HoTTGaugeBridge


/-- A left action of a group on a type. -/
structure GroupAction (G : Type u) (X : Type v) [GroupLike G] where
  act : G -> X -> X
  one_act : forall x, act GroupLike.one x = x
  mul_act : forall g h x, act (GroupLike.mul g h) x = act g (act h x)

/-- The action groupoid X // G: arrows are group elements carrying one
    object to another. This retains isotropy instead of only taking orbits. -/
def actionGroupoid (G : Type u) (X : Type v) [GroupLike G]
    (A : GroupAction G X) : Groupoid where
  Obj := X
  Hom := fun x y => {g : G // A.act g x = y}
  id := fun x => ⟨GroupLike.one, A.one_act x⟩
  comp := fun f h => ⟨GroupLike.mul h.1 f.1, by
    calc
      A.act (GroupLike.mul h.1 f.1) _ = A.act h.1 (A.act f.1 _) := A.mul_act h.1 f.1 _
      _ = A.act h.1 _ := by rw [f.2]
      _ = _ := h.2⟩
  inv := fun f => ⟨GroupLike.inv f.1, by
    calc
      A.act (GroupLike.inv f.1) _ = A.act (GroupLike.mul (GroupLike.inv f.1) f.1) _ := by
        rw [A.mul_act, f.2]
      _ = A.act GroupLike.one _ := by rw [GroupLike.inv_mul_cancel]
      _ = _ := A.one_act _⟩
  id_comp := by
    intro a b f
    apply Subtype.ext
    exact GroupLike.mul_one f.1
  comp_id := by
    intro a b f
    apply Subtype.ext
    exact GroupLike.one_mul f.1
  assoc := by
    intro a b c d f g h
    apply Subtype.ext
    exact (GroupLike.mul_assoc h.1 g.1 f.1).symm
  inv_left := by
    intro a b f
    apply Subtype.ext
    exact GroupLike.mul_inv_cancel f.1
  inv_right := by
    intro a b f
    apply Subtype.ext
    exact GroupLike.inv_mul_cancel f.1

abbrev HomotopyQuotient (G : Type u) (X : Type v) [GroupLike G]
    (A : GroupAction G X) := actionGroupoid G X A

def OrbitRelated {G : Type u} {X : Type v} [GroupLike G]
    (A : GroupAction G X) (x y : X) : Prop :=
  Exists (fun g : G => A.act g x = y)

theorem orbit_iff_action_groupoid_arrow {G : Type u} {X : Type v} [GroupLike G]
    (A : GroupAction G X) (x y : X) :
    OrbitRelated A x y <-> Nonempty ((actionGroupoid G X A).Hom x y) := by
  constructor
  · intro h
    rcases h with ⟨g, hg⟩
    exact ⟨⟨g, hg⟩⟩
  · intro h
    rcases h with ⟨g, hg⟩
    exact ⟨g, hg⟩

/-- The loop space at x in the action groupoid is exactly the stabilizer. -/
def Stabilizer {G : Type u} {X : Type v} [GroupLike G]
    (A : GroupAction G X) (x : X) :=
  {g : G // A.act g x = x}

theorem actionGroupoid_loops_are_stabilizer {G : Type u} {X : Type v} [GroupLike G]
    (A : GroupAction G X) (x : X) :
    (actionGroupoid G X A).Hom x x = Stabilizer A x := rfl

open Cerp.HoTTGaugeBridge

/-- The ordinary orbit relation is the connected-component relation of
    the action groupoid. -/
def orbitSetoid {G : Type u} {X : Type v} [GroupLike G]
    (A : GroupAction G X) : Setoid X where
  r := OrbitRelated A
  iseqv := {
    refl := by
      intro x
      exact ⟨GroupLike.one, A.one_act x⟩
    symm := by
      intro x y h
      rcases h with ⟨g, hg⟩
      exact ⟨GroupLike.inv g, by
        calc
          A.act (GroupLike.inv g) y = A.act (GroupLike.inv g) (A.act g x) := by rw [hg]
          _ = A.act (GroupLike.mul (GroupLike.inv g) g) x := by rw [A.mul_act]
          _ = A.act GroupLike.one x := by rw [GroupLike.inv_mul_cancel]
          _ = x := A.one_act x⟩
    trans := by
      intro x y z hxy hyz
      rcases hxy with ⟨g, hg⟩
      rcases hyz with ⟨h, hh⟩
      exact ⟨GroupLike.mul h g, by
        calc
          A.act (GroupLike.mul h g) x = A.act h (A.act g x) := A.mul_act h g x
          _ = A.act h y := by rw [hg]
          _ = z := hh⟩
  }

/-- The set of orbits is the 0-truncation/connected-components quotient of
    the action groupoid; the groupoid itself retains stabilizer loops. -/
theorem orbit_quotient_eq_iff_action_arrow {G : Type u} {X : Type v}
    [GroupLike G] (A : GroupAction G X) (x y : X) :
    Quotient.mk (orbitSetoid A) x = Quotient.mk (orbitSetoid A) y <->
      Nonempty ((actionGroupoid G X A).Hom x y) := by
  constructor
  · intro h
    exact (orbit_iff_action_groupoid_arrow A x y).mp (Quotient.exact h)
  · intro h
    apply Quotient.sound
    exact (orbit_iff_action_groupoid_arrow A x y).mpr h

end Cerp.HigherSemanticCore
