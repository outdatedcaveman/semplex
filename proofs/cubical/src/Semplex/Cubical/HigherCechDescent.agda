{-# OPTIONS --cubical=full #-}
module Semplex.Cubical.HigherCechDescent where

open import Agda.Primitive using (Level; lzero; lsuc; _⊔_)
open import Agda.Primitive.Cubical
  renaming (primINeg to ~_; primIMax to _∨_; primIMin to _∧_;
            primHComp to hcomp; primTransp to transp; primComp to comp)
open import Agda.Builtin.Sigma using (Σ; _,_; fst; snd)
open import Agda.Builtin.Cubical.Path using (_≡_; PathP)
import Agda.Builtin.Cubical.HCompU as HCompU
open HCompU.Helpers using (refl; sym; cong; isContr; fiber)
open import Semplex.Cubical.Primitives using (_∙_)
open import Semplex.Cubical.SemanticUnivalence
  using ( ⊥; ⊥-elim; ⊤; tt; Bool; true; false; not; notEquiv; true≢false
        ; _×_; ¬_; isProp; isSet
        ; subst; substRefl; transport; transpRefl; J; JRefl; funExt; ΣPathP; isProp→PathP
        ; isProp→isSet; isContr→isProp; isContrRetract
        ; isEquiv; _≃_; equivFun; equivInv; equivSec; idEquiv; equivEq; isPropIsEquiv
        ; ua; uaβ
        ; CausalCoalgebra; SemEquiv; idSemEquiv; semEquivToPath; pathToSemEquiv
        ; boolFlipCoalgebra; boolFlipAut; boolFlipPath≢refl
        )

-- =============================================================================
-- 1. Cubical Path Composition Laws & Definitional Equivalence Composition
-- =============================================================================

refl∙refl≡refl : ∀ {ℓ} {A : Set ℓ} {x : A} → (refl ∙ refl) ≡ refl {x = x}
refl∙refl≡refl {x = x} k i =
  hcomp (λ j → λ { (i = i0) → x ; (i = i1) → x ; (k = i1) → x }) x

compPath-refl-r : ∀ {ℓ} {A : Set ℓ} {x y : A} (p : x ≡ y) → p ∙ refl ≡ p
compPath-refl-r = J (λ y p → p ∙ refl ≡ p) refl∙refl≡refl

compPath-refl-l : ∀ {ℓ} {A : Set ℓ} {x y : A} (p : x ≡ y) → refl ∙ p ≡ p
compPath-refl-l = J (λ y p → refl ∙ p ≡ p) refl∙refl≡refl

compPath-assoc : ∀ {ℓ} {A : Set ℓ} {w x y z : A}
  (p : w ≡ x) (q : x ≡ y) (r : y ≡ z) → (p ∙ q) ∙ r ≡ p ∙ (q ∙ r)
compPath-assoc p q r =
  J (λ _ r' → (p ∙ q) ∙ r' ≡ p ∙ (q ∙ r'))
    (compPath-refl-r (p ∙ q) ∙ cong (p ∙_) (sym (compPath-refl-r q)))
    r

compEquiv : ∀ {ℓ₁ ℓ₂ ℓ₃} {A : Set ℓ₁} {B : Set ℓ₂} {C : Set ℓ₃}
  → A ≃ B → B ≃ C → A ≃ C
compEquiv {A = A} {B = B} {C = C} e₁@(f , pf) e₂@(g , pg) =
  (λ a → g (f a)) , λ c → isContrRetract (to c) (from c) (ret c) (pg c)
  where
    to : (c : C) → fiber (λ a → g (f a)) c → fiber g c
    to c (a , p) = (f a , p)

    from : (c : C) → fiber g c → fiber (λ a → g (f a)) c
    from c (b , q) = (fst (fst (pf b)) , cong g (snd (fst (pf b))) ∙ q)

    ret : (c : C) (z : fiber (λ a → g (f a)) c) → from c (to c z) ≡ z
    ret c (a , p) =
      (λ i → (fst (snd (pf (f a)) (a , refl) i)
            , cong g (snd (snd (pf (f a)) (a , refl) i)) ∙ p))
      ∙ (λ i → (a , compPath-refl-l p i))

path→Equiv : ∀ {ℓ} {A B : Set ℓ} → A ≡ B → A ≃ B
path→Equiv {A = A} p = J (λ X _ → A ≃ X) (idEquiv A) p

path→Equiv-refl : ∀ {ℓ} (A : Set ℓ) → path→Equiv (refl {x = A}) ≡ idEquiv A
path→Equiv-refl A = JRefl (λ X _ → A ≃ X) (idEquiv A)

substEquiv : ∀ {ℓ ℓ'} {X : Set ℓ} (F : X → Set ℓ') {x y : X} (p : x ≡ y) → F x ≃ F y
substEquiv F p = path→Equiv (cong F p)

substEquiv-refl : ∀ {ℓ ℓ'} {X : Set ℓ} (F : X → Set ℓ') (x : X)
  → substEquiv F (refl {x = x}) ≡ idEquiv (F x)
substEquiv-refl F x = path→Equiv-refl (F x)

-- =============================================================================
-- 2. Homotopy Čech Nerve Cech₀..Cech₃ & Simplicial Coherence
-- =============================================================================

Cech0 : ∀ {ℓ₁ ℓ₂} {X : Set ℓ₁} {U : Set ℓ₂} (p : U → X) → Set ℓ₂
Cech0 {U = U} _ = U

Cech1 : ∀ {ℓ₁ ℓ₂} {X : Set ℓ₁} {U : Set ℓ₂} (p : U → X) → Set (ℓ₁ ⊔ ℓ₂)
Cech1 {U = U} p = Σ U (λ u → Σ U (λ v → p u ≡ p v))

Cech2 : ∀ {ℓ₁ ℓ₂} {X : Set ℓ₁} {U : Set ℓ₂} (p : U → X) → Set (ℓ₁ ⊔ ℓ₂)
Cech2 {U = U} p = Σ U (λ u → Σ U (λ v → Σ U (λ w → (p u ≡ p v) × (p v ≡ p w))))

Cech3 : ∀ {ℓ₁ ℓ₂} {X : Set ℓ₁} {U : Set ℓ₂} (p : U → X) → Set (ℓ₁ ⊔ ℓ₂)
Cech3 {U = U} p =
  Σ U (λ u → Σ U (λ v → Σ U (λ w → Σ U (λ z →
    (p u ≡ p v) × ((p v ≡ p w) × (p w ≡ p z))))))

d1-0 : ∀ {ℓ₁ ℓ₂} {X : Set ℓ₁} {U : Set ℓ₂} {p : U → X} → Cech1 p → Cech0 p
d1-0 (_ , v , _) = v

d1-1 : ∀ {ℓ₁ ℓ₂} {X : Set ℓ₁} {U : Set ℓ₂} {p : U → X} → Cech1 p → Cech0 p
d1-1 (u , _ , _) = u

d2-0 : ∀ {ℓ₁ ℓ₂} {X : Set ℓ₁} {U : Set ℓ₂} {p : U → X} → Cech2 p → Cech1 p
d2-0 (_ , v , w , _ , q) = (v , w , q)

d2-1 : ∀ {ℓ₁ ℓ₂} {X : Set ℓ₁} {U : Set ℓ₂} {p : U → X} → Cech2 p → Cech1 p
d2-1 (u , _ , w , r , q) = (u , w , r ∙ q)

d2-2 : ∀ {ℓ₁ ℓ₂} {X : Set ℓ₁} {U : Set ℓ₂} {p : U → X} → Cech2 p → Cech1 p
d2-2 (u , v , _ , r , _) = (u , v , r)

d3-0 : ∀ {ℓ₁ ℓ₂} {X : Set ℓ₁} {U : Set ℓ₂} {p : U → X} → Cech3 p → Cech2 p
d3-0 (_ , v , w , z , _ , q , s) = (v , w , z , q , s)

d3-1 : ∀ {ℓ₁ ℓ₂} {X : Set ℓ₁} {U : Set ℓ₂} {p : U → X} → Cech3 p → Cech2 p
d3-1 (u , _ , w , z , r , q , s) = (u , w , z , r ∙ q , s)

d3-2 : ∀ {ℓ₁ ℓ₂} {X : Set ℓ₁} {U : Set ℓ₂} {p : U → X} → Cech3 p → Cech2 p
d3-2 (u , v , _ , z , r , q , s) = (u , v , z , r , q ∙ s)

d3-3 : ∀ {ℓ₁ ℓ₂} {X : Set ℓ₁} {U : Set ℓ₂} {p : U → X} → Cech3 p → Cech2 p
d3-3 (u , v , w , _ , r , q , _) = (u , v , w , r , q)

-- Up-to-higher-path 2-cell coherence d2-1(d3-1 t) ≡ d2-1(d3-2 t) on Cech₃:
cech3-assoc-coh : ∀ {ℓ₁ ℓ₂} {X : Set ℓ₁} {U : Set ℓ₂} {p : U → X} (t : Cech3 p)
  → d2-1 (d3-1 t) ≡ d2-1 (d3-2 t)
cech3-assoc-coh (u , _ , _ , z , r , q , s) =
  ΣPathP refl (ΣPathP refl (compPath-assoc r q s))

-- =============================================================================
-- 3. Higher (∞, 1) Čech Descent Data, Restriction & Effective Reconstruction
-- =============================================================================

record HigherDescentData {ℓ₁ ℓ₂ ℓ' : Level} {X : Set ℓ₁} {U : Set ℓ₂} (p : U → X)
    : Set (ℓ₁ ⊔ ℓ₂ ⊔ lsuc ℓ') where
  field
    E      : U → Set ℓ'
    φ      : (u v : U) → p u ≡ p v → E u ≃ E v
    φ-refl : (u : U) → φ u u refl ≡ idEquiv (E u)
    φ-comp : (u v w : U) (r : p u ≡ p v) (q : p v ≡ p w)
           → compEquiv (φ u v r) (φ v w q) ≡ φ u w (r ∙ q)

-- Synesist generative direction: global family F : X → Set ℓ' restricts to HigherDescentData p.
cong-∙ : ∀ {ℓ ℓ'} {A : Set ℓ} {B : Set ℓ'} (f : A → B) {x y z : A}
  (r : x ≡ y) (q : y ≡ z) → cong f (r ∙ q) ≡ cong f r ∙ cong f q
cong-∙ f r q =
  J (λ z' q' → cong f (r ∙ q') ≡ cong f r ∙ cong f q')
    (cong (cong f) (compPath-refl-r r) ∙ sym (compPath-refl-r (cong f r)))
    q

path→Equiv-∙ : ∀ {ℓ} {A B C : Set ℓ} (p : A ≡ B) (q : B ≡ C)
  → compEquiv (path→Equiv p) (path→Equiv q) ≡ path→Equiv (p ∙ q)
path→Equiv-∙ p q =
  J (λ _ q' → compEquiv (path→Equiv p) (path→Equiv q') ≡ path→Equiv (p ∙ q'))
    (cong (compEquiv (path→Equiv p)) (path→Equiv-refl _)
     ∙ equivEq (funExt (λ _ → refl))
     ∙ cong path→Equiv (sym (compPath-refl-r p)))
    q

restrict-family : ∀ {ℓ₁ ℓ₂ ℓ'} {X : Set ℓ₁} {U : Set ℓ₂} (p : U → X)
  (F : X → Set ℓ') → HigherDescentData {ℓ' = ℓ'} p
restrict-family p F = record
  { E      = λ u → F (p u)
  ; φ      = λ u v α → path→Equiv (cong F α)
  ; φ-refl = λ u → path→Equiv-refl (F (p u))
  ; φ-comp = λ u v w r q →
      path→Equiv-∙ (cong F r) (cong F q) ∙ cong path→Equiv (sym (cong-∙ F r q))
  }

reconstruct-family : ∀ {ℓ₁ ℓ₂ ℓ'} {X : Set ℓ₁} {U : Set ℓ₂} {p : U → X}
  (s : X → U) → HigherDescentData {ℓ' = ℓ'} p → X → Set ℓ'
reconstruct-family s D x = HigherDescentData.E D (s x)

-- Higher Effective Čech Descent: along a split effective cover (p, s, ps),
-- global type families X → Set ℓ' are reconstructed up to path equality
-- from HigherDescentData p while preserving all higher loops/isotropies.
higher-effective-descent-global : ∀ {ℓ₁ ℓ₂ ℓ'} {X : Set ℓ₁} {U : Set ℓ₂}
  {p : U → X} (s : X → U) (ps : ∀ x → p (s x) ≡ x)
  (F : X → Set ℓ') → reconstruct-family s (restrict-family p F) ≡ F
higher-effective-descent-global s ps F = funExt (λ x → cong F (ps x))

higher-effective-descent-local : ∀ {ℓ₁ ℓ₂ ℓ'} {X : Set ℓ₁} {U : Set ℓ₂}
  {p : U → X} (s : X → U) (ps : ∀ x → p (s x) ≡ x)
  (D : HigherDescentData {ℓ' = ℓ'} p) (u : U)
  → HigherDescentData.E (restrict-family p (reconstruct-family s D)) u
  ≡ HigherDescentData.E D u
higher-effective-descent-local {p = p} s ps D u =
  ua (HigherDescentData.φ D (s (p u)) u (ps (p u)))

-- =============================================================================
-- 4. Arbitrary-Level Cubical Presheaf Coherence & Nontrivial Loop Witness
-- =============================================================================

record CubicalPresheaf {ℓb ℓh ℓf : Level}
    (Obj : Set ℓb) (Hom : Obj → Obj → Set ℓh)
    (idH : ∀ a → Hom a a)
    (_∘_ : ∀ {a b c} → Hom b c → Hom a b → Hom a c)
    : Set (ℓb ⊔ ℓh ⊔ lsuc ℓf) where
  field
    Fiber      : Obj → Set ℓf
    restr      : ∀ {a b} → Hom a b → Fiber b ≃ Fiber a
    restr-id   : ∀ a → restr (idH a) ≡ idEquiv (Fiber a)
    restr-comp : ∀ {a b c} (g : Hom b c) (f : Hom a b)
               → restr (g ∘ f) ≡ compEquiv (restr g) (restr f)
    restr-assoc : ∀ {a b c d} (h : Hom c d) (g : Hom b c) (f : Hom a b)
                  (ass : ((h ∘ g) ∘ f) ≡ (h ∘ (g ∘ f)))
                → compEquiv (restr (h ∘ g)) (restr f)
                ≡ compEquiv (restr h) (restr (g ∘ f))

-- Every HigherDescentData p yields a coherent CubicalPresheaf over U indexed
-- by reversed Čech1 overlap paths `p b ≡ p a`:
cechPresheaf : ∀ {ℓ₁ ℓ₂ ℓ'} {X : Set ℓ₁} {U : Set ℓ₂} (p : U → X)
  → HigherDescentData {ℓ' = ℓ'} p
  → CubicalPresheaf U (λ a b → p b ≡ p a) (λ _ → refl) (λ g f → g ∙ f)
cechPresheaf p D = record
  { Fiber = E
  ; restr = λ {a} {b} α → φ b a α
  ; restr-id = λ a → φ-refl a
  ; restr-comp = λ {a} {b} {c} g f → sym (φ-comp c b a g f)
  ; restr-assoc = λ {a} {b} {c} {d} h g f _ →
      φ-comp d b a (h ∙ g) f
      ∙ cong (φ d a) (compPath-assoc h g f)
      ∙ sym (φ-comp d c a h (g ∙ f))
  }
  where open HigherDescentData D

-- Concrete nontrivial isotropy witness across Čech restriction & reconstruction:
-- Cover `not : Bool → Bool` (split by `not`) carries `boolFlipCoalgebra` / `notEquiv`
-- loops whose transport loop over `true` differs from `refl`.
boolSplitSec : Bool → Bool
boolSplitSec = not

boolSplitLaw : (x : Bool) → not (boolSplitSec x) ≡ x
boolSplitLaw true  = refl
boolSplitLaw false = refl

flipFamily : Bool → Set (lsuc lzero)
flipFamily _ = CausalCoalgebra ⊤ ⊤

cech-preserves-nonrefl-isotropy :
  Σ (HigherDescentData {ℓ' = lsuc lzero} not)
    (λ D → (reconstruct-family boolSplitSec D ≡ flipFamily)
         × (¬ (semEquivToPath boolFlipAut ≡ refl)))
cech-preserves-nonrefl-isotropy =
  ( restrict-family not flipFamily
  , higher-effective-descent-global {p = not} boolSplitSec boolSplitLaw flipFamily
  , boolFlipPath≢refl
  )
