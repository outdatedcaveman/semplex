/-
  Mathlib formalization for Bidirectional Acyclic-Depth Spanning-Tree
  Gauge Classification, Arbitrary `b`-Loop Bouquets, Non-Ambivalent `A₄`,
  and Simultaneous-Conjugacy `S₃` Split-Pair Counterexamples
  (`gemini/master-principle-free-energy`).

  Directly addresses the formal gaps identified in our adversarial audit of
  ChatGPT's `GraphGaugeClassification.lean`:
  1. Adds `disjoint : ∀ e, ¬(isTree e ∧ isChord e)` and bidirectional
     `SignedWalk` (`fwd` / `bwd`) transport covariance for arbitrary edge orientations.
  2. Replaces forward-only `RootedSpanningTree` (which suffers backtracking failure
     when reverse edges are added) with `AcyclicSpanningTree` (`depth : V → ℕ` +
     `parentEdge`), defining `treeFrame` by well-founded recursion on `depth`, deriving
     `treeFrame_edge_recursion` (`P(tgt e) = A(e) * P(src e)`) automatically for BOTH
     forward and backward tree-edge orientations, and proving:
     - `spanningTree_gaugeHomEquiv` (full faithfulness on ANY connected oriented graph),
     - `spanningTree_autEquiv_commonCentralizer` (`Aut(A) ≃* C_G(im rho_A)`),
     - `spanningTree_chordRep_essential_surj` (exact realization of ANY chord assignment).
  3. Proves full faithfulness for arbitrary `b`-loop `L+1`-ring bouquets (`bouquet_homEquiv`),
     non-ambivalence of `A₄` (`∃ c : alternatingGroup (Fin 4), ¬ IsConj c c⁻¹`), and
     both `S₃` two-loop simultaneous-conjugacy split pairs (`(s01, s01) vs (s01, s12)` and
     `(c, c) vs (c, c⁻¹)`).

  Isolated in `proofs/lean-mathlib/` so `proofs/lean/` remains core Lean 4.
-/
import Mathlib.Algebra.Group.Conj
import Mathlib.Data.Fin.VecNotation
import Mathlib.GroupTheory.Perm.Fin
import Mathlib.GroupTheory.SpecificGroups.Alternating

namespace MasterPrincipleBouquet

noncomputable section
set_option linter.unusedSectionVars false

section BidirectionalGraphGauge

universe u v w

/-- Oriented graph partitioned disjointly into tree edges and chord edges. -/
structure OrientedGraph (V : Type u) (E : Type v) where
  src : E → V
  tgt : E → V
  isTree : E → Prop
  isChord : E → Prop
  cover : ∀ e, isTree e ∨ isChord e
  disjoint : ∀ e, ¬(isTree e ∧ isChord e)

variable {V : Type u} {E : Type v} {G : Type w} [Group G]

/-- Vertex gauge action `(g • A)_e = g(tgt e) * A(e) * g(src e)⁻¹`. -/
def graphAct (D : OrientedGraph V E) (g : V → G) (A : E → G) (e : E) : G :=
  g (D.tgt e) * A e * (g (D.src e))⁻¹

theorem graphAct_mul (D : OrientedGraph V E) (g₁ g₂ : V → G) (A : E → G) :
    graphAct D (fun v => g₁ v * g₂ v) A = graphAct D g₁ (graphAct D g₂ A) := by
  funext e
  unfold graphAct
  group

theorem graphAct_one (D : OrientedGraph V E) (A : E → G) :
    graphAct D (fun _ => (1 : G)) A = A := by
  funext e
  simp [graphAct]

/-- Bidirectional edge-indexed walks allowing both forward and reversed edge traversal. -/
inductive SignedWalk (D : OrientedGraph V E) : V → V → Type (max u v)
  | nil (x : V) : SignedWalk D x x
  | fwd {x y z : V} (e : E) (hs : D.src e = x) (ht : D.tgt e = y)
      (tail : SignedWalk D y z) : SignedWalk D x z
  | bwd {x y z : V} (e : E) (ht : D.tgt e = x) (hs : D.src e = y)
      (tail : SignedWalk D y z) : SignedWalk D x z

/-- Ordered parallel transport along a bidirectional signed walk. -/
def signedTransport (D : OrientedGraph V E) (A : E → G) :
    {x y : V} → SignedWalk D x y → G
  | _, _, SignedWalk.nil _ => 1
  | _, _, SignedWalk.fwd e _ _ tail => signedTransport D A tail * A e
  | _, _, SignedWalk.bwd e _ _ tail => signedTransport D A tail * (A e)⁻¹

theorem signedTransport_gauge_covariant
    (D : OrientedGraph V E) (g : V → G) (A : E → G) :
    ∀ {x y : V} (p : SignedWalk D x y),
      signedTransport D (graphAct D g A) p = g y * signedTransport D A p * (g x)⁻¹ := by
  intro x y p
  induction p with
  | nil z =>
      simp [signedTransport]
  | @fwd x y z e hs ht tail ih =>
      subst x
      subst y
      simp only [signedTransport, graphAct]
      rw [ih]
      group
  | @bwd x y z e ht hs tail ih =>
      subst x
      subst y
      simp only [signedTransport, graphAct]
      rw [ih]
      group

/-- Acyclic depth-ranked spanning-tree certificate immune to reverse-edge backtracking. -/
structure AcyclicSpanningTree (D : OrientedGraph V E) where
  root : V
  depth : V → ℕ
  depth_root : depth root = 0
  parentEdge : V → Option E
  parent_spec : ∀ v, v ≠ root → ∃ e, parentEdge v = some e ∧ D.isTree e ∧
    ((D.tgt e = v ∧ depth (D.src e) < depth v) ∨ (D.src e = v ∧ depth (D.tgt e) < depth v))
  tree_edge_unique : ∀ e, D.isTree e →
    (D.tgt e ≠ root ∧ parentEdge (D.tgt e) = some e ∧ depth (D.src e) < depth (D.tgt e)) ∨
    (D.src e ≠ root ∧ parentEdge (D.src e) = some e ∧ depth (D.tgt e) < depth (D.src e))

section TreeFrameClassical
open Classical
set_option linter.unusedVariables false

/-- Tree-gauge parallel transport defined by well-founded recursion on vertex tree depth. -/
def treeFrame (D : OrientedGraph V E) (T : AcyclicSpanningTree D)
    (A : E → G) (v : V) : G :=
  if hv : v = T.root then 1
  else
    let he := Classical.choose (T.parent_spec v hv)
    let hp := Classical.choose_spec (T.parent_spec v hv)
    if hdir : D.tgt he = v ∧ T.depth (D.src he) < T.depth v then
      A he * treeFrame D T A (D.src he)
    else
      (A he)⁻¹ * treeFrame D T A (D.tgt he)
termination_by T.depth v
decreasing_by
  · exact hdir.2
  · rcases hp.2.2 with h1 | h2
    · exact absurd h1 hdir
    · exact h2.2

theorem treeFrame_root (D : OrientedGraph V E) (T : AcyclicSpanningTree D) (A : E → G) :
    treeFrame D T A T.root = 1 := by
  rw [treeFrame]
  exact dif_pos rfl

/-- Tree-edge recursion holds automatically for BOTH forward and backward edge orientations. -/
theorem treeFrame_edge_recursion
    (D : OrientedGraph V E) (T : AcyclicSpanningTree D) (A : E → G)
    (e : E) (ht : D.isTree e) :
    treeFrame D T A (D.tgt e) = A e * treeFrame D T A (D.src e) := by
  rcases T.tree_edge_unique e ht with ⟨htgt_ne, hpar, hdep⟩ | ⟨hsrc_ne, hpar, hdep⟩
  · conv_lhs => rw [treeFrame]
    rw [dif_neg htgt_ne]
    have hch : Classical.choose (T.parent_spec (D.tgt e) htgt_ne) = e :=
      Option.some.inj ((Classical.choose_spec (T.parent_spec (D.tgt e) htgt_ne)).1.symm.trans hpar)
    have hdir : D.tgt (Classical.choose (T.parent_spec (D.tgt e) htgt_ne)) = D.tgt e ∧
        T.depth (D.src (Classical.choose (T.parent_spec (D.tgt e) htgt_ne))) < T.depth (D.tgt e) := by
      rw [hch]; exact ⟨rfl, hdep⟩
    rw [dif_pos hdir, hch]
  · have hsrc_eq : treeFrame D T A (D.src e) = (A e)⁻¹ * treeFrame D T A (D.tgt e) := by
      conv_lhs => rw [treeFrame]
      rw [dif_neg hsrc_ne]
      have hch : Classical.choose (T.parent_spec (D.src e) hsrc_ne) = e :=
        Option.some.inj ((Classical.choose_spec (T.parent_spec (D.src e) hsrc_ne)).1.symm.trans hpar)
      have hndir : ¬(D.tgt (Classical.choose (T.parent_spec (D.src e) hsrc_ne)) = D.src e ∧
          T.depth (D.src (Classical.choose (T.parent_spec (D.src e) hsrc_ne))) <
            T.depth (D.src e)) := by
        rw [hch]
        rintro ⟨_, hlt⟩
        exact Nat.lt_irrefl _ hlt
      rw [dif_neg hndir, hch]
    calc treeFrame D T A (D.tgt e)
        = A e * ((A e)⁻¹ * treeFrame D T A (D.tgt e)) := by group
      _ = A e * treeFrame D T A (D.src e) := by rw [← hsrc_eq]

theorem treeFrame_gauge_covariant
    (D : OrientedGraph V E) (T : AcyclicSpanningTree D)
    (g : V → G) (A : E → G) :
    ∀ v : V, treeFrame D T (graphAct D g A) v =
      g v * treeFrame D T A v * (g T.root)⁻¹ := by
  intro v
  have hwf : ∀ n : ℕ, ∀ w : V, T.depth w = n →
      treeFrame D T (graphAct D g A) w = g w * treeFrame D T A w * (g T.root)⁻¹ := by
    intro n
    induction n using Nat.strong_induction_on with
    | h n ih =>
        intro w hdw
        by_cases hw : w = T.root
        · subst hw
          simp [treeFrame_root]
        · let he := Classical.choose (T.parent_spec w hw)
          have hp := Classical.choose_spec (T.parent_spec w hw)
          have htree := hp.2.1
          have hrecG := treeFrame_edge_recursion D T (graphAct D g A) he htree
          have hrecA := treeFrame_edge_recursion D T A he htree
          rcases hp.2.2 with ⟨htgt, hlt⟩ | ⟨hsrc, hlt⟩
          · have hih := ih (T.depth (D.src he)) (hdw ▸ hlt) (D.src he) rfl
            rw [← htgt, hrecG, hih, hrecA]
            unfold graphAct
            group
          · have hih := ih (T.depth (D.tgt he)) (hdw ▸ hlt) (D.tgt he) rfl
            rw [← hsrc]
            have heG : treeFrame D T (graphAct D g A) (D.src he) =
                (graphAct D g A he)⁻¹ * treeFrame D T (graphAct D g A) (D.tgt he) := by
              rw [hrecG]; group
            have heA : treeFrame D T A (D.src he) = (A he)⁻¹ * treeFrame D T A (D.tgt he) := by
              rw [hrecA]; group
            rw [heG, hih, heA]
            unfold graphAct
            group
  exact hwf (T.depth v) v rfl

/-- Fundamental chord holonomy associated with edge `e` and spanning tree `T`. -/
def chordHol (D : OrientedGraph V E) (T : AcyclicSpanningTree D) (A : E → G) (e : E) : G :=
  (treeFrame D T A (D.tgt e))⁻¹ * A e * treeFrame D T A (D.src e)

theorem chordHol_gauge_covariant
    (D : OrientedGraph V E) (T : AcyclicSpanningTree D) (g : V → G) (A : E → G) (e : E) :
    chordHol D T (graphAct D g A) e =
      g T.root * chordHol D T A e * (g T.root)⁻¹ := by
  unfold chordHol
  rw [treeFrame_gauge_covariant D T g A (D.tgt e),
      treeFrame_gauge_covariant D T g A (D.src e)]
  unfold graphAct
  group

private def canonTreeGauge (D : OrientedGraph V E) (T : AcyclicSpanningTree D)
    (A B : E → G) (k : G) (v : V) : G :=
  treeFrame D T B v * k * (treeFrame D T A v)⁻¹

private theorem canonTreeGauge_act
    (D : OrientedGraph V E) (T : AcyclicSpanningTree D) (A B : E → G) (k : G)
    (hk : ∀ e, D.isChord e → chordHol D T B e = k * chordHol D T A e * k⁻¹) :
    graphAct D (canonTreeGauge D T A B k) A = B := by
  funext e
  unfold graphAct canonTreeGauge
  rcases D.cover e with ht | hc
  · rw [treeFrame_edge_recursion D T A e ht, treeFrame_edge_recursion D T B e ht]
    group
  · have hch := hk e hc
    have hmul : B e = treeFrame D T B (D.tgt e) *
        (k * chordHol D T A e * k⁻¹) * (treeFrame D T B (D.src e))⁻¹ := by
      rw [← hch]
      unfold chordHol
      group
    rw [hmul]
    unfold chordHol
    group

/-- **General Connected-Graph Full Faithfulness Theorem** (`Conn(Γ,G)//G^V → Hom(π₁,G)//G`):
    explicit bijection between vertex-gauge arrows `A → B` and basepoint conjugators
    simultaneously conjugating all fundamental chord holonomies, valid for arbitrary graph
    orientations. -/
def spanningTree_gaugeHomEquiv
    (D : OrientedGraph V E) (T : AcyclicSpanningTree D) (A B : E → G) :
    { g : V → G // graphAct D g A = B } ≃
      { k : G // ∀ e, D.isChord e → chordHol D T B e = k * chordHol D T A e * k⁻¹ } where
  toFun := fun ⟨g, hg⟩ => ⟨g T.root, fun e _ => by
    calc chordHol D T B e = chordHol D T (graphAct D g A) e := by rw [hg]
      _ = g T.root * chordHol D T A e * (g T.root)⁻¹ := chordHol_gauge_covariant D T g A e⟩
  invFun := fun ⟨k, hk⟩ => ⟨canonTreeGauge D T A B k, canonTreeGauge_act D T A B k hk⟩
  left_inv := by
    rintro ⟨g, hg⟩
    apply Subtype.ext
    funext v
    dsimp only
    unfold canonTreeGauge
    have hcov := treeFrame_gauge_covariant D T g A v
    rw [hg] at hcov
    rw [hcov]
    group
  right_inv := by
    rintro ⟨k, hk⟩
    apply Subtype.ext
    dsimp only [canonTreeGauge]
    simp [treeFrame_root]

/-- Vertex-gauge stabilizer isomorphism onto the common centralizer of all chord holonomies. -/
def spanningTree_autEquiv_commonCentralizer
    (D : OrientedGraph V E) (T : AcyclicSpanningTree D) (A : E → G) :
    { g : V → G // graphAct D g A = A } ≃
      { k : G // ∀ e, D.isChord e → k * chordHol D T A e = chordHol D T A e * k } :=
  (spanningTree_gaugeHomEquiv D T A A).trans
    { toFun := fun ⟨k, hk⟩ => ⟨k, fun e hc => by
        calc k * chordHol D T A e
            = (k * chordHol D T A e * k⁻¹) * k := by group
          _ = chordHol D T A e * k := by rw [← hk e hc]⟩
      invFun := fun ⟨k, hk⟩ => ⟨k, fun e hc => by
        symm
        calc k * chordHol D T A e * k⁻¹ = (chordHol D T A e * k) * k⁻¹ := by rw [hk e hc]
          _ = chordHol D T A e := by group⟩
      left_inv := by rintro ⟨k, hk⟩; rfl
      right_inv := by rintro ⟨k, hk⟩; rfl }

/-- **Essential Surjectivity for Arbitrary Chord Assignments**:
    Using `D.disjoint`, any chord-generator assignment lifts cleanly to an identity-on-tree
    connection whose fundamental chord holonomies equal the prescribed values identically. -/
theorem spanningTree_chordRep_essential_surj
    (D : OrientedGraph V E) (T : AcyclicSpanningTree D)
    (ρ : ∀ e, D.isChord e → G) :
    ∃ A : E → G, (∀ e, D.isTree e → A e = 1) ∧
      ∀ e (hc : D.isChord e), chordHol D T A e = ρ e hc := by
  let A : E → G := fun e => if hc : D.isChord e then ρ e hc else 1
  have htree1 : ∀ e, D.isTree e → A e = 1 := fun e ht => by
    dsimp [A]
    exact dif_neg fun hc => D.disjoint e ⟨ht, hc⟩
  have hframe1 : ∀ v : V, treeFrame D T A v = 1 := by
    intro v
    have hwf : ∀ n : ℕ, ∀ w : V, T.depth w = n → treeFrame D T A w = 1 := by
      intro n
      induction n using Nat.strong_induction_on with
      | h n ih =>
          intro w hdw
          by_cases hw : w = T.root
          · subst hw; exact treeFrame_root D T A
          · let he := Classical.choose (T.parent_spec w hw)
            have hp := Classical.choose_spec (T.parent_spec w hw)
            have hrec := treeFrame_edge_recursion D T A he hp.2.1
            have hAe := htree1 he hp.2.1
            rcases hp.2.2 with ⟨htgt, hlt⟩ | ⟨hsrc, hlt⟩
            · have hih := ih (T.depth (D.src he)) (hdw ▸ hlt) (D.src he) rfl
              rw [← htgt, hrec, hAe, hih, mul_one]
            · have hih := ih (T.depth (D.tgt he)) (hdw ▸ hlt) (D.tgt he) rfl
              rw [← hsrc]
              calc treeFrame D T A (D.src he)
                  = (A he)⁻¹ * treeFrame D T A (D.tgt he) := by rw [hrec]; group
                _ = 1 := by rw [hAe, hih, inv_one, mul_one]
    exact hwf (T.depth v) v rfl
  refine ⟨A, htree1, fun e hc => ?_⟩
  unfold chordHol
  rw [hframe1 (D.tgt e), hframe1 (D.src e)]
  simp [A, hc]

end TreeFrameClassical

end BidirectionalGraphGauge

section ArbitraryBouquetAndGroupObstructions

variable {G : Type*} [Group G]

/-- Directed edge composition along loop `r` of a `b`-loop `(L + 1)`-edge bouquet. -/
def bouquetLoopProd {b L : ℕ} (A : Fin b → Fin (L + 1) → G) (r : Fin b) : ℕ → G
  | 0 => 1
  | k + 1 => A r ⟨k % (L + 1), Nat.mod_lt _ (Nat.succ_pos L)⟩ * bouquetLoopProd A r k

def bouquetHol {b L : ℕ} (A : Fin b → Fin (L + 1) → G) (r : Fin b) : G :=
  bouquetLoopProd A r (L + 1)

def bouquetNext {L : ℕ} (i : Fin (L + 1)) : Fin (L + 1) :=
  ⟨(i.1 + 1) % (L + 1), Nat.mod_lt _ (Nat.succ_pos L)⟩

private def bStep (L m : ℕ) : Fin (L + 1) :=
  ⟨m % (L + 1), Nat.mod_lt _ (Nat.succ_pos L)⟩

private theorem bouquetNext_bStep (L m : ℕ) :
    bouquetNext (bStep L m) = bStep L (m + 1) := by
  apply Fin.ext
  simp [bouquetNext, bStep, Nat.add_mod]

/-- Basepoint-shared bouquet vertex-gauge action: `g_base` acts at vertex `0` of every loop,
    while internal vertices `Fin L` vary per loop. -/
def bouquetAct {b L : ℕ} (g_base : G) (g_int : Fin b → Fin L → G)
    (A : Fin b → Fin (L + 1) → G) (r : Fin b) (i : Fin (L + 1)) : G :=
  let v : Fin (L + 1) → G := fun j => if hj : j.1 = 0 then g_base else
    g_int r ⟨j.1 - 1, by omega⟩
  v (bouquetNext i) * A r i * (v i)⁻¹

private theorem bouquetLoopProd_act {b L : ℕ} (g_base : G) (g_int : Fin b → Fin L → G)
    (A : Fin b → Fin (L + 1) → G) (r : Fin b) :
    ∀ k : ℕ, bouquetLoopProd (bouquetAct g_base g_int A) r k =
      (let j := bStep L k
       (if hj : j.1 = 0 then g_base else g_int r ⟨j.1 - 1, by omega⟩)) *
        bouquetLoopProd A r k * g_base⁻¹
  | 0 => by
      have hz : (bStep L 0).1 = 0 := Nat.zero_mod _
      simp [bouquetLoopProd, hz]
  | k + 1 => by
      rw [bouquetLoopProd, bouquetLoopProd_act g_base g_int A r k, bouquetLoopProd]
      change bouquetAct g_base g_int A r (bStep L k) *
          ((if hj : (bStep L k).1 = 0 then g_base else g_int r ⟨(bStep L k).1 - 1, by omega⟩) *
            bouquetLoopProd A r k * g_base⁻¹) =
        (if hj : (bStep L (k + 1)).1 = 0 then g_base else g_int r ⟨(bStep L (k + 1)).1 - 1, by omega⟩) *
          (A r (bStep L k) * bouquetLoopProd A r k) * g_base⁻¹
      unfold bouquetAct
      rw [bouquetNext_bStep]
      group

theorem bouquetHol_covariant {b L : ℕ} (g_base : G) (g_int : Fin b → Fin L → G)
    (A : Fin b → Fin (L + 1) → G) (r : Fin b) :
    bouquetHol (bouquetAct g_base g_int A) r = g_base * bouquetHol A r * g_base⁻¹ := by
  unfold bouquetHol
  rw [bouquetLoopProd_act]
  have h0 : (bStep L (L + 1)).1 = 0 := Nat.mod_self (L + 1)
  simp [h0]

private def canonBouquetInt {b L : ℕ} (A A' : Fin b → Fin (L + 1) → G) (k : G)
    (r : Fin b) (j : Fin L) : G :=
  bouquetLoopProd A' r (j.1 + 1) * k * (bouquetLoopProd A r (j.1 + 1))⁻¹

private theorem canonBouquet_act {b L : ℕ} (A A' : Fin b → Fin (L + 1) → G) (k : G)
    (hk : ∀ r : Fin b, k * bouquetHol A r * k⁻¹ = bouquetHol A' r) :
    bouquetAct k (canonBouquetInt A A' k) A = A' := by
  funext r i
  unfold bouquetAct canonBouquetInt
  have hi_mod : (⟨i.1 % (L + 1), Nat.mod_lt _ (Nat.succ_pos L)⟩ : Fin (L + 1)) = i :=
    Fin.ext (Nat.mod_eq_of_lt i.isLt)
  have hpA : bouquetLoopProd A r (i.1 + 1) = A r i * bouquetLoopProd A r i.1 := by
    rw [bouquetLoopProd, hi_mod]
  have hpA' : bouquetLoopProd A' r (i.1 + 1) = A' r i * bouquetLoopProd A' r i.1 := by
    rw [bouquetLoopProd, hi_mod]
  rcases eq_or_ne i.1 0 with hi0 | hi_pos <;> rcases Nat.lt_or_ge (i.1 + 1) (L + 1) with hnext | hlast
  · have hnext_ne : (bouquetNext i).1 ≠ 0 := by
      simp only [bouquetNext, hi0, zero_add]
      rw [Nat.mod_eq_of_lt (by omega)]
      exact Nat.one_ne_zero
    have hnext_val : (bouquetNext i).1 - 1 = i.1 := by simp [bouquetNext, Nat.mod_eq_of_lt hnext]
    simp only [hi0, hnext_ne, ↓reduceDIte, hnext_val]
    have hAi : A r i = bouquetLoopProd A r 1 := by
      have hp := hpA
      rw [hi0, bouquetLoopProd, mul_one] at hp
      exact hp.symm
    have hA'i : A' r i = bouquetLoopProd A' r 1 := by
      have hp := hpA'
      rw [hi0, bouquetLoopProd, mul_one] at hp
      exact hp.symm
    rw [← hAi, ← hA'i]
    group
  · have heqL1 : i.1 + 1 = L + 1 := by omega
    have hnext0 : (bouquetNext i).1 = 0 := by simp [bouquetNext, heqL1]
    simp only [hi0, hnext0, ↓reduceDIte]
    have hwA : bouquetHol A r = A r i := by
      unfold bouquetHol
      rw [← heqL1, hpA, hi0, bouquetLoopProd, mul_one]
    have hwA' : bouquetHol A' r = A' r i := by
      unfold bouquetHol
      rw [← heqL1, hpA', hi0, bouquetLoopProd, mul_one]
    calc k * A r i * k⁻¹ = k * bouquetHol A r * k⁻¹ := by rw [hwA]
      _ = bouquetHol A' r := hk r
      _ = A' r i := hwA'
  · have hnext_ne : (bouquetNext i).1 ≠ 0 := by
      simp [bouquetNext, Nat.mod_eq_of_lt hnext]
    have hnext_val : (bouquetNext i).1 - 1 = i.1 := by simp [bouquetNext, Nat.mod_eq_of_lt hnext]
    have hi_sub : (i.1 - 1) + 1 = i.1 := by omega
    simp only [hi_pos, hnext_ne, ↓reduceDIte, hnext_val, hi_sub]
    rw [hpA, hpA']
    group
  · have heqL1 : i.1 + 1 = L + 1 := by omega
    have hnext0 : (bouquetNext i).1 = 0 := by simp [bouquetNext, heqL1]
    have hi_sub : (i.1 - 1) + 1 = i.1 := by omega
    simp only [hi_pos, hnext0, ↓reduceDIte, hi_sub]
    have hwA : bouquetHol A r = A r i * bouquetLoopProd A r i.1 := by
      unfold bouquetHol; conv_lhs => rw [← heqL1]; exact hpA
    have hwA' : bouquetHol A' r = A' r i * bouquetLoopProd A' r i.1 := by
      unfold bouquetHol; conv_lhs => rw [← heqL1]; exact hpA'
    calc k * A r i * (bouquetLoopProd A' r i.1 * k * (bouquetLoopProd A r i.1)⁻¹)⁻¹
        = (k * (A r i * bouquetLoopProd A r i.1) * k⁻¹) * (bouquetLoopProd A' r i.1)⁻¹ := by group
      _ = (k * bouquetHol A r * k⁻¹) * (bouquetLoopProd A' r i.1)⁻¹ := by rw [← hwA]
      _ = bouquetHol A' r * (bouquetLoopProd A' r i.1)⁻¹ := by rw [hk r]
      _ = (A' r i * bouquetLoopProd A' r i.1) * (bouquetLoopProd A' r i.1)⁻¹ := by rw [hwA']
      _ = A' r i := by group

/-- **Arbitrary `b`-Loop Bouquet Full Faithfulness Theorem** (`Conn(Bouquet_b)//G^{1+bL} → G^b // G`):
    exact bijection between bouquet vertex-gauge arrows and simultaneous conjugation `k` across all
    `b` loops, valid for any group `G`, any bouquet rank `b`, and any loop length `L + 1`. -/
def bouquet_homEquiv {b L : ℕ} (A A' : Fin b → Fin (L + 1) → G) :
    { p : G × (Fin b → Fin L → G) // bouquetAct p.1 p.2 A = A' } ≃
      { k : G // ∀ r : Fin b, k * bouquetHol A r * k⁻¹ = bouquetHol A' r } where
  toFun := fun ⟨p, hp⟩ => ⟨p.1, fun r => by
    calc p.1 * bouquetHol A r * p.1⁻¹ = bouquetHol (bouquetAct p.1 p.2 A) r :=
          (bouquetHol_covariant p.1 p.2 A r).symm
      _ = bouquetHol A' r := by rw [hp]⟩
  invFun := fun ⟨k, hk⟩ => ⟨⟨k, canonBouquetInt A A' k⟩, canonBouquet_act A A' k hk⟩
  left_inv := by
    rintro ⟨⟨g_base, g_int⟩, hp⟩
    apply Subtype.ext
    ext1
    · rfl
    · funext r j
      dsimp only
      unfold canonBouquetInt
      have hpath := bouquetLoopProd_act g_base g_int A r (j.1 + 1)
      rw [hp] at hpath
      have hlt : j.1 + 1 < L + 1 := Nat.succ_lt_succ j.isLt
      have hval : (bStep L (j.1 + 1)).1 = j.1 + 1 := Nat.mod_eq_of_lt hlt
      have hne0 : (bStep L (j.1 + 1)).1 ≠ 0 := by rw [hval]; exact Nat.succ_ne_zero _
      simp only [hne0, ↓reduceDIte] at hpath
      have hsub : (⟨(bStep L (j.1 + 1)).1 - 1, by omega⟩ : Fin L) = j := by
        apply Fin.ext; simp [hval]
      rw [hsub] at hpath
      rw [hpath]
      group
  right_inv := by
    rintro ⟨k, hk⟩
    rfl

private def c3_4 : Equiv.Perm (Fin 4) :=
  ⟨![1, 2, 0, 3], ![2, 0, 1, 3], by decide, by decide⟩

private theorem c3_4_mem_A4 : c3_4 ∈ alternatingGroup (Fin 4) := by
  rw [Equiv.Perm.mem_alternatingGroup]
  decide

/-- **Non-Ambivalence of `A₄`**: There exists an element in the alternating group `A₄` not
    conjugate to its inverse inside `A₄` (proving real-character / palindromic probes strictly
    fail on `A₄`). -/
theorem a4_non_ambivalent :
    ∃ c : alternatingGroup (Fin 4), ¬ IsConj c c⁻¹ := by
  refine ⟨⟨c3_4, c3_4_mem_A4⟩, ?_⟩
  rw [isConj_iff]
  rintro ⟨k, hk⟩
  have hmul : (k : Equiv.Perm (Fin 4)) * c3_4 = c3_4⁻¹ * (k : Equiv.Perm (Fin 4)) := by
    have hk_val := congrArg Subtype.val hk
    change (k : Equiv.Perm (Fin 4)) * c3_4 * (k : Equiv.Perm (Fin 4))⁻¹ = c3_4⁻¹ at hk_val
    exact mul_inv_eq_iff_eq_mul.mp hk_val
  have h3 : (k : Equiv.Perm (Fin 4)) 3 = 3 := by
    have hev := congrArg (fun p : Equiv.Perm (Fin 4) => p 3) hmul
    have hc3 : c3_4 3 = 3 := by decide
    simp only [Equiv.Perm.mul_apply, hc3] at hev
    have hfix : c3_4 ((k : Equiv.Perm (Fin 4)) 3) = (k : Equiv.Perm (Fin 4)) 3 := by
      calc c3_4 ((k : Equiv.Perm (Fin 4)) 3) = c3_4 (c3_4⁻¹ ((k : Equiv.Perm (Fin 4)) 3)) := by rw [← hev]
        _ = (k : Equiv.Perm (Fin 4)) 3 := by simp
    have : ∀ x : Fin 4, c3_4 x = x → x = 3 := by decide
    exact this _ hfix
  have h1 : (k : Equiv.Perm (Fin 4)) 1 = c3_4⁻¹ ((k : Equiv.Perm (Fin 4)) 0) := by
    have hev := congrArg (fun p : Equiv.Perm (Fin 4) => p 0) hmul
    have hc0 : c3_4 0 = 1 := by decide
    simpa [Equiv.Perm.mul_apply, hc0] using hev
  have h2 : (k : Equiv.Perm (Fin 4)) 2 = c3_4⁻¹ ((k : Equiv.Perm (Fin 4)) 1) := by
    have hev := congrArg (fun p : Equiv.Perm (Fin 4) => p 1) hmul
    have hc1 : c3_4 1 = 2 := by decide
    simpa [Equiv.Perm.mul_apply, hc1] using hev
  have hsign1 : Equiv.Perm.sign (k : Equiv.Perm (Fin 4)) = 1 :=
    Equiv.Perm.mem_alternatingGroup.mp k.2
  have hne3 : (k : Equiv.Perm (Fin 4)) 0 ≠ 3 := by
    intro h
    have h03 : (0 : Fin 4) = 3 := (k : Equiv.Perm (Fin 4)).injective (h.trans h3.symm)
    exact absurd h03 (by decide)
  have hk0_cases : (k : Equiv.Perm (Fin 4)) 0 = 0 ∨ (k : Equiv.Perm (Fin 4)) 0 = 1 ∨
      (k : Equiv.Perm (Fin 4)) 0 = 2 ∨ (k : Equiv.Perm (Fin 4)) 0 = 3 := by
    generalize (k : Equiv.Perm (Fin 4)) 0 = x
    fin_cases x <;> simp
  rcases hk0_cases with hk0 | hk0 | hk0 | hk0
  · have hkeq : (k : Equiv.Perm (Fin 4)) = Equiv.swap 1 2 := by
      ext i; fin_cases i <;> simp [hk0, h1, h2, h3, c3_4] <;> decide
    have hodd : Equiv.Perm.sign (k : Equiv.Perm (Fin 4)) = -1 := by rw [hkeq]; decide
    have h1m1 : (1 : ℤˣ) = -1 := hsign1.symm.trans hodd; revert h1m1; decide
  · have hkeq : (k : Equiv.Perm (Fin 4)) = Equiv.swap 0 1 := by
      ext i; fin_cases i <;> simp [hk0, h1, h2, h3, c3_4] <;> decide
    have hodd : Equiv.Perm.sign (k : Equiv.Perm (Fin 4)) = -1 := by rw [hkeq]; decide
    have h1m1 : (1 : ℤˣ) = -1 := hsign1.symm.trans hodd; revert h1m1; decide
  · have hkeq : (k : Equiv.Perm (Fin 4)) = Equiv.swap 0 2 := by
      ext i; fin_cases i <;> simp [hk0, h1, h2, h3, c3_4] <;> decide
    have hodd : Equiv.Perm.sign (k : Equiv.Perm (Fin 4)) = -1 := by rw [hkeq]; decide
    have h1m1 : (1 : ℤˣ) = -1 := hsign1.symm.trans hodd; revert h1m1; decide
  · exact absurd hk0 hne3

private def s01 : Equiv.Perm (Fin 3) := Equiv.swap 0 1
private def s12 : Equiv.Perm (Fin 3) := Equiv.swap 1 2
private def c3_3 : Equiv.Perm (Fin 3) := ⟨![1, 2, 0], ![2, 0, 1], by decide, by decide⟩

/-- **Both `S₃` Two-Loop Bouquet Simultaneous-Conjugacy Counterexamples**:
    (1) Transposition split pair `(s01, s01)` vs `(s01, s12)` (`s01 ~ s12`, disjoint joint orbits);
    (2) 3-cycle chiral split pair `(c, c)` vs `(c, c⁻¹)` (`c ~ c⁻¹` in `S₃`, disjoint joint orbits). -/
theorem s3_bouquet_both_split_pairs :
    (IsConj s01 s01 ∧ IsConj s01 s12 ∧
      ¬ ∃ k : Equiv.Perm (Fin 3), k * s01 * k⁻¹ = s01 ∧ k * s01 * k⁻¹ = s12) ∧
    (IsConj c3_3 c3_3 ∧ IsConj c3_3 c3_3⁻¹ ∧
      ¬ ∃ k : Equiv.Perm (Fin 3), k * c3_3 * k⁻¹ = c3_3 ∧ k * c3_3 * k⁻¹ = c3_3⁻¹) := by
  refine ⟨⟨IsConj.refl _, isConj_iff.mpr ⟨c3_3, ?_⟩, ?_⟩,
    ⟨IsConj.refl _, isConj_iff.mpr ⟨s12, ?_⟩, ?_⟩⟩
  · ext i; fin_cases i <;> decide
  · rintro ⟨k, h1, h2⟩
    have hne : s01 = s12 := h1.symm.trans h2
    have h0 := congrArg (fun p : Equiv.Perm (Fin 3) => p 0) hne
    revert h0; decide
  · ext i; fin_cases i <;> decide
  · rintro ⟨k, h1, h2⟩
    have hne : c3_3 = c3_3⁻¹ := h1.symm.trans h2
    have h0 := congrArg (fun p : Equiv.Perm (Fin 3) => p 0) hne
    revert h0; decide

end ArbitraryBouquetAndGroupObstructions

end
end MasterPrincipleBouquet
