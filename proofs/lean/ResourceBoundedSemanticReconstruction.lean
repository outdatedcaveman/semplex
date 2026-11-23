import HigherSemanticCore

/-!
# Resource-bounded semantic reconstruction

A partial family of admissible contexts determines not necessarily one
global semantic response, but an interval of all monotone completions.
The lower and upper envelopes are the extremal completions. A response at
a context is identifiable exactly when these envelopes coincide there.

The theorem is a grounded identifiability result once the observed values
are known to be restrictions of the actual target response. It does not
assume that the observed probes are globally dense.
-/

namespace Cerp.ResourceBoundedSemanticReconstruction

universe u v

/-- A context preorder: x ≤ y means x is no more refined/informative than y. -/
structure ContextOrder where
  Ctx : Type u
  le : Ctx -> Ctx -> Prop
  refl : forall x, le x x
  trans : forall {x y z}, le x y -> le y z -> le x z
  antisymm : forall {x y}, le x y -> le y x -> x = y

/-- A complete lattice presented by its order and arbitrary suprema/infima. -/
structure CompleteLattice where
  Carrier : Sort v
  le : Carrier -> Carrier -> Prop
  refl : forall x, le x x
  trans : forall {x y z}, le x y -> le y z -> le x z
  antisymm : forall {x y}, le x y -> le y x -> x = y
  sSup : (Carrier -> Prop) -> Carrier
  sInf : (Carrier -> Prop) -> Carrier
  le_sSup : forall (S : Carrier -> Prop) (x), S x -> le x (sSup S)
  sSup_le : forall (S : Carrier -> Prop) (x),
    (forall y, S y -> le y x) -> le (sSup S) x
  sInf_le : forall (S : Carrier -> Prop) (x), S x -> le (sInf S) x
  le_sInf : forall (S : Carrier -> Prop) (x),
    (forall y, S y -> le x y) -> le x (sInf S)

/-- Observations available at a fixed resource budget. -/
structure PartialObservation (C : ContextOrder) (V : CompleteLattice) where
  observable : C.Ctx -> Prop
  value : forall x, observable x -> V.Carrier
  monotone : forall {x y} (hx : observable x) (hy : observable y),
    C.le x y -> V.le (value x hx) (value y hy)

/-- A possible global semantic response extending all observed values. -/
structure Completion (O : PartialObservation C V) where
  response : C.Ctx -> V.Carrier
  monotone : forall {x y}, C.le x y -> V.le (response x) (response y)
  agrees : forall x (hx : O.observable x), response x = O.value x hx

/-- Least value compatible with every observed predecessor of x. -/
def lowerEnvelope (O : PartialObservation C V) (x : C.Ctx) : V.Carrier :=
  V.sSup (fun z => Exists fun p =>
    Exists fun hp : O.observable p =>
      C.le p x ∧ z = O.value p hp)

/-- Greatest value compatible with every observed successor of x. -/
def upperEnvelope (O : PartialObservation C V) (x : C.Ctx) : V.Carrier :=
  V.sInf (fun z => Exists fun p =>
    Exists fun hp : O.observable p =>
      C.le x p ∧ z = O.value p hp)

theorem lower_le_upper (O : PartialObservation C V) (x : C.Ctx) :
    V.le (lowerEnvelope O x) (upperEnvelope O x) := by
  apply V.sSup_le
  intro a ha
  rcases ha with ⟨p, hp, hpx, rfl⟩
  apply V.le_sInf
  intro b hb
  rcases hb with ⟨q, hq, hxq, rfl⟩
  exact O.monotone hp hq (C.trans hpx hxq)

/-- Every actual monotone completion lies above the lower envelope. -/
theorem lower_le_completion (O : PartialObservation C V)
    (G : Completion O) (x : C.Ctx) :
    V.le (lowerEnvelope O x) (G.response x) := by
  apply V.sSup_le
  intro a ha
  rcases ha with ⟨p, hp, hpx, rfl⟩
  rw [← G.agrees p hp]
  exact G.monotone hpx

/-- Every actual monotone completion lies below the upper envelope. -/
theorem completion_le_upper (O : PartialObservation C V)
    (G : Completion O) (x : C.Ctx) :
    V.le (G.response x) (upperEnvelope O x) := by
  apply V.le_sInf
  intro a ha
  rcases ha with ⟨p, hp, hxp, rfl⟩
  rw [← G.agrees p hp]
  exact G.monotone hxp

/-- The lower envelope is itself monotone. -/
theorem lowerEnvelope_monotone (O : PartialObservation C V)
    {x y : C.Ctx} (hxy : C.le x y) :
    V.le (lowerEnvelope O x) (lowerEnvelope O y) := by
  apply V.sSup_le
  intro a ha
  rcases ha with ⟨p, hp, hpx, rfl⟩
  apply V.le_sSup
  exact ⟨p, hp, C.trans hpx hxy, rfl⟩

/-- The upper envelope is itself monotone. -/
theorem upperEnvelope_monotone (O : PartialObservation C V)
    {x y : C.Ctx} (hxy : C.le x y) :
    V.le (upperEnvelope O x) (upperEnvelope O y) := by
  apply V.le_sInf
  intro a ha
  rcases ha with ⟨p, hp, hyp, rfl⟩
  apply V.sInf_le
  exact ⟨p, hp, C.trans hxy hyp, rfl⟩

/-- On observed contexts, both envelopes recover the observed value. -/
theorem lowerEnvelope_agrees (O : PartialObservation C V)
    (x : C.Ctx) (hx : O.observable x) :
    lowerEnvelope O x = O.value x hx := by
  apply V.antisymm
  · apply V.sSup_le
    intro a ha
    rcases ha with ⟨p, hp, hpx, rfl⟩
    exact O.monotone hp hx hpx
  · apply V.le_sSup
    exact ⟨x, hx, C.refl x, rfl⟩

theorem upperEnvelope_agrees (O : PartialObservation C V)
    (x : C.Ctx) (hx : O.observable x) :
    upperEnvelope O x = O.value x hx := by
  apply V.antisymm
  · apply V.sInf_le
    exact ⟨x, hx, C.refl x, rfl⟩
  · apply V.le_sInf
    intro a ha
    rcases ha with ⟨p, hp, hxp, rfl⟩
    exact O.monotone hx hp hxp

/-- Both extremal envelopes are genuine monotone completions. -/
def lowerCompletion (O : PartialObservation C V) : Completion O where
  response := lowerEnvelope O
  monotone := by
    intro x y hxy
    exact lowerEnvelope_monotone O hxy
  agrees := by
    intro x hx
    exact lowerEnvelope_agrees O x hx

def upperCompletion (O : PartialObservation C V) : Completion O where
  response := upperEnvelope O
  monotone := by
    intro x y hxy
    exact upperEnvelope_monotone O hxy
  agrees := by
    intro x hx
    exact upperEnvelope_agrees O x hx

/-- The semantic value at x is identifiable iff the lower and upper
    completion envelopes coincide there. -/
def IdentifiableAt (O : PartialObservation C V) (x : C.Ctx) : Prop :=
  forall G H : Completion O, G.response x = H.response x

theorem identifiable_iff_envelopes_collapse
    (O : PartialObservation C V) (x : C.Ctx) :
    IdentifiableAt O x <-> lowerEnvelope O x = upperEnvelope O x := by
  constructor
  · intro h
    exact h (lowerCompletion O) (upperCompletion O)
  · intro h G H
    have hGlo := lower_le_completion O G x
    have hGup := completion_le_upper O G x
    have hHlo := lower_le_completion O H x
    have hHup := completion_le_upper O H x
    have hupperlower : V.le (upperEnvelope O x) (lowerEnvelope O x) := by
      rw [h]
      exact V.refl _
    have hG : G.response x = lowerEnvelope O x :=
      V.antisymm (V.trans hGup hupperlower) hGlo
    have hH : H.response x = lowerEnvelope O x :=
      V.antisymm (V.trans hHup hupperlower) hHlo
    exact hG.trans hH.symm

/-- An actual target semantics is grounded by a witness that its values on
    executable probes are exactly the observed values. -/
structure GroundingWitness (O : PartialObservation C V) where
  actual : Completion O

/-- The grounded target response is always inside the observational envelope. -/
theorem grounded_target_within_envelope (O : PartialObservation C V)
    (W : GroundingWitness O) (x : C.Ctx) :
    V.le (lowerEnvelope O x) (W.actual.response x) /\
    V.le (W.actual.response x) (upperEnvelope O x) :=
  ⟨lower_le_completion O W.actual x, completion_le_upper O W.actual x⟩


/-! ## Resource indexing

Budgets form a preorder and executable probes are nested with budget.
The observed value attached to a probe is stable when the same probe is
available at two budgets. The envelopes therefore narrow monotonically
as resources increase.
-/

structure BudgetOrder where
  Budget : Type u
  le : Budget -> Budget -> Prop
  refl : forall b, le b b
  trans : forall {a b c}, le a b -> le b c -> le a c

structure BudgetedObservation (C : ContextOrder) (V : CompleteLattice) where
  Budgets : BudgetOrder
  observable : Budgets.Budget -> C.Ctx -> Prop
  value : forall b x, observable b x -> V.Carrier
  context_monotone : forall b {x y} (hx : observable b x)
    (hy : observable b y), C.le x y ->
      V.le (value b x hx) (value b y hy)
  budget_nested : forall {b c}, Budgets.le b c ->
    forall x, observable b x -> observable c x
  budget_consistent : forall {b c} (_hbc : Budgets.le b c) x
    (hb : observable b x) (hc : observable c x),
    value b x hb = value c x hc

def atBudget (M : BudgetedObservation C V) (b : M.Budgets.Budget) :
    PartialObservation C V where
  observable := M.observable b
  value := M.value b
  monotone := by
    intro x y hx hy hxy
    exact M.context_monotone b hx hy hxy

/-- More resources can only raise the lower semantic envelope. -/
theorem lowerEnvelope_monotone_budget (M : BudgetedObservation C V)
    {b c : M.Budgets.Budget} (hbc : M.Budgets.le b c) (x : C.Ctx) :
    V.le (lowerEnvelope (atBudget M b) x)
      (lowerEnvelope (atBudget M c) x) := by
  apply V.sSup_le
  intro a ha
  rcases ha with ⟨p, hp, hpx, rfl⟩
  have hc := M.budget_nested hbc p hp
  apply V.le_sSup
  exact ⟨p, hc, hpx, M.budget_consistent hbc p hp hc⟩

/-- More resources can only lower the upper semantic envelope. -/
theorem upperEnvelope_antitone_budget (M : BudgetedObservation C V)
    {b c : M.Budgets.Budget} (hbc : M.Budgets.le b c) (x : C.Ctx) :
    V.le (upperEnvelope (atBudget M c) x)
      (upperEnvelope (atBudget M b) x) := by
  apply V.le_sInf
  intro a ha
  rcases ha with ⟨p, hp, hxp, rfl⟩
  have hc := M.budget_nested hbc p hp
  apply V.sInf_le
  exact ⟨p, hc, hxp, M.budget_consistent hbc p hp hc⟩

/-- Once a context is identifiable at one budget, it remains identifiable
    at every larger budget. -/
theorem identifiability_persists_with_budget (M : BudgetedObservation C V)
    {b c : M.Budgets.Budget} (hbc : M.Budgets.le b c) (x : C.Ctx)
    (hident : lowerEnvelope (atBudget M b) x =
      upperEnvelope (atBudget M b) x) :
    lowerEnvelope (atBudget M c) x =
      upperEnvelope (atBudget M c) x := by
  apply V.antisymm
  · exact lower_le_upper (atBudget M c) x
  · have hEq : V.le (upperEnvelope (atBudget M b) x)
        (lowerEnvelope (atBudget M b) x) := by
      rw [hident]
      exact V.refl _
    exact V.trans (upperEnvelope_antitone_budget M hbc x)
      (V.trans hEq (lowerEnvelope_monotone_budget M hbc x))


/-! ## Grounded truth and evidence as proposition-valued semantics

For propositions ordered by implication, the lower envelope is evidence
available uniformly across all compatible completions; the upper envelope
is the strongest truth still compatible with the observations.
-/

def propositionLattice : CompleteLattice where
  Carrier := Prop
  le := fun P Q => P -> Q
  refl := by intro P hP; exact hP
  trans := by intro P Q R hPQ hQR hP; exact hQR (hPQ hP)
  antisymm := by
    intro P Q hPQ hQP
    exact propext ⟨hPQ, hQP⟩
  sSup := fun S => Exists fun P => And (S P) P
  sInf := fun S => forall P, S P -> P
  le_sSup := by
    intro S P hP p
    exact ⟨P, hP, p⟩
  sSup_le := by
    intro S P h
    rintro ⟨Q, hQ, q⟩
    exact h Q hQ q
  sInf_le := by
    intro S P hP h
    exact h P hP
  le_sInf := by
    intro S P hP p Q hQ
    exact hP Q hQ p

structure ClaimReference (C : ContextOrder) where
  Claim : Type u
  reference : Claim -> C.Ctx

def ActualClaimTruth (O : PartialObservation C propositionLattice)
    (G : Completion O) (R : ClaimReference C) (c : R.Claim) : Prop :=
  G.response (R.reference c)

def ProbeEvidence (O : PartialObservation C propositionLattice)
    (R : ClaimReference C) (c : R.Claim) : Prop :=
  lowerEnvelope O (R.reference c)

/-- A proof of the lower envelope is sound evidence of truth in the actual
    target, provided the observations are genuinely grounded in that target. -/
theorem probe_evidence_sound (O : PartialObservation C propositionLattice)
    (G : Completion O) (R : ClaimReference C) (c : R.Claim)
    (h : ProbeEvidence O R c) :
    ActualClaimTruth O G R c :=
  (lower_le_completion O G (R.reference c)) h

/-- If the upper envelope is false, no compatible grounded target can make
    the referenced claim true. -/
theorem upper_envelope_refutes (O : PartialObservation C propositionLattice)
    (G : Completion O) (R : ClaimReference C) (c : R.Claim)
    (hfalse : upperEnvelope O (R.reference c) = False) :
    ActualClaimTruth O G R c -> False := by
  change G.response (R.reference c) -> False
  have h : G.response (R.reference c) ->
      upperEnvelope O (R.reference c) :=
    completion_le_upper O G (R.reference c)
  rw [hfalse] at h
  exact h

/-- Evidence completeness is an additional property, not a consequence of
    evidence soundness or of the envelope construction. -/
def EvidenceComplete (O : PartialObservation C propositionLattice)
    (G : Completion O) (R : ClaimReference C) : Prop :=
  forall c, ActualClaimTruth O G R c -> ProbeEvidence O R c


/-! ## Finite executable-probe witness

A two-context chain has an unobserved upper context at low budget and both
contexts observed at high budget. The envelope is genuinely ambiguous at
low budget and collapses at high budget.
-/

def boolLe (a b : Bool) : Prop := a = false \/ b = true

def boolContextOrder : ContextOrder where
  Ctx := Bool
  le := boolLe
  refl := by intro x; cases x <;> simp [boolLe]
  trans := by
    intro x y z hxy hyz
    cases x <;> cases y <;> cases z <;> simp [boolLe] at *
  antisymm := by
    intro x y hxy hyx
    cases x <;> cases y <;> simp [boolLe] at *

def boolBudgetOrder : BudgetOrder where
  Budget := Bool
  le := boolLe
  refl := by intro x; cases x <;> simp [boolLe]
  trans := by
    intro x y z hxy hyz
    cases x <;> cases y <;> cases z <;> simp [boolLe] at *

def boolBudgetedObservation :
    BudgetedObservation boolContextOrder propositionLattice where
  Budgets := boolBudgetOrder
  observable := fun b x => x = false \/ (b = true /\ x = true)
  value := fun _ x _ => Bool.rec (motive := fun _ => Prop) False True x
  context_monotone := by
    intro b x y hx hy hxy
    change (Bool.rec (motive := fun _ => Prop) False True x) ->
      (Bool.rec (motive := fun _ => Prop) False True y)
    cases x <;> cases y <;> simp [boolContextOrder, boolLe] at *
  budget_nested := by
    intro b c hbc x hx
    rcases hx with hx | ⟨hb, hx⟩
    · exact Or.inl hx
    · subst b
      cases c with
      | false => simp [boolBudgetOrder, boolLe] at hbc
      | true =>
          have hc : true = true := by simp [boolBudgetOrder, boolLe] at hbc ⊢
          exact Or.inr ⟨hc, hx⟩
  budget_consistent := by
    intro b c _hbc x hb hc
    cases x <;> rfl

def lowFalseCompletion :
    Completion (atBudget boolBudgetedObservation false) where
  response := fun _ => False
  monotone := by intro x y _hxy h; exact h
  agrees := by
    intro x hx
    cases x with
    | false => rfl
    | true =>
        change Or (true = false) (And (false = true) (true = true)) at hx
        simp at hx

def lowMixedCompletion :
    Completion (atBudget boolBudgetedObservation false) where
  response := fun x => Bool.rec (motive := fun _ => Prop) False True x
  monotone := by
    intro x y hxy
    change (Bool.rec (motive := fun _ => Prop) False True x) ->
      (Bool.rec (motive := fun _ => Prop) False True y)
    cases x <;> cases y <;> simp [boolContextOrder, boolLe] at *
  agrees := by
    intro x hx
    cases x with
    | false => rfl
    | true =>
        change Or (true = false) (And (false = true) (true = true)) at hx
        simp at hx

/-- At low budget, two monotone completions agree on all observations but
    disagree at the unobserved upper context. -/
theorem low_budget_not_identifiable :
    ¬ IdentifiableAt (atBudget boolBudgetedObservation false) true := by
  intro h
  have hEq := h lowFalseCompletion lowMixedCompletion
  change False = True at hEq
  have hFalse : False := Eq.mpr hEq True.intro
  exact False.elim hFalse

/-- At high budget the upper context itself is observed, so both extremal
    envelopes recover its value and identifiability follows. -/
theorem high_budget_envelope_collapses :
    lowerEnvelope (atBudget boolBudgetedObservation true) true = True /\
    upperEnvelope (atBudget boolBudgetedObservation true) true = True := by
  have hobs : boolBudgetedObservation.observable true true :=
    Or.inr ⟨rfl, rfl⟩
  constructor
  · calc
      lowerEnvelope (atBudget boolBudgetedObservation true) true =
          boolBudgetedObservation.value true true hobs :=
        lowerEnvelope_agrees (atBudget boolBudgetedObservation true) true hobs
      _ = True := rfl
  · calc
      upperEnvelope (atBudget boolBudgetedObservation true) true =
          boolBudgetedObservation.value true true hobs :=
        upperEnvelope_agrees (atBudget boolBudgetedObservation true) true hobs
      _ = True := rfl

end Cerp.ResourceBoundedSemanticReconstruction
