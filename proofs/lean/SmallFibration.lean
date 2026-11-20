/-!
Spike 17 — a small split fibration as a Grothendieck construction.

The base is the two-object preorder coarse ≤ fine. The fiber over coarse
remembers one Boolean coordinate; the fiber over fine remembers an ordered pair
of Boolean coordinates. Reindexing from fine to coarse forgets the second coordinate. The total category is the
category of elements of this contravariant set-valued functor. Since the fibers
are discrete categories, cartesian arrows have a direct factorization proof.

This is a genuine (small, split) fibration, not merely a family of observational
equivalence relations. It is a toy construction; no claim is made that it
already captures Synesism's full module ontology.
-/

namespace SmallFibration

inductive Context where
  | coarse
  | fine
  deriving DecidableEq

def Hom : Context → Context → Prop
  | .coarse, .coarse => True
  | .coarse, .fine => True
  | .fine, .fine => True
  | .fine, .coarse => False

def idHom (c : Context) : Hom c c := by
  cases c <;> trivial

def compHom {a b c : Context} (_ : Hom a b) (_ : Hom b c) : Hom a c := by
  cases a <;> cases b <;> cases c <;> simp_all [Hom]



/-- The base preorder, viewed as a thin category, satisfies the category laws. -/
theorem hom_id_comp {a b : Context} (f : Hom a b) :
    compHom (idHom a) f = f :=
  Subsingleton.elim _ _

theorem hom_comp_id {a b : Context} (f : Hom a b) :
    compHom f (idHom b) = f :=
  Subsingleton.elim _ _

theorem hom_assoc {a b c d : Context}
    (f : Hom a b) (g : Hom b c) (h : Hom c d) :
    compHom (compHom f g) h = compHom f (compHom g h) :=
  Subsingleton.elim _ _

def Fiber : Context → Type
  | .coarse => Bool
  | .fine => Bool × Bool

/-- Pull a refined two-coordinate profile back to the coarse first-coordinate profile. -/
def reindex : {a b : Context} → Hom a b → Fiber b → Fiber a
  | .coarse, .coarse, _, x => x
  | .coarse, .fine, _, x => x.1
  | .fine, .fine, _, x => x
  | .fine, .coarse, h, _ => False.elim h

theorem reindex_id (c : Context) :
    reindex (idHom c) = (fun x => x) := by
  cases c <;> rfl

theorem reindex_comp {a b c : Context} (f : Hom a b) (g : Hom b c) :
    reindex (compHom f g) = (reindex f) ∘ (reindex g) := by
  funext x
  cases a <;> cases b <;> cases c <;> cases f <;> cases g <;> rfl

/-- Objects in the Grothendieck total category. -/
abbrev TotalObject := Sigma Fiber

/-- A total arrow consists of a base arrow and a compatible fiber element. -/
structure TotalArrow (x y : TotalObject) where
  base : Hom x.1 y.1
  fiber : reindex base y.2 = x.2

def totalId (x : TotalObject) : TotalArrow x x where
  base := idHom x.1
  fiber := by
    change reindex (idHom x.1) x.2 = x.2
    rw [reindex_id]

def totalComp {x y z : TotalObject}
    (f : TotalArrow x y) (g : TotalArrow y z) : TotalArrow x z where
  base := compHom f.base g.base
  fiber := by
    calc
      reindex (compHom f.base g.base) z.2 =
          reindex f.base (reindex g.base z.2) := by
            exact congrFun (reindex_comp f.base g.base) z.2
      _ = reindex f.base y.2 := by rw [g.fiber]
      _ = x.2 := f.fiber

/-- In this thin total category, parallel arrows are propositionally equal. -/
theorem totalArrow_ext {x y : TotalObject} (f g : TotalArrow x y) : f = g := by
  cases f with
  | mk fb fp =>
    cases g with
    | mk gb gp =>
      have hb : fb = gb := Subsingleton.elim _ _
      cases hb
      have hp : fp = gp := Subsingleton.elim _ _
      cases hp
      rfl

theorem total_id_comp {x y : TotalObject} (f : TotalArrow x y) :
    totalComp (totalId x) f = f :=
  totalArrow_ext _ _

theorem total_comp_id {x y : TotalObject} (f : TotalArrow x y) :
    totalComp f (totalId y) = f :=
  totalArrow_ext _ _

theorem total_assoc {w x y z : TotalObject}
    (f : TotalArrow w x) (g : TotalArrow x y) (h : TotalArrow y z) :
    totalComp (totalComp f g) h = totalComp f (totalComp g h) :=
  totalArrow_ext _ _

/-- The chosen cartesian lift of f over an object y in its codomain fiber. -/
def cartLift {a b : Context} (f : Hom a b) (y : Fiber b) :
    TotalArrow ⟨a, reindex f y⟩ ⟨b, y⟩ where
  base := f
  fiber := rfl

/--
Cartesian factorization: every arrow into the codomain of a chosen lift factors
uniquely through that lift. The base is a preorder and fibers are discrete.
-/
theorem cartesian_factorization {a b c : Context}
    (f : Hom a b) (g : Hom c a) (y : Fiber b) (z : Fiber c)
    (u : TotalArrow ⟨c, z⟩ ⟨b, y⟩) :
    ∃ k : TotalArrow ⟨c, z⟩ ⟨a, reindex f y⟩,
      (k.base = g ∧ totalComp k (cartLift f y) = u) ∧
      ∀ k' : TotalArrow ⟨c, z⟩ ⟨a, reindex f y⟩,
        (k'.base = g ∧ totalComp k' (cartLift f y) = u) → k' = k := by
  let k : TotalArrow ⟨c, z⟩ ⟨a, reindex f y⟩ :=
    { base := g
      fiber := by
        calc
          reindex g (reindex f y) =
              reindex (compHom g f) y := (congrFun (reindex_comp g f) y).symm
          _ = reindex u.base y := by
                have hb : compHom g f = u.base := Subsingleton.elim _ _
                rw [hb]
          _ = z := u.fiber }
  refine ⟨k, ?_, ?_⟩
  · exact ⟨rfl, totalArrow_ext _ _⟩
  · intro k' _
    exact totalArrow_ext k' k

/-- The chosen cartesian lift over an identity arrow is the total identity. -/
theorem cartLift_id (c : Context) (y : Fiber c) :
    HEq (cartLift (idHom c) y) (totalId ⟨c, y⟩) := by
  cases c <;> rfl

/-- Chosen cartesian lifts compose coherently after reindexing equality. -/
theorem cartLift_comp {a b c : Context}
    (f : Hom a b) (g : Hom b c) (y : Fiber c) :
    HEq (totalComp (cartLift f (reindex g y)) (cartLift g y))
      (cartLift (compHom f g) y) := by
  cases a <;> cases b <;> cases c <;> cases f <;> cases g <;> rfl

end SmallFibration
