import Lean

/-!
# Resource-indexed operational grounding adequacy

This interface keeps the external target distinct from the internal
operational system. A realization relation connects them; calibration
requires internal probe responses to agree with externally specified
responses; separation requires affordable probes to distinguish distinct
external targets.

The theorem is conditional: it proves uniqueness of reference from
calibration plus separation, without defining the external target by the
internal state representation.
-/

namespace Cerp.OperationalGroundingAdequacy

universe u v w x

structure OperationalGrounding
    (System : Type u) (External : Type v) (Probe : Type w) (Outcome : Type x) where
  cost : Probe -> Nat
  systemResponse : System -> Probe -> Outcome
  externalResponse : External -> Probe -> Outcome
  realizes : System -> External -> Prop
  calibration : forall system external,
    realizes system external ->
      forall probe, systemResponse system probe = externalResponse external probe

def ProfileEqualAt
    {System : Type u} {External : Type v} {Probe : Type w} {Outcome : Type x}
    (G : OperationalGrounding System External Probe Outcome)
    (budget : Nat) (s s' : System) : Prop :=
  forall probe, G.cost probe <= budget ->
    G.systemResponse s probe = G.systemResponse s' probe

def SeparatesAt
    {System : Type u} {External : Type v} {Probe : Type w} {Outcome : Type x}
    (G : OperationalGrounding System External Probe Outcome)
    (budget : Nat) : Prop :=
  forall e e', e ≠ e' ->
    exists probe, G.cost probe <= budget /\
      G.externalResponse e probe ≠ G.externalResponse e' probe

/-- Calibration and resource-bounded separation force a unique external
    referent for realized systems with equal affordable response profiles. -/
theorem realized_referent_unique
    {System : Type u} {External : Type v} {Probe : Type w} {Outcome : Type x}
    (G : OperationalGrounding System External Probe Outcome)
    (budget : Nat) (hsep : SeparatesAt G budget)
    {s s' : System} {e e' : External}
    (hrs : G.realizes s e) (hrs' : G.realizes s' e')
    (hprofile : ProfileEqualAt G budget s s') :
    e = e' := by
  apply Classical.byContradiction
  intro hne
  obtain ⟨probe, hcost, hdist⟩ := hsep e e' hne
  exact hdist
    ((G.calibration s e hrs probe).symm.trans
      ((hprofile probe hcost).trans (G.calibration s' e' hrs' probe)))

/-- Failure of separation has an explicit witness: two distinct external
    targets agree on every affordable probe. -/
theorem indistinguishable_external_pair_of_not_separating
    {System : Type u} {External : Type v} {Probe : Type w} {Outcome : Type x}
    (G : OperationalGrounding System External Probe Outcome)
    (budget : Nat) (hnot : ¬ SeparatesAt G budget) :
    exists e e', e ≠ e' /\
      forall probe, G.cost probe <= budget ->
        G.externalResponse e probe = G.externalResponse e' probe := by
  unfold SeparatesAt at hnot
  rcases Classical.not_forall.mp hnot with ⟨e, he⟩
  rcases Classical.not_forall.mp he with ⟨e', he'⟩
  have hne : e ≠ e' := by
    intro heq
    apply he'
    intro hne'
    exact False.elim (hne' heq)
  have hnoProbe :
      ¬ exists probe, G.cost probe <= budget /\
        G.externalResponse e probe ≠ G.externalResponse e' probe := by
    intro hp
    exact he' (fun _ => hp)
  refine ⟨e, e', hne, ?_⟩
  intro probe hcost
  apply Classical.byContradiction
  intro hneq
  exact hnoProbe ⟨probe, hcost, hneq⟩

/-- Once a probe family separates at budget B, it also separates at every
    larger budget C. -/
theorem separatesAt_monotone
    {System : Type u} {External : Type v} {Probe : Type w} {Outcome : Type x}
    (G : OperationalGrounding System External Probe Outcome)
    {b c : Nat} (hle : b <= c) (hsep : SeparatesAt G b) :
    SeparatesAt G c := by
  intro e e' hne
  obtain ⟨probe, hcost, hdist⟩ := hsep e e' hne
  exact ⟨probe, Nat.le_trans hcost hle, hdist⟩

end Cerp.OperationalGroundingAdequacy


namespace Cerp.OperationalGroundingAdequacy

/-- A minimal external hidden-bit world. The passive probe always returns
    false; the active probe (true) reveals the externally specified bit. -/
def hiddenBitGrounding :
    OperationalGrounding (Bool × Bool) Bool Bool Bool where
  cost := fun probe => if probe then 1 else 0
  systemResponse := fun system probe => if probe then system.1 else false
  externalResponse := fun external probe => if probe then external else false
  realizes := fun system external => system.1 = external
  calibration := by
    intro system external hrealizes probe
    cases probe <;> simp [hrealizes]

theorem hiddenBit_separates_at_one :
    SeparatesAt hiddenBitGrounding 1 := by
  intro e e' hne
  refine ⟨true, by decide, ?_⟩
  simpa [hiddenBitGrounding] using hne

theorem hiddenBit_not_separating_at_zero :
    ¬ SeparatesAt hiddenBitGrounding 0 := by
  intro hsep
  obtain ⟨probe, hcost, hdiff⟩ := hsep false true (by decide)
  cases probe <;> simp [hiddenBitGrounding] at hcost hdiff

theorem hiddenBit_external_reference_unique_at_one
    {s s' : Bool × Bool} {e e' : Bool}
    (hrs : hiddenBitGrounding.realizes s e)
    (hrs' : hiddenBitGrounding.realizes s' e')
    (hprofile : ProfileEqualAt hiddenBitGrounding 1 s s') :
    e = e' :=
  realized_referent_unique hiddenBitGrounding 1 hiddenBit_separates_at_one
    hrs hrs' hprofile

end Cerp.OperationalGroundingAdequacy


namespace Cerp.OperationalGroundingAdequacy

universe u v w x

/-- The complete external response profile available at budget B. -/
def ExternalProfileAt
    {System : Type u} {External : Type v} {Probe : Type w} {Outcome : Type x}
    (G : OperationalGrounding System External Probe Outcome)
    (budget : Nat) (external : External) :
    {probe : Probe // G.cost probe <= budget} -> Outcome :=
  fun probe => G.externalResponse external probe.1

/-- The internal system profile at budget B. -/
def SystemProfileAt
    {System : Type u} {External : Type v} {Probe : Type w} {Outcome : Type x}
    (G : OperationalGrounding System External Probe Outcome)
    (budget : Nat) (system : System) :
    {probe : Probe // G.cost probe <= budget} -> Outcome :=
  fun probe => G.systemResponse system probe.1

/-- Calibration is equality of the complete internal and external
    response profiles, not merely a pointwise informal correspondence. -/
theorem calibration_profile
    {System : Type u} {External : Type v} {Probe : Type w} {Outcome : Type x}
    (G : OperationalGrounding System External Probe Outcome)
    (budget : Nat) {system : System} {external : External}
    (hrealizes : G.realizes system external) :
    SystemProfileAt G budget system = ExternalProfileAt G budget external := by
  funext probe
  exact G.calibration system external hrealizes probe.1

def ExternalProfileInjective
    {System : Type u} {External : Type v} {Probe : Type w} {Outcome : Type x}
    (G : OperationalGrounding System External Probe Outcome)
    (budget : Nat) : Prop :=
  forall {e e'}, ExternalProfileAt G budget e = ExternalProfileAt G budget e' -> e = e'

/-- The external profile representation is injective exactly when the
    affordable external probes separate all distinct targets. -/
theorem externalProfile_injective_iff_separatesAt
    {System : Type u} {External : Type v} {Probe : Type w} {Outcome : Type x}
    (G : OperationalGrounding System External Probe Outcome)
    (budget : Nat) :
    ExternalProfileInjective G budget ↔ SeparatesAt G budget := by
  constructor
  · intro hinj e e' hne
    apply Classical.byContradiction
    intro hno
    have hprofiles :
        ExternalProfileAt G budget e = ExternalProfileAt G budget e' := by
      funext probe
      apply Classical.byContradiction
      intro hneq
      exact hno ⟨probe.1, probe.2, hneq⟩
    exact hne (hinj hprofiles)
  · intro hsep e e' hprofiles
    apply Classical.byContradiction
    intro hne
    obtain ⟨probe, hcost, hdiff⟩ := hsep e e' hne
    exact hdiff (congrFun hprofiles ⟨probe, hcost⟩)

end Cerp.OperationalGroundingAdequacy


namespace Cerp.OperationalGroundingAdequacy

universe u v w x

/-- An external relabelling symmetry that leaves every operationally
    available response unchanged. Such a symmetry is invisible to probes. -/
def ResponseInvisibleRelabelling
    {System : Type u} {External : Type v} {Probe : Type w} {Outcome : Type x}
    (G : OperationalGrounding System External Probe Outcome)
    (sigma : External -> External) : Prop :=
  forall external probe,
      G.externalResponse (sigma external) probe =
        G.externalResponse external probe

/-- An invisible relabelling leaves the complete resource-bounded profile
    unchanged, at every budget. -/
theorem invisible_symmetry_preserves_profile
    {System : Type u} {External : Type v} {Probe : Type w} {Outcome : Type x}
    (G : OperationalGrounding System External Probe Outcome)
    (sigma : External -> External)
    (hinv : ResponseInvisibleRelabelling G sigma)
    (budget : Nat) (external : External) :
    ExternalProfileAt G budget (sigma external) =
      ExternalProfileAt G budget external := by
  funext probe
  exact hinv external probe.1

/-- Any nontrivial response-invisible symmetry refutes global probe
    separation, no matter how large the resource budget becomes. -/
theorem invisible_symmetry_refutes_separation
    {System : Type u} {External : Type v} {Probe : Type w} {Outcome : Type x}
    (G : OperationalGrounding System External Probe Outcome)
    (sigma : External -> External)
    (hinv : ResponseInvisibleRelabelling G sigma)
    (budget : Nat) (external : External)
    (hmoves : sigma external ≠ external) :
    ¬ SeparatesAt G budget := by
  intro hsep
  obtain ⟨probe, hcost, hdist⟩ :=
    hsep (sigma external) external hmoves
  exact hdist (hinv external probe)

/-- Calibration is invariant under a response-invisible relabelling:
    the same internal system response is calibrated equally well against
    the relabelled external target. -/
theorem calibration_invariant_under_invisible_symmetry
    {System : Type u} {External : Type v} {Probe : Type w} {Outcome : Type x}
    (G : OperationalGrounding System External Probe Outcome)
    (sigma : External -> External)
    (hinv : ResponseInvisibleRelabelling G sigma)
    {system : System} {external : External}
    (hrealizes : G.realizes system external) :
    forall probe,
      G.systemResponse system probe =
        G.externalResponse (sigma external) probe := by
  intro probe
  calc
    G.systemResponse system probe =
        G.externalResponse external probe :=
      G.calibration system external hrealizes probe
    _ = G.externalResponse (sigma external) probe :=
      (hinv external probe).symm

/-- Reindex the external interpretation by an invisible symmetry.
    The operational system, costs, and response functions remain unchanged;
    only the realization relation is relabelled. -/
def reindexGrounding
    {System : Type u} {External : Type v} {Probe : Type w} {Outcome : Type x}
    (G : OperationalGrounding System External Probe Outcome)
    (sigma : External -> External)
    (hinv : ResponseInvisibleRelabelling G sigma) :
    OperationalGrounding System External Probe Outcome where
  cost := G.cost
  systemResponse := G.systemResponse
  externalResponse := G.externalResponse
  realizes := fun system external => G.realizes system (sigma external)
  calibration := by
    intro system external hrealizes probe
    exact (G.calibration system (sigma external) hrealizes probe).trans
      (hinv external probe)

/-- Two externally distinct interpretations can therefore induce exactly
    the same operational data and both satisfy calibration. This is the
    precise residual gauge freedom that an independent anchor must break. -/
theorem calibration_does_not_fix_invisible_external_labels
    {System : Type u} {External : Type v} {Probe : Type w} {Outcome : Type x}
    (G : OperationalGrounding System External Probe Outcome)
    (sigma : External -> External)
    (hinv : ResponseInvisibleRelabelling G sigma)
    {system : System} {external : External}
    (hrealizes : G.realizes system (sigma external))
    (hmoves : sigma external ≠ external) :
    (reindexGrounding G sigma hinv).realizes system external /\
    (G.realizes system (sigma external)) /\
    (forall probe,
      (reindexGrounding G sigma hinv).systemResponse system probe =
        G.systemResponse system probe) /\
    (forall probe,
      (reindexGrounding G sigma hinv).externalResponse external probe =
        G.externalResponse external probe) /\
    (external ≠ sigma external) := by
  exact ⟨hrealizes, hrealizes, fun _ => rfl, fun _ => rfl, hmoves.symm⟩

/-- A probe family may be perfectly calibrated and still permanently miss
    a semantic coordinate. The hidden second bit is never observable. -/
def hiddenCoordinateGrounding :
    OperationalGrounding (Bool × Bool) (Bool × Bool) Bool Bool where
  cost := fun probe => if probe then 1 else 0
  systemResponse := fun system probe => if probe then system.1 else false
  externalResponse := fun external probe => if probe then external.1 else false
  realizes := fun system external => system.1 = external.1
  calibration := by
    intro system external hrealizes probe
    cases probe <;> simp [hrealizes]

theorem hiddenCoordinate_profiles_equal
    (budget : Nat) :
    ExternalProfileAt hiddenCoordinateGrounding budget (false, false) =
      ExternalProfileAt hiddenCoordinateGrounding budget (false, true) := by
  funext probe
  cases probe.1 <;> rfl

theorem hiddenCoordinate_never_separates
    (budget : Nat) :
    ¬ SeparatesAt hiddenCoordinateGrounding budget := by
  intro hsep
  obtain ⟨probe, _hcost, hdist⟩ :=
    hsep (false, false) (false, true) (by decide)
  exact hdist (by cases probe <;> rfl)

end Cerp.OperationalGroundingAdequacy


namespace Cerp.OperationalGroundingAdequacy

universe u v w x y

/-- An independently supplied anchor contributes an external datum for each
    target. It is deliberately not computed from the operational profile. -/
def AnchoredProfile
    {System : Type u} {External : Type v} {Probe : Type w} {Outcome : Type x}
    {Anchor : Type y}
    (G : OperationalGrounding System External Probe Outcome)
    (budget : Nat) (anchor : External -> Anchor) (external : External) :=
  (ExternalProfileAt G budget external, anchor external)

/-- The exact adequacy condition for an external anchor: it need only
    distinguish pairs that the operational profile fails to distinguish. -/
def AnchorSeparatesResidualAmbiguity
    {System : Type u} {External : Type v} {Probe : Type w} {Outcome : Type x}
    {Anchor : Type y}
    (G : OperationalGrounding System External Probe Outcome)
    (budget : Nat) (anchor : External -> Anchor) : Prop :=
  forall e e',
    ExternalProfileAt G budget e = ExternalProfileAt G budget e' ->
    anchor e = anchor e' -> e = e'

/-- The combined operational profile and independent anchor are injective
    exactly when the anchor separates all residual profile ambiguities. -/
theorem anchoredProfile_injective_iff_anchor_separates_residual
    {System : Type u} {External : Type v} {Probe : Type w} {Outcome : Type x}
    {Anchor : Type y}
    (G : OperationalGrounding System External Probe Outcome)
    (budget : Nat) (anchor : External -> Anchor) :
    (forall e e',
      AnchoredProfile G budget anchor e =
        AnchoredProfile G budget anchor e' -> e = e') <->
    AnchorSeparatesResidualAmbiguity G budget anchor := by
  constructor
  · intro hinj e e' hprofile hanchor
    apply hinj
    exact Prod.ext hprofile hanchor
  · intro hanchor e e' hcombined
    exact hanchor e e' (congrArg Prod.fst hcombined)
      (congrArg Prod.snd hcombined)

/-- An independently validated anchor removes every invisible symmetry
    that it separates. The anchor need not encode distinctions already
    resolved by operational probes. -/
theorem anchor_breaks_invisible_symmetry
    {System : Type u} {External : Type v} {Probe : Type w} {Outcome : Type x}
    {Anchor : Type y}
    (G : OperationalGrounding System External Probe Outcome)
    (sigma : External -> External)
    (hinv : ResponseInvisibleRelabelling G sigma)
    (budget : Nat) (anchor : External -> Anchor)
    (hanchor : AnchorSeparatesResidualAmbiguity G budget anchor)
    (external : External)
    (hmoves : sigma external ≠ external) :
    anchor (sigma external) ≠ anchor external := by
  intro heq
  apply hmoves
  apply hanchor (sigma external) external
  · exact invisible_symmetry_preserves_profile G sigma hinv budget external
  · exact heq

end Cerp.OperationalGroundingAdequacy


namespace Cerp.OperationalGroundingAdequacy

universe u v w x

/-- An external truth predicate is profile-observable precisely when it is
    constant on all pairs that affordable probes cannot distinguish. -/
def ProfileObservable
    {System : Type u} {External : Type v} {Probe : Type w} {Outcome : Type x}
    (G : OperationalGrounding System External Probe Outcome)
    (budget : Nat) (truth : External -> Prop) : Prop :=
  forall e e',
    ExternalProfileAt G budget e = ExternalProfileAt G budget e' ->
    (truth e ↔ truth e')

def hiddenCoordinateTruth (external : Bool × Bool) : Prop :=
  external.2 = true

/-- A perfectly calibrated operational model can fail to identify even a
    binary truth predicate about its external target, at every budget. -/
theorem hiddenCoordinate_truth_not_profile_observable
    (budget : Nat) :
    ¬ ProfileObservable hiddenCoordinateGrounding budget
      hiddenCoordinateTruth := by
  intro hobs
  have hiff := hobs (false, false) (false, true)
    (hiddenCoordinate_profiles_equal budget)
  have hfalse : (false, false).2 = true := hiff.mpr rfl
  cases hfalse

end Cerp.OperationalGroundingAdequacy


namespace Cerp.OperationalGroundingAdequacy

universe u v w x y z

/-- An anchor computed only from the operational profile cannot resolve
    any ambiguity already present in that profile. Genuine gauge fixing
    requires information not functionally determined by the profile. -/
theorem profile_derived_anchor_cannot_break_ambiguity
    {System : Type u} {External : Type v} {Probe : Type w} {Outcome : Type x}
    {Anchor : Type y}
    (G : OperationalGrounding System External Probe Outcome)
    (budget : Nat)
    (decode : ({probe : Probe // G.cost probe <= budget} -> Outcome) -> Anchor)
    {e e' : External}
    (hprofile : ExternalProfileAt G budget e =
      ExternalProfileAt G budget e')
    (hdistinct : e ≠ e') :
    ¬ AnchorSeparatesResidualAmbiguity G budget
      (fun external => decode (ExternalProfileAt G budget external)) := by
  intro hanchor
  apply hdistinct
  apply hanchor e e'
  · exact hprofile
  · exact congrArg decode hprofile

end Cerp.OperationalGroundingAdequacy
