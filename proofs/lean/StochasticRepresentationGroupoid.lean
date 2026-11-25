import StochasticInterventionGrounding
import HigherSemanticCore

namespace Cerp.StochasticRepresentationGroupoid

open Cerp.StochasticInterventionGrounding
open Cerp.HigherSemanticCore

universe u v w

variable {State : Type u} {Action : Type v} {Outcome : Type w}
variable [DecidableEq State] [DecidableEq Action] [DecidableEq Outcome]

/-- A carrier equivalence, independent of Mathlib. -/
@[ext]
structure CarrierEquiv (A : Type u) (B : Type v) where
  toFun : A → B
  invFun : B → A
  left_inv : ∀ a, invFun (toFun a) = a
  right_inv : ∀ b, toFun (invFun b) = b

instance {A : Type u} {B : Type v} : CoeFun (CarrierEquiv A B) (fun _ => A → B) :=
  ⟨CarrierEquiv.toFun⟩

namespace CarrierEquiv

def refl (A : Type u) : CarrierEquiv A A where
  toFun := id
  invFun := id
  left_inv := by intro a; rfl
  right_inv := by intro a; rfl

def trans {A : Type u} {B : Type v} {C : Type w}
    (e : CarrierEquiv A B) (f : CarrierEquiv B C) : CarrierEquiv A C where
  toFun := fun a => f (e a)
  invFun := fun c => e.invFun (f.invFun c)
  left_inv := by intro a; simp [f.left_inv, e.left_inv]
  right_inv := by intro c; simp [e.right_inv, f.right_inv]

def symm {A : Type u} {B : Type v} (e : CarrierEquiv A B) : CarrierEquiv B A where
  toFun := e.invFun
  invFun := e.toFun
  left_inv := e.right_inv
  right_inv := e.left_inv

end CarrierEquiv

theorem mapDist_carrierEquiv_trans {A : Type u} {B : Type v} {C : Type w}
    (e : CarrierEquiv A B) (f : CarrierEquiv B C) (d : FinDist A) :
    mapDist (e.trans f) d = mapDist f (mapDist e d) := by
  induction d with
  | nil => rfl
  | cons p rest ih =>
      rcases p with ⟨a, n⟩
      change (f (e a), n) :: mapDist (e.trans f) rest =
        (f (e a), n) :: mapDist f (mapDist e rest)
      exact congrArg (fun xs => (f (e a), n) :: xs) ih

theorem mapDist_carrierEquiv_refl {A : Type u} (d : FinDist A) :
    mapDist (CarrierEquiv.refl A) d = d := by
  induction d with
  | nil => rfl
  | cons p rest ih =>
      rcases p with ⟨a,n⟩
      change (a,n) :: mapDist (CarrierEquiv.refl A) rest = (a,n) :: rest
      exact congrArg (fun xs => (a,n) :: xs) ih

theorem mapDist_carrierEquiv_symm_cancel {A : Type u} {B : Type v}
    (e : CarrierEquiv A B) (d : FinDist A) :
    mapDist e.symm (mapDist e d) = d := by
  induction d with
  | nil => rfl
  | cons p rest ih =>
      rcases p with ⟨a,n⟩
      change (e.invFun (e a),n) :: mapDist e.symm (mapDist e rest) = (a,n) :: rest
      rw [e.left_inv a]
      exact congrArg (fun xs => (a,n) :: xs) ih

theorem mapDist_invFun_cancel {A : Type u} {B : Type v}
    (e : CarrierEquiv A B) (d : FinDist A) :
    mapDist e.invFun (mapDist e.toFun d) = d := by
  induction d with
  | nil => rfl
  | cons p rest ih =>
      rcases p with ⟨a,n⟩
      change (e.invFun (e.toFun a),n) ::
        mapDist e.invFun (mapDist e.toFun rest) = (a,n) :: rest
      rw [e.left_inv a]
      exact congrArg (fun xs => (a,n) :: xs) ih

theorem distEq_trans_pos {A : Type u} [DecidableEq A]
    {d₁ d₂ d₃ : FinDist A}
    (h₁₂ : distEq d₁ d₂) (h₂₃ : distEq d₂ d₃)
    (hpos : 0 < totalWeight d₂) : distEq d₁ d₃ := by
  intro a
  have hbig :
      weightOf a d₁ * totalWeight d₃ * totalWeight d₂ =
        weightOf a d₃ * totalWeight d₁ * totalWeight d₂ := by
    calc
      weightOf a d₁ * totalWeight d₃ * totalWeight d₂ =
          (weightOf a d₁ * totalWeight d₂) * totalWeight d₃ := by ac_rfl
      _ = (weightOf a d₂ * totalWeight d₁) * totalWeight d₃ := by rw [h₁₂ a]
      _ = (weightOf a d₂ * totalWeight d₃) * totalWeight d₁ := by ac_rfl
      _ = (weightOf a d₃ * totalWeight d₂) * totalWeight d₁ := by rw [h₂₃ a]
      _ = weightOf a d₃ * totalWeight d₁ * totalWeight d₂ := by ac_rfl
  exact Nat.eq_of_mul_eq_mul_right hpos hbig

theorem distEq_refl {A : Type u} [DecidableEq A] (d : FinDist A) : distEq d d := by
  intro a
  rfl

theorem distEq_symm {A : Type u} [DecidableEq A]
    {d₁ d₂ : FinDist A} (h : distEq d₁ d₂) : distEq d₂ d₁ := by
  intro a
  exact (h a).symm

theorem distEq_map_carrierEquiv {A : Type u} {B : Type v}
    [DecidableEq A] [DecidableEq B] (e : CarrierEquiv A B)
    {d₁ d₂ : FinDist A} (h : distEq d₁ d₂) :
    distEq (mapDist e d₁) (mapDist e d₂) :=
  channel_map_preserves_distEq e h

/-- A finite stochastic causal representation with positive-mass laws. -/
structure MarkovRepresentation where
  initialLaw : FinDist State
  observation : State → FinDist Outcome
  transition : State → Action → FinDist State
  initial_pos : 0 < totalWeight initialLaw
  observation_pos : ∀ s, 0 < totalWeight (observation s)
  transition_pos : ∀ s a, 0 < totalWeight (transition s a)
  /-- Every observation row has one common positive mass, so it defines
      a genuine normalized probability kernel after division by this mass. -/
  observationMass : Nat
  observationMass_pos : 0 < observationMass
  observation_normalized : ∀ s, totalWeight (observation s) = observationMass
  /-- Likewise, transition rows share one common positive mass. -/
  transitionMass : Nat
  transitionMass_pos : 0 < transitionMass
  transition_normalized : ∀ s a, totalWeight (transition s a) = transitionMass

/-- A complete isomorphism: independent bijections on states, actions and
    outcomes, preserving initialization, observation, and transitions. -/
@[ext]
structure MarkovIso (M N : MarkovRepresentation (State := State)
    (Action := Action) (Outcome := Outcome)) where
  stateEquiv : CarrierEquiv State State
  actionEquiv : CarrierEquiv Action Action
  outcomeEquiv : CarrierEquiv Outcome Outcome
  initial_preserved :
    distEq (mapDist stateEquiv M.initialLaw) N.initialLaw
  observation_preserved : ∀ s,
    distEq (mapDist outcomeEquiv (M.observation s))
      (N.observation (stateEquiv s))
  transition_preserved : ∀ s a,
    distEq (mapDist stateEquiv (M.transition s a))
      (N.transition (stateEquiv s) (actionEquiv a))

namespace MarkovIso

variable {M N K : MarkovRepresentation
  (State := State) (Action := Action) (Outcome := Outcome)}

def refl (M : MarkovRepresentation (State := State)
    (Action := Action) (Outcome := Outcome)) : MarkovIso M M where
  stateEquiv := CarrierEquiv.refl _
  actionEquiv := CarrierEquiv.refl _
  outcomeEquiv := CarrierEquiv.refl _
  initial_preserved := by
    change distEq (mapDist (CarrierEquiv.refl State) M.initialLaw) M.initialLaw
    rw [mapDist_carrierEquiv_refl]
    exact distEq_refl _
  observation_preserved := by
    intro s
    change distEq (mapDist (CarrierEquiv.refl Outcome) (M.observation s)) (M.observation s)
    rw [mapDist_carrierEquiv_refl]
    exact distEq_refl _
  transition_preserved := by
    intro s a
    change distEq (mapDist (CarrierEquiv.refl State) (M.transition s a)) (M.transition s a)
    rw [mapDist_carrierEquiv_refl]
    exact distEq_refl _

def trans (f : MarkovIso M N) (g : MarkovIso N K) : MarkovIso M K where
  stateEquiv := f.stateEquiv.trans g.stateEquiv
  actionEquiv := f.actionEquiv.trans g.actionEquiv
  outcomeEquiv := f.outcomeEquiv.trans g.outcomeEquiv
  initial_preserved := by
    rw [mapDist_carrierEquiv_trans]
    have hpos : 0 < totalWeight (mapDist g.stateEquiv N.initialLaw) := by
      rw [totalWeight_mapDist]
      exact N.initial_pos
    exact distEq_trans_pos (distEq_map_carrierEquiv g.stateEquiv f.initial_preserved)
      g.initial_preserved hpos
  observation_preserved := by
    intro s
    rw [mapDist_carrierEquiv_trans]
    exact distEq_trans_pos
      (distEq_map_carrierEquiv g.outcomeEquiv (f.observation_preserved s))
      (g.observation_preserved (f.stateEquiv s))
      (by rw [totalWeight_mapDist]; exact N.observation_pos (f.stateEquiv s))
  transition_preserved := by
    intro s a
    rw [mapDist_carrierEquiv_trans]
    exact distEq_trans_pos
      (distEq_map_carrierEquiv g.stateEquiv (f.transition_preserved s a))
      (g.transition_preserved (f.stateEquiv s) (f.actionEquiv a))
      (by rw [totalWeight_mapDist]; exact N.transition_pos (f.stateEquiv s) (f.actionEquiv a))

def symm (f : MarkovIso M N) : MarkovIso N M where
  stateEquiv := f.stateEquiv.symm
  actionEquiv := f.actionEquiv.symm
  outcomeEquiv := f.outcomeEquiv.symm
  initial_preserved := by
    have h := distEq_map_carrierEquiv f.stateEquiv.symm f.initial_preserved
    have hs := distEq_symm h
    change distEq (mapDist f.stateEquiv.symm N.initialLaw)
      (mapDist f.stateEquiv.symm (mapDist f.stateEquiv M.initialLaw)) at hs
    rw [mapDist_carrierEquiv_symm_cancel] at hs
    exact hs
  observation_preserved := by
    intro s
    have h := distEq_map_carrierEquiv f.outcomeEquiv.symm
      (f.observation_preserved (f.stateEquiv.symm s))
    have hs := distEq_symm h
    simp only [CarrierEquiv.symm, f.stateEquiv.right_inv,
      mapDist_invFun_cancel] at hs
    change distEq (mapDist f.outcomeEquiv.invFun (N.observation s))
      (M.observation (f.stateEquiv.invFun s))
    exact hs
  transition_preserved := by
    intro s a
    have h := distEq_map_carrierEquiv f.stateEquiv.symm
      (f.transition_preserved (f.stateEquiv.symm s) (f.actionEquiv.symm a))
    have hs := distEq_symm h
    simp only [CarrierEquiv.symm, f.stateEquiv.right_inv,
      f.actionEquiv.right_inv, mapDist_invFun_cancel] at hs
    change distEq (mapDist f.stateEquiv.invFun (N.transition s a))
      (M.transition (f.stateEquiv.invFun s) (f.actionEquiv.invFun a))
    exact hs

end MarkovIso


/-- The one-step observation channel extracted from a full representation. -/
structure ObservationKernel where
  observe : State → FinDist Outcome
  rowMass : Nat
  rowMass_pos : 0 < rowMass
  rows_have_common_mass : ∀ s, totalWeight (observe s) = rowMass

def observationPart (M : MarkovRepresentation
    (State := State) (Action := Action) (Outcome := Outcome)) :
    ObservationKernel (State := State) (Outcome := Outcome) where
  observe := M.observation
  rowMass := M.observationMass
  rowMass_pos := M.observationMass_pos
  rows_have_common_mass := M.observation_normalized

@[ext]
structure ObservationIso (O P : ObservationKernel
    (State := State) (Outcome := Outcome)) where
  stateEquiv : CarrierEquiv State State
  outcomeEquiv : CarrierEquiv Outcome Outcome
  observation_preserved : ∀ s,
    distEq (mapDist outcomeEquiv (O.observe s))
      (P.observe (stateEquiv s))

namespace ObservationIso

variable {O P Q : ObservationKernel (State := State) (Outcome := Outcome)}

def refl (O : ObservationKernel (State := State) (Outcome := Outcome)) :
    ObservationIso O O where
  stateEquiv := CarrierEquiv.refl _
  outcomeEquiv := CarrierEquiv.refl _
  observation_preserved := by
    intro s
    change distEq (mapDist (CarrierEquiv.refl Outcome) (O.observe s)) (O.observe s)
    rw [mapDist_carrierEquiv_refl]
    exact distEq_refl _

def trans (f : ObservationIso O P) (g : ObservationIso P Q) :
    ObservationIso O Q where
  stateEquiv := f.stateEquiv.trans g.stateEquiv
  outcomeEquiv := f.outcomeEquiv.trans g.outcomeEquiv
  observation_preserved := by
    intro s
    rw [mapDist_carrierEquiv_trans]
    exact distEq_trans_pos
      (distEq_map_carrierEquiv g.outcomeEquiv (f.observation_preserved s))
      (g.observation_preserved (f.stateEquiv s))
      (by rw [totalWeight_mapDist, P.rows_have_common_mass]; exact P.rowMass_pos)

def symm (f : ObservationIso O P) : ObservationIso P O where
  stateEquiv := f.stateEquiv.symm
  outcomeEquiv := f.outcomeEquiv.symm
  observation_preserved := by
    intro s
    have h := distEq_map_carrierEquiv f.outcomeEquiv.symm
      (f.observation_preserved (f.stateEquiv.symm s))
    have hs := distEq_symm h
    simp only [CarrierEquiv.symm, f.stateEquiv.right_inv,
      mapDist_invFun_cancel] at hs
    change distEq (mapDist f.outcomeEquiv.invFun (P.observe s))
      (O.observe (f.stateEquiv.invFun s))
    exact hs

end ObservationIso

def observationGroupoid : Groupoid where
  Obj := ObservationKernel (State := State) (Outcome := Outcome)
  Hom := ObservationIso
  id := ObservationIso.refl
  comp := fun f g => ObservationIso.trans f g
  inv := ObservationIso.symm
  id_comp := by
    intro O P f
    apply ObservationIso.ext <;> apply CarrierEquiv.ext <;> funext x <;>
      simp [ObservationIso.trans, ObservationIso.refl, CarrierEquiv.trans, CarrierEquiv.refl]
  comp_id := by
    intro O P f
    apply ObservationIso.ext <;> apply CarrierEquiv.ext <;> funext x <;>
      simp [ObservationIso.trans, ObservationIso.refl, CarrierEquiv.trans, CarrierEquiv.refl]
  assoc := by
    intro O P Q R f g h
    apply ObservationIso.ext <;> apply CarrierEquiv.ext <;> funext x <;>
      simp [ObservationIso.trans, CarrierEquiv.trans]
  inv_left := by
    intro O P f
    apply ObservationIso.ext <;> apply CarrierEquiv.ext <;> funext x <;>
      simp [ObservationIso.trans, ObservationIso.symm, ObservationIso.refl,
        CarrierEquiv.trans, CarrierEquiv.symm, CarrierEquiv.refl,
        f.stateEquiv.left_inv, f.stateEquiv.right_inv,
        f.outcomeEquiv.left_inv, f.outcomeEquiv.right_inv]
  inv_right := by
    intro O P f
    apply ObservationIso.ext <;> apply CarrierEquiv.ext <;> funext x <;>
      simp [ObservationIso.trans, ObservationIso.symm, ObservationIso.refl,
        CarrierEquiv.trans, CarrierEquiv.symm, CarrierEquiv.refl,
        f.stateEquiv.left_inv, f.stateEquiv.right_inv,
        f.outcomeEquiv.left_inv, f.outcomeEquiv.right_inv]

def representationGroupoid :
    Groupoid where
  Obj := MarkovRepresentation (State := State)
    (Action := Action) (Outcome := Outcome)
  Hom := MarkovIso
  id := MarkovIso.refl
  comp := fun f g => MarkovIso.trans f g
  inv := MarkovIso.symm
  id_comp := by
    intro M N f
    apply MarkovIso.ext <;> apply CarrierEquiv.ext <;> funext x <;>
      simp [MarkovIso.trans, MarkovIso.refl, CarrierEquiv.trans, CarrierEquiv.refl]
  comp_id := by
    intro M N f
    apply MarkovIso.ext <;> apply CarrierEquiv.ext <;> funext x <;>
      simp [MarkovIso.trans, MarkovIso.refl, CarrierEquiv.trans, CarrierEquiv.refl]
  assoc := by
    intro M N K L f g h
    apply MarkovIso.ext <;> apply CarrierEquiv.ext <;> funext x <;>
      simp [MarkovIso.trans, CarrierEquiv.trans]
  inv_left := by
    intro M N f
    apply MarkovIso.ext <;> apply CarrierEquiv.ext <;> funext x <;>
      simp [MarkovIso.trans, MarkovIso.symm, MarkovIso.refl,
        CarrierEquiv.trans, CarrierEquiv.symm, CarrierEquiv.refl,
        f.stateEquiv.left_inv, f.stateEquiv.right_inv,
        f.actionEquiv.left_inv, f.actionEquiv.right_inv,
        f.outcomeEquiv.left_inv, f.outcomeEquiv.right_inv]
  inv_right := by
    intro M N f
    apply MarkovIso.ext <;> apply CarrierEquiv.ext <;> funext x <;>
      simp [MarkovIso.trans, MarkovIso.symm, MarkovIso.refl,
        CarrierEquiv.trans, CarrierEquiv.symm, CarrierEquiv.refl,
        f.stateEquiv.left_inv, f.stateEquiv.right_inv,
        f.actionEquiv.left_inv, f.actionEquiv.right_inv,
        f.outcomeEquiv.left_inv, f.outcomeEquiv.right_inv]


/-- The full representation groupoid forgets transitions and action labels
    to its one-step observation-channel groupoid. -/
def observationChannelFunctor :
    GroupoidFunctor
      (representationGroupoid (State := State) (Action := Action) (Outcome := Outcome))
      (observationGroupoid (State := State) (Outcome := Outcome)) where
  obj := observationPart
  map := fun f =>
    { stateEquiv := f.stateEquiv
      outcomeEquiv := f.outcomeEquiv
      observation_preserved := f.observation_preserved }
  map_id := by
    intro M
    apply ObservationIso.ext <;> apply CarrierEquiv.ext <;> funext x <;> rfl
  map_comp := by
    intro M N P f g
    apply ObservationIso.ext <;> apply CarrierEquiv.ext <;> funext x <;> rfl

/-- Inverses are unique in every groupoid. -/
theorem groupoid_inverse_unique (G : Groupoid) {a b : G.Obj}
    (f : G.Hom a b) (x : G.Hom b a)
    (hx : G.comp x f = G.id b) :
    x = G.inv f := by
  calc
    x = G.comp x (G.id a) := (G.comp_id x).symm
    _ = G.comp x (G.comp f (G.inv f)) :=
      congrArg (fun z => G.comp x z) (G.inv_right f).symm
    _ = G.comp (G.comp x f) (G.inv f) := (G.assoc x f (G.inv f)).symm
    _ = G.comp (G.id b) (G.inv f) := congrArg (fun z => G.comp z (G.inv f)) hx
    _ = G.inv f := G.id_comp (G.inv f)

/-- Every groupoid functor preserves inverses, even though inverse preservation
    is not a separate field in the minimal functor record. -/
theorem GroupoidFunctor.map_inv (G H : Groupoid)
    (F : GroupoidFunctor G H) {a b : G.Obj} (f : G.Hom a b) :
    F.map (G.inv f) = H.inv (F.map f) := by
  apply groupoid_inverse_unique H (F.map f) (F.map (G.inv f))
  calc
    H.comp (F.map (G.inv f)) (F.map f) =
        F.map (G.comp (G.inv f) f) := (F.map_comp (G.inv f) f).symm
    _ = H.id (F.obj b) := by rw [G.inv_left, F.map_id]

/-- Isotropy kernel of a groupoid functor at an object. -/
def FunctorIsotropyKernel (G H : Groupoid)
    (F : GroupoidFunctor G H) (x : G.Obj) :=
  {g : G.Hom x x // F.map g = H.id (F.obj x)}

def kernelIdentity (G H : Groupoid)
    (F : GroupoidFunctor G H) (x : G.Obj) :
    FunctorIsotropyKernel G H F x :=
  ⟨G.id x, F.map_id x⟩

def kernelCompose (G H : Groupoid)
    (F : GroupoidFunctor G H) (x : G.Obj)
    (g h : FunctorIsotropyKernel G H F x) :
    FunctorIsotropyKernel G H F x :=
  ⟨G.comp g.1 h.1, by
    rw [F.map_comp, g.2, h.2, H.id_comp]⟩

def kernelInverse (G H : Groupoid)
    (F : GroupoidFunctor G H) (x : G.Obj)
    (g : FunctorIsotropyKernel G H F x) :
    FunctorIsotropyKernel G H F x :=
  ⟨G.inv g.1, by
    rw [GroupoidFunctor.map_inv G H F g.1, g.2]
    exact (groupoid_inverse_unique H (H.id (F.obj x))
      (H.id (F.obj x)) (by rw [H.id_comp])).symm⟩

theorem kernel_comp_closed (G H : Groupoid)
    (F : GroupoidFunctor G H) (x : G.Obj)
    (g h : FunctorIsotropyKernel G H F x) :
    (kernelCompose G H F x g h).2 =
      (by rw [F.map_comp, g.2, h.2, H.id_comp] : F.map (G.comp g.1 h.1) = H.id (F.obj x)) := rfl


/-- The isotropy kernel itself is a one-object groupoid: its loops are exactly
    the automorphisms of x that the functor sends to identity. -/
def isotropyKernelGroupoid (G H : Groupoid)
    (F : GroupoidFunctor G H) (x : G.Obj) : Groupoid where
  Obj := Unit
  Hom := fun _ _ => FunctorIsotropyKernel G H F x
  id := fun _ => kernelIdentity G H F x
  comp := fun g h => kernelCompose G H F x g h
  inv := fun g => kernelInverse G H F x g
  id_comp := by
    intro a b g
    apply Subtype.ext
    exact G.id_comp g.1
  comp_id := by
    intro a b g
    apply Subtype.ext
    exact G.comp_id g.1
  assoc := by
    intro a b c d g h k
    apply Subtype.ext
    exact G.assoc g.1 h.1 k.1
  inv_left := by
    intro a b g
    apply Subtype.ext
    exact G.inv_left g.1
  inv_right := by
    intro a b g
    apply Subtype.ext
    exact G.inv_right g.1

/-- The kernel groupoid includes into the source representation groupoid. -/
def isotropyKernelInclusion (G H : Groupoid)
    (F : GroupoidFunctor G H) (x : G.Obj) :
    GroupoidFunctor (isotropyKernelGroupoid G H F x) G where
  obj := fun _ => x
  map := fun g => g.1
  map_id := by intro a; rfl
  map_comp := by intro a b c g h; rfl

theorem kernelGroupoid_loop_is_invisible (G H : Groupoid)
    (F : GroupoidFunctor G H) (x : G.Obj)
    (g : (isotropyKernelGroupoid G H F x).Hom () ()) :
    F.map ((isotropyKernelInclusion G H F x).map g) = H.id (F.obj x) :=
  g.2

def RepresentationIsotropy (M : MarkovRepresentation
    (State := State) (Action := Action) (Outcome := Outcome)) :=
  (representationGroupoid (State := State) (Action := Action)
    (Outcome := Outcome)).Hom M M

theorem representation_loops_are_complete_automorphisms
    (M : MarkovRepresentation (State := State)
      (Action := Action) (Outcome := Outcome)) :
    RepresentationIsotropy M = MarkovIso M M := rfl

end Cerp.StochasticRepresentationGroupoid
