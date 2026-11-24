import ContinuumKernelCovariance
import Mathlib.MeasureTheory.Function.Jacobian
import Mathlib.Analysis.SpecialFunctions.ExpDeriv

/-!
# Continuum mu-a.e. Gauge Groupoid, Quantitative Eps-Stability & Variable-Jacobian Covariance

Extends `Semplex.ContinuumKernelCovariance` past exact profile-quotient equalities
(and past exact acyclic Markov-category natural transformations in Lorenz-Tull 2026)
in four directions:

1. **Continuum `mu`-a.e. Gauge Groupoid (`AEGaugeIso`, `aeGaugeRel`):**
   Quotients kernel-preserving measurable equivalences by `=ᵐ[μ]` rather than
   pointwise equality, proving null-set perturbations trivialize and measurable
   anchors trivialize `Aut_ae` iff every non-a.e.-identity symmetry separates the
   anchor on a set of positive `μ`-measure.
2. **Quantitative `ε`-Gauge Algebra & Multi-Step Contraction Horizon Bounds:**
   Formalizes `IsEpsGauge` (`refl`, `symm`, additive `comp`, `k * ε` `pow`) and
   proves the geometric finite-horizon error accumulation bound `contraction_horizon_bound`
   (`0 ≤ ρ < 1`) and non-expansive linear bound `nonexpansive_horizon_bound`.
3. **Observable-Subspace Gauge-Tube & Margin Stability (`ker W`):**
   Proves arbitrary perturbations inside `ker W` leave observable margins exact,
   preserves decision signs within `|W Δpar| < |W x|`, and proves the
   gauge-escape lower bound `|W x| ≤ ‖W‖ * ‖Δpar‖`.
4. **Variable-Jacobian (`|det Dφ(x)| ≠ 1`) Density Pushforward:**
   Lifts arbitrary non-volume-preserving `C^1` coordinate transformations via
   `MeasureTheory.lintegral_image_eq_lintegral_abs_det_fderiv_mul` and instantiates
   on `Real.exp : ℝ → ℝ` where `det = exp x` (`exp 1 ≠ 1`).
-/

open MeasureTheory ProbabilityTheory Function Set Filter
open scoped ENNReal Topology

namespace Semplex.QuantitativeGaugeStability

section AEGaugeGroupoid

variable {State α Outcome Anchor : Type*}
variable [MeasurableSpace State] [MeasurableSpace Outcome]

/-- Measurable gauge automorphism of a continuum system preserving `obs` and `evolve`
    almost everywhere with respect to reachable reference measure `μ`. -/
structure AEGaugeIso
    (μ : Measure State) (obs : Kernel State Outcome) (evolve : α → Kernel State State) where
  stateEquiv : State ≃ᵐ State
  obs_ae : ∀ᵐ s ∂μ, obs (stateEquiv s) = obs s
  evolve_ae : ∀ a, ∀ᵐ s ∂μ, (evolve a (stateEquiv s)) = (evolve a s).map stateEquiv

def AEGaugeIso.refl (μ : Measure State) (obs : Kernel State Outcome)
    (evolve : α → Kernel State State) : AEGaugeIso μ obs evolve where
  stateEquiv := MeasurableEquiv.refl State
  obs_ae := Eventually.of_forall fun _ => rfl
  evolve_ae := fun a => Eventually.of_forall fun s => by
    change (evolve a) s = ((evolve a) s).map id
    rw [Measure.map_id]

def aeGaugeRel
    {μ : Measure State} {obs : Kernel State Outcome} {evolve : α → Kernel State State}
    (g₁ g₂ : AEGaugeIso μ obs evolve) : Prop :=
  (g₁.stateEquiv : State → State) =ᵐ[μ] g₂.stateEquiv

theorem aeGaugeRel_equivalence
    (μ : Measure State) (obs : Kernel State Outcome) (evolve : α → Kernel State State) :
    Equivalence (aeGaugeRel (μ := μ) (obs := obs) (evolve := evolve)) where
  refl := fun _ => EventuallyEq.rfl
  symm := fun h => h.symm
  trans := fun h₁₂ h₂₃ => h₁₂.trans h₂₃

theorem ae_null_perturbation_trivial
    {μ : Measure State} {obs : Kernel State Outcome} {evolve : α → Kernel State State}
    (g : AEGaugeIso μ obs evolve)
    (N : Set State) (hN : μ N = 0)
    (hid : ∀ s, s ∉ N → g.stateEquiv s = s) :
    aeGaugeRel g (AEGaugeIso.refl μ obs evolve) := by
  rw [aeGaugeRel, EventuallyEq, ae_iff]
  refine measure_mono_null (fun s hs => ?_) hN
  by_contra hsN
  exact hs (hid s hsN)

def AEAnchorFixes
    {μ : Measure State} {obs : Kernel State Outcome} {evolve : α → Kernel State State}
    (κA : State → Anchor) (g : AEGaugeIso μ obs evolve) : Prop :=
  (fun s => κA (g.stateEquiv s)) =ᵐ[μ] κA

/-- An independent measurable anchor kills all `μ`-a.e. gauge isotropy if and
    only if every non-`μ`-a.e.-identity gauge separates `κA` on a set of
    strictly positive `μ`-measure. -/
theorem ae_anchor_kills_isotropy_iff
    (μ : Measure State) (obs : Kernel State Outcome) (evolve : α → Kernel State State)
    (κA : State → Anchor) :
    (∀ g : AEGaugeIso μ obs evolve,
        AEAnchorFixes κA g → aeGaugeRel g (AEGaugeIso.refl μ obs evolve)) ↔
      (∀ g : AEGaugeIso μ obs evolve,
        ¬ aeGaugeRel g (AEGaugeIso.refl μ obs evolve) →
          0 < μ {s | κA (g.stateEquiv s) ≠ κA s}) := by
  constructor
  · intro h g hg
    by_contra hzero
    have hmu0 : μ {s | κA (g.stateEquiv s) ≠ κA s} = 0 :=
      le_antisymm (not_lt.mp hzero) (zero_le _)
    have hfix : AEAnchorFixes κA g := by
      rw [AEAnchorFixes, EventuallyEq, ae_iff]
      exact hmu0
    exact hg (h g hfix)
  · intro h g hfix
    by_contra hg
    have hpos := h g hg
    have hmu0 : μ {s | κA (g.stateEquiv s) ≠ κA s} = 0 := by
      rwa [AEAnchorFixes, EventuallyEq, ae_iff] at hfix
    exact (ne_of_gt hpos) hmu0

end AEGaugeGroupoid

section QuantitativeStability

def IsEpsGauge {X Y : Type*} [PseudoMetricSpace Y]
    (f : X → X) (obs : X → Y) (ε : ℝ) : Prop :=
  ∀ x, dist (obs (f x)) (obs x) ≤ ε

theorem epsGauge_refl {X Y : Type*} [PseudoMetricSpace Y] (obs : X → Y) :
    IsEpsGauge id obs 0 := by
  intro x
  simp

theorem epsGauge_symm {X Y : Type*} [PseudoMetricSpace Y]
    (e : X ≃ X) (obs : X → Y) {ε : ℝ}
    (h : IsEpsGauge e obs ε) : IsEpsGauge e.symm obs ε := by
  intro y
  have hx := h (e.symm y)
  simpa [e.apply_symm_apply, dist_comm] using hx

theorem epsGauge_comp {X Y : Type*} [PseudoMetricSpace Y]
    {f g : X → X} (obs : X → Y) {ε₁ ε₂ : ℝ}
    (hf : IsEpsGauge f obs ε₁) (hg : IsEpsGauge g obs ε₂) :
    IsEpsGauge (f ∘ g) obs (ε₁ + ε₂) := by
  intro x
  calc
    dist (obs (f (g x))) (obs x)
        ≤ dist (obs (f (g x))) (obs (g x)) + dist (obs (g x)) (obs x) := dist_triangle _ _ _
    _ ≤ ε₁ + ε₂ := add_le_add (hf (g x)) (hg x)

theorem epsGauge_pow {X Y : Type*} [PseudoMetricSpace Y]
    {f : X → X} (obs : X → Y) {ε : ℝ} (hε : 0 ≤ ε)
    (hf : IsEpsGauge f obs ε) :
    ∀ k : ℕ, IsEpsGauge (f^[k]) obs ((k : ℝ) * ε)
  | 0 => by
      intro x
      simp
  | k + 1 => by
      intro x
      rw [Function.iterate_succ_apply']
      have ih := epsGauge_pow obs hε hf k x
      calc
        dist (obs (f (f^[k] x))) (obs x)
            ≤ dist (obs (f (f^[k] x))) (obs (f^[k] x)) + dist (obs (f^[k] x)) (obs x) :=
          dist_triangle _ _ _
        _ ≤ ε + (k : ℝ) * ε := add_le_add (hf (f^[k] x)) ih
        _ = ((k + 1 : ℕ) : ℝ) * ε := by push_cast; ring

/-- Geometric horizon error accumulation for `ρ`-contractive Markov/dynamical steps. -/
theorem contraction_horizon_bound
    (d : ℕ → ℝ) (ρ δ : ℝ) (hρ0 : 0 ≤ ρ) (hρ1 : ρ < 1)
    (hstep : ∀ t, d (t + 1) ≤ ρ * d t + δ) :
    ∀ T : ℕ, d T ≤ ρ ^ T * d 0 + δ * (1 - ρ ^ T) / (1 - ρ)
  | 0 => by
      simp
  | T + 1 => by
      have ih := contraction_horizon_bound d ρ δ hρ0 hρ1 hstep T
      have hden : 0 < 1 - ρ := sub_pos.mpr hρ1
      calc
        d (T + 1) ≤ ρ * d T + δ := hstep T
        _ ≤ ρ * (ρ ^ T * d 0 + δ * (1 - ρ ^ T) / (1 - ρ)) + δ := by
          gcongr
        _ = ρ ^ (T + 1) * d 0 + δ * (1 - ρ ^ (T + 1)) / (1 - ρ) := by
          have hne : 1 - ρ ≠ 0 := ne_of_gt hden
          field_simp [hne]
          ring

/-- Non-expansive (`ρ = 1`) linear horizon growth bound. -/
theorem nonexpansive_horizon_bound
    (d : ℕ → ℝ) (δ : ℝ) (hstep : ∀ t, d (t + 1) ≤ d t + δ) :
    ∀ T : ℕ, d T ≤ d 0 + (T : ℝ) * δ
  | 0 => by
      simp
  | T + 1 => by
      have ih := nonexpansive_horizon_bound d δ hstep T
      calc
        d (T + 1) ≤ d T + δ := hstep T
        _ ≤ (d 0 + (T : ℝ) * δ) + δ := add_le_add_right ih δ
        _ = d 0 + ((T + 1 : ℕ) : ℝ) * δ := by push_cast; ring

end QuantitativeStability

section GaugeTubeMargins

variable {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]

theorem gauge_perturbation_invisible
    (W : E →L[ℝ] ℝ) (x Δpar Δperp : E) (hker : W Δperp = 0) :
    W (x + Δpar + Δperp) - W x = W Δpar := by
  simp only [map_add, hker]
  ring

theorem no_flip_within_gauge_tube_pos
    (W : E →L[ℝ] ℝ) (x Δpar Δperp : E)
    (hker : W Δperp = 0) (hpos : 0 < W x) (htub : |W Δpar| < |W x|) :
    0 < W (x + Δpar + Δperp) := by
  rw [abs_of_pos hpos] at htub
  have h1 := (abs_lt.mp htub).1
  simp only [map_add, hker]
  linarith

theorem no_flip_within_gauge_tube_neg
    (W : E →L[ℝ] ℝ) (x Δpar Δperp : E)
    (hker : W Δperp = 0) (hneg : W x < 0) (htub : |W Δpar| < |W x|) :
    W (x + Δpar + Δperp) < 0 := by
  rw [abs_of_neg hneg] at htub
  have h2 := (abs_lt.mp htub).2
  simp only [map_add, hker]
  linarith

/-- Any sign flip across a gauge-decomposed perturbation requires the observable
    projection component `‖Δpar‖` to meet the margin-over-opNorm threshold. -/
theorem gauge_escape_lower_bound
    (W : E →L[ℝ] ℝ) (x Δpar Δperp : E)
    (hker : W Δperp = 0)
    (hflip : W x * W (x + Δpar + Δperp) ≤ 0) :
    |W x| ≤ ‖W‖ * ‖Δpar‖ := by
  have hmargin : |W x| ≤ |W Δpar| := by
    have hsq : W x * (W x + W Δpar) ≤ 0 := by
      simpa [map_add, hker, add_assoc] using hflip
    rcases le_total 0 (W x) with hx0 | hx0
    · rw [abs_of_nonneg hx0]
      rcases eq_or_lt_of_le hx0 with hxzero | hxpos
      · simp [← hxzero]
      · have hle : W x + W Δpar ≤ 0 := nonpos_of_mul_nonpos_right hsq hxpos
        calc
          W x ≤ -W Δpar := by linarith
          _ ≤ |W Δpar| := neg_le_abs _
    · rw [abs_of_nonpos hx0]
      rcases lt_or_eq_of_le hx0 with hxneg | hxzero
      · have hge : 0 ≤ W x + W Δpar := nonneg_of_mul_nonpos_right hsq hxneg
        have hpos : -W x ≤ W Δpar := by linarith
        exact le_trans hpos (le_abs_self _)
      · simp [hxzero]
  calc
    |W x| ≤ |W Δpar| := hmargin
    _ = ‖W Δpar‖ := (Real.norm_eq_abs _).symm
    _ ≤ ‖W‖ * ‖Δpar‖ := W.le_opNorm Δpar

/-- Quantitative `ε`-ball separation: two orbits `2ε` apart cannot share an `ε`-neighbor. -/
theorem eps_orbit_rigidity {Z : Type*} [PseudoMetricSpace Z]
    {z z₁ z₂ : Z} {ε : ℝ}
    (hsep : 2 * ε < dist z₁ z₂) (hz₁ : dist z z₁ ≤ ε) :
    ε < dist z z₂ := by
  have htri : dist z₁ z₂ ≤ dist z z₁ + dist z z₂ := by
    simpa [dist_comm] using dist_triangle z₁ z z₂
  linarith

end GaugeTubeMargins

section VariableJacobianPushforward

/-- Arbitrary `C^1` variable-Jacobian pushforward density law over a Haar measure. -/
theorem variable_jacobian_density_pushforward
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    [FiniteDimensional ℝ E] [MeasurableSpace E] [BorelSpace E]
    (μ : Measure E) [μ.IsAddHaarMeasure]
    {s : Set E} (hs : MeasurableSet s)
    {f : E → E} {f' : E → E →L[ℝ] E}
    (hf' : ∀ x ∈ s, HasFDerivWithinAt f (f' x) s x)
    (hf : InjOn f s) (g : E → ℝ≥0∞) :
    ∫⁻ y in f '' s, g y ∂μ = ∫⁻ x in s, ENNReal.ofReal |(f' x).det| * g (f x) ∂μ :=
  MeasureTheory.lintegral_image_eq_lintegral_abs_det_fderiv_mul μ hs hf' hf g

/-- Non-unit Jacobian witness: for `Real.exp`, the derivative operator at `1` has determinant `e ≠ 1`. -/
theorem exp_jacobian_nonunit :
    ((1 : ℝ →L[ℝ] ℝ).smulRight (Real.exp 1)).det ≠ 1 := by
  rw [MeasureTheory.det_one_smulRight]
  have hgt : (1 : ℝ) < Real.exp 1 := Real.one_lt_exp_iff.mpr one_pos
  exact ne_of_gt hgt

/-- Exact Bochner change-of-variables with spatially varying Jacobian `Real.exp x`. -/
theorem exp_density_change_of_variables
    {s : Set ℝ} (hs : MeasurableSet s) (g : ℝ → ℝ) :
    ∫ y in Real.exp '' s, g y = ∫ x in s, Real.exp x • g (Real.exp x) := by
  have h := MeasureTheory.integral_image_eq_integral_abs_deriv_smul hs
    (fun x _ => (Real.hasDerivAt_exp x).hasDerivWithinAt) Real.exp_injective.injOn g
  refine h.trans ?_
  refine MeasureTheory.setIntegral_congr hs (fun x _ => ?_)
  rw [abs_of_pos (Real.exp_pos x)]

end VariableJacobianPushforward

end Semplex.QuantitativeGaugeStability
