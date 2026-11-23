import SemanticYoneda

/-!
# Ordinary institution interface

A formal interface for syntax/model/satisfaction invariance under
signature translation. This is established institution theory, not a
novel result. It supplies a baseline that the grounded higher framework
must extend rather than reinvent.
-/

namespace Cerp.InstitutionalSemantics

open Cerp.SemanticYoneda.GeneralCategory

universe u v w x

structure Institution where
  Sign : SemCategory.{u,v}
  Sentence : Sign.Obj -> Type w
  Model : Sign.Obj -> Type x
  sentenceMap : forall {sigma tau}, Sign.Hom sigma tau ->
    Sentence sigma -> Sentence tau
  reduct : forall {sigma tau}, Sign.Hom sigma tau ->
    Model tau -> Model sigma
  sentence_id : forall (sigma : Sign.Obj) (phi : Sentence sigma),
    sentenceMap (Sign.id sigma) phi = phi
  sentence_comp : forall {sigma tau upsilon : Sign.Obj}
    (f : Sign.Hom sigma tau) (g : Sign.Hom tau upsilon)
    (phi : Sentence sigma),
    sentenceMap (Sign.comp f g) phi =
      sentenceMap g (sentenceMap f phi)
  reduct_id : forall (sigma : Sign.Obj) (M : Model sigma),
    reduct (Sign.id sigma) M = M
  reduct_comp : forall {sigma tau upsilon : Sign.Obj}
    (f : Sign.Hom sigma tau) (g : Sign.Hom tau upsilon)
    (M : Model upsilon),
    reduct (Sign.comp f g) M =
      reduct f (reduct g M)
  satisfies : forall sigma, Model sigma -> Sentence sigma -> Prop
  satisfaction_condition : forall {sigma tau : Sign.Obj}
    (f : Sign.Hom sigma tau) (M : Model tau) (phi : Sentence sigma),
    satisfies tau M (sentenceMap f phi) <->
      satisfies sigma (reduct f M) phi

/-- The defining satisfaction condition of an institution. -/
theorem satisfaction_transport (I : Institution)
    {sigma tau : I.Sign.Obj} (f : I.Sign.Hom sigma tau)
    (M : I.Model tau) (phi : I.Sentence sigma) :
    I.satisfies tau M (I.sentenceMap f phi) <->
      I.satisfies sigma (I.reduct f M) phi :=
  I.satisfaction_condition f M phi

/-- Satisfaction transport along a composite signature translation
    agrees with transport in two stages. -/
theorem satisfaction_composite (I : Institution)
    {sigma tau upsilon : I.Sign.Obj}
    (f : I.Sign.Hom sigma tau) (g : I.Sign.Hom tau upsilon)
    (M : I.Model upsilon) (phi : I.Sentence sigma) :
    I.satisfies upsilon M
        (I.sentenceMap (I.Sign.comp f g) phi) <->
      I.satisfies sigma
        (I.reduct f (I.reduct g M)) phi := by
  rw [I.sentence_comp]
  exact (I.satisfaction_condition g M (I.sentenceMap f phi)).trans
    (I.satisfaction_condition f (I.reduct g M) phi)

/-- Every institution yields a semantics profile of sentences across
    all models of the same signature. -/
def truthProfile (I : Institution) (sigma : I.Sign.Obj)
    (phi : I.Sentence sigma) : I.Model sigma -> Prop :=
  fun M => I.satisfies sigma M phi

end Cerp.InstitutionalSemantics
