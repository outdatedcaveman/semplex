import GraphGaugeHolonomy
namespace Cerp.GraphGaugeClassification
universe u v w
open Cerp.HoTTGaugeBridge
variable {V : Type u} {E : Type v} {G : Type w} [GroupLike G]

structure Graph where
  src : E → V
  tgt : E → V
  isTree : E → Prop
  isChord : E → Prop
  cover : ∀ e, isTree e ∨ isChord e

abbrev Connection := E → G
abbrev Gauge := V → G

def act (D : Graph (V := V) (E := E)) (A : Connection (E := E) (G := G))
    (g : Gauge (V := V) (G := G)) : Connection (E := E) (G := G) :=
  fun e => GroupLike.mul (GroupLike.mul (g (D.tgt e)) (A e))
    (GroupLike.inv (g (D.src e)))

def chordHolonomy (D : Graph (V := V) (E := E))
    (frame : V → G) (A : Connection (E := E) (G := G)) (e : E) : G :=
  GroupLike.mul (GroupLike.mul (GroupLike.inv (frame (D.tgt e))) (A e))
    (frame (D.src e))

def canonicalGauge (PA PB : V → G) (k : G) : Gauge (V := V) (G := G) :=
  fun v => GroupLike.mul (GroupLike.mul (PB v) k) (GroupLike.inv (PA v))

theorem canonicalGauge_chord
    (D : Graph (V := V) (E := E))
    (A B : Connection (E := E) (G := G))
    (PA PB : V → G) (k : G)
    (he : ∀ e, D.isChord e →
      chordHolonomy D PB B e =
        GroupLike.mul (GroupLike.mul k (chordHolonomy D PA A e))
          (GroupLike.inv k))
    (e : E) (hc : D.isChord e) :
    act D A (canonicalGauge PA PB k) e = B e := by
  have h := he e hc
  have h' := congrArg (fun x => GroupLike.mul (PB (D.tgt e)) x) h
  have h'' := congrArg (fun x => GroupLike.mul x (GroupLike.inv (PB (D.src e)))) h'
  simp [chordHolonomy, GroupLike.mul_assoc, inv_mul_left_cancel,
    mul_inv_left_cancel, GroupLike.inv_mul_cancel, GroupLike.mul_inv_cancel,
    GroupLike.one_mul, GroupLike.mul_one] at h''
  simpa [act, canonicalGauge, GroupLike.inv_mul, GroupLike.inv_inv,
    GroupLike.mul_assoc] using h''.symm

theorem canonicalGauge_tree
    (D : Graph (V := V) (E := E))
    (A B : Connection (E := E) (G := G))
    (PA PB : V → G) (k : G)
    (hA : ∀ e, D.isTree e →
      PA (D.tgt e) = GroupLike.mul (A e) (PA (D.src e)))
    (hB : ∀ e, D.isTree e →
      PB (D.tgt e) = GroupLike.mul (B e) (PB (D.src e)))
    (e : E) (ht : D.isTree e) :
    act D A (canonicalGauge PA PB k) e = B e := by
  have hAe := hA e ht
  have hBe := hB e ht
  simp [act, canonicalGauge, hAe, hBe, GroupLike.inv_mul,
    GroupLike.inv_inv, GroupLike.mul_assoc, inv_mul_left_cancel,
    mul_inv_left_cancel, GroupLike.inv_mul_cancel, GroupLike.mul_inv_cancel,
    GroupLike.one_mul, GroupLike.mul_one]

theorem canonicalGauge_isArrow
    (D : Graph (V := V) (E := E))
    (A B : Connection (E := E) (G := G))
    (PA PB : V → G) (k : G)
    (hA : ∀ e, D.isTree e →
      PA (D.tgt e) = GroupLike.mul (A e) (PA (D.src e)))
    (hB : ∀ e, D.isTree e →
      PB (D.tgt e) = GroupLike.mul (B e) (PB (D.src e)))
    (hChord : ∀ e, D.isChord e →
      chordHolonomy D PB B e =
        GroupLike.mul (GroupLike.mul k (chordHolonomy D PA A e))
          (GroupLike.inv k)) :
    act D A (canonicalGauge PA PB k) = B := by
  funext e
  rcases D.cover e with ht | hc
  · exact canonicalGauge_tree D A B PA PB k hA hB e ht
  · exact canonicalGauge_chord D A B PA PB k hChord e hc
/-- A gauge compatible with the two tree frames is uniquely determined by
    its basepoint component. This is the injectivity half of full faithfulness. -/
theorem canonicalGauge_unique
    (PA PB : V → G) (g : Gauge (V := V) (G := G)) (k : G)
    (hFrame : ∀ v,
      PB v = GroupLike.mul
        (GroupLike.mul (g v) (PA v)) (GroupLike.inv k)) :
    g = canonicalGauge PA PB k := by
  funext v
  have hmul : GroupLike.mul (PB v) k =
      GroupLike.mul (g v) (PA v) := by
    have h := congrArg (fun x => GroupLike.mul x k) (hFrame v)
    simpa [GroupLike.mul_assoc, GroupLike.inv_mul_cancel,
      GroupLike.mul_one] using h
  change g v = GroupLike.mul
    (GroupLike.mul (PB v) k) (GroupLike.inv (PA v))
  calc
    g v = GroupLike.mul
      (GroupLike.mul (g v) (PA v)) (GroupLike.inv (PA v)) := by
        simp [GroupLike.mul_assoc, GroupLike.mul_inv_cancel, GroupLike.mul_one]
    _ = GroupLike.mul
      (GroupLike.mul (PB v) k) (GroupLike.inv (PA v)) := by rw [← hmul]

/-- Coordinates for a representation of the free group on the chord set:
    a homomorphism out of a free group is determined by these generator values. -/
def ChordRep (D : Graph (V := V) (E := E)) :=
  { rho : E → G // ∀ e, D.isTree e → rho e = (GroupLike.one : G) }

/-- The tree-gauge representative of a chord representation: tree edges are
    assigned the identity and chord edges their generator holonomy. -/
def treeGaugeRepresentative (D : Graph (V := V) (E := E))
    (rho : ChordRep (G := G) D) : Connection (E := E) (G := G) :=
  rho.1

theorem treeGaugeRepresentative_tree
    (D : Graph (V := V) (E := E)) (rho : ChordRep (G := G) D)
    (e : E) (ht : D.isTree e) :
    treeGaugeRepresentative D rho e = (GroupLike.one : G) :=
  rho.2 e ht

theorem treeGaugeRepresentative_has_trivial_frame
    (D : Graph (V := V) (E := E)) (rho : ChordRep (G := G) D) :
    ∀ e, D.isTree e →
      (fun _ : V => (GroupLike.one : G)) (D.tgt e) =
        GroupLike.mul (treeGaugeRepresentative D rho e)
          ((fun _ : V => (GroupLike.one : G)) (D.src e)) := by
  intro e ht
  simp [treeGaugeRepresentative, rho.2 e ht, GroupLike.one_mul]

theorem treeGaugeRepresentative_chord_holonomy
    (D : Graph (V := V) (E := E)) (rho : ChordRep (G := G) D)
    (e : E) :
    chordHolonomy D (fun _ : V => (GroupLike.one : G))
      (treeGaugeRepresentative D rho) e = rho.1 e := by
  have hone : GroupLike.inv (GroupLike.one : G) = (GroupLike.one : G) := by
    calc
      GroupLike.inv (GroupLike.one : G) =
          GroupLike.mul (GroupLike.inv (GroupLike.one : G)) (GroupLike.one : G) := by
            rw [GroupLike.mul_one]
      _ = GroupLike.one := GroupLike.inv_mul_cancel (GroupLike.one : G)
  simp [chordHolonomy, treeGaugeRepresentative, hone,
    GroupLike.inv_mul_cancel, GroupLike.one_mul, GroupLike.mul_one]

/-- Edge-indexed walks in a graph with a chosen orientation for each edge. -/
inductive EdgeWalk (D : Graph (V := V) (E := E)) : V → V → Type (max u v)
  | nil (x : V) : EdgeWalk D x x
  | cons {x y z : V} (e : E) (hs : D.src e = x) (ht : D.tgt e = y)
      (tail : EdgeWalk D y z) : EdgeWalk D x z

/-- Ordered parallel transport along an edge-indexed walk. -/
def edgeTransport (D : Graph (V := V) (E := E))
    (A : Connection (E := E) (G := G)) :
    {x y : V} → EdgeWalk D x y → G
  | _, _, EdgeWalk.nil _ => GroupLike.one
  | _, _, EdgeWalk.cons e _ _ tail =>
      GroupLike.mul (edgeTransport D A tail) (A e)

/-- Path transport is covariant under the vertex gauge action. -/
theorem edgeTransport_gauge_covariant
    (D : Graph (V := V) (E := E))
    (A : Connection (E := E) (G := G))
    (g : Gauge (V := V) (G := G)) :
    ∀ {x y : V} (p : EdgeWalk D x y),
      edgeTransport D (act D A g) p =
        GroupLike.mul
          (GroupLike.mul (g y) (edgeTransport D A p))
          (GroupLike.inv (g x)) := by
  intro x y p
  induction p with
  | nil z =>
      simp [edgeTransport, GroupLike.one_mul, GroupLike.mul_one,
        GroupLike.inv_inv, GroupLike.mul_inv_cancel]
  | @cons x y z e hs ht tail ih =>
      subst x
      subst y
      simp only [edgeTransport, act]
      rw [ih]
      simp [GroupLike.mul_assoc, inv_mul_left_cancel, GroupLike.inv_mul_cancel,
        GroupLike.mul_inv_cancel, GroupLike.one_mul, GroupLike.mul_one]

/-- If PA and PB are transports along the same chosen root-to-vertex tree
    paths, any gauge arrow induces the expected basepoint-conjugated frame
    relation. This is the missing bridge from actual tree paths to the
    uniqueness theorem above. -/
theorem treeFrames_covariant
    (D : Graph (V := V) (E := E))
    (A B : Connection (E := E) (G := G))
    (g : Gauge (V := V) (G := G))
    (root : V) (paths : ∀ v, EdgeWalk D root v)
    (hArrow : act D A g = B)
    (PA PB : V → G)
    (hPA : ∀ v, PA v = edgeTransport D A (paths v))
    (hPB : ∀ v, PB v = edgeTransport D B (paths v)) :
    ∀ v, PB v =
      GroupLike.mul
        (GroupLike.mul (g v) (PA v))
        (GroupLike.inv (g root)) := by
  intro v
  rw [hPB, hPA]
  have hcov := edgeTransport_gauge_covariant D A g (paths v)
  rw [hArrow] at hcov
  exact hcov

/-- Holonomy of a chord transforms by the root conjugator when the frames
    are transports along common root paths. -/
theorem chordHolonomy_gauge_covariant
    (D : Graph (V := V) (E := E))
    (A B : Connection (E := E) (G := G))
    (g : Gauge (V := V) (G := G)) (k : G)
    (PA PB : V → G)
    (hArrow : act D A g = B)
    (hFrame : ∀ v, PB v =
      GroupLike.mul (GroupLike.mul (g v) (PA v)) (GroupLike.inv k))
    (e : E) :
    chordHolonomy D PB B e =
      GroupLike.mul
        (GroupLike.mul k (chordHolonomy D PA A e))
        (GroupLike.inv k) := by
  rw [← hArrow]
  simp [chordHolonomy, act, hFrame, GroupLike.inv_mul,
    GroupLike.inv_inv, GroupLike.mul_assoc, inv_mul_left_cancel,
    mul_inv_left_cancel, GroupLike.inv_mul_cancel,
    GroupLike.mul_inv_cancel, GroupLike.one_mul, GroupLike.mul_one]

/-- A walk is tree-supported when every edge in it belongs to the selected
    spanning-tree edge family. -/
def IsTreeWalk (D : Graph (V := V) (E := E)) :
    {x y : V} → EdgeWalk D x y → Prop
  | _, _, EdgeWalk.nil _ => True
  | _, _, EdgeWalk.cons e _ _ tail =>
      D.isTree e ∧ IsTreeWalk D tail

/-- Explicit rooted spanning-tree certificate.

The certificate supplies one root-to-vertex walk, proves it uses only tree
edges, and certifies uniqueness among all tree-supported walks. The transport
recursion field records the orientation convention needed by the gauge proof.
The existence of such a certificate from abstract graph connectedness and
acyclicity is a separate graph-theoretic theorem, deliberately not hidden here.
-/
structure RootedSpanningTree (D : Graph (V := V) (E := E)) where
  root : V
  paths : ∀ v, EdgeWalk D root v
  rootPath : paths root = EdgeWalk.nil root
  paths_tree_supported : ∀ v, IsTreeWalk D (paths v)
  unique_tree_path : ∀ v (p : EdgeWalk D root v),
    IsTreeWalk D p → p = paths v
  transport_recursion : forall (A : Connection (E := E) (G := G))
    (e : E), D.isTree e ->
      edgeTransport D A (paths (D.tgt e)) =
        GroupLike.mul (A e)
          (edgeTransport D A (paths (D.src e)))

/-- The tree frame is the parallel transport from the certified root. -/
def treeFrame (D : Graph (V := V) (E := E))
    (T : RootedSpanningTree (V := V) (E := E) (G := G) D)
    (A : Connection (E := E) (G := G)) : V → G :=
  fun v => edgeTransport D A (T.paths v)

theorem treeFrame_root
    (D : Graph (V := V) (E := E))
    (T : RootedSpanningTree (V := V) (E := E) (G := G) D)
    (A : Connection (E := E) (G := G)) :
    treeFrame (G := G) D T A T.root = (GroupLike.one : G) := by
  unfold treeFrame
  rw [T.rootPath]
  rfl

theorem treeFrame_recursion
    (D : Graph (V := V) (E := E))
    (T : RootedSpanningTree (V := V) (E := E) (G := G) D)
    (A : Connection (E := E) (G := G))
    (e : E) (ht : D.isTree e) :
    treeFrame (G := G) D T A (D.tgt e) =
      GroupLike.mul (A e) (treeFrame (G := G) D T A (D.src e)) :=
  T.transport_recursion A e ht

/-- A chord-conjugacy witness and a rooted spanning-tree certificate
    reconstruct a gauge arrow. This is the first theorem where the abstract
    frame hypotheses are discharged by an explicit tree certificate. -/
theorem spanningTree_reconstruct_gauge
    (D : Graph (V := V) (E := E))
    (T : RootedSpanningTree (V := V) (E := E) (G := G) D)
    (A B : Connection (E := E) (G := G)) (k : G)
    (hChord : ∀ e, D.isChord e →
      chordHolonomy D (treeFrame (G := G) D T B) B e =
        GroupLike.mul
          (GroupLike.mul k (chordHolonomy D (treeFrame (G := G) D T A) A e))
          (GroupLike.inv k)) :
    act D A
      (canonicalGauge (treeFrame (G := G) D T A) (treeFrame (G := G) D T B) k) = B := by
  apply canonicalGauge_isArrow
  · exact treeFrame_recursion D T A
  · exact treeFrame_recursion D T B
  · exact hChord

/-- The reconstructed gauge has basepoint component k when both tree
    transports are normalized at the root. -/
theorem spanningTree_reconstruct_basepoint
    (D : Graph (V := V) (E := E))
    (T : RootedSpanningTree (V := V) (E := E) (G := G) D)
    (A B : Connection (E := E) (G := G)) (k : G) :
    canonicalGauge (treeFrame (G := G) D T A) (treeFrame (G := G) D T B) k T.root = k := by
  have hone : GroupLike.inv (GroupLike.one : G) = GroupLike.one := by
    calc
      GroupLike.inv (GroupLike.one : G) =
          GroupLike.mul (GroupLike.inv (GroupLike.one : G)) GroupLike.one := by
            rw [GroupLike.mul_one]
      _ = GroupLike.one := GroupLike.inv_mul_cancel (GroupLike.one : G)
  simp [canonicalGauge, treeFrame_root, hone, GroupLike.one_mul,
    GroupLike.mul_one, GroupLike.inv_mul_cancel]

end Cerp.GraphGaugeClassification
