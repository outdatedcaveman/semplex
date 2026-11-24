/-
  Mathlib formalization for Arbitrary Finite-Group Gauge-Ring Orbits,
  Conjugation-Equivariant Markov Lifts, Symmetric Observation Channel Thresholds,
  and the Two-Loop `S₃` Counterexample (`gemini/master-principle-variational`).

  Generalizes ChatGPT's Spike 25/26 (`Z₃`, `S₃`, `D₄`) finite-instance results to:
  - ANY group `G` and ANY directed ring length `L + 1 ≥ 1`;
  - ANY finite conjugation-equivariant class transition kernel `P`;
  - ANY finite outcome/sector cardinality `n ≥ 2` and the full stochastic channel
    domain `η ∈ [0, 1/(n-1)]` (proving separation holds iff `η ≠ 1/n`, even on `(1/n, 1/(n-1)]`);
  - Mechanized counterexample showing per-loop conjugacy-class quotienting fails for `b₁ ≥ 2`.

  Isolated in `proofs/lean-mathlib/` so `proofs/lean/` remains core Lean 4.
-/
import Mathlib.Algebra.Group.Conj
import Mathlib.Algebra.Group.ConjFinite
import Mathlib.Data.Fintype.BigOperators
import Mathlib.Data.Fintype.Card
import Mathlib.Data.Fintype.Pi
import Mathlib.Data.Matrix.Basic
import Mathlib.Data.Real.Basic
import Mathlib.GroupTheory.Perm.Fin
import Mathlib.LinearAlgebra.Matrix.DotProduct
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring

open scoped BigOperators Matrix

namespace MasterPrincipleGauge

noncomputable section
set_option linter.unusedSectionVars false

section GaugeRing

variable {G : Type*} [Group G] {L : ℕ}

/-- Cyclic next vertex along a directed `(L + 1)`-edge ring. -/
def nextIdx {L : ℕ} (i : Fin (L + 1)) : Fin (L + 1) :=
  ⟨(i.1 + 1) % (L + 1), Nat.mod_lt _ (Nat.succ_pos L)⟩

private def stepIdx (L : ℕ) (m : ℕ) : Fin (L + 1) :=
  ⟨m % (L + 1), Nat.mod_lt _ (Nat.succ_pos L)⟩

private theorem nextIdx_stepIdx (L m : ℕ) :
    nextIdx (stepIdx L m) = stepIdx L (m + 1) := by
  apply Fin.ext
  simp [nextIdx, stepIdx, Nat.add_mod]

/-- Vertex-gauge group action `(g • A)_i = g_{i+1} A_i g_i⁻¹`. -/
def gaugeAct (g A : Fin (L + 1) → G) (i : Fin (L + 1)) : G :=
  g (nextIdx i) * A i * (g i)⁻¹

/-- Ordered edge composition along the directed ring starting at vertex `0`. -/
def pathProd (A : Fin (L + 1) → G) : ℕ → G
  | 0 => 1
  | k + 1 => A ⟨k % (L + 1), Nat.mod_lt _ (Nat.succ_pos L)⟩ * pathProd A k

/-- Full base-pointed Wilson-loop holonomy `H(A) = A_L ⋯ A_1 A_0`. -/
def wilsonLoop (A : Fin (L + 1) → G) : G :=
  pathProd A (L + 1)

theorem pathProd_gaugeAct (g A : Fin (L + 1) → G) :
    ∀ k : ℕ, pathProd (gaugeAct g A) k = g (stepIdx L k) * pathProd A k * (g 0)⁻¹
  | 0 => by
      have hz : stepIdx L 0 = (0 : Fin (L + 1)) := Fin.ext (Nat.zero_mod _)
      simp [pathProd, hz]
  | k + 1 => by
      rw [pathProd, pathProd_gaugeAct g A k, pathProd]
      change gaugeAct g A (stepIdx L k) * (g (stepIdx L k) * pathProd A k * (g 0)⁻¹) =
        g (stepIdx L (k + 1)) * (A (stepIdx L k) * pathProd A k) * (g 0)⁻¹
      unfold gaugeAct
      rw [nextIdx_stepIdx]
      group

/-- Full base-frame covariance of the ordered Wilson loop for ANY group `G` and ANY `L + 1 ≥ 1`. -/
theorem wilsonLoop_gauge_covariant (g A : Fin (L + 1) → G) :
    wilsonLoop (gaugeAct g A) = g 0 * wilsonLoop A * (g 0)⁻¹ := by
  unfold wilsonLoop
  rw [pathProd_gaugeAct]
  have h0 : stepIdx L (L + 1) = (0 : Fin (L + 1)) := Fin.ext (Nat.mod_self (L + 1))
  rw [h0]

/-- Orbit classification theorem for arbitrary `G` and arbitrary ring length `L + 1`:
    two connections lie in the same vertex-gauge orbit iff their Wilson loops are conjugate. -/
private def canonGauge (A A' : Fin (L + 1) → G) (k : G) (i : Fin (L + 1)) : G :=
  pathProd A' i.1 * k * (pathProd A i.1)⁻¹

private theorem canonGauge_act (A A' : Fin (L + 1) → G) (k : G)
    (hk : k * wilsonLoop A * k⁻¹ = wilsonLoop A') :
    gaugeAct (canonGauge A A' k) A = A' := by
  funext i
  unfold gaugeAct canonGauge
  have hi_lt : i.1 < L + 1 := i.isLt
  have hi_mod : (⟨i.1 % (L + 1), Nat.mod_lt _ (Nat.succ_pos L)⟩ : Fin (L + 1)) = i :=
    Fin.ext (Nat.mod_eq_of_lt hi_lt)
  have hpA : pathProd A (i.1 + 1) = A i * pathProd A i.1 := by
    rw [pathProd, hi_mod]
  have hpA' : pathProd A' (i.1 + 1) = A' i * pathProd A' i.1 := by
    rw [pathProd, hi_mod]
  by_cases hlast : i.1 + 1 < L + 1
  · have hnext : (nextIdx i).1 = i.1 + 1 := by
      simp [nextIdx, Nat.mod_eq_of_lt hlast]
    simp only [hnext, hpA, hpA']
    group
  · have heqL1 : i.1 + 1 = L + 1 := by omega
    have hnext0 : (nextIdx i).1 = 0 := by
      simp [nextIdx, heqL1]
    have hwA : wilsonLoop A = A i * pathProd A i.1 := by
      unfold wilsonLoop
      conv_lhs => rw [← heqL1]
      exact hpA
    have hwA' : wilsonLoop A' = A' i * pathProd A' i.1 := by
      unfold wilsonLoop
      conv_lhs => rw [← heqL1]
      exact hpA'
    simp only [hnext0, pathProd, mul_one, one_mul, inv_one]
    calc (k * A i) * (pathProd A' i.1 * k * (pathProd A i.1)⁻¹)⁻¹
        = (k * (A i * pathProd A i.1) * k⁻¹) * (pathProd A' i.1)⁻¹ := by group
      _ = (k * wilsonLoop A * k⁻¹) * (pathProd A' i.1)⁻¹ := by rw [← hwA]
      _ = wilsonLoop A' * (pathProd A' i.1)⁻¹ := by rw [hk]
      _ = (A' i * pathProd A' i.1) * (pathProd A' i.1)⁻¹ := by rw [hwA']
      _ = A' i := by group

theorem gaugeAct_mul (g₁ g₂ A : Fin (L + 1) → G) :
    gaugeAct (fun i => g₁ i * g₂ i) A = gaugeAct g₁ (gaugeAct g₂ A) := by
  funext i
  unfold gaugeAct
  group

theorem gaugeAct_one (A : Fin (L + 1) → G) :
    gaugeAct (fun _ => (1 : G)) A = A := by
  funext i
  simp [gaugeAct]

/-- Full faithfulness of the holonomy functor `Conn(G)//G^{L+1} → G//G`:
    exact bijection between vertex-gauge morphisms `A → A'` and conjugation morphisms
    `H(A) → H(A')` for any group `G` and ring length `L + 1`. -/
def gaugeHomEquiv (A A' : Fin (L + 1) → G) :
    { g : Fin (L + 1) → G // gaugeAct g A = A' } ≃
      { k : G // k * wilsonLoop A * k⁻¹ = wilsonLoop A' } where
  toFun := fun ⟨g, hg⟩ => ⟨g 0, by
    calc g 0 * wilsonLoop A * (g 0)⁻¹ = wilsonLoop (gaugeAct g A) := (wilsonLoop_gauge_covariant g A).symm
      _ = wilsonLoop A' := by rw [hg]⟩
  invFun := fun ⟨k, hk⟩ => ⟨canonGauge A A' k, canonGauge_act A A' k hk⟩
  left_inv := by
    rintro ⟨g, hg⟩
    apply Subtype.ext
    funext i
    have hstep : stepIdx L i.1 = i := Fin.ext (Nat.mod_eq_of_lt i.isLt)
    have hpath := pathProd_gaugeAct g A i.1
    rw [hg, hstep] at hpath
    dsimp only
    unfold canonGauge
    rw [hpath]
    group
  right_inv := by
    rintro ⟨k, hk⟩
    apply Subtype.ext
    simp [canonGauge, pathProd]

/-- Group isomorphism (multiplicative bijection) between gauge stabilizers at `A`
    and centralizer elements of the loop holonomy `wilsonLoop A`. -/
theorem gaugeStabilizer_bijective_centralizer (A : Fin (L + 1) → G) :
    let stabHom := fun (g : { g : Fin (L + 1) → G // gaugeAct g A = A }) =>
      (⟨g.1 0, mul_inv_eq_iff_eq_mul.mp (gaugeHomEquiv A A g).2⟩ :
        { k : G // k * wilsonLoop A = wilsonLoop A * k })
    Function.Bijective stabHom ∧
      (∀ g₁ g₂ : { g : Fin (L + 1) → G // gaugeAct g A = A },
        (stabHom ⟨fun i => g₁.1 i * g₂.1 i, by rw [gaugeAct_mul, g₂.2, g₁.2]⟩).1 =
          (stabHom g₁).1 * (stabHom g₂).1) := by
  intro stabHom
  refine ⟨?_, fun g₁ g₂ => rfl⟩
  let eCen : { k : G // k * wilsonLoop A * k⁻¹ = wilsonLoop A } ≃
      { k : G // k * wilsonLoop A = wilsonLoop A * k } :=
    { toFun := fun ⟨k, hk⟩ => ⟨k, mul_inv_eq_iff_eq_mul.mp hk⟩
      invFun := fun ⟨k, hk⟩ => ⟨k, mul_inv_eq_iff_eq_mul.mpr hk⟩
      left_inv := fun ⟨_, _⟩ => rfl
      right_inv := fun ⟨_, _⟩ => rfl }
  exact ((gaugeHomEquiv A A).trans eCen).bijective

theorem gaugeOrbit_iff_isConj (A A' : Fin (L + 1) → G) :
    (∃ g, gaugeAct g A = A') ↔ IsConj (wilsonLoop A) (wilsonLoop A') := by
  constructor
  · rintro ⟨g, rfl⟩
    exact isConj_iff.mpr ⟨g 0, (wilsonLoop_gauge_covariant g A).symm⟩
  · intro hconj
    rcases isConj_iff.mp hconj with ⟨c, hc⟩
    exact ⟨canonGauge A A' c, canonGauge_act A A' c hc⟩

private def prefixPath {G : Type*} [Group G] {L : ℕ} (p : Fin L → G) : ℕ → G
  | 0 => 1
  | k + 1 =>
      (if h : k < L then p ⟨k, h⟩ else 1) * prefixPath p k

private theorem pathProd_eq_prefixPath (A : Fin (L + 1) → G) :
    ∀ k : ℕ, k ≤ L → pathProd A k = prefixPath (fun j : Fin L => A j.castSucc) k
  | 0, _ => rfl
  | k + 1, hk => by
      have hkL : k < L := by omega
      have hkLt : k < L + 1 := by omega
      have hmod : (⟨k % (L + 1), Nat.mod_lt _ (Nat.succ_pos L)⟩ : Fin (L + 1)) =
          (⟨k, hkL⟩ : Fin L).castSucc := by
        ext
        exact Nat.mod_eq_of_lt hkLt
      rw [pathProd, prefixPath, pathProd_eq_prefixPath A k (by omega), hmod]
      simp [hkL]

private theorem pathProd_invFun_L (p : Fin L → G) (w : G) :
    pathProd (fun i : Fin (L + 1) => if h : i.1 < L then p ⟨i.1, h⟩ else w * (prefixPath p L)⁻¹) L =
      prefixPath p L := by
  have heq : (fun j : Fin L =>
      if h : (j.castSucc : Fin (L + 1)).1 < L then p ⟨(j.castSucc : Fin (L + 1)).1, h⟩
      else w * (prefixPath p L)⁻¹) = p := by
    funext j
    simp [Fin.coe_castSucc, j.isLt]
  rw [pathProd_eq_prefixPath _ L (Nat.le_refl L), heq]

/-- Explicit bijection `(Fin (L + 1) → G) ≃ (Fin L → G) × G` isolating prefix edges and holonomy. -/
def connEquiv (G : Type*) [Group G] (L : ℕ) :
    (Fin (L + 1) → G) ≃ (Fin L → G) × G where
  toFun A := (fun j : Fin L => A j.castSucc, wilsonLoop A)
  invFun pw := fun i =>
    if h : i.1 < L then pw.1 ⟨i.1, h⟩ else pw.2 * (prefixPath pw.1 L)⁻¹
  left_inv A := by
    funext i
    by_cases h : i.1 < L
    · simp only [h, ↓reduceDIte]
      rfl
    · have hiL : i.1 = L := by omega
      have hmod : (⟨L % (L + 1), Nat.mod_lt _ (Nat.succ_pos L)⟩ : Fin (L + 1)) = i := by
        ext
        simp [hiL, Nat.mod_eq_of_lt (Nat.lt_succ_self L)]
      simp only [h, ↓reduceDIte]
      unfold wilsonLoop
      rw [pathProd, hmod, pathProd_eq_prefixPath A L (Nat.le_refl L)]
      group
  right_inv := by
    rintro ⟨p, w⟩
    ext1
    · funext j
      simp [Fin.coe_castSucc, j.isLt]
    · simp only [wilsonLoop]
      have hmod : (⟨L % (L + 1), Nat.mod_lt _ (Nat.succ_pos L)⟩ : Fin (L + 1)) =
          ⟨L, Nat.lt_succ_self L⟩ := by
        ext
        exact Nat.mod_eq_of_lt (Nat.lt_succ_self L)
      rw [pathProd, hmod, pathProd_invFun_L p w]
      simp only [lt_self_iff_false, ↓reduceDIte]
      group

/-- Universal gauge-orbit cardinality formula for EVERY finite group `G` and ANY ring size `L + 1`:
    `|orbit(A)| = |G|^L * |[H(A)]|` (specializing at `L = 2` to `|G|^2 * |[H(A)]|`). -/
theorem gaugeOrbit_card_eq [Fintype G] [DecidableEq G] (A : Fin (L + 1) → G) :
    Fintype.card { A' : Fin (L + 1) → G // ∃ g, gaugeAct g A = A' } =
      (Fintype.card G) ^ L * Fintype.card { h : G // IsConj (wilsonLoop A) h } := by
  classical
  have eOrb : { A' : Fin (L + 1) → G // ∃ g, gaugeAct g A = A' } ≃
      { A' : Fin (L + 1) → G // IsConj (wilsonLoop A) (wilsonLoop A') } :=
    Equiv.subtypeEquivRight fun A' => gaugeOrbit_iff_isConj A A'
  have eProd : { A' : Fin (L + 1) → G // IsConj (wilsonLoop A) (wilsonLoop A') } ≃
      (Fin L → G) × { h : G // IsConj (wilsonLoop A) h } :=
    { toFun := fun ⟨A', hA'⟩ => ((connEquiv G L A').1, ⟨(connEquiv G L A').2, hA'⟩)
      invFun := fun ⟨p, ⟨h, hh⟩⟩ =>
        ⟨(connEquiv G L).symm (p, h), by
          change IsConj (wilsonLoop A) ((connEquiv G L ((connEquiv G L).symm (p, h))).2)
          rw [Equiv.apply_symm_apply]
          exact hh⟩
      left_inv := by
        rintro ⟨A', hA'⟩
        ext i
        exact congr_fun ((connEquiv G L).left_inv A') i
      right_inv := by
        rintro ⟨p, ⟨h, hh⟩⟩
        dsimp only
        simp only [Equiv.apply_symm_apply] }
  rw [Fintype.card_congr (eOrb.trans eProd), Fintype.card_prod, Fintype.card_fun, Fintype.card_fin]

end GaugeRing

section ClassMarkovLift

variable {G : Type*} [Group G] [Fintype G] [DecidableEq G]

open Classical in
/-- Cardinality of the conjugacy class of `x : G`. -/
def conjClassCard (x : G) : ℕ :=
  (Finset.univ.filter fun y : G => ConjClasses.mk y = ConjClasses.mk x).card

open Classical in
theorem conjClassCard_pos (x : G) : 0 < conjClassCard x := by
  unfold conjClassCard
  exact Finset.card_pos.mpr ⟨x, Finset.mem_filter.mpr ⟨Finset.mem_univ x, rfl⟩⟩

open Classical in
/-- Uniform class-kernel lift `Q(g, g') = P([g], [g']) / |[g']|` for any finite group `G`. -/
def classKernelLift (P : ConjClasses G → ConjClasses G → ℝ) (g g' : G) : ℝ :=
  P (ConjClasses.mk g) (ConjClasses.mk g') / (conjClassCard g' : ℝ)

open Classical in
theorem classKernelLift_nonneg (P : ConjClasses G → ConjClasses G → ℝ)
    (hP : ∀ c c' : ConjClasses G, 0 ≤ P c c') (g g' : G) :
    0 ≤ classKernelLift P g g' :=
  div_nonneg (hP _ _) (Nat.cast_nonneg _)

open Classical in
theorem classKernelLift_conj_equivariant (P : ConjClasses G → ConjClasses G → ℝ)
    (k g g' : G) :
    classKernelLift P (k * g * k⁻¹) (k * g' * k⁻¹) = classKernelLift P g g' := by
  have hmk1 : ConjClasses.mk (k * g * k⁻¹) = ConjClasses.mk g :=
    (ConjClasses.mk_eq_mk_iff_isConj.mpr (isConj_iff.mpr ⟨k, rfl⟩)).symm
  have hmk2 : ConjClasses.mk (k * g' * k⁻¹) = ConjClasses.mk g' :=
    (ConjClasses.mk_eq_mk_iff_isConj.mpr (isConj_iff.mpr ⟨k, rfl⟩)).symm
  simp only [classKernelLift, conjClassCard, hmk1, hmk2]

open Classical in
theorem classKernelLift_row_stochastic (P : ConjClasses G → ConjClasses G → ℝ)
    (hstoch : ∀ c : ConjClasses G, ∑ c' : ConjClasses G, P c c' = 1) (g : G) :
    ∑ g' : G, classKernelLift P g g' = 1 := by
  have hfib := (Finset.sum_fiberwise (Finset.univ : Finset G) ConjClasses.mk
    (fun g' => classKernelLift P g g')).symm
  rw [hfib]
  have hclass : ∀ c : ConjClasses G,
      (∑ g' ∈ (Finset.univ : Finset G).filter (fun x => ConjClasses.mk x = c),
        classKernelLift P g g') = P (ConjClasses.mk g) c := by
    intro c
    rcases Quot.exists_rep c with ⟨x₀, hxc⟩
    subst hxc
    change (∑ g' ∈ (Finset.univ : Finset G).filter (fun x => ConjClasses.mk x = ConjClasses.mk x₀),
        classKernelLift P g g') = P (ConjClasses.mk g) (ConjClasses.mk x₀)
    have hconst : ∀ g' ∈ (Finset.univ : Finset G).filter (fun x => ConjClasses.mk x = ConjClasses.mk x₀),
        classKernelLift P g g' =
          P (ConjClasses.mk g) (ConjClasses.mk x₀) / (conjClassCard x₀ : ℝ) := by
      intro g' hg'
      have hmk : ConjClasses.mk g' = ConjClasses.mk x₀ := (Finset.mem_filter.mp hg').2
      simp only [classKernelLift, conjClassCard, hmk]
    rw [Finset.sum_congr rfl hconst, Finset.sum_const, nsmul_eq_mul]
    have hpos : (conjClassCard x₀ : ℝ) ≠ 0 := Nat.cast_ne_zero.mpr (conjClassCard_pos x₀).ne'
    change ((conjClassCard x₀ : ℝ)) * (P (ConjClasses.mk g) (ConjClasses.mk x₀) / (conjClassCard x₀ : ℝ)) =
      P (ConjClasses.mk g) (ConjClasses.mk x₀)
    field_simp [hpos]
  simp_rw [hclass]
  exact hstoch (ConjClasses.mk g)

end ClassMarkovLift

section SymmetricChannel

variable {ι : Type*} [Fintype ι] [DecidableEq ι]

/-- Symmetric `n`-sector noise channel `K_n(η) = η 11ᵀ + (1 - n η) I`. -/
def symChannel (ι : Type*) [Fintype ι] [DecidableEq ι] (η : ℝ) : Matrix ι ι ℝ :=
  fun i j => (if i = j then 1 - (Fintype.card ι : ℝ) * η else 0) + η

theorem symChannel_vecMul_eval (η : ℝ) (v : ι → ℝ) (j : ι) :
    (v ᵥ* symChannel ι η) j =
      (1 - (Fintype.card ι : ℝ) * η) * v j + η * ∑ i : ι, v i := by
  simp only [Matrix.vecMul, Matrix.dotProduct, symChannel, mul_add, Finset.sum_add_distrib]
  simp only [mul_ite, mul_zero, Finset.sum_ite_eq', Finset.mem_univ, ↓reduceIte, ← Finset.sum_mul]
  ring

theorem symChannel_row_sum (η : ℝ) (i : ι) :
    ∑ j : ι, symChannel ι η i j = 1 := by
  simp only [symChannel, Finset.sum_add_distrib, Finset.sum_ite_eq, Finset.mem_univ, ↓reduceIte,
    Finset.sum_const, Finset.card_univ, nsmul_eq_mul]
  ring

/-- Centered vectors scale cleanly by `1 - n η` under `K_n(η)`. -/
theorem symChannel_vecMul_centered (η : ℝ) (v : ι → ℝ) (h0 : ∑ i : ι, v i = 0) :
    v ᵥ* symChannel ι η = (1 - (Fintype.card ι : ℝ) * η) • v := by
  funext j
  rw [symChannel_vecMul_eval, h0, mul_zero, add_zero, Pi.smul_apply, smul_eq_mul]

/-- At `η = 1 / n`, every probability vector collapses identically to the uniform distribution `1 / n`. -/
theorem symChannel_uniform_erasure (hn : (Fintype.card ι : ℝ) ≠ 0) (b : ι → ℝ)
    (hb : ∑ i : ι, b i = 1) (j : ι) :
    (b ᵥ* symChannel ι (1 / (Fintype.card ι : ℝ))) j = 1 / (Fintype.card ι : ℝ) := by
  rw [symChannel_vecMul_eval, hb]
  field_simp [hn]

/-- Exact simplex separation threshold (valid on the FULL stochastic domain `[0, 1/(n-1)]`,
    explicitly including `η ∈ (1/n, 1/(n-1)]`): `K_n(η)` separates all simplex beliefs iff `η ≠ 1/n`. -/
theorem symChannel_separates_simplex_iff (hcard : 2 ≤ Fintype.card ι) (η : ℝ) :
    (∀ b b' : ι → ℝ, (∑ i, b i = 1) → (∑ i, b' i = 1) →
      b ᵥ* symChannel ι η = b' ᵥ* symChannel ι η → b = b') ↔
      η ≠ 1 / (Fintype.card ι : ℝ) := by
  have hn_pos : (0 : ℝ) < Fintype.card ι := by positivity
  have hn_ne : (Fintype.card ι : ℝ) ≠ 0 := hn_pos.ne'
  constructor
  · intro hsep hη
    subst hη
    have hex : ∃ x y : ι, x ≠ y := Fintype.one_lt_card_iff.mp (by omega)
    rcases hex with ⟨x, y, hxy⟩
    let b : ι → ℝ := fun i => if i = x then 1 else 0
    let b' : ι → ℝ := fun i => if i = y then 1 else 0
    have hb : ∑ i, b i = 1 := by simp [b]
    have hb' : ∑ i, b' i = 1 := by simp [b']
    have heq_out : b ᵥ* symChannel ι (1 / (Fintype.card ι : ℝ)) =
        b' ᵥ* symChannel ι (1 / (Fintype.card ι : ℝ)) := by
      funext j
      rw [symChannel_uniform_erasure hn_ne b hb j, symChannel_uniform_erasure hn_ne b' hb' j]
    have heq := hsep b b' hb hb' heq_out
    have := congrFun heq x
    simp [b, b', hxy] at this
  · intro hη b b' hb hb' heq
    have hcoeff : 1 - (Fintype.card ι : ℝ) * η ≠ 0 := by
      intro hz
      apply hη
      field_simp [hn_ne]
      linarith
    funext j
    have hj := congrFun heq j
    rw [symChannel_vecMul_eval, symChannel_vecMul_eval, hb, hb'] at hj
    have hmul : (1 - (Fintype.card ι : ℝ) * η) * (b j - b' j) = 0 := by linarith
    have hdiff := (mul_eq_zero.mp hmul).resolve_left hcoeff
    linarith

end SymmetricChannel

section MultiLoopCounterexample

/-- Two-loop bouquet (`b₁ ≥ 2`) counterexample on `G = S₃`:
    `(s₀₁, s₀₁)` and `(s₀₁, s₁₂)` share identical per-loop conjugacy classes
    yet have distinct holonomy products (`e` vs `c₀₁₂`) and cannot lie in the same
    simultaneous `Ad(S₃)` orbit. Per-loop class quotienting fails for `b₁ ≥ 2`. -/
theorem twoLoop_s3_simultaneous_conj_counterexample :
    let s01 : Equiv.Perm (Fin 3) := Equiv.swap 0 1
    let s12 : Equiv.Perm (Fin 3) := Equiv.swap 1 2
    IsConj s01 s01 ∧ IsConj s01 s12 ∧ s01 * s01 ≠ s01 * s12 ∧
      ¬ ∃ k : Equiv.Perm (Fin 3), k * s01 * k⁻¹ = s01 ∧ k * s01 * k⁻¹ = s12 := by
  intro s01 s12
  refine ⟨IsConj.refl s01, ?_, ?_, ?_⟩
  · refine isConj_iff.mpr ⟨Equiv.swap 0 2, ?_⟩
    decide
  · decide
  · rintro ⟨k, h1, h2⟩
    have hsame : s01 = s12 := h1.symm.trans h2
    exact (by decide : Equiv.swap (0 : Fin 3) 1 ≠ Equiv.swap 1 2) hsame

end MultiLoopCounterexample

end
end MasterPrincipleGauge
