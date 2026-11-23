import Lean

/-!
# Genuine ternary irreducibility

A finite example showing that a ternary relation need not be reducible
to a conjunction of three pairwise binary relations. This gives a precise,
limited mathematical reading of Peirce's "not a complexus of dyadic
relations" condition.
-/

namespace Cerp.IrreducibleTriadicRelations

/-- Even-parity relation on three Boolean coordinates. -/
def evenParity (s o i : Bool) : Prop :=
  (s = o) ↔ (i = false)

/-- The parity relation is satisfiable after fixing any two coordinates. -/
theorem parity_extend_sign_object (s o : Bool) :
    evenParity s o (if s = o then false else true) := by
  cases s <;> cases o <;> simp [evenParity]

theorem parity_extend_sign_interpretant (s i : Bool) :
    evenParity s (if i = false then s else !s) i := by
  cases s <;> cases i <;> simp [evenParity]

theorem parity_extend_object_interpretant (o i : Bool) :
    evenParity (if i = false then o else !o) o i := by
  cases o <;> cases i <;> simp [evenParity]

/-- A ternary relation is pairwise-factorable if it is exactly the
    conjunction of one relation on each pair of coordinates. -/
def PairwiseFactorable (R : Bool -> Bool -> Bool -> Prop) : Prop :=
  exists (rSO : Bool -> Bool -> Prop)
    (rSI : Bool -> Bool -> Prop) (rOI : Bool -> Bool -> Prop),
      forall s o i,
        R s o i <-> rSO s o /\ rSI s i /\ rOI o i

/-- Even parity cannot be represented as a conjunction of pairwise
    constraints. Every two-coordinate assignment extends to a valid
    triple, forcing each proposed binary factor to be universal; yet
    not every triple satisfies even parity. -/
theorem evenParity_not_pairwise_factorable :
    ¬ PairwiseFactorable evenParity := by
  rintro ⟨rSO, rSI, rOI, h⟩
  have hSO : forall s o, rSO s o := by
    intro s o
    have hp := parity_extend_sign_object s o
    exact (h s o (if s = o then false else true)).mp hp |>.1
  have hSI : forall s i, rSI s i := by
    intro s i
    have hp := parity_extend_sign_interpretant s i
    exact ((h s (if i = false then s else !s) i).mp hp).2.1
  have hOI : forall o i, rOI o i := by
    intro o i
    have hp := parity_extend_object_interpretant o i
    exact ((h (if i = false then o else !o) o i).mp hp).2.2
  have hbad := (h false false true).mpr
    ⟨hSO false false, hSI false true, hOI false true⟩
  simp [evenParity] at hbad

end Cerp.IrreducibleTriadicRelations
