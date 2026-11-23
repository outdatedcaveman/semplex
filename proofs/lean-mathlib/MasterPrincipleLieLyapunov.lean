/-
  Semplex Master Principle — Non-Posetal Kan Retract Obstruction,
  Exact Lie/Spectral Presentation Unitary Homomorphisms,
  Hoza Isolating-Weight Spanning Trees (NL=UL),
  and Clark Continuous Lyapunov Tangent Gramians (`gemini/master-principle-lie-lyapunov`).

  Isolated in `proofs/lean-mathlib/` (Mathlib v4.12.0) so `proofs/lean/` remains core Lean 4.
-/
import Mathlib.Data.Complex.Basic
import Mathlib.Data.Fintype.Card
import Mathlib.Data.Matrix.Basic
import Mathlib.Data.Real.Basic
import Mathlib.LinearAlgebra.Matrix.DotProduct
import Mathlib.LinearAlgebra.Matrix.Trace
import Mathlib.Tactic.FinCases
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Positivity

open scoped BigOperators Matrix

namespace Semplex.LieLyapunov

/-! ## 1. Non-Posetal Kan Retract Counterexample & 3-Regime Collapse -/
namespace KanRetractObstruction

abbrev ThreeObj := Fin 3

def extraMidObj : ThreeObj → Type
  | 0 => Bool
  | 1 => Bool ⊕ Unit
  | 2 => Bool

def threeMap (i j : ThreeObj) (h : i ≤ j) : extraMidObj i → extraMidObj j :=
  match i, j with
  | 0, 0 => id
  | 0, 1 => Sum.inl
  | 0, 2 => id
  | 1, 1 => id
  | 1, 2 => Sum.elim id (fun _ => true)
  | 2, 2 => id
  | 1, 0 => fun _ => absurd h (by decide)
  | 2, 0 => fun _ => absurd h (by decide)
  | 2, 1 => fun _ => absurd h (by decide)

structure ThreeFunctor where
  obj : ThreeObj → Type
  map : ∀ {i j : ThreeObj}, i ≤ j → obj i → obj j
  map_id : ∀ (i : ThreeObj) (x : obj i), map (le_refl i) x = x
  map_comp : ∀ {i j k : ThreeObj} (hij : i ≤ j) (hjk : j ≤ k) (x : obj i),
    map hjk (map hij x) = map (le_trans hij hjk) x

def constBoolFunctor : ThreeFunctor where
  obj := fun _ => Bool
  map := fun _ => id
  map_id := fun _ _ => rfl
  map_comp := fun _ _ _ => rfl

def extraMidFunctor : ThreeFunctor where
  obj := extraMidObj
  map := fun {i j} hij x => threeMap i j hij x
  map_id := by
    intro i x
    fin_cases i <;> rfl
  map_comp := by
    intro i j k hij hjk x
    fin_cases i <;> fin_cases j <;> fin_cases k
    all_goals try (exfalso; exact absurd hij (by decide))
    all_goals try (exfalso; exact absurd hjk (by decide))
    all_goals rfl

/-- On `{0, 2} ↪ (0 -> 1 -> 2)` with `v(0) = v(2) = Bool` and `v(0->2) = id`,
    pointwise `Lan_i v(1)` and `Ran_i v(1)` are canonically `Bool`. -/
def lanAt1EquivBool : Bool ≃ Bool := Equiv.refl Bool

def ranAt1EquivBool : Bool ≃ Bool := Equiv.refl Bool

theorem kan_comparison_at_1_is_id (b : Bool) :
    constBoolFunctor.map (by decide : (0 : ThreeObj) ≤ 2) b = b := rfl

private theorem cast_cast_symm {α β : Type} (h : α = β) (x : β) :
    cast h (cast h.symm x) = x := by
  subst h
  rfl

/-- Any `ThreeFunctor` whose `0→2` transition acts as the identity factors `id`
    through `F.obj 1`, forcing `Bool` to be a *retract* (not necessarily equivalent). -/
theorem extension_factors_identity (F : ThreeFunctor)
    (h0 : F.obj 0 = Bool) (h2 : F.obj 2 = Bool)
    (h_agree : ∀ x : F.obj 0,
      cast h2 (F.map (by decide : (0 : ThreeObj) ≤ 2) x) = cast h0 x)
    (b : Bool) :
    cast h2 (F.map (by decide : (1 : ThreeObj) ≤ 2)
      (F.map (by decide : (0 : ThreeObj) ≤ 1) (cast h0.symm b))) = b := by
  rw [F.map_comp (by decide : (0 : ThreeObj) ≤ 1) (by decide : (1 : ThreeObj) ≤ 2)]
  rw [h_agree (cast h0.symm b)]
  exact cast_cast_symm h0 b

theorem extraMidFunctor_restricts_to_v :
    extraMidFunctor.obj 0 = Bool ∧
    extraMidFunctor.obj 2 = Bool ∧
    (∀ b : Bool, extraMidFunctor.map (by decide : (0 : ThreeObj) ≤ 2) b = b) :=
  ⟨rfl, rfl, fun _ => rfl⟩

theorem extraMidFunctor_mid_not_equiv_bool :
    ¬ Nonempty (extraMidFunctor.obj 1 ≃ Bool) := by
  rintro ⟨e⟩
  have hc : Fintype.card (Bool ⊕ Unit) = Fintype.card Bool :=
    Fintype.card_congr e
  simp at hc

/-- **Main Countertheorem (`Task 143` `event 151841`):**
    Even when `can_1 : Lan_i v(1) -> Ran_i v(1)` is `id_Bool`, two functor extensions
    in `Type` (`Set` / `Spaces` 0-types) can agree identically on all observed probes `{0, 2}`
    and morphisms `0 → 2`, while having non-equivalent values at object `1`. -/
theorem kan_comparison_equiv_not_sufficient_in_type :
    ∃ (F G : ThreeFunctor),
      F.obj 0 = G.obj 0 ∧
      F.obj 2 = G.obj 2 ∧
      (∀ (x : F.obj 0) (y : G.obj 0),
        HEq x y →
        HEq (F.map (by decide : (0 : ThreeObj) ≤ 2) x)
            (G.map (by decide : (0 : ThreeObj) ≤ 2) y)) ∧
      ¬ Nonempty (F.obj 1 ≃ G.obj 1) := by
  refine ⟨extraMidFunctor, constBoolFunctor, rfl, rfl, ?_, extraMidFunctor_mid_not_equiv_bool⟩
  intro x y hxy
  simpa [extraMidFunctor, constBoolFunctor, threeMap] using hxy

/-- Regime 1 (Posetal antisymmetry): retracts collapse to equality in any partial order. -/
theorem posetal_retract_eq {α : Type*} [PartialOrder α] {l x u : α}
    (hl : l ≤ x) (hu : x ≤ u) (hcollapse : l = u) : x = l := by
  subst hcollapse
  exact le_antisymm hu hl

/-- Regime 2 (Essential image): any functor preserves equivalences `a ≃ b`,
    pinning intermediate values isomorphic to observed probes. -/
theorem essential_image_equiv_determined (F : ThreeFunctor) {a b : ThreeObj}
    (hab : a ≤ b) (hba : b ≤ a) :
    Nonempty (F.obj a ≃ F.obj b) := by
  have heq : a = b := le_antisymm hab hba
  subst heq
  exact ⟨Equiv.refl _⟩

end KanRetractObstruction


/-! ## 2. Exact Lie / Spectral Presentation Unitary Homomorphisms -/
namespace LiePresentationUnitary

def IsUnitary {d : ℕ} (U : Matrix (Fin d) (Fin d) ℂ) : Prop :=
  U * Uᴴ = 1 ∧ Uᴴ * U = 1

theorem isUnitary_one {d : ℕ} : IsUnitary (1 : Matrix (Fin d) (Fin d) ℂ) := by
  simp [IsUnitary]

theorem isUnitary_conjTranspose {d : ℕ} {U : Matrix (Fin d) (Fin d) ℂ}
    (hU : IsUnitary U) : IsUnitary (Uᴴ) := by
  refine ⟨?_, ?_⟩
  · simpa [Matrix.conjTranspose_conjTranspose] using hU.2
  · simpa [Matrix.conjTranspose_conjTranspose] using hU.1

theorem isUnitary_mul {d : ℕ} {U V : Matrix (Fin d) (Fin d) ℂ}
    (hU : IsUnitary U) (hV : IsUnitary V) : IsUnitary (U * V) := by
  refine ⟨?_, ?_⟩
  · calc
      (U * V) * (U * V)ᴴ = U * V * (Vᴴ * Uᴴ) := by rw [Matrix.conjTranspose_mul]
      _ = U * (V * Vᴴ) * Uᴴ := by simp [Matrix.mul_assoc]
      _ = U * 1 * Uᴴ := by rw [hV.1]
      _ = U * Uᴴ := by rw [Matrix.mul_one]
      _ = 1 := hU.1
  · calc
      (U * V)ᴴ * (U * V) = (Vᴴ * Uᴴ) * (U * V) := by rw [Matrix.conjTranspose_mul]
      _ = Vᴴ * (Uᴴ * U) * V := by simp [Matrix.mul_assoc]
      _ = Vᴴ * 1 * V := by rw [hU.2]
      _ = Vᴴ * V := by rw [Matrix.mul_one]
      _ = 1 := hV.2

theorem isUnitary_pow {d : ℕ} {U : Matrix (Fin d) (Fin d) ℂ}
    (hU : IsUnitary U) (k : ℕ) : IsUnitary (U ^ k) := by
  induction k with
  | zero => simp [isUnitary_one]
  | succ k ih =>
      rw [pow_succ']
      exact isUnitary_mul hU ih

theorem spectral_conjugate_unitary {d : ℕ} {V D : Matrix (Fin d) (Fin d) ℂ}
    (hV : IsUnitary V) (hD : IsUnitary D) : IsUnitary (V * D * Vᴴ) :=
  isUnitary_mul (isUnitary_mul hV hD) (isUnitary_conjTranspose hV)

theorem spectral_conjugate_pow {d : ℕ} {V D : Matrix (Fin d) (Fin d) ℂ}
    (hV : IsUnitary V) (k : ℕ) :
    (V * D * Vᴴ) ^ k = V * D ^ k * Vᴴ := by
  induction k with
  | zero => simp [hV.1]
  | succ k ih =>
      calc
        (V * D * Vᴴ) ^ (k + 1) = (V * D * Vᴴ) ^ k * (V * D * Vᴴ) := pow_succ _ k
        _ = (V * D ^ k * Vᴴ) * (V * D * Vᴴ) := by rw [ih]
        _ = V * D ^ k * (Vᴴ * V) * D * Vᴴ := by simp [Matrix.mul_assoc]
        _ = V * D ^ k * 1 * D * Vᴴ := by rw [hV.2]
        _ = V * (D ^ k * D) * Vᴴ := by simp [Matrix.mul_assoc]
        _ = V * D ^ (k + 1) * Vᴴ := by rw [pow_succ]

/-- Spectral torsion locking: conjugating any k-th root-of-unity diagonal `D^k = 1`
    by a learned unitary `V` guarantees `(V D Vᴴ)^k = 1` identically by construction. -/
theorem spectral_conjugate_torsion {d : ℕ} {V D : Matrix (Fin d) (Fin d) ℂ}
    (hV : IsUnitary V) {k : ℕ} (hDk : D ^ k = 1) :
    (V * D * Vᴴ) ^ k = 1 := by
  rw [spectral_conjugate_pow hV k, hDk, Matrix.mul_one, hV.1]

private theorem mat_pow_succ2 {d : ℕ} (M : Matrix (Fin d) (Fin d) ℂ) :
    M * M ^ 2 = M ^ 3 := (pow_succ' M 2).symm

private theorem mat_pow_succ2' {d : ℕ} (M : Matrix (Fin d) (Fin d) ℂ) :
    M ^ 2 * M = M ^ 3 := (pow_succ M 2).symm

private theorem mat_pow_add_mod2 {d : ℕ} {M : Matrix (Fin d) (Fin d) ℂ}
    (hm2 : M ^ 2 = 1) (a b : Fin 2) :
    M ^ (a + b).val = M ^ a.val * M ^ b.val := by
  fin_cases a <;> fin_cases b
  · simp
  · simp
  · simp
  · simp [← pow_two, hm2]

private theorem mat_pow_add_mod3 {d : ℕ} {M : Matrix (Fin d) (Fin d) ℂ}
    (hm3 : M ^ 3 = 1) (a b : Fin 3) :
    M ^ (a + b).val = M ^ a.val * M ^ b.val := by
  fin_cases a <;> fin_cases b <;> dsimp <;>
    simp only [Fin.add_def, Nat.mod_eq_of_lt, pow_zero, pow_one, Matrix.one_mul, Matrix.mul_one]
  · simp [pow_two]
  · calc (1 : Matrix (Fin d) (Fin d) ℂ) = M ^ 3 := hm3.symm
      _ = M * M ^ 2 := pow_succ' M 2
  · calc (1 : Matrix (Fin d) (Fin d) ℂ) = M ^ 3 := hm3.symm
      _ = M ^ 2 * M := pow_succ M 2
  · calc M = M ^ 3 * M := by rw [hm3, Matrix.one_mul]
      _ = (M ^ 2 * M) * M := by rw [pow_succ M 2]
      _ = M ^ 2 * M ^ 2 := by simp only [pow_two, Matrix.mul_assoc]

/-- Exact $S_3 = C_3 \rtimes C_2$ presentation elements `(a : Fin 2, b : Fin 3)` = $s^a r^b$. -/
abbrev S3Elem := Fin 2 × Fin 3

def s3Mul (x y : S3Elem) : S3Elem :=
  (x.1 + y.1, (if y.1 = 0 then x.2 else -x.2) + y.2)

def s3PresRep {d : ℕ} (Us Ur : Matrix (Fin d) (Fin d) ℂ) (x : S3Elem) :
    Matrix (Fin d) (Fin d) ℂ :=
  Us ^ x.1.val * Ur ^ x.2.val

private theorem s3_rel_swap {d : ℕ} {Us Ur : Matrix (Fin d) (Fin d) ℂ}
    (hs2 : Us ^ 2 = 1) (hr3 : Ur ^ 3 = 1) (hsr : Us * Ur * Us * Ur = 1) :
    Ur * Us = Us * Ur ^ 2 := by
  have hs_inv : Us * Us = 1 := by simpa [pow_two] using hs2
  have h1 : Ur * Us * Ur = Us := by
    calc
      Ur * Us * Ur = 1 * (Ur * Us * Ur) := by rw [Matrix.one_mul]
      _ = (Us * Us) * (Ur * Us * Ur) := by rw [hs_inv]
      _ = Us * (Us * Ur * Us * Ur) := by simp [Matrix.mul_assoc]
      _ = Us * 1 := by rw [hsr]
      _ = Us := Matrix.mul_one _
  calc
    Ur * Us = (Ur * Us) * 1 := (Matrix.mul_one _).symm
    _ = (Ur * Us) * Ur ^ 3 := by rw [hr3]
    _ = (Ur * Us * Ur) * Ur ^ 2 := by rw [pow_succ' Ur 2]; simp only [Matrix.mul_assoc]
    _ = Us * Ur ^ 2 := by rw [h1]

private theorem s3_r_conj_s {d : ℕ} {Us Ur : Matrix (Fin d) (Fin d) ℂ}
    (hs2 : Us ^ 2 = 1) (hr3 : Ur ^ 3 = 1) (hsr : Us * Ur * Us * Ur = 1)
    (b1 : Fin 3) (a2 : Fin 2) :
    Ur ^ b1.val * Us ^ a2.val =
      Us ^ a2.val * Ur ^ (if a2 = 0 then b1 else -b1).val := by
  have hsw := s3_rel_swap hs2 hr3 hsr
  have hsw2 : Ur ^ 2 * Us = Us * Ur := by
    calc
      Ur ^ 2 * Us = Ur * (Ur * Us) := by simp [pow_two, Matrix.mul_assoc]
      _ = Ur * (Us * Ur ^ 2) := by rw [hsw]
      _ = (Ur * Us) * Ur ^ 2 := (Matrix.mul_assoc _ _ _).symm
      _ = (Us * Ur ^ 2) * Ur ^ 2 := by rw [hsw]
      _ = Us * ((Ur * Ur ^ 2) * Ur) := by simp only [pow_two, Matrix.mul_assoc]
      _ = Us * (Ur ^ 3 * Ur) := by rw [pow_succ' Ur 2]
      _ = Us * Ur := by rw [hr3, Matrix.one_mul]
  fin_cases a2
  · simp
  · have hne : (1 : Fin 2) ≠ 0 := by decide
    change Ur ^ b1.val * Us ^ 1 = Us ^ 1 * Ur ^ (if (1 : Fin 2) = 0 then b1 else -b1).val
    rw [if_neg hne]
    fin_cases b1
    · change Ur ^ 0 * Us ^ 1 = Us ^ 1 * Ur ^ 0; simp
    · change Ur ^ 1 * Us ^ 1 = Us ^ 1 * Ur ^ 2; simpa using hsw
    · change Ur ^ 2 * Us ^ 1 = Us ^ 1 * Ur ^ 1; simpa using hsw2

theorem s3PresRep_mul {d : ℕ} {Us Ur : Matrix (Fin d) (Fin d) ℂ}
    (hs2 : Us ^ 2 = 1) (hr3 : Ur ^ 3 = 1) (hsr : Us * Ur * Us * Ur = 1)
    (x y : S3Elem) :
    s3PresRep Us Ur (s3Mul x y) = s3PresRep Us Ur x * s3PresRep Us Ur y := by
  rcases x with ⟨a1, b1⟩
  rcases y with ⟨a2, b2⟩
  dsimp [s3Mul, s3PresRep]
  rw [mat_pow_add_mod2 hs2 a1 a2, mat_pow_add_mod3 hr3 _ b2]
  have hc := s3_r_conj_s hs2 hr3 hsr b1 a2
  calc
    (Us ^ a1.val * Us ^ a2.val) * (Ur ^ (if a2 = 0 then b1 else -b1).val * Ur ^ b2.val) =
      Us ^ a1.val * (Us ^ a2.val * Ur ^ (if a2 = 0 then b1 else -b1).val) * Ur ^ b2.val := by
        simp [Matrix.mul_assoc]
    _ = Us ^ a1.val * (Ur ^ b1.val * Us ^ a2.val) * Ur ^ b2.val := by rw [← hc]
    _ = (Us ^ a1.val * Ur ^ b1.val) * (Us ^ a2.val * Ur ^ b2.val) := by
        simp [Matrix.mul_assoc]

theorem s3PresRep_unitary {d : ℕ} {Us Ur : Matrix (Fin d) (Fin d) ℂ}
    (hUs : IsUnitary Us) (hUr : IsUnitary Ur) (x : S3Elem) :
    IsUnitary (s3PresRep Us Ur x) :=
  isUnitary_mul (isUnitary_pow hUs x.1.val) (isUnitary_pow hUr x.2.val)

/-- Exact $A_4 = V_4 \rtimes C_3$ presentation elements `(u, v : Fin 2, c : Fin 3)`
    representing $s^u (t s t^2)^v t^c$. -/
abbrev A4Elem := Fin 2 × Fin 2 × Fin 3

def a4Rho (p : Fin 2 × Fin 2) : Fin 2 × Fin 2 := (p.2, p.1 + p.2)

def a4Mul (x y : A4Elem) : A4Elem :=
  let (u1, v1, c1) := x
  let (u2, v2, c2) := y
  let (ru, rv) := a4Rho^[c1.val] (u2, v2)
  (u1 + ru, v1 + rv, c1 + c2)

def a4PresRep {d : ℕ} (Us Ut : Matrix (Fin d) (Fin d) ℂ) (x : A4Elem) :
    Matrix (Fin d) (Fin d) ℂ :=
  let Uk := Ut * Us * Ut ^ 2
  Us ^ x.1.val * Uk ^ x.2.1.val * Ut ^ x.2.2.val

theorem a4_v4_commute {d : ℕ} {Us Ut : Matrix (Fin d) (Fin d) ℂ}
    (hs2 : Us ^ 2 = 1) (ht3 : Ut ^ 3 = 1) (hst3 : (Us * Ut) ^ 3 = 1) :
    let Uk := Ut * Us * Ut ^ 2
    Uk ^ 2 = 1 ∧ Us * Uk = Uk * Us ∧ Us * Uk = Ut ^ 2 * Us * Ut := by
  have hs_inv : Us * Us = 1 := by simpa [pow_two] using hs2
  have hst_full : Us * Ut * Us * Ut * Us * Ut = 1 := by
    calc
      Us * Ut * Us * Ut * Us * Ut = (Us * Ut) ^ 3 := by
        simp only [pow_three, Matrix.mul_assoc]
      _ = 1 := hst3
  have ht_u2 : Ut * Ut ^ 2 = 1 := by rw [mat_pow_succ2, ht3]
  have hu2_t : Ut ^ 2 * Ut = 1 := by rw [mat_pow_succ2', ht3]
  have ht_s_t_s : Ut * Us * Ut * Us = Us * Ut ^ 2 := by
    have h_mid : Ut * Us * Ut * Us * Ut = Us := by
      calc
        Ut * Us * Ut * Us * Ut = 1 * (Ut * Us * Ut * Us * Ut) := (Matrix.one_mul _).symm
        _ = (Us * Us) * (Ut * Us * Ut * Us * Ut) := by rw [hs_inv]
        _ = Us * (Us * Ut * Us * Ut * Us * Ut) := by simp only [Matrix.mul_assoc]
        _ = Us * 1 := by rw [hst_full]
        _ = Us := Matrix.mul_one _
    calc
      Ut * Us * Ut * Us = (Ut * Us * Ut * Us) * 1 := (Matrix.mul_one _).symm
      _ = (Ut * Us * Ut * Us) * (Ut * Ut ^ 2) := by rw [ht_u2]
      _ = (Ut * Us * Ut * Us * Ut) * Ut ^ 2 := by simp only [Matrix.mul_assoc]
      _ = Us * Ut ^ 2 := by rw [h_mid]
  have ht_s_t : Ut * Us * Ut = Us * Ut ^ 2 * Us := by
    calc
      Ut * Us * Ut = (Ut * Us * Ut * Us) * Us := by simp [Matrix.mul_assoc, hs_inv]
      _ = Us * Ut ^ 2 * Us := by rw [ht_s_t_s]
  have hs_t_s : Us * Ut * Us = Ut ^ 2 * Us * Ut ^ 2 := by
    calc
      Us * Ut * Us = (Ut ^ 2 * Ut) * (Us * Ut * Us) := by rw [hu2_t, Matrix.one_mul]
      _ = Ut ^ 2 * (Ut * Us * Ut * Us) := by simp [Matrix.mul_assoc]
      _ = Ut ^ 2 * (Us * Ut ^ 2) := by rw [ht_s_t_s]
      _ = Ut ^ 2 * Us * Ut ^ 2 := (Matrix.mul_assoc _ _ _).symm
  have hsk : Us * (Ut * Us * Ut ^ 2) = Ut ^ 2 * Us * Ut := by
    calc
      Us * (Ut * Us * Ut ^ 2) = (Us * Ut * Us) * Ut ^ 2 := by simp [Matrix.mul_assoc]
      _ = (Ut ^ 2 * Us * Ut ^ 2) * Ut ^ 2 := by rw [hs_t_s]
      _ = Ut ^ 2 * Us * ((Ut ^ 2 * Ut) * Ut) := by
          simp only [pow_two, Matrix.mul_assoc]
      _ = Ut ^ 2 * Us * Ut := by rw [hu2_t, Matrix.one_mul]
  have hks : (Ut * Us * Ut ^ 2) * Us = Ut ^ 2 * Us * Ut := by
    calc
      (Ut * Us * Ut ^ 2) * Us = Ut * (Us * Ut ^ 2 * Us) := by simp [Matrix.mul_assoc]
      _ = Ut * (Ut * Us * Ut) := by rw [ht_s_t]
      _ = Ut ^ 2 * Us * Ut := by simp [pow_two, Matrix.mul_assoc]
  dsimp
  refine ⟨?_, hsk.trans hks.symm, hsk⟩
  calc
    (Ut * Us * Ut ^ 2) ^ 2 = (Ut * Us * Ut ^ 2) * (Ut * Us * Ut ^ 2) := pow_two _
    _ = Ut * Us * (Ut ^ 2 * Ut) * Us * Ut ^ 2 := by simp [Matrix.mul_assoc]
    _ = Ut * (Us * Us) * Ut ^ 2 := by simp [hu2_t, Matrix.mul_assoc]
    _ = Ut * Ut ^ 2 := by rw [hs_inv, Matrix.mul_one]
    _ = 1 := ht_u2

private theorem a4_conj_rules {d : ℕ} {Us Ut : Matrix (Fin d) (Fin d) ℂ}
    (hs2 : Us ^ 2 = 1) (ht3 : Ut ^ 3 = 1) (hst3 : (Us * Ut) ^ 3 = 1) :
    let Uk := Ut * Us * Ut ^ 2
    Ut * Us = Uk * Ut ∧
    Ut * Uk = Us * Uk * Ut ∧
    Ut ^ 2 * Us = Us * Uk * Ut ^ 2 ∧
    Ut ^ 2 * Uk = Us * Ut ^ 2 := by
  have ⟨_, _, hsk⟩ := a4_v4_commute hs2 ht3 hst3
  dsimp at hsk ⊢
  have hu2_t : Ut ^ 2 * Ut = 1 := by rw [mat_pow_succ2', ht3]
  have ht_u2 : Ut * Ut ^ 2 = 1 := by rw [mat_pow_succ2, ht3]
  refine ⟨?_, ?_, ?_, ?_⟩
  · calc
      Ut * Us = (Ut * Us) * (Ut ^ 2 * Ut) := by rw [hu2_t, Matrix.mul_one]
      _ = (Ut * Us * Ut ^ 2) * Ut := by simp [Matrix.mul_assoc]
  · calc
      Ut * (Ut * Us * Ut ^ 2) = (Ut * Ut) * Us * Ut ^ 2 := by simp [Matrix.mul_assoc]
      _ = (Ut ^ 2 * Us * Ut) * Ut := by simp [pow_two, Matrix.mul_assoc]
      _ = Us * (Ut * Us * Ut ^ 2) * Ut := by rw [← hsk]
  · calc
      Ut ^ 2 * Us = (Ut ^ 2 * Us) * (Ut * Ut ^ 2) := by rw [ht_u2, Matrix.mul_one]
      _ = (Ut ^ 2 * Us * Ut) * Ut ^ 2 := by simp [Matrix.mul_assoc]
      _ = Us * (Ut * Us * Ut ^ 2) * Ut ^ 2 := by rw [← hsk]
  · calc
      Ut ^ 2 * (Ut * Us * Ut ^ 2) = (Ut ^ 2 * Ut) * Us * Ut ^ 2 := by simp [Matrix.mul_assoc]
      _ = Us * Ut ^ 2 := by rw [hu2_t, Matrix.one_mul]

private theorem a4_t_conj_v4 {d : ℕ} {Us Ut : Matrix (Fin d) (Fin d) ℂ}
    (hs2 : Us ^ 2 = 1) (ht3 : Ut ^ 3 = 1) (hst3 : (Us * Ut) ^ 3 = 1)
    (c1 : Fin 3) (u2 v2 : Fin 2) :
    let Uk := Ut * Us * Ut ^ 2
    Ut ^ c1.val * (Us ^ u2.val * Uk ^ v2.val) =
      (Us ^ (a4Rho^[c1.val] (u2, v2)).1.val * Uk ^ (a4Rho^[c1.val] (u2, v2)).2.val) *
        Ut ^ c1.val := by
  have ⟨hk2, hcomm, _⟩ := a4_v4_commute hs2 ht3 hst3
  have ⟨hr1, hr2, hr3, hr4⟩ := a4_conj_rules hs2 ht3 hst3
  dsimp at hk2 hcomm hr1 hr2 hr3 hr4 ⊢
  set Uk := Ut * Us * Ut ^ 2
  have h111 : Ut * (Us * Uk) = Us * Ut := by
    calc
      Ut * (Us * Uk) = (Ut * Us) * Uk := (Matrix.mul_assoc _ _ _).symm
      _ = (Uk * Ut) * Uk := by rw [hr1]
      _ = Uk * (Ut * Uk) := Matrix.mul_assoc _ _ _
      _ = Uk * (Us * Uk * Ut) := by rw [hr2]
      _ = (Uk * Us) * Uk * Ut := by simp [Matrix.mul_assoc]
      _ = (Us * Uk) * Uk * Ut := by rw [← hcomm]
      _ = Us * Uk ^ 2 * Ut := by simp [pow_two, Matrix.mul_assoc]
      _ = Us * Ut := by rw [hk2, Matrix.mul_one]
  have h211 : Ut ^ 2 * (Us * Uk) = Uk * Ut ^ 2 := by
    calc
      Ut ^ 2 * (Us * Uk) = (Ut ^ 2 * Us) * Uk := (Matrix.mul_assoc _ _ _).symm
      _ = (Us * Uk * Ut ^ 2) * Uk := by rw [hr3]
      _ = Us * Uk * (Ut ^ 2 * Uk) := by simp [Matrix.mul_assoc]
      _ = Us * Uk * (Us * Ut ^ 2) := by rw [hr4]
      _ = Us * (Uk * Us) * Ut ^ 2 := by simp [Matrix.mul_assoc]
      _ = Us * (Us * Uk) * Ut ^ 2 := by rw [← hcomm]
      _ = Us ^ 2 * Uk * Ut ^ 2 := by simp [pow_two, Matrix.mul_assoc]
      _ = Uk * Ut ^ 2 := by rw [hs2, Matrix.one_mul]
  fin_cases c1 <;> fin_cases u2 <;> fin_cases v2
  · change Ut ^ 0 * (Us ^ 0 * Uk ^ 0) = (Us ^ 0 * Uk ^ 0) * Ut ^ 0; simp
  · change Ut ^ 0 * (Us ^ 0 * Uk ^ 1) = (Us ^ 0 * Uk ^ 1) * Ut ^ 0; simp
  · change Ut ^ 0 * (Us ^ 1 * Uk ^ 0) = (Us ^ 1 * Uk ^ 0) * Ut ^ 0; simp
  · change Ut ^ 0 * (Us ^ 1 * Uk ^ 1) = (Us ^ 1 * Uk ^ 1) * Ut ^ 0; simp
  · change Ut ^ 1 * (Us ^ 0 * Uk ^ 0) = (Us ^ 0 * Uk ^ 0) * Ut ^ 1; simp
  · change Ut ^ 1 * (Us ^ 0 * Uk ^ 1) = (Us ^ 1 * Uk ^ 1) * Ut ^ 1; simpa using hr2
  · change Ut ^ 1 * (Us ^ 1 * Uk ^ 0) = (Us ^ 0 * Uk ^ 1) * Ut ^ 1; simpa using hr1
  · change Ut ^ 1 * (Us ^ 1 * Uk ^ 1) = (Us ^ 1 * Uk ^ 0) * Ut ^ 1; simpa using h111
  · change Ut ^ 2 * (Us ^ 0 * Uk ^ 0) = (Us ^ 0 * Uk ^ 0) * Ut ^ 2; simp
  · change Ut ^ 2 * (Us ^ 0 * Uk ^ 1) = (Us ^ 1 * Uk ^ 0) * Ut ^ 2; simpa using hr4
  · change Ut ^ 2 * (Us ^ 1 * Uk ^ 0) = (Us ^ 1 * Uk ^ 1) * Ut ^ 2; simpa using hr3
  · change Ut ^ 2 * (Us ^ 1 * Uk ^ 1) = (Us ^ 0 * Uk ^ 1) * Ut ^ 2; simpa using h211

private theorem pow_comm_of_comm {d : ℕ} {A B : Matrix (Fin d) (Fin d) ℂ}
    (hAB : A * B = B * A) (m n : ℕ) : A ^ m * B ^ n = B ^ n * A ^ m :=
  (Commute.pow_pow hAB m n).eq

/-- Exact $A_4$ unitary homomorphism purely from presentation relations `s^2=1`, `t^3=1`, `(st)^3=1`. -/
theorem a4PresRep_mul {d : ℕ} {Us Ut : Matrix (Fin d) (Fin d) ℂ}
    (hs2 : Us ^ 2 = 1) (ht3 : Ut ^ 3 = 1) (hst3 : (Us * Ut) ^ 3 = 1)
    (x y : A4Elem) :
    a4PresRep Us Ut (a4Mul x y) = a4PresRep Us Ut x * a4PresRep Us Ut y := by
  rcases x with ⟨u1, v1, c1⟩
  rcases y with ⟨u2, v2, c2⟩
  have ⟨hk2, hcomm, _⟩ := a4_v4_commute hs2 ht3 hst3
  set Uk := Ut * Us * Ut ^ 2
  set ru := (a4Rho^[c1.val] (u2, v2)).1
  set rv := (a4Rho^[c1.val] (u2, v2)).2
  dsimp [a4Mul, a4PresRep]
  rw [mat_pow_add_mod2 hs2 u1 ru, mat_pow_add_mod2 hk2 v1 rv, mat_pow_add_mod3 ht3 c1 c2]
  have hc := a4_t_conj_v4 hs2 ht3 hst3 c1 u2 v2
  dsimp at hc
  have hpc : Uk ^ v1.val * Us ^ ru.val = Us ^ ru.val * Uk ^ v1.val :=
    pow_comm_of_comm hcomm.symm v1.val ru.val
  calc
    (Us ^ u1.val * Us ^ ru.val) * (Uk ^ v1.val * Uk ^ rv.val) * (Ut ^ c1.val * Ut ^ c2.val) =
      Us ^ u1.val * (Us ^ ru.val * Uk ^ v1.val) * Uk ^ rv.val * (Ut ^ c1.val * Ut ^ c2.val) := by
        simp [Matrix.mul_assoc]
    _ = Us ^ u1.val * (Uk ^ v1.val * Us ^ ru.val) * Uk ^ rv.val * (Ut ^ c1.val * Ut ^ c2.val) := by
        rw [hpc]
    _ = Us ^ u1.val * Uk ^ v1.val * ((Us ^ ru.val * Uk ^ rv.val) * Ut ^ c1.val) * Ut ^ c2.val := by
        simp [Matrix.mul_assoc]
    _ = Us ^ u1.val * Uk ^ v1.val * (Ut ^ c1.val * (Us ^ u2.val * Uk ^ v2.val)) * Ut ^ c2.val := by
        rw [← hc]
    _ = (Us ^ u1.val * Uk ^ v1.val * Ut ^ c1.val) *
        (Us ^ u2.val * Uk ^ v2.val * Ut ^ c2.val) := by
        simp [Matrix.mul_assoc]

theorem a4PresRep_unitary {d : ℕ} {Us Ut : Matrix (Fin d) (Fin d) ℂ}
    (hUs : IsUnitary Us) (hUt : IsUnitary Ut) (x : A4Elem) :
    IsUnitary (a4PresRep Us Ut x) := by
  have hUk : IsUnitary (Ut * Us * Ut ^ 2) :=
    isUnitary_mul (isUnitary_mul hUt hUs) (isUnitary_pow hUt 2)
  exact isUnitary_mul (isUnitary_mul (isUnitary_pow hUs x.1.val) (isUnitary_pow hUk x.2.1.val))
    (isUnitary_pow hUt x.2.2.val)

theorem a4PresRep_trace_conjugacy_invariant {d : ℕ} {Us Ut K : Matrix (Fin d) (Fin d) ℂ}
    (hK : IsUnitary K) (x : A4Elem) :
    (K * a4PresRep Us Ut x * Kᴴ).trace = (a4PresRep Us Ut x).trace := by
  calc
    (K * a4PresRep Us Ut x * Kᴴ).trace =
      (K * (a4PresRep Us Ut x * Kᴴ)).trace := by rw [Matrix.mul_assoc]
    _ = ((a4PresRep Us Ut x * Kᴴ) * K).trace := Matrix.trace_mul_comm _ _
    _ = (a4PresRep Us Ut x * (Kᴴ * K)).trace := by rw [Matrix.mul_assoc]
    _ = (a4PresRep Us Ut x * 1).trace := by rw [hK.2]
    _ = (a4PresRep Us Ut x).trace := by rw [Matrix.mul_one]

end LiePresentationUnitary


/-! ## 3. Hoza Min-Isolating-Weight Spanning Trees (`ECCC TR26-323`) -/
namespace IsolatingWeightTree

structure WalkGraph where
  V : Type
  E : Type
  src : E → V
  tgt : E → V

inductive SignedDir | fwd | bwd

structure SignedStep (G : WalkGraph) where
  edge : G.E
  dir : SignedDir

def stepSrc (G : WalkGraph) (s : SignedStep G) : G.V :=
  match s.dir with | .fwd => G.src s.edge | .bwd => G.tgt s.edge

def stepTgt (G : WalkGraph) (s : SignedStep G) : G.V :=
  match s.dir with | .fwd => G.tgt s.edge | .bwd => G.src s.edge

inductive SignedWalk (G : WalkGraph) (root : G.V) : G.V → Type
  | nil : SignedWalk G root root
  | snoc {u : G.V} (p : SignedWalk G root u) (s : SignedStep G)
      (hs : stepSrc G s = u) : SignedWalk G root (stepTgt G s)

def walkWeight {G : WalkGraph} {root : G.V} (w : G.E → ℕ) :
    ∀ {v : G.V}, SignedWalk G root v → ℕ
  | _, .nil => 0
  | _, .snoc p s _ => walkWeight w p + w s.edge

theorem walkWeight_step_strict_lt {G : WalkGraph} {root u : G.V}
    (w : G.E → ℕ) (hw : ∀ e, 0 < w e)
    (p : SignedWalk G root u) (s : SignedStep G) (hs : stepSrc G s = u) :
    walkWeight w p < walkWeight w (.snoc p s hs) := by
  change walkWeight w p < walkWeight w p + w s.edge
  exact Nat.lt_add_of_pos_right (hw s.edge)

structure MinIsolatingAssignment (G : WalkGraph) (root : G.V) where
  w : G.E → ℕ
  w_pos : ∀ e, 0 < w e
  minWalk : ∀ v : G.V, SignedWalk G root v
  min_unique : ∀ {v : G.V} (p : SignedWalk G root v),
    walkWeight w p ≤ walkWeight w (minWalk v) → p = minWalk v

theorem minWalk_root_nil {G : WalkGraph} {root : G.V}
    (I : MinIsolatingAssignment G root) :
    I.minWalk root = .nil :=
  (I.min_unique .nil (Nat.zero_le _)).symm

theorem minWalk_le {G : WalkGraph} {root : G.V}
    (I : MinIsolatingAssignment G root) {v : G.V}
    (p : SignedWalk G root v) :
    walkWeight I.w (I.minWalk v) ≤ walkWeight I.w p := by
  by_contra hlt
  have hle : walkWeight I.w p ≤ walkWeight I.w (I.minWalk v) :=
    Nat.le_of_not_ge hlt
  have heq : p = I.minWalk v := I.min_unique p hle
  subst heq
  exact hlt (le_refl _)

theorem minWalk_prefix_eq {G : WalkGraph} {root u : G.V}
    (I : MinIsolatingAssignment G root)
    (p : SignedWalk G root u) (s : SignedStep G) (hs : stepSrc G s = u)
    (hmin : I.minWalk (stepTgt G s) = .snoc p s hs) :
    p = I.minWalk u := by
  have hle_u : walkWeight I.w (I.minWalk u) ≤ walkWeight I.w p :=
    minWalk_le I p
  have hle_snoc :
      walkWeight I.w (.snoc (I.minWalk u) s hs) ≤
        walkWeight I.w (I.minWalk (stepTgt G s)) := by
    rw [hmin]
    change walkWeight I.w (I.minWalk u) + I.w s.edge ≤ walkWeight I.w p + I.w s.edge
    exact Nat.add_le_add_right hle_u (I.w s.edge)
  have heq :
      (SignedWalk.snoc (I.minWalk u) s hs : SignedWalk G root (stepTgt G s)) =
        SignedWalk.snoc p s hs := by
    rw [← hmin]
    exact I.min_unique (.snoc (I.minWalk u) s hs) hle_snoc
  injection heq with _ hp _
  exact hp.symm

def isIsolatingTreeEdge {G : WalkGraph} {root : G.V}
    (I : MinIsolatingAssignment G root) (e : G.E) : Prop :=
  ∃ (u : G.V) (p : SignedWalk G root u) (s : SignedStep G) (hs : stepSrc G s = u),
    s.edge = e ∧ I.minWalk (stepTgt G s) = .snoc p s hs

def isIsolatingChordEdge {G : WalkGraph} {root : G.V}
    (I : MinIsolatingAssignment G root) (e : G.E) : Prop :=
  ¬ isIsolatingTreeEdge I e

theorem isolating_tree_chord_disjoint {G : WalkGraph} {root : G.V}
    (I : MinIsolatingAssignment G root) (e : G.E) :
    ¬ (isIsolatingTreeEdge I e ∧ isIsolatingChordEdge I e) :=
  fun ⟨ht, hc⟩ => hc ht

structure GaugeGroup where
  Carrier : Type
  one : Carrier
  mul : Carrier → Carrier → Carrier
  inv : Carrier → Carrier
  one_mul : ∀ a, mul one a = a
  mul_one : ∀ a, mul a one = a
  mul_assoc : ∀ a b c, mul (mul a b) c = mul a (mul b c)
  mul_left_inv : ∀ a, mul (inv a) a = one
  mul_right_inv : ∀ a, mul a (inv a) = one

def stepEval {G : WalkGraph} {H : GaugeGroup}
    (A : G.E → H.Carrier) (s : SignedStep G) : H.Carrier :=
  match s.dir with
  | .fwd => A s.edge
  | .bwd => H.inv (A s.edge)

def walkEval {G : WalkGraph} {root : G.V} {H : GaugeGroup}
    (A : G.E → H.Carrier) : ∀ {v : G.V}, SignedWalk G root v → H.Carrier
  | _, .nil => H.one
  | _, .snoc p s _ => H.mul (stepEval A s) (walkEval A p)

def isolatingTreeFrame {G : WalkGraph} {root : G.V} {H : GaugeGroup}
    (I : MinIsolatingAssignment G root) (A : G.E → H.Carrier) (v : G.V) : H.Carrier :=
  walkEval A (I.minWalk v)

theorem isolating_treeFrame_edge_recursion {G : WalkGraph} {root u : G.V}
    {H : GaugeGroup} (I : MinIsolatingAssignment G root) (A : G.E → H.Carrier)
    (s : SignedStep G) (hs : stepSrc G s = u)
    (htgt : ∃ p : SignedWalk G root u, I.minWalk (stepTgt G s) = .snoc p s hs) :
    isolatingTreeFrame I A (stepTgt G s) =
      H.mul (stepEval A s) (isolatingTreeFrame I A (stepSrc G s)) := by
  rcases htgt with ⟨p, hmin⟩
  have hp : p = I.minWalk u := minWalk_prefix_eq I p s hs hmin
  unfold isolatingTreeFrame
  rw [hmin, hs, ← hp]
  rfl

def gaugeTransform {G : WalkGraph} {H : GaugeGroup}
    (g : G.V → H.Carrier) (A : G.E → H.Carrier) (e : G.E) : H.Carrier :=
  H.mul (g (G.tgt e)) (H.mul (A e) (H.inv (g (G.src e))))

theorem isolating_treeFrame_gauge_covariant {G : WalkGraph} {root : G.V}
    {H : GaugeGroup} (I : MinIsolatingAssignment G root)
    (g : G.V → H.Carrier) (A : G.E → H.Carrier) (v : G.V) :
    isolatingTreeFrame I (gaugeTransform g A) v =
      H.mul (g v) (H.mul (isolatingTreeFrame I A v) (H.inv (g root))) := by
  unfold isolatingTreeFrame
  suffices h : ∀ (u : G.V) (p : SignedWalk G root u),
      walkEval (gaugeTransform g A) p =
        H.mul (g u) (H.mul (walkEval A p) (H.inv (g root))) by
    exact h v (I.minWalk v)
  intro u p
  induction p with
  | nil =>
      simp only [walkEval]
      rw [H.one_mul, H.mul_right_inv]
  | @snoc u_mid p s hs ih =>
      have ih' : walkEval (gaugeTransform g A) p =
          H.mul (g u_mid) (H.mul (walkEval A p) (H.inv (g root))) := ih
      simp only [walkEval]
      rw [ih']
      cases hd : s.dir with
      | fwd =>
          have hsrc : G.src s.edge = u_mid := by simpa [stepSrc, hd] using hs
          have htgt : stepTgt G s = G.tgt s.edge := by simp [stepTgt, hd]
          simp only [stepEval, hd, htgt, gaugeTransform]
          rw [hsrc]
          calc
            H.mul (H.mul (g (G.tgt s.edge)) (H.mul (A s.edge) (H.inv (g u_mid))))
                (H.mul (g u_mid) (H.mul (walkEval A p) (H.inv (g root)))) =
              H.mul (g (G.tgt s.edge))
                (H.mul (A s.edge)
                  (H.mul (H.mul (H.inv (g u_mid)) (g u_mid))
                    (H.mul (walkEval A p) (H.inv (g root))))) := by
                simp only [H.mul_assoc]
            _ = H.mul (g (G.tgt s.edge))
                (H.mul (A s.edge) (H.mul (walkEval A p) (H.inv (g root)))) := by
                rw [H.mul_left_inv, H.one_mul]
            _ = H.mul (g (G.tgt s.edge))
                (H.mul (H.mul (A s.edge) (walkEval A p)) (H.inv (g root))) := by
                simp only [H.mul_assoc]
      | bwd =>
          have hsrc : G.tgt s.edge = u_mid := by simpa [stepSrc, hd] using hs
          have htgt : stepTgt G s = G.src s.edge := by simp [stepTgt, hd]
          simp only [stepEval, hd, htgt, gaugeTransform]
          have hinv :
              H.inv (H.mul (g (G.tgt s.edge)) (H.mul (A s.edge) (H.inv (g (G.src s.edge))))) =
                H.mul (g (G.src s.edge)) (H.mul (H.inv (A s.edge)) (H.inv (g u_mid))) := by
            have hi : ∀ a b : H.Carrier, H.inv (H.mul a b) = H.mul (H.inv b) (H.inv a) := by
              intro a b
              have hprod : H.mul (H.mul (H.inv b) (H.inv a)) (H.mul a b) = H.one := by
                calc
                  H.mul (H.mul (H.inv b) (H.inv a)) (H.mul a b) =
                    H.mul (H.inv b) (H.mul (H.mul (H.inv a) a) b) := by simp [H.mul_assoc]
                  _ = H.mul (H.inv b) (H.mul H.one b) := by rw [H.mul_left_inv]
                  _ = H.mul (H.inv b) b := by rw [H.one_mul]
                  _ = H.one := H.mul_left_inv b
              calc
                H.inv (H.mul a b) = H.mul H.one (H.inv (H.mul a b)) := (H.one_mul _).symm
                _ = H.mul (H.mul (H.mul (H.inv b) (H.inv a)) (H.mul a b)) (H.inv (H.mul a b)) := by
                    rw [hprod]
                _ = H.mul (H.mul (H.inv b) (H.inv a)) (H.mul (H.mul a b) (H.inv (H.mul a b))) := by
                    simp [H.mul_assoc]
                _ = H.mul (H.inv b) (H.inv a) := by rw [H.mul_right_inv, H.mul_one]
            have hii : ∀ a : H.Carrier, H.inv (H.inv a) = a := by
              intro a
              calc
                H.inv (H.inv a) = H.mul H.one (H.inv (H.inv a)) := (H.one_mul _).symm
                _ = H.mul (H.mul a (H.inv a)) (H.inv (H.inv a)) := by rw [H.mul_right_inv]
                _ = H.mul a (H.mul (H.inv a) (H.inv (H.inv a))) := H.mul_assoc _ _ _
                _ = H.mul a H.one := by rw [H.mul_right_inv]
                _ = a := H.mul_one a
            rw [hi, hi, hii, hsrc]
            simp [H.mul_assoc]
          rw [hinv]
          calc
            H.mul (H.mul (g (G.src s.edge)) (H.mul (H.inv (A s.edge)) (H.inv (g u_mid))))
                (H.mul (g u_mid) (H.mul (walkEval A p) (H.inv (g root)))) =
              H.mul (g (G.src s.edge))
                (H.mul (H.inv (A s.edge))
                  (H.mul (H.mul (H.inv (g u_mid)) (g u_mid))
                    (H.mul (walkEval A p) (H.inv (g root))))) := by
                simp only [H.mul_assoc]
            _ = H.mul (g (G.src s.edge))
                (H.mul (H.inv (A s.edge)) (H.mul (walkEval A p) (H.inv (g root)))) := by
                rw [H.mul_left_inv, H.one_mul]
            _ = H.mul (g (G.src s.edge))
                (H.mul (H.mul (H.inv (A s.edge)) (walkEval A p)) (H.inv (g root))) := by
                simp only [H.mul_assoc]

end IsolatingWeightTree


/-! ## 4. Continuous Lyapunov Tangent Gramians (`arXiv:2610.12426` Clark) -/
namespace ContinuousLyapunovGramian

noncomputable def shiftedGen {n : ℕ} (A : Matrix (Fin n) (Fin n) ℝ) (lam : ℝ) :
    Matrix (Fin n) (Fin n) ℝ :=
  A - (lam / 2) • (1 : Matrix (Fin n) (Fin n) ℝ)

def LyapEq {n : ℕ} (A : Matrix (Fin n) (Fin n) ℝ) (lam : ℝ)
    (W Q : Matrix (Fin n) (Fin n) ℝ) : Prop :=
  shiftedGen A lam * W + W * (shiftedGen A lam)ᵀ = -Q

theorem shiftedGen_zero {n : ℕ} (A : Matrix (Fin n) (Fin n) ℝ) :
    shiftedGen A 0 = A := by
  simp [shiftedGen]

theorem shiftedGen_conj {n : ℕ} (A T Tinv : Matrix (Fin n) (Fin n) ℝ) (lam : ℝ)
    (h1 : T * Tinv = 1) :
    T * shiftedGen A lam * Tinv = shiftedGen (T * A * Tinv) lam := by
  simp only [shiftedGen, Matrix.mul_sub, Matrix.sub_mul, Matrix.mul_smul,
    Matrix.smul_mul, Matrix.mul_one, h1]

theorem lyapEq_congruence_invariant {n : ℕ}
    (A W Q T Tinv : Matrix (Fin n) (Fin n) ℝ) (lam : ℝ)
    (h1 : T * Tinv = 1) (h2 : Tinv * T = 1)
    (hL : LyapEq A lam W Q) :
    LyapEq (T * A * Tinv) lam (T * W * Tᵀ) (T * Q * Tᵀ) := by
  unfold LyapEq at hL ⊢
  have hsh : shiftedGen (T * A * Tinv) lam = T * shiftedGen A lam * Tinv :=
    (shiftedGen_conj A T Tinv lam h1).symm
  rw [hsh]
  have ht : (T * shiftedGen A lam * Tinv)ᵀ = Tinvᵀ * (shiftedGen A lam)ᵀ * Tᵀ := by
    simp [Matrix.transpose_mul, Matrix.mul_assoc]
  rw [ht]
  have hterm1 : (T * shiftedGen A lam * Tinv) * (T * W * Tᵀ) =
      T * (shiftedGen A lam * W) * Tᵀ := by
    calc
      (T * shiftedGen A lam * Tinv) * (T * W * Tᵀ) =
        T * shiftedGen A lam * (Tinv * T) * W * Tᵀ := by simp [Matrix.mul_assoc]
      _ = T * shiftedGen A lam * 1 * W * Tᵀ := by rw [h2]
      _ = T * (shiftedGen A lam * W) * Tᵀ := by simp [Matrix.mul_assoc]
  have hterm2 : (T * W * Tᵀ) * (Tinvᵀ * (shiftedGen A lam)ᵀ * Tᵀ) =
      T * (W * (shiftedGen A lam)ᵀ) * Tᵀ := by
    have htinv : Tᵀ * Tinvᵀ = 1 := by
      calc Tᵀ * Tinvᵀ = (Tinv * T)ᵀ := (Matrix.transpose_mul _ _).symm
        _ = (1 : Matrix (Fin n) (Fin n) ℝ)ᵀ := by rw [h2]
        _ = 1 := Matrix.transpose_one
    calc
      (T * W * Tᵀ) * (Tinvᵀ * (shiftedGen A lam)ᵀ * Tᵀ) =
        T * W * (Tᵀ * Tinvᵀ) * (shiftedGen A lam)ᵀ * Tᵀ := by simp [Matrix.mul_assoc]
      _ = T * W * 1 * (shiftedGen A lam)ᵀ * Tᵀ := by rw [htinv]
      _ = T * (W * (shiftedGen A lam)ᵀ) * Tᵀ := by simp [Matrix.mul_assoc]
  rw [hterm1, hterm2]
  calc
    T * (shiftedGen A lam * W) * Tᵀ + T * (W * (shiftedGen A lam)ᵀ) * Tᵀ =
      T * (shiftedGen A lam * W + W * (shiftedGen A lam)ᵀ) * Tᵀ := by
        simp [Matrix.mul_add, Matrix.add_mul]
    _ = T * (-Q) * Tᵀ := by rw [hL]
    _ = -(T * Q * Tᵀ) := by simp

theorem balanced_trace_similarity_invariant {n : ℕ}
    (Wc Wo T Tinv : Matrix (Fin n) (Fin n) ℝ)
    (h2 : Tinv * T = 1) :
    ((T * Wc * Tᵀ) * (Tinvᵀ * Wo * Tinv)).trace = (Wc * Wo).trace := by
  have htinv : Tᵀ * Tinvᵀ = 1 := by
    calc Tᵀ * Tinvᵀ = (Tinv * T)ᵀ := (Matrix.transpose_mul _ _).symm
      _ = (1 : Matrix (Fin n) (Fin n) ℝ)ᵀ := by rw [h2]
      _ = 1 := Matrix.transpose_one
  calc
    ((T * Wc * Tᵀ) * (Tinvᵀ * Wo * Tinv)).trace =
      (T * (Wc * (Tᵀ * Tinvᵀ) * Wo) * Tinv).trace := by
        congr 1; simp [Matrix.mul_assoc]
    _ = (T * (Wc * Wo) * Tinv).trace := by rw [htinv, Matrix.mul_one]
    _ = ((Wc * Wo) * Tinv * T).trace := by
        simpa [Matrix.mul_assoc] using Matrix.trace_mul_comm T ((Wc * Wo) * Tinv)
    _ = ((Wc * Wo) * (Tinv * T)).trace := by simp [Matrix.mul_assoc]
    _ = (Wc * Wo).trace := by rw [h2, Matrix.mul_one]

theorem skew_lyapunov_trace_exact {n : ℕ}
    (A W Q : Matrix (Fin n) (Fin n) ℝ) (lam : ℝ)
    (hskew : Aᵀ = -A) (hL : LyapEq A lam W Q) :
    lam * W.trace = Q.trace := by
  unfold LyapEq shiftedGen at hL
  have htr : (-(Q)).trace =
      ((A - (lam / 2) • (1 : Matrix (Fin n) (Fin n) ℝ)) * W +
       W * (A - (lam / 2) • (1 : Matrix (Fin n) (Fin n) ℝ))ᵀ).trace := by
    rw [hL]
  have hzero : (A * W + W * Aᵀ).trace = 0 := by
    have : (W * Aᵀ).trace = -(A * W).trace := by
      calc
        (W * Aᵀ).trace = (W * (-A)).trace := by rw [hskew]
        _ = -(W * A).trace := by simp
        _ = -(A * W).trace := by rw [Matrix.trace_mul_comm W A]
    rw [Matrix.trace_add, this, add_neg_cancel]
  have heq : (A - (lam / 2) • (1 : Matrix (Fin n) (Fin n) ℝ)) * W +
      W * (A - (lam / 2) • (1 : Matrix (Fin n) (Fin n) ℝ))ᵀ =
      (A * W + W * Aᵀ) - lam • W := by
    simp only [Matrix.sub_mul, Matrix.mul_sub, Matrix.transpose_sub, Matrix.transpose_smul,
      Matrix.transpose_one, Matrix.smul_mul, Matrix.mul_smul, Matrix.one_mul, Matrix.mul_one]
    have h2 : lam • W = (lam / 2) • W + (lam / 2) • W := by
      rw [← add_smul, add_halves]
    rw [h2]
    abel
  rw [heq, Matrix.trace_sub, Matrix.trace_neg, hzero, zero_sub,
    Matrix.trace_smul, smul_eq_mul] at htr
  linarith

theorem lyapunov_quadratic_decay {n : ℕ}
    (A Wo C : Matrix (Fin n) (Fin n) ℝ) (lam : ℝ)
    (hL : (shiftedGen A lam)ᵀ * Wo + Wo * shiftedGen A lam = -(Cᵀ * C))
    (x : Fin n → ℝ) :
    x ⬝ᵥ (((shiftedGen A lam)ᵀ * Wo + Wo * shiftedGen A lam) *ᵥ x) ≤ 0 := by
  rw [hL, Matrix.neg_mulVec]
  have hneg : x ⬝ᵥ -((Cᵀ * C) *ᵥ x) = -(x ⬝ᵥ ((Cᵀ * C) *ᵥ x)) := by simp
  have hsq : 0 ≤ (C *ᵥ x) ⬝ᵥ (C *ᵥ x) := by
    change 0 ≤ ∑ i, (C *ᵥ x) i * (C *ᵥ x) i
    exact Finset.sum_nonneg (fun i _ => mul_self_nonneg _)
  have hvc : x ᵥ* Cᵀ = C *ᵥ x :=
    Matrix.vecMul_transpose C x
  have heq : x ⬝ᵥ ((Cᵀ * C) *ᵥ x) = (C *ᵥ x) ⬝ᵥ (C *ᵥ x) := by
    rw [← Matrix.mulVec_mulVec, Matrix.dotProduct_mulVec, hvc]
  linarith

theorem discrete_to_continuous_lyapunov_expansion {n : ℕ}
    (B W : Matrix (Fin n) (Fin n) ℝ) (dt : ℝ) :
    W - (1 + dt • B) * W * (1 + dt • B)ᵀ =
      -(dt • (B * W + W * Bᵀ)) - (dt * dt) • (B * W * Bᵀ) := by
  simp only [Matrix.add_mul, Matrix.mul_add, Matrix.transpose_add, Matrix.transpose_one,
    Matrix.transpose_smul, Matrix.one_mul, Matrix.mul_one, Matrix.smul_mul, Matrix.mul_smul,
    smul_smul, smul_add]
  abel

end ContinuousLyapunovGramian

end Semplex.LieLyapunov
