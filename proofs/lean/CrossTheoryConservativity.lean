import SemanticFibrations
import InstitutionalSemantics

/-!
# Cross-theory signature conservativity and T4/T7 incompatibility (T7)

Embeds three heterogeneous source-theory semantics into `GroundedSemiosis`:
1. Classical Tarskian Boolean-valued satisfaction (`TarskiModel`)
2. Intuitionistic Kripke evidential forcing (`HeytingKripkeModel`)
3. Causal intervention observation (`CausalTraceModel`)

Proves joint conservativity on shared atomic observational signatures (Sigma),
and proves the Revised-T7 / T4 no-go theorem: requiring classical excluded
middle (P or not P) inside the shared signature breaks joint conservativity
because an intuitionistic Kripke root lacks evidential warrant for either branch.
-/

namespace Cerp.CrossTheoryConservativity

open Cerp.SemanticFibrations

inductive Formula (Atom : Type) where
  | atom : Atom -> Formula Atom
  | neg : Formula Atom -> Formula Atom
  | disj : Formula Atom -> Formula Atom -> Formula Atom
  deriving DecidableEq

/-- Classical finite/decidable Boolean-world Tarski evaluation. -/
def tarskiEvalBool {Atom : Type} (val : Atom -> Bool) : Formula Atom -> Bool
  | .atom a => val a
  | .neg p => !(tarskiEvalBool val p)
  | .disj p q => (tarskiEvalBool val p) || (tarskiEvalBool val q)

theorem tarski_lem_always_holds {Atom : Type} (val : Atom -> Bool) (p : Formula Atom) :
    tarskiEvalBool val (.disj p (.neg p)) = true := by
  simp [tarskiEvalBool]

/-- Grounded semiosis embedding for a classical Tarski model over `World`. -/
def tarskiSemiosis (World Atom : Type) (val : World -> Atom -> Bool) :
    GroundedSemiosis where
  World := World
  Sign := Atom
  Claim := Formula Atom
  Context := Unit
  refers := fun _ _ => True
  expresses := fun a _ => .atom a
  satisfies := fun phi w => tarskiEvalBool (val w) phi = true
  Evidence := fun _ _ _ => Empty
  evidence_sound := by intro _ _ _ _ hev; cases hev

/-- Intuitionistic Kripke preorder model with monotone atomic forcing. -/
structure KripkeModel (Node Atom : Type) where
  le : Node -> Node -> Prop
  le_refl : forall k, le k k
  le_trans : forall k1 k2 k3, le k1 k2 -> le k2 k3 -> le k1 k3
  atomTrue : Node -> Atom -> Prop
  monotone : forall k1 k2 a, le k1 k2 -> atomTrue k1 a -> atomTrue k2 a

def kripkeForces {Node Atom : Type} (M : KripkeModel Node Atom) :
    Node -> Formula Atom -> Prop
  | k, .atom a => M.atomTrue k a
  | k, .neg p => forall k', M.le k k' -> Not (kripkeForces M k' p)
  | k, .disj p q => Or (kripkeForces M k p) (kripkeForces M k q)

/-- Grounded semiosis embedding for an intuitionistic Kripke model:
    evidential warrant at node `k` requires constructive forcing at `k`. -/
def heytingSemiosis {Node Atom : Type} (M : KripkeModel Node Atom) :
    GroundedSemiosis where
  World := Node
  Sign := Atom
  Claim := Formula Atom
  Context := Unit
  refers := fun _ _ => True
  expresses := fun a _ => .atom a
  satisfies := fun phi k => kripkeForces M k phi
  Evidence := fun a _ k => PLift (kripkeForces M k (.atom a))
  evidence_sound := by
    intro a _ k _ hev
    exact hev.down

/-- Operational causal-observation model on system states `Sys`. -/
def causalSemiosis (Sys Atom : Type) (observe : Sys -> Atom -> Bool) :
    GroundedSemiosis where
  World := Sys
  Sign := Atom
  Claim := Atom
  Context := Unit
  refers := fun a s => observe s a = true
  expresses := fun a _ => a
  satisfies := fun a s => observe s a = true
  Evidence := fun a _ s => PLift (observe s a = true)
  evidence_sound := by
    intro a _ s _ hev
    exact hev.down

theorem tarski_atom_conservative {World Atom : Type}
    (val : World -> Atom -> Bool) (a : Atom) (w : World) :
    ContentTrue (tarskiSemiosis World Atom val) a () w ↔
      tarskiEvalBool (val w) (.atom a) = true :=
  Iff.rfl

theorem heyting_atom_conservative {Node Atom : Type}
    (M : KripkeModel Node Atom) (a : Atom) (k : Node) :
    EvidentiallySupported (heytingSemiosis M) a () k ↔
      kripkeForces M k (.atom a) := by
  constructor
  · intro ⟨hev⟩; exact hev.down
  · intro h; exact ⟨PLift.up h⟩

theorem causal_atom_conservative {Sys Atom : Type}
    (observe : Sys -> Atom -> Bool) (a : Atom) (s : Sys) :
    GroundedAssertionTrue (causalSemiosis Sys Atom observe) a () s ↔
      observe s a = true := by
  constructor
  · intro h; exact h.1
  · intro h; exact ⟨h, h⟩

/-- When three heterogeneous realizations are calibrated to the same atomic
    observation oracle `obs : Atom -> Bool` on the shared signature `Σ`,
    atomic content truth agrees strictly across all three models without
    collapsing internal world or evidence differences. -/
theorem joint_atomic_signature_conservative
    {World Node Sys Atom : Type}
    (val : World -> Atom -> Bool)
    (M : KripkeModel Node Atom)
    (observe : Sys -> Atom -> Bool)
    (w : World) (k : Node) (s : Sys) (obs : Atom -> Bool)
    (hTW : forall a, val w a = obs a)
    (hHK : forall a, M.atomTrue k a ↔ obs a = true)
    (hCS : forall a, observe s a = obs a)
    (a : Atom) :
    (ContentTrue (tarskiSemiosis World Atom val) a () w ↔ obs a = true) ∧
    (ContentTrue (heytingSemiosis M) a () k ↔ obs a = true) ∧
    (GroundedAssertionTrue (causalSemiosis Sys Atom observe) a () s ↔ obs a = true) := by
  refine ⟨?_, ?_, ?_⟩
  · simp [ContentTrue, tarskiSemiosis, tarskiEvalBool, hTW a]
  · simp [ContentTrue, heytingSemiosis, kripkeForces, hHK a]
  · simp [GroundedAssertionTrue, ContentTrue, causalSemiosis, hCS a]

/-- Two-node countermodel (`false ≤ true`) separating classical bivalence from
    intuitionistic/evidential warrant: at root `false`, atom `()` is not yet
    decided, though it holds at `true`. -/
def twoNodeKripke : KripkeModel Bool Unit where
  le := fun a b => (a = false) ∨ (a = b)
  le_refl := by intro k; exact Or.inr rfl
  le_trans := by
    intro k1 k2 k3 h12 h23
    rcases h12 with rfl | rfl
    · exact Or.inl rfl
    · exact h23
  atomTrue := fun k _ => k = true
  monotone := by
    intro k1 k2 _ hle h1
    rcases hle with rfl | rfl
    · simp at h1
    · exact h1

/-- Classical Tarski satisfaction validates LEM (`P ∨ ¬P`) at every world,
    whereas the Kripke-grounded semiosis at root `false` has no evidential
    warrant for either `P` or `¬P` (Revised T7 + T4 incompatibility). -/
theorem classical_lem_not_evidentially_conservative :
    (forall (val : Unit -> Bool),
      tarskiEvalBool val (.disj (.atom ()) (.neg (.atom ()))) = true) ∧
    Not (kripkeForces twoNodeKripke false (.disj (.atom ()) (.neg (.atom ())))) := by
  constructor
  · intro val
    exact tarski_lem_always_holds val (.atom ())
  · intro hdisj
    rcases hdisj with hp | hneg
    · exact Bool.noConfusion hp
    · have hfuture : kripkeForces twoNodeKripke true (.atom ()) := rfl
      exact hneg true (Or.inl rfl) hfuture

theorem twoNodeKripke_root_no_evidential_support :
    Not (EvidentiallySupported (heytingSemiosis twoNodeKripke) () () false) := by
  intro ⟨hev⟩
  exact Bool.noConfusion hev.down

end Cerp.CrossTheoryConservativity
