import CausalAnchorAdequacy
import StochasticCausalCovariance
import GroundedRelativeDensity
import GroundedModuliFiber

/-!
# Reconciled Causal Covariance & Grounded Moduli-Fiber Groupoid Bridge

Reconciles Spike 31 (`ExactCausalRepMap` covariance) with constructive
`StochasticCausalCovariance` (ZERO `Classical.choice`) and discharges the
groupoid/moduli-fiber bridge (`GroundedRelativeDensity` & `GroundedModuliFiber`):

1. Embeds `ExactCausalRepMap E E'` into `MonotoneRepMap E E' 1`, proving Spike 31's
   trace transport and profile-equivalence biconditional purely constructively
   under affordable-experiment lifting and reachable-outcome injectivity.
2. Constructs `profileKernelGroupoid E budget` and proves any constructive
   covariance map induces an explicit `GroupoidEquivalence` between profile
   kernel groupoids with `FiberContractible` homotopy fibers.
3. Connects `GroundedModuliFiber.groundedProfileGroupoid` over a causal
   profile groupoid directly to transported target profiles without `Classical.choice`.
4. Proves transitivity of `distEq` for non-degenerate Markov `FinDist`s
   (`ValidStochasticExp`) and constructs `stochasticProfileKernelGroupoid` plus
   its `GroupoidEquivalence` and fiber contractibility.
-/

namespace Cerp.CausalCovarianceGroupoidBridge

open Cerp.CausalAnchorAdequacy
open Cerp.StochasticInterventionGrounding
open Cerp.StochasticCausalCovariance
open Cerp.HigherSemanticCore
open Cerp.SemanticYoneda.GeneralCategory
open Cerp.SemanticModuliFiber
open Cerp.GroundedRelativeDensity
open Cerp.GroundedModuliFiber

universe u v w x y z t u₀ v₀ u₁ v₁ u₂ v₂

section ExactReconciled

variable {External : Type u}
variable {State : Type v} {Intervention : Type w} {Outcome : Type x}
variable {State' : Type y} {Intervention' : Type z} {Outcome' : Type t}

/-- Exact 4-law deterministic causal representation map (Spike 31 signature). -/
structure ExactCausalRepMap
    (E : CausalExperiment External State Intervention Outcome)
    (E' : CausalExperiment External State' Intervention' Outcome') where
  stateMap : State → State'
  interventionMap : Intervention → Intervention'
  outcomeMap : Outcome → Outcome'
  initial_commute : ∀ e, E'.initial e = stateMap (E.initial e)
  observe_commute : ∀ s, E'.observe (stateMap s) = outcomeMap (E.observe s)
  evolve_commute : ∀ s a,
    E'.evolve (stateMap s) (interventionMap a) = stateMap (E.evolve s a)
  cost_commute : ∀ a, E'.interventionCost (interventionMap a) = E.interventionCost a

def ExactCausalRepMap.toMonotoneRepMap
    {E : CausalExperiment External State Intervention Outcome}
    {E' : CausalExperiment External State' Intervention' Outcome'}
    (R : ExactCausalRepMap E E') :
    MonotoneRepMap E E' 1 where
  stateMap := R.stateMap
  interventionMap := R.interventionMap
  outcomeMap := R.outcomeMap
  initial_commute := R.initial_commute
  observe_commute := R.observe_commute
  evolve_commute := R.evolve_commute
  cost_le := fun a => by
    rw [R.cost_commute a, Nat.one_mul]
    exact Nat.le_refl _

theorem exact_experimentCost_transport
    {E : CausalExperiment External State Intervention Outcome}
    {E' : CausalExperiment External State' Intervention' Outcome'}
    (R : ExactCausalRepMap E E') (actions : List Intervention) :
    experimentCost E' (actions.map R.interventionMap) = experimentCost E actions := by
  induction actions with
  | nil => rfl
  | cons a rest ih => simp [experimentCost, R.cost_commute, ih]

theorem exact_experimentTrace_transport
    {E : CausalExperiment External State Intervention Outcome}
    {E' : CausalExperiment External State' Intervention' Outcome'}
    (R : ExactCausalRepMap E E') (actions : List Intervention) (state : State) :
    List.map R.outcomeMap (experimentTrace E actions state) =
      experimentTrace E' (actions.map R.interventionMap) (R.stateMap state) :=
  experimentTrace_transport_monotone R.toMonotoneRepMap actions state

theorem exact_profileEquality_preserved
    {E : CausalExperiment External State Intervention Outcome}
    {E' : CausalExperiment External State' Intervention' Outcome'}
    (R : ExactCausalRepMap E E')
    (budget : Nat) (e e' : External)
    (hprofile :
      profile (experimentChannel E) budget e =
        profile (experimentChannel E) budget e') :
    ∀ (actions : List Intervention) (hcost : experimentCost E actions ≤ budget),
      profile (experimentChannel E') budget e
          ⟨actions.map R.interventionMap,
            by
              change experimentCost E' (actions.map R.interventionMap) ≤ budget
              rw [exact_experimentCost_transport R actions]
              exact hcost⟩ =
      profile (experimentChannel E') budget e'
          ⟨actions.map R.interventionMap,
            by
              change experimentCost E' (actions.map R.interventionMap) ≤ budget
              rw [exact_experimentCost_transport R actions]
              exact hcost⟩ := by
  intro actions hcost
  simpa [Nat.one_mul, profile, experimentChannel] using
    profileEquality_preserved_scaled R.toMonotoneRepMap budget e e' hprofile actions hcost

theorem exact_profileEquality_reflected_constructive
    {E : CausalExperiment External State Intervention Outcome}
    {E' : CausalExperiment External State' Intervention' Outcome'}
    (R : ExactCausalRepMap E E')
    (budget : Nat) (e e' : External)
    (hinjReach : ∀ x y,
      ReachableOutcome E e x → ReachableOutcome E e' y →
      R.outcomeMap x = R.outcomeMap y → x = y)
    (hprofile' :
      profile (experimentChannel E') budget e =
        profile (experimentChannel E') budget e') :
    profile (experimentChannel E) budget e =
      profile (experimentChannel E) budget e' :=
  profileEquality_reflected_reachable R.toMonotoneRepMap budget e e' hinjReach hprofile'

/-- Choice-free reconciliation of Spike 31's observational equivalence theorem:
    requires only affordable action lifting (or `∀ a', ∃ a, g a = a'`) and
    reachable outcome injectivity, using ZERO `Classical.choice`. -/
theorem exact_profileEquality_iff_constructive
    {E : CausalExperiment External State Intervention Outcome}
    {E' : CausalExperiment External State' Intervention' Outcome'}
    (R : ExactCausalRepMap E E')
    (budget : Nat) (e e' : External)
    (haffSurj : ∀ a', E'.interventionCost a' ≤ budget →
      ∃ a, R.interventionMap a = a')
    (hinjReach : ∀ x y,
      ReachableOutcome E e x → ReachableOutcome E e' y →
      R.outcomeMap x = R.outcomeMap y → x = y) :
    (profile (experimentChannel E) budget e =
      profile (experimentChannel E) budget e') ↔
    (profile (experimentChannel E') budget e =
      profile (experimentChannel E') budget e') := by
  refine profileEquality_iff_constructive_affordable R.toMonotoneRepMap budget e e' ?_ hinjReach
  intro a' hcost'
  obtain ⟨a, ha⟩ := haffSurj a' hcost'
  refine ⟨a, ha, ?_⟩
  change E.interventionCost a ≤ E'.interventionCost a'
  rw [← R.cost_commute a, ha]
  exact Nat.le_refl _

end ExactReconciled

section GroupoidCombinators

def groupoidFunctorComp
    {G : Groupoid.{u₀, v₀}} {H : Groupoid.{u₁, v₁}} {K : Groupoid.{u₂, v₂}}
    (F₁ : GroupoidFunctor G H) (F₂ : GroupoidFunctor H K) :
    GroupoidFunctor G K where
  obj := fun x => F₂.obj (F₁.obj x)
  map := fun f => F₂.map (F₁.map f)
  map_id := fun a => by dsimp only []; rw [F₁.map_id, F₂.map_id]
  map_comp := fun f g => by dsimp only []; rw [F₁.map_comp, F₂.map_comp]

/-- General choice-free composition of groupoid equivalences `G ≃ H` and `H ≃ K`. -/
def groupoidEquivalenceComp
    {G : Groupoid.{u₀, v₀}} {H : Groupoid.{u₁, v₁}} {K : Groupoid.{u₂, v₂}}
    (E₁ : GroupoidEquivalence G H) (E₂ : GroupoidEquivalence H K) :
    GroupoidEquivalence G K where
  functor := groupoidFunctorComp E₁.functor E₂.functor
  homEquiv := fun a b =>
    { toFun := fun f =>
        (E₂.homEquiv (E₁.functor.obj a) (E₁.functor.obj b)).toFun
          ((E₁.homEquiv a b).toFun f)
      invFun := fun k =>
        (E₁.homEquiv a b).invFun
          ((E₂.homEquiv (E₁.functor.obj a) (E₁.functor.obj b)).invFun k)
      left_inv := fun f => by
        dsimp only []
        rw [(E₂.homEquiv (E₁.functor.obj a) (E₁.functor.obj b)).left_inv,
            (E₁.homEquiv a b).left_inv]
      right_inv := fun k => by
        dsimp only []
        rw [(E₁.homEquiv a b).right_inv,
            (E₂.homEquiv (E₁.functor.obj a) (E₁.functor.obj b)).right_inv] }
  homEquiv_map := fun {a b} f => by
    dsimp only [groupoidFunctorComp]
    rw [E₁.homEquiv_map, E₂.homEquiv_map]
  essentiallySurjective := fun z => by
    obtain ⟨y, ⟨g⟩⟩ := E₂.essentiallySurjective z
    obtain ⟨x, ⟨f⟩⟩ := E₁.essentiallySurjective y
    exact ⟨x, ⟨K.comp (E₂.functor.map f) g⟩⟩

end GroupoidCombinators

section CausalGroupoidBridge

variable {External : Type u}
variable {State : Type v} {Intervention : Type w} {Outcome : Type x}
variable {State' : Type y} {Intervention' : Type z} {Outcome' : Type t}

/-- Budget-bounded observational equivalence groupoid of a deterministic causal experiment. -/
def profileKernelGroupoid
    (E : CausalExperiment External State Intervention Outcome)
    (budget : Nat) : Groupoid.{u, 0} where
  Obj := External
  Hom := fun e e' => PLift (profile (experimentChannel E) budget e = profile (experimentChannel E) budget e')
  id := fun _ => ⟨rfl⟩
  comp := fun p q => ⟨p.down.trans q.down⟩
  inv := fun p => ⟨p.down.symm⟩
  id_comp := fun f => by cases f; rfl
  comp_id := fun f => by cases f; rfl
  assoc := fun f g h => by cases f; cases g; cases h; rfl
  inv_left := fun f => by cases f; rfl
  inv_right := fun f => by cases f; rfl

def representationGroupoidFunctor
    {E : CausalExperiment External State Intervention Outcome}
    {E' : CausalExperiment External State' Intervention' Outcome'}
    (R : MonotoneRepMap E E' 1)
    (budget : Nat)
    (haffSurj : ∀ a', E'.interventionCost a' ≤ budget →
      ∃ a, R.interventionMap a = a' ∧ E.interventionCost a ≤ E'.interventionCost a')
    (hinjGlobal : ∀ e e' x y,
      ReachableOutcome E e x → ReachableOutcome E e' y →
      R.outcomeMap x = R.outcomeMap y → x = y) :
    GroupoidFunctor (profileKernelGroupoid E budget) (profileKernelGroupoid E' budget) where
  obj := fun e => e
  map := fun {e e'} p =>
    ⟨(profileEquality_iff_constructive_affordable R budget e e' haffSurj
        (hinjGlobal e e')).mp p.down⟩
  map_id := fun _ => rfl
  map_comp := fun _ _ => rfl

/-- Constructive representation covariance induces an explicit `GroupoidEquivalence`
    between source and target profile kernel groupoids (ZERO `Classical.choice`). -/
def representation_induces_profileGroupoidEquivalence
    {E : CausalExperiment External State Intervention Outcome}
    {E' : CausalExperiment External State' Intervention' Outcome'}
    (R : MonotoneRepMap E E' 1)
    (budget : Nat)
    (haffSurj : ∀ a', E'.interventionCost a' ≤ budget →
      ∃ a, R.interventionMap a = a' ∧ E.interventionCost a ≤ E'.interventionCost a')
    (hinjGlobal : ∀ e e' x y,
      ReachableOutcome E e x → ReachableOutcome E e' y →
      R.outcomeMap x = R.outcomeMap y → x = y) :
    GroupoidEquivalence (profileKernelGroupoid E budget) (profileKernelGroupoid E' budget) where
  functor := representationGroupoidFunctor R budget haffSurj hinjGlobal
  homEquiv := fun e e' =>
    { toFun := fun p =>
        ⟨(profileEquality_iff_constructive_affordable R budget e e' haffSurj
            (hinjGlobal e e')).mp p.down⟩
      invFun := fun q =>
        ⟨(profileEquality_iff_constructive_affordable R budget e e' haffSurj
            (hinjGlobal e e')).mpr q.down⟩
      left_inv := fun p => by cases p; rfl
      right_inv := fun q => by cases q; rfl }
  homEquiv_map := fun _ => rfl
  essentiallySurjective := fun e => ⟨e, ⟨⟨rfl⟩⟩⟩

theorem representation_preserves_contractible_fibers
    {E : CausalExperiment External State Intervention Outcome}
    {E' : CausalExperiment External State' Intervention' Outcome'}
    (R : MonotoneRepMap E E' 1)
    (budget : Nat)
    (haffSurj : ∀ a', E'.interventionCost a' ≤ budget →
      ∃ a, R.interventionMap a = a' ∧ E.interventionCost a ≤ E'.interventionCost a')
    (hinjGlobal : ∀ e e' x y,
      ReachableOutcome E e x → ReachableOutcome E e' y →
      R.outcomeMap x = R.outcomeMap y → x = y)
    (e' : External) :
    FiberContractible
      (representation_induces_profileGroupoidEquivalence R budget haffSurj hinjGlobal) e' :=
  equivalence_has_contractible_fibers _ e'

/-- Transports an arbitrary external groupoid equivalence into `profileKernelGroupoid E budget`
    across a covariance map into `profileKernelGroupoid E' budget`. -/
def groundedProfileGroupoid_transport_equivalence
    {G : Groupoid.{u₀, v₀}}
    {E : CausalExperiment External State Intervention Outcome}
    {E' : CausalExperiment External State' Intervention' Outcome'}
    (R : MonotoneRepMap E E' 1)
    (budget : Nat)
    (eqvG : GroupoidEquivalence G (profileKernelGroupoid E budget))
    (haffSurj : ∀ a', E'.interventionCost a' ≤ budget →
      ∃ a, R.interventionMap a = a' ∧ E.interventionCost a ≤ E'.interventionCost a')
    (hinjGlobal : ∀ e e' x y,
      ReachableOutcome E e x → ReachableOutcome E e' y →
      R.outcomeMap x = R.outcomeMap y → x = y) :
    GroupoidEquivalence G (profileKernelGroupoid E' budget) :=
  groupoidEquivalenceComp eqvG
    (representation_induces_profileGroupoidEquivalence R budget haffSurj hinjGlobal)

theorem groundedProfileGroupoid_transport_fibers_contractible
    {G : Groupoid.{u₀, v₀}}
    {E : CausalExperiment External State Intervention Outcome}
    {E' : CausalExperiment External State' Intervention' Outcome'}
    (R : MonotoneRepMap E E' 1)
    (budget : Nat)
    (eqvG : GroupoidEquivalence G (profileKernelGroupoid E budget))
    (haffSurj : ∀ a', E'.interventionCost a' ≤ budget →
      ∃ a, R.interventionMap a = a' ∧ E.interventionCost a ≤ E'.interventionCost a')
    (hinjGlobal : ∀ e e' x y,
      ReachableOutcome E e x → ReachableOutcome E e' y →
      R.outcomeMap x = R.outcomeMap y → x = y)
    (e' : External) :
    FiberContractible
      (groundedProfileGroupoid_transport_equivalence R budget eqvG haffSurj hinjGlobal) e' :=
  equivalence_has_contractible_fibers _ e'

def groundedModuliToTransportedFunctor
    (E : CausalExperiment External State Intervention Outcome)
    (E' : CausalExperiment External State' Intervention' Outcome')
    (R : MonotoneRepMap E E' 1)
    (budget : Nat)
    (haffSurj : ∀ a', E'.interventionCost a' ≤ budget →
      ∃ a, R.interventionMap a = a' ∧ E.interventionCost a ≤ E'.interventionCost a')
    (hinjGlobal : ∀ e e' x y,
      ReachableOutcome E e x → ReachableOutcome E e' y →
      R.outcomeMap x = R.outcomeMap y → x = y)
    (C : SemCategory)
    (RF : SemFunctor (asSemCategory (profileKernelGroupoid E budget)) C)
    (P : ProbeFamily C)
    (FF : FullyFaithfulRealization (asSemCategory (profileKernelGroupoid E budget)) C RF)
    (D : RelativeProbeDensity (asSemCategory (profileKernelGroupoid E budget)) C RF P) :
    GroupoidFunctor
      (groundedProfileGroupoid (profileKernelGroupoid E budget) C RF P FF D)
      (profileKernelGroupoid E' budget) :=
  let eqSource := groundedProfileEquivalence (profileKernelGroupoid E budget) C RF P FF D
  let eqTarget := representation_induces_profileGroupoidEquivalence R budget haffSurj hinjGlobal
  { obj := fun e => e
    map := fun {a b} eta =>
      eqTarget.functor.map ((eqSource.homEquiv a b).invFun eta)
    map_id := fun a => by
      have hid :
          (eqSource.homEquiv a a).invFun
            ((groundedProfileGroupoid (profileKernelGroupoid E budget) C RF P FF D).id a) =
          (profileKernelGroupoid E budget).id a := by
        change profileRecover (profileKernelGroupoid E budget) C RF P FF D
            (profileIdentity (profileKernelGroupoid E budget) C RF P a) =
          (profileKernelGroupoid E budget).id a
        exact profileRecover_identity (profileKernelGroupoid E budget) C RF P FF D a
      dsimp only []
      rw [hid, eqTarget.functor.map_id]
      rfl
    map_comp := fun {a b c} eta theta => by
      have hcomp :
          (eqSource.homEquiv a c).invFun
            ((groundedProfileGroupoid (profileKernelGroupoid E budget) C RF P FF D).comp eta theta) =
          (profileKernelGroupoid E budget).comp
            ((eqSource.homEquiv a b).invFun eta)
            ((eqSource.homEquiv b c).invFun theta) := by
        change profileRecover (profileKernelGroupoid E budget) C RF P FF D
            (profileCompose (profileKernelGroupoid E budget) C RF P FF D eta theta) =
          (profileKernelGroupoid E budget).comp
            (profileRecover (profileKernelGroupoid E budget) C RF P FF D eta)
            (profileRecover (profileKernelGroupoid E budget) C RF P FF D theta)
        exact profileRecover_compose (profileKernelGroupoid E budget) C RF P FF D eta theta
      dsimp only []
      rw [hcomp, eqTarget.functor.map_comp] }

/-- Direct choice-free bridge from `GroundedModuliFiber.groundedProfileGroupoid` over a
    causal profile groupoid into the covariantly transported target profile groupoid. -/
def groundedModuliToTransportedProfileEquiv
    (E : CausalExperiment External State Intervention Outcome)
    (E' : CausalExperiment External State' Intervention' Outcome')
    (R : MonotoneRepMap E E' 1)
    (budget : Nat)
    (haffSurj : ∀ a', E'.interventionCost a' ≤ budget →
      ∃ a, R.interventionMap a = a' ∧ E.interventionCost a ≤ E'.interventionCost a')
    (hinjGlobal : ∀ e e' x y,
      ReachableOutcome E e x → ReachableOutcome E e' y →
      R.outcomeMap x = R.outcomeMap y → x = y)
    (C : SemCategory)
    (RF : SemFunctor (asSemCategory (profileKernelGroupoid E budget)) C)
    (P : ProbeFamily C)
    (FF : FullyFaithfulRealization (asSemCategory (profileKernelGroupoid E budget)) C RF)
    (D : RelativeProbeDensity (asSemCategory (profileKernelGroupoid E budget)) C RF P) :
    GroupoidEquivalence
      (groundedProfileGroupoid (profileKernelGroupoid E budget) C RF P FF D)
      (profileKernelGroupoid E' budget) :=
  let eqSource := groundedProfileEquivalence (profileKernelGroupoid E budget) C RF P FF D
  let eqTarget := representation_induces_profileGroupoidEquivalence R budget haffSurj hinjGlobal
  { functor := groundedModuliToTransportedFunctor E E' R budget haffSurj hinjGlobal C RF P FF D
    homEquiv := fun a b =>
      { toFun := fun eta =>
          (eqTarget.homEquiv a b).toFun ((eqSource.homEquiv a b).invFun eta)
        invFun := fun q =>
          (eqSource.homEquiv a b).toFun ((eqTarget.homEquiv a b).invFun q)
        left_inv := fun eta => by
          dsimp only []
          rw [(eqTarget.homEquiv a b).left_inv, (eqSource.homEquiv a b).right_inv]
        right_inv := fun q => by
          dsimp only []
          rw [(eqSource.homEquiv a b).left_inv, (eqTarget.homEquiv a b).right_inv] }
    homEquiv_map := fun {a b} eta => by
      dsimp only [groundedModuliToTransportedFunctor]
      exact eqTarget.homEquiv_map ((eqSource.homEquiv a b).invFun eta)
    essentiallySurjective := fun e' => ⟨e', ⟨⟨rfl⟩⟩⟩ }

theorem groundedModuliToTransportedProfile_fiber_contractible
    (E : CausalExperiment External State Intervention Outcome)
    (E' : CausalExperiment External State' Intervention' Outcome')
    (R : MonotoneRepMap E E' 1)
    (budget : Nat)
    (haffSurj : ∀ a', E'.interventionCost a' ≤ budget →
      ∃ a, R.interventionMap a = a' ∧ E.interventionCost a ≤ E'.interventionCost a')
    (hinjGlobal : ∀ e e' x y,
      ReachableOutcome E e x → ReachableOutcome E e' y →
      R.outcomeMap x = R.outcomeMap y → x = y)
    (C : SemCategory)
    (RF : SemFunctor (asSemCategory (profileKernelGroupoid E budget)) C)
    (P : ProbeFamily C)
    (FF : FullyFaithfulRealization (asSemCategory (profileKernelGroupoid E budget)) C RF)
    (D : RelativeProbeDensity (asSemCategory (profileKernelGroupoid E budget)) C RF P)
    (e' : External) :
    FiberContractible
      (groundedModuliToTransportedProfileEquiv E E' R budget haffSurj hinjGlobal C RF P FF D) e' :=
  equivalence_has_contractible_fibers _ e'

/-- Non-degeneracy of a finite stochastic causal experiment: every kernel puts
    strictly positive total weight on its support (no empty zero-weight distributions). -/
structure ValidStochasticExp
    (E : StochasticCausalExperiment External State Intervention Outcome) : Prop where
  initial_pos : ∀ e, 0 < totalWeight (E.initial e)
  observe_pos : ∀ s, 0 < totalWeight (E.observe s)
  evolve_pos : ∀ s a, 0 < totalWeight (E.evolve s a)

theorem stochasticTrace_totalWeight_pos
    {E : StochasticCausalExperiment External State Intervention Outcome}
    (hval : ValidStochasticExp E)
    (actions : List Intervention) (d : FinDist State) (hd : 0 < totalWeight d) :
    0 < totalWeight (stochasticTrace E actions d) := by
  induction actions generalizing d with
  | nil =>
      refine totalWeight_bindDist_pos d _ hd ?_
      intro s
      simpa [stochasticTrace, totalWeight_mapDist] using hval.observe_pos s
  | cons a rest ih =>
      refine totalWeight_bindDist_pos d _ hd ?_
      intro s
      refine totalWeight_bindDist_pos (E.observe s) (fun _ =>
        bindDist (E.evolve s a) (fun s' =>
          mapDist _ (stochasticTrace E rest (dirac s')))) (hval.observe_pos s) ?_
      intro o
      refine totalWeight_bindDist_pos (E.evolve s a) _ (hval.evolve_pos s a) ?_
      intro s'
      rw [totalWeight_mapDist]
      exact ih (dirac s') (by simp [totalWeight_dirac])

theorem distEq_trans_of_pos {α : Type u} [DecidableEq α]
    {d₁ d₂ d₃ : FinDist α} (hpos₂ : 0 < totalWeight d₂)
    (h₁₂ : distEq d₁ d₂) (h₂₃ : distEq d₂ d₃) :
    distEq d₁ d₃ := by
  intro a
  have h12a := h₁₂ a
  have h23a := h₂₃ a
  have hmul :
      (weightOf a d₁ * totalWeight d₃) * totalWeight d₂ =
        (weightOf a d₃ * totalWeight d₁) * totalWeight d₂ := by
    calc
      (weightOf a d₁ * totalWeight d₃) * totalWeight d₂
          = (weightOf a d₁ * totalWeight d₂) * totalWeight d₃ := by
            ac_rfl
      _ = (weightOf a d₂ * totalWeight d₁) * totalWeight d₃ := by
            rw [h12a]
      _ = (weightOf a d₂ * totalWeight d₃) * totalWeight d₁ := by
            ac_rfl
      _ = (weightOf a d₃ * totalWeight d₂) * totalWeight d₁ := by
            rw [h23a]
      _ = (weightOf a d₃ * totalWeight d₁) * totalWeight d₂ := by
            ac_rfl
  exact Nat.eq_of_mul_eq_mul_right hpos₂ hmul

theorem validStochasticExp_target
    {E : StochasticCausalExperiment External State Intervention Outcome}
    {E' : StochasticCausalExperiment External State' Intervention' Outcome'}
    (R : StochasticRepMap E E') (hval : ValidStochasticExp E)
    (hsSurj : ∀ s', ∃ s, R.stateMap s = s')
    (haSurj : ∀ a', ∃ a, R.interventionMap a = a') :
    ValidStochasticExp E' where
  initial_pos := fun e => by
    rw [R.initial_commute e, totalWeight_mapDist]
    exact hval.initial_pos e
  observe_pos := fun s' => by
    obtain ⟨s, rfl⟩ := hsSurj s'
    rw [R.observe_commute s, totalWeight_mapDist]
    exact hval.observe_pos s
  evolve_pos := fun s' a' => by
    obtain ⟨s, rfl⟩ := hsSurj s'
    obtain ⟨a, rfl⟩ := haSurj a'
    rw [R.evolve_commute s a, totalWeight_mapDist]
    exact hval.evolve_pos s a

/-- Stochastic observational-equivalence groupoid for valid non-degenerate
    finite Markov-kernel experiments. -/
def stochasticProfileKernelGroupoid
    (E : StochasticCausalExperiment External State Intervention Outcome)
    [DecidableEq Outcome] (hval : ValidStochasticExp E) (budget : Nat) : Groupoid.{u, 0} where
  Obj := External
  Hom := fun e e' => PLift (StochasticObsEqual E budget e e')
  id := fun _ => ⟨fun _ _ _ => rfl⟩
  comp := fun {e₁ e₂ e₃} p q => ⟨fun actions hcost =>
    distEq_trans_of_pos (stochasticTrace_totalWeight_pos hval actions (E.initial e₂) (hval.initial_pos e₂))
      (p.down actions hcost) (q.down actions hcost)⟩
  inv := fun p => ⟨fun actions hcost o => (p.down actions hcost o).symm⟩
  id_comp := fun f => by cases f; rfl
  comp_id := fun f => by cases f; rfl
  assoc := fun f g h => by cases f; cases g; cases h; rfl
  inv_left := fun f => by cases f; rfl
  inv_right := fun f => by cases f; rfl

/-- Finite Markov-kernel representation covariance induces an explicit `GroupoidEquivalence`
    between valid stochastic profile groupoids without `Classical.choice`. -/
def stochastic_induces_profileGroupoidEquivalence
    {E : StochasticCausalExperiment External State Intervention Outcome}
    {E' : StochasticCausalExperiment External State' Intervention' Outcome'}
    [DecidableEq Outcome] [DecidableEq Outcome']
    (hval : ValidStochasticExp E) (hval' : ValidStochasticExp E')
    (R : StochasticRepMap E E') (budget : Nat)
    (haffSurj : ∀ a', E'.interventionCost a' ≤ budget →
      ∃ a, R.interventionMap a = a')
    (hinj : ∀ x y, R.outcomeMap x = R.outcomeMap y → x = y) :
    GroupoidEquivalence
      (stochasticProfileKernelGroupoid E hval budget)
      (stochasticProfileKernelGroupoid E' hval' budget) where
  functor :=
    { obj := fun e => e
      map := fun {e e'} p =>
        ⟨(stochasticProfile_iff_constructive R budget e e' haffSurj hinj).mp p.down⟩
      map_id := fun _ => rfl
      map_comp := fun _ _ => rfl }
  homEquiv := fun e e' =>
    { toFun := fun p =>
        ⟨(stochasticProfile_iff_constructive R budget e e' haffSurj hinj).mp p.down⟩
      invFun := fun q =>
        ⟨(stochasticProfile_iff_constructive R budget e e' haffSurj hinj).mpr q.down⟩
      left_inv := fun p => by cases p; rfl
      right_inv := fun q => by cases q; rfl }
  homEquiv_map := fun _ => rfl
  essentiallySurjective := fun e => ⟨e, ⟨⟨fun _ _ _ => rfl⟩⟩⟩

theorem stochastic_preserves_contractible_fibers
    {E : StochasticCausalExperiment External State Intervention Outcome}
    {E' : StochasticCausalExperiment External State' Intervention' Outcome'}
    [DecidableEq Outcome] [DecidableEq Outcome']
    (hval : ValidStochasticExp E) (hval' : ValidStochasticExp E')
    (R : StochasticRepMap E E') (budget : Nat)
    (haffSurj : ∀ a', E'.interventionCost a' ≤ budget →
      ∃ a, R.interventionMap a = a')
    (hinj : ∀ x y, R.outcomeMap x = R.outcomeMap y → x = y)
    (e' : External) :
    FiberContractible
      (stochastic_induces_profileGroupoidEquivalence hval hval' R budget haffSurj hinj) e' :=
  equivalence_has_contractible_fibers _ e'

end CausalGroupoidBridge

end Cerp.CausalCovarianceGroupoidBridge
