import ContextualRingDescent
import TotalMarkovRepresentationGroupoid
import ContextualCoalgebraicRing
import ObstructionExactSequence

/-!
# Čech-Nerve Ring of Rings, Spike 44/45 Equivalence & Obstruction Countermodels

Bridges PR #11 (`ContextualRingDescent`) with Spike 44/45 (`TotalMarkovRepresentationGroupoid`,
`ContextualCoalgebraicRing`) and provides a constructive Pure Lean 4 formalization of the
Čech-nerve "ring of rings" framing:

1. **Spike 44 & 45 Integration:**
   - Exact round-trip equivalence between `Cerp.ContextualCoalgebraicRing.ContextualSystem`
     and `Cerp.ContextualRingDescent.ContextualRing`, transferring `sparseABC`, 3-way holonomy,
     and hallucination/grounding separation onto `ContextualSystem`.
   - Faithful functorial bridge between `TotalMarkovRepresentationGroupoid` (`TotalRepresentation`,
     `TotalMarkovIso`) and `VTotalRep Unit` / `VTotalIso`, deriving the missing full
     arbitrary-base-change coCartesian universal property directly for `TotalMarkovIso`.
2. **Generative vs. Reconstructive Čech Nerve (`Cech0`, `Cech1`, `Cech2`):**
   - Formalizes covers `p : U → X`, Čech 0/1/2-simplices, simplicial face identities,
     effective descent for split epimorphic covers (`split_effective_descent_equiv`), and
     the choice-free quotient universal property (`cech_quotient_universal`).
3. **Adversarial Countermodels & Overlap Accounting:**
   - `nonSurjective_cover_loses_global_unity`: non-effective covers lose global unity distinctions;
   - `pullback_preserving_coalgebra_descends` vs. `non_congruent_dynamics_fails_descent`;
   - `partition_of_unity_glues_overlaps` vs. `raw_overlap_double_counts`;
   - `cech_specker_c4_obstruction`: empty distinct triple overlaps with zero global sections.

Zero `Classical.choice`, zero `sorryAx`, zero Mathlib dependencies.
-/

namespace Cerp.CechNerveRingBridge

open Cerp.ContextualCoalgebraicRing
open Cerp.ContextualRingDescent
open Cerp.StochasticInterventionGrounding
open Cerp.StochasticRepresentationGroupoid
open Cerp.SignatureCovariantMarkovTransport
open Cerp.TotalMarkovRepresentationGroupoid
open Cerp.ObstructionExactSequence

universe u v w x y

-- =============================================================================
-- 1. Exact Round-Trip Bridge: ContextualSystem <-> ContextualRing
-- =============================================================================

def contextualSystemToRing (S : ContextualSystem.{u, v, w, x}) :
    ContextualRing.{u, v, w, x} where
  Ctx := S.Context
  Action := S.Action
  Local := S.Local
  Observation := S.Observation
  observe := S.observe
  step := S.step
  adjacent := S.adjacent
  adjacent_symm := S.adjacent_symm
  coh := S.locallyCoherent
  corresponds := S.corresponds
  local_closed := S.local_causal_closure
  corr_closed := S.correspondence_causal_closure

def ringToContextualSystem (R : ContextualRing.{u, v, w, x}) :
    ContextualSystem.{u, v, w, x} where
  Context := R.Ctx
  Action := R.Action
  Local := R.Local
  Observation := R.Observation
  observe := R.observe
  step := R.step
  adjacent := R.adjacent
  adjacent_symm := R.adjacent_symm
  locallyCoherent := R.coh
  corresponds := R.corresponds
  local_causal_closure := R.local_closed
  correspondence_causal_closure := R.corr_closed

theorem contextualSystem_ring_roundtrip (S : ContextualSystem.{u, v, w, x}) :
    ringToContextualSystem (contextualSystemToRing S) = S := by
  cases S; rfl

theorem ring_contextualSystem_roundtrip (R : ContextualRing.{u, v, w, x}) :
    contextualSystemToRing (ringToContextualSystem R) = R := by
  cases R; rfl

def sparseABCSystem : ContextualSystem.{0, 0, 0, 0} :=
  ringToContextualSystem sparseABC

theorem contextualSystem_sparseABC_witness :
    HasNonAdjacentPair sparseABCSystem ∧
    (∀ (actions : List sparseABCSystem.Action) s, GlobalCoherent sparseABCSystem s →
      GlobalCoherent sparseABCSystem (actions.foldl (evolve sparseABCSystem) s)) := by
  refine ⟨⟨.ctxA, .ctxC, sparseABC_hasNonAdjacentPair⟩, ?_⟩
  intro actions s hs
  exact causal_evolution_preserves_all_finite_steps sparseABCSystem s actions hs

theorem contextualSystem_hallucination_separation :
    GlobalCoherent (ringToContextualSystem coherentHallucinationRing) physicalGroundState ∧
    (ringToContextualSystem coherentHallucinationRing).observe false (physicalGroundState false) ≠ true ∧
    (ringToContextualSystem externallyGroundedRing).observe false (physicalGroundState false) = true :=
  ⟨coherentHallucination_is_globally_coherent,
   hallucination_fails_grounding,
   grounded_satisfies_grounding⟩

-- =============================================================================
-- 2. Spike 44 Bridge: TotalRepresentation <-> VTotalRep Unit & Full Universal Property
-- =============================================================================

private def cEquivToVEquiv {A : Type u} {B : Type v} (e : CarrierEquiv A B) : VEquiv A B where
  toFun := e.toFun
  invFun := e.invFun
  left_inv := e.left_inv
  right_inv := e.right_inv

private def vEquivToCEquiv {A : Type u} {B : Type v} (e : VEquiv A B) : CarrierEquiv A B where
  toFun := e.toFun
  invFun := e.invFun
  left_inv := e.left_inv
  right_inv := e.right_inv

def sigToVSig (S : Signature.{u, v, w}) : VSig.{u, v, w} where
  State := S.State
  Action := S.Action
  Outcome := S.Outcome
  stateDec := S.stateDecidableEq
  actionDec := S.actionDecidableEq
  outcomeDec := S.outcomeDecidableEq

def sigEquivToVSigEquiv {S T : Signature.{u, v, w}} (e : SignatureEquiv S T) :
    VSigEquiv (sigToVSig S) (sigToVSig T) where
  stateEq := cEquivToVEquiv e.state
  actionEq := cEquivToVEquiv e.action
  outcomeEq := cEquivToVEquiv e.outcome

def totalRepToVTotal (M : TotalRepresentation.{v, w, x}) : VTotalRep.{0, v, w, x} Unit where
  sig := sigToVSig M.signature
  model :=
    { initial := fun _ => M.model.initialLaw
      observe := M.model.observation
      evolve := M.model.transition
      cost := fun _ => 1
      obsRowMass := M.model.observationMass
      evolveRowMass := M.model.transitionMass
      initial_pos := fun _ => M.model.initial_pos
      obsRowMass_pos := M.model.observationMass_pos
      evolveRowMass_pos := M.model.transitionMass_pos
      obs_mass := M.model.observation_normalized
      evolve_mass := M.model.transition_normalized }

def totalIsoToVTotalIso {M N : TotalRepresentation.{v, w, x}} (h : TotalMarkovIso M N) :
    VTotalIso (totalRepToVTotal M) (totalRepToVTotal N) where
  base :=
    { stateEq := cEquivToVEquiv h.stateEquiv
      actionEq := cEquivToVEquiv h.actionEquiv
      outcomeEq := cEquivToVEquiv h.outcomeEquiv }
  initial_pres := fun _ => h.initial_preserved
  observe_pres := h.observation_preserved
  evolve_pres := h.transition_preserved
  cost_pres := fun _ => rfl

/-- Arbitrary-base-change coCartesian universal property directly for Spike 44's
    `TotalMarkovIso` and `transportLift`. -/
theorem totalIso_coCartesian_universal
    {S T U : Signature.{v, w, x}}
    (M : MarkovRepresentation (State := S.State) (Action := S.Action) (Outcome := S.Outcome))
    (K : MarkovRepresentation (State := U.State) (Action := U.Action) (Outcome := U.Outcome))
    (e : SignatureEquiv S T) (f : SignatureEquiv T U)
    (h : TotalMarkovIso ⟨S, M⟩ ⟨U, K⟩)
    (hbase : e.trans f = signatureOfTotalIso h) :
    ∃ u : TotalMarkovIso ⟨T, transport e M⟩ ⟨U, K⟩,
      signatureOfTotalIso u = f ∧
      TotalMarkovIso.trans (transportLift e M) u = h ∧
      (∀ u' : TotalMarkovIso ⟨T, transport e M⟩ ⟨U, K⟩,
        signatureOfTotalIso u' = f →
        TotalMarkovIso.trans (transportLift e M) u' = h → u' = u) := by
  let vM : VTotalRep.{0, v, w, x} Unit := totalRepToVTotal ⟨S, M⟩
  let vK : VTotalRep.{0, v, w, x} Unit := totalRepToVTotal ⟨U, K⟩
  let ve : VSigEquiv (sigToVSig S) (sigToVSig T) := sigEquivToVSigEquiv e
  let vf : VSigEquiv (sigToVSig T) (sigToVSig U) := sigEquivToVSigEquiv f
  let vh : VTotalIso vM vK := totalIsoToVTotalIso h
  have hvbase : VSigEquiv.trans ve vf = vh.base := by
    have hs := congrArg SignatureEquiv.state hbase
    have ha := congrArg SignatureEquiv.action hbase
    have ho := congrArg SignatureEquiv.outcome hbase
    apply VSigEquiv.ext
    · apply VEquiv.ext
      · intro s; exact congrArg (fun x : CarrierEquiv S.State U.State => x.toFun s) hs
      · intro u0; exact congrArg (fun x : CarrierEquiv S.State U.State => x.invFun u0) hs
    · apply VEquiv.ext
      · intro a; exact congrArg (fun x : CarrierEquiv S.Action U.Action => x.toFun a) ha
      · intro c0; exact congrArg (fun x : CarrierEquiv S.Action U.Action => x.invFun c0) ha
    · apply VEquiv.ext
      · intro o; exact congrArg (fun x : CarrierEquiv S.Outcome U.Outcome => x.toFun o) ho
      · intro o0; exact congrArg (fun x : CarrierEquiv S.Outcome U.Outcome => x.invFun o0) ho
  rcases coCartesian_universal_exists_unique vM.model vK.model ve vf vh hvbase with
    ⟨vu, hvbaseEq, _, _⟩
  let u : TotalMarkovIso ⟨T, transport e M⟩ ⟨U, K⟩ :=
    { stateEquiv := vEquivToCEquiv vu.base.stateEq
      actionEquiv := vEquivToCEquiv vu.base.actionEq
      outcomeEquiv := vEquivToCEquiv vu.base.outcomeEq
      initial_preserved := by
        letI := U.stateDecidableEq
        exact vu.initial_pres ()
      observation_preserved := by
        letI := U.outcomeDecidableEq
        exact vu.observe_pres
      transition_preserved := by
        letI := U.stateDecidableEq
        exact vu.evolve_pres }
  have hsig : signatureOfTotalIso u = f := by
    have hs := congrArg VSigEquiv.stateEq hvbaseEq
    have ha := congrArg VSigEquiv.actionEq hvbaseEq
    have ho := congrArg VSigEquiv.outcomeEq hvbaseEq
    apply SignatureEquiv.ext
    · apply CarrierEquiv.ext
      · exact funext fun s => congrArg (fun x : VEquiv T.State U.State => x.toFun s) hs
      · exact funext fun s => congrArg (fun x : VEquiv T.State U.State => x.invFun s) hs
    · apply CarrierEquiv.ext
      · exact funext fun a => congrArg (fun x : VEquiv T.Action U.Action => x.toFun a) ha
      · exact funext fun a => congrArg (fun x : VEquiv T.Action U.Action => x.invFun a) ha
    · apply CarrierEquiv.ext
      · exact funext fun o => congrArg (fun x : VEquiv T.Outcome U.Outcome => x.toFun o) ho
      · exact funext fun o => congrArg (fun x : VEquiv T.Outcome U.Outcome => x.invFun o) ho
  have hcomp : TotalMarkovIso.trans (transportLift e M) u = h := by
    have hs := congrArg SignatureEquiv.state hsig
    have ha := congrArg SignatureEquiv.action hsig
    have ho := congrArg SignatureEquiv.outcome hsig
    have hsB := congrArg SignatureEquiv.state hbase
    have haB := congrArg SignatureEquiv.action hbase
    have hoB := congrArg SignatureEquiv.outcome hbase
    apply TotalMarkovIso.ext
    · apply CarrierEquiv.ext
      · funext x
        change u.stateEquiv.toFun (e.state.toFun x) = h.stateEquiv.toFun x
        have hu1 := congrArg (fun m : CarrierEquiv T.State U.State => m.toFun (e.state.toFun x)) hs
        have hb1 := congrArg (fun m : CarrierEquiv S.State U.State => m.toFun x) hsB
        exact hu1.trans hb1
      · funext x
        change e.state.invFun (u.stateEquiv.invFun x) = h.stateEquiv.invFun x
        have hu1 := congrArg (fun m : CarrierEquiv T.State U.State => e.state.invFun (m.invFun x)) hs
        have hb1 := congrArg (fun m : CarrierEquiv S.State U.State => m.invFun x) hsB
        exact hu1.trans hb1
    · apply CarrierEquiv.ext
      · funext a
        change u.actionEquiv.toFun (e.action.toFun a) = h.actionEquiv.toFun a
        have hu1 := congrArg (fun m : CarrierEquiv T.Action U.Action => m.toFun (e.action.toFun a)) ha
        have hb1 := congrArg (fun m : CarrierEquiv S.Action U.Action => m.toFun a) haB
        exact hu1.trans hb1
      · funext a
        change e.action.invFun (u.actionEquiv.invFun a) = h.actionEquiv.invFun a
        have hu1 := congrArg (fun m : CarrierEquiv T.Action U.Action => e.action.invFun (m.invFun a)) ha
        have hb1 := congrArg (fun m : CarrierEquiv S.Action U.Action => m.invFun a) haB
        exact hu1.trans hb1
    · apply CarrierEquiv.ext
      · funext o
        change u.outcomeEquiv.toFun (e.outcome.toFun o) = h.outcomeEquiv.toFun o
        have hu1 := congrArg (fun m : CarrierEquiv T.Outcome U.Outcome => m.toFun (e.outcome.toFun o)) ho
        have hb1 := congrArg (fun m : CarrierEquiv S.Outcome U.Outcome => m.toFun o) hoB
        exact hu1.trans hb1
      · funext o
        change e.outcome.invFun (u.outcomeEquiv.invFun o) = h.outcomeEquiv.invFun o
        have hu1 := congrArg (fun m : CarrierEquiv T.Outcome U.Outcome => e.outcome.invFun (m.invFun o)) ho
        have hb1 := congrArg (fun m : CarrierEquiv S.Outcome U.Outcome => m.invFun o) hoB
        exact hu1.trans hb1
  refine ⟨u, hsig, hcomp, ?_⟩
  intro u' hsig' _
  have hsigEq : signatureOfTotalIso u' = signatureOfTotalIso u := hsig'.trans hsig.symm
  have hs := congrArg SignatureEquiv.state hsigEq
  have ha := congrArg SignatureEquiv.action hsigEq
  have ho := congrArg SignatureEquiv.outcome hsigEq
  exact TotalMarkovIso.ext hs ha ho

-- =============================================================================
-- 3. Constructive Čech Nerve Relative to Global Unity X (Comments #28–#29)
-- =============================================================================

/-- A presentation/cover `p : U → X` generating module data from global unity `X`. -/
structure Cover (X : Type u) where
  U : Type v
  p : U → X

def Cech0 {X : Type u} (C : Cover.{u, v} X) : Type v := C.U

def Cech1 {X : Type u} (C : Cover.{u, v} X) : Type v :=
  { pair : C.U × C.U // C.p pair.1 = C.p pair.2 }

def Cech2 {X : Type u} (C : Cover.{u, v} X) : Type v :=
  { triple : C.U × C.U × C.U //
    C.p triple.1 = C.p triple.2.1 ∧ C.p triple.2.1 = C.p triple.2.2 }

def d1_0 {X : Type u} {C : Cover.{u, v} X} (e : Cech1 C) : Cech0 C := e.1.2
def d1_1 {X : Type u} {C : Cover.{u, v} X} (e : Cech1 C) : Cech0 C := e.1.1

def d2_0 {X : Type u} {C : Cover.{u, v} X} (t : Cech2 C) : Cech1 C := ⟨(t.1.2.1, t.1.2.2), t.2.2⟩
def d2_1 {X : Type u} {C : Cover.{u, v} X} (t : Cech2 C) : Cech1 C := ⟨(t.1.1, t.1.2.2), t.2.1.trans t.2.2⟩
def d2_2 {X : Type u} {C : Cover.{u, v} X} (t : Cech2 C) : Cech1 C := ⟨(t.1.1, t.1.2.1), t.2.1⟩

/-- Simplicial Čech-nerve face identities `dᵢ ∘ dⱼ` relating degrees 0, 1, and 2. -/
theorem cech_simplicial_ids {X : Type u} {C : Cover.{u, v} X} (t : Cech2 C) :
    d1_1 (d2_2 t) = d1_1 (d2_1 t) ∧
    d1_0 (d2_2 t) = d1_1 (d2_0 t) ∧
    d1_0 (d2_1 t) = d1_0 (d2_0 t) :=
  ⟨rfl, rfl, rfl⟩

/-- Coherent 0-truncated descent data over the Čech nerve of `C`. -/
@[ext]
structure SetDescentData {X : Type u} (C : Cover.{u, v} X) (Y : Type w) where
  localVal : Cech0 C → Y
  compat : ∀ e : Cech1 C, localVal (d1_1 e) = localVal (d1_0 e)

/-- Synesist generative direction: global data restricts canonically along `p : U → X`. -/
def restrictGlobal {X : Type u} (C : Cover.{u, v} X) {Y : Type w} (g : X → Y) :
    SetDescentData C Y where
  localVal := fun u => g (C.p u)
  compat := fun e => congrArg g e.2

/-- A split effective cover: global unity `X` admits a section `s : X → U`. -/
structure SplitEffectiveCover (X : Type u) extends Cover.{u, v} X where
  sect : X → U
  right_inv : ∀ x, p (sect x) = x

def reconstructGlobal {X : Type u} (C : SplitEffectiveCover.{u, v} X) {Y : Type w}
    (d : SetDescentData C.toCover Y) : X → Y :=
  fun x => d.localVal (C.sect x)

/-- Split effective Čech descent equivalence: restricting global unity data and
    reconstructing from Čech-1 compatible local data form a constructive bijection. -/
theorem split_effective_descent_equiv {X : Type u} (C : SplitEffectiveCover.{u, v} X)
    {Y : Type w} :
    (∀ g : X → Y, reconstructGlobal C (restrictGlobal C.toCover g) = g) ∧
    (∀ d : SetDescentData C.toCover Y, restrictGlobal C.toCover (reconstructGlobal C d) = d) := by
  constructor
  · intro g
    funext x
    change g (C.p (C.sect x)) = g x
    rw [C.right_inv]
  · intro d
    apply SetDescentData.ext
    funext u
    change d.localVal (C.sect (C.p u)) = d.localVal u
    exact d.compat ⟨(C.sect (C.p u), u), C.right_inv (C.p u)⟩

/-- Without assuming any section or Axiom of Choice, Čech descent data on `C` is
    canonically isomorphic to functions on the coequalizer quotient `Quot (C.p u = C.p v)`. -/
def CechQuot {X : Type u} (C : Cover.{u, v} X) : Type v :=
  Quot (fun u v : C.U => C.p u = C.p v)

theorem cech_quotient_universal {X : Type u} (C : Cover.{u, v} X) {Y : Type w} :
    ∃ (toQ : SetDescentData C Y → (CechQuot C → Y))
      (ofQ : (CechQuot C → Y) → SetDescentData C Y),
      (∀ d, ofQ (toQ d) = d) ∧ (∀ qf, toQ (ofQ qf) = qf) := by
  let toQ : SetDescentData C Y → (CechQuot C → Y) := fun d q =>
    Quot.lift d.localVal (fun u v h => d.compat ⟨(u, v), h⟩) q
  let ofQ : (CechQuot C → Y) → SetDescentData C Y := fun qf =>
    { localVal := fun u => qf (Quot.mk _ u)
      compat := fun e => congrArg qf (Quot.sound e.2) }
  refine ⟨toQ, ofQ, ?_, ?_⟩
  · intro d
    apply SetDescentData.ext
    rfl
  · intro qf
    funext q
    induction q using Quot.ind with
    | _ u => rfl

-- =============================================================================
-- 4. Minimal Countermodels for Comments #28 & #29
-- =============================================================================

/-- Non-effective cover (`Unit → Bool`) loses global distinctions: two distinct
    global predicates restrict to identical Čech data. -/
theorem nonSurjective_cover_loses_global_unity :
    let C : Cover.{0, 0} Bool := ⟨Unit, fun _ => false⟩
    (fun x : Bool => x) ≠ (fun _ : Bool => false) ∧
    restrictGlobal C (fun x : Bool => x) = restrictGlobal C (fun _ : Bool => false) := by
  intro C
  refine ⟨?_, ?_⟩
  · intro h
    exact Bool.noConfusion (congrFun h true)
  · apply SetDescentData.ext
    rfl

/-- Congruent local dynamics on `U` descend cleanly to `X` along a split effective cover. -/
theorem pullback_preserving_coalgebra_descends {X : Type u} {A : Type w}
    (C : SplitEffectiveCover.{u, v} X)
    (stepU : C.U → A → C.U)
    (hcong : ∀ u v a, C.p u = C.p v → C.p (stepU u a) = C.p (stepU v a)) :
    ∃ stepX : X → A → X, ∀ u a, C.p (stepU u a) = stepX (C.p u) a := by
  refine ⟨fun x a => C.p (stepU (C.sect x) a), ?_⟩
  intro u a
  exact hcong u (C.sect (C.p u)) a (C.right_inv (C.p u)).symm

/-- Non-congruent local dynamics fail to descend to any global transition on `X`:
    `0` and `1` project identically (`true`), yet `stepU 0 () = 1 ↦ true` while
    `stepU 1 () = 2 ↦ false`. -/
theorem non_congruent_dynamics_fails_descent :
    let C : Cover.{0, 0} Bool := ⟨Nat, fun n => decide (n < 2)⟩
    let stepU : Nat → Unit → Nat := fun n _ => n + 1
    (C.p 0 = C.p 1) ∧
    (¬ ∃ stepX : Bool → Unit → Bool, ∀ n a, C.p (stepU n a) = stepX (C.p n) a) := by
  refine ⟨rfl, ?_⟩
  rintro ⟨stepX, hdesc⟩
  have h0 : true = stepX true () := hdesc 0 ()
  have h1 : false = stepX true () := hdesc 1 ()
  exact Bool.noConfusion (h0.trans h1.symm)

-- =============================================================================
-- 5. Partition of Unity vs. Raw Overlap Double-Counting & C4 Triangle Nerve
-- =============================================================================

/-- Chart weights `{0,1}` (`2,1,0`) and `{1,2}` (`0,1,2`) forming a finite-Nat
    partition of unity of denominator `2` on `Fin 3`. -/
def poWeight0 : Fin 3 → Nat
  | ⟨0, _⟩ => 2
  | ⟨1, _⟩ => 1
  | ⟨2, _⟩ => 0

def poWeight1 : Fin 3 → Nat
  | ⟨0, _⟩ => 0
  | ⟨1, _⟩ => 1
  | ⟨2, _⟩ => 2

theorem partition_of_unity_glues_overlaps (val : Fin 3 → Nat) :
    (∀ x : Fin 3, poWeight0 x + poWeight1 x = 2) ∧
    (poWeight0 ⟨0, by decide⟩ * val ⟨0, by decide⟩ + poWeight0 ⟨1, by decide⟩ * val ⟨1, by decide⟩) +
    (poWeight1 ⟨1, by decide⟩ * val ⟨1, by decide⟩ + poWeight1 ⟨2, by decide⟩ * val ⟨2, by decide⟩) =
      2 * (val ⟨0, by decide⟩ + val ⟨1, by decide⟩ + val ⟨2, by decide⟩) := by
  constructor
  · intro x
    rcases x with ⟨n, hn⟩
    match n with
    | 0 => rfl
    | 1 => rfl
    | 2 => rfl
  · simp only [poWeight0, poWeight1, Nat.one_mul]
    rw [Nat.two_mul (val ⟨0, by decide⟩)]
    rw [Nat.two_mul (val ⟨2, by decide⟩)]
    rw [Nat.two_mul]
    ac_rfl

/-- Unnormalized module summation strictly double-counts overlap point `1` when
    no partition of unity (or gluing quotient) weighs the intersection. -/
theorem raw_overlap_double_counts :
    let val : Fin 3 → Nat := fun _ => 1
    let chart0 := val ⟨0, by decide⟩ + val ⟨1, by decide⟩
    let chart1 := val ⟨1, by decide⟩ + val ⟨2, by decide⟩
    let globalSum := val ⟨0, by decide⟩ + val ⟨1, by decide⟩ + val ⟨2, by decide⟩
    chart0 + chart1 = globalSum + val ⟨1, by decide⟩ ∧ chart0 + chart1 ≠ globalSum :=
  ⟨rfl, by intro h; cases h⟩

/-- Distinct-triple emptiness vs. coset-0 Specker `C4` obstruction inside the Čech nerve:
    a triangle cover with no distinct triple (`U_0 ∩ U_1 ∩ U_2 = ∅`) makes any
    triple-distinct cocycle condition vacuous while retaining a genuine `H^1`
    gluing obstruction blocking global reconstruction. -/
theorem cech_specker_c4_obstruction :
    (¬ triangleCover.overlap3 Tri.v0 Tri.v1 Tri.v2) ∧
    (¬ IsCoboundary c4Group c2InC4 triangleCover speckerC2Cocycle) ∧
    (c4Mul (speckerCoset0Local Tri.v0 Tri.v0 (by trivial))
           (speckerCoset0Local Tri.v0 Tri.v1 (by trivial)) = C4.c2 ∧
     c4Mul (speckerCoset0Local Tri.v1 Tri.v1 (by trivial))
           (speckerCoset0Local Tri.v1 Tri.v2 (by trivial)) = C4.c2 ∧
     c4Mul (speckerCoset0Local Tri.v2 Tri.v2 (by trivial))
           (speckerCoset0Local Tri.v2 Tri.v0 (by trivial)) = C4.c2) ∧
    (¬ GluesByGauge c4Group c2InC4 speckerVarCover speckerCoset0Local) ∧
    (¬ ∃ r : Tri → C4, ValidTriangleRealization r ∧ ∀ v, c2InC4.mem (r v)) := by
  refine ⟨?_, speckerC2Cocycle_nontrivial, speckerCoset0Local_valid_edges,
          speckerCoset0Local_not_gluesByGauge, c4_triangle_coset0_anchor_no_global_realization⟩
  intro h
  rcases h with h | h | h <;> cases h

end Cerp.CechNerveRingBridge
