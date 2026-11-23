import HigherSemanticCore

/-!
# Semantic Yoneda: reconstruction from all admissible probes

This is the strict 1-groupoid layer of the proposed Grounded Higher
Semantic Representation Theorem. A probe p observes an object x through
the arrows p ⟶ x. Natural transformations between these response profiles
are exactly arrows between the represented objects.

The result is a direct, constructive Yoneda proof. It does NOT yet establish
that a restricted physical/computational probe family is dense, nor does it
identify internal truth with truth about an external world.
-/

namespace Cerp.SemanticYoneda

open Cerp.HigherSemanticCore

universe u v

/-- The response profile of x: every object p probes x by arrows p ⟶ x. -/
def Profile (G : Groupoid) (x : G.Obj) (p : G.Obj) : Type v :=
  G.Hom p x

/-- Natural transformations between two representable response profiles. -/
@[ext]
structure ProfileNat (G : Groupoid) (x y : G.Obj) where
  app : forall p : G.Obj, Profile G x p -> Profile G y p
  natural : forall {p q : G.Obj} (u : G.Hom q p) (f : Profile G x p),
    app q (G.comp u f) = G.comp u (app p f)

/-- An arrow x ⟶ y acts on every probe response by postcomposition. -/
def represent (G : Groupoid) {x y : G.Obj} (g : G.Hom x y) :
    ProfileNat G x y where
  app := fun p f => G.comp f g
  natural := by
    intro p q u f
    exact G.assoc u f g


/-- The representation sends identity arrows to identity natural maps. -/
theorem represent_id (G : Groupoid) (x : G.Obj) :
    represent G (G.id x) =
      { app := fun _ f => f
        natural := by intro p q u f; rfl } := by
  apply ProfileNat.ext
  funext p f
  change G.comp f (G.id x) = f
  exact G.comp_id f

/-- The representation preserves composition. -/
theorem represent_comp (G : Groupoid) {x y z : G.Obj}
    (g : G.Hom x y) (h : G.Hom y z) :
    represent G (G.comp g h) =
      { app := fun p f => G.comp (G.comp f g) h
        natural := by
          intro p q u f
          change G.comp (G.comp (G.comp u f) g) h =
            G.comp u (G.comp (G.comp f g) h)
          calc
            G.comp (G.comp (G.comp u f) g) h =
                G.comp (G.comp u f) (G.comp g h) := G.assoc _ _ _
            _ = G.comp u (G.comp f (G.comp g h)) := G.assoc _ _ _
            _ = G.comp u (G.comp (G.comp f g) h) := by
                  rw [← G.assoc f g h] } := by
  apply ProfileNat.ext
  funext p f
  change G.comp f (G.comp g h) = G.comp (G.comp f g) h
  exact (G.assoc f g h).symm

/-- Recover an arrow by probing at x with its identity response. -/
def recover (G : Groupoid) {x y : G.Obj} (eta : ProfileNat G x y) :
    G.Hom x y :=
  eta.app x (G.id x)

/-- Yoneda's first inverse law: an arrow is recovered from its profile map. -/
theorem recover_represent (G : Groupoid) {x y : G.Obj}
    (g : G.Hom x y) :
    recover G (represent G g) = g := by
  change G.comp (G.id x) g = g
  exact G.id_comp g

/-- Yoneda's second inverse law: a natural response transformation is
    completely determined by its value on the identity probe. -/
theorem represent_recover (G : Groupoid) {x y : G.Obj}
    (eta : ProfileNat G x y) :
    represent G (recover G eta) = eta := by
  cases eta with
  | mk app natural =>
    apply ProfileNat.ext
    funext p f
    change G.comp f (app x (G.id x)) = app p f
    have h := natural (p := x) (q := p) f (G.id x)
    calc
      G.comp f (app x (G.id x)) =
          app p (G.comp f (G.id x)) := h.symm
      _ = app p f := by rw [G.comp_id]

/-- Full faithfulness of the all-probes response-profile representation. -/
def homEquiv (G : Groupoid) (x y : G.Obj) :
    HomBijection (G.Hom x y) (ProfileNat G x y) where
  toFun := represent G
  invFun := recover G
  left_inv := recover_represent G
  right_inv := represent_recover G

/-- Two objects are connected iff their complete all-probes profiles admit
    a natural transformation. In a groupoid this is equivalently a natural
    isomorphism, since every component arrow is invertible. -/
theorem profileConnected_iff_objectConnected (G : Groupoid)
    (x y : G.Obj) :
    Nonempty (ProfileNat G x y) <-> Nonempty (G.Hom x y) := by
  constructor
  · intro h
    rcases h with ⟨eta⟩
    exact ⟨recover G eta⟩
  · intro h
    rcases h with ⟨g⟩
    exact ⟨represent G g⟩

/-- The profile representation reflects and preserves all arrows, not merely
    connected components or object-level observations. -/
def profile_representation_fully_faithful (G : Groupoid) :
    forall x y : G.Obj,
      HomBijection (G.Hom x y) (ProfileNat G x y) :=
  homEquiv G


/-! ## General category version

The groupoid theorem above is a special case. This version allows
non-invertible morphisms, so it also models programs, compilers, state
transitions, and ordinary structure-preserving maps.
-/

namespace GeneralCategory

/-- A locally small category presented by its object and hom types. -/
structure SemCategory where
  Obj : Type u
  Hom : Obj -> Obj -> Type v
  id : forall a, Hom a a
  comp : forall {a b c : Obj}, Hom a b -> Hom b c -> Hom a c
  id_comp : forall {a b : Obj} (f : Hom a b), comp (id a) f = f
  comp_id : forall {a b : Obj} (f : Hom a b), comp f (id b) = f
  assoc : forall {a b c d : Obj} (f : Hom a b) (g : Hom b c)
    (h : Hom c d), comp (comp f g) h = comp f (comp g h)

/-- The contravariant all-probes profile represented by x. -/
def Profile (C : SemCategory) (x : C.Obj) (p : C.Obj) : Type v :=
  C.Hom p x

/-- Natural transformations between represented response profiles. -/
@[ext]
structure ProfileNat (C : SemCategory) (x y : C.Obj) where
  app : forall p : C.Obj, Profile C x p -> Profile C y p
  natural : forall {p q : C.Obj} (u : C.Hom q p) (f : Profile C x p),
    app q (C.comp u f) = C.comp u (app p f)

/-- An object morphism induces postcomposition on every probe response. -/
def represent (C : SemCategory) {x y : C.Obj} (g : C.Hom x y) :
    ProfileNat C x y where
  app := fun _ f => C.comp f g
  natural := by
    intro p q u f
    exact C.assoc u f g

/-- Recover the represented morphism by evaluating at the identity probe. -/
def recover (C : SemCategory) {x y : C.Obj} (eta : ProfileNat C x y) :
    C.Hom x y :=
  eta.app x (C.id x)

theorem recover_represent (C : SemCategory) {x y : C.Obj}
    (g : C.Hom x y) :
    recover C (represent C g) = g := by
  change C.comp (C.id x) g = g
  exact C.id_comp g

theorem represent_recover (C : SemCategory) {x y : C.Obj}
    (eta : ProfileNat C x y) :
    represent C (recover C eta) = eta := by
  cases eta with
  | mk app natural =>
    apply ProfileNat.ext
    funext p f
    change C.comp f (app x (C.id x)) = app p f
    have h := natural (p := x) (q := p) f (C.id x)
    calc
      C.comp f (app x (C.id x)) =
          app p (C.comp f (C.id x)) := h.symm
      _ = app p f := by rw [C.comp_id]

theorem represent_id (C : SemCategory) (x : C.Obj) :
    represent C (C.id x) =
      { app := fun _ f => f
        natural := by intro p q u f; rfl } := by
  apply ProfileNat.ext
  funext p f
  change C.comp f (C.id x) = f
  exact C.comp_id f

theorem represent_comp (C : SemCategory) {x y z : C.Obj}
    (g : C.Hom x y) (h : C.Hom y z) :
    represent C (C.comp g h) =
      { app := fun p f => C.comp (C.comp f g) h
        natural := by
          intro p q u f
          change C.comp (C.comp (C.comp u f) g) h =
            C.comp u (C.comp (C.comp f g) h)
          calc
            C.comp (C.comp (C.comp u f) g) h =
                C.comp (C.comp u f) (C.comp g h) := C.assoc _ _ _
            _ = C.comp u (C.comp f (C.comp g h)) := C.assoc _ _ _
            _ = C.comp u (C.comp (C.comp f g) h) := by
                  rw [← C.assoc f g h] } := by
  apply ProfileNat.ext
  funext p f
  change C.comp f (C.comp g h) = C.comp (C.comp f g) h
  exact (C.assoc f g h).symm

/-- The all-probes representation is fully faithful, including non-invertible
    morphisms. -/
def homEquiv (C : SemCategory) (x y : C.Obj) :
    HomBijection (C.Hom x y) (ProfileNat C x y) where
  toFun := represent C
  invFun := recover C
  left_inv := recover_represent C
  right_inv := represent_recover C

def profile_representation_fully_faithful (C : SemCategory) :
    forall x y : C.Obj,
      HomBijection (C.Hom x y) (ProfileNat C x y) :=
  homEquiv C

theorem profileConnected_iff_morphism (C : SemCategory)
    (x y : C.Obj) :
    Nonempty (ProfileNat C x y) <-> Nonempty (C.Hom x y) := by
  constructor
  · intro h
    rcases h with ⟨eta⟩
    exact ⟨recover C eta⟩
  · intro h
    rcases h with ⟨f⟩
    exact ⟨represent C f⟩


/-! ## Restricted probes and a non-circular density hypothesis

A selected probe family is not assumed to be complete. Density is the
universal property that the canonical incidence cocone of all probe maps
into x is a colimit. The following structure states that universal property
directly, without defining density as full faithfulness of the nerve.
-/

structure ProbeFamily (C : SemCategory) where
  isProbe : C.Obj -> Prop

@[ext]
structure RestrictedProfileNat (C : SemCategory) (P : ProbeFamily C)
    (x y : C.Obj) where
  app : forall p : C.Obj, P.isProbe p ->
    C.Hom p x -> C.Hom p y
  natural : forall {p q : C.Obj} (hp : P.isProbe p) (hq : P.isProbe q)
    (u : C.Hom p q) (f : C.Hom q x),
    app p hp (C.comp u f) = C.comp u (app q hq f)

/-- The canonical incidence diagram sends each probe arrow p ⟶ x to p.
    lift_spec and lift_unique are exactly the colimit cocone's universal
    property, expressed using its cone legs p ⟶ x. -/
structure ProbeDensity (C : SemCategory) (P : ProbeFamily C) where
  lift : forall {x y : C.Obj}, RestrictedProfileNat C P x y -> C.Hom x y
  lift_spec : forall {x y : C.Obj} (eta : RestrictedProfileNat C P x y)
    (p : C.Obj) (hp : P.isProbe p) (alpha : C.Hom p x),
    C.comp alpha (lift eta) = eta.app p hp alpha
  lift_unique : forall {x y : C.Obj}
    (eta : RestrictedProfileNat C P x y) (m : C.Hom x y),
    (forall (p : C.Obj) (hp : P.isProbe p) (alpha : C.Hom p x),
      C.comp alpha m = eta.app p hp alpha) ->
    m = lift eta

/-- A morphism induces a natural transformation on any chosen probe family. -/
def restrictedRepresent (C : SemCategory) (P : ProbeFamily C)
    {x y : C.Obj} (f : C.Hom x y) : RestrictedProfileNat C P x y where
  app := fun _ _ alpha => C.comp alpha f
  natural := by
    intro p q _ _ u alpha
    exact C.assoc u alpha f

/-- Density gives full faithfulness of the restricted probe-profile nerve. -/
def restrictedProfileHomEquiv (C : SemCategory) (P : ProbeFamily C)
    (D : ProbeDensity C P) (x y : C.Obj) :
    HomBijection (C.Hom x y) (RestrictedProfileNat C P x y) where
  toFun := restrictedRepresent C P
  invFun := D.lift
  left_inv := by
    intro f
    exact (D.lift_unique (restrictedRepresent C P f) f
      (by intro p _ alpha; rfl)).symm
  right_inv := by
    intro eta
    apply RestrictedProfileNat.ext
    funext p hp alpha
    exact D.lift_spec eta p hp alpha

/-- The family containing every object is dense: the identity probe is
    terminal in the category of elements of the represented profile. -/
def allProbes (C : SemCategory) : ProbeFamily C where
  isProbe := fun _ => True

def allProbesDense (C : SemCategory) : ProbeDensity C (allProbes C) where
  lift := fun {x y} eta => eta.app x trivial (C.id x)
  lift_spec := by
    intro x y eta p hp alpha
    have h := eta.natural hp trivial alpha (C.id x)
    calc
      C.comp alpha (eta.app x trivial (C.id x)) =
          eta.app p hp (C.comp alpha (C.id x)) := h.symm
      _ = eta.app p hp alpha := by rw [C.comp_id]
  lift_unique := by
    intro x y eta m h
    have hId := h x trivial (C.id x)
    calc
      m = C.comp (C.id x) m := (C.id_comp m).symm
      _ = eta.app x trivial (C.id x) := hId
      _ = eta.app x trivial (C.id x) := rfl

/-- The unrestricted Yoneda theorem is recovered as the all-probes instance
    of the restricted-density theorem. -/
def allProbesHomEquiv (C : SemCategory) (x y : C.Obj) :
    HomBijection (C.Hom x y)
      (RestrictedProfileNat C (allProbes C) x y) :=
  restrictedProfileHomEquiv C (allProbes C) (allProbesDense C) x y


/-! ## Countermodel: an empty probe family is not dense -/

def discreteBoolCategory : SemCategory where
  Obj := Bool
  Hom := fun a b => PLift (a = b)
  id := fun a => ⟨rfl⟩
  comp := fun f g => ⟨Eq.trans f.down g.down⟩
  id_comp := by intro a b f; cases f; rfl
  comp_id := by intro a b f; cases f; rfl
  assoc := by intro a b c d f g h; cases f; cases g; cases h; rfl

def emptyProbeFamily : ProbeFamily discreteBoolCategory where
  isProbe := fun _ => False

def emptyProbeProfileNat :
    RestrictedProfileNat discreteBoolCategory emptyProbeFamily false true where
  app := fun _ hp _ => False.elim hp
  natural := by
    intro p q hp hq u f
    exact False.elim hp

/-- With no admissible probes, distinct disconnected objects have identical
    (empty) profiles. This refutes any unconditional reconstruction claim. -/
theorem empty_probes_do_not_reflect_morphisms :
    Nonempty (RestrictedProfileNat discreteBoolCategory emptyProbeFamily false true) /\
      (Nonempty (discreteBoolCategory.Hom false true) -> False) := by
  constructor
  · exact ⟨emptyProbeProfileNat⟩
  · intro h
    rcases h with ⟨h⟩
    exact Bool.noConfusion h.down

end GeneralCategory

end Cerp.SemanticYoneda
