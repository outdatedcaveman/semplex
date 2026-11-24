{-# OPTIONS --cubical=full #-}
module Semplex.Cubical.SimplicialKanNerve where

open import Agda.Primitive
open import Agda.Primitive.Cubical
open import Agda.Builtin.Cubical.Path
open import Semplex.Cubical.Primitives
open import Semplex.Cubical.BGClassifyingSpace
open import Semplex.Cubical.HomotopyProfileFiber

-- =============================================================================
-- 1. Empty, Unit, and Negation Primitives (Zero Stdlib Dependencies)
-- =============================================================================

data ⊥ : Set where

¬_ : {ℓ : Level} → Set ℓ → Set ℓ
¬ A = A → ⊥

record ⊤ : Set where
  constructor tt

-- =============================================================================
-- 2. 2-Truncated Simplicial Sets, Inner/Outer Horns, and Kan Condition
-- =============================================================================

record Simplicial2 : Set₁ where
  field
    Obj : Set
    Hom : Obj → Obj → Set
    Tri : {x y z : Obj} → Hom x y → Hom y z → Hom x z → Set

-- Inner horn Λ²₁: given 0→1 (f) and 1→2 (g), fill 0→2 (h) and 2-simplex.
HasInnerHorn2 : Simplicial2 → Set
HasInnerHorn2 S =
  ∀ {x y z : Simplicial2.Obj S} →
  (f : Simplicial2.Hom S x y) →
  (g : Simplicial2.Hom S y z) →
  Σ (Simplicial2.Hom S x z) (λ h → Simplicial2.Tri S f g h)

-- Left outer horn Λ²₀: given 0→1 (f) and 0→2 (h), fill 1→2 (g) and 2-simplex.
HasOuterHorn2Left : Simplicial2 → Set
HasOuterHorn2Left S =
  ∀ {x y z : Simplicial2.Obj S} →
  (f : Simplicial2.Hom S x y) →
  (h : Simplicial2.Hom S x z) →
  Σ (Simplicial2.Hom S y z) (λ g → Simplicial2.Tri S f g h)

-- Right outer horn Λ²₂: given 1→2 (g) and 0→2 (h), fill 0→1 (f) and 2-simplex.
HasOuterHorn2Right : Simplicial2 → Set
HasOuterHorn2Right S =
  ∀ {x y z : Simplicial2.Obj S} →
  (g : Simplicial2.Hom S y z) →
  (h : Simplicial2.Hom S x z) →
  Σ (Simplicial2.Hom S x y) (λ f → Simplicial2.Tri S f g h)

IsKan2 : Simplicial2 → Set
IsKan2 S = Σ (HasInnerHorn2 S) (λ _ → Σ (HasOuterHorn2Left S) (λ _ → HasOuterHorn2Right S))

-- =============================================================================
-- 3. Path Algebra & Type Path Nerve (BG G Is a 2-Kan Complex)
-- =============================================================================

rUnitFill : {ℓ : Level} {A : Set ℓ} {x y : A} (p : x ≡ y) (k i : I) → A
rUnitFill {x = x} {y = y} p k i =
  primHComp
    (λ j → λ
      { (i = i0) → x
      ; (i = i1) → y
      ; (k = i1) → p i
      })
    (p i)

rUnit : {ℓ : Level} {A : Set ℓ} {x y : A} (p : x ≡ y) → p ∙ refl ≡ p
rUnit p k i = rUnitFill p k i

lUnit : {ℓ : Level} {A : Set ℓ} {x y : A} (p : x ≡ y) → refl ∙ p ≡ p
lUnit {x = x} p = J (λ z q → refl ∙ q ≡ q) (rUnit (refl {x = x})) p

cancelLeft : {ℓ : Level} {A : Set ℓ} {x y z : A}
  (f : x ≡ y) (h : x ≡ z) → f ∙ (sym f ∙ h) ≡ h
cancelLeft {x = x} {z = z} f h =
  J (λ y' f' → (h' : x ≡ z) → f' ∙ (sym f' ∙ h') ≡ h')
    (λ h' → (λ i → refl ∙ lUnit h' i) ∙ lUnit h')
    f h

cancelRight : {ℓ : Level} {A : Set ℓ} {x y z : A}
  (g : y ≡ z) (h : x ≡ z) → (h ∙ sym g) ∙ g ≡ h
cancelRight {x = x} {y = y} g h =
  J (λ z' g' → (h' : x ≡ z') → (h' ∙ sym g') ∙ g' ≡ h')
    (λ h' → (λ i → rUnit h' i ∙ refl) ∙ rUnit h')
    g h

typePathNerve : Set → Simplicial2
typePathNerve A = record
  { Obj = A
  ; Hom = λ x y → x ≡ y
  ; Tri = λ f g h → f ∙ g ≡ h
  }

typePathNerve-innerHorn : (A : Set) → HasInnerHorn2 (typePathNerve A)
typePathNerve-innerHorn A f g = (f ∙ g) , refl

typePathNerve-outerHornLeft : (A : Set) → HasOuterHorn2Left (typePathNerve A)
typePathNerve-outerHornLeft A f h = (sym f ∙ h) , cancelLeft f h

typePathNerve-outerHornRight : (A : Set) → HasOuterHorn2Right (typePathNerve A)
typePathNerve-outerHornRight A g h = (h ∙ sym g) , cancelRight g h

typePathNerve-isKan2 : (A : Set) → IsKan2 (typePathNerve A)
typePathNerve-isKan2 A =
  typePathNerve-innerHorn A ,
  (typePathNerve-outerHornLeft A , typePathNerve-outerHornRight A)

BG-isKan2 : (G : SetGroup) → IsKan2 (typePathNerve (BG G))
BG-isKan2 G = typePathNerve-isKan2 (BG G)

-- =============================================================================
-- 4. Set-Level Monoid Nerves (Quasi-Category Inner Horn)
-- =============================================================================

record SetMonoid : Set₁ where
  field
    Carrier : Set
    isSet-Carrier : isSet Carrier
    e : Carrier
    mul : Carrier → Carrier → Carrier
    assoc : (a b c : Carrier) → mul (mul a b) c ≡ mul a (mul b c)
    unit-left : (a : Carrier) → mul e a ≡ a
    unit-right : (a : Carrier) → mul a e ≡ a

monoidNerve : SetMonoid → Simplicial2
monoidNerve M = record
  { Obj = ⊤
  ; Hom = λ _ _ → SetMonoid.Carrier M
  ; Tri = λ a b c → SetMonoid.mul M a b ≡ c
  }

monoidNerve-innerHorn : (M : SetMonoid) → HasInnerHorn2 (monoidNerve M)
monoidNerve-innerHorn M f g = SetMonoid.mul M f g , refl

-- =============================================================================
-- 5. Non-Invertible Flip-Flop Reset Monoid U₂: Λ²₁ Fills, Λ²₀/Λ²₂ Refuted
-- =============================================================================

data U2Elem : Set where
  u2Id u2R0 u2R1 : U2Elem

u2Mul : U2Elem → U2Elem → U2Elem
u2Mul u2Id y = y
u2Mul u2R0 _ = u2R0
u2Mul u2R1 _ = u2R1

u2Assoc : (a b c : U2Elem) → u2Mul (u2Mul a b) c ≡ u2Mul a (u2Mul b c)
u2Assoc u2Id b c = refl
u2Assoc u2R0 b c = refl
u2Assoc u2R1 b c = refl

u2UnitLeft : (a : U2Elem) → u2Mul u2Id a ≡ a
u2UnitLeft _ = refl

u2UnitRight : (a : U2Elem) → u2Mul a u2Id ≡ a
u2UnitRight u2Id = refl
u2UnitRight u2R0 = refl
u2UnitRight u2R1 = refl

U2Code : U2Elem → U2Elem → Set
U2Code u2Id u2Id = ⊤
U2Code u2R0 u2R0 = ⊤
U2Code u2R1 u2R1 = ⊤
U2Code _    _    = ⊥

u2CodeRefl : (x : U2Elem) → U2Code x x
u2CodeRefl u2Id = tt
u2CodeRefl u2R0 = tt
u2CodeRefl u2R1 = tt

u2Encode : {x y : U2Elem} → x ≡ y → U2Code x y
u2Encode {x} p = subst (U2Code x) p (u2CodeRefl x)

u2Decode : {x y : U2Elem} → U2Code x y → x ≡ y
u2Decode {u2Id} {u2Id} _ = refl
u2Decode {u2R0} {u2R0} _ = refl
u2Decode {u2R1} {u2R1} _ = refl
u2Decode {u2Id} {u2R0} ()
u2Decode {u2Id} {u2R1} ()
u2Decode {u2R0} {u2Id} ()
u2Decode {u2R0} {u2R1} ()
u2Decode {u2R1} {u2Id} ()
u2Decode {u2R1} {u2R0} ()

u2Code-isProp : {x y : U2Elem} (c d : U2Code x y) → c ≡ d
u2Code-isProp {u2Id} {u2Id} tt tt = refl
u2Code-isProp {u2R0} {u2R0} tt tt = refl
u2Code-isProp {u2R1} {u2R1} tt tt = refl
u2Code-isProp {u2Id} {u2R0} () _
u2Code-isProp {u2Id} {u2R1} () _
u2Code-isProp {u2R0} {u2Id} () _
u2Code-isProp {u2R0} {u2R1} () _
u2Code-isProp {u2R1} {u2Id} () _
u2Code-isProp {u2R1} {u2R0} () _

transpRefl : {ℓ : Level} {A : Set ℓ} (a : A) → primTransp (λ _ → A) i0 a ≡ a
transpRefl {A = A} a i = primTransp (λ _ → A) i a

u2EncodeRefl : (x : U2Elem) → u2Decode (u2Encode (refl {x = x})) ≡ refl {x = x}
u2EncodeRefl u2Id = cong u2Decode (transpRefl tt)
u2EncodeRefl u2R0 = cong u2Decode (transpRefl tt)
u2EncodeRefl u2R1 = cong u2Decode (transpRefl tt)

u2DecodeEncode : {x y : U2Elem} (p : x ≡ y) → u2Decode (u2Encode p) ≡ p
u2DecodeEncode p = J (λ _ q → u2Decode (u2Encode q) ≡ q) (u2EncodeRefl _) p

isSet-U2Elem : isSet U2Elem
isSet-U2Elem x y p q =
  sym (u2DecodeEncode p) ∙ cong u2Decode (u2Code-isProp (u2Encode p) (u2Encode q)) ∙ u2DecodeEncode q

u2R0≢u2Id : u2R0 ≡ u2Id → ⊥
u2R0≢u2Id p = u2Encode p

u2R1≢u2Id : u2R1 ≡ u2Id → ⊥
u2R1≢u2Id p = u2Encode p

U2Monoid : SetMonoid
U2Monoid = record
  { Carrier = U2Elem
  ; isSet-Carrier = isSet-U2Elem
  ; e = u2Id
  ; mul = u2Mul
  ; assoc = u2Assoc
  ; unit-left = u2UnitLeft
  ; unit-right = u2UnitRight
  }

U2-nerve-fills-innerHorn : HasInnerHorn2 (monoidNerve U2Monoid)
U2-nerve-fills-innerHorn = monoidNerve-innerHorn U2Monoid

-- Outer horn Λ²₀ fails for f = u2R0, h = u2Id because u2Mul u2R0 g = u2R0 ≠ u2Id.
U2-nerve-refutes-outerHornLeft : ¬ HasOuterHorn2Left (monoidNerve U2Monoid)
U2-nerve-refutes-outerHornLeft horn =
  u2R0≢u2Id (snd (horn {tt} {tt} {tt} u2R0 u2Id))

-- Outer horn Λ²₂ fails for g = u2R0, h = u2Id because u2Mul f u2R0 ∈ {u2R0, u2R1}.
U2-nerve-refutes-outerHornRight : ¬ HasOuterHorn2Right (monoidNerve U2Monoid)
U2-nerve-refutes-outerHornRight horn with horn {tt} {tt} {tt} u2R0 u2Id
... | u2Id , eq = u2R0≢u2Id eq
... | u2R0 , eq = u2R0≢u2Id eq
... | u2R1 , eq = u2R1≢u2Id eq

U2-nerve-not-Kan2 : ¬ IsKan2 (monoidNerve U2Monoid)
U2-nerve-not-Kan2 (_ , (outerL , _)) = U2-nerve-refutes-outerHornLeft outerL

-- =============================================================================
-- 6. Simplicial Profile Presheaf Transport & Contractible Homotopy Fibers
-- =============================================================================

record NerveProfile (S : Simplicial2) : Set₁ where
  field
    Val : Simplicial2.Obj S → Set
    act : {x y : Simplicial2.Obj S} → Simplicial2.Hom S x y → Val x → Val y

transportHalfAdjointEquiv : {A : Set} (P : A → Set) {x y : A} (p : x ≡ y) →
  HalfAdjointEquiv (P x) (P y)
transportHalfAdjointEquiv P {x = x} p =
  J (λ z _ → HalfAdjointEquiv (P x) (P z)) (idEquiv (P x)) p

pathNerveProfile : {A : Set} (P : A → Set) → NerveProfile (typePathNerve A)
pathNerveProfile P = record
  { Val = P
  ; act = λ p v → HalfAdjointEquiv.to (transportHalfAdjointEquiv P p) v
  }

nerve-profile-equiv-contr-fiber :
  (A : Set) (P : A → Set) {x y : A} (p : x ≡ y) (v : P y) →
  isContr (fiber (NerveProfile.act (pathNerveProfile P) p) v)
nerve-profile-equiv-contr-fiber A P p v =
  halfAdjointEquiv→isContrFiber (transportHalfAdjointEquiv P p) v

BG-profile-transport-contr-fiber :
  (G : SetGroup) (P : BG G → Set) {x y : BG G} (p : x ≡ y) (v : P y) →
  isContr (fiber (NerveProfile.act (pathNerveProfile P) p) v)
BG-profile-transport-contr-fiber G P p v =
  nerve-profile-equiv-contr-fiber (BG G) P p v
