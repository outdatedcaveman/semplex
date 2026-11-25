import StochasticRepresentationGroupoid

namespace Cerp.SignatureCovariantMarkovTransport

open Cerp.StochasticInterventionGrounding
open Cerp.StochasticRepresentationGroupoid
open Cerp.HigherSemanticCore

universe u v w

/-- A typed signature with the equality instances needed by finite laws. -/
structure Signature where
  State : Type u
  Action : Type v
  Outcome : Type w
  stateDecidableEq : DecidableEq State
  actionDecidableEq : DecidableEq Action
  outcomeDecidableEq : DecidableEq Outcome

/-- Invertible changes of state, action, and outcome coordinates. -/
@[ext]
structure SignatureEquiv (S : Signature) (T : Signature) where
  state : CarrierEquiv S.State T.State
  action : CarrierEquiv S.Action T.Action
  outcome : CarrierEquiv S.Outcome T.Outcome

namespace SignatureEquiv

def refl (S : Signature) : SignatureEquiv S S where
  state := CarrierEquiv.refl S.State
  action := CarrierEquiv.refl S.Action
  outcome := CarrierEquiv.refl S.Outcome

def trans {S T U : Signature}
    (e : SignatureEquiv S T) (f : SignatureEquiv T U) :
    SignatureEquiv S U where
  state := e.state.trans f.state
  action := e.action.trans f.action
  outcome := e.outcome.trans f.outcome

def symm {S T : Signature} (e : SignatureEquiv S T) :
    SignatureEquiv T S where
  state := e.state.symm
  action := e.action.symm
  outcome := e.outcome.symm

end SignatureEquiv

/-- The groupoid of typed signatures and invertible coordinate changes. -/
def signatureGroupoid : Groupoid where
  Obj := Signature
  Hom := SignatureEquiv
  id := SignatureEquiv.refl
  comp := fun e f => SignatureEquiv.trans e f
  inv := SignatureEquiv.symm
  id_comp := by
    intro S T e
    apply SignatureEquiv.ext <;> apply CarrierEquiv.ext <;> funext x <;>
      simp [SignatureEquiv.trans, SignatureEquiv.refl,
        CarrierEquiv.trans, CarrierEquiv.refl]
  comp_id := by
    intro S T e
    apply SignatureEquiv.ext <;> apply CarrierEquiv.ext <;> funext x <;>
      simp [SignatureEquiv.trans, SignatureEquiv.refl,
        CarrierEquiv.trans, CarrierEquiv.refl]
  assoc := by
    intro S T U V e f g
    apply SignatureEquiv.ext <;> apply CarrierEquiv.ext <;> funext x <;>
      simp [SignatureEquiv.trans, CarrierEquiv.trans]
  inv_left := by
    intro S T e
    apply SignatureEquiv.ext
    · apply CarrierEquiv.ext
      · funext x
        first | exact e.state.right_inv x | first | exact e.state.right_inv x | exact e.state.left_inv x
      · funext x
        first | exact e.state.right_inv x | exact e.state.left_inv x
    · apply CarrierEquiv.ext
      · funext x
        first | exact e.action.right_inv x | first | exact e.action.right_inv x | exact e.action.left_inv x
      · funext x
        first | exact e.action.right_inv x | exact e.action.left_inv x
    · apply CarrierEquiv.ext
      · funext x
        first | exact e.outcome.right_inv x | first | exact e.outcome.right_inv x | exact e.outcome.left_inv x
      · funext x
        first | exact e.outcome.right_inv x | exact e.outcome.left_inv x
  inv_right := by
    intro S T e
    apply SignatureEquiv.ext
    · apply CarrierEquiv.ext
      · funext x
        first | exact e.state.right_inv x | exact e.state.left_inv x
      · funext x
        first | exact e.state.right_inv x | first | exact e.state.right_inv x | exact e.state.left_inv x
    · apply CarrierEquiv.ext
      · funext x
        first | exact e.action.right_inv x | exact e.action.left_inv x
      · funext x
        first | exact e.action.right_inv x | first | exact e.action.right_inv x | exact e.action.left_inv x
    · apply CarrierEquiv.ext
      · funext x
        first | exact e.outcome.right_inv x | exact e.outcome.left_inv x
      · funext x
        first | exact e.outcome.right_inv x | first | exact e.outcome.right_inv x | exact e.outcome.left_inv x

/-- Push a Markov representation forward along a signature equivalence.
Kernel inputs are pulled back and kernel outputs are pushed forward. -/
def transport {S : Signature} {T : Signature}
    (e : SignatureEquiv S T)
    (M : MarkovRepresentation (State := S.State)
      (Action := S.Action) (Outcome := S.Outcome)) :
    MarkovRepresentation (State := T.State)
      (Action := T.Action) (Outcome := T.Outcome) := by
  letI := T.stateDecidableEq
  letI := T.actionDecidableEq
  letI := T.outcomeDecidableEq
  exact {
    initialLaw := mapDist e.state M.initialLaw
    observation := fun t => mapDist e.outcome (M.observation (e.state.invFun t))
    transition := fun t a =>
      mapDist e.state (M.transition (e.state.invFun t) (e.action.invFun a))
    initial_pos := by
      rw [totalWeight_mapDist]
      exact M.initial_pos
    observation_pos := by
      intro t
      rw [totalWeight_mapDist]
      exact M.observation_pos (e.state.invFun t)
    transition_pos := by
      intro t a
      rw [totalWeight_mapDist]
      exact M.transition_pos (e.state.invFun t) (e.action.invFun a)
    observationMass := M.observationMass
    observationMass_pos := M.observationMass_pos
    observation_normalized := by
      intro t
      rw [totalWeight_mapDist]
      exact M.observation_normalized (e.state.invFun t)
    transitionMass := M.transitionMass
    transitionMass_pos := M.transitionMass_pos
    transition_normalized := by
      intro t a
      rw [totalWeight_mapDist]
      exact M.transition_normalized (e.state.invFun t) (e.action.invFun a)
  }

/-- Signature transport preserves the common observation-row mass. -/
theorem transport_observation_mass
    {S T : Signature} (e : SignatureEquiv S T)
    (M : MarkovRepresentation (State := S.State)
      (Action := S.Action) (Outcome := S.Outcome)) :
    (transport e M).observationMass = M.observationMass := rfl

/-- Signature transport preserves the common transition-row mass. -/
theorem transport_transition_mass
    {S T : Signature} (e : SignatureEquiv S T)
    (M : MarkovRepresentation (State := S.State)
      (Action := S.Action) (Outcome := S.Outcome)) :
    (transport e M).transitionMass = M.transitionMass := rfl

end Cerp.SignatureCovariantMarkovTransport
