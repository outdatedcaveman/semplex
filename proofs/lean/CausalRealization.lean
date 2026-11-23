import ResponseQuotient
import ObservableCongruence
import ResourceRelativeProbes
import BeliefStateHankel

/-!
Causal-realization bridge.
Connects response quotients, resource-indexed probes, and predictive states.
Physical grounding requires instantiating tests and costs from real dynamics.
-/

namespace Cerp.CausalRealization

universe u v w x

structure TestFamily (History : Type u) (Test : Type v) (Outcome : Type w) where
  cost : Test -> Nat
  response : History -> Test -> Outcome

variable {History : Type u} {Test : Type v} {Outcome : Type w}

abbrev Affordable (F : TestFamily History Test Outcome) (b : Nat) :=
  {t : Test // F.cost t <= b}

def profile (F : TestFamily History Test Outcome) (b : Nat)
    (h : History) : Affordable F b -> Outcome :=
  fun t => F.response h t.1

def equivalent (F : TestFamily History Test Outcome) (b : Nat)
    (h h' : History) : Prop :=
  forall t : Affordable F b, F.response h t.1 = F.response h' t.1

theorem equivalent_equivalence (F : TestFamily History Test Outcome) (b : Nat) :
    Equivalence (equivalent F b) := by
  refine { refl := ?_, symm := ?_, trans := ?_ }
  case refine_1 =>
    intro h t
    rfl
  case refine_2 =>
    intro h h' hh t
    exact (hh t).symm
  case refine_3 =>
    intro h h' h'' hh hh' t
    exact (hh t).trans (hh' t)

theorem equivalent_antitone (F : TestFamily History Test Outcome)
    {b1 b2 : Nat} (hle : b1 <= b2) {h h' : History}
    (hh : equivalent F b2 h h') :
    equivalent F b1 h h' := by
  intro t
  exact hh ⟨t.1, Nat.le_trans t.2 hle⟩

def budgetSetoid (F : TestFamily History Test Outcome) (b : Nat) :
    Setoid History where
  r := equivalent F b
  iseqv := equivalent_equivalence F b

def semanticState (F : TestFamily History Test Outcome) (b : Nat) (h : History) :
    Quotient (budgetSetoid F b) :=
  Quotient.mk (budgetSetoid F b) h

def forgetBudget (F : TestFamily History Test Outcome) {b1 b2 : Nat}
    (hle : b1 <= b2) :
    Quotient (budgetSetoid F b2) -> Quotient (budgetSetoid F b1) :=
  Quotient.lift
    (fun h => semanticState F b1 h)
    (by
      intro h h' hh
      exact Quotient.sound (equivalent_antitone F hle hh))

@[simp] theorem forgetBudget_mk (F : TestFamily History Test Outcome)
    {b1 b2 : Nat} (hle : b1 <= b2) (h : History) :
    forgetBudget F hle (semanticState F b2 h) = semanticState F b1 h := rfl

def ExactRealization (F : TestFamily History Test Outcome) (b : Nat)
    (State : Type x) (encode : History -> State)
    (decode : State -> Affordable F b -> Outcome) : Prop :=
  forall h t, F.response h t.1 = decode (encode h) t

theorem exact_realization_kernel (F : TestFamily History Test Outcome) (b : Nat)
    (State : Type x) (encode : History -> State)
    (decode : State -> Affordable F b -> Outcome)
    (hexact : ExactRealization F b State encode decode) :
    forall h h', encode h = encode h' -> equivalent F b h h' := by
  intro h h' heq t
  calc
    F.response h t.1 = decode (encode h) t := hexact h t
    _ = decode (encode h') t := by rw [heq]
    _ = F.response h' t.1 := (hexact h' t).symm

def FullyAbstract (F : TestFamily History Test Outcome) (b : Nat)
    (State : Type x) (encode : History -> State) : Prop :=
  forall h h', encode h = encode h' <-> equivalent F b h h'

theorem quotient_fully_abstract (F : TestFamily History Test Outcome) (b : Nat) :
    FullyAbstract F b (Quotient (budgetSetoid F b)) (semanticState F b) := by
  intro h h'
  constructor
  case mp =>
    intro heq
    exact Quotient.exact heq
  case mpr =>
    intro heq
    exact Quotient.sound heq

theorem predictive_state_full_abstraction
    (F : TestFamily History Test Outcome) (b : Nat)
    (State : Type x) (belief : History -> State)
    (h_sufficient : forall h h' (t : Affordable F b),
      belief h = belief h' -> F.response h t.1 = F.response h' t.1)
    (h_separating : forall h h', equivalent F b h h' -> belief h = belief h') :
    FullyAbstract F b State belief := by
  intro h h'
  constructor
  case mp =>
    intro heq t
    exact h_sufficient h h' t heq
  case mpr =>
    intro heq
    exact h_separating h h' heq

theorem approximate_realization_bound
    (F : TestFamily History Test Outcome) (b : Nat)
    (State : Type x) (encode : History -> State)
    (decode : State -> Affordable F b -> Outcome)
    (dist : (Affordable F b -> Outcome) -> (Affordable F b -> Outcome) -> Nat)
    (hsymm : forall a c, dist a c = dist c a)
    (htri : forall a c d, dist a d <= dist a c + dist c d)
    (eps : Nat)
    (hacc : forall h, dist (profile F b h) (decode (encode h)) <= eps)
    {h h' : History} (heq : encode h = encode h') :
    dist (profile F b h) (profile F b h') <= eps + eps := by
  calc
    dist (profile F b h) (profile F b h')
      <= dist (profile F b h) (decode (encode h)) +
        dist (decode (encode h)) (profile F b h') := htri _ _ _
    _ = dist (profile F b h) (decode (encode h')) +
        dist (profile F b h') (decode (encode h')) := by
          rw [heq]
          rw [hsymm (decode (encode h')) (profile F b h')]
    _ <= eps + eps := Nat.add_le_add (by simpa [congrArg decode heq] using hacc h) (hacc h')

end Cerp.CausalRealization


namespace Cerp.CausalRealization

/-- Turn actual costed-category arrows into the test family used by the quotient. -/
def costedTestFamily
    (C : Cerp.ResourceRelativeProbes.CostedCategory)
    {History : Type u} (X P : C.Obj) (Outcome : Type w)
    (respond : History -> C.Hom P X -> Outcome) :
    TestFamily History (C.Hom P X) Outcome where
  cost := C.cost
  response := respond

/-- The affordable tests of the semantic layer are exactly the affordable
    arrows in the resource-relative probe category. -/
theorem costed_affordable_identification
    (C : Cerp.ResourceRelativeProbes.CostedCategory)
    {History : Type u} (X P : C.Obj) (Outcome : Type w)
    (respond : History -> C.Hom P X -> Outcome) (b : Nat) :
    Affordable (costedTestFamily C X P Outcome respond) b =
      Cerp.ResourceRelativeProbes.Affordable C b X P := rfl

/-- A predictive belief and future-response pairing induces a causal test family. -/
def beliefTestFamily
    (cost : Test -> Nat)
    {X : Type x} (belief : History -> X -> Outcome)
    (future : Test -> X -> Outcome)
    (pair : (X -> Outcome) -> (X -> Outcome) -> Outcome) :
    TestFamily History Test Outcome where
  cost := cost
  response := fun h t => pair (belief h) (future t)

/-- If affordable future tests separate belief states, the belief representation
    is fully abstract for the resource-bounded response semantics. -/
theorem belief_predictive_full_abstraction
    {X : Type x}
    (cost : Test -> Nat)
    (belief : History -> X -> Outcome)
    (future : Test -> X -> Outcome)
    (pair : (X -> Outcome) -> (X -> Outcome) -> Outcome)
    (b : Nat)
    (hsep : forall mu nu : X -> Outcome,
      (forall t : Affordable (beliefTestFamily cost belief future pair) b,
        pair mu (future t.1) = pair nu (future t.1)) -> mu = nu) :
    FullyAbstract (beliefTestFamily cost belief future pair) b (X -> Outcome) belief := by
  apply predictive_state_full_abstraction
  · intro h h' t heq
    simp [beliefTestFamily, heq]
  · intro h h' heq
    apply hsep
    intro t
    exact heq t

end Cerp.CausalRealization
