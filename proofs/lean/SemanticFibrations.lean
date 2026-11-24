import HigherSemanticCore

namespace Cerp.SemanticFibrations

universe u v w x

/-- Typed world, sign, claim, and context domains. Reference is relational. -/
structure GroundedSemiosis where
  World : Type u
  Sign : Type v
  Claim : Type w
  Context : Type x
  refers : Sign -> World -> Prop
  expresses : Sign -> Context -> Claim
  satisfies : Claim -> World -> Prop
  Evidence : Sign -> Context -> World -> Type
  evidence_sound : forall s c w, refers s w -> Evidence s c w -> satisfies (expresses s c) w

/-- Content truth is model satisfaction; it does not itself assert that a
    particular sign is about the evaluated world. -/
def ContentTrue (M : GroundedSemiosis) (s : M.Sign) (c : M.Context) (w : M.World) : Prop :=
  M.satisfies (M.expresses s c) w

/-- Grounded assertion truth combines content satisfaction with the
    independently specified aboutness/reference relation. -/
def GroundedAssertionTrue (M : GroundedSemiosis) (s : M.Sign)
    (c : M.Context) (w : M.World) : Prop :=
  And (M.refers s w) (ContentTrue M s c w)

abbrev AssertionTrue := GroundedAssertionTrue

def EvidentiallySupported (M : GroundedSemiosis) (s : M.Sign) (c : M.Context) (w : M.World) : Prop :=
  Nonempty (M.Evidence s c w)

theorem evidence_yields_assertion_truth (M : GroundedSemiosis) (s : M.Sign) (c : M.Context) (w : M.World)
    (href : M.refers s w) (hev : M.Evidence s c w) : GroundedAssertionTrue M s c w :=
  And.intro href (M.evidence_sound s c w href hev)

def UniquelyRefers (M : GroundedSemiosis) (s : M.Sign) : Prop :=
  Exists (fun w => And (M.refers s w) (forall w', M.refers s w' -> w' = w))

def trueWithoutEvidence : GroundedSemiosis where
  World := Unit
  Sign := Unit
  Claim := Unit
  Context := Unit
  refers := fun _ _ => True
  expresses := fun _ _ => ()
  satisfies := fun _ _ => True
  Evidence := fun _ _ _ => Empty
  evidence_sound := by intro s c w href hev; cases hev

theorem truth_need_not_imply_evidence :
    And (GroundedAssertionTrue trueWithoutEvidence () () ())
      (Not (EvidentiallySupported trueWithoutEvidence () () ())) := by
  constructor
  · exact And.intro trivial trivial
  · intro h
    rcases h with ⟨ev⟩
    cases ev

def trueButUnreferenced : GroundedSemiosis where
  World := Unit
  Sign := Unit
  Claim := Unit
  Context := Unit
  refers := fun _ _ => False
  expresses := fun _ _ => ()
  satisfies := fun _ _ => True
  Evidence := fun _ _ _ => Empty
  evidence_sound := by intro s c w href hev; cases href

theorem satisfaction_need_not_imply_reference :
    And (ContentTrue trueButUnreferenced () () ())
      (Not (trueButUnreferenced.refers () ())) := by
  constructor
  · trivial
  · intro h
    exact h

end Cerp.SemanticFibrations
