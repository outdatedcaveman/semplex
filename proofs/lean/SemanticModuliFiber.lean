import HigherSemanticCore

/-!
# Moduli fibers of fully faithful groupoid representations

A point of the fiber over h is a source object x together with an
isomorphism F(x) ≅ h. Fiber arrows are source isomorphisms commuting with
these comparisons. An equivalence of groupoids has contractible fibers:
the fiber is inhabited, and between any two of its points there is exactly
one compatible arrow.

This is the strict 1-groupoid prototype of the higher moduli-space
reconstruction statement.
-/

namespace Cerp.SemanticModuliFiber

open Cerp.HigherSemanticCore

universe u v

variable {G H : Groupoid}

structure FiberPoint (F : GroupoidFunctor G H) (h : H.Obj) where
  source : G.Obj
  comparison : H.Hom (F.obj source) h

def FiberArrow (F : GroupoidFunctor G H) (h : H.Obj)
    (a b : FiberPoint F h) :=
  { f : G.Hom a.source b.source //
      H.comp (F.map f) b.comparison = a.comparison }

/-- A compatible arrow exists between any two points in the fiber. -/
theorem fiberArrow_nonempty (E : GroupoidEquivalence G H) (h : H.Obj)
    (a b : FiberPoint E.functor h) :
    Nonempty (FiberArrow E.functor h a b) := by
  let k : H.Hom (E.functor.obj a.source) (E.functor.obj b.source) :=
    H.comp a.comparison (H.inv b.comparison)
  let f : G.Hom a.source b.source :=
    (E.homEquiv a.source b.source).invFun k
  have hf : E.functor.map f = k := by
    calc
      E.functor.map f =
          (E.homEquiv a.source b.source).toFun f :=
        (E.homEquiv_map f).symm
      _ = k := (E.homEquiv a.source b.source).right_inv k
  have hcomm :
      H.comp (E.functor.map f) b.comparison = a.comparison := by
    rw [hf]
    calc
      H.comp (H.comp a.comparison (H.inv b.comparison)) b.comparison =
          H.comp a.comparison
            (H.comp (H.inv b.comparison) b.comparison) :=
        H.assoc _ _ _
      _ = H.comp a.comparison (H.id h) := by rw [H.inv_left]
      _ = a.comparison := H.comp_id _
  exact ⟨⟨f, hcomm⟩⟩

/-- The compatible arrow is unique when the functor is fully faithful. -/
theorem fiberArrow_unique (E : GroupoidEquivalence G H) (h : H.Obj)
    (a b : FiberPoint E.functor h)
    (f g : FiberArrow E.functor h a b) :
    f = g := by
  apply Subtype.ext
  have hf : E.functor.map f.1 =
      H.comp a.comparison (H.inv b.comparison) := by
    calc
      E.functor.map f.1 =
          H.comp (E.functor.map f.1) (H.id (E.functor.obj b.source)) := by
            exact (H.comp_id (E.functor.map f.1)).symm
      _ = H.comp (E.functor.map f.1)
          (H.comp b.comparison (H.inv b.comparison)) := by
            rw [H.inv_right]
      _ = H.comp (H.comp (E.functor.map f.1) b.comparison)
          (H.inv b.comparison) := (H.assoc _ _ _).symm
      _ = H.comp a.comparison (H.inv b.comparison) := by
            rw [f.2]
  have hg : E.functor.map g.1 =
      H.comp a.comparison (H.inv b.comparison) := by
    calc
      E.functor.map g.1 =
          H.comp (E.functor.map g.1) (H.id (E.functor.obj b.source)) := by
            exact (H.comp_id (E.functor.map g.1)).symm
      _ = H.comp (E.functor.map g.1)
          (H.comp b.comparison (H.inv b.comparison)) := by
            rw [H.inv_right]
      _ = H.comp (H.comp (E.functor.map g.1) b.comparison)
          (H.inv b.comparison) := (H.assoc _ _ _).symm
      _ = H.comp a.comparison (H.inv b.comparison) := by
            rw [g.2]
  have hmap : E.functor.map f.1 = E.functor.map g.1 := hf.trans hg.symm
  calc
    f.1 = (E.homEquiv a.source b.source).invFun
        ((E.homEquiv a.source b.source).toFun f.1) :=
          (E.homEquiv a.source b.source).left_inv f.1 |>.symm
    _ = (E.homEquiv a.source b.source).invFun
        ((E.homEquiv a.source b.source).toFun g.1) :=
          congrArg (E.homEquiv a.source b.source).invFun
            (by rw [E.homEquiv_map, E.homEquiv_map]; exact hmap)
    _ = g.1 := (E.homEquiv a.source b.source).left_inv g.1

/-- Every target object has at least one point in the fiber when the functor
    is essentially surjective. -/
theorem fiberPoint_nonempty (E : GroupoidEquivalence G H) (h : H.Obj) :
    Nonempty (FiberPoint E.functor h) := by
  obtain ⟨x, ⟨f⟩⟩ := E.essentiallySurjective h
  exact ⟨⟨x, f⟩⟩

/-- Contractibility of the homotopy fiber, expressed as nonempty objects and
    singleton compatible-arrow types. -/
def FiberContractible (E : GroupoidEquivalence G H) (h : H.Obj) : Prop :=
  And (Nonempty (FiberPoint E.functor h))
    (forall a b : FiberPoint E.functor h,
      And (Nonempty (FiberArrow E.functor h a b))
        (Subsingleton (FiberArrow E.functor h a b)))

theorem equivalence_has_contractible_fibers
    (E : GroupoidEquivalence G H) (h : H.Obj) :
    FiberContractible E h := by
  constructor
  · exact fiberPoint_nonempty E h
  · intro a b
    constructor
    · exact fiberArrow_nonempty E h a b
    · constructor
      intro f g
      exact fiberArrow_unique E h a b f g

end Cerp.SemanticModuliFiber
