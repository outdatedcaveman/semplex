import Lean

/-!
# Operational semiotic scaffold

A minimal non-homuncular, closed-loop model of sign processing:
environment -> sensor/sign -> internal interpretation -> action ->
environment update, with internal learning. Structure-preserving maps
preserve finite observable traces.
-/

namespace Cerp.OperationalSemioticScaffold

universe u v w x y

structure OperationalScaffold where
  World : Type u
  Internal : Type v
  Sign : Type w
  Interpretant : Type x
  Action : Type y
  sense : World -> Sign
  interpret : Internal -> Sign -> Interpretant
  chooseAction : Internal -> Interpretant -> Action
  learn : Internal -> Sign -> Internal
  evolve : World -> Action -> World

abbrev Config (S : OperationalScaffold.{u,v,w,x,y}) :=
  S.World × S.Internal

abbrev Output (S : OperationalScaffold.{u,v,w,x,y}) :=
  S.Sign × S.Interpretant × S.Action

/-- One closed-loop cycle: observe, interpret, act, and update memory/world. -/
def step (S : OperationalScaffold.{u,v,w,x,y})
    (c : Config S) : Config S × Output S :=
  let world := c.1
  let memory := c.2
  let sign := S.sense world
  let meaning := S.interpret memory sign
  let action := S.chooseAction memory meaning
  ((S.evolve world action, S.learn memory sign),
    (sign, meaning, action))

structure ScaffoldHom
    (S T : OperationalScaffold.{u,v,w,x,y}) where
  worldMap : S.World -> T.World
  internalMap : S.Internal -> T.Internal
  signMap : S.Sign -> T.Sign
  interpretantMap : S.Interpretant -> T.Interpretant
  actionMap : S.Action -> T.Action
  sense_commutes : forall w,
    signMap (S.sense w) = T.sense (worldMap w)
  interpret_commutes : forall m s,
    interpretantMap (S.interpret m s) =
      T.interpret (internalMap m) (signMap s)
  action_commutes : forall m i,
    actionMap (S.chooseAction m i) =
      T.chooseAction (internalMap m) (interpretantMap i)
  learn_commutes : forall m s,
    internalMap (S.learn m s) =
      T.learn (internalMap m) (signMap s)
  evolve_commutes : forall w a,
    worldMap (S.evolve w a) =
      T.evolve (worldMap w) (actionMap a)

def mapConfig {S T : OperationalScaffold.{u,v,w,x,y}}
    (f : ScaffoldHom S T) (c : Config S) : Config T :=
  (f.worldMap c.1, f.internalMap c.2)

def mapOutput {S T : OperationalScaffold.{u,v,w,x,y}}
    (f : ScaffoldHom S T) (o : Output S) : Output T :=
  (f.signMap o.1, f.interpretantMap o.2.1, f.actionMap o.2.2)

/-- A scaffold homomorphism commutes with one full closed-loop cycle. -/
theorem step_commutes {S T : OperationalScaffold.{u,v,w,x,y}}
    (f : ScaffoldHom S T) (c : Config S) :
    mapConfig f (step S c).1 = (step T (mapConfig f c)).1 ∧
      mapOutput f (step S c).2 = (step T (mapConfig f c)).2 := by
  rcases c with ⟨w, m⟩
  simp [step, mapConfig, mapOutput, f.sense_commutes,
    f.interpret_commutes, f.action_commutes,
    f.learn_commutes, f.evolve_commutes]

/-- Finite observable trace of a scaffold from an initial configuration. -/
def runOutputs (S : OperationalScaffold.{u,v,w,x,y}) :
    Nat -> Config S -> List (Output S)
  | 0, _ => []
  | n + 1, c =>
      let result := step S c
      result.2 :: runOutputs S n result.1

/-- Structure-preserving scaffold maps preserve every finite output trace. -/
theorem runOutputs_map {S T : OperationalScaffold.{u,v,w,x,y}}
    (f : ScaffoldHom S T) :
    forall (n : Nat) (c : Config S),
      (runOutputs S n c).map (mapOutput f) =
        runOutputs T n (mapConfig f c) := by
  intro n
  induction n with
  | zero =>
      intro c
      rfl
  | succ n ih =>
      intro c
      simp only [runOutputs, List.map_cons]
      rcases step_commutes f c with ⟨hc, ho⟩
      rw [ho]
      have htail := ih (step S c).1
      rw [hc] at htail
      exact congrArg (List.cons ((step T (mapConfig f c)).2)) htail

end Cerp.OperationalSemioticScaffold
