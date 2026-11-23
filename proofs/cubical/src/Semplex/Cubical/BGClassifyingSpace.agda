{-# OPTIONS --cubical=full #-}
module Semplex.Cubical.BGClassifyingSpace where

open import Agda.Primitive
open import Agda.Builtin.Cubical.Path
open import Semplex.Cubical.Primitives

isProp : {ℓ : Level} -> Set ℓ -> Set ℓ
isProp A = (x y : A) -> x ≡ y

isSet : {ℓ : Level} -> Set ℓ -> Set ℓ
isSet A = (x y : A) -> isProp (x ≡ y)

isGroupoid : {ℓ : Level} -> Set ℓ -> Set ℓ
isGroupoid A = (x y : A) -> isSet (x ≡ y)

{- A discrete group whose carrier is an h-set (0-truncated), required so
   the 1-truncated classifying space `BG G` avoids higher carrier coherence. -}
record SetGroup : Set₁ where
  field
    Carrier : Set
    isSet-Carrier : isSet Carrier
    e : Carrier
    mul : Carrier -> Carrier -> Carrier
    inv : Carrier -> Carrier
    assoc : (g h k : Carrier) -> mul (mul g h) k ≡ mul g (mul h k)
    unit-left : (g : Carrier) -> mul e g ≡ g
    unit-right : (g : Carrier) -> mul g e ≡ g
    inverse-left : (g : Carrier) -> mul (inv g) g ≡ e
    inverse-right : (g : Carrier) -> mul g (inv g) ≡ e

{- 1-truncated classifying space `BG` for a set-level group `G`. Adding the
   explicit groupoid-truncation constructor `trunc` collapses all 3-cells
   (such as Mac Lane associativity coherence cubes) automatically. -}
data BG (G : SetGroup) : Set where
  base : BG G
  loop : SetGroup.Carrier G -> base ≡ base
  unit-cell : loop (SetGroup.e G) ≡ refl
  multiplication-cell : (g h : SetGroup.Carrier G) ->
    loop (SetGroup.mul G g h) ≡ loop g ∙ loop h
  inverse-cell : (g : SetGroup.Carrier G) ->
    loop (SetGroup.inv G g) ∙ loop g ≡ refl
  trunc : (x y : BG G) -> (p q : x ≡ y) -> (r s : p ≡ q) -> r ≡ s

BG-isGroupoid : (G : SetGroup) -> isGroupoid (BG G)
BG-isGroupoid G = trunc

loop-assoc-coherence : (G : SetGroup) (g h k : SetGroup.Carrier G) ->
  (p q : loop {G} (SetGroup.mul G (SetGroup.mul G g h) k) ≡ (loop {G} g ∙ loop {G} h) ∙ loop {G} k) ->
  p ≡ q
loop-assoc-coherence G g h k p q =
  trunc (base {G}) (base {G})
    (loop {G} (SetGroup.mul G (SetGroup.mul G g h) k))
    ((loop {G} g ∙ loop {G} h) ∙ loop {G} k)
    p q
