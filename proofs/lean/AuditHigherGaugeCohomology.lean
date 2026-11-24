import Lean

/-!
Finite cochain model for the tetrahedral 2-sphere with Z₂ coefficients.

C⁰ --d₀--> C¹ --d₁--> C².
The file proves d₁ ∘ d₀ = 0 and invariance of total surface holonomy
under 1-form gauge transformations. It is deliberately core-Lean only:
no Mathlib, axioms, sorry, or external dependencies.
-/

namespace Cerp.HigherGaugeCohomology

/-- Addition in the field with two elements, represented by Bool. -/
def bxor : Bool → Bool → Bool
  | false, b => b
  | true, false => true
  | true, true => false

@[simp] theorem bxor_false_left (b : Bool) : bxor false b = b := by
  cases b <;> rfl

@[simp] theorem bxor_false_right (a : Bool) : bxor a false = a := by
  cases a <;> rfl

@[simp] theorem bxor_self (a : Bool) : bxor a a = false := by
  cases a <;> rfl

theorem bxor_assoc (a b c : Bool) :
    bxor (bxor a b) c = bxor a (bxor b c) := by
  cases a <;> cases b <;> cases c <;> rfl

theorem bxor_comm (a b : Bool) : bxor a b = bxor b a := by
  cases a <;> cases b <;> rfl

/-- 0-cochains: vertex gauge parameters on the four tetrahedral vertices. -/
structure C0 where
  v0 : Bool
  v1 : Bool
  v2 : Bool
  v3 : Bool
deriving DecidableEq, Repr

/-- 1-cochains: edge gauge parameters on the six tetrahedral edges. -/
structure C1 where
  e01 : Bool
  e02 : Bool
  e03 : Bool
  e12 : Bool
  e13 : Bool
  e23 : Bool
deriving DecidableEq, Repr

/-- 2-cochains: 2-form fields on the four triangular faces. -/
structure C2 where
  f012 : Bool
  f013 : Bool
  f023 : Bool
  f123 : Bool
deriving DecidableEq, Repr

def zeroC2 : C2 := ⟨false, false, false, false⟩

/-- Coboundary d₀ : C⁰ → C¹. -/
def d0 (v : C0) : C1 :=
  ⟨bxor v.v0 v.v1,
   bxor v.v0 v.v2,
   bxor v.v0 v.v3,
   bxor v.v1 v.v2,
   bxor v.v1 v.v3,
   bxor v.v2 v.v3⟩

/-- Coboundary d₁ : C¹ → C², summing the three edges of each face. -/
def d1 (e : C1) : C2 :=
  ⟨bxor (bxor e.e01 e.e02) e.e12,
   bxor (bxor e.e01 e.e03) e.e13,
   bxor (bxor e.e02 e.e03) e.e23,
   bxor (bxor e.e12 e.e13) e.e23⟩

/-- Pointwise addition of 2-cochains. -/
def addC2 (a b : C2) : C2 :=
  ⟨bxor a.f012 b.f012,
   bxor a.f013 b.f013,
   bxor a.f023 b.f023,
   bxor a.f123 b.f123⟩

/-- The cochain identity d₁ ∘ d₀ = 0, checked for every vertex gauge. -/
theorem d1_d0_zero (v : C0) : d1 (d0 v) = zeroC2 := by
  cases v with
  | mk v0 v1 v2 v3 =>
    cases v0 <;> cases v1 <;> cases v2 <;> cases v3 <;> rfl

/-- Total Z₂ surface holonomy on the fundamental 2-cycle of S². -/
def surfaceHolonomy (b : C2) : Bool :=
  bxor (bxor b.f012 b.f013) (bxor b.f023 b.f123)

/-- Every exact 2-cochain has trivial total surface holonomy. -/
theorem surfaceHolonomy_d1_zero (e : C1) :
    surfaceHolonomy (d1 e) = false := by
  cases e with
  | mk e01 e02 e03 e12 e13 e23 =>
    cases e01 <;> cases e02 <;> cases e03 <;>
    cases e12 <;> cases e13 <;> cases e23 <;> rfl

/-- Surface holonomy is invariant under every 1-form gauge transformation. -/
theorem surfaceHolonomy_gauge_invariant (b : C2) (e : C1) :
    surfaceHolonomy (addC2 b (d1 e)) = surfaceHolonomy b := by
  cases b with
  | mk b012 b013 b023 b123 =>
    cases e with
    | mk e01 e02 e03 e12 e13 e23 =>
      cases b012 <;> cases b013 <;> cases b023 <;> cases b123 <;>
      cases e01 <;> cases e02 <;> cases e03 <;>
      cases e12 <;> cases e13 <;> cases e23 <;> rfl

/-- Zero 0-cochain and zero 1-cochain. -/
def zeroC0 : C0 := ⟨false, false, false, false⟩
def oneC0 : C0 := ⟨true, true, true, true⟩
def zeroC1 : C1 := ⟨false, false, false, false, false, false⟩

/-- The only vertex gauges with zero coboundary are the constant gauges. -/
theorem d0_kernel_iff_constants (v : C0) :
    d0 v = zeroC1 ↔ v = zeroC0 ∨ v = oneC0 := by
  cases v with
  | mk v0 v1 v2 v3 =>
    cases v0 <;> cases v1 <;> cases v2 <;> cases v3 <;>
    simp [d0, zeroC1, zeroC0, oneC0, bxor]

/-- Every closed 1-cochain on the tetrahedral sphere is exact. -/
theorem d1_kernel_is_d0_image (e : C1) (h : d1 e = zeroC2) :
    ∃ v : C0, d0 v = e := by
  cases e with
  | mk e01 e02 e03 e12 e13 e23 =>
    refine ⟨⟨false, e01, e02, e03⟩, ?_⟩
    cases e01 <;> cases e02 <;> cases e03 <;>
    cases e12 <;> cases e13 <;> cases e23 <;>
    simp_all [d1, zeroC2, d0, bxor]

/-- A canonical edge cochain whose coboundary is a given even face field. -/
def facePreimage (b : C2) : C1 :=
  ⟨b.f013, b.f023, false, b.f123, false, false⟩

/-- Every 2-cochain with trivial total surface holonomy is exact. -/
theorem d1_facePreimage (b : C2) (h : surfaceHolonomy b = false) :
    d1 (facePreimage b) = b := by
  cases b with
  | mk b012 b013 b023 b123 =>
    cases b012 <;> cases b013 <;> cases b023 <;> cases b123 <;>
    simp_all [surfaceHolonomy, facePreimage, d1, bxor]

/-- Exact 2-cochains are precisely those with trivial surface holonomy. -/
theorem surfaceHolonomy_zero_iff_exact (b : C2) :
    surfaceHolonomy b = false ↔ ∃ e : C1, d1 e = b := by
  constructor
  · intro h
    exact ⟨facePreimage b, d1_facePreimage b h⟩
  · rintro ⟨e, rfl⟩
    exact surfaceHolonomy_d1_zero e

end Cerp.HigherGaugeCohomology

#print axioms Cerp.HigherGaugeCohomology.d1_d0_zero
#print axioms Cerp.HigherGaugeCohomology.surfaceHolonomy_d1_zero
#print axioms Cerp.HigherGaugeCohomology.surfaceHolonomy_gauge_invariant
#print axioms Cerp.HigherGaugeCohomology.d0_kernel_iff_constants
#print axioms Cerp.HigherGaugeCohomology.d1_kernel_is_d0_image
#print axioms Cerp.HigherGaugeCohomology.d1_facePreimage
#print axioms Cerp.HigherGaugeCohomology.surfaceHolonomy_zero_iff_exact
