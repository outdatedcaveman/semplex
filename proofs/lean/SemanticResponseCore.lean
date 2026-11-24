import ResponseQuotient

namespace Cerp.SemanticResponseCore

universe u v w x

structure ProbeSemantics (S : Type u) (P : Type v) (R : Type w) where
  response : P -> S -> R

def semEq {S : Type u} {P : Type v} {R : Type w}
    (M : ProbeSemantics S P R) (s t : S) : Prop :=
  forall p, M.response p s = M.response p t

theorem semEq_refl {S : Type u} {P : Type v} {R : Type w}
    (M : ProbeSemantics S P R) : forall s, semEq M s s := by
  intro s p
  rfl

theorem semEq_symm {S : Type u} {P : Type v} {R : Type w}
    (M : ProbeSemantics S P R) : forall {s t}, semEq M s t -> semEq M t s := by
  intro s t h p
  exact (h p).symm

theorem semEq_trans {S : Type u} {P : Type v} {R : Type w}
    (M : ProbeSemantics S P R) :
    forall {s t u'}, semEq M s t -> semEq M t u' -> semEq M s u' := by
  intro s t u' hst htu p
  exact (hst p).trans (htu p)

def semanticSetoid {S : Type u} {P : Type v} {R : Type w}
    (M : ProbeSemantics S P R) : Setoid S where
  r := semEq M
  iseqv := {
    refl := semEq_refl M
    symm := semEq_symm M
    trans := semEq_trans M
  }

def responseProfile {S : Type u} {P : Type v} {R : Type w}
    (M : ProbeSemantics S P R) : S -> P -> R :=
  fun s p => M.response p s

theorem semEq_iff_responseProfile_eq {S : Type u} {P : Type v} {R : Type w}
    (M : ProbeSemantics S P R) (s t : S) :
    semEq M s t <-> responseProfile M s = responseProfile M t := by
  constructor
  · intro h
    funext p
    exact h p
  · intro h p
    exact congrFun h p

def SeparatingProbes {S : Type u} {P : Type v} {R : Type w}
    (M : ProbeSemantics S P R) : Prop :=
  forall s t, semEq M s t -> s = t

structure ExactRealization {S : Type u} {P : Type v} {R : Type w}
    (M : ProbeSemantics S P R) (Z : Type x) where
  encode : S -> Z
  decode : P -> Z -> R
  adequate : forall p s, decode p (encode s) = M.response p s

theorem encoding_collision_implies_semEq
    {S : Type u} {P : Type v} {R : Type w} {Z : Type x}
    (M : ProbeSemantics S P R) (E : ExactRealization M Z)
    {s t : S} (h : E.encode s = E.encode t) :
    semEq M s t := by
  intro p
  calc
    M.response p s = E.decode p (E.encode s) := (E.adequate p s).symm
    _ = E.decode p (E.encode t) := by rw [h]
    _ = M.response p t := E.adequate p t

def Injective {S : Type u} {Z : Type v} (f : S -> Z) : Prop :=
  forall {s t}, f s = f t -> s = t

theorem exact_realization_injective
    {S : Type u} {P : Type v} {R : Type w} {Z : Type x}
    (M : ProbeSemantics S P R) (E : ExactRealization M Z)
    (hsep : SeparatingProbes M) :
    Injective E.encode := by
  intro s t h
  exact hsep s t (encoding_collision_implies_semEq M E h)

structure Dynamics (S : Type u) (A : Type v) where
  step : S -> A -> S

structure DynamicRealization {S : Type u} {Z : Type v} {A : Type w}
    (T : Dynamics S A) where
  encode : S -> Z
  update : Z -> A -> Z
  commutes : forall s a, encode (T.step s a) = update (encode s) a

def runTarget {S : Type u} {A : Type v} (T : Dynamics S A)
    (s : S) (actions : List A) : S :=
  actions.foldl (fun state a => T.step state a) s

def runImplementation {S : Type u} {Z : Type v} {A : Type w}
    {T : Dynamics S A} (E : DynamicRealization (Z := Z) T)
    (z : Z) (actions : List A) : Z :=
  actions.foldl (fun state a => E.update state a) z

theorem DynamicRealization.commutes_list
    {S : Type u} {Z : Type v} {A : Type w}
    {T : Dynamics S A} (E : DynamicRealization (Z := Z) T) :
    forall (s : S) (actions : List A),
      E.encode (runTarget T s actions) =
        runImplementation E (E.encode s) actions := by
  intro s actions
  induction actions generalizing s with
  | nil => rfl
  | cons a rest ih =>
      change E.encode (runTarget T (T.step s a) rest) =
        runImplementation E (E.update (E.encode s) a) rest
      have hcomm : E.encode (T.step s a) = E.update (E.encode s) a :=
        E.commutes s a
      calc
        E.encode (runTarget T (T.step s a) rest) =
            runImplementation E (E.encode (T.step s a)) rest := ih (T.step s a)
        _ = runImplementation E (E.update (E.encode s) a) rest := by rw [hcomm]

structure SatisfactionModel (S : Type u) (C : Type v) where
  satisfies : C -> S -> Prop

structure EvidenceSystem (C : Type u) where
  Evidence : C -> Type v

def SoundEvidence {S : Type u} {C : Type v}
    (M : SatisfactionModel S C) (E : EvidenceSystem C) : Prop :=
  forall c s, E.Evidence c -> M.satisfies c s

def CompleteEvidence {S : Type u} {C : Type v}
    (M : SatisfactionModel S C) (E : EvidenceSystem C) : Prop :=
  forall c, (forall s, M.satisfies c s) -> Nonempty (E.Evidence c)

theorem evidence_soundness
    {S : Type u} {C : Type v}
    (M : SatisfactionModel S C) (E : EvidenceSystem C)
    (hsound : SoundEvidence M E)
    {c : C} {s : S} (ev : E.Evidence c) :
    M.satisfies c s :=
  hsound c s ev

end Cerp.SemanticResponseCore
