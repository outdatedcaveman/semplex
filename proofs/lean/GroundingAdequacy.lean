import CausalRealization

/-!
# Grounding adequacy: separation, descent, and impossibility

A profile decoder can recover an external referent only if the declared
probe family separates every pair of histories with distinct referents.
An external truth predicate descends to the observational quotient exactly
when it is invariant under observational equivalence.

These are conditional mathematical results. They do not establish that a
chosen probe family is physically adequate; that requires independent
operational calibration.
-/

namespace Cerp.GroundingAdequacy

open Cerp.CausalRealization

universe u v w x
variable {History : Type u} {Test : Type v} {Outcome : Type w}

theorem profile_eq_of_equivalent
    (F : TestFamily History Test Outcome) (b : Nat)
    {h h' : History} (heq : equivalent F b h h') :
    profile F b h = profile F b h' := by
  funext t
  exact heq t

theorem profile_decoder_respects_equivalence
    (F : TestFamily History Test Outcome) (b : Nat)
    {Z : Type x} (decode : (Affordable F b -> Outcome) -> Z)
    {h h' : History} (heq : equivalent F b h h') :
    decode (profile F b h) = decode (profile F b h') :=
  congrArg decode (profile_eq_of_equivalent F b heq)

def ExactReferentDecoder
    (F : TestFamily History Test Outcome) (b : Nat)
    (External : Type x) (referent : History -> External)
    (decode : (Affordable F b -> Outcome) -> External) : Prop :=
  forall h, decode (profile F b h) = referent h

theorem no_exact_referent_decoder
    (F : TestFamily History Test Outcome) (b : Nat)
    (External : Type x) (referent : History -> External)
    {h h' : History}
    (hobs : equivalent F b h h')
    (href : referent h ≠ referent h') :
    forall decode : (Affordable F b -> Outcome) -> External,
      ¬ ExactReferentDecoder F b External referent decode := by
  intro decode hexact
  have hdecoded := profile_decoder_respects_equivalence F b decode hobs
  have hsame : referent h = referent h' := by
    calc
      referent h = decode (profile F b h) := (hexact h).symm
      _ = decode (profile F b h') := hdecoded
      _ = referent h' := hexact h'
  exact href hsame

def ReferentObservable
    (F : TestFamily History Test Outcome) (b : Nat)
    (External : Type x) (referent : History -> External) : Prop :=
  forall h h', equivalent F b h h' -> referent h = referent h'

def quotientReferent
    (F : TestFamily History Test Outcome) (b : Nat)
    (External : Type x) (referent : History -> External)
    (hinv : ReferentObservable F b External referent) :
    Quotient (budgetSetoid F b) -> External :=
  Quotient.lift referent (by
    intro h h' heq
    exact hinv h h' heq)

@[simp] theorem quotientReferent_mk
    (F : TestFamily History Test Outcome) (b : Nat)
    (External : Type x) (referent : History -> External)
    (hinv : ReferentObservable F b External referent) (h : History) :
    quotientReferent F b External referent hinv
      (Quotient.mk (budgetSetoid F b) h) = referent h := rfl

theorem referent_descends_iff_observable
    (F : TestFamily History Test Outcome) (b : Nat)
    (External : Type x) (referent : History -> External) :
    (exists Q : Quotient (budgetSetoid F b) -> External,
      forall h, Q (Quotient.mk (budgetSetoid F b) h) = referent h) <->
    ReferentObservable F b External referent := by
  constructor
  · rintro ⟨Q, hQ⟩ h h' heq
    have hquot :
        Quotient.mk (budgetSetoid F b) h =
          Quotient.mk (budgetSetoid F b) h' :=
      Quotient.sound heq
    calc
      referent h = Q (Quotient.mk (budgetSetoid F b) h) := (hQ h).symm
      _ = Q (Quotient.mk (budgetSetoid F b) h') := congrArg Q hquot
      _ = referent h' := hQ h'
  · intro hinv
    refine ⟨quotientReferent F b External referent hinv, ?_⟩
    intro h
    rfl

def TruthObservable
    (F : TestFamily History Test Outcome) (b : Nat)
    (truth : History -> Prop) : Prop :=
  forall h h', equivalent F b h h' -> (truth h <-> truth h')

def quotientTruth
    (F : TestFamily History Test Outcome) (b : Nat)
    (truth : History -> Prop)
    (hinv : TruthObservable F b truth) :
    Quotient (budgetSetoid F b) -> Prop :=
  Quotient.lift truth (by
    intro h h' heq
    exact propext (hinv h h' heq))

@[simp] theorem quotientTruth_mk
    (F : TestFamily History Test Outcome) (b : Nat)
    (truth : History -> Prop)
    (hinv : TruthObservable F b truth) (h : History) :
    quotientTruth F b truth hinv
      (Quotient.mk (budgetSetoid F b) h) = truth h := rfl

theorem quotient_predicate_observable
    (F : TestFamily History Test Outcome) (b : Nat)
    (Q : Quotient (budgetSetoid F b) -> Prop) :
    TruthObservable F b (fun h => Q (Quotient.mk (budgetSetoid F b) h)) := by
  intro h h' heq
  have hquot :
      Quotient.mk (budgetSetoid F b) h =
        Quotient.mk (budgetSetoid F b) h' :=
    Quotient.sound heq
  change Q (Quotient.mk (budgetSetoid F b) h) ↔
    Q (Quotient.mk (budgetSetoid F b) h')
  exact Iff.of_eq (congrArg Q hquot)

theorem truth_descends_iff_observable
    (F : TestFamily History Test Outcome) (b : Nat)
    (truth : History -> Prop) :
    (exists Q : Quotient (budgetSetoid F b) -> Prop,
      forall h, Q (Quotient.mk (budgetSetoid F b) h) <-> truth h) <->
    TruthObservable F b truth := by
  constructor
  · rintro ⟨Q, hQ⟩ h h' heq
    have hquot :
        Quotient.mk (budgetSetoid F b) h =
          Quotient.mk (budgetSetoid F b) h' :=
      Quotient.sound heq
    have hQeq :
        Q (Quotient.mk (budgetSetoid F b) h) =
          Q (Quotient.mk (budgetSetoid F b) h') :=
      congrArg Q hquot
    exact (hQ h).symm.trans ((Iff.of_eq hQeq).trans (hQ h'))
  · intro hinv
    refine ⟨quotientTruth F b truth hinv, ?_⟩
    intro h
    rfl

end Cerp.GroundingAdequacy


namespace Cerp.GroundingAdequacy

open Cerp.CausalRealization
universe u v w
variable {History : Type u} {Test : Type v} {Outcome : Type w}

/-- Observational equivalence is exactly equality of the complete
    resource-bounded response profiles. -/
theorem equivalent_iff_profile_eq
    (F : TestFamily History Test Outcome) (b : Nat)
    (h h' : History) :
    equivalent F b h h' ↔ profile F b h = profile F b h' := by
  constructor
  · exact profile_eq_of_equivalent F b
  · intro heq t
    exact congrFun heq t

end Cerp.GroundingAdequacy
