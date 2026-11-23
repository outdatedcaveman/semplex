import Lean

/-!
The universal probe-response congruence for a monoid action.

A state is equivalent to another when every protected readout agrees
after every admissible transformation. This is the deterministic core
of the semantic-grounding programme.
-/

namespace Cerp.ObservableCongruence

/-- Minimal monoid structure, kept local so this file depends only on Lean core. -/
class Monoid (M : Type) where
  one : M
  mul : M → M → M
  one_mul : ∀ a : M, mul one a = a
  mul_one : ∀ a : M, mul a one = a
  mul_assoc : ∀ a b c : M, mul (mul a b) c = mul a (mul b c)

variable {M X I Y : Type}
variable [Monoid M]

/-- A left action of a monoid on a state space. -/
structure MonoidAction (M X : Type) [Monoid M] where
  act : M → X → X
  one_act : ∀ x, act Monoid.one x = x
  mul_act : ∀ m n x, act (Monoid.mul m n) x = act m (act n x)

/-- Equality of all protected readouts after every admissible action. -/
def probeEq (A : MonoidAction M X) (obs : I → X → Y) (x y : X) : Prop :=
  ∀ (m : M) (i : I), obs i (A.act m x) = obs i (A.act m y)

/-- The universal probe-response relation is an equivalence relation. -/
theorem probeEq_equivalence
    (A : MonoidAction M X) (obs : I → X → Y) :
    Equivalence (probeEq A obs) := by
  constructor
  · intro x m i
    rfl
  · intro x y h m i
    exact (h m i).symm
  · intro x y z hxy hyz m i
    exact (hxy m i).trans (hyz m i)

/-- The universal probe-response relation is stable under every action. -/
theorem probeEq_action
    (A : MonoidAction M X) (obs : I → X → Y)
    {x y : X} (h : probeEq A obs x y) (n : M) :
    probeEq A obs (A.act n x) (A.act n y) := by
  intro m i
  rw [← A.mul_act m n x, ← A.mul_act m n y]
  exact h (Monoid.mul m n) i

/-- Any action-stable relation that preserves the protected readouts
    is contained in the universal probe-response relation. -/
theorem stable_relation_le_probeEq
    (A : MonoidAction M X) (obs : I → X → Y)
    (R : X → X → Prop)
    (hstable : ∀ x y, R x y → ∀ m, R (A.act m x) (A.act m y))
    (hobs : ∀ x y, R x y → ∀ i, obs i x = obs i y) :
    ∀ x y, R x y → probeEq A obs x y := by
  intro x y h m i
  exact hobs (A.act m x) (A.act m y) (hstable x y h m) i

/-- A representation is sufficient when protected readouts factor through it
    and its internal dynamics commute with the source action. -/
theorem representation_kernel_le_probeEq
    (A : MonoidAction M X) (obs : I → X → Y)
    {Z : Type} (actZ : M → Z → Z) (r : X → Z)
    (hequiv : ∀ m x, r (A.act m x) = actZ m (r x))
    (obsZ : I → Z → Y)
    (hobs : ∀ i x, obs i x = obsZ i (r x)) :
    ∀ x y, r x = r y → probeEq A obs x y := by
  intro x y h m i
  calc
    obs i (A.act m x) = obsZ i (r (A.act m x)) :=
      hobs i (A.act m x)
    _ = obsZ i (actZ m (r x)) := by rw [hequiv]
    _ = obsZ i (actZ m (r y)) := by rw [h]
    _ = obsZ i (r (A.act m y)) := by rw [← hequiv]
    _ = obs i (A.act m y) := (hobs i (A.act m y)).symm

/-- The setoid induced by all protected counterfactual probes. -/
def probeSetoid (A : MonoidAction M X) (obs : I → X → Y) : Setoid X where
  r := probeEq A obs
  iseqv := probeEq_equivalence A obs

/-- The induced action on the quotient of semantically indistinguishable states. -/
def quotientAct (A : MonoidAction M X) (obs : I → X → Y) (m : M)
    (q : Quotient (probeSetoid A obs)) : Quotient (probeSetoid A obs) :=
  Quotient.lift
    (fun x => Quotient.mk (probeSetoid A obs) (A.act m x))
    (by
      intro x y h
      exact Quotient.sound (probeEq_action A obs h m)) q

/-- Each protected readout descends to the semantic quotient. -/
def quotientObs (A : MonoidAction M X) (obs : I → X → Y) (i : I) :
    Quotient (probeSetoid A obs) → Y :=
  Quotient.lift (obs i) (by
    intro x y h
    have h1 := h Monoid.one i
    simpa [A.one_act] using h1)

/-- The quotient readout agrees with the original readout on every state. -/
@[simp] theorem quotientObs_mk
    (A : MonoidAction M X) (obs : I → X → Y) (i : I) (x : X) :
    quotientObs A obs i (Quotient.mk (probeSetoid A obs) x) = obs i x := rfl

end Cerp.ObservableCongruence
