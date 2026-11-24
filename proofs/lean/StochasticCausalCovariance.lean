import CausalAnchorAdequacy
import StochasticInterventionGrounding

/-!
# Constructive & Stochastic Causal Representation Covariance

Addresses the open gates and hypothesis relaxations for causal representation covariance:
1. Replaces `Classical.choice` in profile equivalence (`↔`) with pure inductive `List` lifting in `Prop`.
2. Generalizes exact cost equality (`cost_commute`) to monotone scaled cost reindexing (`c'(g a) ≤ scale * c(a)`).
3. Relaxes global intervention surjectivity and global outcome injectivity to **affordable-only**
   intervention lifting and **reachable-only** outcome injectivity, with explicit counterexamples
   demonstrating both boundaries.
4. Extends deterministic trace transport and budget-bounded equivalence covariance to **finite
   stochastic Markov kernels** (`FinDist` via `StochasticInterventionGrounding`), axiom-free of `Classical.choice`.
-/

namespace Cerp.StochasticCausalCovariance

open Cerp.CausalAnchorAdequacy
open Cerp.StochasticInterventionGrounding

universe u v w x y z t

section DeterministicWeakened

variable {External : Type u}
variable {State : Type v} {Intervention : Type w} {Outcome : Type x}
variable {State' : Type y} {Intervention' : Type z} {Outcome' : Type t}

/-- Cost-monotone causal representation map with multiplicative budget scaling factor `scale`. -/
structure MonotoneRepMap
    (E : CausalExperiment External State Intervention Outcome)
    (E' : CausalExperiment External State' Intervention' Outcome')
    (scale : Nat) where
  stateMap : State → State'
  interventionMap : Intervention → Intervention'
  outcomeMap : Outcome → Outcome'
  initial_commute : ∀ e, E'.initial e = stateMap (E.initial e)
  observe_commute : ∀ s, E'.observe (stateMap s) = outcomeMap (E.observe s)
  evolve_commute : ∀ s a,
    E'.evolve (stateMap s) (interventionMap a) = stateMap (E.evolve s a)
  cost_le : ∀ a,
    E'.interventionCost (interventionMap a) ≤ scale * E.interventionCost a

def evolveList (E : CausalExperiment External State Intervention Outcome) :
    State → List Intervention → State
  | s, [] => s
  | s, a :: rest => evolveList E (E.evolve s a) rest

def ReachableOutcome
    (E : CausalExperiment External State Intervention Outcome)
    (e : External) (o : Outcome) : Prop :=
  ∃ actions, E.observe (evolveList E (E.initial e) actions) = o

theorem mem_experimentTrace_reachable_aux
    (E : CausalExperiment External State Intervention Outcome)
    (e : External) (prefixActions : List Intervention)
    (actions : List Intervention) {o : Outcome}
    (hmem : o ∈ experimentTrace E actions (evolveList E (E.initial e) prefixActions)) :
    ReachableOutcome E e o := by
  induction actions generalizing prefixActions with
  | nil =>
      simp only [experimentTrace, List.mem_singleton] at hmem
      refine ⟨prefixActions, ?_⟩
      exact hmem.symm
  | cons a rest ih =>
      simp only [experimentTrace, List.mem_cons] at hmem
      rcases hmem with rfl | hrest
      · exact ⟨prefixActions, rfl⟩
      · have ih' := ih (prefixActions ++ [a])
        have hev : ∀ p s l, evolveList E s (p ++ l) = evolveList E (evolveList E s p) l := by
          intro p
          induction p with
          | nil => intro s l; rfl
          | cons b bs ihp => intro s l; simp [evolveList, ihp]
        have hstep : evolveList E (E.initial e) (prefixActions ++ [a]) =
            E.evolve (evolveList E (E.initial e) prefixActions) a := by
          rw [hev]
          rfl
        rw [hstep] at ih'
        exact ih' hrest

theorem mem_experimentTrace_reachable
    (E : CausalExperiment External State Intervention Outcome)
    (e : External) (actions : List Intervention) {o : Outcome}
    (hmem : o ∈ experimentTrace E actions (E.initial e)) :
    ReachableOutcome E e o :=
  mem_experimentTrace_reachable_aux E e [] actions hmem

/-- Choice-free existential list lifting by structural induction on `actions'`. -/
theorem list_lift_exists_of_surj_mem
    {A : Type u} {B : Type v} (f : A → B) (P : A → B → Prop)
    (bs : List B)
    (hlift : ∀ b ∈ bs, ∃ a, f a = b ∧ P a b) :
    ∃ as : List A, as.map f = bs ∧
      (∀ (costA : A → Nat) (costB : B → Nat),
        (∀ a b, P a b → costA a ≤ costB b) →
        as.foldr (fun a acc => costA a + acc) 0 ≤ bs.foldr (fun b acc => costB b + acc) 0) := by
  induction bs with
  | nil =>
      refine ⟨[], rfl, ?_⟩
      intro _ _ _
      exact Nat.le_refl 0
  | cons b rest ih =>
      obtain ⟨a, ha, hPa⟩ := hlift b (List.mem_cons_self _ _)
      obtain ⟨as, has, hcostRest⟩ := ih (fun x hx => hlift x (List.mem_cons_of_mem _ hx))
      refine ⟨a :: as, ?_, ?_⟩
      · simp [ha, has]
      · intro costA costB hP
        have haCost := hP a b hPa
        have hrestCost := hcostRest costA costB hP
        simp only [List.foldr_cons]
        exact Nat.add_le_add haCost hrestCost

theorem experimentCost_eq_foldr
    (E : CausalExperiment External State Intervention Outcome)
    (actions : List Intervention) :
    experimentCost E actions =
      actions.foldr (fun a acc => E.interventionCost a + acc) 0 := by
  induction actions with
  | nil => rfl
  | cons a rest ih => simp [experimentCost, ih]

theorem experimentCost_mem_le
    (E : CausalExperiment External State Intervention Outcome)
    {actions : List Intervention} {a : Intervention}
    (hmem : a ∈ actions) :
    E.interventionCost a ≤ experimentCost E actions := by
  induction actions with
  | nil => cases hmem
  | cons x rest ih =>
      simp only [List.mem_cons] at hmem
      simp only [experimentCost]
      rcases hmem with rfl | hrest
      · exact Nat.le_add_right _ _
      · exact Nat.le_trans (ih hrest) (Nat.le_add_left _ _)

theorem experimentCost_le_of_monotone
    {E : CausalExperiment External State Intervention Outcome}
    {E' : CausalExperiment External State' Intervention' Outcome'}
    {scale : Nat}
    (R : MonotoneRepMap E E' scale)
    (actions : List Intervention) :
    experimentCost E' (actions.map R.interventionMap) ≤
      scale * experimentCost E actions := by
  induction actions with
  | nil => simp [experimentCost]
  | cons a rest ih =>
      simp only [List.map_cons, experimentCost, Nat.mul_add]
      exact Nat.add_le_add (R.cost_le a) ih

theorem experimentTrace_transport_monotone
    {E : CausalExperiment External State Intervention Outcome}
    {E' : CausalExperiment External State' Intervention' Outcome'}
    {scale : Nat}
    (R : MonotoneRepMap E E' scale)
    (actions : List Intervention) (state : State) :
    List.map R.outcomeMap (experimentTrace E actions state) =
      experimentTrace E' (actions.map R.interventionMap) (R.stateMap state) := by
  induction actions generalizing state with
  | nil => simp [experimentTrace, R.observe_commute]
  | cons a rest ih => simp [experimentTrace, R.observe_commute, R.evolve_commute, ih]

theorem profile_transport_monotone
    {E : CausalExperiment External State Intervention Outcome}
    {E' : CausalExperiment External State' Intervention' Outcome'}
    {scale : Nat}
    (R : MonotoneRepMap E E' scale)
    (budget : Nat) (e : External) (actions : List Intervention)
    (hcost : experimentCost E actions ≤ budget) :
    profile (experimentChannel E') (scale * budget) e
        ⟨actions.map R.interventionMap,
          (by
            change experimentCost E' (actions.map R.interventionMap) ≤ scale * budget
            exact Nat.le_trans (experimentCost_le_of_monotone R actions)
              (Nat.mul_le_mul_left scale hcost))⟩ =
      List.map R.outcomeMap
        (profile (experimentChannel E) budget e ⟨actions, hcost⟩) := by
  change experimentTrace E' (actions.map R.interventionMap) (E'.initial e) =
    List.map R.outcomeMap (experimentTrace E actions (E.initial e))
  rw [R.initial_commute]
  exact (experimentTrace_transport_monotone R actions (E.initial e)).symm

/-- Monotone cost scaling preserves profile equality into budget `scale * budget`. -/
theorem profileEquality_preserved_scaled
    {E : CausalExperiment External State Intervention Outcome}
    {E' : CausalExperiment External State' Intervention' Outcome'}
    {scale : Nat}
    (R : MonotoneRepMap E E' scale)
    (budget : Nat) (e e' : External)
    (hprofile :
      profile (experimentChannel E) budget e =
        profile (experimentChannel E) budget e') :
    ∀ (actions : List Intervention) (hcost : experimentCost E actions ≤ budget),
      profile (experimentChannel E') (scale * budget) e
          ⟨actions.map R.interventionMap,
            Nat.le_trans (experimentCost_le_of_monotone R actions)
              (Nat.mul_le_mul_left scale hcost)⟩ =
      profile (experimentChannel E') (scale * budget) e'
          ⟨actions.map R.interventionMap,
            Nat.le_trans (experimentCost_le_of_monotone R actions)
              (Nat.mul_le_mul_left scale hcost)⟩ := by
  intro actions hcost
  have h := congrFun hprofile ⟨actions, hcost⟩
  have ht := congrArg (List.map R.outcomeMap) h
  rw [profile_transport_monotone R budget e actions hcost,
      profile_transport_monotone R budget e' actions hcost]
  exact ht

theorem list_map_injective_on_pred
    {A : Type u} {B : Type v} (f : A → B)
    (P Q : A → Prop)
    (hinj : ∀ x y, P x → Q y → f x = f y → x = y) :
    ∀ {xs ys : List A},
      (∀ x ∈ xs, P x) → (∀ y ∈ ys, Q y) →
      List.map f xs = List.map f ys → xs = ys := by
  intro xs
  induction xs with
  | nil =>
      intro ys _ _ h
      cases ys with
      | nil => rfl
      | cons _ _ => simp at h
  | cons x xs ih =>
      intro ys hP hQ h
      cases ys with
      | nil => simp at h
      | cons y ys =>
          have hp : f x = f y ∧ List.map f xs = List.map f ys := by simpa using h
          have hxy := hinj x y
            (hP x (List.mem_cons_self _ _))
            (hQ y (List.mem_cons_self _ _)) hp.1
          have htail := ih
            (fun a ha => hP a (List.mem_cons_of_mem _ ha))
            (fun b hb => hQ b (List.mem_cons_of_mem _ hb)) hp.2
          simp [hxy, htail]

/-- Profile reflection requires outcome injectivity ONLY on outcomes reachable from
    `e` and `e'`, not globally across unreachable phantom states. -/
theorem profileEquality_reflected_reachable
    {E : CausalExperiment External State Intervention Outcome}
    {E' : CausalExperiment External State' Intervention' Outcome'}
    (R : MonotoneRepMap E E' 1)
    (budget : Nat) (e e' : External)
    (hinjReach : ∀ x y,
      ReachableOutcome E e x → ReachableOutcome E e' y →
      R.outcomeMap x = R.outcomeMap y → x = y)
    (hprofile :
      profile (experimentChannel E') budget e =
        profile (experimentChannel E') budget e') :
    profile (experimentChannel E) budget e =
      profile (experimentChannel E) budget e' := by
  funext probe
  rcases probe with ⟨actions, hcost⟩
  have hcost1 : experimentCost E' (actions.map R.interventionMap) ≤ 1 * budget :=
    Nat.le_trans (experimentCost_le_of_monotone R actions) (Nat.mul_le_mul_left 1 hcost)
  have hcost' : experimentCost E' (actions.map R.interventionMap) ≤ budget := by
    simpa [Nat.one_mul] using hcost1
  have h := congrFun hprofile ⟨actions.map R.interventionMap, hcost'⟩
  have htr :
      List.map R.outcomeMap (profile (experimentChannel E) budget e ⟨actions, hcost⟩) =
      List.map R.outcomeMap (profile (experimentChannel E) budget e' ⟨actions, hcost⟩) := by
    have hL :
        profile (experimentChannel E') (1 * budget) e
          ⟨actions.map R.interventionMap, hcost1⟩ =
        profile (experimentChannel E') budget e ⟨actions.map R.interventionMap, hcost'⟩ := rfl
    have hR :
        profile (experimentChannel E') (1 * budget) e'
          ⟨actions.map R.interventionMap, hcost1⟩ =
        profile (experimentChannel E') budget e' ⟨actions.map R.interventionMap, hcost'⟩ := rfl
    have ht1 := profile_transport_monotone R budget e actions hcost
    have ht2 := profile_transport_monotone R budget e' actions hcost
    rw [hL] at ht1
    rw [hR] at ht2
    rw [← ht1, ← ht2]
    exact h
  exact list_map_injective_on_pred R.outcomeMap
    (ReachableOutcome E e) (ReachableOutcome E e') hinjReach
    (fun o ho => mem_experimentTrace_reachable E e actions ho)
    (fun o ho => mem_experimentTrace_reachable E e' actions ho)
    htr

/-- Constructive (ZERO `Classical.choice`!) characterization of observational equivalence under:
    - monotone cost (`R : MonotoneRepMap E E' 1`),
    - affordable-only lifting (`∀ a', c'(a') ≤ budget → ∃ a, g a = a' ∧ c(a) ≤ c'(a')`),
    - reachable-only outcome injectivity. -/
theorem profileEquality_iff_constructive_affordable
    {E : CausalExperiment External State Intervention Outcome}
    {E' : CausalExperiment External State' Intervention' Outcome'}
    (R : MonotoneRepMap E E' 1)
    (budget : Nat) (e e' : External)
    (haffSurj : ∀ a', E'.interventionCost a' ≤ budget →
      ∃ a, R.interventionMap a = a' ∧ E.interventionCost a ≤ E'.interventionCost a')
    (hinjReach : ∀ x y,
      ReachableOutcome E e x → ReachableOutcome E e' y →
      R.outcomeMap x = R.outcomeMap y → x = y) :
    (profile (experimentChannel E) budget e =
      profile (experimentChannel E) budget e') ↔
    (profile (experimentChannel E') budget e =
      profile (experimentChannel E') budget e') := by
  constructor
  · intro h
    funext probe
    rcases probe with ⟨actions', hcost'⟩
    have hmemLift : ∀ a' ∈ actions',
        ∃ a, R.interventionMap a = a' ∧ E.interventionCost a ≤ E'.interventionCost a' := by
      intro a' ha'
      exact haffSurj a' (Nat.le_trans (experimentCost_mem_le E' ha') hcost')
    obtain ⟨actions, hmap, hcostFold⟩ :=
      list_lift_exists_of_surj_mem R.interventionMap
        (fun a a' => E.interventionCost a ≤ E'.interventionCost a') actions' hmemLift
    have hcost : experimentCost E actions ≤ budget := by
      have hc1 : experimentCost E actions ≤ experimentCost E' actions' := by
        rw [experimentCost_eq_foldr E actions, experimentCost_eq_foldr E' actions']
        exact hcostFold E.interventionCost E'.interventionCost (fun _ _ hp => hp)
      exact Nat.le_trans hc1 hcost'
    have hEq := profileEquality_preserved_scaled R budget e e' h actions hcost
    simpa [hmap, profile, experimentChannel, Nat.one_mul] using hEq
  · exact profileEquality_reflected_reachable R budget e e' hinjReach

end DeterministicWeakened

section Counterexamples

/-- Target adds a new affordable diagnostic probe (`a' = true`) while sharing initial
    and baseline observations; `embedWithoutTrueProbe` commutes yet misses `true`. -/
def sharedInitSource : CausalExperiment Bool Bool Unit Bool where
  initial := fun e => e
  observe := fun _ => false
  evolve := fun s _ => s
  interventionCost := fun _ => 1

/-- Both states initially look `false`; after action `true`, the state identity is exposed. -/
def sharedInitTarget : CausalExperiment Bool (Bool × Bool) Bool Bool where
  initial := fun e => (e, false)
  observe := fun st => if st.2 then st.1 else false
  evolve := fun st a => (st.1, a)
  interventionCost := fun _ => 1

def embedWithoutTrueProbe :
    MonotoneRepMap sharedInitSource sharedInitTarget 1 where
  stateMap := fun s => (s, false)
  interventionMap := fun _ => false
  outcomeMap := id
  initial_commute := by intro _; rfl
  observe_commute := by intro _; rfl
  evolve_commute := by intro _ _; rfl
  cost_le := by intro _; exact Nat.le_refl 1

/-- Counterexample 1: Without affordable-probe surjectivity (even with injective `outcomeMap = id`
    and exact commuting `MonotoneRepMap`), `sharedInitSource` equates `false` and `true` while
    `sharedInitTarget` separates them via the unmapped probe `true`. -/
theorem extra_affordable_probe_breaks_forward_preservation :
    (profile (experimentChannel sharedInitSource) 1 false =
      profile (experimentChannel sharedInitSource) 1 true) ∧
    (profile (experimentChannel sharedInitTarget) 1 false ≠
      profile (experimentChannel sharedInitTarget) 1 true) := by
  constructor
  · have htr : ∀ (actions : List Unit) (s1 s2 : Bool),
        experimentTrace sharedInitSource actions s1 =
          experimentTrace sharedInitSource actions s2 := by
      intro actions
      induction actions with
      | nil => intro _ _; rfl
      | cons _ rest ih =>
          intro s1 s2
          simp only [experimentTrace, sharedInitSource]
          exact congrArg (List.cons false) (ih s1 s2)
    funext probe
    exact htr probe.1 false true
  · intro h
    have h1 := congrFun h ⟨[true], by decide⟩
    simp [profile, experimentChannel, experimentTrace, sharedInitTarget] at h1

def reachTwoOutcomesExp : CausalExperiment Bool Bool Unit (Fin 3) where
  initial := fun e => e
  observe := fun b => if b then ⟨1, by decide⟩ else ⟨0, by decide⟩
  evolve := fun s _ => s
  interventionCost := fun _ => 1

def binaryOutcomeExp : CausalExperiment Bool Bool Unit Bool where
  initial := fun e => e
  observe := id
  evolve := fun s _ => s
  interventionCost := fun _ => 1

def mergeUnreachableOutcome (o : Fin 3) : Bool :=
  if o.1 = 0 then false else true

def reachOnlyRepMap :
    MonotoneRepMap reachTwoOutcomesExp binaryOutcomeExp 1 where
  stateMap := id
  interventionMap := id
  outcomeMap := mergeUnreachableOutcome
  initial_commute := by intro _; rfl
  observe_commute := by
    intro s
    cases s <;> rfl
  evolve_commute := by intro _ _; rfl
  cost_le := by intro _; exact Nat.le_refl 1

/-- Counterexample 2: `mergeUnreachableOutcome` collides `1` and `2` (so it is NOT globally
    injective!), yet `2` is unreachable from both `false` and `true`, so reachable-only reflection
    still holds cleanly. -/
theorem unreachable_outcome_collision_still_reflects :
    (∃ x y : Fin 3, x ≠ y ∧ mergeUnreachableOutcome x = mergeUnreachableOutcome y) ∧
    (∀ e e',
      profile (experimentChannel binaryOutcomeExp) 1 e =
        profile (experimentChannel binaryOutcomeExp) 1 e' →
      profile (experimentChannel reachTwoOutcomesExp) 1 e =
        profile (experimentChannel reachTwoOutcomesExp) 1 e') := by
  constructor
  · refine ⟨⟨1, by decide⟩, ⟨2, by decide⟩, by decide, rfl⟩
  · intro e e' h
    refine profileEquality_reflected_reachable reachOnlyRepMap 1 e e' ?_ h
    intro x y hx hy hmerge
    rcases hx with ⟨ax, hax⟩
    rcases hy with ⟨ay, hay⟩
    have hxBin : (if evolveList reachTwoOutcomesExp (reachTwoOutcomesExp.initial e) ax
        then (⟨1, by decide⟩ : Fin 3) else ⟨0, by decide⟩) = x := hax
    have hyBin : (if evolveList reachTwoOutcomesExp (reachTwoOutcomesExp.initial e') ay
        then (⟨1, by decide⟩ : Fin 3) else ⟨0, by decide⟩) = y := hay
    cases hb1 : evolveList reachTwoOutcomesExp (reachTwoOutcomesExp.initial e) ax <;>
      cases hb2 : evolveList reachTwoOutcomesExp (reachTwoOutcomesExp.initial e') ay <;>
      simp [hb1, hb2] at hxBin hyBin <;>
      subst hxBin <;> subst hyBin <;>
      simp [reachOnlyRepMap, mergeUnreachableOutcome] at hmerge ⊢

end Counterexamples

section StochasticCovariance

variable {External : Type u}
variable {State : Type v} {Intervention : Type w} {Outcome : Type x}
variable {State' : Type y} {Intervention' : Type z} {Outcome' : Type t}

theorem mapDist_append {α : Type u} {β : Type v} (f : α → β) (d1 d2 : FinDist α) :
    mapDist f (d1 ++ d2) = mapDist f d1 ++ mapDist f d2 := by
  induction d1 with
  | nil => rfl
  | cons p rest ih =>
      rcases p with ⟨a, w⟩
      simp [mapDist, ih]

theorem mapDist_scale {α : Type u} {β : Type v} (f : α → β) (d : FinDist α) (w : Nat) :
    mapDist f (d.map (fun p => (p.1, w * p.2))) =
      (mapDist f d).map (fun p => (p.1, w * p.2)) := by
  induction d with
  | nil => rfl
  | cons p rest ih =>
      rcases p with ⟨a, w'⟩
      simp [mapDist, ih]

theorem mapDist_comp {α : Type u} {β : Type v} {γ : Type w}
    (g : β → γ) (f : α → β) (d : FinDist α) :
    mapDist g (mapDist f d) = mapDist (fun a => g (f a)) d := by
  induction d with
  | nil => rfl
  | cons p rest ih =>
      rcases p with ⟨a, w⟩
      simp [mapDist, ih]

theorem mapDist_id {α : Type u} (d : FinDist α) :
    mapDist (fun a => a) d = d := by
  induction d with
  | nil => rfl
  | cons p rest ih =>
      rcases p with ⟨a, w⟩
      simp [mapDist, ih]

theorem mapDist_bindDist {α : Type u} {β : Type v} {γ : Type w}
    (f : β → γ) (d : FinDist α) (k : α → FinDist β) :
    mapDist f (bindDist d k) = bindDist d (fun a => mapDist f (k a)) := by
  induction d with
  | nil => rfl
  | cons p rest ih =>
      rcases p with ⟨a, w⟩
      simp [bindDist, mapDist_append, mapDist_scale, ih]

theorem bindDist_mapDist {α : Type u} {β : Type v} {γ : Type w}
    (g : α → β) (d : FinDist α) (k : β → FinDist γ) :
    bindDist (mapDist g d) k = bindDist d (fun a => k (g a)) := by
  induction d with
  | nil => rfl
  | cons p rest ih =>
      rcases p with ⟨a, w⟩
      simp [mapDist, bindDist, ih]

theorem bindDist_congr {α : Type u} {β : Type v}
    (d : FinDist α) {k1 k2 : α → FinDist β}
    (hk : ∀ a, k1 a = k2 a) :
    bindDist d k1 = bindDist d k2 := by
  induction d with
  | nil => rfl
  | cons p rest ih =>
      rcases p with ⟨a, w⟩
      simp [bindDist, hk a, ih]

theorem weightOf_mapDist_inj {α : Type u} {β : Type v}
    [DecidableEq α] [DecidableEq β]
    (f : α → β) (hinj : ∀ x y, f x = f y → x = y)
    (a : α) (d : FinDist α) :
    weightOf (f a) (mapDist f d) = weightOf a d := by
  induction d with
  | nil => rfl
  | cons p rest ih =>
      rcases p with ⟨b, w⟩
      simp only [mapDist, weightOf]
      by_cases hba : b = a
      · subst hba
        simp [ih]
      · have hne : f b ≠ f a := fun heq => hba (hinj b a heq)
        simp [hba, hne, ih]

theorem distEq_reflected_inj {α : Type u} {β : Type v}
    [DecidableEq α] [DecidableEq β]
    (f : α → β) (hinj : ∀ x y, f x = f y → x = y)
    {d1 d2 : FinDist α}
    (h : distEq (mapDist f d1) (mapDist f d2)) :
    distEq d1 d2 := by
  intro a
  have ha := h (f a)
  rw [weightOf_mapDist_inj f hinj a d1,
      weightOf_mapDist_inj f hinj a d2,
      totalWeight_mapDist, totalWeight_mapDist] at ha
  exact ha

/-- Stochastic Markov-kernel causal experiment parameterized by external states and budget. -/
structure StochasticCausalExperiment (External : Type u) (State : Type v)
    (Intervention : Type w) (Outcome : Type x) where
  initial : External → FinDist State
  observe : State → FinDist Outcome
  evolve : State → Intervention → FinDist State
  interventionCost : Intervention → Nat

def stochasticExperimentCost
    (E : StochasticCausalExperiment External State Intervention Outcome) :
    List Intervention → Nat
  | [] => 0
  | a :: rest => E.interventionCost a + stochasticExperimentCost E rest

def stochasticTrace
    (E : StochasticCausalExperiment External State Intervention Outcome) :
    List Intervention → FinDist State → FinDist (List Outcome)
  | [], d => bindDist d fun s => mapDist (fun o => [o]) (E.observe s)
  | a :: rest, d =>
      bindDist d fun s =>
        bindDist (E.observe s) fun o =>
          bindDist (E.evolve s a) fun s' =>
            mapDist (fun ts => o :: ts) (stochasticTrace E rest (dirac s'))

/-- Structure-preserving covariance map between two stochastic causal experiments. -/
structure StochasticRepMap
    (E : StochasticCausalExperiment External State Intervention Outcome)
    (E' : StochasticCausalExperiment External State' Intervention' Outcome') where
  stateMap : State → State'
  interventionMap : Intervention → Intervention'
  outcomeMap : Outcome → Outcome'
  initial_commute : ∀ e, E'.initial e = mapDist stateMap (E.initial e)
  observe_commute : ∀ s, E'.observe (stateMap s) = mapDist outcomeMap (E.observe s)
  evolve_commute : ∀ s a,
    E'.evolve (stateMap s) (interventionMap a) = mapDist stateMap (E.evolve s a)
  cost_commute : ∀ a,
    E'.interventionCost (interventionMap a) = E.interventionCost a

theorem stochasticExperimentCost_transport
    {E : StochasticCausalExperiment External State Intervention Outcome}
    {E' : StochasticCausalExperiment External State' Intervention' Outcome'}
    (R : StochasticRepMap E E') (actions : List Intervention) :
    stochasticExperimentCost E' (actions.map R.interventionMap) =
      stochasticExperimentCost E actions := by
  induction actions with
  | nil => rfl
  | cons a rest ih => simp [stochasticExperimentCost, R.cost_commute, ih]

theorem stochasticExperimentCost_eq_foldr
    (E : StochasticCausalExperiment External State Intervention Outcome)
    (actions : List Intervention) :
    stochasticExperimentCost E actions =
      actions.foldr (fun a acc => E.interventionCost a + acc) 0 := by
  induction actions with
  | nil => rfl
  | cons a rest ih => simp [stochasticExperimentCost, ih]

theorem stochasticExperimentCost_mem_le
    (E : StochasticCausalExperiment External State Intervention Outcome)
    {actions : List Intervention} {a : Intervention}
    (hmem : a ∈ actions) :
    E.interventionCost a ≤ stochasticExperimentCost E actions := by
  induction actions with
  | nil => cases hmem
  | cons x rest ih =>
      simp only [List.mem_cons] at hmem
      simp only [stochasticExperimentCost]
      rcases hmem with rfl | hrest
      · exact Nat.le_add_right _ _
      · exact Nat.le_trans (ih hrest) (Nat.le_add_left _ _)

/-- Exact Markov pushforward trace transport (zero `Classical.choice`). -/
theorem stochasticTrace_transport
    {E : StochasticCausalExperiment External State Intervention Outcome}
    {E' : StochasticCausalExperiment External State' Intervention' Outcome'}
    (R : StochasticRepMap E E')
    (actions : List Intervention) (d : FinDist State) :
    mapDist (List.map R.outcomeMap) (stochasticTrace E actions d) =
      stochasticTrace E' (actions.map R.interventionMap) (mapDist R.stateMap d) := by
  induction actions generalizing d with
  | nil =>
      simp only [List.map_nil, stochasticTrace, mapDist_bindDist, bindDist_mapDist]
      apply bindDist_congr d
      intro s
      rw [R.observe_commute s, mapDist_comp, mapDist_comp]
      rfl
  | cons a rest ih =>
      simp only [List.map_cons, stochasticTrace, mapDist_bindDist, bindDist_mapDist]
      apply bindDist_congr d
      intro s
      rw [R.observe_commute s, bindDist_mapDist]
      apply bindDist_congr (E.observe s)
      intro o
      rw [R.evolve_commute s a, bindDist_mapDist]
      apply bindDist_congr (E.evolve s a)
      intro s'
      have hdir : mapDist R.stateMap (dirac s') = dirac (R.stateMap s') := rfl
      have ih' := ih (dirac s')
      rw [hdir] at ih'
      rw [← ih', mapDist_comp, mapDist_comp]
      rfl

theorem stochasticExternalTrace_transport
    {E : StochasticCausalExperiment External State Intervention Outcome}
    {E' : StochasticCausalExperiment External State' Intervention' Outcome'}
    (R : StochasticRepMap E E')
    (e : External) (actions : List Intervention) :
    mapDist (List.map R.outcomeMap) (stochasticTrace E actions (E.initial e)) =
      stochasticTrace E' (actions.map R.interventionMap) (E'.initial e) := by
  rw [R.initial_commute e]
  exact stochasticTrace_transport R actions (E.initial e)

def StochasticObsEqual
    (E : StochasticCausalExperiment External State Intervention Outcome)
    [DecidableEq Outcome] (budget : Nat) (e e' : External) : Prop :=
  ∀ actions, stochasticExperimentCost E actions ≤ budget →
    distEq (stochasticTrace E actions (E.initial e))
           (stochasticTrace E actions (E.initial e'))

/-- Stochastic profile equivalence is preserved on all transported affordable probes
    via channel data-processing invariance (`channel_map_preserves_distEq`). -/
theorem stochasticProfile_preserved
    {E : StochasticCausalExperiment External State Intervention Outcome}
    {E' : StochasticCausalExperiment External State' Intervention' Outcome'}
    [DecidableEq Outcome] [DecidableEq Outcome']
    (R : StochasticRepMap E E')
    (budget : Nat) (e e' : External)
    (hobs : StochasticObsEqual E budget e e')
    (actions : List Intervention)
    (hcost : stochasticExperimentCost E actions ≤ budget) :
    distEq (stochasticTrace E' (actions.map R.interventionMap) (E'.initial e))
           (stochasticTrace E' (actions.map R.interventionMap) (E'.initial e')) := by
  rw [← stochasticExternalTrace_transport R e actions,
      ← stochasticExternalTrace_transport R e' actions]
  exact channel_map_preserves_distEq (List.map R.outcomeMap) (hobs actions hcost)

/-- Injective outcome encoding reflects stochastic observational equivalence. -/
theorem stochasticProfile_reflected_inj
    {E : StochasticCausalExperiment External State Intervention Outcome}
    {E' : StochasticCausalExperiment External State' Intervention' Outcome'}
    [DecidableEq Outcome] [DecidableEq Outcome']
    (R : StochasticRepMap E E')
    (budget : Nat) (e e' : External)
    (hinj : ∀ x y, R.outcomeMap x = R.outcomeMap y → x = y)
    (hobs' : StochasticObsEqual E' budget e e') :
    StochasticObsEqual E budget e e' := by
  intro actions hcost
  have hcost' : stochasticExperimentCost E' (actions.map R.interventionMap) ≤ budget := by
    rw [stochasticExperimentCost_transport R actions]
    exact hcost
  have hd' := hobs' (actions.map R.interventionMap) hcost'
  rw [← stochasticExternalTrace_transport R e actions,
      ← stochasticExternalTrace_transport R e' actions] at hd'
  refine distEq_reflected_inj (List.map R.outcomeMap) ?_ hd'
  intro xs ys hmap
  exact list_map_injective_on_pred R.outcomeMap (fun _ => True) (fun _ => True)
    (fun x y _ _ heq => hinj x y heq) (fun _ _ => trivial) (fun _ _ => trivial) hmap

/-- Constructive (ZERO `Classical.choice`!) stochastic equivalence `↔` under
    affordable-only intervention lifting and injective outcome encoding. -/
theorem stochasticProfile_iff_constructive
    {E : StochasticCausalExperiment External State Intervention Outcome}
    {E' : StochasticCausalExperiment External State' Intervention' Outcome'}
    [DecidableEq Outcome] [DecidableEq Outcome']
    (R : StochasticRepMap E E')
    (budget : Nat) (e e' : External)
    (haffSurj : ∀ a', E'.interventionCost a' ≤ budget →
      ∃ a, R.interventionMap a = a')
    (hinj : ∀ x y, R.outcomeMap x = R.outcomeMap y → x = y) :
    StochasticObsEqual E budget e e' ↔ StochasticObsEqual E' budget e e' := by
  constructor
  · intro hobs actions' hcost'
    have hmemLift : ∀ a' ∈ actions',
        ∃ a, R.interventionMap a = a' ∧ True := by
      intro a' ha'
      obtain ⟨a, ha⟩ := haffSurj a' (Nat.le_trans (stochasticExperimentCost_mem_le E' ha') hcost')
      exact ⟨a, ha, trivial⟩
    obtain ⟨actions, hmap, _⟩ :=
      list_lift_exists_of_surj_mem R.interventionMap (fun _ _ => True) actions' hmemLift
    have hcost : stochasticExperimentCost E actions ≤ budget := by
      rw [← stochasticExperimentCost_transport R actions, hmap]
      exact hcost'
    have hEq := stochasticProfile_preserved R budget e e' hobs actions hcost
    rw [hmap] at hEq
    exact hEq
  · exact stochasticProfile_reflected_inj R budget e e' hinj

end StochasticCovariance

end Cerp.StochasticCausalCovariance
