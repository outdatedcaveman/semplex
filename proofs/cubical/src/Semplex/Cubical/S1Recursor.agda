{-# OPTIONS --cubical=full #-}
module Semplex.Cubical.S1Recursor where

open import Agda.Primitive
open import Semplex.Cubical.Primitives
open import Semplex.Cubical.S1

record CircleAlgebra : Set₁ where
  field
    Carrier : Set
    point : Carrier
    loopPath : Path {A = Carrier} point point

open CircleAlgebra

s1Rec : (A : CircleAlgebra) -> S1 -> Carrier A
s1Rec A base = point A
s1Rec A (loop i) = loopPath A i

open import Agda.Primitive.Cubical

s1Rec-base-computation : (A : CircleAlgebra) -> Path {A = Carrier A} (s1Rec A base) (point A)
s1Rec-base-computation A = refl

s1Rec-loop-computation : (A : CircleAlgebra) -> (i : I) ->
  Path {A = Carrier A} (s1Rec A (loop i)) (loopPath A i)
s1Rec-loop-computation A i = refl

open import Agda.Builtin.Cubical.Path

s1Elim : {ℓ : Level} (P : S1 -> Set ℓ) -> (p : P base) ->
  PathP (λ i -> P (loop i)) p p -> (x : S1) -> P x
s1Elim P p q base = p
s1Elim P p q (loop i) = q i

s1Elim-base-computation : {ℓ : Level} (P : S1 -> Set ℓ) (p : P base)
  (q : PathP (λ i -> P (loop i)) p p) -> Path {A = P base} (s1Elim P p q base) p
s1Elim-base-computation P p q = refl

s1Elim-loop-computation : {ℓ : Level} (P : S1 -> Set ℓ) (p : P base)
  (q : PathP (λ i -> P (loop i)) p p) (i : I) ->
  Path {A = P (loop i)} (s1Elim P p q (loop i)) (q i)
s1Elim-loop-computation P p q i = refl
