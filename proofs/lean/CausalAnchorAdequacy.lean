import Lean

/-!
# Causal anchor adequacy by independent channel fusion

Two independently specified causal measurement channels observe a common
external state. Their joint profile is the product of their response
profiles. The central criterion is exact: the joint channel identifies
external states iff the intersection of the two observational kernels is
the diagonal. The finite model exhibits complementary blindness.
-/

namespace Cerp.CausalAnchorAdequacy

universe u v w x y z

structure CausalChannel (External : Type u) (Probe : Type v)
    (Outcome : Type w) where
  cost : Probe -> Nat
  response : External -> Probe -> Outcome

abbrev Affordable (C : CausalChannel External Probe Outcome) (budget : Nat) :=
  {p : Probe // C.cost p <= budget}

def profile (C : CausalChannel External Probe Outcome) (budget : Nat)
    (external : External) : Affordable C budget -> Outcome :=
  fun p => C.response external p.1

def ObservationallyEqual (C : CausalChannel External Probe Outcome)
    (budget : Nat) (e e' : External) : Prop :=
  profile C budget e = profile C budget e'

def JointProfile
    (A : CausalChannel External Probe Outcome)
    (B : CausalChannel External Probe' Outcome')
    (budgetA budgetB : Nat) (external : External) :=
  (profile A budgetA external, profile B budgetB external)

def JointlyObservable
    (A : CausalChannel External Probe Outcome)
    (B : CausalChannel External Probe' Outcome')
    (budgetA budgetB : Nat) : Prop :=
  forall e e', JointProfile A B budgetA budgetB e =
    JointProfile A B budgetA budgetB e' -> e = e'

theorem joint_profile_eq_iff
    (A : CausalChannel External Probe Outcome)
    (B : CausalChannel External Probe' Outcome')
    (budgetA budgetB : Nat) (e e' : External) :
    JointProfile A B budgetA budgetB e =
      JointProfile A B budgetA budgetB e' ↔
      ObservationallyEqual A budgetA e e' ∧
      ObservationallyEqual B budgetB e e' := by
  simp [JointProfile, ObservationallyEqual]

/-- Exact causal-anchor adequacy: the two channels jointly identify the
    external domain iff no distinct pair is invisible to both. -/
theorem joint_identification_iff_kernel_intersection_trivial
    (A : CausalChannel External Probe Outcome)
    (B : CausalChannel External Probe' Outcome')
    (budgetA budgetB : Nat) :
    JointlyObservable A B budgetA budgetB ↔
      forall e e', ObservationallyEqual A budgetA e e' ->
        ObservationallyEqual B budgetB e e' -> e = e' := by
  constructor
  · intro hinj e e' hA hB
    apply hinj
    exact (joint_profile_eq_iff A B budgetA budgetB e e').2 ⟨hA,hB⟩
  · intro h e e' hjoint
    apply h
    · exact (joint_profile_eq_iff A B budgetA budgetB e e').1 hjoint |>.1
    · exact (joint_profile_eq_iff A B budgetA budgetB e e').1 hjoint |>.2

/-- Any channel computed as a deterministic post-processing of another
    channel's complete profile is observationally redundant. -/
theorem derived_channel_cannot_refine_kernel
    (A : CausalChannel External Probe Outcome)
    (budgetA : Nat) (Derived : Type z)
    (decode : (Affordable A budgetA -> Outcome) -> Derived)
    (e e' : External)
    (hA : ObservationallyEqual A budgetA e e') :
    decode (profile A budgetA e) = decode (profile A budgetA e') :=
  congrArg decode hA

/-- Two independent sensors on a two-bit external state. Each sensor sees
    only one coordinate; together they recover the entire state. -/
def firstCoordinate : CausalChannel (Bool × Bool) Bool Bool where
  cost := fun p => if p then 1 else 0
  response := fun e p => if p then e.1 else false

def secondCoordinate : CausalChannel (Bool × Bool) Bool Bool where
  cost := fun p => if p then 1 else 0
  response := fun e p => if p then e.2 else false

theorem first_channel_blind_to_second_coordinate (budget : Nat) :
    ObservationallyEqual firstCoordinate budget (false,false) (false,true) := by
  funext p
  cases p.1 <;> rfl

theorem second_channel_blind_to_first_coordinate (budget : Nat) :
    ObservationallyEqual secondCoordinate budget (false,false) (true,false) := by
  funext p
  cases p.1 <;> rfl

theorem complementary_channels_jointly_identify_at_one :
    JointlyObservable firstCoordinate secondCoordinate 1 1 := by
  intro e e' h
  have hAprof : profile firstCoordinate 1 e = profile firstCoordinate 1 e' :=
    congrArg Prod.fst h
  have hBprof : profile secondCoordinate 1 e = profile secondCoordinate 1 e' :=
    congrArg Prod.snd h
  have hA : e.1 = e'.1 := by
    have := congrFun hAprof ⟨true, by decide⟩
    exact this
  have hB : e.2 = e'.2 := by
    have := congrFun hBprof ⟨true, by decide⟩
    exact this
  exact Prod.ext hA hB

theorem complementary_channels_jointly_identify_iff :
    forall e e' : Bool × Bool,
      ObservationallyEqual firstCoordinate 1 e e' ->
      ObservationallyEqual secondCoordinate 1 e e' ->
      e = e' :=
  (joint_identification_iff_kernel_intersection_trivial
    firstCoordinate secondCoordinate 1 1).1
    complementary_channels_jointly_identify_at_one

end Cerp.CausalAnchorAdequacy


namespace Cerp.CausalAnchorAdequacy

universe u v w x
variable {External : Type u} {State : Type v} {Intervention : Type w} {Outcome : Type x}

/-! ## Causal intervention realization

A causal channel is now instantiated by an explicit dynamical experiment:
an external state is loaded into an apparatus, interventions change its
state, and a trace records observations before and after each intervention.
The response map is generated by this transition semantics rather than
stipulated independently for each probe.
-/

structure CausalExperiment (External : Type u) (State : Type v)
    (Intervention : Type w) (Outcome : Type x) where
  initial : External -> State
  observe : State -> Outcome
  evolve : State -> Intervention -> State
  interventionCost : Intervention -> Nat

def experimentCost (E : CausalExperiment External State Intervention Outcome)
    : List Intervention -> Nat
  | [] => 0
  | a :: rest => E.interventionCost a + experimentCost E rest

def experimentTrace (E : CausalExperiment External State Intervention Outcome)
    : List Intervention -> State -> List Outcome
  | [], state => [E.observe state]
  | a :: rest, state =>
      E.observe state :: experimentTrace E rest (E.evolve state a)

def experimentChannel (E : CausalExperiment External State Intervention Outcome) :
    CausalChannel External (List Intervention) (List Outcome) where
  cost := experimentCost E
  response := fun external actions =>
    experimentTrace E actions (E.initial external)

def CausallyIdentifies
    (E : CausalExperiment External State Intervention Outcome)
    (budget : Nat) : Prop :=
  forall e e', profile (experimentChannel E) budget e =
    profile (experimentChannel E) budget e' -> e = e'

/-- A measurement apparatus initially reads the first coordinate. One
    intervention changes its observation phase, exposing the second. -/
def twoStageMeasurement : CausalExperiment (Bool × Bool)
    ((Bool × Bool) × Bool) Unit Bool where
  initial := fun external => (external, false)
  observe := fun state => if state.2 then state.1.2 else state.1.1
  evolve := fun state _ => (state.1, true)
  interventionCost := fun _ => 1

theorem twoStageMeasurement_not_identifying_at_zero :
    ¬ CausallyIdentifies twoStageMeasurement 0 := by
  intro h
  have hprofile :
      profile (experimentChannel twoStageMeasurement) 0 (false,false) =
      profile (experimentChannel twoStageMeasurement) 0 (false,true) := by
    funext p
    rcases p with ⟨actions, hcost⟩
    cases actions with
    | nil =>
        simp [experimentChannel, profile, experimentTrace, twoStageMeasurement]
    | cons a rest =>
        have hf : False := by
          have hle : 1 ≤ 1 + experimentCost twoStageMeasurement rest :=
            Nat.le_add_right 1 (experimentCost twoStageMeasurement rest)
          change 1 + experimentCost twoStageMeasurement rest ≤ 0 at hcost
          have hle0 : 1 ≤ 0 := Nat.le_trans hle hcost
          exact Nat.lt_irrefl 0 (Nat.lt_of_lt_of_le (Nat.zero_lt_succ 0) hle0)
        exact False.elim hf
  exact (by decide : (false,false) ≠ (false,true))
    (h (false,false) (false,true) hprofile)

theorem twoStageMeasurement_identifies_at_one :
    CausallyIdentifies twoStageMeasurement 1 := by
  intro e e' h
  have hfirst := congrFun h ⟨[], by decide⟩
  have hsecond := congrFun h ⟨[()], by decide⟩
  have hA : e.1 = e'.1 := by
    simpa [experimentChannel, profile, experimentCost,
      experimentTrace, twoStageMeasurement] using hfirst
  have hboth : e.1 = e'.1 ∧ e.2 = e'.2 := by
    simpa [experimentChannel, profile, experimentCost,
      experimentTrace, twoStageMeasurement] using hsecond
  exact Prod.ext hA hboth.2

#print axioms twoStageMeasurement_identifies_at_one

end Cerp.CausalAnchorAdequacy
