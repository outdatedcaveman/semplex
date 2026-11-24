{-# OPTIONS --cubical=full #-}
module Semplex.Cubical.HigherHornCoherence where

open import Agda.Primitive
open import Agda.Primitive.Cubical
open import Agda.Builtin.Cubical.Path
open import Semplex.Cubical.Primitives
open import Semplex.Cubical.BGClassifyingSpace
open import Semplex.Cubical.HomotopyProfileFiber
open import Semplex.Cubical.SimplicialKanNerve

-- =============================================================================
-- 1. Higher Path Algebra & Cancellation Coherence
-- =============================================================================

assoc : {ℓ : Level} {A : Set ℓ} {w x y z : A}
  (p : w ≡ x) (q : x ≡ y) (r : y ≡ z) → (p ∙ q) ∙ r ≡ p ∙ (q ∙ r)
assoc {w = w} {y = y} {z = z} p q r =
  J (λ x' p' → (q' : x' ≡ y) (r' : y ≡ z) → (p' ∙ q') ∙ r' ≡ p' ∙ (q' ∙ r'))
    (λ q' r' → (λ i → lUnit q' i ∙ r') ∙ sym (lUnit (q' ∙ r')))
    p q r

whiskerLeftFill : {ℓ : Level} {A : Set ℓ} {w x y : A}
  (f : w ≡ x) {u v : x ≡ y} (h : f ∙ u ≡ f ∙ v) → u ≡ v
whiskerLeftFill {w = w} {y = y} f {u} {v} h =
  J (λ x' f' → (u' v' : x' ≡ y) → (f' ∙ u' ≡ f' ∙ v') → u' ≡ v')
    (λ u' v' q → sym (lUnit u') ∙ q ∙ lUnit v')
    f u v h

whiskerRightFill : {ℓ : Level} {A : Set ℓ} {x y z : A}
  (g : y ≡ z) {u v : x ≡ y} (h : u ∙ g ≡ v ∙ g) → u ≡ v
whiskerRightFill {x = x} {y = y} g {u} {v} h =
  J (λ z' g' → (u' v' : x ≡ y) → (u' ∙ g' ≡ v' ∙ g') → u' ≡ v')
    (λ u' v' q → sym (rUnit u') ∙ q ∙ rUnit v')
    g u v h

cong-∙ : {ℓ₁ ℓ₂ : Level} {A : Set ℓ₁} {B : Set ℓ₂} (f : A → B) {x y z : A}
  (p : x ≡ y) (q : y ≡ z) → cong f (p ∙ q) ≡ cong f p ∙ cong f q
cong-∙ f {x = x} {y = y} p q =
  J (λ z' q' → cong f (p ∙ q') ≡ cong f p ∙ cong f q')
    (cong (cong f) (rUnit p) ∙ sym (rUnit (cong f p)))
    q

-- =============================================================================
-- 2. 3-Truncated Simplicial Sets, 3-Horns (Λ³₁, Λ³₂, Λ³₀, Λ³₃), and 3-Kan
-- =============================================================================

record Simplicial3 : Set₁ where
  field
    Base : Simplicial2
    Tet : {w x y z : Simplicial2.Obj Base}
      {f01 : Simplicial2.Hom Base w x}
      {f12 : Simplicial2.Hom Base x y}
      {f23 : Simplicial2.Hom Base y z}
      {f02 : Simplicial2.Hom Base w y}
      {f13 : Simplicial2.Hom Base x z}
      {f03 : Simplicial2.Hom Base w z} →
      Simplicial2.Tri Base f12 f23 f13 →
      Simplicial2.Tri Base f02 f23 f03 →
      Simplicial2.Tri Base f01 f13 f03 →
      Simplicial2.Tri Base f01 f12 f02 →
      Set

HasInnerHorn31 : Simplicial3 → Set
HasInnerHorn31 S =
  let B = Simplicial3.Base S in
  ∀ {w x y z : Simplicial2.Obj B}
    {f01 : Simplicial2.Hom B w x}
    {f12 : Simplicial2.Hom B x y}
    {f23 : Simplicial2.Hom B y z}
    {f02 : Simplicial2.Hom B w y}
    {f13 : Simplicial2.Hom B x z}
    {f03 : Simplicial2.Hom B w z}
    (face0 : Simplicial2.Tri B f12 f23 f13)
    (face2 : Simplicial2.Tri B f01 f13 f03)
    (face3 : Simplicial2.Tri B f01 f12 f02) →
  Σ (Simplicial2.Tri B f02 f23 f03) (λ face1 → Simplicial3.Tet S face0 face1 face2 face3)

HasInnerHorn32 : Simplicial3 → Set
HasInnerHorn32 S =
  let B = Simplicial3.Base S in
  ∀ {w x y z : Simplicial2.Obj B}
    {f01 : Simplicial2.Hom B w x}
    {f12 : Simplicial2.Hom B x y}
    {f23 : Simplicial2.Hom B y z}
    {f02 : Simplicial2.Hom B w y}
    {f13 : Simplicial2.Hom B x z}
    {f03 : Simplicial2.Hom B w z}
    (face0 : Simplicial2.Tri B f12 f23 f13)
    (face1 : Simplicial2.Tri B f02 f23 f03)
    (face3 : Simplicial2.Tri B f01 f12 f02) →
  Σ (Simplicial2.Tri B f01 f13 f03) (λ face2 → Simplicial3.Tet S face0 face1 face2 face3)

HasOuterHorn30 : Simplicial3 → Set
HasOuterHorn30 S =
  let B = Simplicial3.Base S in
  ∀ {w x y z : Simplicial2.Obj B}
    {f01 : Simplicial2.Hom B w x}
    {f12 : Simplicial2.Hom B x y}
    {f23 : Simplicial2.Hom B y z}
    {f02 : Simplicial2.Hom B w y}
    {f13 : Simplicial2.Hom B x z}
    {f03 : Simplicial2.Hom B w z}
    (face1 : Simplicial2.Tri B f02 f23 f03)
    (face2 : Simplicial2.Tri B f01 f13 f03)
    (face3 : Simplicial2.Tri B f01 f12 f02) →
  Σ (Simplicial2.Tri B f12 f23 f13) (λ face0 → Simplicial3.Tet S face0 face1 face2 face3)

HasOuterHorn33 : Simplicial3 → Set
HasOuterHorn33 S =
  let B = Simplicial3.Base S in
  ∀ {w x y z : Simplicial2.Obj B}
    {f01 : Simplicial2.Hom B w x}
    {f12 : Simplicial2.Hom B x y}
    {f23 : Simplicial2.Hom B y z}
    {f02 : Simplicial2.Hom B w y}
    {f13 : Simplicial2.Hom B x z}
    {f03 : Simplicial2.Hom B w z}
    (face0 : Simplicial2.Tri B f12 f23 f13)
    (face1 : Simplicial2.Tri B f02 f23 f03)
    (face2 : Simplicial2.Tri B f01 f13 f03) →
  Σ (Simplicial2.Tri B f01 f12 f02) (λ face3 → Simplicial3.Tet S face0 face1 face2 face3)

IsKan3 : Simplicial3 → Set
IsKan3 S =
  Σ (IsKan2 (Simplicial3.Base S)) (λ _ →
  Σ (HasInnerHorn31 S) (λ _ →
  Σ (HasInnerHorn32 S) (λ _ →
  Σ (HasOuterHorn30 S) (λ _ → HasOuterHorn33 S))))

-- =============================================================================
-- 3. Type Path 3-Nerve: Arbitrary Type Inner 3-Horns & BG G Is 3-Kan
-- =============================================================================

typePathNerve3 : Set → Simplicial3
typePathNerve3 A = record
  { Base = typePathNerve A
  ; Tet = λ {w} {x} {y} {z} {f01} {f12} {f23} {f02} {f13} {f03} face0 face1 face2 face3 →
      ((λ i → face3 i ∙ f23) ∙ face1) ≡ (assoc f01 f12 f23 ∙ ((λ i → f01 ∙ face0 i) ∙ face2))
  }

typePathNerve3-innerHorn1 : (A : Set) → HasInnerHorn31 (typePathNerve3 A)
typePathNerve3-innerHorn1 A {f01 = f01} {f12} {f23} face0 face2 face3 =
  face1 , cancelLeft leftPrefix targetPath
  where
  leftPrefix = λ i → face3 i ∙ f23
  targetPath = assoc f01 f12 f23 ∙ ((λ i → f01 ∙ face0 i) ∙ face2)
  face1 = sym leftPrefix ∙ targetPath

typePathNerve3-innerHorn2 : (A : Set) → HasInnerHorn32 (typePathNerve3 A)
typePathNerve3-innerHorn2 A {f01 = f01} {f12} {f23} face0 face1 face3 =
  face2 , (sym (cancelLeft P L) ∙ assoc (assoc f01 f12 f23) (λ i → f01 ∙ face0 i) face2)
  where
  L = (λ i → face3 i ∙ f23) ∙ face1
  P = assoc f01 f12 f23 ∙ (λ i → f01 ∙ face0 i)
  face2 = sym P ∙ L

groupoidPathNerve3-outerHorn0 : (A : Set) → isGroupoid A → HasOuterHorn30 (typePathNerve3 A)
groupoidPathNerve3-outerHorn0 A isGrp {w} {z = z} {f01} {f12} {f23} face1 face2 face3 =
  face0 , isGrp w z _ _ _ _
  where
  h = sym (assoc f01 f12 f23) ∙ ((λ i → face3 i ∙ f23) ∙ face1) ∙ sym face2
  face0 = whiskerLeftFill f01 h

groupoidPathNerve3-outerHorn3 : (A : Set) → isGroupoid A → HasOuterHorn33 (typePathNerve3 A)
groupoidPathNerve3-outerHorn3 A isGrp {w} {z = z} {f01} {f12} {f23} face0 face1 face2 =
  face3 , isGrp w z _ _ _ _
  where
  h = (assoc f01 f12 f23 ∙ ((λ i → f01 ∙ face0 i) ∙ face2)) ∙ sym face1
  face3 = whiskerRightFill f23 h

BG-isKan3 : (G : SetGroup) → IsKan3 (typePathNerve3 (BG G))
BG-isKan3 G =
  BG-isKan2 G ,
  (typePathNerve3-innerHorn1 (BG G) ,
  (typePathNerve3-innerHorn2 (BG G) ,
  (groupoidPathNerve3-outerHorn0 (BG G) (BG-isGroupoid G) ,
   groupoidPathNerve3-outerHorn3 (BG G) (BG-isGroupoid G))))

-- =============================================================================
-- 4. Set-Monoid 3-Nerve & U₂ Inner-3-Horn / Outer-3-Horn Separation
-- =============================================================================

monoidNerve3 : SetMonoid → Simplicial3
monoidNerve3 M = record
  { Base = monoidNerve M
  ; Tet = λ {f01 = f01} {f12} {f23} face0 face1 face2 face3 →
      (cong (λ u → SetMonoid.mul M u f23) face3 ∙ face1) ≡
        (SetMonoid.assoc M f01 f12 f23 ∙ cong (SetMonoid.mul M f01) face0 ∙ face2)
  }

monoidNerve3-innerHorn1 : (M : SetMonoid) → HasInnerHorn31 (monoidNerve3 M)
monoidNerve3-innerHorn1 M {f01 = f01} {f12} {f23} face0 face2 face3 =
  face1 , SetMonoid.isSet-Carrier M _ _ _ _
  where
  face1 =
    cong (λ u → SetMonoid.mul M u f23) (sym face3) ∙
      SetMonoid.assoc M f01 f12 f23 ∙
      cong (SetMonoid.mul M f01) face0 ∙
      face2

monoidNerve3-innerHorn2 : (M : SetMonoid) → HasInnerHorn32 (monoidNerve3 M)
monoidNerve3-innerHorn2 M {f01 = f01} {f12} {f23} face0 face1 face3 =
  face2 , SetMonoid.isSet-Carrier M _ _ _ _
  where
  face2 =
    cong (SetMonoid.mul M f01) (sym face0) ∙
      sym (SetMonoid.assoc M f01 f12 f23) ∙
      cong (λ u → SetMonoid.mul M u f23) face3 ∙
      face1

U2-nerve3-fills-innerHorns :
  Σ (HasInnerHorn31 (monoidNerve3 U2Monoid))
    (λ _ → HasInnerHorn32 (monoidNerve3 U2Monoid))
U2-nerve3-fills-innerHorns =
  monoidNerve3-innerHorn1 U2Monoid , monoidNerve3-innerHorn2 U2Monoid

U2-nerve3-refutes-outerHorn0 : ¬ HasOuterHorn30 (monoidNerve3 U2Monoid)
U2-nerve3-refutes-outerHorn0 horn =
  u2R0≢u2Id (fst (horn {tt} {tt} {tt} {tt} {u2R0} {u2R0} {u2R0} {u2R0} {u2Id} {u2R0} refl refl refl))

-- =============================================================================
-- 5. Simplicial Representation Maps & Naturality of Profile Transport
-- =============================================================================

record Simplicial2Map (S T : Simplicial2) : Set where
  field
    mapObj : Simplicial2.Obj S → Simplicial2.Obj T
    mapHom : {x y : Simplicial2.Obj S} →
      Simplicial2.Hom S x y → Simplicial2.Hom T (mapObj x) (mapObj y)
    mapTri : {x y z : Simplicial2.Obj S}
      {f : Simplicial2.Hom S x y} {g : Simplicial2.Hom S y z} {h : Simplicial2.Hom S x z} →
      Simplicial2.Tri S f g h →
      Simplicial2.Tri T (mapHom f) (mapHom g) (mapHom h)

typePathNerveMap : {A B : Set} (fn : A → B) →
  Simplicial2Map (typePathNerve A) (typePathNerve B)
typePathNerveMap fn = record
  { mapObj = fn
  ; mapHom = λ p → cong fn p
  ; mapTri = λ {f = p} {g = q} eq → sym (cong-∙ fn p q) ∙ cong (cong fn) eq
  }

private
  transportHalfAdjointEquivRefl : {A : Set} (P : A → Set) (x : A) →
    transportHalfAdjointEquiv P (refl {x = x}) ≡ idEquiv (P x)
  transportHalfAdjointEquivRefl P x = transpRefl (idEquiv (P x))

profile-transport-natural : {A B : Set} (f : A → B) (Q : B → Set)
  {x y : A} (p : x ≡ y) (v : Q (f x)) →
  NerveProfile.act (pathNerveProfile (λ a → Q (f a))) p v ≡
    NerveProfile.act (pathNerveProfile Q) (cong f p) v
profile-transport-natural f Q {x = x} p v =
  J (λ y' p' →
      NerveProfile.act (pathNerveProfile (λ a → Q (f a))) p' v ≡
        NerveProfile.act (pathNerveProfile Q) (cong f p') v)
    baseCase p
  where
  baseCase :
    NerveProfile.act (pathNerveProfile (λ a → Q (f a))) (refl {x = x}) v ≡
      NerveProfile.act (pathNerveProfile Q) (refl {x = f x}) v
  baseCase =
    cong (λ e → HalfAdjointEquiv.to e v) (transportHalfAdjointEquivRefl (λ a → Q (f a)) x) ∙
      sym (cong (λ e → HalfAdjointEquiv.to e v) (transportHalfAdjointEquivRefl Q (f x)))

BG-repMap-preserves-contr-fiber :
  (G H : SetGroup) (f : BG G → BG H) (Q : BG H → Set)
  {x y : BG G} (p : x ≡ y) (v : Q (f y)) →
  isContr (fiber (NerveProfile.act (pathNerveProfile (λ a → Q (f a))) p) v)
BG-repMap-preserves-contr-fiber G H f Q p v =
  BG-profile-transport-contr-fiber G (λ a → Q (f a)) p v
