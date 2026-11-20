/-
  Mathlib formalization for the Two-Sided Causal-Kinetic Master Operator:
    G(lam) = P_perp * exp(-lam/2 * L) * (W_c + W_o) * exp(-lam/2 * L) * P_perp
  in L^2(pi) on any finite deterministic automaton (Q, A, delta, pi).

  Proves:
  1. `pastStep_adjoint`: adjointness of the Perron-Frobenius pull-back `pastStep` and
     the Koopman transition operator `koopman` in L^2(pi).
  2. `pastStep_const_of_bijective`, `pastOp_of_bijective`, `wcOp_eq_zero_of_bijective`,
     and `pastForm_eq_zero_of_bijective`: the past-reachability chi^2 Gramian W_c
     vanishes identically on centered states for every bijective / group automaton.
  3. `kineticOp_inner_eq_dirichlet`, `kineticOp_selfAdjoint`, `kineticForm_nonneg`,
     `kineticForm_const`, `kineticOp_const`: self-adjointness, PSD Dirichlet energy
     identity, and constant-annihilation of the Dirichlet kinetic operator L.
  4. `heatApply_eigenmode`, `masterOperator_eigenvalue_on_commuting_mode`, and
     `group_master_reduces_to_gibbs`: exact reduction on commuting / group modes to the
     Gibbs selection spectrum e * exp(-lam * c) of Spikes 77-80 and 85.
  5. `hypercube_kineticForm_eq_totalInfluence`: on the Boolean n-cube with single-bit flips,
     the same Dirichlet kinetic energy equals (2 / n) times total Boolean influence.

  Isolated in `proofs/lean-mathlib/` so `proofs/lean/` remains core Lean 4.
-/
import Mathlib.Analysis.SpecialFunctions.Exponential
import Mathlib.Data.Fintype.BigOperators
import Mathlib.Data.Real.Basic
import Mathlib.Tactic.Ring
import Mathlib.Tactic.Positivity

open scoped BigOperators

namespace MasterPrinciple

noncomputable section
set_option linter.unusedSectionVars false

section AutomatonOperators

variable {Q A : Type*} [Fintype Q] [DecidableEq Q] [Fintype A] [DecidableEq A]

/-- Stationary-weighted inner product `⟨u, v⟩_π = ∑_q π(q) u(q) v(q)`. -/
def piInner (π : Q → ℝ) (u v : Q → ℝ) : ℝ :=
  ∑ q : Q, π q * u q * v q

theorem piInner_symm (π : Q → ℝ) (u v : Q → ℝ) :
    piInner π u v = piInner π v u := by
  unfold piInner
  refine Finset.sum_congr rfl fun q _ => ?_
  ring

/-- Constant-one state function `𝟙`. -/
def constOne : Q → ℝ := fun _ => 1

/-- Orthogonal projection `P_⊥ u = u - E_π[u] 𝟙` onto zero-mean observables in `L^2(π)`. -/
def center (π : Q → ℝ) (u : Q → ℝ) : Q → ℝ :=
  fun q => u q - ∑ r : Q, π r * u r

theorem piInner_constOne_left (π : Q → ℝ) (u : Q → ℝ) :
    piInner π constOne u = ∑ q : Q, π q * u q := by
  unfold piInner constOne
  refine Finset.sum_congr rfl fun q _ => by ring

theorem center_mean_zero (π : Q → ℝ) (hπ_sum : ∑ q : Q, π q = 1) (u : Q → ℝ) :
    ∑ q : Q, π q * center π u q = 0 := by
  unfold center
  simp_rw [mul_sub, Finset.sum_sub_distrib, ← Finset.sum_mul, hπ_sum, one_mul, sub_self]

theorem center_const (π : Q → ℝ) (hπ_sum : ∑ q : Q, π q = 1) (c : ℝ) :
    center π (fun _ => c) = fun _ => 0 := by
  funext _
  simp only [center, ← Finset.sum_mul, hπ_sum, one_mul, sub_self]

theorem center_smul (π : Q → ℝ) (α : ℝ) (u : Q → ℝ) :
    center π (fun q => α * u q) = fun q => α * center π u q := by
  funext q
  unfold center
  have hs : (∑ r : Q, π r * (α * u r)) = α * ∑ r : Q, π r * u r := by
    rw [Finset.mul_sum]
    refine Finset.sum_congr rfl fun r _ => by ring
  rw [hs]
  ring

theorem piInner_smul_right (π : Q → ℝ) (α : ℝ) (u v : Q → ℝ) :
    piInner π u (fun q => α * v q) = α * piInner π u v := by
  unfold piInner
  rw [Finset.mul_sum]
  refine Finset.sum_congr rfl fun q _ => by ring

/-- Koopman pull-back `(T_a f)(q) = f(δ_a q)` for input letter `a`. -/
def koopman (δ : A → Q → Q) (a : A) (f : Q → ℝ) : Q → ℝ :=
  fun q => f (δ a q)

/-- Perron-Frobenius `L^2(π)` adjoint step `(T_a^* f)(r) = π(r)⁻¹ ∑_{δ_a q = r} π(q) f(q)`. -/
def pastStep (δ : A → Q → Q) (π : Q → ℝ) (a : A) (f : Q → ℝ) : Q → ℝ :=
  fun r => (π r)⁻¹ * ∑ q : Q, if δ a q = r then π q * f q else 0

/-- Exact `L^2(π)` duality `⟨T_a^* f, g⟩_π = ⟨f, T_a g⟩_π`. -/
theorem pastStep_adjoint (δ : A → Q → Q) (π : Q → ℝ)
    (hπ_pos : ∀ q, 0 < π q) (a : A) (f g : Q → ℝ) :
    piInner π (pastStep δ π a f) g = piInner π f (koopman δ a g) := by
  unfold piInner pastStep koopman
  have hcanc : ∀ r : Q,
      π r * ((π r)⁻¹ * ∑ q : Q, if δ a q = r then π q * f q else 0) * g r =
        (∑ q : Q, if δ a q = r then π q * f q else 0) * g r := by
    intro r
    have hne : π r ≠ 0 := ne_of_gt (hπ_pos r)
    rw [← mul_assoc, mul_inv_cancel₀ hne, one_mul]
  simp_rw [hcanc, Finset.sum_mul]
  have hpush : ∀ r q : Q,
      (if δ a q = r then π q * f q else 0) * g r =
        if δ a q = r then π q * f q * g r else 0 := by
    intro r q
    split_ifs <;> simp
  simp_rw [hpush]
  rw [Finset.sum_comm]
  refine Finset.sum_congr rfl fun q _ => ?_
  simp

theorem pastStep_smul (δ : A → Q → Q) (π : Q → ℝ) (a : A) (α : ℝ) (f : Q → ℝ) :
    pastStep δ π a (fun q => α * f q) = fun r => α * pastStep δ π a f r := by
  funext r
  unfold pastStep
  have hite : (∑ q : Q, if δ a q = r then π q * (α * f q) else 0) =
      α * ∑ q : Q, if δ a q = r then π q * f q else 0 := by
    rw [Finset.mul_sum]
    refine Finset.sum_congr rfl fun q _ => ?_
    split_ifs <;> ring
  rw [hite]
  ring

theorem pastStep_add (δ : A → Q → Q) (π : Q → ℝ) (a : A) (f g : Q → ℝ) :
    pastStep δ π a (fun q => f q + g q) = fun r => pastStep δ π a f r + pastStep δ π a g r := by
  funext r
  unfold pastStep
  have hite : (∑ q : Q, if δ a q = r then π q * (f q + g q) else 0) =
      (∑ q : Q, if δ a q = r then π q * f q else 0) +
      (∑ q : Q, if δ a q = r then π q * g q else 0) := by
    rw [← Finset.sum_add_distrib]
    refine Finset.sum_congr rfl fun q _ => ?_
    split_ifs <;> ring
  rw [hite, mul_add]

/-- On any `π`-preserving bijective letter `δ_a` (every group generator under uniform `π`),
    `pastStep` maps constants to constants. -/
theorem pastStep_const_of_bijective (δ : A → Q → Q) (π : Q → ℝ)
    (hπ_pos : ∀ q, 0 < π q) (a : A)
    (hbij : Function.Bijective (δ a)) (hpres : ∀ q, π (δ a q) = π q) (c : ℝ) :
    pastStep δ π a (fun _ => c) = fun _ => c := by
  funext r
  unfold pastStep
  obtain ⟨q₀, hq₀⟩ := hbij.2 r
  have hsum : (∑ q : Q, if δ a q = r then π q * c else 0) = π q₀ * c := by
    rw [Finset.sum_eq_single q₀]
    · simp [hq₀]
    · intro q _ hne
      have hdiff : δ a q ≠ r := fun heq => hne (hbij.1 (heq.trans hq₀.symm))
      simp [hdiff]
    · intro hmem
      exact absurd (Finset.mem_univ q₀) hmem
  have hπq : π q₀ = π r := by simpa [hq₀] using (hpres q₀).symm
  rw [hsum, hπq]
  have hne : π r ≠ 0 := ne_of_gt (hπ_pos r)
  rw [← mul_assoc, inv_mul_cancel₀ hne, one_mul]

/-- Recursive `t`-step backward reachability operator `Op_t` corresponding to `B_t` in `L^2(π)`:
    `B_0 = 𝟙 ⊗ 𝟙`, and `B_{t+1} = (1 / |A|) ∑_a T_a^* B_t T_a`. -/
def pastOp (δ : A → Q → Q) (π : Q → ℝ) : Nat → (Q → ℝ) → (Q → ℝ)
  | 0, f => fun _ => ∑ q : Q, π q * f q
  | t + 1, f => fun q =>
      (Fintype.card A : ℝ)⁻¹ * ∑ a : A, pastStep δ π a (pastOp δ π t (koopman δ a f)) q

/-- Exact `t`-step past reachability kernel on `Q × Q`, such that `B_0(q, r) = 1` and
    `B_{t+1}` propagates backward along `pastStep`. -/
def pastKernel (δ : A → Q → Q) (π : Q → ℝ) : Nat → Q → Q → ℝ
  | 0, _, _ => 1
  | t + 1, q, r =>
      (Fintype.card A : ℝ)⁻¹ *
        ∑ a : A, pastStep δ π a (fun q' => pastStep δ π a (fun r' => pastKernel δ π t q' r') r) q

theorem pastOp_inner (δ : A → Q → Q) (π : Q → ℝ) (hπ_pos : ∀ q, 0 < π q) :
    ∀ (t : Nat) (u v : Q → ℝ),
      piInner π u (pastOp δ π (t + 1) v) =
        (Fintype.card A : ℝ)⁻¹ *
          ∑ a : A, piInner π (koopman δ a u) (pastOp δ π t (koopman δ a v))
  | t, u, v => by
      simp only [piInner, pastOp]
      have hterm : ∀ q : Q,
          π q * u q * ((Fintype.card A : ℝ)⁻¹ * ∑ a : A, pastStep δ π a (pastOp δ π t (koopman δ a v)) q) =
            (Fintype.card A : ℝ)⁻¹ *
              ∑ a : A, π q * u q * pastStep δ π a (pastOp δ π t (koopman δ a v)) q := by
        intro q
        have h1 : (Fintype.card A : ℝ)⁻¹ * ∑ a : A, pastStep δ π a (pastOp δ π t (koopman δ a v)) q =
            ∑ a : A, (Fintype.card A : ℝ)⁻¹ * pastStep δ π a (pastOp δ π t (koopman δ a v)) q :=
          Finset.mul_sum Finset.univ _ (Fintype.card A : ℝ)⁻¹
        have h2 : π q * u q * ∑ a : A, (Fintype.card A : ℝ)⁻¹ * pastStep δ π a (pastOp δ π t (koopman δ a v)) q =
            ∑ a : A, π q * u q * ((Fintype.card A : ℝ)⁻¹ * pastStep δ π a (pastOp δ π t (koopman δ a v)) q) :=
          Finset.mul_sum Finset.univ _ (π q * u q)
        have h3 : (Fintype.card A : ℝ)⁻¹ * ∑ a : A, π q * u q * pastStep δ π a (pastOp δ π t (koopman δ a v)) q =
            ∑ a : A, (Fintype.card A : ℝ)⁻¹ * (π q * u q * pastStep δ π a (pastOp δ π t (koopman δ a v)) q) :=
          Finset.mul_sum Finset.univ _ (Fintype.card A : ℝ)⁻¹
        rw [h1, h2, h3]
        refine Finset.sum_congr rfl fun a _ => ?_
        ring
      simp_rw [hterm]
      rw [← Finset.mul_sum Finset.univ _ (Fintype.card A : ℝ)⁻¹, Finset.sum_comm]
      congr 1
      refine Finset.sum_congr rfl fun a _ => ?_
      change piInner π u (pastStep δ π a (pastOp δ π t (koopman δ a v))) =
        piInner π (koopman δ a u) (pastOp δ π t (koopman δ a v))
      rw [piInner_symm, pastStep_adjoint δ π hπ_pos, piInner_symm]

/-- Discounted centered past-reachability operator `W_c(γ, T) = P_⊥ (∑_{t<T} γ^{t+1} Op_{t+1}) P_⊥`. -/
def wcOp (δ : A → Q → Q) (π : Q → ℝ) (γ : ℝ) (T : Nat) (v : Q → ℝ) : Q → ℝ :=
  center π (fun q => ∑ t ∈ Finset.range T, γ ^ (t + 1) * pastOp δ π (t + 1) (center π v) q)

theorem pastOp_smul (δ : A → Q → Q) (π : Q → ℝ) :
    ∀ (t : Nat) (α : ℝ) (f : Q → ℝ),
      pastOp δ π t (fun q => α * f q) = fun q => α * pastOp δ π t f q
  | 0, α, f => by
      funext _
      simp only [pastOp]
      rw [Finset.mul_sum]
      refine Finset.sum_congr rfl fun q _ => by ring
  | t + 1, α, f => by
      funext r
      simp only [pastOp]
      have hk : ∀ a : A, koopman δ a (fun q => α * f q) = fun q => α * koopman δ a f q := fun _ => rfl
      have hs : ∀ a : A,
          pastStep δ π a (pastOp δ π t (fun q => α * koopman δ a f q)) r =
            α * pastStep δ π a (pastOp δ π t (koopman δ a f)) r := fun a => by
        rw [pastOp_smul δ π t α (koopman δ a f), pastStep_smul]
      simp only [hk, hs]
      rw [← Finset.mul_sum Finset.univ _ α]
      ring

theorem wcOp_smul (δ : A → Q → Q) (π : Q → ℝ) (γ : ℝ) (T : Nat) (α : ℝ) (v : Q → ℝ) :
    wcOp δ π γ T (fun q => α * v q) = fun q => α * wcOp δ π γ T v q := by
  unfold wcOp
  have hinner : (fun q => ∑ t ∈ Finset.range T, γ ^ (t + 1) * pastOp δ π (t + 1) (center π (fun x => α * v x)) q) =
      fun q => α * ∑ t ∈ Finset.range T, γ ^ (t + 1) * pastOp δ π (t + 1) (center π v) q := by
    funext q
    rw [center_smul, Finset.mul_sum]
    refine Finset.sum_congr rfl fun t _ => ?_
    rw [pastOp_smul]
    dsimp only
    ring
  rw [hinner, center_smul]

/-- Discounted centered past-reachability bilinear form `⟨u, W_c(γ, T) v⟩_π`. -/
def pastForm (δ : A → Q → Q) (π : Q → ℝ) (γ : ℝ) (T : Nat) (u v : Q → ℝ) : ℝ :=
  ∑ t ∈ Finset.range T,
    γ ^ (t + 1) * ∑ q : Q, ∑ r : Q, π q * π r * center π u q * pastKernel δ π (t + 1) q r * center π v r

/-- Bijective `π`-preserving automaton transitions preserve `pastOp` identically at `pastOp 0` (rank 1 on constants). -/
theorem pastOp_of_bijective (δ : A → Q → Q) (π : Q → ℝ)
    (hπ_pos : ∀ q, 0 < π q) [Nonempty A]
    (hbij : ∀ a, Function.Bijective (δ a)) (hpres : ∀ a q, π (δ a q) = π q) :
    ∀ (t : Nat) (f : Q → ℝ), pastOp δ π t f = fun _ => ∑ q : Q, π q * f q
  | 0, _ => rfl
  | t + 1, f => by
      funext r
      simp only [pastOp]
      have hterm : ∀ a : A, pastStep δ π a (pastOp δ π t (koopman δ a f)) r = ∑ q : Q, π q * f q := by
        intro a
        rw [pastOp_of_bijective δ π hπ_pos hbij hpres t (koopman δ a f)]
        have hmean : (∑ q : Q, π q * koopman δ a f q) = ∑ q : Q, π q * f q := by
          have hrew : ∀ q : Q, π q * koopman δ a f q = π (δ a q) * f (δ a q) := by
            intro q
            rw [hpres a q]; rfl
          simp_rw [hrew]
          exact Fintype.sum_bijective (δ a) (hbij a) (fun q => π (δ a q) * f (δ a q)) (fun q => π q * f q) fun _ => rfl
        rw [hmean]
        exact congrFun (pastStep_const_of_bijective δ π hπ_pos a (hbij a) (hpres a) (∑ q : Q, π q * f q)) r
      simp only [hterm, Finset.sum_const, Finset.card_univ, nsmul_eq_mul]
      have hcard : (Fintype.card A : ℝ) ≠ 0 := Nat.cast_ne_zero.mpr Fintype.card_ne_zero
      rw [← mul_assoc, inv_mul_cancel₀ hcard, one_mul]

/-- Theorem 1a (Vanishing of `W_c` on every group / bijective automaton): `wcOp ≡ 0` on all observables. -/
theorem wcOp_eq_zero_of_bijective (δ : A → Q → Q) (π : Q → ℝ)
    (hπ_pos : ∀ q, 0 < π q) (hπ_sum : ∑ q : Q, π q = 1) [Nonempty A]
    (hbij : ∀ a, Function.Bijective (δ a)) (hpres : ∀ a q, π (δ a q) = π q)
    (γ : ℝ) (T : Nat) (v : Q → ℝ) :
    wcOp δ π γ T v = fun _ => 0 := by
  unfold wcOp
  have hzero : (fun q => ∑ t ∈ Finset.range T, γ ^ (t + 1) * pastOp δ π (t + 1) (center π v) q) = fun _ => 0 := by
    funext q
    refine Finset.sum_eq_zero fun t _ => ?_
    rw [pastOp_of_bijective δ π hπ_pos hbij hpres (t + 1) (center π v)]
    rw [center_mean_zero π hπ_sum v, mul_zero]
  rw [hzero]
  exact center_const π hπ_sum 0

theorem pastKernel_eq_one_of_bijective (δ : A → Q → Q) (π : Q → ℝ)
    (hπ_pos : ∀ q, 0 < π q) [Nonempty A]
    (hbij : ∀ a, Function.Bijective (δ a)) (hpres : ∀ a q, π (δ a q) = π q) :
    ∀ (t : Nat) (q r : Q), pastKernel δ π t q r = 1
  | 0, _, _ => rfl
  | t + 1, q, r => by
      simp only [pastKernel]
      have hinner : ∀ a : A,
          pastStep δ π a (fun q' => pastStep δ π a (fun r' => pastKernel δ π t q' r') r) q = 1 := by
        intro a
        have hr : ∀ q' : Q, pastStep δ π a (fun r' => pastKernel δ π t q' r') r = 1 := by
          intro q'
          have hconst : (fun r' : Q => pastKernel δ π t q' r') = fun _ => 1 := by
            funext r'; exact pastKernel_eq_one_of_bijective δ π hπ_pos hbij hpres t q' r'
          rw [hconst]
          exact congrFun (pastStep_const_of_bijective δ π hπ_pos a (hbij a) (hpres a) 1) r
        have hq : (fun q' : Q => pastStep δ π a (fun r' => pastKernel δ π t q' r') r) = fun _ => 1 := by
          funext q'; exact hr q'
        rw [hq]
        exact congrFun (pastStep_const_of_bijective δ π hπ_pos a (hbij a) (hpres a) 1) q
      simp only [hinner, Finset.sum_const, Finset.card_univ, nsmul_eq_mul, mul_one]
      have hcard : (Fintype.card A : ℝ) ≠ 0 := Nat.cast_ne_zero.mpr Fintype.card_ne_zero
      exact inv_mul_cancel₀ hcard

/-- Theorem 1b (Bilinear form vanishing of `W_c` on every bijective / group automaton). -/
theorem pastForm_eq_zero_of_bijective (δ : A → Q → Q) (π : Q → ℝ)
    (hπ_pos : ∀ q, 0 < π q) (hπ_sum : ∑ q : Q, π q = 1) [Nonempty A]
    (hbij : ∀ a, Function.Bijective (δ a)) (hpres : ∀ a q, π (δ a q) = π q)
    (γ : ℝ) (T : Nat) (u v : Q → ℝ) :
    pastForm δ π γ T u v = 0 := by
  unfold pastForm
  refine Finset.sum_eq_zero fun t _ => ?_
  have hsum : (∑ q : Q, ∑ r : Q,
      π q * π r * center π u q * pastKernel δ π (t + 1) q r * center π v r) = 0 := by
    have hker : ∀ q r : Q, pastKernel δ π (t + 1) q r = 1 := fun q r =>
      pastKernel_eq_one_of_bijective δ π hπ_pos hbij hpres (t + 1) q r
    have hsplit : ∀ q r : Q,
        π q * π r * center π u q * pastKernel δ π (t + 1) q r * center π v r =
          (π q * center π u q) * (π r * center π v r) := by
      intro q r
      rw [hker q r]
      ring
    simp_rw [hsplit, ← Finset.mul_sum, ← Finset.sum_mul, center_mean_zero π hπ_sum u, zero_mul]
  rw [hsum, mul_zero]

/-- Forward Koopman observability operator `Wo(o, γ, T)` matching `W_o` on `L^2(π)`. -/
def futureOp (δ : A → Q → Q) (π : Q → ℝ) (o : Q → ℝ) : Nat → (Q → ℝ) → (Q → ℝ)
  | 0, f => fun q => o q * piInner π o f
  | t + 1, f => fun q =>
      (Fintype.card A : ℝ)⁻¹ * ∑ a : A, koopman δ a (futureOp δ π o t (pastStep δ π a f)) q

def woOp (δ : A → Q → Q) (π : Q → ℝ) (o : Q → ℝ) (γ : ℝ) (T : Nat) (v : Q → ℝ) : Q → ℝ :=
  center π (fun q => ∑ t ∈ Finset.range T, γ ^ t * futureOp δ π o t (center π v) q)

theorem futureOp_smul (δ : A → Q → Q) (π : Q → ℝ) (o : Q → ℝ) :
    ∀ (t : Nat) (α : ℝ) (f : Q → ℝ),
      futureOp δ π o t (fun q => α * f q) = fun q => α * futureOp δ π o t f q
  | 0, α, f => by
      funext q
      simp only [futureOp, piInner_smul_right]
      ring
  | t + 1, α, f => by
      funext q
      simp only [futureOp]
      have hterm : ∀ a : A,
          koopman δ a (futureOp δ π o t (pastStep δ π a (fun x => α * f x))) q =
            α * koopman δ a (futureOp δ π o t (pastStep δ π a f)) q := fun a => by
        rw [pastStep_smul, futureOp_smul δ π o t α (pastStep δ π a f)]
        rfl
      simp only [hterm]
      rw [← Finset.mul_sum Finset.univ _ α]
      ring

theorem woOp_smul (δ : A → Q → Q) (π : Q → ℝ) (o : Q → ℝ) (γ : ℝ) (T : Nat) (α : ℝ) (v : Q → ℝ) :
    woOp δ π o γ T (fun q => α * v q) = fun q => α * woOp δ π o γ T v q := by
  unfold woOp
  have hinner : (fun q => ∑ t ∈ Finset.range T, γ ^ t * futureOp δ π o t (center π (fun x => α * v x)) q) =
      fun q => α * ∑ t ∈ Finset.range T, γ ^ t * futureOp δ π o t (center π v) q := by
    funext q
    rw [center_smul, Finset.mul_sum]
    refine Finset.sum_congr rfl fun t _ => ?_
    rw [futureOp_smul]
    dsimp only
    ring
  rw [hinner, center_smul]

/-! ### Dirichlet Kinetic Operator `ℒ` -/

/-- Dirichlet kinetic quadratic form `(1 / (2|A|)) ∑_{a,q} π(q) (f(δ_a q) - f(q))^2`. -/
def kineticForm (δ : A → Q → Q) (π : Q → ℝ) (f : Q → ℝ) : ℝ :=
  (1 / (2 * (Fintype.card A : ℝ))) * ∑ a : A, ∑ q : Q, π q * (f (δ a q) - f q) ^ 2

/-- Dirichlet kinetic linear operator `ℒ = (1 / (2|A|)) ∑_a (T_a - I)^* (T_a - I)` on `L^2(π)`. -/
def kineticOp (δ : A → Q → Q) (π : Q → ℝ) (f : Q → ℝ) : Q → ℝ :=
  fun q =>
    (1 / (2 * (Fintype.card A : ℝ))) *
      ∑ a : A, (pastStep δ π a (fun r => koopman δ a f r - f r) q - (koopman δ a f q - f q))

theorem kineticOp_smul (δ : A → Q → Q) (π : Q → ℝ) (α : ℝ) (f : Q → ℝ) :
    kineticOp δ π (fun q => α * f q) = fun q => α * kineticOp δ π f q := by
  funext q
  unfold kineticOp
  have hterm : ∀ a : A,
      pastStep δ π a (fun r => koopman δ a (fun x => α * f x) r - α * f r) q -
          (koopman δ a (fun x => α * f x) q - α * f q) =
        α * (pastStep δ π a (fun r => koopman δ a f r - f r) q - (koopman δ a f q - f q)) := by
    intro a
    have hdiff : (fun r => koopman δ a (fun x => α * f x) r - α * f r) =
        fun r => α * (koopman δ a f r - f r) := by
      funext r; unfold koopman; ring
    rw [hdiff, pastStep_smul]
    unfold koopman
    ring
  simp_rw [hterm, ← Finset.mul_sum]
  ring

theorem kineticOp_const (δ : A → Q → Q) (π : Q → ℝ) (c : ℝ) :
    kineticOp δ π (fun _ => c) = fun _ => 0 := by
  funext q
  unfold kineticOp pastStep koopman
  simp

theorem kineticForm_const (δ : A → Q → Q) (π : Q → ℝ) (c : ℝ) :
    kineticForm δ π (fun _ => c) = 0 := by
  unfold kineticForm
  simp

theorem kineticForm_nonneg (δ : A → Q → Q) (π : Q → ℝ)
    (hπ_pos : ∀ q, 0 < π q) (f : Q → ℝ) :
    0 ≤ kineticForm δ π f := by
  unfold kineticForm
  refine mul_nonneg (by positivity) (Finset.sum_nonneg fun a _ => Finset.sum_nonneg fun q _ => ?_)
  exact mul_nonneg (le_of_lt (hπ_pos q)) (sq_nonneg _)

/-- Exact bilinear identity `⟨u, ℒ v⟩_π = (1 / (2|A|)) ∑_{a,q} π(q)(u(δ_a q) - u(q))(v(δ_a q) - v(q))`. -/
theorem kineticOp_inner (δ : A → Q → Q) (π : Q → ℝ)
    (hπ_pos : ∀ q, 0 < π q) (u v : Q → ℝ) :
    piInner π u (kineticOp δ π v) =
      (1 / (2 * (Fintype.card A : ℝ))) *
        ∑ a : A, ∑ q : Q, π q * (u (δ a q) - u q) * (v (δ a q) - v q) := by
  unfold kineticOp piInner
  have h1 : ∀ q : Q,
      π q * u q * ((1 / (2 * (Fintype.card A : ℝ))) *
        ∑ a : A, (pastStep δ π a (fun r => koopman δ a v r - v r) q - (koopman δ a v q - v q))) =
      (1 / (2 * (Fintype.card A : ℝ))) *
        ∑ a : A, π q * u q * (pastStep δ π a (fun r => koopman δ a v r - v r) q - (koopman δ a v q - v q)) := by
    intro q
    have ha : (1 / (2 * (Fintype.card A : ℝ))) *
        ∑ a : A, (pastStep δ π a (fun r => koopman δ a v r - v r) q - (koopman δ a v q - v q)) =
        ∑ a : A, (1 / (2 * (Fintype.card A : ℝ))) *
          (pastStep δ π a (fun r => koopman δ a v r - v r) q - (koopman δ a v q - v q)) :=
      Finset.mul_sum Finset.univ _ (1 / (2 * (Fintype.card A : ℝ)))
    have hb : π q * u q * ∑ a : A, (1 / (2 * (Fintype.card A : ℝ))) *
        (pastStep δ π a (fun r => koopman δ a v r - v r) q - (koopman δ a v q - v q)) =
        ∑ a : A, π q * u q * ((1 / (2 * (Fintype.card A : ℝ))) *
          (pastStep δ π a (fun r => koopman δ a v r - v r) q - (koopman δ a v q - v q))) :=
      Finset.mul_sum Finset.univ _ (π q * u q)
    have hc : (1 / (2 * (Fintype.card A : ℝ))) *
        ∑ a : A, π q * u q * (pastStep δ π a (fun r => koopman δ a v r - v r) q - (koopman δ a v q - v q)) =
        ∑ a : A, (1 / (2 * (Fintype.card A : ℝ))) *
          (π q * u q * (pastStep δ π a (fun r => koopman δ a v r - v r) q - (koopman δ a v q - v q))) :=
      Finset.mul_sum Finset.univ _ (1 / (2 * (Fintype.card A : ℝ)))
    rw [ha, hb, hc]
    refine Finset.sum_congr rfl fun a _ => ?_
    ring
  simp_rw [h1]
  rw [← Finset.mul_sum Finset.univ _ (1 / (2 * (Fintype.card A : ℝ))), Finset.sum_comm]
  congr 1
  refine Finset.sum_congr rfl fun a _ => ?_
  let d : Q → ℝ := fun r => koopman δ a v r - v r
  have hsplit : (∑ q : Q, π q * u q * (pastStep δ π a d q - d q)) =
      piInner π u (pastStep δ π a d) - piInner π u d := by
    unfold piInner
    rw [← Finset.sum_sub_distrib]
    refine Finset.sum_congr rfl fun q _ => by ring
  rw [hsplit, piInner_symm π u (pastStep δ π a d), pastStep_adjoint δ π hπ_pos]
  dsimp only [d]
  unfold piInner koopman
  rw [← Finset.sum_sub_distrib]
  refine Finset.sum_congr rfl fun q _ => by ring

/-- Theorem 2a: `⟨f, ℒ f⟩_π = kineticForm δ π f`. -/
theorem kineticOp_inner_eq_dirichlet (δ : A → Q → Q) (π : Q → ℝ)
    (hπ_pos : ∀ q, 0 < π q) (f : Q → ℝ) :
    piInner π f (kineticOp δ π f) = kineticForm δ π f := by
  rw [kineticOp_inner δ π hπ_pos f f]
  unfold kineticForm
  congr 1
  refine Finset.sum_congr rfl fun a _ => Finset.sum_congr rfl fun q _ => ?_
  ring

/-- Theorem 2b: `ℒ` is self-adjoint in `L^2(π)`. -/
theorem kineticOp_selfAdjoint (δ : A → Q → Q) (π : Q → ℝ)
    (hπ_pos : ∀ q, 0 < π q) (u v : Q → ℝ) :
    piInner π u (kineticOp δ π v) = piInner π (kineticOp δ π u) v := by
  rw [kineticOp_inner δ π hπ_pos u v, piInner_symm, kineticOp_inner δ π hπ_pos v u]
  congr 1
  refine Finset.sum_congr rfl fun a _ => Finset.sum_congr rfl fun q _ => by ring

/-- Constant vectors are always orthogonal to the image of `ℒ`, even before assuming `π` is stationary. -/
theorem piInner_constOne_kineticOp (δ : A → Q → Q) (π : Q → ℝ)
    (hπ_pos : ∀ q, 0 < π q) (f : Q → ℝ) :
    piInner π constOne (kineticOp δ π f) = 0 := by
  rw [kineticOp_selfAdjoint δ π hπ_pos]
  unfold constOne
  rw [kineticOp_const]
  simp [piInner]

end AutomatonOperators

section HeatAndReduction

variable {Q : Type*}

/-- Heat semigroup action `exp(t L) v = ∑' k, (t^k / k!) (L^[k] v)` on `Q → ℝ`. -/
noncomputable def heatApply (t : ℝ) (L : (Q → ℝ) → (Q → ℝ)) (v : Q → ℝ) : Q → ℝ :=
  fun q => ∑' k : ℕ, (t ^ k / (k.factorial : ℝ)) * (L^[k] v q)

private theorem iterate_eigen {L : (Q → ℝ) → (Q → ℝ)}
    (hL_smul : ∀ (α : ℝ) (w : Q → ℝ), L (fun q => α * w q) = fun q => α * L w q)
    {v : Q → ℝ} {c : ℝ} (heig : L v = fun q => c * v q) :
    ∀ k : ℕ, L^[k] v = fun q => c ^ k * v q
  | 0 => by funext q; simp
  | k + 1 => by
      rw [Function.iterate_succ_apply', iterate_eigen hL_smul heig k, hL_smul, heig]
      funext q
      rw [pow_succ']
      ring

/-- On any eigenmode `L v = c v` of a scalar-homogeneous operator `L`, `exp(t L) v = exp(t c) v`. -/
theorem heatApply_eigenmode (t : ℝ) (L : (Q → ℝ) → (Q → ℝ))
    (hL_smul : ∀ (α : ℝ) (w : Q → ℝ), L (fun q => α * w q) = fun q => α * L w q)
    {v : Q → ℝ} {c : ℝ} (heig : L v = fun q => c * v q) :
    heatApply t L v = fun q => Real.exp (t * c) * v q := by
  funext q
  unfold heatApply
  have hterm : ∀ k : ℕ,
      (t ^ k / (k.factorial : ℝ)) * (L^[k] v q) = ((t * c) ^ k / (k.factorial : ℝ)) * v q := by
    intro k
    rw [iterate_eigen hL_smul heig k]
    dsimp only
    rw [mul_pow]
    ring
  simp_rw [hterm, tsum_mul_right]
  have hexp : ∑' k : ℕ, (t * c) ^ k / (k.factorial : ℝ) = Real.exp (t * c) := by
    rw [Real.exp_eq_exp_ℝ, NormedSpace.exp_eq_tsum_div]
  rw [hexp]

/-- Theorem 3a (Spectral reduction on commuting modes): if `W_c v = 0`, `W_o v = e v`, and `L v = c v`,
    then `exp(-λ/2 L) (W_c + W_o) exp(-λ/2 L) v = (e * exp(-λ c)) v`. -/
theorem masterOperator_eigenvalue_on_commuting_mode
    (L Wc Wo : (Q → ℝ) → (Q → ℝ))
    (hL_smul : ∀ (α : ℝ) (w : Q → ℝ), L (fun q => α * w q) = fun q => α * L w q)
    (hWc_smul : ∀ (α : ℝ) (w : Q → ℝ), Wc (fun q => α * w q) = fun q => α * Wc w q)
    (hWo_smul : ∀ (α : ℝ) (w : Q → ℝ), Wo (fun q => α * w q) = fun q => α * Wo w q)
    {v : Q → ℝ} {e c : ℝ}
    (hWc0 : Wc v = fun _ => 0)
    (hWo : Wo v = fun q => e * v q)
    (hL : L v = fun q => c * v q)
    (lam : ℝ) :
    heatApply (-lam / 2) L
      (fun q => Wc (heatApply (-lam / 2) L v) q + Wo (heatApply (-lam / 2) L v) q) =
      fun q => (e * Real.exp (-lam * c)) * v q := by
  have hhalf : heatApply (-lam / 2) L v = fun q => Real.exp ((-lam / 2) * c) * v q :=
    heatApply_eigenmode (-lam / 2) L hL_smul hL
  have hmid : (fun q => Wc (heatApply (-lam / 2) L v) q + Wo (heatApply (-lam / 2) L v) q) =
      fun q => (e * Real.exp ((-lam / 2) * c)) * v q := by
    rw [hhalf, hWc_smul, hWo_smul, hWc0, hWo]
    funext q
    ring
  rw [hmid]
  have hscal : heatApply (-lam / 2) L (fun q => (e * Real.exp ((-lam / 2) * c)) * v q) =
      fun q => (e * Real.exp ((-lam / 2) * c)) * heatApply (-lam / 2) L v q := by
    funext q
    unfold heatApply
    have hlin : ∀ k : ℕ, L^[k] (fun q' => (e * Real.exp ((-lam / 2) * c)) * v q') =
        fun q' => (e * Real.exp ((-lam / 2) * c)) * L^[k] v q' := by
      intro k
      induction k with
      | zero => rfl
      | succ k ih =>
          rw [Function.iterate_succ_apply', ih, hL_smul]
          funext q'
          rw [Function.iterate_succ_apply']
    have hpull : ∀ k : ℕ,
        ((-lam / 2) ^ k / (k.factorial : ℝ)) *
            (L^[k] (fun q' => (e * Real.exp ((-lam / 2) * c)) * v q') q) =
          (e * Real.exp ((-lam / 2) * c)) *
            (((-lam / 2) ^ k / (k.factorial : ℝ)) * (L^[k] v q)) := by
      intro k
      rw [hlin k]
      dsimp only
      ring
    simp_rw [hpull, tsum_mul_left]
  rw [hscal, hhalf]
  funext q
  have hexp : Real.exp ((-lam / 2) * c) * Real.exp ((-lam / 2) * c) = Real.exp (-lam * c) := by
    rw [← Real.exp_add]
    congr 1
    ring
  calc
    e * Real.exp ((-lam / 2) * c) * (Real.exp ((-lam / 2) * c) * v q) =
        e * (Real.exp ((-lam / 2) * c) * Real.exp ((-lam / 2) * c)) * v q := by ring
    _ = (e * Real.exp (-lam * c)) * v q := by rw [hexp]

/-- Theorem 3b (Exact Group Reduction to Gibbs Selection `C43`): for any bijective `π`-preserving
    automaton (such as a finite group automaton with uniform `π`), `wcOp ≡ 0` automatically,
    and on any joint `(Wo, kineticOp)` eigenmode `(e, c)`, the two-sided Master Operator
    reduces identically to eigenvalue `e * exp(-lam * c)` — with zero linearity hypotheses left. -/
theorem group_master_reduces_to_gibbs {Q A : Type*} [Fintype Q] [DecidableEq Q]
    [Fintype A] [DecidableEq A] [Nonempty A]
    (δ : A → Q → Q) (π : Q → ℝ)
    (hπ_pos : ∀ q, 0 < π q) (hπ_sum : ∑ q : Q, π q = 1)
    (hbij : ∀ a, Function.Bijective (δ a)) (hpres : ∀ a q, π (δ a q) = π q)
    (o : Q → ℝ) (γc γo : ℝ) (T : Nat)
    (v : Q → ℝ) (e c lam : ℝ)
    (hWo : woOp δ π o γo T v = fun q => e * v q)
    (hL : kineticOp δ π v = fun q => c * v q) :
    wcOp δ π γc T v = (fun _ => 0) ∧
      heatApply (-lam / 2) (kineticOp δ π)
        (fun q => wcOp δ π γc T (heatApply (-lam / 2) (kineticOp δ π) v) q +
                  woOp δ π o γo T (heatApply (-lam / 2) (kineticOp δ π) v) q) =
        fun q => (e * Real.exp (-lam * c)) * v q := by
  have hwc0 : wcOp δ π γc T v = fun _ => 0 :=
    wcOp_eq_zero_of_bijective δ π hπ_pos hπ_sum hbij hpres γc T v
  refine ⟨hwc0, ?_⟩
  exact masterOperator_eigenvalue_on_commuting_mode
    (kineticOp δ π) (wcOp δ π γc T) (woOp δ π o γo T)
    (kineticOp_smul δ π) (wcOp_smul δ π γc T) (woOp_smul δ π o γo T)
    hwc0 hWo hL lam

end HeatAndReduction

section HypercubeBridge

/-- Single-bit flip transition on `{0, 1}^n` (`Fin n → Bool`). -/
def flipDelta (n : Nat) (i : Fin n) (x : Fin n → Bool) : Fin n → Bool :=
  Function.update x i (!(x i))

/-- Uniform distribution `2^{-n}` on `{0, 1}^n`. -/
noncomputable def unifCube (n : Nat) : (Fin n → Bool) → ℝ :=
  fun _ => ((2 : ℝ) ^ n)⁻¹

/-- `±1` Walsh-Fourier sign encoding of a Boolean output. -/
def boolSign (b : Bool) : ℝ :=
  if b then 1 else -1

/-- Coordinate Boolean influence `Inf_i(g) = P_x[g(x ⊕ e_i) ≠ g(x)]`. -/
noncomputable def coordInfluence {n : Nat} (g : (Fin n → Bool) → Bool) (i : Fin n) : ℝ :=
  ((2 : ℝ) ^ n)⁻¹ * ((Finset.univ.filter fun x : Fin n → Bool => g (flipDelta n i x) ≠ g x).card : ℝ)

/-- Total Boolean influence `I(g) = ∑_i Inf_i(g)`. -/
noncomputable def totalInfluence {n : Nat} (g : (Fin n → Bool) → Bool) : ℝ :=
  ∑ i : Fin n, coordInfluence g i

private theorem boolSign_sub_sq (a b : Bool) :
    (boolSign a - boolSign b) ^ 2 = if a ≠ b then (4 : ℝ) else 0 := by
  cases a <;> cases b <;> norm_num [boolSign]

/-- Theorem 4 (Hypercube Boolean Influence Identity): on the Boolean `n`-cube with single-bit flips
    (`0 < n`), the automaton Dirichlet kinetic form `kineticForm` of a signed Boolean function
    `g` equals normalized total Boolean influence `(2 / n) * I(g)`. -/
theorem hypercube_kineticForm_eq_totalInfluence (n : Nat) (hn : 0 < n)
    (g : (Fin n → Bool) → Bool) :
    kineticForm (flipDelta n) (unifCube n) (fun x => boolSign (g x)) =
      (2 / (n : ℝ)) * totalInfluence g := by
  unfold kineticForm unifCube totalInfluence coordInfluence
  have hinner : ∀ i : Fin n,
      (∑ x : Fin n → Bool, ((2 : ℝ) ^ n)⁻¹ * (boolSign (g (flipDelta n i x)) - boolSign (g x)) ^ 2) =
        4 * (((2 : ℝ) ^ n)⁻¹ * ((Finset.univ.filter fun x : Fin n → Bool => g (flipDelta n i x) ≠ g x).card : ℝ)) := by
    intro i
    have hrow : ∀ x : Fin n → Bool,
        ((2 : ℝ) ^ n)⁻¹ * (boolSign (g (flipDelta n i x)) - boolSign (g x)) ^ 2 =
          ((2 : ℝ) ^ n)⁻¹ * (if g (flipDelta n i x) ≠ g x then (4 : ℝ) else 0) := fun x => by
      rw [boolSign_sub_sq]
    simp_rw [hrow, ← Finset.mul_sum]
    have hcard : (∑ x : Fin n → Bool, if g (flipDelta n i x) ≠ g x then (4 : ℝ) else 0) =
        ((Finset.univ.filter fun x : Fin n → Bool => g (flipDelta n i x) ≠ g x).card : ℝ) * 4 := by
      rw [← Finset.sum_filter, Finset.sum_const, nsmul_eq_mul]
    rw [hcard]
    ring
  simp only [hinner]
  rw [← Finset.mul_sum Finset.univ _ 4, Fintype.card_fin]
  have hne : (n : ℝ) ≠ 0 := Nat.cast_ne_zero.mpr (Nat.ne_of_gt hn)
  calc
    1 / (2 * (n : ℝ)) * (4 * ∑ i : Fin n, ((2 : ℝ) ^ n)⁻¹ *
        ↑(Finset.univ.filter fun x => g (flipDelta n i x) ≠ g x).card) =
        (4 / (2 * (n : ℝ))) * ∑ i : Fin n, ((2 : ℝ) ^ n)⁻¹ *
          ↑(Finset.univ.filter fun x => g (flipDelta n i x) ≠ g x).card := by ring
    _ = (2 / (n : ℝ)) * ∑ i : Fin n, ((2 : ℝ) ^ n)⁻¹ *
          ↑(Finset.univ.filter fun x => g (flipDelta n i x) ≠ g x).card := by
        congr 1
        field_simp [hne]
        ring

end HypercubeBridge

end

end MasterPrinciple
