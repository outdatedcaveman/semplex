import InterventionGrounding

/-!
# Operational reference as a resource-relative moduli relation

Referents are equivalence classes of world states under the available
intervention-response profile. A sign may relate to multiple referent
classes when current observations do not determine a unique target.
-/

namespace Cerp.OperationalReference

open Cerp.InterventionGrounding
open Cerp.OperationalSemioticScaffold

universe u v w x y

variable {S : OperationalScaffold.{u,v,w,x,y}}

/-- World states indistinguishable under a budgeted intervention protocol. -/
def worldSetoid (P : InterventionProtocol S) (budget : Nat) : Setoid S.World where
  r := experimentEquivalent P budget
  iseqv := {
    refl := experimentEquivalent_refl P budget
    symm := fun h => experimentEquivalent_symm P budget h
    trans := fun h1 h2 => experimentEquivalent_trans P budget h1 h2
  }

/-- The space of operational referents at budget B. -/
abbrev ReferentSpace (P : InterventionProtocol S) (budget : Nat) :=
  Quotient (worldSetoid P budget)

/-- A sign operationally refers to a referent class when some world
    representative of that class produces the sign. -/
def operationalReference (P : InterventionProtocol S) (budget : Nat)
    (sign : S.Sign) (q : ReferentSpace P budget) : Prop :=
  exists world, Quotient.mk (worldSetoid P budget) world = q /\
    S.sense world = sign

/-- A larger budget has a canonical map to the coarser referent space. -/
def forgetReferent (P : InterventionProtocol S) {b1 b2 : Nat}
    (hle : b1 <= b2) :
    ReferentSpace P b2 -> ReferentSpace P b1 :=
  Quotient.lift
    (fun world => Quotient.mk (worldSetoid P b1) world)
    (by
      intro w1 w2 h
      exact Quotient.sound (experimentEquivalent_antitone P hle h))

@[simp] theorem forgetReferent_mk (P : InterventionProtocol S)
    {b1 b2 : Nat} (hle : b1 <= b2) (world : S.World) :
    forgetReferent P hle
      (Quotient.mk (worldSetoid P b2) world) =
        Quotient.mk (worldSetoid P b1) world := rfl

/-- Operational reference is preserved when a richer referent class is
    forgotten to a coarser, lower-budget class. -/
theorem reference_forget_monotone (P : InterventionProtocol S)
    {b1 b2 : Nat} (hle : b1 <= b2) (sign : S.Sign)
    (q : ReferentSpace P b2)
    (h : operationalReference P b2 sign q) :
    operationalReference P b1 sign (forgetReferent P hle q) := by
  rcases h with ⟨world, hq, hs⟩
  refine ⟨world, ?_, hs⟩
  have hq' := congrArg (forgetReferent P hle) hq
  simpa using hq'

/-- At budget zero, the two hidden worlds occupy the same referent class. -/
theorem hidden_referents_coincide_at_zero :
    (Quotient.mk (worldSetoid revealProtocol 0) (false, false) :
      ReferentSpace revealProtocol 0) =
    Quotient.mk (worldSetoid revealProtocol 0) (true, false) :=
  Quotient.sound hidden_worlds_indistinguishable_at_zero

/-- At budget one, the same two worlds are distinct referent classes. -/
theorem hidden_referents_separate_at_one :
    (Quotient.mk (worldSetoid revealProtocol 1) (false, false) :
      ReferentSpace revealProtocol 1) ≠
    Quotient.mk (worldSetoid revealProtocol 1) (true, false) := by
  intro heq
  exact reveal_intervention_separates (Quotient.exact heq)

/-- The same observed sign can relate to two distinct operational referents
    once the intervention family is rich enough. Thus reference need not be
    a function from signs to unique worlds. -/
theorem one_sign_two_referents_at_budget_one :
    exists q1 q2 : ReferentSpace revealProtocol 1,
      q1 ≠ q2 /\
      operationalReference revealProtocol 1 false q1 /\
      operationalReference revealProtocol 1 false q2 := by
  let q1 : ReferentSpace revealProtocol 1 :=
    Quotient.mk (worldSetoid revealProtocol 1) (false, false)
  let q2 : ReferentSpace revealProtocol 1 :=
    Quotient.mk (worldSetoid revealProtocol 1) (true, false)
  refine ⟨q1, q2, ?_, ?_, ?_⟩
  · exact hidden_referents_separate_at_one
  · exact ⟨(false, false), rfl, rfl⟩
  · exact ⟨(true, false), rfl, rfl⟩

/-- Every budgeted observational equivalence preserves the current sensor
    output, since the empty intervention is always affordable. -/
theorem equivalent_same_current_sign (P : InterventionProtocol S)
    (budget : Nat) {w1 w2 : S.World}
    (h : experimentEquivalent P budget w1 w2) :
    S.sense w1 = S.sense w2 := by
  have htrace := h [] (by simp [experimentCost])
  simpa [experimentTrace] using htrace

/-- The current sensor output is independent of the representative chosen
    from an operational referent class. -/
theorem operationalReference_representative_invariant
    (P : InterventionProtocol S) (budget : Nat)
    (q : ReferentSpace P budget)
    (w1 w2 : S.World)
    (h1 : Quotient.mk (worldSetoid P budget) w1 = q)
    (h2 : Quotient.mk (worldSetoid P budget) w2 = q) :
    S.sense w1 = S.sense w2 := by
  have hquot : Quotient.mk (worldSetoid P budget) w1 =
      Quotient.mk (worldSetoid P budget) w2 := h1.trans h2.symm
  exact equivalent_same_current_sign P budget (Quotient.exact hquot)

/-- Once a sign refers to a quotient class, every representative of that
    class produces that same sign. The existential definition of reference
    is therefore representative-independent. -/
theorem operationalReference_all_representatives
    (P : InterventionProtocol S) (budget : Nat) (sign : S.Sign)
    (q : ReferentSpace P budget)
    (href : operationalReference P budget sign q) :
    forall world, Quotient.mk (worldSetoid P budget) world = q ->
      S.sense world = sign := by
  rcases href with ⟨witness, hclass, hsign⟩
  intro world hworld
  have hsame := operationalReference_representative_invariant
    P budget q witness world hclass hworld
  exact hsame.symm.trans hsign

end Cerp.OperationalReference

