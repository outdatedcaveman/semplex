import GraphGaugeClassification

namespace Cerp.GraphGaugePathDecomposition

open Cerp.HoTTGaugeBridge
open Cerp.GraphGaugeClassification

universe u v w
variable {V : Type u} {E : Type v} {G : Type w} [GroupLike G]


/-- Concatenation of edge-indexed walks. The first walk is traversed first. -/
def append {D : Cerp.GraphGaugeClassification.Graph (V := V) (E := E)} :
    {x y z : V} → EdgeWalk D x y → EdgeWalk D y z → EdgeWalk D x z
  | _, _, _, EdgeWalk.nil _, q => q
  | _, _, _, EdgeWalk.cons e hs ht p, q =>
      EdgeWalk.cons e hs ht (append p q)

/-- Transport along a concatenation is the later transport multiplied
    on the left of the earlier transport, matching the chosen convention. -/
theorem edgeTransport_append
    (D : Cerp.GraphGaugeClassification.Graph (V := V) (E := E))
    (A : Cerp.GraphGaugeClassification.Connection (E := E) (G := G)) :
    ∀ {x y z : V} (p : EdgeWalk D x y) (q : EdgeWalk D y z),
      edgeTransport D A (append p q) =
        GroupLike.mul (edgeTransport D A q) (edgeTransport D A p) := by
  intro x y z p q
  induction p with
  | nil => simp [append, edgeTransport, GroupLike.mul_one]
  | @cons x y mid e hs ht tail ih =>
      simp [append, edgeTransport, ih, GroupLike.mul_assoc]

theorem append_tree_supported
    (D : Cerp.GraphGaugeClassification.Graph (V := V) (E := E)) :
    ∀ {x y z : V} (p : EdgeWalk D x y) (q : EdgeWalk D y z),
      IsTreeWalk D p → IsTreeWalk D q →
      IsTreeWalk D (append p q) := by
  intro x y z p q hp hq
  induction p with
  | nil => simpa [append] using hq
  | @cons x y mid e hs ht tail ih =>
      exact And.intro hp.1 (ih q hp.2 hq)
/-- A spanning-tree certificate with only path existence, tree support,
    and uniqueness. It does not assume the desired transport recursion. -/
structure RootedTreePaths (D : Cerp.GraphGaugeClassification.Graph (V := V) (E := E)) where
  root : V
  paths : ∀ v, EdgeWalk D root v
  rootPath : paths root = EdgeWalk.nil root
  paths_tree_supported : ∀ v, IsTreeWalk D (paths v)
  unique_tree_path : ∀ v (p : EdgeWalk D root v),
    IsTreeWalk D p → p = paths v

/-- Every tree edge extends the unique root path to its source into the
    unique root path to its target. This is derived, not postulated. -/
theorem tree_edge_path_decomposition
    (D : Cerp.GraphGaugeClassification.Graph (V := V) (E := E))
    (T : RootedTreePaths D)
    (e : E) (ht : D.isTree e) :
    append (T.paths (D.src e))
        (EdgeWalk.cons e rfl rfl (EdgeWalk.nil (D.tgt e))) =
      T.paths (D.tgt e) := by
  apply T.unique_tree_path
  exact append_tree_supported D (T.paths (D.src e))
    (EdgeWalk.cons e rfl rfl (EdgeWalk.nil (D.tgt e)))
    (T.paths_tree_supported (D.src e)) (And.intro ht trivial)

/-- The transport recursion previously stored as a certificate field now
    follows from unique tree paths and the concatenation theorem. -/
theorem tree_transport_recursion
    (D : Cerp.GraphGaugeClassification.Graph (V := V) (E := E))
    (T : RootedTreePaths D)
    (A : Cerp.GraphGaugeClassification.Connection (E := E) (G := G))
    (e : E) (ht : D.isTree e) :
    edgeTransport D A (T.paths (D.tgt e)) =
      GroupLike.mul (A e) (edgeTransport D A (T.paths (D.src e))) := by
  rw [← tree_edge_path_decomposition D T e ht]
  rw [edgeTransport_append]
  simp [edgeTransport, GroupLike.one_mul]

/-- Convert the weaker path certificate into the existing reconstruction
    certificate, discharging its transport-recursion field. -/
def toRootedSpanningTree
    (D : Cerp.GraphGaugeClassification.Graph (V := V) (E := E))
    (T : RootedTreePaths D) :
    RootedSpanningTree (G := G) D where
  root := T.root
  paths := T.paths
  rootPath := T.rootPath
  paths_tree_supported := T.paths_tree_supported
  unique_tree_path := T.unique_tree_path
  transport_recursion := fun A e ht => tree_transport_recursion D T A e ht

end Cerp.GraphGaugePathDecomposition
