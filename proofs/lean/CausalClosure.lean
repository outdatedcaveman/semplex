import Lean

/-!
Causal closure as stability of block indicators under the Koopman pullback action.

This is a finite/deterministic core lemma for the semantic-grounding programme.
It does not claim that arbitrary invariant linear subspaces define quotients.
-/

namespace Cerp.CausalClosure

variable {Q A : Type}
variable (r : Q → Q → Prop) [DecidableRel r]

/-- Indicator of the equivalence class of c. -/
def blockInd (c : Q) : Q → Bool :=
  fun q => decide (r q c)

/-- Koopman (pullback) action induced by one input letter. -/
def koopman (δ : Q → A → Q) (a : A) (f : Q → Bool) : Q → Bool :=
  fun q => f (δ q a)

/-- The partition is stable when every pulled-back block indicator
    is still constant on each block. -/
def stableIndicators (δ : Q → A → Q) : Prop :=
  ∀ (a : A) (c q q' : Q), r q q' →
    koopman δ a (blockInd r c) q =
    koopman δ a (blockInd r c) q'

/-- The equivalence relation is respected by every transition. -/
def transitionCongruence (δ : Q → A → Q) : Prop :=
  ∀ (a : A) {q q' : Q}, r q q' →
    r (δ q a) (δ q' a)

/--
A partition is a transition congruence exactly when its block indicators
are stable under every Koopman operator.

This is the deterministic finite-state bridge from behavioral closure
to invariant observable structure. The statement itself does not require
finiteness; finiteness is needed to identify the span of block indicators
with all block-constant real-valued observables.
-/
theorem stable_indicators_iff_transition_congruence
    (δ : Q → A → Q) (hr : Equivalence r) :
    stableIndicators r δ ↔ transitionCongruence r δ := by
  constructor
  · intro h a q q' hqq
    have heq := h a (δ q a) q q' hqq
    change blockInd r (δ q a) (δ q a) =
      blockInd r (δ q a) (δ q' a) at heq
    have hleft : blockInd r (δ q a) (δ q a) = true := by
      simp [blockInd, hr.refl]
    have hright : blockInd r (δ q a) (δ q' a) = true := by
      rw [← heq]
      exact hleft
    exact hr.symm (of_decide_eq_true hright)
  · intro h a c q q' hqq
    have hsucc : r (δ q a) (δ q' a) := h a hqq
    change blockInd r c (δ q a) = blockInd r c (δ q' a)
    by_cases hc : r (δ q a) c
    · have hc' : r (δ q' a) c :=
        hr.trans (hr.symm hsucc) hc
      simp [blockInd, hc, hc']
    · have hc' : ¬ r (δ q' a) c := by
        intro h'
        exact hc (hr.trans hsucc h')
      simp [blockInd, hc, hc']

end Cerp.CausalClosure
