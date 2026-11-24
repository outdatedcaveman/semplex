{-# OPTIONS --cubical=full #-}
module Semplex.Cubical.FiberObstructionSequence where

open import Agda.Primitive
open import Agda.Primitive.Cubical
open import Agda.Builtin.Cubical.Path
open import Semplex.Cubical.Primitives
open import Semplex.Cubical.BGClassifyingSpace
open import Semplex.Cubical.HomotopyProfileFiber
open import Semplex.Cubical.SimplicialKanNerve
open import Semplex.Cubical.HigherHornCoherence

record SetGroupHom (G K : SetGroup) : Set where
  field
    fun : SetGroup.Carrier G → SetGroup.Carrier K
    pres-e : fun (SetGroup.e G) ≡ SetGroup.e K
    pres-mul : (x y : SetGroup.Carrier G) →
      fun (SetGroup.mul G x y) ≡ SetGroup.mul K (fun x) (fun y)
    pres-inv : (x : SetGroup.Carrier G) →
      fun (SetGroup.inv G x) ≡ SetGroup.inv K (fun x)

data Deloop (G : SetGroup) : Set where
  pt : Deloop G
  emloop : SetGroup.Carrier G → pt ≡ pt
  emcomp : (g h : SetGroup.Carrier G) →
    PathP (λ i → emloop g i ≡ pt) (emloop (SetGroup.mul G g h)) (emloop h)
  emsquash : (x y : Deloop G) → (p q : x ≡ y) → (r s : p ≡ q) → r ≡ s

fillSquareFromComp : {ℓ : Level} {A : Set ℓ} {x y z : A}
  {a : x ≡ y} {b : y ≡ z} {c : x ≡ z} →
  (a ∙ b) ≡ c → PathP (λ i → a i ≡ z) c b
fillSquareFromComp {A = A} {x = x} {y = y} {z = z} {a = a} {b = b} {c = c} q =
  J (λ y' a' → {b' : y' ≡ z} {c' : x ≡ z} → (a' ∙ b') ≡ c' → PathP (λ i → a' i ≡ z) c' b')
    (λ {b' = b'} {c' = c'} q' →
      J (λ z' b'' → {c'' : x ≡ z'} → (refl ∙ b'') ≡ c'' → c'' ≡ b'')
        (λ {c'' = c''} q'' → sym q'' ∙ lUnit (refl {x = x}))
        b' q')
    a q

fillCompFromSquare : {ℓ : Level} {A : Set ℓ} {x y z : A}
  {a : x ≡ y} {b : y ≡ z} {c : x ≡ z} →
  PathP (λ i → a i ≡ z) c b → (a ∙ b) ≡ c
fillCompFromSquare {A = A} {x = x} {z = z} {a = a} {b = b} {c = c} sq =
  J (λ y' a' → {b' : y' ≡ z} {c' : x ≡ z} → PathP (λ i → a' i ≡ z) c' b' → (a' ∙ b') ≡ c')
    (λ {b' = b'} {c' = c'} sq' → lUnit b' ∙ sym sq')
    a sq

emloop-mul : {G : SetGroup} (g h : SetGroup.Carrier G) →
  emloop {G = G} g ∙ emloop {G = G} h ≡ emloop {G = G} (SetGroup.mul G g h)
emloop-mul {G = G} g h = fillCompFromSquare (emcomp g h)

emloop-unit : {G : SetGroup} → emloop {G = G} (SetGroup.e G) ≡ refl
emloop-unit {G = G} = whiskerRightFill (emloop {G = G} (SetGroup.e G)) eq
  where
  eq : emloop {G = G} (SetGroup.e G) ∙ emloop {G = G} (SetGroup.e G) ≡
       refl ∙ emloop {G = G} (SetGroup.e G)
  eq = emloop-mul {G = G} (SetGroup.e G) (SetGroup.e G)
     ∙ cong (emloop {G = G}) (SetGroup.unit-left G (SetGroup.e G))
     ∙ sym (lUnit (emloop {G = G} (SetGroup.e G)))

Deloop→BG : (G : SetGroup) → Deloop G → BG G
Deloop→BG G pt = base
Deloop→BG G (emloop g i) = loop g i
Deloop→BG G (emcomp g h i j) =
  fillSquareFromComp (sym (multiplication-cell g h)) i j
Deloop→BG G (emsquash x y p q r s i j k) =
  trunc (Deloop→BG G x) (Deloop→BG G y)
    (λ i₁ → Deloop→BG G (p i₁)) (λ i₁ → Deloop→BG G (q i₁))
    (λ i₁ j₁ → Deloop→BG G (r i₁ j₁)) (λ i₁ j₁ → Deloop→BG G (s i₁ j₁))
    i j k

BHom : {G K : SetGroup} → SetGroupHom G K → Deloop G → Deloop K
BHom {G} {K} φ pt = pt
BHom {G} {K} φ (emloop g i) = emloop (SetGroupHom.fun φ g) i
BHom {G} {K} φ (emcomp g h i j) =
  primHComp
    (λ k → λ
      { (i = i0) → emloop (SetGroupHom.pres-mul φ g h (primINeg k)) j
      ; (i = i1) → emloop (SetGroupHom.fun φ h) j
      ; (j = i0) → emloop (SetGroupHom.fun φ g) i
      ; (j = i1) → pt
      })
    (emcomp (SetGroupHom.fun φ g) (SetGroupHom.fun φ h) i j)
BHom {G} {K} φ (emsquash x y p q r s i j k) =
  emsquash (BHom φ x) (BHom φ y)
    (λ i₁ → BHom φ (p i₁)) (λ i₁ → BHom φ (q i₁))
    (λ i₁ j₁ → BHom φ (r i₁ j₁))
    (λ i₁ j₁ → BHom φ (s i₁ j₁)) i j k

Fib : {G K : SetGroup} → SetGroupHom G K → Set
Fib {K = K} φ = fiber (BHom φ) (pt {G = K})

fibBase : {G K : SetGroup} (φ : SetGroupHom G K) → Fib φ
fibBase φ = pt , refl

connectingPoint : {G K : SetGroup} (φ : SetGroupHom G K) → SetGroup.Carrier K → Fib φ
connectingPoint φ k = pt , emloop k

kerLoop : {G K : SetGroup} (φ : SetGroupHom G K) (g : SetGroup.Carrier G) →
  SetGroupHom.fun φ g ≡ SetGroup.e K →
  fibBase φ ≡ fibBase φ
kerLoop {K = K} φ g hg =
  SigmaPathP (emloop g) (λ i j → sq j i)
  where
  sq : emloop {G = K} (SetGroupHom.fun φ g) ≡ refl
  sq = cong (emloop {G = K}) hg ∙ emloop-unit {G = K}

kerLoop-fst : {G K : SetGroup} (φ : SetGroupHom G K) (g : SetGroup.Carrier G)
  (hg : SetGroupHom.fun φ g ≡ SetGroup.e K) →
  cong fst (kerLoop φ g hg) ≡ emloop g
kerLoop-fst φ g hg = refl

connecting-coset-path : {G K : SetGroup} (φ : SetGroupHom G K)
  (g : SetGroup.Carrier G) (k₁ k₂ : SetGroup.Carrier K) →
  SetGroup.mul K (SetGroupHom.fun φ g) k₂ ≡ k₁ →
  connectingPoint φ k₁ ≡ connectingPoint φ k₂
connecting-coset-path {K = K} φ g k₁ k₂ h =
  SigmaPathP (emloop g)
    (subst (λ x → PathP (λ i → emloop (SetGroupHom.fun φ g) i ≡ pt) (emloop x) (emloop k₂))
      h (emcomp (SetGroupHom.fun φ g) k₂))

im-trivializes-connecting : {G K : SetGroup} (φ : SetGroupHom G K)
  (g : SetGroup.Carrier G) (k : SetGroup.Carrier K) →
  SetGroupHom.fun φ g ≡ k →
  fibBase φ ≡ connectingPoint φ k
im-trivializes-connecting {K = K} φ g k h =
  pUnit ∙ sym (connecting-coset-path φ g k (SetGroup.e K) hk)
  where
  pUnit : fibBase φ ≡ connectingPoint φ (SetGroup.e K)
  pUnit = SigmaPathP refl (sym (emloop-unit {G = K}))

  hk : SetGroup.mul K (SetGroupHom.fun φ g) (SetGroup.e K) ≡ k
  hk = SetGroup.unit-right K (SetGroupHom.fun φ g) ∙ h

private
  isProp-⊤ : isProp ⊤
  isProp-⊤ tt tt = refl

  isProp-⊥ : isProp ⊥
  isProp-⊥ ()

  data C2 : Set where
    c2-0 c2-1 : C2

  C2Code : C2 → C2 → Set
  C2Code c2-0 c2-0 = ⊤
  C2Code c2-1 c2-1 = ⊤
  C2Code _ _ = ⊥

  C2Code-refl : (x : C2) → C2Code x x
  C2Code-refl c2-0 = tt
  C2Code-refl c2-1 = tt

  isProp-C2Code : (x y : C2) → isProp (C2Code x y)
  isProp-C2Code c2-0 c2-0 = isProp-⊤
  isProp-C2Code c2-0 c2-1 = isProp-⊥
  isProp-C2Code c2-1 c2-0 = isProp-⊥
  isProp-C2Code c2-1 c2-1 = isProp-⊤

  c2-enc : {x y : C2} → x ≡ y → C2Code x y
  c2-enc {x} p = subst (C2Code x) p (C2Code-refl x)

  c2-dec : {x y : C2} → C2Code x y → x ≡ y
  c2-dec {c2-0} {c2-0} _ = refl
  c2-dec {c2-1} {c2-1} _ = refl

  c2-dec-enc : {x y : C2} (p : x ≡ y) → c2-dec (c2-enc p) ≡ p
  c2-dec-enc {x} = J (λ y p → c2-dec (c2-enc p) ≡ p) (step x)
    where
    step : (x : C2) → c2-dec (c2-enc {x} {x} refl) ≡ refl
    step c2-0 = refl
    step c2-1 = refl

  isSet-C2 : isSet C2
  isSet-C2 x y p q =
    sym (c2-dec-enc p) ∙ cong c2-dec (isProp-C2Code x y (c2-enc p) (c2-enc q)) ∙ c2-dec-enc q

  c2Mul : C2 → C2 → C2
  c2Mul c2-0 y = y
  c2Mul c2-1 c2-0 = c2-1
  c2Mul c2-1 c2-1 = c2-0

  c2Assoc : (a b c : C2) → c2Mul (c2Mul a b) c ≡ c2Mul a (c2Mul b c)
  c2Assoc c2-0 b c = refl
  c2Assoc c2-1 c2-0 c = refl
  c2Assoc c2-1 c2-1 c2-0 = refl
  c2Assoc c2-1 c2-1 c2-1 = refl

  c2UnitR : (a : C2) → c2Mul a c2-0 ≡ a
  c2UnitR c2-0 = refl
  c2UnitR c2-1 = refl

  c2InvL : (a : C2) → c2Mul a a ≡ c2-0
  c2InvL c2-0 = refl
  c2InvL c2-1 = refl

C2Group : SetGroup
C2Group = record
  { Carrier = C2
  ; isSet-Carrier = isSet-C2
  ; e = c2-0
  ; mul = c2Mul
  ; inv = λ x → x
  ; assoc = c2Assoc
  ; unit-left = λ _ → refl
  ; unit-right = c2UnitR
  ; inverse-left = c2InvL
  ; inverse-right = c2InvL
  }

private
  data C4 : Set where
    q0 q1 q2 q3 : C4

  C4Code : C4 → C4 → Set
  C4Code q0 q0 = ⊤
  C4Code q1 q1 = ⊤
  C4Code q2 q2 = ⊤
  C4Code q3 q3 = ⊤
  C4Code _ _ = ⊥

  C4Code-refl : (x : C4) → C4Code x x
  C4Code-refl q0 = tt
  C4Code-refl q1 = tt
  C4Code-refl q2 = tt
  C4Code-refl q3 = tt

  isProp-C4Code : (x y : C4) → isProp (C4Code x y)
  isProp-C4Code q0 q0 = isProp-⊤
  isProp-C4Code q1 q1 = isProp-⊤
  isProp-C4Code q2 q2 = isProp-⊤
  isProp-C4Code q3 q3 = isProp-⊤
  isProp-C4Code q0 q1 = isProp-⊥
  isProp-C4Code q0 q2 = isProp-⊥
  isProp-C4Code q0 q3 = isProp-⊥
  isProp-C4Code q1 q0 = isProp-⊥
  isProp-C4Code q1 q2 = isProp-⊥
  isProp-C4Code q1 q3 = isProp-⊥
  isProp-C4Code q2 q0 = isProp-⊥
  isProp-C4Code q2 q1 = isProp-⊥
  isProp-C4Code q2 q3 = isProp-⊥
  isProp-C4Code q3 q0 = isProp-⊥
  isProp-C4Code q3 q1 = isProp-⊥
  isProp-C4Code q3 q2 = isProp-⊥

  c4-enc : {x y : C4} → x ≡ y → C4Code x y
  c4-enc {x} p = subst (C4Code x) p (C4Code-refl x)

  c4-dec : {x y : C4} → C4Code x y → x ≡ y
  c4-dec {q0} {q0} _ = refl
  c4-dec {q1} {q1} _ = refl
  c4-dec {q2} {q2} _ = refl
  c4-dec {q3} {q3} _ = refl

  c4-dec-enc : {x y : C4} (p : x ≡ y) → c4-dec (c4-enc p) ≡ p
  c4-dec-enc {x} = J (λ y p → c4-dec (c4-enc p) ≡ p) (step x)
    where
    step : (x : C4) → c4-dec (c4-enc {x} {x} refl) ≡ refl
    step q0 = refl
    step q1 = refl
    step q2 = refl
    step q3 = refl

  isSet-C4 : isSet C4
  isSet-C4 x y p q =
    sym (c4-dec-enc p) ∙ cong c4-dec (isProp-C4Code x y (c4-enc p) (c4-enc q)) ∙ c4-dec-enc q

  c4Mul : C4 → C4 → C4
  c4Mul q0 y = y
  c4Mul q1 q0 = q1
  c4Mul q1 q1 = q2
  c4Mul q1 q2 = q3
  c4Mul q1 q3 = q0
  c4Mul q2 q0 = q2
  c4Mul q2 q1 = q3
  c4Mul q2 q2 = q0
  c4Mul q2 q3 = q1
  c4Mul q3 q0 = q3
  c4Mul q3 q1 = q0
  c4Mul q3 q2 = q1
  c4Mul q3 q3 = q2

  c4Inv : C4 → C4
  c4Inv q0 = q0
  c4Inv q1 = q3
  c4Inv q2 = q2
  c4Inv q3 = q1

  c4Assoc : (a b c : C4) → c4Mul (c4Mul a b) c ≡ c4Mul a (c4Mul b c)
  c4Assoc q0 b c = refl
  c4Assoc q1 q0 c = refl
  c4Assoc q1 q1 q0 = refl
  c4Assoc q1 q1 q1 = refl
  c4Assoc q1 q1 q2 = refl
  c4Assoc q1 q1 q3 = refl
  c4Assoc q1 q2 q0 = refl
  c4Assoc q1 q2 q1 = refl
  c4Assoc q1 q2 q2 = refl
  c4Assoc q1 q2 q3 = refl
  c4Assoc q1 q3 q0 = refl
  c4Assoc q1 q3 q1 = refl
  c4Assoc q1 q3 q2 = refl
  c4Assoc q1 q3 q3 = refl
  c4Assoc q2 q0 c = refl
  c4Assoc q2 q1 q0 = refl
  c4Assoc q2 q1 q1 = refl
  c4Assoc q2 q1 q2 = refl
  c4Assoc q2 q1 q3 = refl
  c4Assoc q2 q2 q0 = refl
  c4Assoc q2 q2 q1 = refl
  c4Assoc q2 q2 q2 = refl
  c4Assoc q2 q2 q3 = refl
  c4Assoc q2 q3 q0 = refl
  c4Assoc q2 q3 q1 = refl
  c4Assoc q2 q3 q2 = refl
  c4Assoc q2 q3 q3 = refl
  c4Assoc q3 q0 c = refl
  c4Assoc q3 q1 q0 = refl
  c4Assoc q3 q1 q1 = refl
  c4Assoc q3 q1 q2 = refl
  c4Assoc q3 q1 q3 = refl
  c4Assoc q3 q2 q0 = refl
  c4Assoc q3 q2 q1 = refl
  c4Assoc q3 q2 q2 = refl
  c4Assoc q3 q2 q3 = refl
  c4Assoc q3 q3 q0 = refl
  c4Assoc q3 q3 q1 = refl
  c4Assoc q3 q3 q2 = refl
  c4Assoc q3 q3 q3 = refl

  c4UnitR : (a : C4) → c4Mul a q0 ≡ a
  c4UnitR q0 = refl
  c4UnitR q1 = refl
  c4UnitR q2 = refl
  c4UnitR q3 = refl

  c4InvL : (a : C4) → c4Mul (c4Inv a) a ≡ q0
  c4InvL q0 = refl
  c4InvL q1 = refl
  c4InvL q2 = refl
  c4InvL q3 = refl

  c4InvR : (a : C4) → c4Mul a (c4Inv a) ≡ q0
  c4InvR q0 = refl
  c4InvR q1 = refl
  c4InvR q2 = refl
  c4InvR q3 = refl

C4Group : SetGroup
C4Group = record
  { Carrier = C4
  ; isSet-Carrier = isSet-C4
  ; e = q0
  ; mul = c4Mul
  ; inv = c4Inv
  ; assoc = c4Assoc
  ; unit-left = λ _ → refl
  ; unit-right = c4UnitR
  ; inverse-left = c4InvL
  ; inverse-right = c4InvR
  }

mod2 : C4 → C2
mod2 q0 = c2-0
mod2 q1 = c2-1
mod2 q2 = c2-0
mod2 q3 = c2-1

mod2-mul : (x y : C4) → mod2 (c4Mul x y) ≡ c2Mul (mod2 x) (mod2 y)
mod2-mul q0 q0 = refl
mod2-mul q0 q1 = refl
mod2-mul q0 q2 = refl
mod2-mul q0 q3 = refl
mod2-mul q1 q0 = refl
mod2-mul q1 q1 = refl
mod2-mul q1 q2 = refl
mod2-mul q1 q3 = refl
mod2-mul q2 q0 = refl
mod2-mul q2 q1 = refl
mod2-mul q2 q2 = refl
mod2-mul q2 q3 = refl
mod2-mul q3 q0 = refl
mod2-mul q3 q1 = refl
mod2-mul q3 q2 = refl
mod2-mul q3 q3 = refl

mod2-inv : (x : C4) → mod2 (c4Inv x) ≡ mod2 x
mod2-inv q0 = refl
mod2-inv q1 = refl
mod2-inv q2 = refl
mod2-inv q3 = refl

mod2Hom : SetGroupHom C4Group C2Group
mod2Hom = record
  { fun = mod2
  ; pres-e = refl
  ; pres-mul = mod2-mul
  ; pres-inv = mod2-inv
  }

c4-mod2-ker-loop : fibBase mod2Hom ≡ fibBase mod2Hom
c4-mod2-ker-loop = kerLoop mod2Hom q2 refl

c4-mod2-ker-loop-proj : cong fst c4-mod2-ker-loop ≡ emloop q2
c4-mod2-ker-loop-proj = refl

c4-mod2-coset1-trivializes : fibBase mod2Hom ≡ connectingPoint mod2Hom c2-1
c4-mod2-coset1-trivializes = im-trivializes-connecting mod2Hom q1 c2-1 refl
