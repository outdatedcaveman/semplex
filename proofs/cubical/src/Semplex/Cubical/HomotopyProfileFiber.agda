{-# OPTIONS --cubical=full #-}
module Semplex.Cubical.HomotopyProfileFiber where

open import Agda.Primitive
open import Agda.Primitive.Cubical
open import Agda.Builtin.Cubical.Path
open import Semplex.Cubical.Primitives
open import Semplex.Cubical.BGClassifyingSpace

record Σ {ℓ₁ ℓ₂ : Level} (A : Set ℓ₁) (B : A → Set ℓ₂) : Set (ℓ₁ ⊔ ℓ₂) where
  constructor _,_
  field
    fst : A
    snd : B fst

open Σ public

sym : {ℓ : Level} {A : Set ℓ} {x y : A} → x ≡ y → y ≡ x
sym p i = p (primINeg i)

cong : {ℓ₁ ℓ₂ : Level} {A : Set ℓ₁} {B : Set ℓ₂} (f : A → B) {x y : A} →
  x ≡ y → f x ≡ f y
cong f p i = f (p i)

subst : {ℓ₁ ℓ₂ : Level} {A : Set ℓ₁} (P : A → Set ℓ₂) {x y : A} →
  x ≡ y → P x → P y
subst P p px = primTransp (λ i → P (p i)) i0 px

J : {ℓ₁ ℓ₂ : Level} {A : Set ℓ₁} {x : A}
  (P : (y : A) → x ≡ y → Set ℓ₂) →
  P x refl →
  {y : A} (p : x ≡ y) → P y p
J P d p = primTransp (λ i → P (p i) (λ j → p (primIMin i j))) i0 d

funExt : {ℓ₁ ℓ₂ : Level} {A : Set ℓ₁} {B : A → Set ℓ₂} {f g : (x : A) → B x} →
  ((x : A) → f x ≡ g x) → f ≡ g
funExt h i x = h x i

SigmaPathP : {ℓ₁ ℓ₂ : Level} {A : Set ℓ₁} {B : A → Set ℓ₂} {u v : Σ A B} →
  (p : fst u ≡ fst v) →
  PathP (λ i → B (p i)) (snd u) (snd v) →
  u ≡ v
SigmaPathP p q i = p i , q i

isContr : {ℓ : Level} → Set ℓ → Set ℓ
isContr A = Σ A (λ c → (x : A) → c ≡ x)

fiber : {ℓ₁ ℓ₂ : Level} {A : Set ℓ₁} {B : Set ℓ₂} (f : A → B) (y : B) → Set (ℓ₁ ⊔ ℓ₂)
fiber {A = A} f y = Σ A (λ x → f x ≡ y)

record Equiv {ℓ₁ ℓ₂ : Level} (A : Set ℓ₁) (B : Set ℓ₂) : Set (ℓ₁ ⊔ ℓ₂) where
  field
    to : A → B
    from : B → A
    sec : (b : B) → to (from b) ≡ b
    ret : (a : A) → from (to a) ≡ a

record HalfAdjointEquiv {ℓ₁ ℓ₂ : Level} (A : Set ℓ₁) (B : Set ℓ₂) : Set (ℓ₁ ⊔ ℓ₂) where
  field
    to : A → B
    from : B → A
    sec : (b : B) → to (from b) ≡ b
    ret : (a : A) → from (to a) ≡ a
    coh : (a : A) → PathP (λ i → to (ret a i) ≡ to a) (sec (to a)) refl

iso-fiber-inhabited : {ℓ₁ ℓ₂ : Level} {A : Set ℓ₁} {B : Set ℓ₂} →
  (e : Equiv A B) (y : B) → fiber (Equiv.to e) y
iso-fiber-inhabited e y = Equiv.from e y , Equiv.sec e y

halfAdjointEquiv→isContrFiber : {ℓ₁ ℓ₂ : Level} {A : Set ℓ₁} {B : Set ℓ₂} →
  (e : HalfAdjointEquiv A B) (y : B) → isContr (fiber (HalfAdjointEquiv.to e) y)
halfAdjointEquiv→isContrFiber e y =
  (from y , sec y) , λ { (x , p) → J (λ z q → (from z , sec z) ≡ (x , q)) (basePath x) p }
  where
  to = HalfAdjointEquiv.to e
  from = HalfAdjointEquiv.from e
  sec = HalfAdjointEquiv.sec e
  ret = HalfAdjointEquiv.ret e
  coh = HalfAdjointEquiv.coh e

  basePath : (x : _) → (from (to x) , sec (to x)) ≡ (x , refl)
  basePath x = SigmaPathP (ret x) (coh x)

idEquiv : {ℓ : Level} (A : Set ℓ) → HalfAdjointEquiv A A
idEquiv A = record
  { to = λ x → x
  ; from = λ x → x
  ; sec = λ _ → refl
  ; ret = λ _ → refl
  ; coh = λ _ _ → refl
  }

id-equiv-isContrFiber : {ℓ : Level} {A : Set ℓ} (y : A) →
  isContr (fiber (λ (x : A) → x) y)
id-equiv-isContrFiber {A = A} y = halfAdjointEquiv→isContrFiber (idEquiv A) y

BG-identity-moduli-contractible : (G : SetGroup) (y : BG G) →
  isContr (fiber (λ (x : BG G) → x) y)
BG-identity-moduli-contractible G y = halfAdjointEquiv→isContrFiber (idEquiv (BG G)) y
