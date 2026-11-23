import SemanticResponseCore

namespace Cerp.SemanticGroundingBridge

open Cerp.SemanticResponseCore

universe u v w x y

structure ProbeRestriction (P : Type u) where
  Q : Type v
  embed : Q → P

def agreesOn {S : Type w} {P : Type u} {R : Type x}
    (M : ProbeSemantics S P R) (Q : ProbeRestriction P) (s t : S) : Prop :=
  ∀ q : Q.Q, M.response (Q.embed q) s = M.response (Q.embed q) t

theorem semEq_restrict {S : Type w} {P : Type u} {R : Type x}
    (M : ProbeSemantics S P R) (Q : ProbeRestriction P) {s t : S}
    (h : semEq M s t) : agreesOn M Q s t := by
  intro q
  exact h (Q.embed q)

theorem separating_of_restricted {S : Type w} {P : Type u} {R : Type x}
    (M : ProbeSemantics S P R) (Q : ProbeRestriction P)
    (hQ : ∀ s t, agreesOn M Q s t → s = t) :
    SeparatingProbes M := by
  intro s t h
  exact hQ s t (semEq_restrict M Q h)

/-- Non-separating observations leave at least two target states
    indistinguishable. -/
theorem underdetermination_of_nonseparation
    {S : Type w} {P : Type u} {R : Type x}
    (M : ProbeSemantics S P R) (h : ¬ SeparatingProbes M) :
    ∃ s t, s ≠ t ∧ semEq M s t := by
  exact Classical.byContradiction fun hNo =>
    h (fun s t hst =>
      Classical.byContradiction fun hNe =>
        hNo ⟨s, t, hNe, hst⟩)

structure ClaimInterpretation (S : Type u) (C : Type v) (D : Type w) where
  sourceSatisfies : C → S → Prop
  targetSatisfies : D → S → Prop
  translate : C → D

def TruthPreserving {S : Type u} {C : Type v} {D : Type w}
    (I : ClaimInterpretation S C D) : Prop :=
  ∀ c s, I.sourceSatisfies c s → I.targetSatisfies (I.translate c) s

def TruthReflecting {S : Type u} {C : Type v} {D : Type w}
    (I : ClaimInterpretation S C D) : Prop :=
  ∀ c s, I.targetSatisfies (I.translate c) s → I.sourceSatisfies c s

def TruthAdequate {S : Type u} {C : Type v} {D : Type w}
    (I : ClaimInterpretation S C D) : Prop :=
  ∀ c s, I.sourceSatisfies c s ↔ I.targetSatisfies (I.translate c) s

theorem truth_adequate_iff
    {S : Type u} {C : Type v} {D : Type w}
    (I : ClaimInterpretation S C D) :
    TruthAdequate I ↔ TruthPreserving I ∧ TruthReflecting I := by
  constructor
  · intro h
    constructor
    · intro c s hs
      exact (h c s).mp hs
    · intro c s ht
      exact (h c s).mpr ht
  · rintro ⟨hp, hr⟩ c s
    exact ⟨hp c s, hr c s⟩

/-- Grounding here is deliberately relative: exact target-response adequacy,
    plus a representation whose state encoding commutes with target updates. -/
structure GroundedRealization
    {S : Type u} {P : Type v} {R : Type w} {Z : Type x} {A : Type y}
    (M : ProbeSemantics S P R) (T : Dynamics S A) where
  realization : ExactRealization M Z
  dynamics : DynamicRealization (Z := Z) T
  encoding_agrees : dynamics.encode = realization.encode

/-- Exact adequacy plus one-step commutation entails adequacy after every
    finite sequence of interventions/actions. -/
theorem GroundedRealization.finite_intervention_adequacy
    {S : Type u} {P : Type v} {R : Type w} {Z : Type x} {A : Type y}
    {M : ProbeSemantics S P R} {T : Dynamics S A}
    (G : GroundedRealization (Z := Z) M T) :
    ∀ (s : S) (actions : List A) (p : P),
      G.realization.decode p
        (runImplementation G.dynamics (G.dynamics.encode s) actions) =
      M.response p (runTarget T s actions) := by
  intro s actions p
  rw [← DynamicRealization.commutes_list G.dynamics s actions]
  change G.realization.decode p
      (G.dynamics.encode (runTarget T s actions)) =
    M.response p (runTarget T s actions)
  rw [G.encoding_agrees]
  exact G.realization.adequate p (runTarget T s actions)

end Cerp.SemanticGroundingBridge

namespace Cerp.SemanticGroundingBridge

open Cerp.SemanticResponseCore

/-- Passive observations that ignore the target state. -/
def passiveBooleanObservations : ProbeSemantics Bool Unit Bool where
  response := fun _ _ => false

/-- Passive observations cannot distinguish the two Boolean target states. -/
theorem passive_observations_underdetermine :
    semEq passiveBooleanObservations false true ∧ false ≠ true := by
  constructor
  · intro p
    rfl
  · decide

/-- A minimal intervention-sensitive response model. The probe true
    represents an intervention that exposes the state; false is passive. -/
def interventionBooleanObservations : ProbeSemantics Bool Bool Bool where
  response := fun intervene state => if intervene then state else false

theorem intervention_probe_separates :
    SeparatingProbes interventionBooleanObservations := by
  intro s t h
  have hProbe := h true
  simpa [interventionBooleanObservations] using hProbe

end Cerp.SemanticGroundingBridge

namespace Cerp.SemanticGroundingBridge

open Cerp.SemanticResponseCore

/-- Evidence is indexed by both a claim and the target state at which it is
    assessed. This avoids treating evidence for a state-dependent claim as
    if it established that claim in every possible state. -/
structure StateIndexedEvidence (S : Type u) (C : Type v) where
  Evidence : C → S → Type w

def EvidenceSoundFor {S : Type u} {C : Type v}
    (M : SatisfactionModel S C) (E : StateIndexedEvidence S C) : Prop :=
  ∀ c s, E.Evidence c s → M.satisfies c s

def EvidenceCompleteFor {S : Type u} {C : Type v}
    (M : SatisfactionModel S C) (E : StateIndexedEvidence S C) : Prop :=
  ∀ c s, M.satisfies c s → Nonempty (E.Evidence c s)

theorem indexed_evidence_soundness
    {S : Type u} {C : Type v}
    (M : SatisfactionModel S C) (E : StateIndexedEvidence S C)
    (hsound : EvidenceSoundFor M E)
    {c : C} {s : S} (ev : E.Evidence c s) : M.satisfies c s :=
  hsound c s ev

end Cerp.SemanticGroundingBridge
