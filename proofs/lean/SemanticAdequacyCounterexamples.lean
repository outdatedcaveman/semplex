import CausalRealization

/-!
# Adversarial counterexamples for semantic adequacy

These examples separate predictive sufficiency from full abstraction,
and expose observational equivalence as a relative rather than absolute
notion of semantic identity.
-/

namespace Cerp.SemanticAdequacyCounterexamples

open Cerp.CausalRealization

/-- One trivial test: it returns the same observation on every history. -/
def trivialObservation : TestFamily Bool Unit Unit where
  cost := fun _ => 0
  response := fun _ _ => ()

/-- A representation may retain distinctions invisible to all probes. -/
def overFineBelief : Bool -> Bool := id

/-- The representation is sufficient: equal states certainly predict
    equal observations. -/
theorem overFineBelief_sufficient :
    forall h h' (t : Affordable trivialObservation 0),
      overFineBelief h = overFineBelief h' ->
        trivialObservation.response h t.1 =
          trivialObservation.response h' t.1 := by
  intro h h' t _heq
  rfl

/-- But sufficiency alone does not imply full abstraction: the identity
    representation distinguishes histories that the probe semantics
    deliberately cannot distinguish. -/
theorem sufficiency_not_full_abstraction :
    ¬ FullyAbstract trivialObservation 0 Bool overFineBelief := by
  intro hfull
  have hobs : equivalent trivialObservation 0 false true := by
    intro t
    rfl
  have hEq := (hfull false true).mpr hobs
  exact Bool.noConfusion hEq

/-- A coarser, constant representation is fully abstract for this
    deliberately impoverished observational semantics. -/
def coarseBelief : Bool -> Unit := fun _ => ()

theorem coarseBelief_fully_abstract :
    FullyAbstract trivialObservation 0 Unit coarseBelief := by
  intro h h'
  constructor
  · intro _heq t
    rfl
  · intro _heq
    exact Subsingleton.elim _ _

/-- Strengthening the probe family can break an old observational
    equivalence; the old quotient is budget-relative, not absolute. -/
def informativeObservation : TestFamily Bool Bool Bool where
  cost := fun t => if t then 1 else 0
  response := fun h t => if t then h else false

theorem low_budget_indistinguishable :
    equivalent informativeObservation 0 false true := by
  intro t
  cases ht : t.1 with
  | false => rfl
  | true =>
      have hcost : 1 ≤ 0 := by simpa [informativeObservation, ht] using t.2
      omega

theorem high_budget_separates :
    ¬ equivalent informativeObservation 1 false true := by
  intro h
  have hsep := h ⟨true, by decide⟩
  change false = true at hsep
  exact Bool.noConfusion hsep

end Cerp.SemanticAdequacyCounterexamples
