import Lean

/-!
A generic finite-state predictive factorization.

Histories are mapped to posterior/information states. Future tests are
mapped to state-conditioned response functions. The history-future
response matrix factors through the posterior state. If the future tests
separate posterior states, equality of response profiles is equivalent
to equality of posterior states.

This file formalizes the algebraic factorization only. A physical model
must still supply the Bayesian update law, the observation channel, and
the admissible future tests.
-/

namespace Cerp.BeliefStateHankel

variable {H X T R Z : Type}

/-- Posterior/information state associated with each history. -/
abbrev Belief (H X : Type) := H → X → R

/-- Future response of a state to a test. -/
abbrev FutureResponse (X T : Type) := T → X → R

/-- A pairing evaluates a belief against a state-conditioned future response. -/
abbrev Pairing (X R : Type) := (X → R) → (X → R) → R

/-- The history-future response matrix, written as a two-argument function. -/
def historyFuture
    (belief : H → X → R)
    (future : T → X → R)
    (pair : Pairing X R) (h : H) (t : T) : R :=
  pair (belief h) (future t)

/-- Two histories are predictively equivalent when every protected future test agrees. -/
def responseEq
    (belief : H → X → R)
    (future : T → X → R)
    (pair : Pairing X R) (h h' : H) : Prop :=
  ∀ t, historyFuture belief future pair h t =
       historyFuture belief future pair h' t

/-- Equality of posterior states is sufficient for equality of all future responses. -/
theorem beliefEq_implies_responseEq
    (belief : H → X → R)
    (future : T → X → R)
    (pair : Pairing X R)
    {h h' : H}
    (heq : belief h = belief h') :
    responseEq belief future pair h h' := by
  intro t
  simp [historyFuture, heq]

/-- Future tests are separating when their response evaluations determine a belief. -/
def testsSeparate
    (future : T → X → R)
    (pair : Pairing X R) : Prop :=
  ∀ μ ν, (∀ t, pair μ (future t) = pair ν (future t)) → μ = ν

/-- If future tests separate beliefs, predictive equivalence implies belief equality. -/
theorem responseEq_implies_beliefEq
    (belief : H → X → R)
    (future : T → X → R)
    (pair : Pairing X R)
    (hsep : testsSeparate future pair)
    {h h' : H}
    (hresp : responseEq belief future pair h h') :
    belief h = belief h' := by
  apply hsep
  exact hresp

/-- Under test separation, posterior equality and predictive equivalence coincide. -/
theorem beliefEq_iff_responseEq
    (belief : H → X → R)
    (future : T → X → R)
    (pair : Pairing X R)
    (hsep : testsSeparate future pair)
    (h h' : H) :
    belief h = belief h' ↔ responseEq belief future pair h h' := by
  constructor
  · intro heq
    exact beliefEq_implies_responseEq belief future pair heq
  · intro hresp
    exact responseEq_implies_beliefEq belief future pair hsep hresp

/-- A decoder from posterior states to future predictions. -/
def beliefDecoder
    (future : T → X → R)
    (pair : Pairing X R) (μ : X → R) (t : T) : R :=
  pair μ (future t)

/-- The history-future response factors exactly through the posterior state. -/
theorem posterior_factorization
    (belief : H → X → R)
    (future : T → X → R)
    (pair : Pairing X R) :
    ∀ h t,
      historyFuture belief future pair h t =
      beliefDecoder future pair (belief h) t := by
  intro h t
  rfl

/-- Any exact internal representation that decodes every future response
    cannot identify histories with different response profiles. -/
theorem representation_kernel_le_responseEq
    (Φ : H → T → R)
    (z : H → Z)
    (decode : Z → T → R)
    (hexact : ∀ h t, Φ h t = decode (z h) t) :
    ∀ h h', z h = z h' → ∀ t, Φ h t = Φ h' t := by
  intro h h' hz t
  calc
    Φ h t = decode (z h) t := hexact h t
    _ = decode (z h') t := by rw [hz]
    _ = Φ h' t := (hexact h' t).symm

/-- Exact realizations must distinguish histories with different future-response profiles. -/
theorem exact_representation_separates_profiles
    (Φ : H → T → R)
    (z : H → Z)
    (decode : Z → T → R)
    (hexact : ∀ h t, Φ h t = decode (z h) t)
    {h h' : H}
    (hneq : ¬ (∀ t, Φ h t = Φ h' t)) :
    z h ≠ z h' := by
  intro hz
  apply hneq
  exact representation_kernel_le_responseEq Φ z decode hexact h h' hz

/-- Approximate response realization: every history's profile is within epsilon
    of the decoder output associated with its internal state. -/
def epsilonAccurate
    (dist : (T → R) → (T → R) → Nat)
    (Φ : H → T → R)
    (z : H → Z)
    (decode : Z → T → R)
    (epsilon : Nat) : Prop :=
  ∀ h, dist (Φ h) (decode (z h)) ≤ epsilon

/-- Histories encoded by the same internal state must have response profiles
    at distance at most 2 epsilon. This is the metric packing lower-bound lemma. -/
theorem same_state_profiles_within_two_epsilon
    (dist : (T → R) → (T → R) → Nat)
    (hsymm : ∀ a b, dist a b = dist b a)
    (htri : ∀ a b c, dist a c ≤ dist a b + dist b c)
    (Φ : H → T → R)
    (z : H → Z)
    (decode : Z → T → R)
    (epsilon : Nat)
    (hacc : epsilonAccurate dist Φ z decode epsilon)
    {h h' : H}
    (hz : z h = z h') :
    dist (Φ h) (Φ h') ≤ epsilon + epsilon := by
  calc
    dist (Φ h) (Φ h')
        ≤ dist (Φ h) (decode (z h)) +
          dist (decode (z h)) (Φ h') :=
          htri (Φ h) (decode (z h)) (Φ h')
    _ = dist (Φ h) (decode (z h')) +
        dist (Φ h') (decode (z h')) := by
          rw [hz, hsymm (decode (z h')) (Φ h')]
    _ ≤ epsilon + epsilon := by
      have hleft : dist (Φ h) (decode (z h')) ≤ epsilon := by
        simpa [hz] using hacc h
      exact Nat.add_le_add hleft (hacc h')

/-- A pair of histories separated by more than 2 epsilon cannot share an
    internal state in an epsilon-accurate realization. -/
theorem separated_profiles_require_distinct_states
    (dist : (T → R) → (T → R) → Nat)
    (hsymm : ∀ a b, dist a b = dist b a)
    (htri : ∀ a b c, dist a c ≤ dist a b + dist b c)
    (Φ : H → T → R)
    (z : H → Z)
    (decode : Z → T → R)
    (epsilon : Nat)
    (hacc : epsilonAccurate dist Φ z decode epsilon)
    {h h' : H}
    (hfar : epsilon + epsilon < dist (Φ h) (Φ h')) :
    z h ≠ z h' := by
  intro hz
  have hclose :=
    same_state_profiles_within_two_epsilon
      dist hsymm htri Φ z decode epsilon hacc hz
  have hcontr : epsilon + epsilon < epsilon + epsilon :=
    Nat.lt_of_lt_of_le hfar hclose
  exact Nat.lt_irrefl _ hcontr

end Cerp.BeliefStateHankel
