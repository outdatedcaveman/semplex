{-# OPTIONS --cubical=full #-}
module Semplex.Cubical.S1 where

open import Semplex.Cubical.Primitives

data S1 : Set where
  base : S1
  loop : Path {A = S1} base base

loopAtBase : Path {A = S1} base base
loopAtBase = loop
