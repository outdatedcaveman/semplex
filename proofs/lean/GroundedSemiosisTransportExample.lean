import GroundedSemiosisTransport
import OperationalGroundingAdequacy

namespace Cerp.GroundedSemiosisTransportExample

open Cerp.SemanticFibrations
open Cerp.OperationalGroundingAdequacy
open Cerp.GroundedSemiosisTransport

def hiddenBitSemiosis : GroundedSemiosis where
  World := Bool
  Sign := Unit
  Claim := Unit
  Context := Unit
  refers := fun _ w => w = true
  expresses := fun _ _ => ()
  satisfies := fun _ w => w = true
  Evidence := fun _ _ _ => Empty
  evidence_sound := by intro _s _c _w _href hev; cases hev

def hiddenBitProfileSemiosis :=
  transportGroundedSemiosis hiddenBitSemiosis hiddenBitGrounding 1
    hiddenBit_separates_at_one

def trueBitProfileWorld : ProfileWorld hiddenBitGrounding 1 :=
  Quotient.mk (profileSetoid hiddenBitGrounding 1) true

/-- The transported profile semantics retains a true, grounded assertion
    even though no evidence object exists. Truth has not been collapsed
    into evidential support by the representation change. -/
theorem transported_truth_without_evidence :
    And
      (GroundedAssertionTrue hiddenBitProfileSemiosis () () trueBitProfileWorld)
      (Not (EvidentiallySupported hiddenBitProfileSemiosis () () trueBitProfileWorld)) := by
  constructor
  · constructor <;>
      simp [ContentTrue, hiddenBitProfileSemiosis, hiddenBitSemiosis,
        transportGroundedSemiosis, trueBitProfileWorld,
        profileToExternal_mk]
  · intro h
    rcases h with ⟨ev⟩
    cases ev

end Cerp.GroundedSemiosisTransportExample
