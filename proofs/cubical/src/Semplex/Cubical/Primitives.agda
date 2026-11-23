{-# OPTIONS --cubical=full #-}
module Semplex.Cubical.Primitives where

open import Agda.Primitive
open import Agda.Primitive.Cubical
open import Agda.Builtin.Cubical.Path

refl : {ℓ : Level} {A : Set ℓ} {x : A} -> x ≡ x
refl {x = x} i = x

doubleCompFaces : {ℓ : Level} {A : Set ℓ} {x y z w : A} ->
  (p : x ≡ y) -> (r : z ≡ w) -> (i j : I) -> Partial (primIMax i (primINeg i)) A
doubleCompFaces p r i j (i = i0) = p (primINeg j)
doubleCompFaces p r i j (i = i1) = r j

infixr 30 _∙_
_∙_ : {ℓ : Level} {A : Set ℓ} {x y z : A} -> x ≡ y -> y ≡ z -> x ≡ z
p ∙ q = (refl ∙∙ p ∙∙ q)
  where
  _∙∙_∙∙_ : {ℓ : Level} {A : Set ℓ} {x y z w : A} ->
    x ≡ y -> y ≡ z -> z ≡ w -> x ≡ w
  (p ∙∙ q ∙∙ r) i = primHComp (doubleCompFaces p r i) (q i)

Path : {ℓ : Level} {A : Set ℓ} -> A -> A -> Set ℓ
Path = _≡_
