import GroundingAdequacy
import SemanticAdequacyCounterexamples

/-!
Finite witness: passive observations cannot recover a hidden external
referent or hidden truth bit, while the intervention-sensitive probe
separates the two states at the higher budget.
-/

namespace Cerp.GroundingAdequacyExample

open Cerp.CausalRealization
open Cerp.SemanticAdequacyCounterexamples
open Cerp.GroundingAdequacy

theorem hidden_referent_not_decodable_at_zero :
    forall decode : (Affordable informativeObservation 0 -> Bool) -> Bool,
      ¬ ExactReferentDecoder informativeObservation 0 Bool id decode := by
  apply no_exact_referent_decoder informativeObservation 0 Bool id
  · exact low_budget_indistinguishable
  · decide

def hiddenTruth (b : Bool) : Prop := b = true

theorem hidden_truth_not_observable_at_zero :
    ¬ TruthObservable informativeObservation 0 hiddenTruth := by
  intro hinv
  have hiff := hinv false true low_budget_indistinguishable
  have hbad : false = true := hiff.mpr rfl
  cases hbad

theorem hidden_referent_observable_at_one :
    ReferentObservable informativeObservation 1 Bool id := by
  intro h h' heq
  cases h <;> cases h' <;> simp_all [equivalent, informativeObservation]

theorem hidden_truth_observable_at_one :
    TruthObservable informativeObservation 1 hiddenTruth := by
  intro h h' heq
  cases h <;> cases h' <;> simp_all [hiddenTruth, equivalent, informativeObservation]

end Cerp.GroundingAdequacyExample
