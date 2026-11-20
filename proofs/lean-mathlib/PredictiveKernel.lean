/-
  Mathlib formalization of the predictive-kernel counting & expectation identities
  (`charter/FOUNDATIONS.md` §11.4, Gemini G18):

  1. `card_conj_mem_eq_card_mul_fixedCosets` (and `Finset.filter` form):
     For any finite group `G`, subgroup `H : Subgroup G`, and `x : G`,
       `#{w : G | w⁻¹ * x * w ∈ H} = |H| * #{q : G ⧸ H | x • q = q}`.

  2. `predictive_kernel_coset_expectation`:
     For the one-hot coset readout `o g q = if (g : G ⧸ H) = q then 1 else 0`,
       `E_w ⟨o(gw), o(hw)⟩ = χ_perm(g⁻¹h) / [G : H]`
     (and `χ_perm(g⁻¹h) / |G ⧸ H|`).
-/
import Mathlib.GroupTheory.Index
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.BigOperators.Group.Finset
import Mathlib.Data.Fintype.BigOperators

open scoped BigOperators

namespace PredictiveKernel

section CountingIdentity

open Classical

/-- An element `w : G` satisfies `w⁻¹ * x * w ∈ H` iff `x` fixes the left coset `wH`. -/
theorem conj_mem_iff_smul_coset_eq {G : Type*} [Group G] (H : Subgroup G) (x w : G) :
    w⁻¹ * x * w ∈ H ↔ x • (w : G ⧸ H) = (w : G ⧸ H) := by
  rw [MulAction.Quotient.smul_coe, smul_eq_mul, eq_comm, QuotientGroup.eq, mul_assoc]

/-- Explicit bijection between `{w : G // x • (w : G ⧸ H) = (w : G ⧸ H)}` and
    `{q : G ⧸ H // x • q = q} × H`. -/
noncomputable def fixedCosetPreimageEquiv {G : Type*} [Group G] (H : Subgroup G) (x : G) :
    {w : G // x • (w : G ⧸ H) = (w : G ⧸ H)} ≃ {q : G ⧸ H // x • q = q} × H where
  toFun w :=
    (⟨(w.1 : G ⧸ H), w.2⟩,
      ⟨(Quotient.out' (w.1 : G ⧸ H))⁻¹ * w.1,
        QuotientGroup.eq.mp (QuotientGroup.out_eq' (w.1 : G ⧸ H))⟩)
  invFun p :=
    ⟨Quotient.out' p.1.1 * p.2.1, by
      rw [QuotientGroup.mk_mul_of_mem _ p.2.2, QuotientGroup.out_eq']
      exact p.1.2⟩
  left_inv w := by
    ext
    simp [mul_inv_cancel_left]
  right_inv p := by
    rcases p with ⟨⟨q, hq⟩, ⟨h, hh⟩⟩
    have hqeq : ((Quotient.out' q * h : G) : G ⧸ H) = q := by
      rw [QuotientGroup.mk_mul_of_mem _ hh, QuotientGroup.out_eq']
    ext
    · exact hqeq
    · simp [hqeq]

/-- Counting identity (`FOUNDATIONS.md` §11.4): for any finite group `G`, subgroup `H`,
    and `x : G`, `#{w : w⁻¹xw ∈ H} = |H| * #{gH : x • gH = gH}`. -/
theorem card_conj_mem_eq_card_mul_fixedCosets {G : Type*} [Group G] [Fintype G]
    (H : Subgroup G) (x : G) :
    Fintype.card {w : G // w⁻¹ * x * w ∈ H} =
      Fintype.card H * Fintype.card {q : G ⧸ H // x • q = q} := by
  have heq :
      {w : G // w⁻¹ * x * w ∈ H} ≃ {w : G // x • (w : G ⧸ H) = (w : G ⧸ H)} :=
    Equiv.subtypeEquivRight fun w => conj_mem_iff_smul_coset_eq H x w
  calc
    Fintype.card {w : G // w⁻¹ * x * w ∈ H}
        = Fintype.card {w : G // x • (w : G ⧸ H) = (w : G ⧸ H)} := Fintype.card_congr heq
    _ = Fintype.card ({q : G ⧸ H // x • q = q} × H) :=
        Fintype.card_congr (fixedCosetPreimageEquiv H x)
    _ = Fintype.card {q : G ⧸ H // x • q = q} * Fintype.card H := Fintype.card_prod _ _
    _ = Fintype.card H * Fintype.card {q : G ⧸ H // x • q = q} := Nat.mul_comm _ _

/-- Finset cardinality form of `card_conj_mem_eq_card_mul_fixedCosets`. -/
theorem card_filter_conj_mem_eq {G : Type*} [Group G] [Fintype G]
    (H : Subgroup G) (x : G) :
    (Finset.univ.filter fun w : G => w⁻¹ * x * w ∈ H).card =
      Fintype.card H * (Finset.univ.filter fun q : G ⧸ H => x • q = q).card := by
  simpa only [Fintype.card_subtype] using card_conj_mem_eq_card_mul_fixedCosets H x

end CountingIdentity

section ExpectationIdentity

open Classical

/-- One-hot left-coset indicator readout `o : G → (G ⧸ H → ℝ)`. -/
noncomputable def cosetOneHot {G : Type*} [Group G] (H : Subgroup G) (g : G) : G ⧸ H → ℝ :=
  fun q => if (g : G ⧸ H) = q then 1 else 0

/-- Inner product `⟨u, v⟩` on `G ⧸ H → ℝ`. -/
noncomputable def cosetInner {G : Type*} [Group G] [Fintype G] (H : Subgroup G)
    (u v : G ⧸ H → ℝ) : ℝ :=
  ∑ q : G ⧸ H, u q * v q

/-- Permutation character `χ_perm(x) = #{gH : x • gH = gH}` on left cosets of `H`. -/
noncomputable def permChar {G : Type*} [Group G] [Fintype G] (H : Subgroup G) (x : G) : ℝ :=
  (Fintype.card {q : G ⧸ H // x • q = q} : ℝ)

/-- Inner product of two coset one-hot vectors equals the indicator that they share a coset. -/
theorem cosetInner_cosetOneHot_eq {G : Type*} [Group G] [Fintype G]
    (H : Subgroup G) (g h w : G) :
    cosetInner H (cosetOneHot H (g * w)) (cosetOneHot H (h * w)) =
      if w⁻¹ * (g⁻¹ * h) * w ∈ H then 1 else 0 := by
  have hmem :
      ((g * w : G) : G ⧸ H) = ((h * w : G) : G ⧸ H) ↔ w⁻¹ * (g⁻¹ * h) * w ∈ H := by
    rw [QuotientGroup.eq]
    have hmul : (g * w)⁻¹ * (h * w) = w⁻¹ * (g⁻¹ * h) * w := by
      rw [mul_inv_rev]
      simp [mul_assoc]
    rw [hmul]
  unfold cosetInner cosetOneHot
  have hsum :
      ∑ q : G ⧸ H,
        (if ((g * w : G) : G ⧸ H) = q then (1 : ℝ) else 0) *
          (if ((h * w : G) : G ⧸ H) = q then (1 : ℝ) else 0) =
      if ((g * w : G) : G ⧸ H) = ((h * w : G) : G ⧸ H) then 1 else 0 := by
    rw [Finset.sum_eq_single (((h * w : G) : G ⧸ H))]
    · by_cases he : ((g * w : G) : G ⧸ H) = ((h * w : G) : G ⧸ H)
      · simp [he]
      · simp [he]
    · intro q _ hq
      have hq' : ((h * w : G) : G ⧸ H) ≠ q := fun e => hq e.symm
      simp [hq']
    · intro hnot
      exact absurd (Finset.mem_univ _) hnot
  rw [hsum]
  by_cases hcond : ((g * w : G) : G ⧸ H) = ((h * w : G) : G ⧸ H)
  · simp [hcond, hmem.mp hcond]
  · simp [hcond, mt hmem.mpr hcond]

/-- Uniform expectation over `w : G` of `⟨o(gw), o(hw)⟩` equals `χ_perm(g⁻¹h) / [G : H]`. -/
theorem predictive_kernel_coset_expectation {G : Type*} [Group G] [Fintype G]
    (H : Subgroup G) (g h : G) :
    (1 / (Fintype.card G : ℝ)) *
        ∑ w : G, cosetInner H (cosetOneHot H (g * w)) (cosetOneHot H (h * w)) =
      permChar H (g⁻¹ * h) / (H.index : ℝ) := by
  have hsum_card :
      ∑ w : G, cosetInner H (cosetOneHot H (g * w)) (cosetOneHot H (h * w)) =
        ((Finset.univ.filter fun w : G => w⁻¹ * (g⁻¹ * h) * w ∈ H).card : ℝ) := by
    simp_rw [cosetInner_cosetOneHot_eq H g h]
    rw [← Finset.sum_filter (p := fun w : G => w⁻¹ * (g⁻¹ * h) * w ∈ H) (f := fun _ => (1 : ℝ))]
    simp [Finset.sum_const, nsmul_eq_mul]
  rw [hsum_card]
  have hcount := card_filter_conj_mem_eq H (g⁻¹ * h)
  rw [hcount]
  push_cast
  have hlag : H.index * Fintype.card H = Fintype.card G := by
    simpa [Nat.card_eq_fintype_card] using Subgroup.index_mul_card H
  have hH_ne : (Fintype.card H : ℝ) ≠ 0 := by exact_mod_cast Fintype.card_ne_zero
  have hG_cast : (Fintype.card G : ℝ) = (H.index : ℝ) * (Fintype.card H : ℝ) := by
    exact_mod_cast hlag.symm
  rw [hG_cast, one_div, mul_inv_rev]
  have hcancel :
      ((Fintype.card H : ℝ)⁻¹ * (H.index : ℝ)⁻¹) *
          ((Fintype.card H : ℝ) * ((Finset.univ.filter fun q : G ⧸ H => (g⁻¹ * h) • q = q).card : ℝ)) =
        ((Finset.univ.filter fun q : G ⧸ H => (g⁻¹ * h) • q = q).card : ℝ) * (H.index : ℝ)⁻¹ := by
    calc
      ((Fintype.card H : ℝ)⁻¹ * (H.index : ℝ)⁻¹) *
          ((Fintype.card H : ℝ) * ((Finset.univ.filter fun q : G ⧸ H => (g⁻¹ * h) • q = q).card : ℝ))
          = ((Fintype.card H : ℝ)⁻¹ * (Fintype.card H : ℝ)) * (H.index : ℝ)⁻¹ *
              ((Finset.univ.filter fun q : G ⧸ H => (g⁻¹ * h) • q = q).card : ℝ) := by
            simp only [mul_assoc, mul_left_comm]
      _ = (1 * (H.index : ℝ)⁻¹) *
            ((Finset.univ.filter fun q : G ⧸ H => (g⁻¹ * h) • q = q).card : ℝ) := by
            rw [inv_mul_cancel₀ hH_ne]
      _ = ((Finset.univ.filter fun q : G ⧸ H => (g⁻¹ * h) • q = q).card : ℝ) * (H.index : ℝ)⁻¹ := by
            rw [one_mul, mul_comm]
  rw [hcancel, ← div_eq_mul_inv]
  congr 1
  unfold permChar
  rw [Fintype.card_subtype]

/-- Equivalent form writing the index `[G : H]` explicitly as `Fintype.card (G ⧸ H)`. -/
theorem predictive_kernel_coset_expectation_card_quotient {G : Type*} [Group G] [Fintype G]
    (H : Subgroup G) (g h : G) :
    (1 / (Fintype.card G : ℝ)) *
        ∑ w : G, cosetInner H (cosetOneHot H (g * w)) (cosetOneHot H (h * w)) =
      permChar H (g⁻¹ * h) / (Fintype.card (G ⧸ H) : ℝ) := by
  rw [predictive_kernel_coset_expectation H g h]
  have hidx : H.index = Fintype.card (G ⧸ H) := by
    rw [Subgroup.index, Nat.card_eq_fintype_card]
  rw [hidx]

end ExpectationIdentity

end PredictiveKernel
