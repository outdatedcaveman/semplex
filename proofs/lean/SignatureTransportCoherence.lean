import SignatureCovariantMarkovTransport

namespace Cerp.SignatureTransportCoherence

open Cerp.StochasticInterventionGrounding
open Cerp.StochasticRepresentationGroupoid
open Cerp.SignatureCovariantMarkovTransport
open Cerp.HigherSemanticCore

private theorem mapDist_id {A : Type} (d : FinDist A) :
    mapDist (id : A → A) d = d := by
  induction d with
  | nil => rfl
  | cons p rest ih =>
      cases p
      simp [mapDist, ih]

/-- Identity reindexing changes only the presentation of finite laws; the
underlying normalized representation is canonically Markov-isomorphic. -/
def identityTransportIso (S : Signature)
    (M : MarkovRepresentation (State := S.State)
      (Action := S.Action) (Outcome := S.Outcome)) :
    letI := S.stateDecidableEq
    letI := S.outcomeDecidableEq
    MarkovIso (transport (SignatureEquiv.refl S) M) M := by
  letI := S.stateDecidableEq
  letI := S.outcomeDecidableEq
  refine {
    stateEquiv := CarrierEquiv.refl S.State
    actionEquiv := CarrierEquiv.refl S.Action
    outcomeEquiv := CarrierEquiv.refl S.Outcome
    initial_preserved := ?_
    observation_preserved := ?_
    transition_preserved := ?_ }
  case refine_1 =>
    change distEq (mapDist (CarrierEquiv.refl S.State)
      (mapDist (CarrierEquiv.refl S.State) M.initialLaw)) M.initialLaw
    rw [mapDist_carrierEquiv_refl, mapDist_carrierEquiv_refl]
    exact distEq_refl _
  case refine_2 =>
    intro s
    change distEq (mapDist (CarrierEquiv.refl S.Outcome)
      (mapDist (CarrierEquiv.refl S.Outcome)
        (M.observation ((CarrierEquiv.refl S.State).invFun s))))
      (M.observation s)
    simp only [CarrierEquiv.refl, id_eq]
    rw [mapDist_id, mapDist_id]
    exact distEq_refl _
  case refine_3 =>
    intro s a
    change distEq (mapDist (CarrierEquiv.refl S.State)
      (mapDist (CarrierEquiv.refl S.State)
        (M.transition ((CarrierEquiv.refl S.State).invFun s)
          ((CarrierEquiv.refl S.Action).invFun a))))
      (M.transition s a)
    simp only [CarrierEquiv.refl, id_eq]
    rw [mapDist_id, mapDist_id]
    exact distEq_refl _

/-- Sequential signature transport is canonically isomorphic to transport
along the composite signature equivalence. The comparison maps are identity
maps on the final carriers; equality is asserted at the level of normalized
finite laws, not raw list presentations. -/
def compositeTransportIso {S : Signature} {T : Signature} {U : Signature}
    (e : SignatureEquiv S T) (f : SignatureEquiv T U)
    (M : MarkovRepresentation (State := S.State)
      (Action := S.Action) (Outcome := S.Outcome)) :
    letI := S.stateDecidableEq
    letI := S.outcomeDecidableEq
    letI := T.stateDecidableEq
    letI := T.outcomeDecidableEq
    letI := U.stateDecidableEq
    letI := U.outcomeDecidableEq
    MarkovIso (transport f (transport e M))
      (transport (SignatureEquiv.trans e f) M) := by
  letI := S.stateDecidableEq
  letI := S.outcomeDecidableEq
  letI := T.stateDecidableEq
  letI := T.outcomeDecidableEq
  letI := U.stateDecidableEq
  letI := U.outcomeDecidableEq
  refine {
    stateEquiv := CarrierEquiv.refl U.State
    actionEquiv := CarrierEquiv.refl U.Action
    outcomeEquiv := CarrierEquiv.refl U.Outcome
    initial_preserved := ?_
    observation_preserved := ?_
    transition_preserved := ?_ }
  case refine_1 =>
    change distEq
      (mapDist (CarrierEquiv.refl U.State)
        (mapDist f.state (mapDist e.state M.initialLaw)))
      (mapDist (e.state.trans f.state) M.initialLaw)
    rw [mapDist_carrierEquiv_refl, mapDist_carrierEquiv_trans]
    exact distEq_refl _
  case refine_2 =>
    intro t
    change distEq
      (mapDist (CarrierEquiv.refl U.Outcome)
        (mapDist f.outcome
          (mapDist e.outcome
            (M.observation (e.state.invFun (f.state.invFun t))))))
      (mapDist (e.outcome.trans f.outcome)
        (M.observation ((e.state.trans f.state).invFun t)))
    rw [mapDist_carrierEquiv_refl, mapDist_carrierEquiv_trans]
    simp [CarrierEquiv.trans]
    exact distEq_refl _
  case refine_3 =>
    intro t a
    change distEq
      (mapDist (CarrierEquiv.refl U.State)
        (mapDist f.state
          (mapDist e.state
            (M.transition (e.state.invFun (f.state.invFun t))
              (e.action.invFun (f.action.invFun a))))))
      (mapDist (e.state.trans f.state)
        (M.transition ((e.state.trans f.state).invFun t)
          ((e.action.trans f.action).invFun a)))
    rw [mapDist_carrierEquiv_refl, mapDist_carrierEquiv_trans]
    simp [CarrierEquiv.trans]
    exact distEq_refl _

end Cerp.SignatureTransportCoherence
