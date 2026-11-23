import Lean

/-!
Resource-relative probe presheaves.

A costed category carries a natural-number cost on arrows, zero-cost
identities, and subadditive composition. The zero-cost arrows are the
free refinements. For each target X and budget B, affordable arrows
P -> X form a presheaf over the free-refinement subcategory.

This module is compiled and axiom-audited as part of the unified Lake project.
-/

namespace Cerp.ResourceRelativeProbes

/-- A small category equipped with a natural-number cost on arrows. -/
structure CostedCategory where
  Obj : Type
  Hom : Obj → Obj → Type
  id : (X : Obj) → Hom X X
  comp : {A B C : Obj} → Hom B C → Hom A B → Hom A C
  id_comp : ∀ {A B : Obj} (f : Hom A B), comp (id B) f = f
  comp_id : ∀ {A B : Obj} (f : Hom A B), comp f (id A) = f
  assoc : ∀ {A B C D : Obj}
    (h : Hom C D) (g : Hom B C) (f : Hom A B),
    comp h (comp g f) = comp (comp h g) f
  cost : ∀ {A B : Obj}, Hom A B → Nat
  cost_id : ∀ (X : Obj), cost (id X) = 0
  cost_comp : ∀ {A B C : Obj} (g : Hom B C) (f : Hom A B),
    cost (comp g f) ≤ cost g + cost f

/-- A probe arrow is affordable at budget B. -/
def Affordable (C : CostedCategory) (B : Nat) (X P : C.Obj) :=
  { f : C.Hom P X // C.cost f ≤ B }

/-- Every zero-cost arrow is a free refinement. -/
def Free {C : CostedCategory} {A B : C.Obj} (u : C.Hom A B) : Prop :=
  C.cost u = 0

/-- Zero-cost arrows are closed under composition. -/
theorem free_comp {C : CostedCategory} {A B D : C.Obj}
    (g : C.Hom B D) (f : C.Hom A B)
    (hg : Free g) (hf : Free f) :
    Free (C.comp g f) := by
  unfold Free
  have h := C.cost_comp g f
  rw [hg, hf] at h
  exact Nat.eq_zero_of_le_zero h

/-- Precomposition by a free refinement preserves affordability. -/
def precompose {C : CostedCategory} {B : Nat} {P Q X : C.Obj}
    (u : C.Hom Q P) (hu : Free u)
    (f : Affordable C B X P) : Affordable C B X Q :=
  ⟨C.comp f.1 u, by
    calc
      C.cost (C.comp f.1 u) ≤ C.cost f.1 + C.cost u :=
        C.cost_comp f.1 u
      _ = C.cost f.1 := by simp [Free] at hu; simp [hu]
      _ ≤ B := f.2
  ⟩

/-- The identity refinement acts as the identity on affordable probes. -/
theorem precompose_id {C : CostedCategory} {B : Nat} {P X : C.Obj}
    (f : Affordable C B X P) :
    precompose (C := C) (B := B) (C.id P) (by simp [Free, C.cost_id]) f = f := by
  apply Subtype.ext
  exact C.comp_id f.1

/-- Precomposition actions compose, so affordable probes form a presheaf
    over the zero-cost/free subcategory. -/
theorem precompose_comp {C : CostedCategory} {B : Nat}
    {P Q R X : C.Obj}
    (u : C.Hom Q P) (v : C.Hom R Q)
    (hu : Free u) (hv : Free v)
    (f : Affordable C B X P) :
    precompose (C := C) (B := B) (C.comp u v) (free_comp u v hu hv) f
      =
    precompose (C := C) (B := B) v hv
      (precompose (C := C) (B := B) u hu f) := by
  apply Subtype.ext
  exact C.assoc f.1 u v

/-- Postcomposition by an arrow of cost K shifts the probe budget by K. -/
def postcompose {C : CostedCategory} {B : Nat} {P X Y : C.Obj}
    (h : C.Hom X Y) (f : Affordable C B X P) :
    Affordable C (C.cost h + B) Y P :=
  ⟨C.comp h f.1, by
    calc
      C.cost (C.comp h f.1) ≤ C.cost h + C.cost f.1 :=
        C.cost_comp h f.1
      _ ≤ C.cost h + B := Nat.add_le_add_left f.2 _
  ⟩

/-- Grade-shifted postcomposition is natural under free precomposition. -/
theorem postcompose_natural {C : CostedCategory} {B : Nat}
    {P Q X Y : C.Obj}
    (h : C.Hom X Y) (u : C.Hom Q P) (hu : Free u)
    (f : Affordable C B X P) :
    precompose (C := C) (B := C.cost h + B) u hu
      (postcompose (C := C) (B := B) h f)
      =
    postcompose (C := C) (B := B) h
      (precompose (C := C) (B := B) u hu f) := by
  apply Subtype.ext
  exact (C.assoc h f.1 u).symm

/-- If the target transformation is free, postcomposition preserves the
    original budget rather than shifting it. -/
def postcompose_free {C : CostedCategory} {B : Nat} {P X Y : C.Obj}
    (h : C.Hom X Y) (hh : Free h)
    (f : Affordable C B X P) : Affordable C B Y P :=
  ⟨C.comp h f.1, by
    calc
      C.cost (C.comp h f.1) ≤ C.cost h + C.cost f.1 :=
        C.cost_comp h f.1
      _ = C.cost f.1 := by simp [Free] at hh; simp [hh]
      _ ≤ B := f.2
  ⟩

/-- Free postcomposition is the zero-grade case of the general grade shift. -/
theorem postcompose_free_natural {C : CostedCategory} {B : Nat}
    {P Q X Y : C.Obj}
    (h : C.Hom X Y) (hh : Free h)
    (u : C.Hom Q P) (hu : Free u)
    (f : Affordable C B X P) :
    precompose (C := C) (B := B) u hu
      (postcompose_free (C := C) (B := B) h hh f)
      =
    postcompose_free (C := C) (B := B) h hh
      (precompose (C := C) (B := B) u hu f) := by
  apply Subtype.ext
  exact (C.assoc h f.1 u).symm

end Cerp.ResourceRelativeProbes
