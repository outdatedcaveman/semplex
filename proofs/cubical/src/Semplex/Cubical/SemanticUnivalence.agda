{-# OPTIONS --cubical=full #-}
module Semplex.Cubical.SemanticUnivalence where

open import Agda.Primitive using (Level; lzero; lsuc; _⊔_)
open import Agda.Primitive.Cubical
  renaming (primINeg to ~_; primIMax to _∨_; primIMin to _∧_;
            primHComp to hcomp; primTransp to transp; primComp to comp;
            itIsOne to 1=1)
open import Agda.Builtin.Sigma using (Σ; _,_; fst; snd)
open import Agda.Builtin.Cubical.Path using (_≡_; PathP)
open import Agda.Builtin.Cubical.Sub using (Sub; inS) renaming (primSubOut to outS)
import Agda.Builtin.Cubical.HCompU as HCompU
open HCompU.Helpers using (hfill; fill; refl; sym; cong; isContr; fiber)
open import Agda.Builtin.Cubical.Equiv using (pathToEquiv) renaming (_≃_ to Builtin≃; isEquiv to BuiltinIsEquiv)
open import Agda.Builtin.Cubical.Glue using (primGlue; prim^glue; prim^unglue)
open import Semplex.Cubical.Primitives using (_∙_)

-- =============================================================================
-- 1. Core Cubical Helpers (Zero Postulates, Zero External Library)
-- =============================================================================

data ⊥ : Set where

⊥-elim : ∀ {ℓ} {A : Set ℓ} → ⊥ → A
⊥-elim ()

record ⊤ : Set where
  constructor tt

data Bool : Set where
  true false : Bool

not : Bool → Bool
not true  = false
not false = true

not-invol : (b : Bool) → not (not b) ≡ b
not-invol true  = refl
not-invol false = refl

BoolTag : Bool → Set
BoolTag true  = ⊤
BoolTag false = ⊥

true≢false : (true ≡ false) → ⊥
true≢false p = transp (λ i → BoolTag (p i)) i0 tt

infixr 4 _×_
_×_ : ∀ {ℓ₁ ℓ₂} → Set ℓ₁ → Set ℓ₂ → Set (ℓ₁ ⊔ ℓ₂)
A × B = Σ A (λ _ → B)

¬_ : ∀ {ℓ} → Set ℓ → Set ℓ
¬ A = A → ⊥

isProp : ∀ {ℓ} → Set ℓ → Set ℓ
isProp A = (x y : A) → x ≡ y

isSet : ∀ {ℓ} → Set ℓ → Set ℓ
isSet A = (x y : A) → isProp (x ≡ y)

subst : ∀ {ℓ ℓ'} {A : Set ℓ} (P : A → Set ℓ') {x y : A} → x ≡ y → P x → P y
subst P p pa = transp (λ i → P (p i)) i0 pa

transport : ∀ {ℓ} {A B : Set ℓ} → A ≡ B → A → B
transport p a = transp (λ i → p i) i0 a

transpFill : ∀ {ℓ} (P : I → Set ℓ) (p₀ : P i0) → PathP P p₀ (transp P i0 p₀)
transpFill P p₀ i = transp (λ j → P (i ∧ j)) (~ i) p₀

transpRefl : ∀ {ℓ} {A : Set ℓ} (a : A) → transp (λ _ → A) i0 a ≡ a
transpRefl {A = A} a i = transp (λ _ → A) i a

substRefl : ∀ {ℓ ℓ'} {A : Set ℓ} (P : A → Set ℓ') {x : A} (px : P x)
  → subst P refl px ≡ px
substRefl P px = transpRefl px

J : ∀ {ℓ ℓ'} {A : Set ℓ} {x : A} (P : ∀ y → x ≡ y → Set ℓ')
  → P x refl → ∀ {y} (p : x ≡ y) → P y p
J P d p = transp (λ i → P (p i) (λ j → p (i ∧ j))) i0 d

JRefl : ∀ {ℓ ℓ'} {A : Set ℓ} {x : A} (P : ∀ y → x ≡ y → Set ℓ') (d : P x refl)
  → J P d refl ≡ d
JRefl P d = transpRefl d

funExt : ∀ {ℓ ℓ'} {A : Set ℓ} {B : A → Set ℓ'} {f g : (x : A) → B x}
  → (∀ x → f x ≡ g x) → f ≡ g
funExt h i x = h x i

funExt⁻ : ∀ {ℓ ℓ'} {A : Set ℓ} {B : A → Set ℓ'} {f g : (x : A) → B x}
  → f ≡ g → ∀ x → f x ≡ g x
funExt⁻ p x i = p i x

ΣPathP : ∀ {ℓ ℓ'} {A : I → Set ℓ} {B : (i : I) → A i → Set ℓ'}
  {u : Σ (A i0) (B i0)} {v : Σ (A i1) (B i1)}
  → (p : PathP A (fst u) (fst v))
  → PathP (λ i → B i (p i)) (snd u) (snd v)
  → PathP (λ i → Σ (A i) (B i)) u v
ΣPathP p q i = (p i , q i)

isProp→PathP : ∀ {ℓ} {B : I → Set ℓ}
  → (∀ i → isProp (B i)) → (b₀ : B i0) → (b₁ : B i1) → PathP B b₀ b₁
isProp→PathP {B = B} h b₀ b₁ i =
  comp (λ _ → B i)
       (λ { j (i = i0) → b₀
          ; j (i = i1) → h i1 (transp B i0 b₀) b₁ j })
       (transpFill B b₀ i)

isPropΠ : ∀ {ℓ ℓ'} {A : Set ℓ} {B : A → Set ℓ'}
  → (∀ x → isProp (B x)) → isProp ((x : A) → B x)
isPropΠ h f g i x = h x (f x) (g x) i

isContrSingl : ∀ {ℓ} {A : Set ℓ} (a : A) → isContr (Σ A (λ x → a ≡ x))
isContrSingl a = (a , refl) , λ { (x , p) i → (p i , λ j → p (i ∧ j)) }

isContrSinglRev : ∀ {ℓ} {A : Set ℓ} (a : A) → isContr (Σ A (λ x → x ≡ a))
isContrSinglRev a = (a , refl) , λ { (x , p) i → (p (~ i) , λ j → p ((~ i) ∨ j)) }

isProp→isSet : ∀ {ℓ} {A : Set ℓ} → isProp A → isSet A
isProp→isSet {A = A} h x y p q j i =
  comp (λ _ → A)
       (λ { k (i = i0) → h x x k
          ; k (i = i1) → h x y k
          ; k (j = i0) → h x (p i) k
          ; k (j = i1) → h x (q i) k })
       x

isPropIsProp : ∀ {ℓ} {A : Set ℓ} → isProp (isProp A)
isPropIsProp h₁ h₂ i x y = isProp→isSet h₁ x y (h₁ x y) (h₂ x y) i

isContr→isProp : ∀ {ℓ} {A : Set ℓ} → isContr A → isProp A
isContr→isProp (c , p) x y = sym (p x) ∙ p y

isPropIsContr : ∀ {ℓ} {A : Set ℓ} → isProp (isContr A)
isPropIsContr {A = A} c₁@(x , p) c₂@(y , q) =
  ΣPathP (p y) (isProp→PathP (λ _ → isPropΠ (λ z → isSetA _ z)) p q)
  where
    isSetA : isSet A
    isSetA = isProp→isSet (isContr→isProp c₁)

isContrRetract : ∀ {ℓ ℓ'} {A : Set ℓ} {B : Set ℓ'}
  → (f : A → B) (g : B → A) (h : ∀ x → g (f x) ≡ x)
  → isContr B → isContr A
isContrRetract f g h (cb , pb) =
  (g cb , λ a → cong g (pb (f a)) ∙ h a)

isContrΣ : ∀ {ℓ ℓ'} {A : Set ℓ} {B : A → Set ℓ'}
  → isContr A → (∀ a → isContr (B a)) → isContr (Σ A B)
isContrΣ (ca , pa) cb =
  ((ca , fst (cb ca)) ,
   λ { (a , b) → ΣPathP (pa a)
                   (isProp→PathP (λ i → isContr→isProp (cb (pa a i)))
                                 (fst (cb ca)) b) })

isContrFiberOfContrBase : ∀ {ℓ ℓ'} {T : Set ℓ} (u : isContr T)
  (P : T → Set ℓ') → isContr (P (fst u)) → isContr (Σ T P)
isContrFiberOfContrBase u P p₀ =
  isContrΣ u (λ t → subst (λ z → isContr (P z)) (snd u t) p₀)

isContrUnit : ∀ {ℓ} {A : Set ℓ} (a : A) → isProp A → isContr A
isContrUnit a h = a , h a

isEquiv : ∀ {ℓ ℓ'} {A : Set ℓ} {B : Set ℓ'} → (A → B) → Set (ℓ ⊔ ℓ')
isEquiv {B = B} f = (y : B) → isContr (fiber f y)

infix 4 _≃_
_≃_ : ∀ {ℓ ℓ'} (A : Set ℓ) (B : Set ℓ') → Set (ℓ ⊔ ℓ')
A ≃ B = Σ (A → B) isEquiv

equivFun : ∀ {ℓ ℓ'} {A : Set ℓ} {B : Set ℓ'} → A ≃ B → A → B
equivFun = fst

toBuiltinEquiv : ∀ {ℓ ℓ'} {A : Set ℓ} {B : Set ℓ'} → A ≃ B → Builtin≃ A B
toBuiltinEquiv (f , p) = f , record { equiv-proof = p }

fromBuiltinEquiv : ∀ {ℓ ℓ'} {A : Set ℓ} {B : Set ℓ'} → Builtin≃ A B → A ≃ B
fromBuiltinEquiv (f , q) = f , BuiltinIsEquiv.equiv-proof q

isPropIsEquiv : ∀ {ℓ ℓ'} {A : Set ℓ} {B : Set ℓ'} (f : A → B) → isProp (isEquiv f)
isPropIsEquiv _ = isPropΠ (λ _ → isPropIsContr)

-- =============================================================================
-- 2. Equivalences, Univalence from primGlue, and Fundamental Theorem of Id
-- =============================================================================

idEquiv : ∀ {ℓ} (A : Set ℓ) → A ≃ A
idEquiv A = (λ x → x) , λ y → (y , refl) , λ { (x , p) i → (p (~ i) , λ j → p ((~ i) ∨ j)) }

equivEq : ∀ {ℓ ℓ'} {A : Set ℓ} {B : Set ℓ'} {e₁ e₂ : A ≃ B}
  → equivFun e₁ ≡ equivFun e₂ → e₁ ≡ e₂
equivEq {e₁ = e₁} {e₂ = e₂} p =
  ΣPathP p (isProp→PathP (λ i → isPropIsEquiv (p i)) (snd e₁) (snd e₂))

ua : ∀ {ℓ} {A B : Set ℓ} → A ≃ B → A ≡ B
ua {A = A} {B = B} e i =
  primGlue B (λ { (i = i0) → A ; (i = i1) → B })
             (λ { (i = i0) → toBuiltinEquiv e ; (i = i1) → toBuiltinEquiv (idEquiv B) })

uaβ : ∀ {ℓ} {A B : Set ℓ} (e : A ≃ B) (x : A) → transport (ua e) x ≡ equivFun e x
uaβ {A = A} {B = B} e x =
  sym (λ i → prim^unglue {A = B} {φ = (~ i) ∨ i}
               {T = λ { (i = i0) → A ; (i = i1) → B }}
               {e = λ { (i = i0) → toBuiltinEquiv e ; (i = i1) → toBuiltinEquiv (idEquiv B) }}
               (transpFill (λ j → ua e j) x i))

-- Co-based contractibility of equivalences directly from primGlue + isPropIsEquiv:
isContrSinglEquiv : ∀ {ℓ} (B : Set ℓ) → isContr (Σ (Set ℓ) (λ X → X ≃ B))
isContrSinglEquiv {ℓ} B = (B , idEquiv B) , contr
  where
    contr : (p : Σ (Set ℓ) (λ X → X ≃ B)) → (B , idEquiv B) ≡ p
    contr (A , e) i = (E i , (unglueMap i , proofPath i))
      where
        E : I → Set ℓ
        E i = primGlue B (λ { (i = i0) → B ; (i = i1) → A })
                         (λ { (i = i0) → toBuiltinEquiv (idEquiv B) ; (i = i1) → toBuiltinEquiv e })

        unglueMap : (i : I) → E i → B
        unglueMap i x = prim^unglue {A = B} {φ = (~ i) ∨ i} x

        proofPath : PathP (λ i → isEquiv (unglueMap i)) (snd (idEquiv B)) (snd e)
        proofPath =
          isProp→PathP (λ i → isPropIsEquiv (unglueMap i))
                        (snd (idEquiv B)) (snd e)

contrMapIsEquiv : ∀ {ℓ₁ ℓ₂} {X : Set ℓ₁} {Y : Set ℓ₂}
  → isContr X → isContr Y → (f : X → Y) → isEquiv f
contrMapIsEquiv cX@(cx , _) cY f y =
  (cx , isContr→isProp cY (f cx) y) ,
  λ { (x , p) → ΣPathP (isContr→isProp cX cx x)
                  (isProp→PathP (λ _ → isProp→isSet (isContr→isProp cY) _ y) _ p) }

fundamentalThmIdRev : ∀ {ℓ ℓ'} {A : Set ℓ} (P : A → Set ℓ') {b : A}
  → isContr (Σ A P)
  → (f : ∀ {x} → x ≡ b → P x)
  → ∀ x → (x ≡ b) ≃ P x
fundamentalThmIdRev {A = A} P {b = b} cP f x = f , proof
  where
    totMap : Σ A (λ y → y ≡ b) → Σ A P
    totMap (y , p) = (y , f p)

    totEquiv : isEquiv totMap
    totEquiv = contrMapIsEquiv (isContrSinglRev b) cP totMap

    sec : ∀ {q} → fiber (f {x}) q → fiber totMap (x , q)
    sec (p , r) = ((x , p) , ΣPathP refl r)

    retAux : ∀ y (eq₁ : x ≡ y) (p : y ≡ b) {q : P x}
      → PathP (λ i → P (eq₁ (~ i))) (f p) q → fiber (f {x}) q
    retAux y eq₁ p {q = q} eq₂ =
      J (λ z (xz : x ≡ z) → (pz : z ≡ b) → PathP (λ i → P (xz (~ i))) (f pz) q → fiber (f {x}) q)
        (λ px rq → (px , rq))
        eq₁ p eq₂

    ret : ∀ {q} → fiber totMap (x , q) → fiber (f {x}) q
    ret {q = q} ((y , p) , eq) =
      retAux y (sym (λ i → fst (eq i))) p (λ i → snd (eq i))

    retSec : ∀ {q} (z : fiber (f {x}) q) → ret (sec z) ≡ z
    retSec {q = q} (p , r) i =
      JRefl (λ z (xz : x ≡ z) → (pz : z ≡ b) → PathP (λ j → P (xz (~ j))) (f pz) q → fiber (f {x}) q)
            (λ px rq → (px , rq))
            i p r

    proof : (q : P x) → isContr (fiber (f {x}) q)
    proof q = isContrRetract (sec {q}) (ret {q}) (retSec {q}) (totEquiv (x , q))

-- Co-based univalence theorem from primGlue:
univalence : ∀ {ℓ} (A B : Set ℓ) → (A ≡ B) ≃ (A ≃ B)
univalence {ℓ} A B =
  fundamentalThmIdRev (λ X → X ≃ B) {b = B}
    (isContrSinglEquiv B)
    (λ p → fromBuiltinEquiv (pathToEquiv {ℓ = λ _ → ℓ} (λ i → p i)))
    A

equivInv : ∀ {ℓ₁ ℓ₂} {A : Set ℓ₁} {B : Set ℓ₂} → A ≃ B → B → A
equivInv e b = fst (fst (snd e b))

equivSec : ∀ {ℓ₁ ℓ₂} {A : Set ℓ₁} {B : Set ℓ₂} (e : A ≃ B) (b : B)
  → equivFun e (equivInv e b) ≡ b
equivSec e b = snd (fst (snd e b))

-- Propositional bi-implications form equivalences and contractibly glue to N:
propBiimpl→Equiv : ∀ {ℓ₁ ℓ₂} {P : Set ℓ₁} {Q : Set ℓ₂}
  → isProp P → isProp Q → (P → Q) → (Q → P) → P ≃ Q
propBiimpl→Equiv {Q = Q} hp hq f g = f , proof
  where
    proof : (q : Q) → isContr (fiber f q)
    proof q = (g q , hq (f (g q)) q) ,
              λ { (p , eq) → ΣPathP (hp (g q) p)
                              (isProp→PathP (λ _ → isProp→isSet hq _ q) _ eq) }

isContrHPropSingl : ∀ {ℓ} (Q : Set ℓ) (hq : isProp Q)
  → isContr (Σ (Σ (Set ℓ) isProp) (λ (P , _) → (P → Q) × (Q → P)))
isContrHPropSingl {ℓ} Q hq = isContrRetract to from linv cBase
  where
    Base : Set (lsuc ℓ)
    Base = Σ (Σ (Set ℓ) (λ P → P ≃ Q)) (λ (P , _) → isProp P)

    cBase : isContr Base
    cBase = isContrFiberOfContrBase (isContrSinglEquiv Q)
              (λ (P , _) → isProp P) (isContrUnit hq isPropIsProp)

    to : Σ (Σ (Set ℓ) isProp) (λ (P , _) → (P → Q) × (Q → P)) → Base
    to ((P , hp) , (f , g)) = ((P , propBiimpl→Equiv hp hq f g) , hp)

    from : Base → Σ (Σ (Set ℓ) isProp) (λ (P , _) → (P → Q) × (Q → P))
    from ((P , e) , hp) = ((P , hp) , (equivFun e , equivInv e))

    linv : (u : Σ (Σ (Set ℓ) isProp) (λ (P , _) → (P → Q) × (Q → P)))
      → from (to u) ≡ u
    linv ((P , hp) , (f , g)) =
      ΣPathP refl (ΣPathP (isPropΠ (λ _ → hq) _ f) (isPropΠ (λ _ → hp) _ g))

-- =============================================================================
-- 3. Causal Coalgebraic Semantic Universe & Computational Semantic Univalence
-- =============================================================================

record CausalCoalgebra {ℓ : Level} (A O : Set ℓ) : Set (lsuc ℓ) where
  field
    Carrier : Set ℓ
    obs     : Carrier → O
    step    : Carrier → A → Carrier
    coh     : Carrier → Set ℓ
    cohProp : (x : Carrier) → isProp (coh x)
    closed  : (x : Carrier) (a : A) → coh x → coh (step x a)

record SemEquiv {ℓ : Level} {A O : Set ℓ} (M N : CausalCoalgebra A O) : Set ℓ where
  private
    module M = CausalCoalgebra M
    module N = CausalCoalgebra N
  field
    carrierEq  : M.Carrier ≃ N.Carrier
    obsComm    : (x : M.Carrier) → M.obs x ≡ N.obs (equivFun carrierEq x)
    stepComm   : (x : M.Carrier) (a : A)
      → equivFun carrierEq (M.step x a) ≡ N.step (equivFun carrierEq x) a
    cohComm    : (x : M.Carrier) → M.coh x → N.coh (equivFun carrierEq x)
    cohCommInv : (x : M.Carrier) → N.coh (equivFun carrierEq x) → M.coh x

idSemEquiv : ∀ {ℓ} {A O : Set ℓ} (M : CausalCoalgebra A O) → SemEquiv M M
idSemEquiv M = record
  { carrierEq  = idEquiv (CausalCoalgebra.Carrier M)
  ; obsComm    = λ _ → refl
  ; stepComm   = λ _ _ → refl
  ; cohComm    = λ _ c → c
  ; cohCommInv = λ _ c → c
  }

pathToSemEquiv : ∀ {ℓ} {A O : Set ℓ} {M N : CausalCoalgebra A O}
  → M ≡ N → SemEquiv M N
pathToSemEquiv {N = N} p = subst (λ X → SemEquiv X N) (sym p) (idSemEquiv N)

isContrSinglSemEquiv : ∀ {ℓ} {A O : Set ℓ} (N : CausalCoalgebra A O)
  → isContr (Σ (CausalCoalgebra A O) (λ M → SemEquiv M N))
isContrSinglSemEquiv {ℓ} {A = A} {O = O} N = isContrRetract pack unpack packUnpack contrNested
  where
    open CausalCoalgebra N renaming
      (Carrier to NC; obs to Nobs; step to Nstep; coh to Ncoh; cohProp to NcohProp; closed to Nclosed)

    XEq : Set (lsuc ℓ)
    XEq = Σ (Set ℓ) (λ X → X ≃ NC)

    ObsLayer : XEq → Set ℓ
    ObsLayer (X , eq) = Σ (X → O) (λ o → (x : X) → o x ≡ Nobs (equivFun eq x))

    StepLayer : XEq → Set ℓ
    StepLayer (X , eq) =
      Σ (X → A → X) (λ s → (x : X) (a : A) → equivFun eq (s x a) ≡ Nstep (equivFun eq x) a)

    CohLayer : XEq → Set (lsuc ℓ)
    CohLayer (X , eq) =
      Σ (X → Σ (Set ℓ) isProp)
        (λ ch → ((x : X) → fst (ch x) → Ncoh (equivFun eq x))
              × ((x : X) → Ncoh (equivFun eq x) → fst (ch x)))

    StructAtX : XEq → Set (lsuc ℓ)
    StructAtX xe =
      Σ (ObsLayer xe × StepLayer xe × CohLayer xe)
        (λ (_ , (s , _) , (ch , _)) →
          (x : fst xe) (a : A) → fst (ch x) → fst (ch (s x a)))

    Nested : Set (lsuc ℓ)
    Nested = Σ XEq StructAtX

    contrXEq : isContr XEq
    contrXEq = isContrSinglEquiv NC

    contrObsAtCenter : isContr (ObsLayer (NC , idEquiv NC))
    contrObsAtCenter = isContrRetract toRev fromRev toFromRev (isContrSinglRev Nobs)
      where
        toRev : ObsLayer (NC , idEquiv NC) → Σ (NC → O) (λ o → o ≡ Nobs)
        toRev (o , h) = (o , funExt h)

        fromRev : Σ (NC → O) (λ o → o ≡ Nobs) → ObsLayer (NC , idEquiv NC)
        fromRev (o , p) = (o , funExt⁻ p)

        toFromRev : (u : ObsLayer (NC , idEquiv NC)) → fromRev (toRev u) ≡ u
        toFromRev (o , h) = refl

    contrStepAtCenter : isContr (StepLayer (NC , idEquiv NC))
    contrStepAtCenter = isContrRetract toRev fromRev toFromRev (isContrSinglRev Nstep)
      where
        toRev : StepLayer (NC , idEquiv NC) → Σ (NC → A → NC) (λ s → s ≡ Nstep)
        toRev (s , h) = (s , λ i x a → h x a i)

        fromRev : Σ (NC → A → NC) (λ s → s ≡ Nstep) → StepLayer (NC , idEquiv NC)
        fromRev (s , p) = (s , λ x a i → p i x a)

        toFromRev : (u : StepLayer (NC , idEquiv NC)) → fromRev (toRev u) ≡ u
        toFromRev (s , h) = refl

    contrCohAtCenter : isContr (CohLayer (NC , idEquiv NC))
    contrCohAtCenter = isContrRetract toPi fromPi toFromPi contrPointwise
      where
        Pt : NC → Set (lsuc ℓ)
        Pt x = Σ (Σ (Set ℓ) isProp) (λ (P , _) → (P → Ncoh x) × (Ncoh x → P))

        contrPointwise : isContr ((x : NC) → Pt x)
        contrPointwise =
          ( (λ x → fst (isContrHPropSingl (Ncoh x) (NcohProp x)))
          , λ f i x → snd (isContrHPropSingl (Ncoh x) (NcohProp x)) (f x) i
          )

        toPi : CohLayer (NC , idEquiv NC) → (x : NC) → Pt x
        toPi (ch , (f , g)) x = (ch x , (f x , g x))

        fromPi : ((x : NC) → Pt x) → CohLayer (NC , idEquiv NC)
        fromPi u = ((λ x → fst (u x)) , ((λ x → fst (snd (u x))) , (λ x → snd (snd (u x)))))

        toFromPi : (u : CohLayer (NC , idEquiv NC)) → fromPi (toPi u) ≡ u
        toFromPi (ch , (f , g)) = refl

    contrStructAtCenter : isContr (StructAtX (NC , idEquiv NC))
    contrStructAtCenter =
      isContrFiberOfContrBase contrBaseTuple
        (λ (_ , (s , _) , (ch , _)) → (x : NC) (a : A) → fst (ch x) → fst (ch (s x a)))
        (isContrUnit Nclosed (isPropΠ (λ x → isPropΠ (λ a → isPropΠ (λ _ → NcohProp (Nstep x a))))))
      where
        contrBaseTuple : isContr (ObsLayer (NC , idEquiv NC) × StepLayer (NC , idEquiv NC) × CohLayer (NC , idEquiv NC))
        contrBaseTuple =
          isContrΣ contrObsAtCenter (λ _ → isContrΣ contrStepAtCenter (λ _ → contrCohAtCenter))

    contrNested : isContr Nested
    contrNested = isContrFiberOfContrBase contrXEq StructAtX contrStructAtCenter

    pack : Σ (CausalCoalgebra A O) (λ M → SemEquiv M N) → Nested
    pack (M , e) =
      ( (M.Carrier , e.carrierEq)
      , ( ( (M.obs , e.obsComm)
          , (M.step , e.stepComm)
          , ((λ x → (M.coh x , M.cohProp x)) , (e.cohComm , e.cohCommInv))
          )
        , M.closed
        )
      )
      where
        module M = CausalCoalgebra M
        module e = SemEquiv e

    unpack : Nested → Σ (CausalCoalgebra A O) (λ M → SemEquiv M N)
    unpack ((X , eq) , (( (o , oc) , (s , sc) , (ch , (cc , cci)) ) , cl)) =
      ( record
          { Carrier = X
          ; obs     = o
          ; step    = s
          ; coh     = λ x → fst (ch x)
          ; cohProp = λ x → snd (ch x)
          ; closed  = cl
          }
      , record
          { carrierEq  = eq
          ; obsComm    = oc
          ; stepComm   = sc
          ; cohComm    = cc
          ; cohCommInv = cci
          }
      )

    packUnpack : (u : Σ (CausalCoalgebra A O) (λ M → SemEquiv M N)) → unpack (pack u) ≡ u
    packUnpack (M , e) = refl

semanticUnivalence : ∀ {ℓ} {A O : Set ℓ} (M N : CausalCoalgebra A O)
  → (M ≡ N) ≃ SemEquiv M N
semanticUnivalence M N =
  fundamentalThmIdRev (λ X → SemEquiv X N) {b = N} (isContrSinglSemEquiv N) pathToSemEquiv M

semEquivToPath : ∀ {ℓ} {A O : Set ℓ} {M N : CausalCoalgebra A O}
  → SemEquiv M N → M ≡ N
semEquivToPath {M = M} {N = N} e = equivInv (semanticUnivalence M N) e

semLoopEquivAut : ∀ {ℓ} {A O : Set ℓ} (M : CausalCoalgebra A O)
  → (M ≡ M) ≃ SemEquiv M M
semLoopEquivAut M = semanticUnivalence M M

-- =============================================================================
-- 4. Non-Trivial Isotropy Witness & Contextual Ring Transport
-- =============================================================================

notEquiv : Bool ≃ Bool
notEquiv = not , proof
  where
    isSetBool : isSet Bool
    isSetBool = h
      where
        code : Bool → Bool → Set
        code true  true  = ⊤
        code false false = ⊤
        code _     _     = ⊥

        codeProp : ∀ a b → isProp (code a b)
        codeProp true  true  tt tt = refl
        codeProp false false tt tt = refl
        codeProp true  false ()
        codeProp false true  ()

        reflCode : ∀ b → code b b
        reflCode true  = tt
        reflCode false = tt

        encode : ∀ {a b} → a ≡ b → code a b
        encode {a} p = subst (code a) p (reflCode a)

        decode : ∀ {a b} → code a b → a ≡ b
        decode {true}  {true}  tt = refl
        decode {false} {false} tt = refl
        decode {true}  {false} ()
        decode {false} {true}  ()

        retractEq : ∀ {a b} (p : a ≡ b) → decode {a} {b} (encode p) ≡ p
        retractEq {a} p =
          J (λ b q → decode {a} {b} (encode q) ≡ q) (JBase a) p
          where
            JBase : ∀ c → decode {c} {c} (encode {c} {c} refl) ≡ refl
            JBase true  = cong (decode {true} {true}) (substRefl (code true) {x = true} tt)
            JBase false = cong (decode {false} {false}) (substRefl (code false) {x = false} tt)

        h : isSet Bool
        h a b p q = sym (retractEq p) ∙ cong decode (codeProp a b (encode p) (encode q)) ∙ retractEq q

    proof : (y : Bool) → isContr (fiber not y)
    proof true  = (false , refl) , λ { (false , p) → ΣPathP refl (isSetBool _ _ refl p)
                                     ; (true  , p) → ⊥-elim (true≢false (sym p)) }
    proof false = (true  , refl) , λ { (true  , p) → ΣPathP refl (isSetBool _ _ refl p)
                                     ; (false , p) → ⊥-elim (true≢false p) }

boolFlipCoalgebra : CausalCoalgebra {lzero} ⊤ ⊤
boolFlipCoalgebra = record
  { Carrier = Bool
  ; obs     = λ _ → tt
  ; step    = λ b _ → b
  ; coh     = λ _ → ⊤
  ; cohProp = λ _ tt tt → refl
  ; closed  = λ _ _ tt → tt
  }

boolFlipAut : SemEquiv boolFlipCoalgebra boolFlipCoalgebra
boolFlipAut = record
  { carrierEq  = notEquiv
  ; obsComm    = λ _ → refl
  ; stepComm   = λ _ _ → refl
  ; cohComm    = λ _ tt → tt
  ; cohCommInv = λ _ tt → tt
  }

-- Proves that SemEquiv univalence retains nontrivial automorphisms (non-thin 1-groupoid):
boolFlipPath≢refl : ¬ (semEquivToPath boolFlipAut ≡ refl)
boolFlipPath≢refl eq = true≢false (sym (sym evalFalse ∙ cong ev eq ∙ evalTrue))
  where
    ev : (p : boolFlipCoalgebra ≡ boolFlipCoalgebra) → Bool
    ev p = equivFun (SemEquiv.carrierEq (pathToSemEquiv p)) true

    evalTrue : ev refl ≡ true
    evalTrue =
      cong (λ q → equivFun (SemEquiv.carrierEq q) true)
           (substRefl (λ X → SemEquiv X boolFlipCoalgebra) (idSemEquiv boolFlipCoalgebra))

    evalFalse : ev (semEquivToPath boolFlipAut) ≡ false
    evalFalse =
      cong (λ q → equivFun (SemEquiv.carrierEq q) true)
           (equivSec (semanticUnivalence boolFlipCoalgebra boolFlipCoalgebra) boolFlipAut)

-- =============================================================================
-- 5. Contextual Ring Closure & Transport Along SemEquiv in Cubical HoTT
-- =============================================================================

record ContextualRing {ℓ : Level} (Ctx : Set ℓ) (A : Set ℓ) (O : Ctx → Set ℓ) : Set (lsuc ℓ) where
  field
    moduleAt    : (c : Ctx) → CausalCoalgebra A (O c)
    adjacent    : Ctx → Ctx → Set ℓ
    corresponds : ∀ {c d} → adjacent c d
      → CausalCoalgebra.Carrier (moduleAt c)
      → CausalCoalgebra.Carrier (moduleAt d)
      → Set ℓ
    corrClosed  : ∀ {c d} (h : adjacent c d) (x : CausalCoalgebra.Carrier (moduleAt c))
      (y : CausalCoalgebra.Carrier (moduleAt d)) (a : A)
      → corresponds h x y
      → corresponds h (CausalCoalgebra.step (moduleAt c) x a)
                      (CausalCoalgebra.step (moduleAt d) y a)

GlobalCoherentSection : ∀ {ℓ} {Ctx A : Set ℓ} {O : Ctx → Set ℓ}
  (R : ContextualRing Ctx A O) → Set ℓ
GlobalCoherentSection R =
  Σ ((c : _) → CausalCoalgebra.Carrier (moduleAt c))
    (λ s → ((c : _) → CausalCoalgebra.coh (moduleAt c) (s c))
         × (∀ {c d} (h : adjacent c d) → corresponds h (s c) (s d)))
  where open ContextualRing R

ring-evolve-preserves : ∀ {ℓ} {Ctx A : Set ℓ} {O : Ctx → Set ℓ}
  (R : ContextualRing Ctx A O) → A → GlobalCoherentSection R → GlobalCoherentSection R
ring-evolve-preserves R a (s , (loc , cor)) =
  ( (λ c → CausalCoalgebra.step (moduleAt c) (s c) a)
  , ( (λ c → CausalCoalgebra.closed (moduleAt c) (s c) a (loc c))
    , λ h → corrClosed h (s _) (s _) a (cor h) )
  )
  where open ContextualRing R

module-transport-closed : ∀ {ℓ} {A O : Set ℓ} {M N : CausalCoalgebra A O}
  (e : SemEquiv M N) (x : CausalCoalgebra.Carrier M) (a : A)
  → CausalCoalgebra.coh M x
  → CausalCoalgebra.coh N (CausalCoalgebra.step N (equivFun (SemEquiv.carrierEq e) x) a)
module-transport-closed {M = M} {N = N} e x a hx =
  subst (CausalCoalgebra.coh N) (SemEquiv.stepComm e x a)
        (SemEquiv.cohComm e (CausalCoalgebra.step M x a) (CausalCoalgebra.closed M x a hx))

ring-transport-along-semEquiv : ∀ {ℓ ℓ'} {Ctx A O : Set ℓ}
  (P : ((c : Ctx) → CausalCoalgebra A O) → Set ℓ')
  {F₁ F₂ : (c : Ctx) → CausalCoalgebra A O}
  → ((c : Ctx) → SemEquiv (F₁ c) (F₂ c))
  → P F₁ → P F₂
ring-transport-along-semEquiv P eqs =
  subst P (funExt (λ c → semEquivToPath (eqs c)))

ring-section-transport : ∀ {ℓ} {Ctx A O : Set ℓ}
  (adj : Ctx → Ctx → Set ℓ)
  (corr : ∀ {M₁ M₂ : CausalCoalgebra A O} → (c₁ c₂ : Ctx) → adj c₁ c₂
    → CausalCoalgebra.Carrier M₁ → CausalCoalgebra.Carrier M₂ → Set ℓ)
  (F₁ F₂ : (c : Ctx) → CausalCoalgebra A O)
  (eqs : (c : Ctx) → SemEquiv (F₁ c) (F₂ c))
  → (Σ ((c : Ctx) → CausalCoalgebra.Carrier (F₁ c))
       (λ s → ((c : Ctx) → CausalCoalgebra.coh (F₁ c) (s c))
            × (∀ {c d} (h : adj c d) → corr c d h (s c) (s d))))
  → (Σ ((c : Ctx) → CausalCoalgebra.Carrier (F₂ c))
       (λ s → ((c : Ctx) → CausalCoalgebra.coh (F₂ c) (s c))
            × (∀ {c d} (h : adj c d) → corr c d h (s c) (s d))))
ring-section-transport {Ctx = Ctx} adj corr F₁ F₂ eqs =
  ring-transport-along-semEquiv
    (λ F → Σ ((c : Ctx) → CausalCoalgebra.Carrier (F c))
             (λ s → ((c : Ctx) → CausalCoalgebra.coh (F c) (s c))
                  × (∀ {c d} (h : adj c d) → corr {M₁ = F c} {M₂ = F d} c d h (s c) (s d))))
    eqs
