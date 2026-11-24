import InstitutionalSemantics
import OperationalSatisfaction

/-!
# Operational reference and satisfaction as an institution

Packages `Cerp.OperationalSatisfaction` as an instance of `Cerp.InstitutionalSemantics.Institution`
over the resource-budget preorder category (`Nat`, `b1 <= b2`), giving an exact kernel-checked
bridge between abstract institution satisfaction invariance and operational budget refinement.
-/

namespace Cerp.OperationalInstitutionBridge

open Cerp.SemanticYoneda.GeneralCategory
open Cerp.InstitutionalSemantics
open Cerp.OperationalSemioticScaffold
open Cerp.InterventionGrounding
open Cerp.OperationalReference
open Cerp.OperationalSatisfaction

universe u v w x y

/-- Small thin category of resource budgets ordered by `<=`. -/
def budgetCategory : SemCategory.{0, 0} where
  Obj := Nat
  Hom := fun b1 b2 => PLift (b1 <= b2)
  id := fun b => PLift.up (Nat.le_refl b)
  comp := fun f g => PLift.up (Nat.le_trans f.down g.down)
  id_comp := by
    intro a b f
    cases f
    rfl
  comp_id := by
    intro a b f
    cases f
    rfl
  assoc := by
    intro a b c d f g h
    cases f
    cases g
    cases h
    rfl

/-- An operational intervention protocol induces a budget-indexed institution whose
    sentences are budget-admissible observable claims and whose models are quotient
    operational referent spaces. -/
def operationalInstitution
    {S : OperationalScaffold.{u, v, w, x, y}}
    (P : InterventionProtocol S) :
    Institution.{0, 0, u, u} where
  Sign := budgetCategory
  Sentence := fun b => ObservableClaim P b
  Model := fun b => ReferentSpace P b
  sentenceMap := fun h phi => refineClaim P h.down phi
  reduct := fun h M => forgetReferent P h.down M
  sentence_id := by
    intro b phi
    cases phi
    rfl
  sentence_comp := by
    intro b1 b2 b3 f g phi
    cases phi
    rfl
  reduct_id := by
    intro b M
    refine Quotient.inductionOn M ?_
    intro world
    rfl
  reduct_comp := by
    intro b1 b2 b3 f g M
    refine Quotient.inductionOn M ?_
    intro world
    rfl
  satisfies := fun b M phi => satisfaction P b phi M
  satisfaction_condition := by
    intro b1 b2 f M phi
    exact satisfaction_forget P f.down phi M

/-- Satisfaction transport in the operational institution specializes cleanly to
    budget forgetting along `b1 <= b2`. -/
theorem operational_satisfaction_transport
    {S : OperationalScaffold.{u, v, w, x, y}}
    (P : InterventionProtocol S)
    {b1 b2 : Nat} (hle : b1 <= b2)
    (M : ReferentSpace P b2) (phi : ObservableClaim P b1) :
    (operationalInstitution P).satisfies b2 M
        ((operationalInstitution P).sentenceMap (PLift.up hle) phi) <->
      (operationalInstitution P).satisfies b1
        ((operationalInstitution P).reduct (PLift.up hle) M) phi :=
  satisfaction_transport (operationalInstitution P) (PLift.up hle) M phi

/-- Concrete witness instantiating `revealProtocol` into the operational institution:
    revealing the hidden bit at budget `1` satisfies the invariant claim whose
    expression is forbidden at budget `0`. -/
theorem revealProtocol_institution_witness :
    (operationalInstitution revealProtocol).satisfies (1 : Nat)
      (Quotient.mk (worldSetoid revealProtocol 1) (true, false))
      hiddenBitObservableAtOne := by
  change satisfaction revealProtocol 1 hiddenBitObservableAtOne
    (Quotient.mk (worldSetoid revealProtocol 1) (true, false))
  rw [satisfaction_mk]
  rfl

end Cerp.OperationalInstitutionBridge
