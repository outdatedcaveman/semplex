import SignatureTransportAction

namespace Cerp.TotalMarkovRepresentationGroupoid

open Cerp.StochasticInterventionGrounding
open Cerp.StochasticRepresentationGroupoid
open Cerp.SignatureCovariantMarkovTransport
open Cerp.SignatureTransportCoherence
open Cerp.HigherSemanticCore

/-- A representation together with its own typed state/action/outcome
signature. This is the object type for the total moduli groupoid. -/
structure TotalRepresentation where
  signature : Signature
  model : MarkovRepresentation (State := signature.State)
    (Action := signature.Action) (Outcome := signature.Outcome)

/-- A cross-signature isomorphism of stochastic representations. Unlike the
fixed-signature MarkovIso, its three carrier equivalences may connect
different types. -/
@[ext]
structure TotalMarkovIso (M N : TotalRepresentation) where
  stateEquiv : CarrierEquiv M.signature.State N.signature.State
  actionEquiv : CarrierEquiv M.signature.Action N.signature.Action
  outcomeEquiv : CarrierEquiv M.signature.Outcome N.signature.Outcome
  initial_preserved :
    letI := N.signature.stateDecidableEq
    distEq (mapDist stateEquiv M.model.initialLaw) N.model.initialLaw
  observation_preserved : forall s,
    letI := N.signature.outcomeDecidableEq
    distEq (mapDist outcomeEquiv (M.model.observation s))
      (N.model.observation (stateEquiv s))
  transition_preserved : forall s a,
    letI := N.signature.stateDecidableEq
    distEq (mapDist stateEquiv (M.model.transition s a))
      (N.model.transition (stateEquiv s) (actionEquiv a))

namespace TotalMarkovIso

def refl (M : TotalRepresentation) : TotalMarkovIso M M := by
  letI := M.signature.stateDecidableEq
  letI := M.signature.outcomeDecidableEq
  refine {
    stateEquiv := CarrierEquiv.refl M.signature.State
    actionEquiv := CarrierEquiv.refl M.signature.Action
    outcomeEquiv := CarrierEquiv.refl M.signature.Outcome
    initial_preserved := ?_
    observation_preserved := ?_
    transition_preserved := ?_ }
  case refine_1 =>
    rw [mapDist_carrierEquiv_refl]
    exact distEq_refl _
  case refine_2 =>
    intro s
    rw [mapDist_carrierEquiv_refl]
    exact distEq_refl _
  case refine_3 =>
    intro s a
    rw [mapDist_carrierEquiv_refl]
    exact distEq_refl _

def trans {M N K : TotalRepresentation}
    (f : TotalMarkovIso M N) (g : TotalMarkovIso N K) :
    TotalMarkovIso M K := by
  letI := N.signature.stateDecidableEq
  letI := N.signature.outcomeDecidableEq
  letI := K.signature.stateDecidableEq
  letI := K.signature.outcomeDecidableEq
  refine {
    stateEquiv := f.stateEquiv.trans g.stateEquiv
    actionEquiv := f.actionEquiv.trans g.actionEquiv
    outcomeEquiv := f.outcomeEquiv.trans g.outcomeEquiv
    initial_preserved := ?_
    observation_preserved := ?_
    transition_preserved := ?_ }
  case refine_1 =>
    rw [mapDist_carrierEquiv_trans]
    have hpos : 0 < totalWeight (mapDist g.stateEquiv N.model.initialLaw) := by
      rw [totalWeight_mapDist]
      exact N.model.initial_pos
    exact distEq_trans_pos
      (distEq_map_carrierEquiv g.stateEquiv f.initial_preserved)
      g.initial_preserved hpos
  case refine_2 =>
    intro s
    rw [mapDist_carrierEquiv_trans]
    exact distEq_trans_pos
      (distEq_map_carrierEquiv g.outcomeEquiv (f.observation_preserved s))
      (g.observation_preserved (f.stateEquiv s))
      (by rw [totalWeight_mapDist]; exact N.model.observation_pos (f.stateEquiv s))
  case refine_3 =>
    intro s a
    rw [mapDist_carrierEquiv_trans]
    exact distEq_trans_pos
      (distEq_map_carrierEquiv g.stateEquiv (f.transition_preserved s a))
      (g.transition_preserved (f.stateEquiv s) (f.actionEquiv a))
      (by rw [totalWeight_mapDist]; exact N.model.transition_pos (f.stateEquiv s) (f.actionEquiv a))

def symm {M N : TotalRepresentation} (f : TotalMarkovIso M N) :
    TotalMarkovIso N M := by
  letI := M.signature.stateDecidableEq
  letI := M.signature.outcomeDecidableEq
  letI := N.signature.stateDecidableEq
  letI := N.signature.outcomeDecidableEq
  refine {
    stateEquiv := f.stateEquiv.symm
    actionEquiv := f.actionEquiv.symm
    outcomeEquiv := f.outcomeEquiv.symm
    initial_preserved := ?_
    observation_preserved := ?_
    transition_preserved := ?_ }
  case refine_1 =>
    have h := distEq_map_carrierEquiv f.stateEquiv.symm f.initial_preserved
    have hs := distEq_symm h
    change distEq (mapDist f.stateEquiv.symm N.model.initialLaw)
      (mapDist f.stateEquiv.symm (mapDist f.stateEquiv M.model.initialLaw)) at hs
    rw [mapDist_carrierEquiv_symm_cancel] at hs
    exact hs
  case refine_2 =>
    intro s
    have h := distEq_map_carrierEquiv f.outcomeEquiv.symm
      (f.observation_preserved (f.stateEquiv.symm s))
    have hs := distEq_symm h
    simp only [CarrierEquiv.symm, mapDist_invFun_cancel] at hs
    rw [f.stateEquiv.right_inv] at hs
    change distEq (mapDist f.outcomeEquiv.invFun (N.model.observation s))
      (M.model.observation (f.stateEquiv.invFun s))
    exact hs
  case refine_3 =>
    intro s a
    have h := distEq_map_carrierEquiv f.stateEquiv.symm
      (f.transition_preserved (f.stateEquiv.symm s) (f.actionEquiv.symm a))
    have hs := distEq_symm h
    simp only [CarrierEquiv.symm, mapDist_invFun_cancel] at hs
    rw [f.stateEquiv.right_inv, f.actionEquiv.right_inv] at hs
    change distEq (mapDist f.stateEquiv.invFun (N.model.transition s a))
      (M.model.transition (f.stateEquiv.invFun s) (f.actionEquiv.invFun a))
    exact hs

end TotalMarkovIso

/-- The total groupoid of stochastic causal representations over all typed
signatures. Its arrows are cross-signature Markov isomorphisms. -/
def totalRepresentationGroupoid : Groupoid where
  Obj := TotalRepresentation
  Hom := TotalMarkovIso
  id := TotalMarkovIso.refl
  comp := fun f g => TotalMarkovIso.trans f g
  inv := TotalMarkovIso.symm
  id_comp := by
    intro M N f
    apply TotalMarkovIso.ext <;> apply Cerp.StochasticRepresentationGroupoid.CarrierEquiv.ext <;> funext x <;>
      simp [TotalMarkovIso.trans, TotalMarkovIso.refl,
        CarrierEquiv.trans, CarrierEquiv.refl]
  comp_id := by
    intro M N f
    apply TotalMarkovIso.ext <;> apply Cerp.StochasticRepresentationGroupoid.CarrierEquiv.ext <;> funext x <;>
      simp [TotalMarkovIso.trans, TotalMarkovIso.refl,
        CarrierEquiv.trans, CarrierEquiv.refl]
  assoc := by
    intro M N K L f g h
    apply TotalMarkovIso.ext <;> apply Cerp.StochasticRepresentationGroupoid.CarrierEquiv.ext <;> funext x <;>
      simp [TotalMarkovIso.trans, CarrierEquiv.trans]
  inv_left := by
    intro M N f
    apply TotalMarkovIso.ext
    · apply Cerp.StochasticRepresentationGroupoid.CarrierEquiv.ext
      · funext x
        exact f.stateEquiv.right_inv x
      · funext x
        exact f.stateEquiv.right_inv x
    · apply Cerp.StochasticRepresentationGroupoid.CarrierEquiv.ext
      · funext x
        exact f.actionEquiv.right_inv x
      · funext x
        exact f.actionEquiv.right_inv x
    · apply Cerp.StochasticRepresentationGroupoid.CarrierEquiv.ext
      · funext x
        exact f.outcomeEquiv.right_inv x
      · funext x
        exact f.outcomeEquiv.right_inv x
  inv_right := by
    intro M N f
    apply TotalMarkovIso.ext
    · apply Cerp.StochasticRepresentationGroupoid.CarrierEquiv.ext
      · funext x
        exact f.stateEquiv.left_inv x
      · funext x
        exact f.stateEquiv.left_inv x
    · apply Cerp.StochasticRepresentationGroupoid.CarrierEquiv.ext
      · funext x
        exact f.actionEquiv.left_inv x
      · funext x
        exact f.actionEquiv.left_inv x
    · apply Cerp.StochasticRepresentationGroupoid.CarrierEquiv.ext
      · funext x
        exact f.outcomeEquiv.left_inv x
      · funext x
        exact f.outcomeEquiv.left_inv x
/-- Projection from the total representation groupoid to the signature
groupoid, forgetting the stochastic kernels but retaining all three
coordinate changes. -/
def signatureProjection : GroupoidFunctor totalRepresentationGroupoid
    signatureGroupoid where
  obj := TotalRepresentation.signature
  map := fun f =>
    { state := f.stateEquiv, action := f.actionEquiv, outcome := f.outcomeEquiv }
  map_id := by
    intro M
    apply SignatureEquiv.ext <;> apply Cerp.StochasticRepresentationGroupoid.CarrierEquiv.ext <;> funext x <;> rfl
  map_comp := by
    intro M N K f g
    apply SignatureEquiv.ext <;> apply Cerp.StochasticRepresentationGroupoid.CarrierEquiv.ext <;> funext x <;> rfl

end Cerp.TotalMarkovRepresentationGroupoid

namespace Cerp.TotalMarkovRepresentationGroupoid

open Cerp.StochasticInterventionGrounding
open Cerp.StochasticRepresentationGroupoid
open Cerp.SignatureCovariantMarkovTransport
open Cerp.HigherSemanticCore

/-- The signature arrow underlying a total representation isomorphism. -/
def signatureOfTotalIso {M N : TotalRepresentation}
    (h : TotalMarkovIso M N) : SignatureEquiv M.signature N.signature where
  state := h.stateEquiv
  action := h.actionEquiv
  outcome := h.outcomeEquiv

/-- CoCartesian lift of a signature equivalence: transport a representation
along the signature map. -/
def transportLift {S T : Signature}
    (e : SignatureEquiv S T)
    (M : MarkovRepresentation (State := S.State)
      (Action := S.Action) (Outcome := S.Outcome)) :
    TotalMarkovIso
      ⟨S, M⟩
      ⟨T, transport e M⟩ := by
  letI := T.stateDecidableEq
  letI := T.outcomeDecidableEq
  refine {
    stateEquiv := e.state
    actionEquiv := e.action
    outcomeEquiv := e.outcome
    initial_preserved := ?_
    observation_preserved := ?_
    transition_preserved := ?_ }
  case refine_1 =>
    exact distEq_refl _
  case refine_2 =>
    intro s
    change distEq (mapDist e.outcome (M.observation s))
      (mapDist e.outcome
        (M.observation (e.state.invFun (e.state s))))
    rw [e.state.left_inv]
    exact distEq_refl _
  case refine_3 =>
    intro s a
    change distEq (mapDist e.state (M.transition s a))
      (mapDist e.state
        (M.transition (e.state.invFun (e.state s))
          (e.action.invFun (e.action a))))
    rw [e.state.left_inv, e.action.left_inv]
    exact distEq_refl _

/-- Vertical comparison after a total arrow: the transported source model
and target model now share one signature, and the remaining coordinate maps
are identities. -/
def verticalPart {M N : TotalRepresentation}
    (h : TotalMarkovIso M N) :
    TotalMarkovIso
      ⟨N.signature,
        transport (signatureOfTotalIso h) M.model⟩
      N := by
  let e := signatureOfTotalIso h
  letI := N.signature.stateDecidableEq
  letI := N.signature.outcomeDecidableEq
  refine {
    stateEquiv := CarrierEquiv.refl N.signature.State
    actionEquiv := CarrierEquiv.refl N.signature.Action
    outcomeEquiv := CarrierEquiv.refl N.signature.Outcome
    initial_preserved := ?_
    observation_preserved := ?_
    transition_preserved := ?_ }
  case refine_1 =>
    change distEq
      (mapDist (CarrierEquiv.refl N.signature.State)
        (mapDist e.state M.model.initialLaw))
      N.model.initialLaw
    rw [mapDist_carrierEquiv_refl]
    exact h.initial_preserved
  case refine_2 =>
    intro t
    change distEq
      (mapDist (CarrierEquiv.refl N.signature.Outcome)
        (mapDist e.outcome
          (M.model.observation (e.state.invFun t))))
      (N.model.observation t)
    rw [mapDist_carrierEquiv_refl]
    have hobs := h.observation_preserved (e.state.invFun t)
    change distEq (mapDist h.outcomeEquiv (M.model.observation (h.stateEquiv.invFun t))) (N.model.observation (h.stateEquiv (h.stateEquiv.invFun t))) at hobs
    rw [h.stateEquiv.right_inv] at hobs
    exact hobs
  case refine_3 =>
    intro t a
    change distEq
      (mapDist (CarrierEquiv.refl N.signature.State)
        (mapDist e.state
          (M.model.transition (e.state.invFun t) (e.action.invFun a))))
      (N.model.transition t a)
    rw [mapDist_carrierEquiv_refl]
    have htrans := h.transition_preserved
      (e.state.invFun t) (e.action.invFun a)
    change distEq (mapDist h.stateEquiv (M.model.transition (h.stateEquiv.invFun t) (h.actionEquiv.invFun a))) (N.model.transition (h.stateEquiv (h.stateEquiv.invFun t)) (h.actionEquiv (h.actionEquiv.invFun a))) at htrans
    rw [h.stateEquiv.right_inv, h.actionEquiv.right_inv] at htrans
    exact htrans

/-- Every total arrow factors as a coCartesian signature-transport lift
followed by a vertical, fixed-signature representation isomorphism. This
is the concrete Grothendieck-opfibration factorization. -/
theorem totalIso_factorization {M N : TotalRepresentation}
    (h : TotalMarkovIso M N) :
    TotalMarkovIso.trans
      (transportLift (signatureOfTotalIso h) M.model)
      (verticalPart h) = h := by
  apply TotalMarkovIso.ext <;> apply Cerp.StochasticRepresentationGroupoid.CarrierEquiv.ext <;> funext x <;>
    simp [TotalMarkovIso.trans, transportLift, verticalPart,
      signatureOfTotalIso, CarrierEquiv.trans, CarrierEquiv.refl]

end Cerp.TotalMarkovRepresentationGroupoid

namespace Cerp.TotalMarkovRepresentationGroupoid

open Cerp.SignatureCovariantMarkovTransport

/-- Uniqueness of the vertical factor. Any factorization through the chosen
transport lift has the same vertical arrow. Thus the lift has the universal
factorization property required of a coCartesian arrow. -/
theorem totalIso_vertical_factor_unique {M N : TotalRepresentation}
    (h : TotalMarkovIso M N)
    (v : TotalMarkovIso
      ⟨N.signature,
        transport (signatureOfTotalIso h) M.model⟩ N)
    (hv : TotalMarkovIso.trans
      (transportLift (signatureOfTotalIso h) M.model) v = h) :
    v = verticalPart h := by
  have hstate := congrArg TotalMarkovIso.stateEquiv hv
  have haction := congrArg TotalMarkovIso.actionEquiv hv
  have houtcome := congrArg TotalMarkovIso.outcomeEquiv hv
  change h.stateEquiv.trans v.stateEquiv = h.stateEquiv at hstate
  change h.actionEquiv.trans v.actionEquiv = h.actionEquiv at haction
  change h.outcomeEquiv.trans v.outcomeEquiv = h.outcomeEquiv at houtcome
  apply TotalMarkovIso.ext
  · apply Cerp.StochasticRepresentationGroupoid.CarrierEquiv.ext
    · funext t
      have ht := congrFun (congrArg Cerp.StochasticRepresentationGroupoid.CarrierEquiv.toFun hstate)
        (h.stateEquiv.invFun t)
      change v.stateEquiv (h.stateEquiv (h.stateEquiv.invFun t)) =
        h.stateEquiv (h.stateEquiv.invFun t) at ht
      simpa [h.stateEquiv.right_inv] using ht
    · funext t
      have ht := congrFun (congrArg Cerp.StochasticRepresentationGroupoid.CarrierEquiv.invFun hstate) t
      change h.stateEquiv.invFun (v.stateEquiv.invFun t) =
        h.stateEquiv.invFun t at ht
      have ht' := congrArg h.stateEquiv ht
      simpa [h.stateEquiv.right_inv] using ht'
  · apply Cerp.StochasticRepresentationGroupoid.CarrierEquiv.ext
    · funext a
      have ha := congrFun (congrArg Cerp.StochasticRepresentationGroupoid.CarrierEquiv.toFun haction)
        (h.actionEquiv.invFun a)
      change v.actionEquiv (h.actionEquiv (h.actionEquiv.invFun a)) =
        h.actionEquiv (h.actionEquiv.invFun a) at ha
      simpa [h.actionEquiv.right_inv] using ha
    · funext a
      have ha := congrFun (congrArg Cerp.StochasticRepresentationGroupoid.CarrierEquiv.invFun haction) a
      change h.actionEquiv.invFun (v.actionEquiv.invFun a) =
        h.actionEquiv.invFun a at ha
      have ha' := congrArg h.actionEquiv ha
      simpa [h.actionEquiv.right_inv] using ha'
  · apply Cerp.StochasticRepresentationGroupoid.CarrierEquiv.ext
    · funext o
      have ho := congrFun (congrArg Cerp.StochasticRepresentationGroupoid.CarrierEquiv.toFun houtcome)
        (h.outcomeEquiv.invFun o)
      change v.outcomeEquiv (h.outcomeEquiv (h.outcomeEquiv.invFun o)) =
        h.outcomeEquiv (h.outcomeEquiv.invFun o) at ho
      simpa [h.outcomeEquiv.right_inv] using ho
    · funext o
      have ho := congrFun (congrArg Cerp.StochasticRepresentationGroupoid.CarrierEquiv.invFun houtcome) o
      change h.outcomeEquiv.invFun (v.outcomeEquiv.invFun o) =
        h.outcomeEquiv.invFun o at ho
      have ho' := congrArg h.outcomeEquiv ho
      simpa [h.outcomeEquiv.right_inv] using ho'

end Cerp.TotalMarkovRepresentationGroupoid
