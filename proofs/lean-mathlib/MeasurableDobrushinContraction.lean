import MasterPrincipleUniversalClosure
import Mathlib.MeasureTheory.Decomposition.Jordan
import Mathlib.MeasureTheory.Integral.Bochner

/-!
# Measurable-Space Dobrushin Total-Variation Contraction & Kernel Composition

Generalizes `MasterPrincipleUniversalClosure.dobrushin_tv_contraction` from finite
`[Fintype α]` probability vectors to arbitrary measurable spaces
`[MeasurableSpace α] [MeasurableSpace β] [MeasurableSpace γ]` and Markov kernels
`K : ProbabilityTheory.Kernel α β` without topological or finite-support assumptions:

1. **Measurable Total-Variation Distance (`measureTV`):**
   Defines `measureTV μ ν := ⨆ s : {s : Set α // MeasurableSet s}, |(μ s.1).toReal - (ν s.1).toReal|`
   and proves `measureTV_nonneg`, `measureTV_self`, `measureTV_symm`,
   `measureTV_triangle`, and `measureTV_le_one`.
2. **Signed Jordan Decomposition Identity:**
   For probability measures `μ, ν`, sets `s = μ.toSignedMeasure - ν.toSignedMeasure` and
   `j = s.toJordanDecomposition`, proving `jordan_pos_eq_neg_univ`, `jordan_add_eq`
   (`μ + j.negPart = ν + j.posPart`), and `measureTV_eq_jordan_univ`.
3. **Measurable Dobrushin Contraction & Composition:**
   Proves `measurable_dobrushin_tv_contraction` (`measureTV (μ.bind K) (ν.bind K) ≤ c * measureTV μ ν`)
   for any `IsMarkovKernel K` satisfying `kernelDobrushinBound K c`, and kernel composition
   submultiplicativity `measurable_dobrushin_comp` (`kernelDobrushinBound (K₂ ∘ₖ K₁) (c₁ * c₂)`).
4. **Perturbed Kernel Horizon Stability & Universal Capstone:**
   Proves `measurable_kernel_step_perturb`, `measurable_dobrushin_one_step_stability`,
   `measurable_dobrushin_horizon_stability`, `measurable_dobrushin_uniform_ceiling`, and
   `measurable_dobrushin_universal_capstone`.
-/

open MeasureTheory ProbabilityTheory Function Set Filter
open scoped ENNReal Topology ProbabilityTheory

namespace Semplex.MeasurableDobrushinContraction

open Semplex.ContinuumKernelCovariance
open Semplex.QuantitativeGaugeStability
open Semplex.MasterPrincipleUniversalClosure

section MeasurableTV

variable {α : Type*} [MeasurableSpace α]

/-- Total-variation distance on arbitrary measurable spaces:
    `sup { |(μ E).toReal - (ν E).toReal| : MeasurableSet E }`. -/
noncomputable def measureTV (μ ν : Measure α) : ℝ :=
  ⨆ E : {s : Set α // MeasurableSet s}, |(μ E.1).toReal - (ν E.1).toReal|

/-- Uniform Dobrushin contraction bound for a Markov kernel `K : Kernel α β`. -/
def kernelDobrushinBound {β : Type*} [MeasurableSpace β]
    (K : Kernel α β) (c : ℝ) : Prop :=
  0 ≤ c ∧ ∀ a b : α, measureTV (K a) (K b) ≤ c

theorem measureTV_bddAbove (μ ν : Measure α)
    [IsFiniteMeasure μ] [IsFiniteMeasure ν] :
    BddAbove (Set.range fun E : {s : Set α // MeasurableSet s} =>
      |(μ E.1).toReal - (ν E.1).toReal|) := by
  refine ⟨(μ Set.univ).toReal + (ν Set.univ).toReal, ?_⟩
  rintro r ⟨E, rfl⟩
  have hμ : (μ E.1).toReal ≤ (μ Set.univ).toReal :=
    ENNReal.toReal_mono (measure_ne_top μ Set.univ) (measure_mono (Set.subset_univ E.1))
  have hν : (ν E.1).toReal ≤ (ν Set.univ).toReal :=
    ENNReal.toReal_mono (measure_ne_top ν Set.univ) (measure_mono (Set.subset_univ E.1))
  have h0μ : 0 ≤ (μ E.1).toReal := ENNReal.toReal_nonneg
  have h0ν : 0 ≤ (ν E.1).toReal := ENNReal.toReal_nonneg
  rw [abs_le]
  constructor <;> linarith

theorem abs_sub_le_measureTV (μ ν : Measure α)
    [IsFiniteMeasure μ] [IsFiniteMeasure ν]
    {E : Set α} (hE : MeasurableSet E) :
    |(μ E).toReal - (ν E).toReal| ≤ measureTV μ ν :=
  le_ciSup (measureTV_bddAbove μ ν) ⟨E, hE⟩

theorem measureTV_le_of_finite {μ ν : Measure α}
    [IsFiniteMeasure μ] [IsFiniteMeasure ν]
    {r : ℝ} (_hr : 0 ≤ r)
    (h : ∀ E : Set α, MeasurableSet E → |(μ E).toReal - (ν E).toReal| ≤ r) :
    measureTV μ ν ≤ r :=
  ciSup_le fun E => h E.1 E.2

theorem measureTV_le_iff {μ ν : Measure α}
    [IsFiniteMeasure μ] [IsFiniteMeasure ν]
    {r : ℝ} (hr : 0 ≤ r) :
    measureTV μ ν ≤ r ↔ ∀ E : Set α, MeasurableSet E → |(μ E).toReal - (ν E).toReal| ≤ r :=
  ⟨fun h _ hE => le_trans (abs_sub_le_measureTV μ ν hE) h, measureTV_le_of_finite hr⟩

theorem measureTV_nonneg (μ ν : Measure α)
    [IsFiniteMeasure μ] [IsFiniteMeasure ν] :
    0 ≤ measureTV μ ν := by
  have h0 := abs_sub_le_measureTV μ ν MeasurableSet.empty
  simp only [measure_empty, ENNReal.zero_toReal, sub_self, abs_zero] at h0
  exact h0

theorem measureTV_self (μ : Measure α) :
    measureTV μ μ = 0 := by
  unfold measureTV
  simp only [sub_self, abs_zero]
  haveI : Nonempty {s : Set α // MeasurableSet s} := ⟨⟨Set.univ, MeasurableSet.univ⟩⟩
  exact ciSup_const

theorem measureTV_symm (μ ν : Measure α) :
    measureTV μ ν = measureTV ν μ := by
  unfold measureTV
  congr 1
  ext E
  exact abs_sub_comm _ _

theorem measureTV_triangle (μ ν ξ : Measure α)
    [IsFiniteMeasure μ] [IsFiniteMeasure ν] [IsFiniteMeasure ξ] :
    measureTV μ ξ ≤ measureTV μ ν + measureTV ν ξ := by
  refine measureTV_le_of_finite (add_nonneg (measureTV_nonneg μ ν) (measureTV_nonneg ν ξ)) ?_
  intro E hE
  calc
    |(μ E).toReal - (ξ E).toReal|
        ≤ |(μ E).toReal - (ν E).toReal| + |(ν E).toReal - (ξ E).toReal| :=
      abs_sub_le _ _ _
    _ ≤ measureTV μ ν + measureTV ν ξ :=
      add_le_add (abs_sub_le_measureTV μ ν hE) (abs_sub_le_measureTV ν ξ hE)

theorem measureTV_le_one (μ ν : Measure α)
    [IsProbabilityMeasure μ] [IsProbabilityMeasure ν] :
    measureTV μ ν ≤ 1 := by
  refine measureTV_le_of_finite zero_le_one ?_
  intro E _
  have hμ0 : 0 ≤ (μ E).toReal := ENNReal.toReal_nonneg
  have hν0 : 0 ≤ (ν E).toReal := ENNReal.toReal_nonneg
  have hμ1 : (μ E).toReal ≤ 1 := by
    simpa [measure_univ] using ENNReal.toReal_mono (measure_ne_top μ Set.univ) (measure_mono (Set.subset_univ E))
  have hν1 : (ν E).toReal ≤ 1 := by
    simpa [measure_univ] using ENNReal.toReal_mono (measure_ne_top ν Set.univ) (measure_mono (Set.subset_univ E))
  rw [abs_le]
  constructor <;> linarith

end MeasurableTV

section JordanBridge

variable {α : Type*} [MeasurableSpace α]

private noncomputable def jordanDiff (μ ν : Measure α)
    [IsFiniteMeasure μ] [IsFiniteMeasure ν] : JordanDecomposition α :=
  (μ.toSignedMeasure - ν.toSignedMeasure).toJordanDecomposition

private theorem jordanDiff_eval (μ ν : Measure α)
    [IsFiniteMeasure μ] [IsFiniteMeasure ν]
    {E : Set α} (hE : MeasurableSet E) :
    (μ E).toReal - (ν E).toReal =
      ((jordanDiff μ ν).posPart E).toReal - ((jordanDiff μ ν).negPart E).toReal := by
  have hdecomp : (jordanDiff μ ν).toSignedMeasure = μ.toSignedMeasure - ν.toSignedMeasure :=
    SignedMeasure.toSignedMeasure_toJordanDecomposition _
  have hEv := congrArg (fun m : SignedMeasure α => m E) hdecomp
  change ((jordanDiff μ ν).posPart.toSignedMeasure -
      (jordanDiff μ ν).negPart.toSignedMeasure) E = (μ.toSignedMeasure - ν.toSignedMeasure) E at hEv
  simp only [VectorMeasure.sub_apply, Measure.toSignedMeasure_apply, if_pos hE] at hEv
  exact hEv.symm

private theorem jordanDiff_pos_finite (μ ν : Measure α)
    [IsFiniteMeasure μ] [IsFiniteMeasure ν] :
    IsFiniteMeasure (jordanDiff μ ν).posPart := inferInstance

private theorem jordanDiff_neg_finite (μ ν : Measure α)
    [IsFiniteMeasure μ] [IsFiniteMeasure ν] :
    IsFiniteMeasure (jordanDiff μ ν).negPart := inferInstance

theorem jordan_add_eq (μ ν : Measure α)
    [IsFiniteMeasure μ] [IsFiniteMeasure ν] :
    μ + (jordanDiff μ ν).negPart = ν + (jordanDiff μ ν).posPart := by
  ext E hE
  have heval := jordanDiff_eval μ ν hE
  have haddL : ((μ + (jordanDiff μ ν).negPart) E).toReal =
      (μ E).toReal + ((jordanDiff μ ν).negPart E).toReal := by
    simp [Measure.add_apply, ENNReal.toReal_add (measure_ne_top μ E)
      (measure_ne_top (jordanDiff μ ν).negPart E)]
  have haddR : ((ν + (jordanDiff μ ν).posPart) E).toReal =
      (ν E).toReal + ((jordanDiff μ ν).posPart E).toReal := by
    simp [Measure.add_apply, ENNReal.toReal_add (measure_ne_top ν E)
      (measure_ne_top (jordanDiff μ ν).posPart E)]
  have htopL : (μ + (jordanDiff μ ν).negPart) E ≠ ⊤ :=
    measure_ne_top (μ + (jordanDiff μ ν).negPart) E
  have htopR : (ν + (jordanDiff μ ν).posPart) E ≠ ⊤ :=
    measure_ne_top (ν + (jordanDiff μ ν).posPart) E
  exact (ENNReal.toReal_eq_toReal htopL htopR).mp (by linarith)

theorem jordan_pos_eq_neg_univ (μ ν : Measure α)
    [IsProbabilityMeasure μ] [IsProbabilityMeasure ν] :
    ((jordanDiff μ ν).posPart Set.univ).toReal =
      ((jordanDiff μ ν).negPart Set.univ).toReal := by
  have heval := jordanDiff_eval μ ν MeasurableSet.univ
  simp only [measure_univ, ENNReal.one_toReal, sub_self] at heval
  linarith

theorem measureTV_eq_jordan_univ (μ ν : Measure α)
    [IsProbabilityMeasure μ] [IsProbabilityMeasure ν] :
    measureTV μ ν = ((jordanDiff μ ν).posPart Set.univ).toReal := by
  let j := jordanDiff μ ν
  have hmass : (j.posPart Set.univ).toReal = (j.negPart Set.univ).toReal :=
    jordan_pos_eq_neg_univ μ ν
  have hle : measureTV μ ν ≤ (j.posPart Set.univ).toReal := by
    refine measureTV_le_of_finite ENNReal.toReal_nonneg ?_
    intro E hE
    have heval : (μ E).toReal - (ν E).toReal = (j.posPart E).toReal - (j.negPart E).toReal :=
      jordanDiff_eval μ ν hE
    have hp1 : (j.posPart E).toReal ≤ (j.posPart Set.univ).toReal :=
      ENNReal.toReal_mono (measure_ne_top j.posPart Set.univ) (measure_mono (Set.subset_univ E))
    have hq1 : (j.negPart E).toReal ≤ (j.negPart Set.univ).toReal :=
      ENNReal.toReal_mono (measure_ne_top j.negPart Set.univ) (measure_mono (Set.subset_univ E))
    have hp0 : 0 ≤ (j.posPart E).toReal := ENNReal.toReal_nonneg
    have hq0 : 0 ≤ (j.negPart E).toReal := ENNReal.toReal_nonneg
    rw [heval, abs_le]
    constructor <;> linarith
  have hge : (j.posPart Set.univ).toReal ≤ measureTV μ ν := by
    rcases j.mutuallySingular with ⟨A, hA, hpA, hqAc⟩
    have hp_split : j.posPart A + j.posPart Aᶜ = j.posPart Set.univ := by
      simpa using measure_add_measure_compl (μ := j.posPart) hA
    have hpAc : j.posPart Aᶜ = j.posPart Set.univ := by
      simpa [hpA] using hp_split
    have hev := abs_sub_le_measureTV μ ν hA.compl
    have heval := jordanDiff_eval μ ν hA.compl
    rw [heval, hpAc, hqAc] at hev
    simpa [abs_of_nonneg ENNReal.toReal_nonneg] using hev
  exact le_antisymm hle hge

end JordanBridge

section DobrushinContraction

private theorem isFiniteMeasure_bind_kernel
    {α β : Type*} [MeasurableSpace α] [MeasurableSpace β]
    (m : Measure α) [IsFiniteMeasure m]
    (K : Kernel α β) [IsMarkovKernel K] :
    IsFiniteMeasure (m.bind K) := by
  constructor
  rw [Measure.bind_apply MeasurableSet.univ (Kernel.measurable K)]
  have hlt : (∫⁻ a : α, (K a) Set.univ ∂m) = m Set.univ := by
    simp only [measure_univ, lintegral_one]
  rw [hlt]
  exact measure_lt_top m Set.univ

private theorem isProbabilityMeasure_bind_kernel
    {α β : Type*} [MeasurableSpace α] [MeasurableSpace β]
    (m : Measure α) [IsProbabilityMeasure m]
    (K : Kernel α β) [IsMarkovKernel K] :
    IsProbabilityMeasure (m.bind K) := by
  constructor
  rw [Measure.bind_apply MeasurableSet.univ (Kernel.measurable K)]
  simp only [measure_univ, lintegral_one]

private theorem bind_kernel_eval_eq_integral
    {α β : Type*} [MeasurableSpace α] [MeasurableSpace β]
    (m : Measure α) [IsFiniteMeasure m]
    (K : Kernel α β) [IsMarkovKernel K]
    {B : Set β} (hB : MeasurableSet B) :
    ((m.bind K) B).toReal = ∫ a : α, ((K a B).toReal) ∂m := by
  rw [Measure.bind_apply hB (Kernel.measurable K)]
  have hmeas : Measurable fun a : α => K a B := Kernel.measurable_coe K hB
  have hlt : ∀ᵐ a ∂m, K a B < ⊤ := ae_of_all m fun a => measure_lt_top (K a) B
  exact (integral_toReal hmeas.aemeasurable hlt).symm

private theorem integrable_kernel_eval
    {α β : Type*} [MeasurableSpace α] [MeasurableSpace β]
    (m : Measure α) [IsFiniteMeasure m]
    (K : Kernel α β) [IsMarkovKernel K]
    {B : Set β} (hB : MeasurableSet B) :
    Integrable (fun a : α => (K a B).toReal) m := by
  have hmeas : Measurable fun a : α => (K a B).toReal :=
    (Kernel.measurable_coe K hB).ennreal_toReal
  refine MeasureTheory.Integrable.mono' (integrable_const (1 : ℝ)) hmeas.aestronglyMeasurable
    (ae_of_all m fun a => ?_)
  rw [Real.norm_eq_abs, abs_of_nonneg ENNReal.toReal_nonneg]
  simpa [measure_univ] using ENNReal.toReal_mono (measure_ne_top (K a) Set.univ)
    (measure_mono (Set.subset_univ B))

/-- **Measurable Dobrushin Total-Variation Contraction:**
    For any measurable spaces `α`, `β`, probability measures `μ, ν : Measure α`,
    and Markov kernel `K : Kernel α β` with uniform Dobrushin bound `c`,
    `measureTV (μ.bind K) (ν.bind K) ≤ c * measureTV μ ν`. -/
theorem measurable_dobrushin_tv_contraction
    {α β : Type*} [MeasurableSpace α] [MeasurableSpace β]
    (μ ν : Measure α) [IsProbabilityMeasure μ] [IsProbabilityMeasure ν]
    (K : Kernel α β) [IsMarkovKernel K]
    {c : ℝ} (hK : kernelDobrushinBound K c) :
    measureTV (μ.bind K) (ν.bind K) ≤ c * measureTV μ ν := by
  let j := jordanDiff μ ν
  let p := j.posPart
  let q := j.negPart
  let M : ℝ := (p Set.univ).toReal
  have hp_univ_real : (p Set.univ).toReal = M := rfl
  have hM_tv : M = measureTV μ ν := (measureTV_eq_jordan_univ μ ν).symm
  have hM_q : (q Set.univ).toReal = M := (jordan_pos_eq_neg_univ μ ν).symm
  have hM_nonneg : 0 ≤ M := ENNReal.toReal_nonneg
  have hadd : μ + q = ν + p := jordan_add_eq μ ν
  haveI : IsFiniteMeasure (μ.bind K) := isFiniteMeasure_bind_kernel μ K
  haveI : IsFiniteMeasure (ν.bind K) := isFiniteMeasure_bind_kernel ν K
  haveI : IsFiniteMeasure (p.bind K) := isFiniteMeasure_bind_kernel p K
  haveI : IsFiniteMeasure (q.bind K) := isFiniteMeasure_bind_kernel q K
  by_cases hM0 : M = 0
  · have hp_univ : p Set.univ = 0 :=
      ((ENNReal.toReal_eq_zero_iff (p Set.univ)).mp hM0).resolve_right (measure_ne_top p Set.univ)
    have hq_univ : q Set.univ = 0 :=
      ((ENNReal.toReal_eq_zero_iff (q Set.univ)).mp (hM_q ▸ hM0)).resolve_right (measure_ne_top q Set.univ)
    have hp0 : p = 0 := Measure.measure_univ_eq_zero.mp hp_univ
    have hq0 : q = 0 := Measure.measure_univ_eq_zero.mp hq_univ
    have hμν : μ = ν := by simpa [hp0, hq0] using hadd
    rw [← hM_tv, hM0, mul_zero, hμν, measureTV_self]
  · have hM_pos : 0 < M := lt_of_le_of_ne hM_nonneg (Ne.symm hM0)
    refine measureTV_le_of_finite (mul_nonneg hK.1 (measureTV_nonneg μ ν)) ?_
    intro B hB
    have hbind_add : ((μ.bind K) B) + ((q.bind K) B) = ((ν.bind K) B) + ((p.bind K) B) := by
      rw [Measure.bind_apply hB (Kernel.measurable K), Measure.bind_apply hB (Kernel.measurable K),
        Measure.bind_apply hB (Kernel.measurable K), Measure.bind_apply hB (Kernel.measurable K),
        ← lintegral_add_measure, ← lintegral_add_measure, hadd]
    have hbind_real :
        ((μ.bind K) B).toReal + ((q.bind K) B).toReal =
          ((ν.bind K) B).toReal + ((p.bind K) B).toReal := by
      have hL := ENNReal.toReal_add (measure_ne_top (μ.bind K) B) (measure_ne_top (q.bind K) B)
      have hR := ENNReal.toReal_add (measure_ne_top (ν.bind K) B) (measure_ne_top (p.bind K) B)
      rw [← hL, ← hR, hbind_add]
    let f : α → ℝ := fun a => (K a B).toReal
    have hfp : Integrable f p := integrable_kernel_eval p K hB
    have hfq : Integrable f q := integrable_kernel_eval q K hB
    have hdiff_eval :
        ((μ.bind K) B).toReal - ((ν.bind K) B).toReal =
          (∫ a, f a ∂p) - (∫ b, f b ∂q) := by
      rw [← bind_kernel_eval_eq_integral p K hB, ← bind_kernel_eval_eq_integral q K hB]
      linarith
    have hinner : ∀ a : α, M * f a - ∫ b, f b ∂q = ∫ b, (f a - f b) ∂q := by
      intro a
      rw [integral_sub (integrable_const (f a)) hfq, integral_const, smul_eq_mul, hM_q]
    have houter :
        M * ((∫ a, f a ∂p) - (∫ b, f b ∂q)) =
          ∫ a, (∫ b, (f a - f b) ∂q) ∂p := by
      simp_rw [← hinner]
      rw [integral_sub (hfp.const_mul M) (integrable_const (∫ b, f b ∂q)),
        integral_mul_left, integral_const, smul_eq_mul, hp_univ_real]
      ring
    have hinner_abs : ∀ a : α, |∫ b, (f a - f b) ∂q| ≤ M * c := by
      intro a
      have hsub_int : Integrable (fun b => f a - f b) q := (integrable_const (f a)).sub hfq
      calc
        |∫ b, (f a - f b) ∂q|
            = ‖∫ b, (f a - f b) ∂q‖ := (Real.norm_eq_abs _).symm
        _ ≤ ∫ b, ‖f a - f b‖ ∂q := norm_integral_le_integral_norm _
        _ = ∫ b, |f a - f b| ∂q := by simp_rw [Real.norm_eq_abs]
        _ ≤ ∫ _b, c ∂q := by
            refine integral_mono hsub_int.abs (integrable_const c) fun b => ?_
            exact le_trans (abs_sub_le_measureTV (K a) (K b) hB) (hK.2 a b)
        _ = M * c := by rw [integral_const, smul_eq_mul, hM_q]
    have houter_int : Integrable (fun a => ∫ b, (f a - f b) ∂q) p := by
      simp_rw [← hinner]
      exact (hfp.const_mul M).sub (integrable_const _)
    have hbound_prod : M * |((μ.bind K) B).toReal - ((ν.bind K) B).toReal| ≤ M * (c * M) := by
      have h1 : M * |((μ.bind K) B).toReal - ((ν.bind K) B).toReal| =
          |M * ((∫ a, f a ∂p) - (∫ b, f b ∂q))| := by
        rw [hdiff_eval, abs_mul, abs_of_nonneg hM_nonneg]
      rw [h1, houter]
      calc
        |∫ a, (∫ b, (f a - f b) ∂q) ∂p|
            = ‖∫ a, (∫ b, (f a - f b) ∂q) ∂p‖ := (Real.norm_eq_abs _).symm
        _ ≤ ∫ a, ‖∫ b, (f a - f b) ∂q‖ ∂p := norm_integral_le_integral_norm _
        _ = ∫ a, |∫ b, (f a - f b) ∂q| ∂p := by simp_rw [Real.norm_eq_abs]
        _ ≤ ∫ _a, M * c ∂p := by
            refine integral_mono houter_int.abs (integrable_const (M * c)) hinner_abs
        _ = M * (c * M) := by
            rw [integral_const, smul_eq_mul, hp_univ_real]
            ring
    rw [← hM_tv]
    exact le_of_mul_le_mul_left hbound_prod hM_pos

/-- **Kernel Composition Dobrushin Submultiplicativity:**
    If `K₁ : Kernel α β` has Dobrushin bound `c₁` and `K₂ : Kernel β γ` has Dobrushin bound `c₂`,
    their Markov kernel composition `K₂ ∘ₖ K₁` has Dobrushin bound `c₁ * c₂`. -/
theorem measurable_dobrushin_comp
    {α β γ : Type*} [MeasurableSpace α] [MeasurableSpace β] [MeasurableSpace γ]
    (K₁ : Kernel α β) [IsMarkovKernel K₁]
    (K₂ : Kernel β γ) [IsMarkovKernel K₂]
    {c₁ c₂ : ℝ}
    (hK₁ : kernelDobrushinBound K₁ c₁) (hK₂ : kernelDobrushinBound K₂ c₂) :
    kernelDobrushinBound (K₂ ∘ₖ K₁) (c₁ * c₂) := by
  refine ⟨mul_nonneg hK₁.1 hK₂.1, fun a b => ?_⟩
  rw [Kernel.comp_apply K₂ K₁ a, Kernel.comp_apply K₂ K₁ b]
  have hcontr := measurable_dobrushin_tv_contraction (K₁ a) (K₁ b) K₂ hK₂
  calc
    measureTV ((K₁ a).bind K₂) ((K₁ b).bind K₂)
        ≤ c₂ * measureTV (K₁ a) (K₁ b) := hcontr
    _ ≤ c₂ * c₁ := mul_le_mul_of_nonneg_left (hK₁.2 a b) hK₂.1
    _ = c₁ * c₂ := mul_comm _ _

end DobrushinContraction

section HorizonStabilityAndCapstone

/-- **Measurable Kernel Step Perturbation Bound:**
    If two Markov kernels `K, K' : Kernel α β` satisfy `∀ a, measureTV (K a) (K' a) ≤ ε`,
    then `measureTV (μ.bind K) (μ.bind K') ≤ ε`. -/
theorem measurable_kernel_step_perturb
    {α β : Type*} [MeasurableSpace α] [MeasurableSpace β]
    (μ : Measure α) [IsProbabilityMeasure μ]
    (K K' : Kernel α β) [IsMarkovKernel K] [IsMarkovKernel K']
    {ε : ℝ} (hε : 0 ≤ ε)
    (hpert : ∀ a, measureTV (K a) (K' a) ≤ ε) :
    measureTV (μ.bind K) (μ.bind K') ≤ ε := by
  haveI : IsFiniteMeasure (μ.bind K) := isFiniteMeasure_bind_kernel μ K
  haveI : IsFiniteMeasure (μ.bind K') := isFiniteMeasure_bind_kernel μ K'
  refine measureTV_le_of_finite hε ?_
  intro B hB
  rw [bind_kernel_eval_eq_integral μ K hB, bind_kernel_eval_eq_integral μ K' hB]
  have hf : Integrable (fun a => (K a B).toReal) μ := integrable_kernel_eval μ K hB
  have hg : Integrable (fun a => (K' a B).toReal) μ := integrable_kernel_eval μ K' hB
  rw [← integral_sub hf hg]
  calc
    |∫ a, ((K a B).toReal - (K' a B).toReal) ∂μ|
        = ‖∫ a, ((K a B).toReal - (K' a B).toReal) ∂μ‖ := (Real.norm_eq_abs _).symm
    _ ≤ ∫ a, ‖(K a B).toReal - (K' a B).toReal‖ ∂μ := norm_integral_le_integral_norm _
    _ = ∫ a, |(K a B).toReal - (K' a B).toReal| ∂μ := by simp_rw [Real.norm_eq_abs]
    _ ≤ ∫ _a, ε ∂μ := by
        refine integral_mono (hf.sub hg).abs (integrable_const ε) fun a => ?_
        exact le_trans (abs_sub_le_measureTV (K a) (K' a) hB) (hpert a)
    _ = ε := by simp [integral_const, measure_univ]

/-- **One-Step Contraction + Perturbation Stability:**
    Combines `measurable_dobrushin_tv_contraction` and `measurable_kernel_step_perturb`
    via the triangle inequality for `measureTV`. -/
theorem measurable_dobrushin_one_step_stability
    {α β : Type*} [MeasurableSpace α] [MeasurableSpace β]
    (μ ν : Measure α) [IsProbabilityMeasure μ] [IsProbabilityMeasure ν]
    (K K' : Kernel α β) [IsMarkovKernel K] [IsMarkovKernel K']
    {c ε : ℝ} (hK : kernelDobrushinBound K c) (hε : 0 ≤ ε)
    (hpert : ∀ a, measureTV (K a) (K' a) ≤ ε) :
    measureTV (μ.bind K) (ν.bind K') ≤ c * measureTV μ ν + ε := by
  haveI : IsProbabilityMeasure (μ.bind K) := isProbabilityMeasure_bind_kernel μ K
  haveI : IsProbabilityMeasure (ν.bind K) := isProbabilityMeasure_bind_kernel ν K
  haveI : IsProbabilityMeasure (ν.bind K') := isProbabilityMeasure_bind_kernel ν K'
  calc
    measureTV (μ.bind K) (ν.bind K')
        ≤ measureTV (μ.bind K) (ν.bind K) + measureTV (ν.bind K) (ν.bind K') :=
      measureTV_triangle (μ.bind K) (ν.bind K) (ν.bind K')
    _ ≤ c * measureTV μ ν + ε :=
      add_le_add (measurable_dobrushin_tv_contraction μ ν K hK)
        (measurable_kernel_step_perturb ν K K' hε hpert)

/-- **Measurable Dobrushin Horizon Stability:**
    For inhomogeneous Markov-kernel trajectories on any `[MeasurableSpace α]`, total-variation
    drift satisfies the geometric horizon bound `c^T d₀ + ε (1 - c^T)/(1 - c)`. -/
theorem measurable_dobrushin_horizon_stability
    {α : Type*} [MeasurableSpace α]
    (μseq νseq : ℕ → Measure α)
    (K K' : ℕ → Kernel α α)
    (c ε : ℝ) (hc1 : c < 1) (hε : 0 ≤ ε)
    [∀ t, IsProbabilityMeasure (μseq t)]
    [∀ t, IsProbabilityMeasure (νseq t)]
    [∀ t, IsMarkovKernel (K t)]
    [∀ t, IsMarkovKernel (K' t)]
    (hD : ∀ t, kernelDobrushinBound (K t) c)
    (hstepμ : ∀ t, μseq (t + 1) = (μseq t).bind (K t))
    (hstepν : ∀ t, νseq (t + 1) = (νseq t).bind (K' t))
    (hpert : ∀ t a, measureTV (K t a) (K' t a) ≤ ε) :
    ∀ T : ℕ, measureTV (μseq T) (νseq T) ≤
      c ^ T * measureTV (μseq 0) (νseq 0) + ε * (1 - c ^ T) / (1 - c) := by
  refine contraction_horizon_bound (fun t => measureTV (μseq t) (νseq t)) c ε (hD 0).1 hc1 ?_
  intro t
  dsimp only
  rw [hstepμ t, hstepν t]
  exact measurable_dobrushin_one_step_stability (μseq t) (νseq t) (K t) (K' t)
    (hD t) hε (hpert t)

/-- **Uniform Measurable Contraction Ceiling:**
    If initial divergence satisfies `measureTV (μseq 0) (νseq 0) ≤ ε / (1 - c)`,
    it stays uniformly bounded by `ε / (1 - c)` for all `T : ℕ`. -/
theorem measurable_dobrushin_uniform_ceiling
    {α : Type*} [MeasurableSpace α]
    (μseq νseq : ℕ → Measure α)
    (K K' : ℕ → Kernel α α)
    (c ε : ℝ) (hc1 : c < 1) (hε : 0 ≤ ε)
    [∀ t, IsProbabilityMeasure (μseq t)]
    [∀ t, IsProbabilityMeasure (νseq t)]
    [∀ t, IsMarkovKernel (K t)]
    [∀ t, IsMarkovKernel (K' t)]
    (hD : ∀ t, kernelDobrushinBound (K t) c)
    (hstepμ : ∀ t, μseq (t + 1) = (μseq t).bind (K t))
    (hstepν : ∀ t, νseq (t + 1) = (νseq t).bind (K' t))
    (hpert : ∀ t a, measureTV (K t a) (K' t a) ≤ ε)
    (hinit : measureTV (μseq 0) (νseq 0) ≤ ε / (1 - c)) :
    ∀ T : ℕ, measureTV (μseq T) (νseq T) ≤ ε / (1 - c) := by
  intro T
  have hbound := measurable_dobrushin_horizon_stability μseq νseq K K' c ε hc1 hε
    hD hstepμ hstepν hpert T
  have hc0 : 0 ≤ c := (hD 0).1
  have hcT : 0 ≤ c ^ T := pow_nonneg hc0 T
  have hden : 0 < 1 - c := sub_pos.mpr hc1
  have hmix :
      c ^ T * (ε / (1 - c)) + ε * (1 - c ^ T) / (1 - c) = ε / (1 - c) := by
    have hne : 1 - c ≠ 0 := ne_of_gt hden
    field_simp [hne]
    ring
  calc
    measureTV (μseq T) (νseq T)
        ≤ c ^ T * measureTV (μseq 0) (νseq 0) + ε * (1 - c ^ T) / (1 - c) := hbound
    _ ≤ c ^ T * (ε / (1 - c)) + ε * (1 - c ^ T) / (1 - c) := by
        refine add_le_add_right (mul_le_mul_of_nonneg_left hinit hcT) _
    _ = ε / (1 - c) := hmix

/-- **Universal Measurable Master Principle Capstone:**
    Unifies:
    1. Standard-Borel continuum response-profile covariance,
    2. `μ`-a.e. countable product-anchor gauge trivialization,
    3. Observable-subspace `ker W` gauge-tube escape lower bounds, and
    4. Arbitrary measurable-space Dobrushin contraction, kernel composition
       submultiplicativity, and perturbed finite-horizon stability. -/
theorem measurable_dobrushin_universal_capstone
    -- (1) Continuum response-profile covariance
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
    -- (2) Countable product-anchor μ-a.e. trivialization
    {Act ContState ContOutcome : Type*}
    [MeasurableSpace ContState] [MeasurableSpace ContOutcome]
    (μ : Measure ContState) (obs : Kernel ContState ContOutcome)
    (evolve : Act → Kernel ContState ContState)
    {ι : Type*} [Countable ι] {Anchor : ι → Type*}
    (κ : ∀ j : ι, ContState → Anchor j)
    -- (3) ker W observable-subspace escape lower bound
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (W : E →L[ℝ] ℝ) (x Δpar Δperp : E)
    (hker : W Δperp = 0)
    (hflip : W x * W (x + Δpar + Δperp) ≤ 0)
    -- (4) Arbitrary measurable-space Dobrushin contraction & composition
    {Stateβ : Type*} [MeasurableSpace Stateβ]
    (μseq νseq : ℕ → Measure ContState)
    (K K' : ℕ → Kernel ContState ContState)
    (Kstep : Kernel ContState Stateβ) [IsMarkovKernel Kstep]
    (c cstep ε : ℝ) (hc1 : c < 1) (hε : 0 ≤ ε)
    [∀ t, IsProbabilityMeasure (μseq t)]
    [∀ t, IsProbabilityMeasure (νseq t)]
    [∀ t, IsMarkovKernel (K t)]
    [∀ t, IsMarkovKernel (K' t)]
    (hD : ∀ t, kernelDobrushinBound (K t) c)
    (hDstep : kernelDobrushinBound Kstep cstep)
    (hstepμ : ∀ t, μseq (t + 1) = (μseq t).bind (K t))
    (hstepν : ∀ t, νseq (t + 1) = (νseq t).bind (K' t))
    (hpert : ∀ t a, measureTV (K t a) (K' t a) ≤ ε) :
    (∀ e e', ContinuumObsEqual E₁ budget e e' ↔ ContinuumObsEqual E₂ budget e e') ∧
    ((∀ g : AEGaugeIso μ obs evolve,
        (∀ j, AEAnchorFixes (κ j) g) → aeGaugeRel g (AEGaugeIso.refl μ obs evolve)) ↔
      (∀ g : AEGaugeIso μ obs evolve,
        ¬ aeGaugeRel g (AEGaugeIso.refl μ obs evolve) →
          0 < μ {s | (fun j => κ j (g.stateEquiv s)) ≠ (fun j => κ j s)})) ∧
    (|W x| ≤ ‖W‖ * ‖Δpar‖) ∧
    (∀ t, kernelDobrushinBound (Kstep ∘ₖ K t) (c * cstep)) ∧
    (∀ T : ℕ, measureTV (μseq T) (νseq T) ≤
      c ^ T * measureTV (μseq 0) (νseq 0) + ε * (1 - c ^ T) / (1 - c)) := by
  refine ⟨?_, ?_, ?_, ?_, ?_⟩
  · intro e e'
    exact continuum_profile_iff_standardBorel R budget haffSurj hinj e e'
  · have hiff := ae_anchor_kills_isotropy_iff μ obs evolve (fun s j => κ j s)
    constructor
    · intro hcoord
      refine hiff.mp (fun g hprod => hcoord g ((ae_product_anchor_kernel_inter μ obs evolve κ g).mp hprod))
    · intro hsep g hj
      exact hiff.mpr hsep g ((ae_product_anchor_kernel_inter μ obs evolve κ g).mpr hj)
  · exact gauge_escape_lower_bound W x Δpar Δperp hker hflip
  · intro t
    exact measurable_dobrushin_comp (K t) Kstep (hD t) hDstep
  · exact measurable_dobrushin_horizon_stability μseq νseq K K' c ε hc1 hε
      hD hstepμ hstepν hpert

end HorizonStabilityAndCapstone

end Semplex.MeasurableDobrushinContraction
