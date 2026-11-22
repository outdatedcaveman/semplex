/-
  Semplex Master Principle — Grounded Higher Semantic Representation Theorem (GHSRT),
  Constructive Spanning Trees, Quantale Concept Lattices, Group-Algebra Frobenius Monoid Laws,
  and Homomorphic Unitary OOD Length Invariance.

  Isolated in `proofs/lean-mathlib/` (Mathlib v4.12.0) so `proofs/lean/` remains core Lean 4.
-/
import Mathlib.LinearAlgebra.UnitaryGroup
import Mathlib.LinearAlgebra.Matrix.Trace
import Mathlib.Data.Complex.Basic
import Mathlib.GroupTheory.Perm.Basic
import Mathlib.Data.Fintype.Perm
import Mathlib.Data.Set.Lattice
import Mathlib.Algebra.BigOperators.Group.Finset

open scoped BigOperators

namespace Semplex.GHSRT

/-! ## 1. Non-Circular Dense Restricted Yoneda & Groupoid Isotropy (`Task 143` WP-A/B/E) -/
namespace RestrictedYoneda

universe u v w

/-- Locally small category without assuming all objects are probes. -/
structure SemCat where
  Obj : Type u
  Hom : Obj → Obj → Type v
  id : ∀ a : Obj, Hom a a
  comp : ∀ {a b c : Obj}, Hom a b → Hom b c → Hom a c
  id_comp : ∀ {a b : Obj} (f : Hom a b), comp (id a) f = f
  comp_id : ∀ {a b : Obj} (f : Hom a b), comp f (id b) = f
  assoc : ∀ {a b c d : Obj} (f : Hom a b) (g : Hom b c) (h : Hom c d),
    comp (comp f g) h = comp f (comp g h)

/-- An isomorphism in `SemCat`. -/
@[ext]
structure SemIso (C : SemCat.{u, v}) (X Y : C.Obj) where
  toHom : C.Hom X Y
  invHom : C.Hom Y X
  left_inv : C.comp toHom invHom = C.id X
  right_inv : C.comp invHom toHom = C.id Y

instance semAutGroup (C : SemCat.{u, v}) (X : C.Obj) : Group (SemIso C X X) where
  one := ⟨C.id X, C.id X, C.id_comp _, C.id_comp _⟩
  mul f g := ⟨C.comp f.toHom g.toHom, C.comp g.invHom f.invHom,
    by
      calc C.comp (C.comp f.toHom g.toHom) (C.comp g.invHom f.invHom)
          = C.comp f.toHom (C.comp (C.comp g.toHom g.invHom) f.invHom) := by
            rw [C.assoc, ← C.assoc g.toHom g.invHom f.invHom]
        _ = C.comp f.toHom (C.comp (C.id X) f.invHom) := by rw [g.left_inv]
        _ = C.comp f.toHom f.invHom := by rw [C.id_comp]
        _ = C.id X := f.left_inv,
    by
      calc C.comp (C.comp g.invHom f.invHom) (C.comp f.toHom g.toHom)
          = C.comp g.invHom (C.comp (C.comp f.invHom f.toHom) g.toHom) := by
            rw [C.assoc, ← C.assoc f.invHom f.toHom g.toHom]
        _ = C.comp g.invHom (C.comp (C.id X) g.toHom) := by rw [f.right_inv]
        _ = C.comp g.invHom g.toHom := by rw [C.id_comp]
        _ = C.id X := g.right_inv⟩
  inv f := ⟨f.invHom, f.toHom, f.right_inv, f.left_inv⟩
  mul_assoc f g h := by
    apply SemIso.ext
    · change C.comp (C.comp f.toHom g.toHom) h.toHom = C.comp f.toHom (C.comp g.toHom h.toHom)
      exact C.assoc _ _ _
    · change C.comp h.invHom (C.comp g.invHom f.invHom) = C.comp (C.comp h.invHom g.invHom) f.invHom
      exact (C.assoc _ _ _).symm
  one_mul f := by
    apply SemIso.ext
    · exact C.id_comp f.toHom
    · exact C.comp_id f.invHom
  mul_one f := by
    apply SemIso.ext
    · exact C.comp_id f.toHom
    · exact C.id_comp f.invHom
  inv_mul_cancel f := by
    apply SemIso.ext
    · change C.comp f.invHom f.toHom = C.id X
      exact f.right_inv
    · change C.comp f.invHom f.toHom = C.id X
      exact f.right_inv

/-- Groupoid extending `SemCat`. -/
structure SemGroupoid extends SemCat.{u, v} where
  inv : ∀ {a b : Obj}, Hom a b → Hom b a
  inv_left : ∀ {a b : Obj} (f : Hom a b), comp (inv f) f = id b
  inv_right : ∀ {a b : Obj} (f : Hom a b), comp f (inv f) = id a

/-- Restricted probe profile: only probes in the image of `ι : P → C.Obj` are observed. -/
def RestrictedProfile (C : SemCat.{u, v}) {P : Type w} (ι : P → C.Obj)
    (X : C.Obj) (p : P) : Type v :=
  C.Hom (ι p) X

/-- Natural transformation between restricted probe profiles over the probe subcategory `ι`. -/
@[ext]
structure RestrictedNat (C : SemCat.{u, v}) {P : Type w} (ι : P → C.Obj)
    (X Y : C.Obj) where
  app : ∀ p : P, RestrictedProfile C ι X p → RestrictedProfile C ι Y p
  natural : ∀ {p q : P} (u : C.Hom (ι q) (ι p)) (f : RestrictedProfile C ι X p),
    app q (C.comp u f) = C.comp u (app p f)

/-- Natural isomorphism of restricted probe profiles (diagram composition order). -/
@[ext]
structure RestrictedNatIso (C : SemCat.{u, v}) {P : Type w} (ι : P → C.Obj)
    (X Y : C.Obj) where
  toNat : RestrictedNat C ι X Y
  invNat : RestrictedNat C ι Y X
  left_inv : ∀ p f, invNat.app p (toNat.app p f) = f
  right_inv : ∀ p g, toNat.app p (invNat.app p g) = g

def RestrictedNat.id (C : SemCat.{u, v}) {P : Type w} (ι : P → C.Obj) (X : C.Obj) :
    RestrictedNat C ι X X where
  app := fun _ f => f
  natural := fun _ _ => rfl

def RestrictedNat.comp {C : SemCat.{u, v}} {P : Type w} {ι : P → C.Obj}
    {X Y Z : C.Obj} (η : RestrictedNat C ι X Y) (θ : RestrictedNat C ι Y Z) :
    RestrictedNat C ι X Z where
  app := fun p f => θ.app p (η.app p f)
  natural := fun {_ _} u f => by
    calc θ.app _ (η.app _ (C.comp u f))
        = θ.app _ (C.comp u (η.app _ f)) := by rw [η.natural]
      _ = C.comp u (θ.app _ (η.app _ f)) := θ.natural u _

instance restrictedAutGroup (C : SemCat.{u, v}) {P : Type w} (ι : P → C.Obj)
    (X : C.Obj) : Group (RestrictedNatIso C ι X X) where
  one := ⟨RestrictedNat.id C ι X, RestrictedNat.id C ι X, fun _ _ => rfl, fun _ _ => rfl⟩
  mul η θ := ⟨η.toNat.comp θ.toNat, θ.invNat.comp η.invNat,
    fun p f => by simp [RestrictedNat.comp, θ.left_inv, η.left_inv],
    fun p g => by simp [RestrictedNat.comp, η.right_inv, θ.right_inv]⟩
  inv η := ⟨η.invNat, η.toNat, η.right_inv, η.left_inv⟩
  mul_assoc _ _ _ := by ext p f <;> rfl
  one_mul _ := by ext p f <;> rfl
  mul_one _ := by ext p f <;> rfl
  inv_mul_cancel η := by
    apply RestrictedNatIso.ext <;> ext p f
    · change η.toNat.app p (η.invNat.app p f) = f
      exact η.right_inv p f
    · change η.toNat.app p (η.invNat.app p f) = f
      exact η.right_inv p f

/-- The restricted Yoneda functor sends `g : X ⟶ Y` to postcomposition on probe responses. -/
def restrictedYoneda (C : SemCat.{u, v}) {P : Type w} (ι : P → C.Obj)
    {X Y : C.Obj} (g : C.Hom X Y) : RestrictedNat C ι X Y where
  app := fun _ f => C.comp f g
  natural := fun {_ _} u f => C.assoc u f g

theorem restrictedYoneda_id (C : SemCat.{u, v}) {P : Type w} (ι : P → C.Obj) (X : C.Obj) :
    restrictedYoneda C ι (C.id X) = RestrictedNat.id C ι X := by
  ext p f
  exact C.comp_id f

theorem restrictedYoneda_comp (C : SemCat.{u, v}) {P : Type w} (ι : P → C.Obj)
    {X Y Z : C.Obj} (g : C.Hom X Y) (h : C.Hom Y Z) :
    restrictedYoneda C ι (C.comp g h) =
      (restrictedYoneda C ι g).comp (restrictedYoneda C ι h) := by
  ext p f
  exact (C.assoc f g h).symm

/-- Non-circular density of the probe family `ι : P → C.Obj`: every object `X` is
    canonically the colimit of `(ι ↓ X) → C` — every cocone from probe responses into
    any target `Y` factors uniquely through a morphism `X ⟶ Y`. -/
def IsDenseProbeSubcat (C : SemCat.{u, v}) {P : Type w} (ι : P → C.Obj) : Prop :=
  ∀ (X Y : C.Obj)
    (cocone : ∀ p : P, C.Hom (ι p) X → C.Hom (ι p) Y),
    (∀ {p q : P} (u : C.Hom (ι q) (ι p)) (f : C.Hom (ι p) X),
      cocone q (C.comp u f) = C.comp u (cocone p f)) →
    ∃! m : C.Hom X Y, ∀ p (f : C.Hom (ι p) X), C.comp f m = cocone p f

/-- Full faithfulness equivalence from cocone density. -/
noncomputable def restrictedYoneda_homEquiv_of_dense
    (C : SemCat.{u, v}) {P : Type w} (ι : P → C.Obj)
    (hdense : IsDenseProbeSubcat C ι) (X Y : C.Obj) :
    C.Hom X Y ≃ RestrictedNat C ι X Y where
  toFun := restrictedYoneda C ι
  invFun η := Classical.choose (hdense X Y η.app η.natural)
  left_inv g := by
    have hex : ∃! m : C.Hom X Y, ∀ p f, C.comp f m = (restrictedYoneda C ι g).app p f :=
      hdense X Y (restrictedYoneda C ι g).app (restrictedYoneda C ι g).natural
    have huniq := (Classical.choose_spec hex).2 g (fun _ _ => rfl)
    exact huniq.symm
  right_inv η := by
    have hspec := (Classical.choose_spec (hdense X Y η.app η.natural)).1
    ext p f
    exact hspec p f

/-- Dense probe subcategories make `restrictedYoneda` bijective iff cocones factor uniquely. -/
theorem dense_iff_restrictedYoneda_bijective
    (C : SemCat.{u, v}) {P : Type w} (ι : P → C.Obj) :
    IsDenseProbeSubcat C ι ↔
      ∀ X Y : C.Obj, Function.Bijective (fun g : C.Hom X Y => restrictedYoneda C ι g) := by
  constructor
  · intro hdense X Y
    exact (restrictedYoneda_homEquiv_of_dense C ι hdense X Y).bijective
  · intro hbij X Y cocone hnat
    let η : RestrictedNat C ι X Y := ⟨cocone, hnat⟩
    obtain ⟨m, hm⟩ := (hbij X Y).2 η
    refine ⟨m, ?_, ?_⟩
    · intro p f
      exact congr_arg (fun t => t.app p f) hm
    · intro m' hm'
      apply (hbij X Y).1
      rw [hm]
      ext p f
      exact hm' p f

/-- Density reflects probe-profile isomorphisms back to genuine object isomorphisms. -/
noncomputable def restrictedYoneda_reflects_iso_of_dense
    (C : SemCat.{u, v}) {P : Type w} (ι : P → C.Obj)
    (hdense : IsDenseProbeSubcat C ι) {X Y : C.Obj}
    (e : RestrictedNatIso C ι X Y) : SemIso C X Y :=
  let eqvXY := restrictedYoneda_homEquiv_of_dense C ι hdense X Y
  let eqvYX := restrictedYoneda_homEquiv_of_dense C ι hdense Y X
  let eqvXX := restrictedYoneda_homEquiv_of_dense C ι hdense X X
  let eqvYY := restrictedYoneda_homEquiv_of_dense C ι hdense Y Y
  { toHom := eqvXY.invFun e.toNat
    invHom := eqvYX.invFun e.invNat
    left_inv := by
      apply eqvXX.injective
      change restrictedYoneda C ι (C.comp (eqvXY.invFun e.toNat) (eqvYX.invFun e.invNat)) =
        restrictedYoneda C ι (C.id X)
      rw [restrictedYoneda_comp, restrictedYoneda_id]
      change ((eqvXY.toFun (eqvXY.invFun e.toNat)).comp (eqvYX.toFun (eqvYX.invFun e.invNat))) =
        RestrictedNat.id C ι X
      rw [eqvXY.right_inv, eqvYX.right_inv]
      ext p f
      exact e.left_inv p f
    right_inv := by
      apply eqvYY.injective
      change restrictedYoneda C ι (C.comp (eqvYX.invFun e.invNat) (eqvXY.invFun e.toNat)) =
        restrictedYoneda C ι (C.id Y)
      rw [restrictedYoneda_comp, restrictedYoneda_id]
      change ((eqvYX.toFun (eqvYX.invFun e.invNat)).comp (eqvXY.toFun (eqvXY.invFun e.toNat))) =
        RestrictedNat.id C ι Y
      rw [eqvXY.right_inv, eqvYX.right_inv]
      ext p g
      exact e.right_inv p g }

/-- Under probe density, object automorphism groups and restricted profile automorphism groups
    are canonically isomorphic as groups. -/
noncomputable def dense_autEquiv (C : SemCat.{u, v}) {P : Type w} (ι : P → C.Obj)
    (hdense : IsDenseProbeSubcat C ι) (X : C.Obj) :
    SemIso C X X ≃* RestrictedNatIso C ι X X where
  toFun f :=
    { toNat := restrictedYoneda C ι f.toHom
      invNat := restrictedYoneda C ι f.invHom
      left_inv := fun p x => by
        change C.comp (C.comp x f.toHom) f.invHom = x
        rw [C.assoc, f.left_inv, C.comp_id]
      right_inv := fun p x => by
        change C.comp (C.comp x f.invHom) f.toHom = x
        rw [C.assoc, f.right_inv, C.comp_id] }
  invFun e := restrictedYoneda_reflects_iso_of_dense C ι hdense e
  left_inv f := by
    let eqv := restrictedYoneda_homEquiv_of_dense C ι hdense X X
    ext
    · exact eqv.left_inv f.toHom
    · exact eqv.left_inv f.invHom
  right_inv e := by
    let eqv := restrictedYoneda_homEquiv_of_dense C ι hdense X X
    ext p f
    · exact congr_arg (fun t => t.app p f) (eqv.apply_symm_apply e.toNat)
    · exact congr_arg (fun t => t.app p f) (eqv.apply_symm_apply e.invNat)
  map_mul' f g := by
    ext p x
    · exact congr_arg (fun t => t.app p x) (restrictedYoneda_comp C ι f.toHom g.toHom)
    · exact congr_arg (fun t => t.app p x) (restrictedYoneda_comp C ι g.invHom f.invHom)

/-- Endomorphism group instance on a vertex `a` in a `SemGroupoid`. -/
instance loopGroup (G : SemGroupoid.{u, v}) (a : G.Obj) : Group (G.Hom a a) where
  one := G.id a
  mul := G.comp
  inv := G.inv
  mul_assoc f g h := by
    change G.comp (G.comp f g) h = G.comp f (G.comp g h)
    exact G.assoc f g h
  one_mul := G.id_comp
  mul_one := G.comp_id
  inv_mul_cancel := G.inv_left

/-- Closes ChatGPT's open gap in `ConnectedIsotropy.lean`: conjugation transport along any
    groupoid arrow is a genuine `MulEquiv` (preserving `1`, `*`, `⁻¹`). -/
def automorphismTransport_isGroupIso (G : SemGroupoid.{u, v}) {a b : G.Obj}
    (f : G.Hom a b) : G.Hom a a ≃* G.Hom b b where
  toFun h := G.comp (G.comp (G.inv f) h) f
  invFun k := G.comp (G.comp f k) (G.inv f)
  left_inv h := by
    calc G.comp (G.comp f (G.comp (G.comp (G.inv f) h) f)) (G.inv f)
        = G.comp f (G.comp (G.comp (G.comp (G.inv f) h) f) (G.inv f)) := G.assoc _ _ _
      _ = G.comp f (G.comp (G.comp (G.inv f) h) (G.comp f (G.inv f))) := by rw [G.assoc]
      _ = G.comp f (G.comp (G.inv f) h) := by rw [G.inv_right, G.comp_id]
      _ = G.comp (G.comp f (G.inv f)) h := (G.assoc _ _ _).symm
      _ = h := by rw [G.inv_right, G.id_comp]
  right_inv k := by
    calc G.comp (G.comp (G.inv f) (G.comp (G.comp f k) (G.inv f))) f
        = G.comp (G.inv f) (G.comp (G.comp (G.comp f k) (G.inv f)) f) := G.assoc _ _ _
      _ = G.comp (G.inv f) (G.comp (G.comp f k) (G.comp (G.inv f) f)) := by rw [G.assoc]
      _ = G.comp (G.inv f) (G.comp f k) := by rw [G.inv_left, G.comp_id]
      _ = G.comp (G.comp (G.inv f) f) k := (G.assoc _ _ _).symm
      _ = k := by rw [G.inv_left, G.id_comp]
  map_mul' h₁ h₂ := by
    change G.comp (G.comp (G.inv f) (G.comp h₁ h₂)) f =
      G.comp (G.comp (G.comp (G.inv f) h₁) f) (G.comp (G.comp (G.inv f) h₂) f)
    calc G.comp (G.comp (G.inv f) (G.comp h₁ h₂)) f
        = G.comp (G.comp (G.comp (G.inv f) h₁) h₂) f := by rw [← G.assoc (G.inv f) h₁ h₂]
      _ = G.comp (G.comp (G.inv f) h₁) (G.comp h₂ f) := G.assoc _ _ _
      _ = G.comp (G.comp (G.inv f) h₁) (G.comp (G.id a) (G.comp h₂ f)) := by rw [G.id_comp]
      _ = G.comp (G.comp (G.inv f) h₁) (G.comp (G.comp f (G.inv f)) (G.comp h₂ f)) := by
          congr 1
          congr 1
          exact (G.inv_right f).symm
      _ = G.comp (G.comp (G.inv f) h₁) (G.comp f (G.comp (G.inv f) (G.comp h₂ f))) := by
          congr 1
          exact G.assoc f (G.inv f) (G.comp h₂ f)
      _ = G.comp (G.comp (G.comp (G.inv f) h₁) f) (G.comp (G.inv f) (G.comp h₂ f)) := by
          exact (G.assoc (G.comp (G.inv f) h₁) f (G.comp (G.inv f) (G.comp h₂ f))).symm
      _ = G.comp (G.comp (G.comp (G.inv f) h₁) f) (G.comp (G.comp (G.inv f) h₂) f) := by
          congr 1
          exact (G.assoc (G.inv f) h₂ f).symm

def DiscreteHom : Bool → Bool → Type
  | true, true => Bool
  | false, false => Bool
  | _, _ => Empty

/-- Counterexample: a non-dense probe subcategory (`Bool` category with morphisms only on
    `false → false` and `true → true`, probing only at `false`) fails faithfulness on `true`. -/
def discreteBoolCat : SemCat.{0, 0} where
  Obj := Bool
  Hom := DiscreteHom
  id a := match a with | true => false | false => false
  comp {a b c} f g := by
    cases a <;> cases b <;> cases c <;>
      first | exact Empty.elim f | exact Empty.elim g | exact Bool.xor f g
  id_comp {a b} f := by
    cases a <;> cases b <;> first | exact Empty.elim f | (cases f <;> rfl)
  comp_id {a b} f := by
    cases a <;> cases b <;> first | exact Empty.elim f | (cases f <;> rfl)
  assoc {a b c d} f g h := by
    cases a <;> cases b <;> cases c <;> cases d <;>
      first | exact Empty.elim f | exact Empty.elim g | exact Empty.elim h |
        (cases f <;> cases g <;> cases h <;> rfl)

theorem nonDense_probe_fails_faithfulness :
    ∃ (m₁ m₂ : discreteBoolCat.Hom true true),
      m₁ ≠ m₂ ∧
      restrictedYoneda discreteBoolCat (fun _ : Unit => false) m₁ =
        restrictedYoneda discreteBoolCat (fun _ : Unit => false) m₂ := by
  refine ⟨(false : Bool), (true : Bool), Bool.false_ne_true, ?_⟩
  ext _ f
  exact f.elim

end RestrictedYoneda

/-! ## 2. Indexed Grounded Semantic Fibrations & Countermodels (`Task 143` WP-C/E) -/
namespace GroundedFibration

universe u v w

/-- Relational reference + satisfaction + state-indexed evidence (never silently complete). -/
structure GroundedFiber where
  World : Type u
  Claim : Type v
  ref : Claim → World → Prop
  sat : Claim → World → Prop
  Ev : Claim → World → Type w
  ev_sound : ∀ c w, ref c w → Ev c w → sat c w

def GroundedTruth (F : GroundedFiber.{u, v, w}) (c : F.Claim) (w : F.World) : Prop :=
  F.ref c w ∧ F.sat c w

/-- Cartesian / structure-preserving morphism between grounded fibers. -/
structure CartesianGroundedMorphism (F₁ F₂ : GroundedFiber.{u, v, w}) where
  mapWorld : F₁.World → F₂.World
  mapClaim : F₁.Claim → F₂.Claim
  mapEv : ∀ c w, F₁.Ev c w → F₂.Ev (mapClaim c) (mapWorld w)
  ref_iff : ∀ c w, F₁.ref c w ↔ F₂.ref (mapClaim c) (mapWorld w)
  sat_iff : ∀ c w, F₁.sat c w ↔ F₂.sat (mapClaim c) (mapWorld w)

/-- Context-indexed contravariant fibration of grounded semantics over a context category `Ctx`. -/
structure IndexedGroundedFibration (Ctx : RestrictedYoneda.SemCat.{u, v}) where
  fiber : Ctx.Obj → GroundedFiber.{u, v, w}
  reidx : ∀ {c d : Ctx.Obj}, Ctx.Hom c d → CartesianGroundedMorphism (fiber d) (fiber c)
  reidx_id_world : ∀ (c : Ctx.Obj) (x : (fiber c).World),
    (reidx (Ctx.id c)).mapWorld x = x
  reidx_id_claim : ∀ (c : Ctx.Obj) (k : (fiber c).Claim),
    (reidx (Ctx.id c)).mapClaim k = k
  reidx_comp_world : ∀ {a b c : Ctx.Obj} (f : Ctx.Hom a b) (g : Ctx.Hom b c)
    (x : (fiber c).World),
    (reidx (Ctx.comp f g)).mapWorld x = (reidx f).mapWorld ((reidx g).mapWorld x)
  reidx_comp_claim : ∀ {a b c : Ctx.Obj} (f : Ctx.Hom a b) (g : Ctx.Hom b c)
    (k : (fiber c).Claim),
    (reidx (Ctx.comp f g)).mapClaim k = (reidx f).mapClaim ((reidx g).mapClaim k)

theorem cartesian_groundedTruth_iff
    {F₁ F₂ : GroundedFiber.{u, v, w}} (M : CartesianGroundedMorphism F₁ F₂)
    (c : F₁.Claim) (x : F₁.World) :
    GroundedTruth F₁ c x ↔ GroundedTruth F₂ (M.mapClaim c) (M.mapWorld x) := by
  unfold GroundedTruth
  constructor
  · rintro ⟨href, hsat⟩
    exact ⟨(M.ref_iff c x).mp href, (M.sat_iff c x).mp hsat⟩
  · rintro ⟨href, hsat⟩
    exact ⟨(M.ref_iff c x).mpr href, (M.sat_iff c x).mpr hsat⟩

theorem cartesian_evidence_soundness_transfer
    {F₁ F₂ : GroundedFiber.{u, v, w}} (M : CartesianGroundedMorphism F₁ F₂)
    (c : F₁.Claim) (x : F₁.World) (href : F₁.ref c x) (ev : F₁.Ev c x) :
    GroundedTruth F₂ (M.mapClaim c) (M.mapWorld x) :=
  (cartesian_groundedTruth_iff M c x).mp ⟨href, F₁.ev_sound c x href ev⟩

theorem fibration_reidx_preserves_groundedTruth
    {Ctx : RestrictedYoneda.SemCat.{u, v}}
    (Fib : IndexedGroundedFibration.{u, v, w} Ctx)
    {c d : Ctx.Obj} (u : Ctx.Hom c d)
    (k : (Fib.fiber d).Claim) (x : (Fib.fiber d).World) :
    GroundedTruth (Fib.fiber d) k x ↔
      GroundedTruth (Fib.fiber c) ((Fib.reidx u).mapClaim k) ((Fib.reidx u).mapWorld x) :=
  cartesian_groundedTruth_iff (Fib.reidx u) k x

/-- Countermodel 1: two fibers with identical bare carriers and identical probe maps
    can still assign opposite `GroundedTruth`. -/
def fiberTrue : GroundedFiber.{0, 0, 0} where
  World := Unit
  Claim := Unit
  ref := fun _ _ => True
  sat := fun _ _ => True
  Ev := fun _ _ => Empty
  ev_sound := fun _ _ _ e => nomatch e

def fiberFalse : GroundedFiber.{0, 0, 0} where
  World := Unit
  Claim := Unit
  ref := fun _ _ => True
  sat := fun _ _ => False
  Ev := fun _ _ => Empty
  ev_sound := fun _ _ _ e => nomatch e

theorem ungrounded_equiv_disagrees_on_truth :
    GroundedTruth fiberTrue () () ∧ ¬ GroundedTruth fiberFalse () () := by
  refine ⟨⟨trivial, trivial⟩, ?_⟩
  rintro ⟨_, h⟩
  exact h

/-- Countermodel 2: soundness of evidence never implies completeness. -/
theorem sound_evidence_not_complete :
    GroundedTruth fiberTrue () () ∧ IsEmpty (fiberTrue.Ev () ()) := by
  exact ⟨⟨trivial, trivial⟩, ⟨fun e => nomatch e⟩⟩

/-- Audit 3 regression witness: an unindexed universal `SoundEvidence` together with an
    existential `CompleteEvidence` collapses state-contingent satisfaction into constants. -/
theorem unindexed_complete_collapses_contingency
    {S C : Type*} (sat : C → S → Prop) (Ev : C → Type*)
    (hSound : ∀ c s, Ev c → sat c s)
    (hComplete : ∀ c s, sat c s → Nonempty (Ev c)) :
    ∀ c s₁ s₂, sat c s₁ → sat c s₂ := by
  intro c s₁ s₂ hs₁
  obtain ⟨ev⟩ := hComplete c s₁ hs₁
  exact hSound c s₂ ev

end GroundedFibration

/-! ## 3. Constructive Spanning-Tree Extraction from Pure Connectivity (`Task 143` + `Stage F`) -/
namespace ConstructiveTree

universe u v w

structure FiniteGraph (V : Type u) (E : Type v) where
  src : E → V
  tgt : E → V

/-- Bidirectional oriented edge step (`rev = false` traverses `src → tgt`, `rev = true` traverses `tgt → src`). -/
structure SignedStep {V : Type u} {E : Type v} (D : FiniteGraph V E) (x y : V) where
  edge : E
  rev : Bool
  src_eq : (if rev then D.tgt edge else D.src edge) = x
  tgt_eq : (if rev then D.src edge else D.tgt edge) = y

def stepTransport {V : Type u} {E : Type v} {G : Type w} [Group G]
    (D : FiniteGraph V E) (A : E → G) {x y : V} (s : SignedStep D x y) : G :=
  if s.rev then (A s.edge)⁻¹ else A s.edge

theorem stepTransport_gauge_covariant
    {V : Type u} {E : Type v} {G : Type w} [Group G]
    (D : FiniteGraph V E) (A : E → G) (g : V → G) {x y : V} (s : SignedStep D x y) :
    stepTransport D (fun e => g (D.tgt e) * A e * (g (D.src e))⁻¹) s =
      g y * stepTransport D A s * (g x)⁻¹ := by
  cases hr : s.rev
  · have hx : D.src s.edge = x := by simpa [hr] using s.src_eq
    have hy : D.tgt s.edge = y := by simpa [hr] using s.tgt_eq
    simp [stepTransport, hr, hx, hy]
  · have hx : D.tgt s.edge = x := by simpa [hr] using s.src_eq
    have hy : D.src s.edge = y := by simpa [hr] using s.tgt_eq
    simp [stepTransport, hr, hx, hy, mul_assoc]

/-- Bidirectional walks over `D`. -/
inductive SignedWalk {V : Type u} {E : Type v} (D : FiniteGraph V E) : V → V → Type max u v where
  | nil {x : V} : SignedWalk D x x
  | cons {x y z : V} : SignedStep D x y → SignedWalk D y z → SignedWalk D x z

def SignedWalk.length {V : Type u} {E : Type v} {D : FiniteGraph V E} :
    {x y : V} → SignedWalk D x y → ℕ
  | _, _, .nil => 0
  | _, _, .cons _ rest => rest.length + 1

def SignedWalk.append {V : Type u} {E : Type v} {D : FiniteGraph V E} :
    {x y z : V} → SignedWalk D x y → SignedWalk D y z → SignedWalk D x z
  | _, _, _, .nil, q => q
  | _, _, _, .cons s rest, q => .cons s (rest.append q)

def signedTransport {V : Type u} {E : Type v} {G : Type w} [Group G]
    (D : FiniteGraph V E) (A : E → G) : {x y : V} → SignedWalk D x y → G
  | _, _, .nil => 1
  | _, _, .cons s rest => signedTransport D A rest * stepTransport D A s

theorem signedTransport_append {V : Type u} {E : Type v} {G : Type w} [Group G]
    (D : FiniteGraph V E) (A : E → G) :
    ∀ {x y z : V} (p : SignedWalk D x y) (q : SignedWalk D y z),
      signedTransport D A (p.append q) =
        signedTransport D A q * signedTransport D A p
  | _, _, _, .nil, q => by simp [SignedWalk.append, signedTransport]
  | _, _, _, .cons s rest, q => by
      simp [SignedWalk.append, signedTransport, signedTransport_append, mul_assoc]

theorem signedTransport_gauge_covariant
    {V : Type u} {E : Type v} {G : Type w} [Group G]
    (D : FiniteGraph V E) (A : E → G) (g : V → G) :
    ∀ {x y : V} (p : SignedWalk D x y),
      signedTransport D (fun e => g (D.tgt e) * A e * (g (D.src e))⁻¹) p =
        g y * signedTransport D A p * (g x)⁻¹
  | x, _, .nil => by simp [signedTransport]
  | _, z, .cons s rest => by
      have ih := signedTransport_gauge_covariant D A g rest
      have hs := stepTransport_gauge_covariant D A g s
      simp only [signedTransport, ih, hs]
      group

theorem walk_decompose_last {V : Type u} {E : Type v} {D : FiniteGraph V E} :
    ∀ {a b : V} (w : SignedWalk D a b),
      (w.length = 0 ∧ a = b) ∨
        (∃ c : V, ∃ w' : SignedWalk D a c, ∃ _ : SignedStep D c b, w'.length + 1 = w.length)
  | a, _, .nil => Or.inl ⟨rfl, rfl⟩
  | a, _, .cons s₁ rest => by
      rcases walk_decompose_last rest with ⟨hlen, hEq⟩ | ⟨c, w', sLast, hlen⟩
      · subst hEq
        exact Or.inr ⟨a, .nil, s₁, by simp [SignedWalk.length, hlen]⟩
      · exact Or.inr ⟨c, .cons s₁ w', sLast, by simp [SignedWalk.length, hlen]⟩

section ExtractedTree

open Classical

theorem SignedWalk.append_length {V : Type u} {E : Type v} {D : FiniteGraph V E} :
    ∀ {x y z : V} (p : SignedWalk D x y) (q : SignedWalk D y z),
      (p.append q).length = p.length + q.length
  | _, _, _, .nil, q => by simp [SignedWalk.append, SignedWalk.length]
  | _, _, _, .cons s rest, q => by
      simp [SignedWalk.append, SignedWalk.length, SignedWalk.append_length]
      omega

private lemma exists_len {V : Type u} {E : Type v} (D : FiniteGraph V E) (root : V)
    (hConn : ∀ v : V, Nonempty (SignedWalk D root v)) (v : V) :
    ∃ n : ℕ, ∃ w : SignedWalk D root v, w.length = n := by
  obtain ⟨w⟩ := hConn v
  exact ⟨w.length, w, rfl⟩

/-- Shortest bidirectional walk distance from `root` to `v`. -/
noncomputable def minDist {V : Type u} {E : Type v} (D : FiniteGraph V E) (root : V)
    (hConn : ∀ v : V, Nonempty (SignedWalk D root v)) (v : V) : ℕ :=
  Nat.find (exists_len D root hConn v)

theorem minDist_root {V : Type u} {E : Type v} (D : FiniteGraph V E) (root : V)
    (hConn : ∀ v : V, Nonempty (SignedWalk D root v)) :
    minDist D root hConn root = 0 := by
  unfold minDist
  rw [Nat.find_eq_zero]
  exact ⟨.nil, rfl⟩

theorem minDist_pos_of_ne {V : Type u} {E : Type v} (D : FiniteGraph V E) (root : V)
    (hConn : ∀ v : V, Nonempty (SignedWalk D root v)) {v : V} (hv : v ≠ root) :
    0 < minDist D root hConn v := by
  by_contra hle
  have hzero : minDist D root hConn v = 0 := Nat.eq_zero_of_not_pos hle
  obtain ⟨w, hw⟩ := Nat.find_spec (exists_len D root hConn v)
  change w.length = minDist D root hConn v at hw
  rw [hzero] at hw
  cases w with
  | nil => exact hv rfl
  | cons _ _ => simp [SignedWalk.length] at hw

/-- Every non-root vertex admits a signed parent edge from a strictly closer neighbor `u`. -/
theorem exists_parent_step {V : Type u} {E : Type v} (D : FiniteGraph V E) (root : V)
    (hConn : ∀ v : V, Nonempty (SignedWalk D root v)) {v : V} (hv : v ≠ root) :
    ∃ u : V, ∃ _ : SignedStep D u v, minDist D root hConn u + 1 = minDist D root hConn v := by
  obtain ⟨w, hw⟩ := Nat.find_spec (exists_len D root hConn v)
  change w.length = minDist D root hConn v at hw
  rcases walk_decompose_last w with ⟨_, hEq⟩ | ⟨u, w', s, hlen⟩
  · exact absurd hEq.symm hv
  · have _hw_dist : w'.length + 1 = minDist D root hConn v := hlen.trans hw
    have hu_le : minDist D root hConn u ≤ w'.length := Nat.find_min' _ ⟨w', rfl⟩
    have hv_le : minDist D root hConn v ≤ minDist D root hConn u + 1 := by
      obtain ⟨wu, hwu⟩ := Nat.find_spec (exists_len D root hConn u)
      change wu.length = minDist D root hConn u at hwu
      have hmin : minDist D root hConn v ≤ (wu.append (.cons s .nil)).length :=
        Nat.find_min' _ ⟨wu.append (.cons s .nil), rfl⟩
      rw [SignedWalk.append_length] at hmin
      have _hs1 : (SignedWalk.cons s (.nil : SignedWalk D v v)).length = 1 := rfl
      omega
    have hu_eq : minDist D root hConn u + 1 = minDist D root hConn v := by omega
    exact ⟨u, s, hu_eq⟩

noncomputable def parentVertex {V : Type u} {E : Type v} (D : FiniteGraph V E) (root : V)
    (hConn : ∀ v : V, Nonempty (SignedWalk D root v)) {v : V} (hv : v ≠ root) : V :=
  Classical.choose (exists_parent_step D root hConn hv)

noncomputable def parentStep {V : Type u} {E : Type v} (D : FiniteGraph V E) (root : V)
    (hConn : ∀ v : V, Nonempty (SignedWalk D root v)) {v : V} (hv : v ≠ root) :
    SignedStep D (parentVertex D root hConn hv) v :=
  Classical.choose (Classical.choose_spec (exists_parent_step D root hConn hv))

theorem parent_dist_lt {V : Type u} {E : Type v} (D : FiniteGraph V E) (root : V)
    (hConn : ∀ v : V, Nonempty (SignedWalk D root v)) {v : V} (hv : v ≠ root) :
    minDist D root hConn (parentVertex D root hConn hv) < minDist D root hConn v := by
  have hs : minDist D root hConn (parentVertex D root hConn hv) + 1 = minDist D root hConn v :=
    Classical.choose_spec (Classical.choose_spec (exists_parent_step D root hConn hv))
  omega

noncomputable def parentEdge {V : Type u} {E : Type v} (D : FiniteGraph V E) (root : V)
    (hConn : ∀ v : V, Nonempty (SignedWalk D root v)) {v : V} (hv : v ≠ root) : E :=
  (parentStep D root hConn hv).edge

def isTreeEdge {V : Type u} {E : Type v} (D : FiniteGraph V E) (root : V)
    (hConn : ∀ v : V, Nonempty (SignedWalk D root v)) (e : E) : Prop :=
  ∃ v : V, ∃ hv : v ≠ root, parentEdge D root hConn hv = e

def isChordEdge {V : Type u} {E : Type v} (D : FiniteGraph V E) (root : V)
    (hConn : ∀ v : V, Nonempty (SignedWalk D root v)) (e : E) : Prop :=
  ¬ isTreeEdge D root hConn e

/-- Automatically disjoint partition into tree and chord edges (fixes missing `Graph.disjoint`). -/
theorem tree_chord_disjoint {V : Type u} {E : Type v} (D : FiniteGraph V E) (root : V)
    (hConn : ∀ v : V, Nonempty (SignedWalk D root v)) (e : E) :
    ¬ (isTreeEdge D root hConn e ∧ isChordEdge D root hConn e) :=
  fun ⟨ht, hc⟩ => hc ht

private lemma parentStep_edge_unique_aux {V : Type u} {E : Type v} (D : FiniteGraph V E)
    {u₁ u₂ v₁ v₂ : V} (d : V → ℕ)
    (s₁ : SignedStep D u₁ v₁) (s₂ : SignedStep D u₂ v₂)
    (hlt₁ : d u₁ < d v₁) (hlt₂ : d u₂ < d v₂)
    (hed : s₁.edge = s₂.edge) : v₁ = v₂ := by
  cases hr₁ : s₁.rev <;> cases hr₂ : s₂.rev
  · have ht₁ : D.tgt s₁.edge = v₁ := by simpa [hr₁] using s₁.tgt_eq
    have ht₂ : D.tgt s₂.edge = v₂ := by simpa [hr₂] using s₂.tgt_eq
    calc v₁ = D.tgt s₁.edge := ht₁.symm
      _ = D.tgt s₂.edge := congrArg D.tgt hed
      _ = v₂ := ht₂
  · have hs₁ : D.src s₁.edge = u₁ := by simpa [hr₁] using s₁.src_eq
    have ht₁ : D.tgt s₁.edge = v₁ := by simpa [hr₁] using s₁.tgt_eq
    have hs₂ : D.tgt s₂.edge = u₂ := by simpa [hr₂] using s₂.src_eq
    have ht₂ : D.src s₂.edge = v₂ := by simpa [hr₂] using s₂.tgt_eq
    have huv₁ : u₁ = v₂ := hs₁.symm.trans ((congrArg D.src hed).trans ht₂)
    have huv₂ : v₁ = u₂ := ht₁.symm.trans ((congrArg D.tgt hed).trans hs₂)
    rw [huv₁, huv₂] at hlt₁
    exact absurd hlt₁ (Nat.lt_asymm hlt₂)
  · have hs₁ : D.tgt s₁.edge = u₁ := by simpa [hr₁] using s₁.src_eq
    have ht₁ : D.src s₁.edge = v₁ := by simpa [hr₁] using s₁.tgt_eq
    have hs₂ : D.src s₂.edge = u₂ := by simpa [hr₂] using s₂.src_eq
    have ht₂ : D.tgt s₂.edge = v₂ := by simpa [hr₂] using s₂.tgt_eq
    have huv₁ : u₁ = v₂ := hs₁.symm.trans ((congrArg D.tgt hed).trans ht₂)
    have huv₂ : v₁ = u₂ := ht₁.symm.trans ((congrArg D.src hed).trans hs₂)
    rw [huv₁, huv₂] at hlt₁
    exact absurd hlt₁ (Nat.lt_asymm hlt₂)
  · have ht₁ : D.src s₁.edge = v₁ := by simpa [hr₁] using s₁.tgt_eq
    have ht₂ : D.src s₂.edge = v₂ := by simpa [hr₂] using s₂.tgt_eq
    calc v₁ = D.src s₁.edge := ht₁.symm
      _ = D.src s₂.edge := congrArg D.src hed
      _ = v₂ := ht₂

/-- Parent assignment is injective on non-root vertices: no tree edge can be chosen by two
    distinct children, because any edge connects two depths differing by 1 and the parent step
    must go strictly deeper. -/
theorem parentEdge_unique_child {V : Type u} {E : Type v} (D : FiniteGraph V E) (root : V)
    (hConn : ∀ v : V, Nonempty (SignedWalk D root v)) {v₁ v₂ : V} (hv₁ : v₁ ≠ root) (hv₂ : v₂ ≠ root)
    (heq : parentEdge D root hConn hv₁ = parentEdge D root hConn hv₂) : v₁ = v₂ :=
  parentStep_edge_unique_aux D (minDist D root hConn)
    (parentStep D root hConn hv₁) (parentStep D root hConn hv₂)
    (parent_dist_lt D root hConn hv₁) (parent_dist_lt D root hConn hv₂) heq

/-- Well-founded tree frame computed recursively down the shortest-path tree without assuming
    any out-arborescence orientation or certificate axioms. -/
noncomputable def treeFrame {V : Type u} {E : Type v} (D : FiniteGraph V E) (root : V)
    (hConn : ∀ v : V, Nonempty (SignedWalk D root v))
    {G : Type w} [Group G] (A : E → G) (v : V) : G :=
  if hv : v = root then 1
  else stepTransport D A (parentStep D root hConn hv) *
    treeFrame D root hConn A (parentVertex D root hConn hv)
termination_by minDist D root hConn v
decreasing_by
  exact parent_dist_lt D root hConn hv

theorem treeFrame_root {V : Type u} {E : Type v} (D : FiniteGraph V E) (root : V)
    (hConn : ∀ v : V, Nonempty (SignedWalk D root v))
    {G : Type w} [Group G] (A : E → G) :
    treeFrame D root hConn A root = 1 := by
  rw [treeFrame]
  simp

theorem treeFrame_step {V : Type u} {E : Type v} (D : FiniteGraph V E) (root : V)
    (hConn : ∀ v : V, Nonempty (SignedWalk D root v))
    {G : Type w} [Group G] (A : E → G) {v : V} (hv : v ≠ root) :
    treeFrame D root hConn A v =
      stepTransport D A (parentStep D root hConn hv) *
        treeFrame D root hConn A (parentVertex D root hConn hv) := by
  rw [treeFrame, dif_neg hv]

/-- Automatic bidirectional tree-edge recursion (`P_A(tgt e) = A e * P_A(src e)`) for BOTH
    edge orientations relative to `root`. -/
theorem constructive_treeFrame_edge_recursion {V : Type u} {E : Type v} (D : FiniteGraph V E)
    (root : V) (hConn : ∀ v : V, Nonempty (SignedWalk D root v))
    {G : Type w} [Group G] (A : E → G)
    (e : E) (ht : isTreeEdge D root hConn e) :
    treeFrame D root hConn A (D.tgt e) = A e * treeFrame D root hConn A (D.src e) := by
  rcases ht with ⟨v, hv, he⟩
  have hstep := treeFrame_step D root hConn A hv
  set s := parentStep D root hConn hv
  change s.edge = e at he
  cases hr : s.rev
  · have hsrc : D.src e = parentVertex D root hConn hv := by simpa [hr, he] using s.src_eq
    have htgt : D.tgt e = v := by simpa [hr, he] using s.tgt_eq
    rw [htgt, hsrc, hstep]
    simp [stepTransport, hr, he]
  · have hsrc : D.tgt e = parentVertex D root hConn hv := by simpa [hr, he] using s.src_eq
    have htgt : D.src e = v := by simpa [hr, he] using s.tgt_eq
    rw [hsrc, htgt, hstep]
    simp [stepTransport, hr, he, mul_assoc]

/-- Gauge covariance of the constructively extracted tree frame. -/
theorem constructive_treeFrame_gauge_covariant {V : Type u} {E : Type v} (D : FiniteGraph V E)
    (root : V) (hConn : ∀ v : V, Nonempty (SignedWalk D root v))
    {G : Type w} [Group G] (A : E → G) (g : V → G) :
    ∀ v : V,
      treeFrame D root hConn (fun e => g (D.tgt e) * A e * (g (D.src e))⁻¹) v =
        g v * treeFrame D root hConn A v * (g root)⁻¹ := by
  have hStrong : ∀ n (v : V), minDist D root hConn v = n →
      treeFrame D root hConn (fun e => g (D.tgt e) * A e * (g (D.src e))⁻¹) v =
        g v * treeFrame D root hConn A v * (g root)⁻¹ := by
    intro n
    induction n using Nat.strong_induction_on with
    | h n ih =>
      intro v hd
      by_cases hv : v = root
      · subst hv
        simp [treeFrame_root]
      · have hlt : minDist D root hConn (parentVertex D root hConn hv) < n := by
          rw [← hd]
          exact parent_dist_lt D root hConn hv
        have ih_p := ih _ hlt (parentVertex D root hConn hv) rfl
        rw [treeFrame_step D root hConn _ hv, treeFrame_step D root hConn _ hv,
          stepTransport_gauge_covariant, ih_p]
        group
  intro v
  exact hStrong _ v rfl

/-- Unique gauge reconstruction from a tree edge partition extracted purely from `hConn`. -/
theorem constructive_spanningTree_gauge_uniqueness {V : Type u} {E : Type v} (D : FiniteGraph V E)
    (root : V) (hConn : ∀ v : V, Nonempty (SignedWalk D root v))
    {G : Type w} [Group G] (A B : E → G) (g : V → G)
    (hAct : ∀ e, g (D.tgt e) * A e * (g (D.src e))⁻¹ = B e) (v : V) :
    g v = treeFrame D root hConn B v * g root * (treeFrame D root hConn A v)⁻¹ := by
  have heq : (fun e => g (D.tgt e) * A e * (g (D.src e))⁻¹) = B := funext hAct
  have hcov := constructive_treeFrame_gauge_covariant D root hConn A g v
  rw [heq] at hcov
  calc g v = (g v * treeFrame D root hConn A v * (g root)⁻¹) *
        (g root * (treeFrame D root hConn A v)⁻¹) := by group
    _ = treeFrame D root hConn B v * g root * (treeFrame D root hConn A v)⁻¹ := by
        rw [← hcov]; group

end ExtractedTree

end ConstructiveTree

/-! ## 4. Quantales as Formal Concept Lattices (`arXiv:2608.26631`, Shen & Zhao 2026) -/
namespace ConceptQuantale

def polarUp {S T : Type*} (R : S → T → Prop) (A : Set S) : Set T :=
  {t | ∀ s ∈ A, R s t}

def polarDown {S T : Type*} (R : S → T → Prop) (B : Set T) : Set S :=
  {s | ∀ t ∈ B, R s t}

def gamma {S T : Type*} (R : S → T → Prop) (A : Set S) : Set S :=
  polarDown R (polarUp R A)

theorem subset_gamma {S T : Type*} (R : S → T → Prop) (A : Set S) :
    A ⊆ gamma R A :=
  fun _ hs _ ht => ht _ hs

theorem gamma_mono {S T : Type*} (R : S → T → Prop) {A B : Set S} (h : A ⊆ B) :
    gamma R A ⊆ gamma R B := by
  intro s hs t ht
  exact hs t fun a ha => ht a (h ha)

theorem gamma_idem {S T : Type*} (R : S → T → Prop) (A : Set S) :
    gamma R (gamma R A) = gamma R A := by
  apply Set.Subset.antisymm
  · intro s hs t ht
    exact hs t fun x hx => hx t ht
  · exact subset_gamma R (gamma R A)

def setMul {S : Type*} [Mul S] (A B : Set S) : Set S :=
  {z | ∃ a ∈ A, ∃ b ∈ B, z = a * b}

/-- Residuated semigroup relation compatibility (`Shen & Zhao 2026` closure stability). -/
def IsResiduatedRel {S T : Type*} [Mul S] (R : S → T → Prop) : Prop :=
  (∀ s t, gamma R {x | R (x * s) t} = {x | R (x * s) t}) ∧
  (∀ s t, gamma R {x | R (s * x) t} = {x | R (s * x) t})

theorem setMul_gamma_subset_left {S T : Type*} [Mul S]
    (R : S → T → Prop) (hRes : IsResiduatedRel R) (A B : Set S) :
    setMul (gamma R A) B ⊆ gamma R (setMul A B) := by
  rintro z ⟨x, hx, b, hb, rfl⟩ t ht
  have hSub : A ⊆ {y | R (y * b) t} := fun a ha => ht (a * b) ⟨a, ha, b, hb, rfl⟩
  have hx' : x ∈ gamma R {y | R (y * b) t} := gamma_mono R hSub hx
  rw [hRes.1 b t] at hx'
  exact hx'

theorem setMul_gamma_subset_right {S T : Type*} [Mul S]
    (R : S → T → Prop) (hRes : IsResiduatedRel R) (A B : Set S) :
    setMul A (gamma R B) ⊆ gamma R (setMul A B) := by
  rintro z ⟨a, ha, y, hy, rfl⟩ t ht
  have hSub : B ⊆ {x | R (a * x) t} := fun b hb => ht (a * b) ⟨a, ha, b, hb, rfl⟩
  have hy' : y ∈ gamma R {x | R (a * x) t} := gamma_mono R hSub hy
  rw [hRes.2 a t] at hy'
  exact hy'

theorem gamma_setMul_left {S T : Type*} [Mul S]
    (R : S → T → Prop) (hRes : IsResiduatedRel R) (A B : Set S) :
    gamma R (setMul (gamma R A) B) = gamma R (setMul A B) := by
  apply Set.Subset.antisymm
  · rw [← gamma_idem R (setMul A B)]
    exact gamma_mono R (setMul_gamma_subset_left R hRes A B)
  · exact gamma_mono R fun z ⟨a, ha, b, hb, hz⟩ => ⟨a, subset_gamma R A ha, b, hb, hz⟩

theorem gamma_setMul_right {S T : Type*} [Mul S]
    (R : S → T → Prop) (hRes : IsResiduatedRel R) (A B : Set S) :
    gamma R (setMul A (gamma R B)) = gamma R (setMul A B) := by
  apply Set.Subset.antisymm
  · rw [← gamma_idem R (setMul A B)]
    exact gamma_mono R (setMul_gamma_subset_right R hRes A B)
  · exact gamma_mono R fun z ⟨a, ha, b, hb, hz⟩ => ⟨a, ha, b, subset_gamma R B hb, hz⟩

/-- Closed Galois concepts generated by `(S, T, R)`. -/
@[ext]
structure ClosedConcept {S T : Type*} (R : S → T → Prop) where
  carrier : Set S
  closed : gamma R carrier = carrier

def cLe {S T : Type*} {R : S → T → Prop} (A B : ClosedConcept R) : Prop :=
  A.carrier ⊆ B.carrier

def cSup {S T : Type*} (R : S → T → Prop) (ℱ : Set (ClosedConcept R)) : ClosedConcept R where
  carrier := gamma R (⋃ A ∈ ℱ, A.carrier)
  closed := gamma_idem R _

def cMul {S T : Type*} [Monoid S] {R : S → T → Prop}
    (A B : ClosedConcept R) : ClosedConcept R where
  carrier := gamma R (setMul A.carrier B.carrier)
  closed := gamma_idem R _

def cOne {S T : Type*} [Monoid S] (R : S → T → Prop) : ClosedConcept R where
  carrier := gamma R {1}
  closed := gamma_idem R _

def resRight {S T : Type*} [Monoid S] (R : S → T → Prop) (hRes : IsResiduatedRel R)
    (A B : ClosedConcept R) : ClosedConcept R where
  carrier := {x | ∀ a ∈ A.carrier, a * x ∈ B.carrier}
  closed := by
    apply Set.Subset.antisymm
    · intro x hx a ha
      rw [← B.closed]
      intro t ht
      have hSub : {y | ∀ a' ∈ A.carrier, a' * y ∈ B.carrier} ⊆ {y | R (a * y) t} :=
        fun y hy => by
          have hyB : a * y ∈ gamma R B.carrier := B.closed.symm ▸ hy a ha
          exact hyB t ht
      have hx' := gamma_mono R hSub hx
      rw [hRes.2 a t] at hx'
      exact hx'
    · exact subset_gamma R _

def resLeft {S T : Type*} [Monoid S] (R : S → T → Prop) (hRes : IsResiduatedRel R)
    (B C : ClosedConcept R) : ClosedConcept R where
  carrier := {x | ∀ b ∈ B.carrier, x * b ∈ C.carrier}
  closed := by
    apply Set.Subset.antisymm
    · intro x hx b hb
      rw [← C.closed]
      intro t ht
      have hSub : {y | ∀ b' ∈ B.carrier, y * b' ∈ C.carrier} ⊆ {y | R (y * b) t} :=
        fun y hy => by
          have hyC : y * b ∈ gamma R C.carrier := C.closed.symm ▸ hy b hb
          exact hyC t ht
      have hx' := gamma_mono R hSub hx
      rw [hRes.1 b t] at hx'
      exact hx'
    · exact subset_gamma R _

theorem cMul_assoc {S T : Type*} [Monoid S] (R : S → T → Prop) (hRes : IsResiduatedRel R)
    (A B C : ClosedConcept R) : cMul (cMul A B) C = cMul A (cMul B C) := by
  ext s
  dsimp [cMul]
  rw [gamma_setMul_left R hRes, gamma_setMul_right R hRes]
  have hEq : setMul (setMul A.carrier B.carrier) C.carrier =
      setMul A.carrier (setMul B.carrier C.carrier) := by
    ext z
    constructor
    · rintro ⟨_, ⟨a, ha, b, hb, rfl⟩, c, hc, rfl⟩
      exact ⟨a, ha, b * c, ⟨b, hb, c, hc, rfl⟩, mul_assoc a b c⟩
    · rintro ⟨a, ha, _, ⟨b, hb, c, hc, rfl⟩, rfl⟩
      exact ⟨a * b, ⟨a, ha, b, hb, rfl⟩, c, hc, (mul_assoc a b c).symm⟩
  rw [hEq]

theorem cMul_one {S T : Type*} [Monoid S] (R : S → T → Prop) (hRes : IsResiduatedRel R)
    (A : ClosedConcept R) : cMul A (cOne R) = A := by
  ext s
  dsimp [cMul, cOne]
  rw [gamma_setMul_right R hRes]
  have hEq : setMul A.carrier ({1} : Set S) = A.carrier := by
    ext z
    constructor
    · rintro ⟨a, ha, _, rfl, rfl⟩
      simpa using ha
    · intro hz
      exact ⟨z, hz, 1, rfl, (mul_one z).symm⟩
  rw [hEq, A.closed]

theorem one_cMul {S T : Type*} [Monoid S] (R : S → T → Prop) (hRes : IsResiduatedRel R)
    (A : ClosedConcept R) : cMul (cOne R) A = A := by
  ext s
  dsimp [cMul, cOne]
  rw [gamma_setMul_left R hRes]
  have hEq : setMul ({1} : Set S) A.carrier = A.carrier := by
    ext z
    constructor
    · rintro ⟨_, rfl, a, ha, rfl⟩
      simpa using ha
    · intro hz
      exact ⟨1, rfl, z, hz, (one_mul z).symm⟩
  rw [hEq, A.closed]

theorem cMul_sSup_left {S T : Type*} [Monoid S] (R : S → T → Prop) (hRes : IsResiduatedRel R)
    (ℱ : Set (ClosedConcept R)) (B : ClosedConcept R) :
    cMul (cSup R ℱ) B = cSup R {C | ∃ A ∈ ℱ, C = cMul A B} := by
  apply ClosedConcept.ext
  dsimp [cMul, cSup]
  rw [gamma_setMul_left R hRes]
  apply Set.Subset.antisymm
  · apply gamma_mono R
    rintro z ⟨_, haU, b, hb, rfl⟩
    rcases Set.mem_iUnion₂.mp haU with ⟨A, hA, ha⟩
    rw [Set.mem_iUnion₂]
    exact ⟨cMul A B, ⟨A, hA, rfl⟩, subset_gamma R _ ⟨_, ha, b, hb, rfl⟩⟩
  · rw [← gamma_idem R (setMul (⋃ A ∈ ℱ, A.carrier) B.carrier)]
    apply gamma_mono R
    intro z hz
    rcases Set.mem_iUnion₂.mp hz with ⟨C, ⟨A, hA, rfl⟩, hzC⟩
    apply gamma_mono R _ hzC
    rintro w ⟨a, ha, b, hb, rfl⟩
    exact ⟨a, Set.mem_iUnion₂.mpr ⟨A, hA, ha⟩, b, hb, rfl⟩

theorem cMul_sSup_right {S T : Type*} [Monoid S] (R : S → T → Prop) (hRes : IsResiduatedRel R)
    (A : ClosedConcept R) (ℱ : Set (ClosedConcept R)) :
    cMul A (cSup R ℱ) = cSup R {C | ∃ B ∈ ℱ, C = cMul A B} := by
  apply ClosedConcept.ext
  dsimp [cMul, cSup]
  rw [gamma_setMul_right R hRes]
  apply Set.Subset.antisymm
  · apply gamma_mono R
    rintro z ⟨a, ha, _, hbU, rfl⟩
    rcases Set.mem_iUnion₂.mp hbU with ⟨B, hB, hb⟩
    rw [Set.mem_iUnion₂]
    exact ⟨cMul A B, ⟨B, hB, rfl⟩, subset_gamma R _ ⟨a, ha, _, hb, rfl⟩⟩
  · rw [← gamma_idem R (setMul A.carrier (⋃ B ∈ ℱ, B.carrier))]
    apply gamma_mono R
    intro z hz
    rcases Set.mem_iUnion₂.mp hz with ⟨C, ⟨B, hB, rfl⟩, hzC⟩
    apply gamma_mono R _ hzC
    rintro w ⟨a, ha, b, hb, rfl⟩
    exact ⟨a, ha, b, Set.mem_iUnion₂.mpr ⟨B, hB, hb⟩, rfl⟩

theorem cMul_le_iff_le_resRight {S T : Type*} [Monoid S] (R : S → T → Prop)
    (hRes : IsResiduatedRel R) (A B C : ClosedConcept R) :
    cLe (cMul A B) C ↔ cLe B (resRight R hRes A C) := by
  constructor
  · intro h b hb a ha
    exact h (subset_gamma R _ ⟨a, ha, b, hb, rfl⟩)
  · intro h
    show gamma R (setMul A.carrier B.carrier) ⊆ C.carrier
    rw [← C.closed]
    apply gamma_mono R
    rintro _ ⟨a, ha, b, hb, rfl⟩
    exact h hb a ha

theorem cMul_le_iff_le_resLeft {S T : Type*} [Monoid S] (R : S → T → Prop)
    (hRes : IsResiduatedRel R) (A B C : ClosedConcept R) :
    cLe (cMul A B) C ↔ cLe A (resLeft R hRes B C) := by
  constructor
  · intro h a ha b hb
    exact h (subset_gamma R _ ⟨a, ha, b, hb, rfl⟩)
  · intro h
    show gamma R (setMul A.carrier B.carrier) ⊆ C.carrier
    rw [← C.closed]
    apply gamma_mono R
    rintro _ ⟨a, ha, b, hb, rfl⟩
    exact h ha b hb

end ConceptQuantale

/-! ## 5. Group-Algebra Frobenius Monoid Laws & Homomorphic Unitary `U(d)` OOD Invariance -/
namespace FrobeniusAndHomomorphicU

section GroupFrobenius

/-- Convolution multiplication on the group algebra `G → R`. -/
def frobMul {G : Type*} [Group G] [Fintype G] {R : Type*} [CommRing R] (f h : G → R) (x : G) : R :=
  ∑ a : G, f a * h (a⁻¹ * x)

/-- Convolution unit. -/
def frobUnit {G : Type*} [One G] [DecidableEq G] {R : Type*} [Zero R] [One R] : G → R :=
  fun x => if x = 1 then 1 else 0

/-- Dual Frobenius comultiplication `Δ(f)(x, y) = f(x * y)`. -/
def frobComul {G : Type*} [Mul G] {R : Type*} (f : G → R) (p : G × G) : R :=
  f (p.1 * p.2)

/-- Frobenius counit `ε(f) = f(1)`. -/
def frobCounit {G : Type*} [One G] {R : Type*} (f : G → R) : R :=
  f 1

/-- Left action `(μ ⊗ id)(f ⊗ g)` on `G × G → R`. -/
def mulLeftTensor {G : Type*} [Group G] [Fintype G] {R : Type*} [CommRing R]
    (f : G → R) (g : G × G → R) (p : G × G) : R :=
  ∑ a : G, f a * g (a⁻¹ * p.1, p.2)

/-- Right action `(id ⊗ μ)(g ⊗ h)` on `G × G → R`. -/
def mulRightTensor {G : Type*} [Group G] [Fintype G] {R : Type*} [CommRing R]
    (g : G × G → R) (h : G → R) (p : G × G) : R :=
  ∑ b : G, g (p.1, b) * h (b⁻¹ * p.2)

/-- Multiplication contraction `μ : (G × G → R) → (G → R)`. -/
def contractMul {G : Type*} [Group G] [Fintype G] {R : Type*} [CommRing R]
    (g : G × G → R) (x : G) : R :=
  ∑ a : G, g (a, a⁻¹ * x)

theorem frobMul_assoc {G : Type*} [Group G] [Fintype G] {R : Type*} [CommRing R]
    (f h k : G → R) :
    frobMul (frobMul f h) k = frobMul f (frobMul h k) := by
  funext x
  dsimp [frobMul]
  calc ∑ a : G, (∑ b : G, f b * h (b⁻¹ * a)) * k (a⁻¹ * x)
      = ∑ a : G, ∑ b : G, f b * (h (b⁻¹ * a) * k (a⁻¹ * x)) := by
        refine Finset.sum_congr rfl fun a _ => ?_
        rw [Finset.sum_mul]
        refine Finset.sum_congr rfl fun b _ => mul_assoc _ _ _
    _ = ∑ b : G, ∑ a : G, f b * (h (b⁻¹ * a) * k (a⁻¹ * x)) := Finset.sum_comm
    _ = ∑ b : G, f b * ∑ c : G, h c * k (c⁻¹ * (b⁻¹ * x)) := by
        refine Finset.sum_congr rfl fun b _ => ?_
        rw [← Finset.mul_sum]
        congr 1
        refine Fintype.sum_equiv (Equiv.mulLeft b).symm _ _ fun a => ?_
        simp [mul_inv_rev, mul_assoc]

theorem frobMul_one {G : Type*} [Group G] [Fintype G] [DecidableEq G] {R : Type*} [CommRing R]
    (f : G → R) :
    frobMul f (frobUnit : G → R) = f := by
  funext x
  dsimp [frobMul, frobUnit]
  rw [Finset.sum_eq_single x]
  · simp
  · intro a _ hne
    have hinv : a⁻¹ * x ≠ 1 := by
      intro h1
      have := mul_left_cancel (a := a) (by simpa [mul_assoc] using congrArg (fun z => a * z) h1)
      exact hne this.symm
    simp [hinv]
  · intro hx
    exact absurd (Finset.mem_univ x) hx

theorem one_frobMul {G : Type*} [Group G] [Fintype G] [DecidableEq G] {R : Type*} [CommRing R]
    (f : G → R) :
    frobMul (frobUnit : G → R) f = f := by
  funext x
  dsimp [frobMul, frobUnit]
  rw [Finset.sum_eq_single (1 : G)]
  · simp
  · intro a _ hne
    simp [hne]
  · intro h1
    exact absurd (Finset.mem_univ (1 : G)) h1

theorem frobComul_coassoc {G : Type*} [Semigroup G] {R : Type*} (f : G → R) (x y z : G) :
    frobComul (fun u => frobComul f (u, z)) (x, y) =
      frobComul (fun u => frobComul f (x, u)) (y, z) := by
  dsimp [frobComul]
  rw [mul_assoc]

theorem frobCounit_left {G : Type*} [Monoid G] {R : Type*} (f : G → R) (y : G) :
    frobCounit (fun x => frobComul f (x, y)) = f y := by
  simp [frobCounit, frobComul]

theorem frobCounit_right {G : Type*} [Monoid G] {R : Type*} (f : G → R) (x : G) :
    frobCounit (fun y => frobComul f (x, y)) = f x := by
  simp [frobCounit, frobComul]

/-- Left Frobenius law: `Δ ∘ μ = (μ ⊗ id) ∘ (id ⊗ Δ)`. -/
theorem frob_law_left {G : Type*} [Group G] [Fintype G] {R : Type*} [CommRing R] (f h : G → R) :
    frobComul (frobMul f h) = mulLeftTensor f (frobComul h) := by
  funext ⟨x, y⟩
  dsimp [frobComul, frobMul, mulLeftTensor]
  refine Finset.sum_congr rfl fun a _ => ?_
  rw [mul_assoc]

/-- Right Frobenius law: `Δ ∘ μ = (id ⊗ μ) ∘ (Δ ⊗ id)`. -/
theorem frob_law_right {G : Type*} [Group G] [Fintype G] {R : Type*} [CommRing R] (f h : G → R) :
    frobComul (frobMul f h) = mulRightTensor (frobComul f) h := by
  funext ⟨x, y⟩
  dsimp [frobComul, frobMul, mulRightTensor]
  refine Fintype.sum_equiv (Equiv.mulLeft x⁻¹) _ _ fun a => ?_
  simp [mul_inv_rev, mul_assoc]

/-- Special Frobenius identity: `μ ∘ Δ = |G| · id`. -/
theorem frob_special {G : Type*} [Group G] [Fintype G] {R : Type*} [CommRing R] (f : G → R) :
    contractMul (frobComul f) = fun x => (Fintype.card G : R) * f x := by
  funext x
  simp [contractMul, frobComul, Finset.sum_const, Finset.card_univ, nsmul_eq_mul]

/-- Genuine non-commutativity witness of the `S₃` group-algebra Frobenius structure. -/
theorem s3_frob_noncommutative :
    let δ := fun (g x : Equiv.Perm (Fin 3)) => if x = g then (1 : ℤ) else 0
    let σ : Equiv.Perm (Fin 3) := Equiv.swap 0 1
    let τ : Equiv.Perm (Fin 3) := Equiv.swap 1 2
    frobMul (δ σ) (δ τ) ≠ frobMul (δ τ) (δ σ) := by
  dsimp
  intro h
  have hval := congr_fun h (Equiv.swap 0 1 * Equiv.swap 1 2)
  revert hval
  decide

end GroupFrobenius

section HomomorphicU

variable {G : Type*} [Group G] {d : ℕ}

/-- Matrix product evaluation of any variable-length word `w : List G` under `ρ : G →* U(d)`. -/
noncomputable def evalWord (ρ : G →* Matrix.unitaryGroup (Fin d) ℂ) (w : List G) :
    Matrix (Fin d) (Fin d) ℂ :=
  (w.map (fun g => (ρ g : Matrix (Fin d) (Fin d) ℂ))).prod

/-- Exact homomorphism composition law: `evalWord ρ w` collapses any word `w` of ANY length `L`
    to the single unitary group evaluation `ρ w.prod`. -/
theorem homomorphism_word_eval (ρ : G →* Matrix.unitaryGroup (Fin d) ℂ) (w : List G) :
    evalWord ρ w = (ρ w.prod : Matrix (Fin d) (Fin d) ℂ) := by
  induction w with
  | nil => simp [evalWord]
  | cons g gs ih =>
      simp only [evalWord, List.map_cons, List.prod_cons] at ih ⊢
      rw [ih, map_mul]
      rfl

/-- Unitary gauge conjugation of a representation `ρ` by `U : U(d)`. -/
noncomputable def conjUnitaryRep (U : Matrix.unitaryGroup (Fin d) ℂ)
    (ρ : G →* Matrix.unitaryGroup (Fin d) ℂ) : G →* Matrix.unitaryGroup (Fin d) ℂ where
  toFun g := U * ρ g * U⁻¹
  map_one' := by simp
  map_mul' a b := by
    calc U * ρ (a * b) * U⁻¹ = U * (ρ a * ρ b) * U⁻¹ := by rw [map_mul]
      _ = (U * ρ a * U⁻¹) * (U * ρ b * U⁻¹) := by group

private lemma trace_unitary_conj {d : ℕ} (A : Matrix.unitaryGroup (Fin d) ℂ)
    (M : Matrix (Fin d) (Fin d) ℂ) :
    Matrix.trace ((A : Matrix (Fin d) (Fin d) ℂ) * M * (A⁻¹ : Matrix.unitaryGroup (Fin d) ℂ).1) =
      Matrix.trace M := by
  rw [Matrix.trace_mul_comm, ← Matrix.mul_assoc]
  have hinv : (A⁻¹ : Matrix.unitaryGroup (Fin d) ℂ).1 * (A : Matrix (Fin d) (Fin d) ℂ) = 1 :=
    congr_arg Subtype.val (inv_mul_cancel A)
  rw [hinv, Matrix.one_mul]

/-- OOD length + gauge + conjugacy invariance: under a true group homomorphism `ρ : G →* U(d)`,
    word evaluation traces depend ONLY on the conjugacy class of `w.prod`, completely invariant
    to word length `L` and global unitary frame `U`. -/
theorem homomorphism_trace_conjugacy_length_invariant
    (ρ : G →* Matrix.unitaryGroup (Fin d) ℂ) (U : Matrix.unitaryGroup (Fin d) ℂ)
    (w₁ w₂ : List G) (k : G) (hconj : w₂.prod = k * w₁.prod * k⁻¹) :
    Matrix.trace (evalWord (conjUnitaryRep U ρ) w₂) = Matrix.trace (evalWord ρ w₁) := by
  rw [homomorphism_word_eval, homomorphism_word_eval, hconj]
  have hg : conjUnitaryRep U ρ (k * w₁.prod * k⁻¹) =
      (U * ρ k) * ρ w₁.prod * (U * ρ k)⁻¹ := by
    simp only [conjUnitaryRep, MonoidHom.coe_mk, OneHom.coe_mk, map_mul, map_inv]
    group
  rw [hg]
  exact trace_unitary_conj (U * ρ k) (ρ w₁.prod : Matrix (Fin d) (Fin d) ℂ)

/-- Bouquet OOD invariance: for ANY `b₁ = 2` two-loop words `(w₁, w₂)` vs `(v₁, v₂)` of ANY
    loop lengths, joint traces `Tr(evalWord ρ w₁ * evalWord ρ w₂)` are strictly invariant under
    global unitary gauge `U` and simultaneous conjugacy `(k w₁ k⁻¹, k w₂ k⁻¹)`. -/
theorem homomorphism_bouquet_joint_trace_gauge_invariant
    (ρ : G →* Matrix.unitaryGroup (Fin d) ℂ) (U : Matrix.unitaryGroup (Fin d) ℂ)
    (w₁ w₂ v₁ v₂ : List G) (k : G)
    (h1 : v₁.prod = k * w₁.prod * k⁻¹) (h2 : v₂.prod = k * w₂.prod * k⁻¹) :
    Matrix.trace (evalWord (conjUnitaryRep U ρ) v₁ * evalWord (conjUnitaryRep U ρ) v₂) =
      Matrix.trace (evalWord ρ w₁ * evalWord ρ w₂) := by
  rw [homomorphism_word_eval, homomorphism_word_eval,
      homomorphism_word_eval, homomorphism_word_eval, h1, h2]
  have hg :
      conjUnitaryRep U ρ (k * w₁.prod * k⁻¹) * conjUnitaryRep U ρ (k * w₂.prod * k⁻¹) =
        (U * ρ k) * (ρ w₁.prod * ρ w₂.prod) * (U * ρ k)⁻¹ := by
    simp only [conjUnitaryRep, MonoidHom.coe_mk, OneHom.coe_mk, map_mul, map_inv]
    group
  have hm := congr_arg Subtype.val hg
  change (conjUnitaryRep U ρ (k * w₁.prod * k⁻¹) : Matrix (Fin d) (Fin d) ℂ) *
      (conjUnitaryRep U ρ (k * w₂.prod * k⁻¹) : Matrix (Fin d) (Fin d) ℂ) =
      ((U * ρ k : Matrix.unitaryGroup (Fin d) ℂ) : Matrix (Fin d) (Fin d) ℂ) *
        ((ρ w₁.prod : Matrix (Fin d) (Fin d) ℂ) * (ρ w₂.prod : Matrix (Fin d) (Fin d) ℂ)) *
        ((U * ρ k)⁻¹ : Matrix.unitaryGroup (Fin d) ℂ).1 at hm
  rw [hm]
  exact trace_unitary_conj (U * ρ k) _

end HomomorphicU

end FrobeniusAndHomomorphicU

end Semplex.GHSRT
