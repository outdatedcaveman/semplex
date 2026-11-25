import SignatureTransportCoherence

namespace Cerp.SignatureTransportCoherence

open Cerp.StochasticInterventionGrounding
open Cerp.StochasticRepresentationGroupoid
open Cerp.SignatureCovariantMarkovTransport
open Cerp.HigherSemanticCore

/-- Conjugate a representation isomorphism by a signature equivalence.
This is the reindexing action on arrows required by the Grothendieck
construction. -/
def transportMarkovIso {S T : Signature}
    (e : SignatureEquiv S T)
    (M N : MarkovRepresentation (State := S.State)
      (Action := S.Action) (Outcome := S.Outcome))
    (h : letI := S.stateDecidableEq; letI := S.outcomeDecidableEq; MarkovIso M N) :
    letI := T.stateDecidableEq
    letI := T.outcomeDecidableEq
    MarkovIso (transport e M) (transport e N) := by
  letI := S.stateDecidableEq
  letI := S.outcomeDecidableEq
  letI := T.stateDecidableEq
  letI := T.outcomeDecidableEq
  let stateConj : CarrierEquiv T.State T.State :=
    (e.state.symm.trans h.stateEquiv).trans e.state
  let actionConj : CarrierEquiv T.Action T.Action :=
    (e.action.symm.trans h.actionEquiv).trans e.action
  let outcomeConj : CarrierEquiv T.Outcome T.Outcome :=
    (e.outcome.symm.trans h.outcomeEquiv).trans e.outcome
  refine {
    stateEquiv := stateConj
    actionEquiv := actionConj
    outcomeEquiv := outcomeConj
    initial_preserved := ?_
    observation_preserved := ?_
    transition_preserved := ?_ }
  case refine_1 =>
    change distEq
      (mapDist stateConj (mapDist e.state M.initialLaw))
      (mapDist e.state N.initialLaw)
    dsimp [stateConj]
    rw [mapDist_carrierEquiv_trans, mapDist_carrierEquiv_trans,
      mapDist_carrierEquiv_symm_cancel]
    exact distEq_map_carrierEquiv e.state h.initial_preserved
  case refine_2 =>
    intro t
    change distEq
      (mapDist outcomeConj
        (mapDist e.outcome (M.observation (e.state.invFun t))))
      (mapDist e.outcome
        (N.observation (e.state.invFun (stateConj t))))
    dsimp [outcomeConj, stateConj]
    rw [mapDist_carrierEquiv_trans, mapDist_carrierEquiv_trans,
      mapDist_carrierEquiv_symm_cancel]
    have hstate :
        e.state.invFun (((e.state.symm.trans h.stateEquiv).trans e.state) t) =
          h.stateEquiv (e.state.invFun t) := by
      simp only [CarrierEquiv.trans, CarrierEquiv.symm]
      exact e.state.left_inv _
    rw [hstate]
    exact distEq_map_carrierEquiv e.outcome
      (h.observation_preserved (e.state.invFun t))
  case refine_3 =>
    intro t a
    change distEq
      (mapDist stateConj
        (mapDist e.state
          (M.transition (e.state.invFun t) (e.action.invFun a))))
      (mapDist e.state
        (N.transition (e.state.invFun (stateConj t))
          (e.action.invFun (actionConj a))))
    dsimp [stateConj, actionConj]
    rw [mapDist_carrierEquiv_trans, mapDist_carrierEquiv_trans,
      mapDist_carrierEquiv_symm_cancel]
    have hstate :
        e.state.invFun (((e.state.symm.trans h.stateEquiv).trans e.state) t) =
          h.stateEquiv (e.state.invFun t) := by
      simp only [CarrierEquiv.trans, CarrierEquiv.symm]
      exact e.state.left_inv _
    have haction :
        e.action.invFun (((e.action.symm.trans h.actionEquiv).trans e.action) a) =
          h.actionEquiv (e.action.invFun a) := by
      simp only [CarrierEquiv.trans, CarrierEquiv.symm]
      exact e.action.left_inv _
    rw [hstate, haction]
    exact distEq_map_carrierEquiv e.state
      (h.transition_preserved (e.state.invFun t) (e.action.invFun a))

end Cerp.SignatureTransportCoherence
