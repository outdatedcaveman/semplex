{-# OPTIONS --cubical=full #-}
module Semplex.Cubical.BGroup2Skeleton where

open import Agda.Primitive
open import Agda.Builtin.Cubical.Path
open import Semplex.Cubical.Primitives

record Group : Set₁ where
  field
    Carrier : Set
    e : Carrier
    mul : Carrier -> Carrier -> Carrier
    inv : Carrier -> Carrier
    assoc : (g h k : Carrier) -> mul (mul g h) k ≡ mul g (mul h k)
    unit-left : (g : Carrier) -> mul e g ≡ g
    unit-right : (g : Carrier) -> mul g e ≡ g
    inverse-left : (g : Carrier) -> mul (inv g) g ≡ e
    inverse-right : (g : Carrier) -> mul g (inv g) ≡ e

{- The 2-dimensional presentation skeleton of the classifying space of G.
   It has one point, one loop per group element, and 2-cells for unit,
   multiplication, and inverse relations. Higher coherence cells are
   intentionally not claimed here. -} 
data BGroup2Skeleton (G : Group) : Set where
  base : BGroup2Skeleton G
  loop : Group.Carrier G -> base ≡ base
  unit-cell : loop (Group.e G) ≡ refl
  multiplication-cell : (g h : Group.Carrier G) ->
    loop (Group.mul G g h) ≡ loop g ∙ loop h
  inverse-cell : (g : Group.Carrier G) ->
    loop (Group.inv G g) ∙ loop g ≡ refl
