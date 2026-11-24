{-# OPTIONS --cubical=full #-}
module Semplex.Cubical.InductiveHigherHorn where

open import Agda.Primitive
open import Agda.Primitive.Cubical
open import Agda.Builtin.Cubical.Path
open import Semplex.Cubical.Primitives
open import Semplex.Cubical.BGClassifyingSpace
open import Semplex.Cubical.HomotopyProfileFiber
open import Semplex.Cubical.SimplicialKanNerve
open import Semplex.Cubical.HigherHornCoherence

-- =============================================================================
-- 1. Zero-Stdlib Arithmetic, Non-Indexed Fin, Ordering, and Decidability
-- =============================================================================

infixr 4 _×_
_×_ : {ℓ₁ ℓ₂ : Level} → Set ℓ₁ → Set ℓ₂ → Set (ℓ₁ ⊔ ℓ₂)
A × B = Σ A (λ _ → B)

infixr 2 _⊎_
data _⊎_ {ℓ₁ ℓ₂ : Level} (A : Set ℓ₁) (B : Set ℓ₂) : Set (ℓ₁ ⊔ ℓ₂) where
  inl : A → A ⊎ B
  inr : B → A ⊎ B

data ℕ : Set where
  zero : ℕ
  suc  : ℕ → ℕ

add4 : ℕ → ℕ
add4 m = suc (suc (suc (suc m)))

add5 : ℕ → ℕ
add5 m = suc (add4 m)

-- Recursive non-indexed Fin avoids indexed constructor injectivity warnings in Cubical Agda.
Fin : ℕ → Set
Fin zero    = ⊥
Fin (suc n) = ⊤ ⊎ Fin n

fzero : {n : ℕ} → Fin (suc n)
fzero = inl tt

fsuc : {n : ℕ} → Fin n → Fin (suc n)
fsuc = inr

toNat : {n : ℕ} → Fin n → ℕ
toNat {suc n} (inl tt) = zero
toNat {suc n} (inr i)  = suc (toNat i)

infix 4 _≤ₙ_
_≤ₙ_ : ℕ → ℕ → Set
zero  ≤ₙ _     = ⊤
suc _ ≤ₙ zero  = ⊥
suc m ≤ₙ suc n = m ≤ₙ n

isProp-≤ₙ : (m n : ℕ) → isProp (m ≤ₙ n)
isProp-≤ₙ zero _ tt tt = refl
isProp-≤ₙ (suc _) zero () _
isProp-≤ₙ (suc m) (suc n) = isProp-≤ₙ m n

infix 4 _≢_
_≢_ : {ℓ : Level} {A : Set ℓ} → A → A → Set ℓ
x ≢ y = ¬ (x ≡ y)

≢-sym : {ℓ : Level} {A : Set ℓ} {x y : A} → x ≢ y → y ≢ x
≢-sym h eq = h (sym eq)

data Dec {ℓ : Level} (A : Set ℓ) : Set ℓ where
  yes : A → Dec A
  no  : ¬ A → Dec A

private
  isInlTag : {n : ℕ} → Fin (suc n) → Set
  isInlTag (inl _) = ⊤
  isInlTag (inr _) = ⊥

  isInrTag : {n : ℕ} → Fin (suc n) → Set
  isInrTag (inl _) = ⊥
  isInrTag (inr _) = ⊤

  unInr : {n : ℕ} → Fin n → Fin (suc n) → Fin n
  unInr d (inl _) = d
  unInr _ (inr j) = j

decEqFin : {n : ℕ} (i j : Fin n) → Dec (i ≡ j)
decEqFin {zero} () _
decEqFin {suc n} (inl tt) (inl tt) = yes refl
decEqFin {suc n} (inl tt) (inr j)  = no (λ p → subst isInlTag p tt)
decEqFin {suc n} (inr i)  (inl tt) = no (λ p → subst isInrTag p tt)
decEqFin {suc n} (inr i)  (inr j)  with decEqFin i j
... | yes p  = yes (cong inr p)
... | no ¬p  = no (λ eq → ¬p (cong (unInr i) eq))

-- =============================================================================
-- 2. Constructive 5-vs-4 Pigeonhole Face Selector (Exact Separation at n ≥ 4)
-- =============================================================================

AllDiff2 : {A : Set} → A → A → Set
AllDiff2 a b = a ≢ b

AllDiff3 : {A : Set} → A → A → A → Set
AllDiff3 a b c = (a ≢ b) × ((a ≢ c) × (b ≢ c))

AllDiff4 : {A : Set} → A → A → A → A → Set
AllDiff4 a b c d = (a ≢ b) × ((a ≢ c) × ((a ≢ d) × AllDiff3 b c d))

AllDiff5 : {A : Set} → A → A → A → A → A → Set
AllDiff5 a b c d e = (a ≢ b) × ((a ≢ c) × ((a ≢ d) × ((a ≢ e) × AllDiff4 b c d e)))

private
  avoid1 : {n : ℕ} (c0 c1 : Fin n) → AllDiff2 c0 c1 →
    (t0 : Fin n) → Σ (Fin n) (λ j → (j ≢ t0) × (j ≡ c0 ⊎ j ≡ c1))
  avoid1 c0 c1 d01 t0 with decEqFin c0 t0
  ... | no  c0≠t0 = c0 , (c0≠t0 , inl refl)
  ... | yes c0≡t0 = c1 , ((λ c1≡t0 → d01 (c0≡t0 ∙ sym c1≡t0)) , inr refl)

  avoid2 : {n : ℕ} (c0 c1 c2 : Fin n) → AllDiff3 c0 c1 c2 →
    (t0 t1 : Fin n) →
    Σ (Fin n) (λ j → (j ≢ t0) × ((j ≢ t1) × (j ≡ c0 ⊎ (j ≡ c1 ⊎ j ≡ c2))))
  avoid2 c0 c1 c2 (d01 , (d02 , d12)) t0 t1 with decEqFin c0 t0
  ... | yes c0≡t0 with avoid1 c1 c2 d12 t1
  ...   | j , (j≠t1 , inl j≡c1) =
      j , ((λ j≡t0 → d01 (c0≡t0 ∙ sym (sym j≡c1 ∙ j≡t0))) , (j≠t1 , inr (inl j≡c1)))
  ...   | j , (j≠t1 , inr j≡c2) =
      j , ((λ j≡t0 → d02 (c0≡t0 ∙ sym (sym j≡c2 ∙ j≡t0))) , (j≠t1 , inr (inr j≡c2)))
  avoid2 c0 c1 c2 (d01 , (d02 , d12)) t0 t1 | no c0≠t0 with decEqFin c0 t1
  ... | no  c0≠t1 = c0 , (c0≠t0 , (c0≠t1 , inl refl))
  ... | yes c0≡t1 with avoid1 c1 c2 d12 t0
  ...   | j , (j≠t0 , inl j≡c1) =
      j , (j≠t0 , ((λ j≡t1 → d01 (c0≡t1 ∙ sym (sym j≡c1 ∙ j≡t1))) , inr (inl j≡c1)))
  ...   | j , (j≠t0 , inr j≡c2) =
      j , (j≠t0 , ((λ j≡t1 → d02 (c0≡t1 ∙ sym (sym j≡c2 ∙ j≡t1))) , inr (inr j≡c2)))

  liftNeq3 : {A : Set} {c0 c1 c2 c3 j t : A} →
    c0 ≢ c1 → c0 ≢ c2 → c0 ≢ c3 → c0 ≡ t →
    (j ≡ c1 ⊎ (j ≡ c2 ⊎ j ≡ c3)) → j ≢ t
  liftNeq3 d01 _ _ eq (inl p) q = d01 (eq ∙ sym q ∙ p)
  liftNeq3 _ d02 _ eq (inr (inl p)) q = d02 (eq ∙ sym q ∙ p)
  liftNeq3 _ _ d03 eq (inr (inr p)) q = d03 (eq ∙ sym q ∙ p)

  avoid3 : {n : ℕ} (c0 c1 c2 c3 : Fin n) → AllDiff4 c0 c1 c2 c3 →
    (t0 t1 t2 : Fin n) →
    Σ (Fin n) (λ j →
      (j ≢ t0) × ((j ≢ t1) × ((j ≢ t2) × (j ≡ c0 ⊎ (j ≡ c1 ⊎ (j ≡ c2 ⊎ j ≡ c3))))))
  avoid3 c0 c1 c2 c3 (d01 , (d02 , (d03 , d123))) t0 t1 t2 with decEqFin c0 t0
  ... | yes c0≡t0 with avoid2 c1 c2 c3 d123 t1 t2
  ...   | j , (j≠t1 , (j≠t2 , mem)) =
      j , (liftNeq3 d01 d02 d03 c0≡t0 mem , (j≠t1 , (j≠t2 , inr mem)))
  avoid3 c0 c1 c2 c3 (d01 , (d02 , (d03 , d123))) t0 t1 t2 | no c0≠t0 with decEqFin c0 t1
  ... | yes c0≡t1 with avoid2 c1 c2 c3 d123 t0 t2
  ...   | j , (j≠t0 , (j≠t2 , mem)) =
      j , (j≠t0 , (liftNeq3 d01 d02 d03 c0≡t1 mem , (j≠t2 , inr mem)))
  avoid3 c0 c1 c2 c3 (d01 , (d02 , (d03 , d123))) t0 t1 t2 | no c0≠t0 | no c0≠t1 with decEqFin c0 t2
  ... | no c0≠t2 = c0 , (c0≠t0 , (c0≠t1 , (c0≠t2 , inl refl)))
  ... | yes c0≡t2 with avoid2 c1 c2 c3 d123 t0 t1
  ...   | j , (j≠t0 , (j≠t1 , mem)) =
      j , (j≠t0 , (j≠t1 , (liftNeq3 d01 d02 d03 c0≡t2 mem , inr mem)))

  liftNeq4 : {A : Set} {c0 c1 c2 c3 c4 j t : A} →
    c0 ≢ c1 → c0 ≢ c2 → c0 ≢ c3 → c0 ≢ c4 → c0 ≡ t →
    (j ≡ c1 ⊎ (j ≡ c2 ⊎ (j ≡ c3 ⊎ j ≡ c4))) → j ≢ t
  liftNeq4 d01 _ _ _ eq (inl p) q = d01 (eq ∙ sym q ∙ p)
  liftNeq4 _ d02 _ _ eq (inr (inl p)) q = d02 (eq ∙ sym q ∙ p)
  liftNeq4 _ _ d03 _ eq (inr (inr (inl p))) q = d03 (eq ∙ sym q ∙ p)
  liftNeq4 _ _ _ d04 eq (inr (inr (inr p))) q = d04 (eq ∙ sym q ∙ p)

  avoid4 : {n : ℕ} (c0 c1 c2 c3 c4 : Fin n) → AllDiff5 c0 c1 c2 c3 c4 →
    (t0 t1 t2 t3 : Fin n) →
    Σ (Fin n) (λ j → (j ≢ t0) × ((j ≢ t1) × ((j ≢ t2) × (j ≢ t3))))
  avoid4 c0 c1 c2 c3 c4 (d01 , (d02 , (d03 , (d04 , d1234)))) t0 t1 t2 t3 with decEqFin c0 t0
  ... | yes eq0 with avoid3 c1 c2 c3 c4 d1234 t1 t2 t3
  ...   | j , (j≠t1 , (j≠t2 , (j≠t3 , mem))) =
      j , (liftNeq4 d01 d02 d03 d04 eq0 mem , (j≠t1 , (j≠t2 , j≠t3)))
  avoid4 c0 c1 c2 c3 c4 (d01 , (d02 , (d03 , (d04 , d1234)))) t0 t1 t2 t3 | no ≠0 with decEqFin c0 t1
  ... | yes eq1 with avoid3 c1 c2 c3 c4 d1234 t0 t2 t3
  ...   | j , (j≠t0 , (j≠t2 , (j≠t3 , mem))) =
      j , (j≠t0 , (liftNeq4 d01 d02 d03 d04 eq1 mem , (j≠t2 , j≠t3)))
  avoid4 c0 c1 c2 c3 c4 (d01 , (d02 , (d03 , (d04 , d1234)))) t0 t1 t2 t3 | no ≠0 | no ≠1 with decEqFin c0 t2
  ... | yes eq2 with avoid3 c1 c2 c3 c4 d1234 t0 t1 t3
  ...   | j , (j≠t0 , (j≠t1 , (j≠t3 , mem))) =
      j , (j≠t0 , (j≠t1 , (liftNeq4 d01 d02 d03 d04 eq2 mem , j≠t3)))
  avoid4 c0 c1 c2 c3 c4 (d01 , (d02 , (d03 , (d04 , d1234)))) t0 t1 t2 t3 | no ≠0 | no ≠1 | no ≠2 with decEqFin c0 t3
  ... | no ≠3 = c0 , (≠0 , (≠1 , (≠2 , ≠3)))
  ... | yes eq3 with avoid3 c1 c2 c3 c4 d1234 t0 t1 t2
  ...   | j , (j≠t0 , (j≠t1 , (j≠t2 , mem))) =
      j , (j≠t0 , (j≠t1 , (j≠t2 , liftNeq4 d01 d02 d03 d04 eq3 mem)))

  inr-inj : {n : ℕ} {i j : Fin n} → fsuc i ≡ fsuc j → i ≡ j
  inr-inj {i = i} eq = cong (unInr i) eq

  fsuc-allDiff2 : {n : ℕ} {a b : Fin n} → AllDiff2 a b → AllDiff2 (fsuc a) (fsuc b)
  fsuc-allDiff2 d eq = d (inr-inj eq)

  fsuc-allDiff3 : {n : ℕ} {a b c : Fin n} → AllDiff3 a b c → AllDiff3 (fsuc a) (fsuc b) (fsuc c)
  fsuc-allDiff3 (d01 , (d02 , d12)) = fsuc-allDiff2 d01 , (fsuc-allDiff2 d02 , fsuc-allDiff2 d12)

  fsuc-allDiff4 : {n : ℕ} {a b c d : Fin n} → AllDiff4 a b c d →
    AllDiff4 (fsuc a) (fsuc b) (fsuc c) (fsuc d)
  fsuc-allDiff4 (d01 , (d02 , (d03 , d123))) =
    fsuc-allDiff2 d01 , (fsuc-allDiff2 d02 , (fsuc-allDiff2 d03 , fsuc-allDiff3 d123))

find-avoiding-face : (m : ℕ) (k a b c : Fin (add5 m)) →
  Σ (Fin (add5 m)) (λ j → (j ≢ k) × ((a ≢ j) × ((b ≢ j) × (c ≢ j))))
find-avoiding-face m k a b c =
  let j , (jk , (ja , (jb , jc))) = avoid4 v0 v1 v2 v3 v4 diff5 k a b c
  in j , (jk , (≢-sym ja , (≢-sym jb , ≢-sym jc)))
  where
  v0 v1 v2 v3 v4 : Fin (add5 m)
  v0 = fzero
  v1 = fsuc fzero
  v2 = fsuc (fsuc fzero)
  v3 = fsuc (fsuc (fsuc fzero))
  v4 = fsuc (fsuc (fsuc (fsuc fzero)))
  f0≠s : {n : ℕ} {x : Fin n} → fzero ≢ fsuc x
  f0≠s p = subst isInlTag p tt
  diff5 : AllDiff5 v0 v1 v2 v3 v4
  diff5 =
    f0≠s , (f0≠s , (f0≠s , (f0≠s ,
      fsuc-allDiff4 (f0≠s , (f0≠s , (f0≠s ,
        fsuc-allDiff3 (f0≠s , (f0≠s ,
          fsuc-allDiff2 f0≠s))))))))

dim3-no-avoiding-face : ¬ Σ (Fin (add4 zero)) (λ j →
  (j ≢ inl tt) ×
  ((j ≢ inr (inl tt)) ×
  ((j ≢ inr (inr (inl tt))) ×
   (j ≢ inr (inr (inr (inl tt)))))))
dim3-no-avoiding-face (inl tt , (h0 , _)) = h0 refl
dim3-no-avoiding-face (inr (inl tt) , (_ , (h1 , _))) = h1 refl
dim3-no-avoiding-face (inr (inr (inl tt)) , (_ , (_ , (h2 , _)))) = h2 refl
dim3-no-avoiding-face (inr (inr (inr (inl tt))) , (_ , (_ , (_ , h3)))) = h3 refl
dim3-no-avoiding-face (inr (inr (inr (inr ()))) , _)

-- =============================================================================
-- 3. 2-Coskeletal ∞-Simplicial Nerve, General n-Horns, & Contraction for n ≥ 4
-- =============================================================================

IsPropTri : Simplicial2 → Set
IsPropTri S =
  {x y z : Simplicial2.Obj S}
  {f : Simplicial2.Hom S x y}
  {g : Simplicial2.Hom S y z}
  {h : Simplicial2.Hom S x z} →
  isProp (Simplicial2.Tri S f g h)

EdgeOf : (S : Simplicial2) (n : ℕ) → (Fin (suc n) → Simplicial2.Obj S) → Set
EdgeOf S n v =
  (i j : Fin (suc n)) → (toNat i ≤ₙ toNat j) → Simplicial2.Hom S (v i) (v j)

TriOf : (S : Simplicial2) (n : ℕ)
  (v : Fin (suc n) → Simplicial2.Obj S) → EdgeOf S n v → Set
TriOf S n v e =
  (a b c : Fin (suc n)) →
  (p : toNat a ≤ₙ toNat b) →
  (q : toNat b ≤ₙ toNat c) →
  (r : toNat a ≤ₙ toNat c) →
  Simplicial2.Tri S (e a b p) (e b c q) (e a c r)

record Cosk2 (S : Simplicial2) (n : ℕ) : Set where
  constructor mkCosk2
  field
    vert : Fin (suc n) → Simplicial2.Obj S
    edge : EdgeOf S n vert
    tri  : TriOf S n vert edge

FaceTriOf : (S : Simplicial2) (n : ℕ) (k : Fin (suc n))
  (v : Fin (suc n) → Simplicial2.Obj S) → EdgeOf S n v → Set
FaceTriOf S n k v e =
  (j : Fin (suc n)) → (j ≢ k) →
  (a b c : Fin (suc n)) → (a ≢ j) → (b ≢ j) → (c ≢ j) →
  (p : toNat a ≤ₙ toNat b) →
  (q : toNat b ≤ₙ toNat c) →
  (r : toNat a ≤ₙ toNat c) →
  Simplicial2.Tri S (e a b p) (e b c q) (e a c r)

record Horn2 (S : Simplicial2) (n : ℕ) (k : Fin (suc n)) : Set where
  constructor mkHorn2
  field
    vert    : Fin (suc n) → Simplicial2.Obj S
    edge    : EdgeOf S n vert
    faceTri : FaceTriOf S n k vert edge

hornOfSimplex : {S : Simplicial2} {n : ℕ} {k : Fin (suc n)} →
  Cosk2 S n → Horn2 S n k
hornOfSimplex σ = record
  { vert    = Cosk2.vert σ
  ; edge    = Cosk2.edge σ
  ; faceTri = λ _ _ a b c _ _ _ p q r → Cosk2.tri σ a b c p q r
  }

HornFiller : (S : Simplicial2) (n : ℕ) (k : Fin (suc n)) (H : Horn2 S n k) → Set
HornFiller S n k H = fiber (hornOfSimplex {S} {n} {k}) H

fillHornSimplex : {S : Simplicial2} {m : ℕ} {k : Fin (add5 m)} →
  Horn2 S (add4 m) k → Cosk2 S (add4 m)
fillHornSimplex {m = m} {k = k} H = record
  { vert = Horn2.vert H
  ; edge = Horn2.edge H
  ; tri  = λ a b c p q r →
      let j , (jk , (aj , (bj , cj))) = find-avoiding-face m k a b c
      in Horn2.faceTri H j jk a b c aj bj cj p q r
  }

private
  isProp-TriOf : {S : Simplicial2} → IsPropTri S → {n : ℕ}
    (v : Fin (suc n) → Simplicial2.Obj S) (e : EdgeOf S n v) →
    isProp (TriOf S n v e)
  isProp-TriOf {S = S} isP v e t₁ t₂ =
    funExt λ a → funExt λ b → funExt λ c →
    funExt λ p → funExt λ q → funExt λ r →
      isP (t₁ a b c p q r) (t₂ a b c p q r)

  isProp-FaceTriOf : {S : Simplicial2} → IsPropTri S → {n : ℕ} (k : Fin (suc n))
    (v : Fin (suc n) → Simplicial2.Obj S) (e : EdgeOf S n v) →
    isProp (FaceTriOf S n k v e)
  isProp-FaceTriOf {S = S} isP k v e ft₁ ft₂ =
    funExt λ j → funExt λ jk → funExt λ a → funExt λ b → funExt λ c →
    funExt λ aj → funExt λ bj → funExt λ cj →
    funExt λ p → funExt λ q → funExt λ r →
      isP (ft₁ j jk a b c aj bj cj p q r) (ft₂ j jk a b c aj bj cj p q r)

  isProp→CohSquare : {ℓ : Level} {A : Set ℓ} (p : isProp A)
    {f : I → A} {b : A} (lhs : f i0 ≡ b) (rhs : f i1 ≡ b) →
    PathP (λ i → f i ≡ b) lhs rhs
  isProp→CohSquare p {f = f} {b = b} lhs rhs i j =
    primHComp
      (λ k → λ
        { (i = i0) → p b (lhs j) k
        ; (i = i1) → p b (rhs j) k
        ; (j = i0) → p b (f i) k
        ; (j = i1) → p b b k
        })
      b

Cosk2-Horn2-HalfAdjointEquiv : {S : Simplicial2} → IsPropTri S →
  (m : ℕ) (k : Fin (add5 m)) →
  HalfAdjointEquiv (Cosk2 S (add4 m)) (Horn2 S (add4 m) k)
Cosk2-Horn2-HalfAdjointEquiv {S = S} isP m k = record
  { to   = hornOfSimplex {S} {add4 m} {k}
  ; from = fillHornSimplex {S} {m} {k}
  ; sec  = λ H →
      cong (mkHorn2 {S} {add4 m} {k} (Horn2.vert H) (Horn2.edge H)) (secFT H)
  ; ret  = retPath
  ; coh  = λ σ i →
      let ftCurve : I → FaceTriOf S (add4 m) k (Cosk2.vert σ) (Cosk2.edge σ)
          ftCurve t = Horn2.faceTri (hornOfSimplex {S} {add4 m} {k} (retPath σ t))
          lhs = secFT (hornOfSimplex {S} {add4 m} {k} σ)
      in cong (mkHorn2 {S} {add4 m} {k} (Cosk2.vert σ) (Cosk2.edge σ))
           (isProp→CohSquare
             (isProp-FaceTriOf {S} isP k (Cosk2.vert σ) (Cosk2.edge σ))
             {f = ftCurve}
             {b = Horn2.faceTri (hornOfSimplex {S} {add4 m} {k} σ)}
             lhs
             refl
             i)
  }
  where
  secFT : (H : Horn2 S (add4 m) k) →
    Horn2.faceTri (hornOfSimplex {S} {add4 m} {k} (fillHornSimplex {S} {m} {k} H)) ≡
    Horn2.faceTri H
  secFT H =
    isProp-FaceTriOf {S} isP k (Horn2.vert H) (Horn2.edge H)
      (Horn2.faceTri (hornOfSimplex {S} {add4 m} {k} (fillHornSimplex {S} {m} {k} H)))
      (Horn2.faceTri H)

  retPath : (σ : Cosk2 S (add4 m)) →
    fillHornSimplex {S} {m} {k} (hornOfSimplex {S} {add4 m} {k} σ) ≡ σ
  retPath σ =
    cong (mkCosk2 {S} {add4 m} (Cosk2.vert σ) (Cosk2.edge σ))
      (isProp-TriOf {S} isP (Cosk2.vert σ) (Cosk2.edge σ)
        (Cosk2.tri (fillHornSimplex {S} {m} {k} (hornOfSimplex {S} {add4 m} {k} σ)))
        (Cosk2.tri σ))

Cosk2-fills-all-horns-ge-4 : {S : Simplicial2} → IsPropTri S →
  (m : ℕ) (k : Fin (add5 m)) (H : Horn2 S (add4 m) k) →
  HornFiller S (add4 m) k H
Cosk2-fills-all-horns-ge-4 isP m k H =
  let eqv = Cosk2-Horn2-HalfAdjointEquiv isP m k
  in HalfAdjointEquiv.from eqv H , HalfAdjointEquiv.sec eqv H

Cosk2-filler-contr-ge-4 : {S : Simplicial2} → IsPropTri S →
  (m : ℕ) (k : Fin (add5 m)) (H : Horn2 S (add4 m) k) →
  isContr (HornFiller S (add4 m) k H)
Cosk2-filler-contr-ge-4 isP m k H =
  halfAdjointEquiv→isContrFiber (Cosk2-Horn2-HalfAdjointEquiv isP m k) H

-- =============================================================================
-- 4. Specializations: Classifying Spaces BG G and Semigroup U₂ Stabilization
-- =============================================================================

typePathNerve-isPropTri : {A : Set} → isGroupoid A → IsPropTri (typePathNerve A)
typePathNerve-isPropTri isGrp {x} {_} {z} {f} {g} {h} =
  isGrp x z (f ∙ g) h

monoidNerve-isPropTri : (M : SetMonoid) → IsPropTri (monoidNerve M)
monoidNerve-isPropTri M {x} {y} {z} {f} {g} {h} p q =
  SetMonoid.isSet-Carrier M (SetMonoid.mul M f g) h p q

BG-isKan-all-dims : (G : SetGroup) →
  IsKan3 (typePathNerve3 (BG G)) ×
  ((m : ℕ) (k : Fin (add5 m)) (H : Horn2 (typePathNerve (BG G)) (add4 m) k) →
    isContr (HornFiller (typePathNerve (BG G)) (add4 m) k H))
BG-isKan-all-dims G =
  BG-isKan3 G , Cosk2-filler-contr-ge-4 (typePathNerve-isPropTri (BG-isGroupoid G))

U2-stabilizes-at-dim-4 :
  HasInnerHorn2 (monoidNerve U2Monoid) ×
  ¬ HasOuterHorn2Left (monoidNerve U2Monoid) ×
  ¬ HasOuterHorn30 (monoidNerve3 U2Monoid) ×
  ((m : ℕ) (k : Fin (add5 m)) (H : Horn2 (monoidNerve U2Monoid) (add4 m) k) →
    isContr (HornFiller (monoidNerve U2Monoid) (add4 m) k H))
U2-stabilizes-at-dim-4 =
  U2-nerve-fills-innerHorn ,
  (U2-nerve-refutes-outerHornLeft ,
  (U2-nerve3-refutes-outerHorn0 ,
   (λ m k H → Cosk2-filler-contr-ge-4 {S = monoidNerve U2Monoid}
     (λ {x} {y} {z} {f} {g} {h} → isSet-U2Elem (u2Mul f g) h) m k H)))

BG-fills-all-4-horns : (G : SetGroup) (k : Fin (add5 zero))
  (H : Horn2 (typePathNerve (BG G)) (add4 zero) k) →
  isContr (HornFiller (typePathNerve (BG G)) (add4 zero) k H)
BG-fills-all-4-horns G k H = snd (BG-isKan-all-dims G) zero k H

U2-fills-all-4-horns : (k : Fin (add5 zero))
  (H : Horn2 (monoidNerve U2Monoid) (add4 zero) k) →
  isContr (HornFiller (monoidNerve U2Monoid) (add4 zero) k H)
U2-fills-all-4-horns k H = snd (snd (snd U2-stabilizes-at-dim-4)) zero k H
