/-!
# Contextual descent, gluing uniqueness, and presheaf obstruction (T5)

Formalizes the strict descent / sheaf gluing square for context-indexed
semantic assignments together with a finite Specker / Abramsky-Brandenburger
triangle presheaf witness showing that pairwise-consistent local marginals and
per-context satisfiability can obstruct any global section.
-/

namespace Cerp.ContextualDescentObstruction

universe u v w

structure ContextCover where
  Ctx : Type u
  Var : Type v
  inCtx : Ctx -> Var -> Prop
  Val : Var -> Type w
  total : forall x : Var, Exists (fun c : Ctx => inCtx c x)

def LocalSection (S : ContextCover.{u, v, w}) (c : S.Ctx) :=
  forall x : S.Var, S.inCtx c x -> S.Val x

def GlobalSection (S : ContextCover.{u, v, w}) :=
  forall x : S.Var, S.Val x

def restrictSection (S : ContextCover.{u, v, w})
    (g : GlobalSection S) (c : S.Ctx) : LocalSection S c :=
  fun x _ => g x

def LocallyCompatible (S : ContextCover.{u, v, w})
    (f : forall c : S.Ctx, LocalSection S c) : Prop :=
  forall c1 c2 x (h1 : S.inCtx c1 x) (h2 : S.inCtx c2 x),
    f c1 x h1 = f c2 x h2

def Glues (S : ContextCover.{u, v, w})
    (f : forall c : S.Ctx, LocalSection S c) (g : GlobalSection S) : Prop :=
  forall c x (hx : S.inCtx c x), g x = f c x hx

theorem globalSection_induces_compatible
    (S : ContextCover.{u, v, w}) (g : GlobalSection S) :
    LocallyCompatible S (restrictSection S g) := by
  intro _c1 _c2 _x _h1 _h2
  rfl

theorem globalSection_glues_restrict
    (S : ContextCover.{u, v, w}) (g : GlobalSection S) :
    Glues S (restrictSection S g) g := by
  intro _c _x _hx
  rfl

theorem gluing_implies_compatible
    (S : ContextCover.{u, v, w})
    (f : forall c : S.Ctx, LocalSection S c)
    (hglue : Exists (fun g : GlobalSection S => Glues S f g)) :
    LocallyCompatible S f := by
  obtain ⟨g, hg⟩ := hglue
  intro c1 c2 x h1 h2
  exact (hg c1 x h1).symm.trans (hg c2 x h2)

theorem glued_section_unique
    (S : ContextCover.{u, v, w})
    (f : forall c : S.Ctx, LocalSection S c)
    {g1 g2 : GlobalSection S}
    (h1 : Glues S f g1) (h2 : Glues S f g2) :
    g1 = g2 := by
  funext x
  obtain ⟨c, hc⟩ := S.total x
  exact (h1 c x hc).trans (h2 c x hc).symm

/-- Explicit 3-context Specker triangle cover:
    context 0 covers {0, 1}, context 1 covers {1, 2}, context 2 covers {2, 0}. -/
def speckerInCtx (c x : Fin 3) : Bool :=
  (x == c) || (x.val == (c.val + 1) % 3)

theorem specker_in_left (c : Fin 3) : speckerInCtx c c = true := by
  simp [speckerInCtx]

theorem specker_in_right_0 : speckerInCtx 0 1 = true := by decide
theorem specker_in_right_1 : speckerInCtx 1 2 = true := by decide
theorem specker_in_right_2 : speckerInCtx 2 0 = true := by decide

def speckerCover : ContextCover.{0, 0, 0} where
  Ctx := Fin 3
  Var := Fin 3
  inCtx := fun c x => speckerInCtx c x = true
  Val := fun _ => Bool
  total := fun x => ⟨x, specker_in_left x⟩

/-- Empirical anti-correlation on each triangle edge (0-1, 1-2, 2-0). -/
def SpeckerEdgeValid (f : forall c : Fin 3, LocalSection speckerCover c) : Prop :=
  (f (0 : Fin 3) (0 : Fin 3) (specker_in_left 0) ≠
     f (0 : Fin 3) (1 : Fin 3) specker_in_right_0) ∧
  (f (1 : Fin 3) (1 : Fin 3) (specker_in_left 1) ≠
     f (1 : Fin 3) (2 : Fin 3) specker_in_right_1) ∧
  (f (2 : Fin 3) (2 : Fin 3) (specker_in_left 2) ≠
     f (2 : Fin 3) (0 : Fin 3) specker_in_right_2)

/-- Individual local sections satisfy each edge anti-correlation condition. -/
def speckerEdgeAssignment (c x : Fin 3) : Bool :=
  x != c

theorem specker_each_context_locally_consistent :
    (speckerEdgeAssignment 0 0 ≠ speckerEdgeAssignment 0 1) ∧
    (speckerEdgeAssignment 1 1 ≠ speckerEdgeAssignment 1 2) ∧
    (speckerEdgeAssignment 2 2 ≠ speckerEdgeAssignment 2 0) := by
  decide

/-- Uniform coin-flip empirical marginal weight (numerator out of 2) for each variable
    within any triangle context: two local sections [(false,true),(true,false)] give
    weight 1/2 to `true` on both endpoints, so overlap marginals match pairwise. -/
def speckerLocalTable (_c : Fin 3) : List (Bool × Bool) :=
  [(false, true), (true, false)]

def speckerLeftMarginalTrue (c : Fin 3) : Nat :=
  ((speckerLocalTable c).filter (fun p => p.1 == true)).length

def speckerRightMarginalTrue (c : Fin 3) : Nat :=
  ((speckerLocalTable c).filter (fun p => p.2 == true)).length

theorem specker_overlap_marginals_agree (c c' : Fin 3) :
    speckerLeftMarginalTrue c = speckerRightMarginalTrue c' := by
  rfl

/-- Pure Boolean parity obstruction: no global section can simultaneously
    anti-correlate all three triangle edges. -/
theorem specker_triangle_no_global_section :
    Not (Exists (fun g : Fin 3 -> Bool =>
      g 0 ≠ g 1 ∧ g 1 ≠ g 2 ∧ g 2 ≠ g 0)) := by
  intro h
  rcases h with ⟨g, h01, h12, h20⟩
  cases h0 : g 0 <;> cases h1 : g 1 <;> cases h2 : g 2 <;> simp_all

/-- Strong contextual obstruction: no locally compatible family on the
    Specker triangle can satisfy all three edge anti-correlations, and hence
    no gluing global section exists. -/
theorem specker_no_compatible_valid_family
    (f : forall c : Fin 3, LocalSection speckerCover c)
    (hcomp : LocallyCompatible speckerCover f) :
    Not (SpeckerEdgeValid f) := by
  intro hvalid
  apply specker_triangle_no_global_section
  refine ⟨fun x => f x x (specker_in_left x), ?_⟩
  rcases hvalid with ⟨h01, h12, h20⟩
  refine ⟨?_, ?_, ?_⟩
  · intro h
    dsimp only at h
    exact h01 (h.trans (hcomp (1 : Fin 3) (0 : Fin 3) (1 : Fin 3)
      (specker_in_left 1) specker_in_right_0))
  · intro h
    dsimp only at h
    exact h12 (h.trans (hcomp (2 : Fin 3) (1 : Fin 3) (2 : Fin 3)
      (specker_in_left 2) specker_in_right_1))
  · intro h
    dsimp only at h
    exact h20 (h.trans (hcomp (0 : Fin 3) (2 : Fin 3) (0 : Fin 3)
      (specker_in_left 0) specker_in_right_2))

theorem specker_no_global_gluing_for_valid_family
    (f : forall c : Fin 3, LocalSection speckerCover c)
    (hvalid : SpeckerEdgeValid f) :
    Not (Exists (fun g : GlobalSection speckerCover => Glues speckerCover f g)) := by
  intro hglue
  exact specker_no_compatible_valid_family f (gluing_implies_compatible speckerCover f hglue) hvalid

end Cerp.ContextualDescentObstruction
