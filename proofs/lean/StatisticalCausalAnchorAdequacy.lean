import StochasticInterventionGrounding

/-!
# Statistical causal-anchor fusion

Finite discrete stochastic channels are compared by exact equality of their
normalized distributions. The two-channel criterion identifies a target iff
the intersection of the channels' statistical indistinguishability relations
is diagonal. A noisy complementary-coordinate example shows that neither
channel alone identifies the whole state, while their joint profile does.

Scope: distribution-level identifiability, not finite-sample error bounds.
-/

namespace Cerp.StatisticalCausalAnchorAdequacy

open Cerp.StochasticInterventionGrounding

universe u v w x

structure StatisticalChannel (External : Type u) (Probe : Type v)
    (Outcome : Type w) where
  cost : Probe -> Nat
  response : External -> Probe -> FinDist Outcome

def StatisticalObservationallyEqual
    (C : StatisticalChannel External Probe Outcome) (budget : Nat)
    [DecidableEq Outcome] (e e' : External) : Prop :=
  forall p : {p : Probe // C.cost p <= budget},
    distEq (C.response e p.1) (C.response e' p.1)

def StatisticalJointlyIdentifies
    (A : StatisticalChannel External Probe Outcome)
    (B : StatisticalChannel External Probe' Outcome')
    (budgetA budgetB : Nat) [DecidableEq Outcome] [DecidableEq Outcome'] : Prop :=
  forall e e', (StatisticalObservationallyEqual A budgetA e e' ∧
    StatisticalObservationallyEqual B budgetB e e') -> e = e'

theorem statistical_joint_identification_iff_kernel_intersection_trivial
    (A : StatisticalChannel External Probe Outcome)
    (B : StatisticalChannel External Probe' Outcome')
    (budgetA budgetB : Nat) [DecidableEq Outcome] [DecidableEq Outcome'] :
    StatisticalJointlyIdentifies A B budgetA budgetB ↔
      forall e e', StatisticalObservationallyEqual A budgetA e e' ->
        StatisticalObservationallyEqual B budgetB e e' -> e = e' := by
  constructor
  · intro h e e' hA hB
    exact h e e' ⟨hA, hB⟩
  · intro h e e' hAB
    exact h e e' hAB.1 hAB.2

/-- A 3:1 binary noise channel: it reports the true bit with probability 3/4. -/
def noisyBit (b : Bool) : FinDist Bool :=
  if b then [(true, 3), (false, 1)] else [(false, 3), (true, 1)]

def noisyFirst : StatisticalChannel (Bool × Bool) Unit Bool where
  cost := fun _ => 1
  response := fun e _ => noisyBit e.1

def noisySecond : StatisticalChannel (Bool × Bool) Unit Bool where
  cost := fun _ => 1
  response := fun e _ => noisyBit e.2

theorem noisyBit_separates_truth_values :
    ¬ distEq (noisyBit false) (noisyBit true) := by
  intro h
  have hfalse := h false
  simp [noisyBit, weightOf, totalWeight] at hfalse

theorem noisyFirst_blind_to_second_coordinate (budget : Nat) :
    StatisticalObservationallyEqual noisyFirst budget (false, false) (false, true) := by
  intro p a
  rfl

theorem noisySecond_blind_to_first_coordinate (budget : Nat) :
    StatisticalObservationallyEqual noisySecond budget (false, false) (true, false) := by
  intro p a
  rfl

theorem noisyFirst_distinguishes_first_coordinate
    (e e' : Bool × Bool)
    (h : StatisticalObservationallyEqual noisyFirst 1 e e') :
    e.1 = e'.1 := by
  by_cases heq : e.1 = e'.1
  · exact heq
  · have hdist := h ⟨(), by decide⟩
    have hfalse := hdist false
    cases hleft : e.1 <;> cases hright : e'.1 <;>
      simp_all [noisyFirst, noisyBit, weightOf, totalWeight]

theorem noisySecond_distinguishes_second_coordinate
    (e e' : Bool × Bool)
    (h : StatisticalObservationallyEqual noisySecond 1 e e') :
    e.2 = e'.2 := by
  by_cases heq : e.2 = e'.2
  · exact heq
  · have hdist := h ⟨(), by decide⟩
    have hfalse := hdist false
    cases hleft : e.2 <;> cases hright : e'.2 <;>
      simp_all [noisySecond, noisyBit, weightOf, totalWeight]

/-- Complementary noisy measurements identify the complete external state. -/
theorem noisy_complementary_channels_jointly_identify :
    StatisticalJointlyIdentifies noisyFirst noisySecond 1 1 := by
  intro e e' h
  have hfirst := noisyFirst_distinguishes_first_coordinate e e' h.1
  have hsecond := noisySecond_distinguishes_second_coordinate e e' h.2
  exact Prod.ext hfirst hsecond

theorem noisy_channels_uninformative_at_zero
    (e e' : Bool × Bool) :
    StatisticalObservationallyEqual noisyFirst 0 e e' ∧
    StatisticalObservationallyEqual noisySecond 0 e e' := by
  constructor
  · intro p
    have hp : 1 ≤ 0 := by simpa [noisyFirst] using p.2
    omega
  · intro p
    have hp : 1 ≤ 0 := by simpa [noisySecond] using p.2
    omega

#print axioms noisy_complementary_channels_jointly_identify

end Cerp.StatisticalCausalAnchorAdequacy
