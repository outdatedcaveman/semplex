import QuantitativeGaugeStability
import ContinuumKernelCovariance

/-!
# Finite-State Dobrushin TV Contraction, Product Anchor Intersection & Master Principle Closure

Completes the quantitative continuum + finite-Markov bridge of the Semplex-Synesism
Master Principle over Mathlib v4.12.0:

1. **First-Principles Finite-State Total Variation Metric (`tvDist`):**
   Proves `tvDist_nonneg`, `tvDist_self`, `tvDist_symm`, `tvDist_triangle`, and
   Stochastic pushforward conservation `pushVec_isProbVec`.
2. **Dobrushin Total-Variation Contraction (`dobrushin_tv_contraction`):**
   Via signed Jordan positive/negative mass decomposition `p = max (μ - ν) 0`,
   `q = max (ν - μ) 0`, proves `tvDist (pushVec μ P) (pushVec ν P) ≤ c * tvDist μ ν`
   from first principles without Gaussian linearity assumptions.
3. **Perturbed Markov-Dobrushin Horizon Stability (`dobrushin_horizon_stability`):**
   Proves per-step kernel perturbation bounds `pushVec_tvDist_step_perturb`, one-step
   triangle stability, geometric finite-horizon error bounds (via
   `contraction_horizon_bound`), and uniform asymptotic ceilings `dobrushin_uniform_ceiling`.
4. **Indexed Product Anchor Kernel Intersection (`ae_product_anchor_kernel_inter`):**
   Proves that a countable family of `μ`-a.e. measurable anchors stabilizes a gauge
   automorphism if and only if each coordinate anchor does, characterizing
   `⋂ j, Fix_ae(κ_j)`.
5. **Unified Master Principle Capstone (`master_principle_universal_closure`):**
   Packages Borel continuum profile invariance, `μ`-a.e. product-anchor trivialization,
   observable-subspace `ker W` tube escape bounds, and Dobrushin contraction horizon
   stability into one cohesive theorem.
-/

open MeasureTheory ProbabilityTheory Function Set Filter Finset
open scoped BigOperators ENNReal Topology

namespace Semplex.MasterPrincipleUniversalClosure

open Semplex.ContinuumKernelCovariance
open Semplex.QuantitativeGaugeStability

section FiniteStateDobrushin

variable {α : Type*} [Fintype α]

/-- Total variation distance `½ ∑ᵢ |μᵢ - νᵢ|` on finite-state real vectors. -/
noncomputable def tvDist (μ ν : α → ℝ) : ℝ :=
  (1 / 2 : ℝ) * ∑ i : α, |μ i - ν i|

/-- Nonnegative real vector summing to `1`. -/
def IsProbVec (μ : α → ℝ) : Prop :=
  (∀ i, 0 ≤ μ i) ∧ ∑ i : α, μ i = 1

/-- Row-stochastic transition matrix `α → β → ℝ`. -/
def IsMarkovMat {β : Type*} [Fintype β] (P : α → β → ℝ) : Prop :=
  ∀ i, (∀ j, 0 ≤ P i j) ∧ ∑ j : β, P i j = 1

/-- Row-vector pushforward `(μP)_j = ∑ᵢ μᵢ P_{ij}`. -/
def pushVec {β : Type*} [Fintype β] (μ : α → ℝ) (P : α → β → ℝ) : β → ℝ :=
  fun j => ∑ i : α, μ i * P i j

/-- Uniform Dobrushin ergodicity bound: all pairs of rows differ by at most `c` in TV. -/
def dobrushinBound {β : Type*} [Fintype β] (P : α → β → ℝ) (c : ℝ) : Prop :=
  0 ≤ c ∧ ∀ i k, tvDist (P i) (P k) ≤ c

theorem tvDist_nonneg (μ ν : α → ℝ) : 0 ≤ tvDist μ ν :=
  mul_nonneg (by positivity) (Finset.sum_nonneg fun _ _ => abs_nonneg _)

theorem tvDist_self (μ : α → ℝ) : tvDist μ μ = 0 := by
  simp [tvDist]

theorem tvDist_symm (μ ν : α → ℝ) : tvDist μ ν = tvDist ν μ := by
  simp only [tvDist, abs_sub_comm]

theorem tvDist_triangle (μ ν ξ : α → ℝ) :
    tvDist μ ξ ≤ tvDist μ ν + tvDist ν ξ := by
  simp only [tvDist, ← mul_add, ← Finset.sum_add_distrib]
  refine mul_le_mul_of_nonneg_left ?_ (by positivity)
  exact Finset.sum_le_sum fun i _ => abs_sub_le (μ i) (ν i) (ξ i)

theorem pushVec_isProbVec {β : Type*} [Fintype β]
    {μ : α → ℝ} {P : α → β → ℝ}
    (hμ : IsProbVec μ) (hP : IsMarkovMat P) :
    IsProbVec (pushVec μ P) := by
  constructor
  · intro j
    exact Finset.sum_nonneg fun i _ => mul_nonneg (hμ.1 i) ((hP i).1 j)
  · simp only [pushVec]
    rw [Finset.sum_comm]
    calc
      ∑ i : α, ∑ j : β, μ i * P i j
          = ∑ i : α, μ i * ∑ j : β, P i j := by
              refine Finset.sum_congr rfl fun i _ => ?_
              rw [← Finset.mul_sum]
      _ = ∑ i : α, μ i * 1 := by
              refine Finset.sum_congr rfl fun i _ => by rw [(hP i).2]
      _ = 1 := by simpa using hμ.2

/-- First-principles Dobrushin total-variation contraction for finite-state Markov
    pushforwards using signed Jordan decomposition `p = max (μ - ν) 0`,
    `q = max (ν - μ) 0`. -/
theorem dobrushin_tv_contraction {β : Type*} [Fintype β]
    {μ ν : α → ℝ} {P : α → β → ℝ} {c : ℝ}
    (hμ : IsProbVec μ) (hν : IsProbVec ν)
    (_hP : IsMarkovMat P)
    (hD : dobrushinBound P c) :
    tvDist (pushVec μ P) (pushVec ν P) ≤ c * tvDist μ ν := by
  let p : α → ℝ := fun i => max (μ i - ν i) 0
  let q : α → ℝ := fun i => max (ν i - μ i) 0
  have hp_nn : ∀ i, 0 ≤ p i := fun i => le_max_right _ _
  have hq_nn : ∀ i, 0 ≤ q i := fun i => le_max_right _ _
  have hpq_sub : ∀ i, p i - q i = μ i - ν i := fun i => by
    dsimp only [p, q]
    rcases le_total (μ i) (ν i) with h | h
    · rw [max_eq_right (sub_nonpos.mpr h), max_eq_left (sub_nonneg.mpr h)]
      ring
    · rw [max_eq_left (sub_nonneg.mpr h), max_eq_right (sub_nonpos.mpr h)]
      ring
  have hpq_add : ∀ i, p i + q i = |μ i - ν i| := fun i => by
    dsimp only [p, q]
    rcases le_total (μ i) (ν i) with h | h
    · rw [max_eq_right (sub_nonpos.mpr h), max_eq_left (sub_nonneg.mpr h),
        abs_of_nonpos (sub_nonpos.mpr h)]
      ring
    · rw [max_eq_left (sub_nonneg.mpr h), max_eq_right (sub_nonpos.mpr h),
        abs_of_nonneg (sub_nonneg.mpr h)]
      ring
  have hsum_sub : ∑ i : α, p i - ∑ i : α, q i = 0 := by
    rw [← Finset.sum_sub_distrib]
    calc
      ∑ i : α, (p i - q i) = ∑ i : α, (μ i - ν i) :=
          Finset.sum_congr rfl fun i _ => hpq_sub i
      _ = (∑ i : α, μ i) - (∑ i : α, ν i) := Finset.sum_sub_distrib
      _ = 1 - 1 := by rw [hμ.2, hν.2]
      _ = 0 := sub_self 1
  have hMpMq : ∑ i : α, p i = ∑ i : α, q i := sub_eq_zero.mp hsum_sub
  let M : ℝ := ∑ i : α, p i
  have hM_nn : 0 ≤ M := Finset.sum_nonneg fun i _ => hp_nn i
  have hsum_abs : ∑ i : α, |μ i - ν i| = M + M := by
    calc
      ∑ i : α, |μ i - ν i| = ∑ i : α, (p i + q i) :=
          Finset.sum_congr rfl fun i _ => (hpq_add i).symm
      _ = (∑ i : α, p i) + (∑ i : α, q i) := Finset.sum_add_distrib
      _ = M + M := by rw [← hMpMq]
  have hM_tv : M = tvDist μ ν := by
    simp only [tvDist, hsum_abs]
    ring
  rcases eq_or_lt_of_le hM_nn with hM0 | hMpos
  · have hsum0 : ∑ i : α, |μ i - ν i| = 0 := by
      rw [hsum_abs, ← hM0]
      ring
    have habs0 : ∀ i ∈ (Finset.univ : Finset α), |μ i - ν i| = 0 :=
      (Finset.sum_eq_zero_iff_of_nonneg fun i _ => abs_nonneg _).mp hsum0
    have hEq : μ = ν := funext fun i => by
      have hi : |μ i - ν i| = 0 := habs0 i (Finset.mem_univ i)
      exact sub_eq_zero.mp (abs_eq_zero.mp hi)
    subst hEq
    rw [tvDist_self, tvDist_self, mul_zero]
  · have hdiff : ∀ j : β,
        M * (pushVec μ P j - pushVec ν P j) =
          ∑ i : α, ∑ k : α, p i * q k * (P i j - P k j) := fun j => by
      have h1 : pushVec μ P j - pushVec ν P j =
          (∑ i : α, p i * P i j) - (∑ k : α, q k * P k j) := by
        simp only [pushVec]
        rw [← Finset.sum_sub_distrib, ← Finset.sum_sub_distrib]
        refine Finset.sum_congr rfl fun i _ => ?_
        have hs := hpq_sub i
        calc
          μ i * P i j - ν i * P i j = (μ i - ν i) * P i j := by ring
          _ = (p i - q i) * P i j := by rw [hs]
          _ = p i * P i j - q i * P i j := by ring
      rw [h1, mul_sub]
      have hL : M * (∑ i : α, p i * P i j) =
          ∑ i : α, ∑ k : α, p i * q k * P i j := by
        calc
          M * (∑ i : α, p i * P i j)
              = (∑ i : α, p i * P i j) * (∑ k : α, q k) := by
                  rw [← hMpMq, mul_comm]
          _ = ∑ i : α, (p i * P i j) * (∑ k : α, q k) := Finset.sum_mul _ _ _
          _ = ∑ i : α, ∑ k : α, p i * q k * P i j := by
              refine Finset.sum_congr rfl fun i _ => ?_
              rw [Finset.mul_sum]
              refine Finset.sum_congr rfl fun k _ => by ring
      have hR : M * (∑ k : α, q k * P k j) =
          ∑ i : α, ∑ k : α, p i * q k * P k j := by
        calc
          M * (∑ k : α, q k * P k j)
              = (∑ i : α, p i) * (∑ k : α, q k * P k j) := rfl
          _ = ∑ i : α, p i * (∑ k : α, q k * P k j) := Finset.sum_mul _ _ _
          _ = ∑ i : α, ∑ k : α, p i * q k * P k j := by
              refine Finset.sum_congr rfl fun i _ => ?_
              rw [Finset.mul_sum]
              refine Finset.sum_congr rfl fun k _ => by ring
      rw [hL, hR, ← Finset.sum_sub_distrib]
      refine Finset.sum_congr rfl fun i _ => ?_
      rw [← Finset.sum_sub_distrib]
      refine Finset.sum_congr rfl fun k _ => by ring
    have hpt : ∀ j : β,
        M * |pushVec μ P j - pushVec ν P j| ≤
          ∑ i : α, ∑ k : α, p i * q k * |P i j - P k j| := fun j => by
      calc
        M * |pushVec μ P j - pushVec ν P j|
            = |M * (pushVec μ P j - pushVec ν P j)| := by
                rw [abs_mul, abs_of_pos hMpos]
        _ = |∑ i : α, ∑ k : α, p i * q k * (P i j - P k j)| := by rw [hdiff j]
        _ ≤ ∑ i : α, |∑ k : α, p i * q k * (P i j - P k j)| :=
              Finset.abs_sum_le_sum_abs _ _
        _ ≤ ∑ i : α, ∑ k : α, |p i * q k * (P i j - P k j)| := by
              refine Finset.sum_le_sum fun i _ => Finset.abs_sum_le_sum_abs _ _
        _ = ∑ i : α, ∑ k : α, p i * q k * |P i j - P k j| := by
              refine Finset.sum_congr rfl fun i _ => Finset.sum_congr rfl fun k _ => ?_
              rw [abs_mul, abs_of_nonneg (mul_nonneg (hp_nn i) (hq_nn k))]
    have hprod : M * tvDist (pushVec μ P) (pushVec ν P) ≤ M * (c * M) := by
      calc
        M * tvDist (pushVec μ P) (pushVec ν P)
            = (1 / 2 : ℝ) * ∑ j : β, M * |pushVec μ P j - pushVec ν P j| := by
                simp only [tvDist]
                calc
                  M * ((1 / 2 : ℝ) * ∑ j : β, |pushVec μ P j - pushVec ν P j|)
                      = (1 / 2 : ℝ) * (M * ∑ j : β, |pushVec μ P j - pushVec ν P j|) := by ring
                  _ = (1 / 2 : ℝ) * ∑ j : β, M * |pushVec μ P j - pushVec ν P j| := by
                      rw [Finset.mul_sum]
        _ ≤ (1 / 2 : ℝ) * ∑ j : β, ∑ i : α, ∑ k : α, p i * q k * |P i j - P k j| := by
              refine mul_le_mul_of_nonneg_left (Finset.sum_le_sum fun j _ => hpt j) (by positivity)
        _ = (1 / 2 : ℝ) * ∑ i : α, ∑ k : α, ∑ j : β, p i * q k * |P i j - P k j| := by
              congr 1
              rw [Finset.sum_comm]
              refine Finset.sum_congr rfl fun i _ => Finset.sum_comm
        _ = ∑ i : α, ∑ k : α, p i * q k * tvDist (P i) (P k) := by
              rw [Finset.mul_sum]
              refine Finset.sum_congr rfl fun i _ => ?_
              rw [Finset.mul_sum]
              refine Finset.sum_congr rfl fun k _ => ?_
              simp only [tvDist, ← Finset.mul_sum]
              ring
        _ ≤ ∑ i : α, ∑ k : α, p i * q k * c := by
              refine Finset.sum_le_sum fun i _ => Finset.sum_le_sum fun k _ => ?_
              exact mul_le_mul_of_nonneg_left (hD.2 i k) (mul_nonneg (hp_nn i) (hq_nn k))
        _ = M * (c * M) := by
              calc
                ∑ i : α, ∑ k : α, p i * q k * c
                    = ∑ i : α, p i * (∑ k : α, q k * c) := by
                        refine Finset.sum_congr rfl fun i _ => ?_
                        rw [Finset.mul_sum]
                        refine Finset.sum_congr rfl fun k _ => by ring
                _ = (∑ i : α, p i) * ((∑ k : α, q k) * c) := by
                        rw [← Finset.sum_mul, ← Finset.sum_mul]
                _ = M * (c * M) := by
                        rw [← hMpMq]
                        change M * (M * c) = M * (c * M)
                        ring
    rw [← hM_tv]
    exact le_of_mul_le_mul_left hprod hMpos

theorem pushVec_tvDist_step_perturb {β : Type*} [Fintype β]
    {μ : α → ℝ} {P Q : α → β → ℝ} {δ : ℝ}
    (hμ : IsProbVec μ)
    (hpert : ∀ i, tvDist (P i) (Q i) ≤ δ) :
    tvDist (pushVec μ P) (pushVec μ Q) ≤ δ := by
  have hpt : ∀ j : β, |pushVec μ P j - pushVec μ Q j| ≤ ∑ i : α, μ i * |P i j - Q i j| := by
    intro j
    calc
      |pushVec μ P j - pushVec μ Q j|
          = |∑ i : α, μ i * (P i j - Q i j)| := by
              simp only [pushVec, ← Finset.sum_sub_distrib, mul_sub]
      _ ≤ ∑ i : α, |μ i * (P i j - Q i j)| := Finset.abs_sum_le_sum_abs _ _
      _ = ∑ i : α, μ i * |P i j - Q i j| := by
              refine Finset.sum_congr rfl fun i _ => ?_
              rw [abs_mul, abs_of_nonneg (hμ.1 i)]
  calc
    tvDist (pushVec μ P) (pushVec μ Q)
        ≤ (1 / 2 : ℝ) * ∑ j : β, ∑ i : α, μ i * |P i j - Q i j| := by
            refine mul_le_mul_of_nonneg_left (Finset.sum_le_sum fun j _ => hpt j) (by positivity)
    _ = ∑ i : α, μ i * tvDist (P i) (Q i) := by
            rw [Finset.sum_comm, Finset.mul_sum]
            refine Finset.sum_congr rfl fun i _ => ?_
            simp only [tvDist, ← Finset.mul_sum]
            ring
    _ ≤ ∑ i : α, μ i * δ := by
            refine Finset.sum_le_sum fun i _ => ?_
            exact mul_le_mul_of_nonneg_left (hpert i) (hμ.1 i)
    _ = (∑ i : α, μ i) * δ := (Finset.sum_mul _ _ _).symm
    _ = δ := by rw [hμ.2, one_mul]

theorem dobrushin_one_step_stability {β : Type*} [Fintype β]
    {μ ν : α → ℝ} {P Q : α → β → ℝ} {c δ : ℝ}
    (hμ : IsProbVec μ) (hν : IsProbVec ν)
    (hP : IsMarkovMat P)
    (hD : dobrushinBound P c)
    (hpert : ∀ i, tvDist (P i) (Q i) ≤ δ) :
    tvDist (pushVec μ P) (pushVec ν Q) ≤ c * tvDist μ ν + δ := by
  calc
    tvDist (pushVec μ P) (pushVec ν Q)
        ≤ tvDist (pushVec μ P) (pushVec ν P) + tvDist (pushVec ν P) (pushVec ν Q) :=
          tvDist_triangle _ _ _
    _ ≤ c * tvDist μ ν + δ :=
          add_le_add (dobrushin_tv_contraction hμ hν hP hD) (pushVec_tvDist_step_perturb hν hpert)

/-- Exact finite-horizon TV deviation bound for perturbed time-inhomogeneous
    Markov chains satisfying uniform Dobrushin contraction `c < 1` and step
    perturbation `≤ δ`. -/
theorem dobrushin_horizon_stability
    (μseq νseq : ℕ → α → ℝ)
    (P Q : ℕ → α → α → ℝ)
    (c δ : ℝ) (hc1 : c < 1)
    (hμ0 : IsProbVec (μseq 0)) (hν0 : IsProbVec (νseq 0))
    (hP : ∀ t, IsMarkovMat (P t))
    (hQ : ∀ t, IsMarkovMat (Q t))
    (hD : ∀ t, dobrushinBound (P t) c)
    (hstepμ : ∀ t, μseq (t + 1) = pushVec (μseq t) (P t))
    (hstepν : ∀ t, νseq (t + 1) = pushVec (νseq t) (Q t))
    (hpert : ∀ t i, tvDist (P t i) (Q t i) ≤ δ) :
    ∀ T : ℕ,
      tvDist (μseq T) (νseq T) ≤
        c ^ T * tvDist (μseq 0) (νseq 0) + δ * (1 - c ^ T) / (1 - c) := by
  have hprobμ : ∀ t, IsProbVec (μseq t) := fun t => by
    induction t with
    | zero => exact hμ0
    | succ t ih => rw [hstepμ t]; exact pushVec_isProbVec ih (hP t)
  have hprobν : ∀ t, IsProbVec (νseq t) := fun t => by
    induction t with
    | zero => exact hν0
    | succ t ih => rw [hstepν t]; exact pushVec_isProbVec ih (hQ t)
  have hstep : ∀ t, tvDist (μseq (t + 1)) (νseq (t + 1)) ≤ c * tvDist (μseq t) (νseq t) + δ := by
    intro t
    rw [hstepμ t, hstepν t]
    exact dobrushin_one_step_stability (hprobμ t) (hprobν t) (hP t) (hD t) (hpert t)
  exact contraction_horizon_bound (fun t => tvDist (μseq t) (νseq t)) c δ (hD 0).1 hc1 hstep

/-- Uniform horizon-independent ceiling `c^T d₀ + δ / (1 - c)` when `0 ≤ c < 1`,
    contrasting geometric saturation against linear `T * δ` blowup. -/
theorem dobrushin_uniform_ceiling
    (μseq νseq : ℕ → α → ℝ)
    (P Q : ℕ → α → α → ℝ)
    (c δ : ℝ) (hc1 : c < 1) (hδ0 : 0 ≤ δ)
    (hμ0 : IsProbVec (μseq 0)) (hν0 : IsProbVec (νseq 0))
    (hP : ∀ t, IsMarkovMat (P t))
    (hQ : ∀ t, IsMarkovMat (Q t))
    (hD : ∀ t, dobrushinBound (P t) c)
    (hstepμ : ∀ t, μseq (t + 1) = pushVec (μseq t) (P t))
    (hstepν : ∀ t, νseq (t + 1) = pushVec (νseq t) (Q t))
    (hpert : ∀ t i, tvDist (P t i) (Q t i) ≤ δ) :
    ∀ T : ℕ,
      tvDist (μseq T) (νseq T) ≤ c ^ T * tvDist (μseq 0) (νseq 0) + δ / (1 - c) := by
  intro T
  have hbound := dobrushin_horizon_stability μseq νseq P Q c δ hc1 hμ0 hν0 hP hQ hD hstepμ hstepν hpert T
  have hc0 : 0 ≤ c := (hD 0).1
  have hcT : 0 ≤ c ^ T := pow_nonneg hc0 T
  have hden : 0 < 1 - c := sub_pos.mpr hc1
  have hfrac : δ * (1 - c ^ T) / (1 - c) ≤ δ / (1 - c) := by
    refine div_le_div_of_nonneg_right ?_ (le_of_lt hden)
    nlinarith
  exact le_trans hbound (add_le_add_left hfrac _)

end FiniteStateDobrushin

section ProductAnchorKernel

variable {State α Outcome : Type*}
variable [MeasurableSpace State] [MeasurableSpace Outcome]

/-- Countable product anchor stabilizes a `μ`-a.e. gauge automorphism if and only if
    every coordinate anchor in the family does. -/
theorem ae_product_anchor_kernel_inter
    {ι : Type*} [Countable ι] {Anchor : ι → Type*}
    (μ : Measure State) (obs : Kernel State Outcome) (evolve : α → Kernel State State)
    (κ : ∀ j : ι, State → Anchor j)
    (g : AEGaugeIso μ obs evolve) :
    AEAnchorFixes (fun s j => κ j s) g ↔ ∀ j, AEAnchorFixes (κ j) g := by
  constructor
  · intro hprod j
    exact hprod.mono fun s hs => congrFun hs j
  · intro hj
    have hall : ∀ᵐ s ∂μ, ∀ j, κ j (g.stateEquiv s) = κ j s := ae_all_iff.mpr hj
    exact hall.mono fun s hs => funext hs

end ProductAnchorKernel

section UniversalClosureCapstone

/-- **Unified Semplex-Synesism Master Principle Closure:**
    Integrates (1) continuum Standard-Borel response-profile covariance across
    representation maps, (2) countable product-anchor `μ`-a.e. gauge trivialization,
    (3) observable-subspace `ker W` gauge-tube escape lower bounds, and
    (4) first-principles Markov-Dobrushin contraction horizon bounds. -/
theorem master_principle_universal_closure
    -- (1) Continuum response-profile covariance assumptions
    {External State₁ Intervention₁ Outcome₁ State₂ Intervention₂ Outcome₂ : Type*}
    [MeasurableSpace State₁] [MeasurableSpace Outcome₁] [StandardBorelSpace Outcome₁]
    [MeasurableSpace State₂] [MeasurableSpace Outcome₂] [MeasurableSpace.CountablySeparated Outcome₂]
    {E₁ : MeasurableCausalExperiment External State₁ Intervention₁ Outcome₁}
    {E₂ : MeasurableCausalExperiment External State₂ Intervention₂ Outcome₂}
    (R : MeasurableRepMap E₁ E₂ 1)
    (budget : ℕ)
    (haffSurj : ∀ a', E₂.interventionCost a' ≤ budget →
      ∃ a, R.interventionMap a = a' ∧ E₁.interventionCost a ≤ E₂.interventionCost a')
    (hinj : Function.Injective R.outcomeMap)
    -- (2) Continuum μ-a.e. product-anchor trivialization assumptions
    {Act ContState ContOutcome : Type*}
    [MeasurableSpace ContState] [MeasurableSpace ContOutcome]
    (μ : Measure ContState) (obs : Kernel ContState ContOutcome)
    (evolve : Act → Kernel ContState ContState)
    {ι : Type*} [Countable ι] {Anchor : ι → Type*}
    (κ : ∀ j : ι, ContState → Anchor j)
    -- (3) Observable-subspace ker W tube escape assumptions
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (W : E →L[ℝ] ℝ) (x Δpar Δperp : E)
    (hker : W Δperp = 0)
    (hflip : W x * W (x + Δpar + Δperp) ≤ 0)
    -- (4) Finite-state Dobrushin horizon contraction assumptions
    {α : Type*} [Fintype α]
    (μseq νseq : ℕ → α → ℝ)
    (P Q : ℕ → α → α → ℝ)
    (c δ : ℝ) (hc1 : c < 1)
    (hμ0 : IsProbVec (μseq 0)) (hν0 : IsProbVec (νseq 0))
    (hP : ∀ t, IsMarkovMat (P t))
    (hQ : ∀ t, IsMarkovMat (Q t))
    (hD : ∀ t, dobrushinBound (P t) c)
    (hstepμ : ∀ t, μseq (t + 1) = pushVec (μseq t) (P t))
    (hstepν : ∀ t, νseq (t + 1) = pushVec (νseq t) (Q t))
    (hpert : ∀ t i, tvDist (P t i) (Q t i) ≤ δ) :
    (∀ e e', ContinuumObsEqual E₁ budget e e' ↔ ContinuumObsEqual E₂ budget e e') ∧
    ((∀ g : AEGaugeIso μ obs evolve,
        (∀ j, AEAnchorFixes (κ j) g) → aeGaugeRel g (AEGaugeIso.refl μ obs evolve)) ↔
      (∀ g : AEGaugeIso μ obs evolve,
        ¬ aeGaugeRel g (AEGaugeIso.refl μ obs evolve) →
          0 < μ {s | (fun j => κ j (g.stateEquiv s)) ≠ (fun j => κ j s)})) ∧
    (|W x| ≤ ‖W‖ * ‖Δpar‖) ∧
    (∀ T : ℕ, tvDist (μseq T) (νseq T) ≤
      c ^ T * tvDist (μseq 0) (νseq 0) + δ * (1 - c ^ T) / (1 - c)) := by
  refine ⟨?_, ?_, ?_, ?_⟩
  · intro e e'
    exact continuum_profile_iff_standardBorel R budget haffSurj hinj e e'
  · have hiff := ae_anchor_kills_isotropy_iff μ obs evolve (fun s j => κ j s)
    constructor
    · intro hcoord
      refine hiff.mp (fun g hprod => hcoord g ((ae_product_anchor_kernel_inter μ obs evolve κ g).mp hprod))
    · intro hsep g hj
      exact hiff.mpr hsep g ((ae_product_anchor_kernel_inter μ obs evolve κ g).mpr hj)
  · exact gauge_escape_lower_bound W x Δpar Δperp hker hflip
  · exact dobrushin_horizon_stability μseq νseq P Q c δ hc1 hμ0 hν0 hP hQ hD hstepμ hstepν hpert

end UniversalClosureCapstone

end Semplex.MasterPrincipleUniversalClosure
