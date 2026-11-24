/-!
# Unified Cech H^1 / Gauge-Isotropy Exact Sequence & Monolith Impossibility

Constructive Pure Lean 4 unification of the two core epistemic obstructions
beyond profile quotienting (`G_prof`):

1. **Cover Cech H^1 & Gauge-Gluing Obstruction (`gluesByGauge_iff_transition_coboundary`):**
   Formalizes local context sections `ContextSection Γ S c` over a cover `S`,
   their overlap transition elements `contextTransition`, and proves that a
   local family admits an `H`-gauge correction gluing it to a global `G`-section
   if and only if its overlap transitions form an `H`-coboundary
   (`u c₁ * (u c₂)⁻¹`). Also includes the discrete `CoverGraph` exactness
   characterizations `connecting_trivial_iff_lift` and `exactness_at_H1_H`.

2. **Non-Vacuous Anchor-Induced Contextual Obstruction (`C4` Specker Triangle):**
   On the 3-context triangle over `G = C4`, unanchored global realizations exist
   (`c1, c1, c1` and `c3, c3, c3`) with `H = {c0, c2} ~= C2` residual symmetry.
   Anchoring values to coset `0 mod 2` (`c2InC4`) remains locally satisfiable on
   every edge, yet **zero** global realizations exist (`c4_triangle_coset0_anchor_no_global_realization`),
   witnessed by the non-trivial connecting cocycle `speckerC2Cocycle`
   (`speckerC2Cocycle_nontrivial`) on the 3-context nerve (`U_0 ∩ U_1 ∩ U_2 = ∅`),
   whereas coset `1 mod 2` restores gluing with residual `C2` isotropy.

3. **Monolith Partial-Anchor Impossibility (`hasMonolith_not_partialAnchorAdequate`):**
   Whenever a symmetry group `G` has a monolith `z != 1` lying in every
   non-trivial subgroup (`HasMonolith G`), NO finite family of non-trivial
   partial anchor subgroups can intersect to `{1}`. Proved constructively for
   `C4` and non-abelian `Q8` (`q8_not_partialAnchorAdequate`), contrasted with
   abelian `C2^3` of the same order `8` (`c2cubed_partialAnchorAdequate`).

Zero `Classical.choice`, zero `sorryAx`, zero Mathlib dependencies.
-/

namespace Cerp.ObstructionExactSequence

universe u v w

/-- Minimal constructive group interface. -/
structure FinGroup (G : Type u) where
  one : G
  mul : G → G → G
  inv : G → G
  mul_assoc : ∀ a b c : G, mul (mul a b) c = mul a (mul b c)
  one_mul : ∀ a : G, mul one a = a
  mul_one : ∀ a : G, mul a one = a
  mul_left_inv : ∀ a : G, mul (inv a) a = one
  mul_right_inv : ∀ a : G, mul a (inv a) = one

section GroupLemmas

variable {G : Type u} (Γ : FinGroup G)

theorem inv_mul_cancel_left (a b : G) :
    Γ.mul (Γ.inv a) (Γ.mul a b) = b := by
  rw [← Γ.mul_assoc, Γ.mul_left_inv, Γ.one_mul]

theorem mul_inv_cancel_left (a b : G) :
    Γ.mul a (Γ.mul (Γ.inv a) b) = b := by
  rw [← Γ.mul_assoc, Γ.mul_right_inv, Γ.one_mul]

theorem mul_inv_cancel_right (a b : G) :
    Γ.mul (Γ.mul a b) (Γ.inv b) = a := by
  rw [Γ.mul_assoc, Γ.mul_right_inv, Γ.mul_one]

theorem inv_mul_cancel_right (a b : G) :
    Γ.mul (Γ.mul a (Γ.inv b)) b = a := by
  rw [Γ.mul_assoc, Γ.mul_left_inv, Γ.mul_one]

theorem mul_left_cancel {a b c : G} (h : Γ.mul a b = Γ.mul a c) : b = c := by
  have h1 := congrArg (Γ.mul (Γ.inv a)) h
  simpa [inv_mul_cancel_left Γ] using h1

theorem mul_right_cancel {a b c : G} (h : Γ.mul a c = Γ.mul b c) : a = b := by
  have h1 := congrArg (fun z => Γ.mul z (Γ.inv c)) h
  simpa [mul_inv_cancel_right Γ] using h1

theorem eq_inv_of_mul_eq_one {a b : G} (h : Γ.mul a b = Γ.one) : a = Γ.inv b := by
  apply mul_right_cancel Γ (c := b)
  rw [h, Γ.mul_left_inv]

theorem inv_inv (a : G) : Γ.inv (Γ.inv a) = a :=
  (eq_inv_of_mul_eq_one Γ (Γ.mul_right_inv a)).symm

theorem inv_one : Γ.inv Γ.one = Γ.one := by
  symm
  exact eq_inv_of_mul_eq_one Γ (Γ.one_mul Γ.one)

theorem inv_mul_rev (a b : G) :
    Γ.inv (Γ.mul a b) = Γ.mul (Γ.inv b) (Γ.inv a) := by
  symm
  apply eq_inv_of_mul_eq_one Γ
  calc
    Γ.mul (Γ.mul (Γ.inv b) (Γ.inv a)) (Γ.mul a b)
        = Γ.mul (Γ.inv b) (Γ.mul (Γ.inv a) (Γ.mul a b)) := Γ.mul_assoc _ _ _
    _ = Γ.mul (Γ.inv b) b := by rw [inv_mul_cancel_left]
    _ = Γ.one := Γ.mul_left_inv b

end GroupLemmas

/-- Subgroup of `Γ`. -/
structure Subgroup {G : Type u} (Γ : FinGroup G) where
  mem : G → Prop
  one_mem : mem Γ.one
  mul_mem : ∀ {a b}, mem a → mem b → mem (Γ.mul a b)
  inv_mem : ∀ {a}, mem a → mem (Γ.inv a)

def topSubgroup {G : Type u} (Γ : FinGroup G) : Subgroup Γ where
  mem := fun _ => True
  one_mem := trivial
  mul_mem := fun _ _ => trivial
  inv_mem := fun _ => trivial

def Subgroup.inter {G : Type u} {Γ : FinGroup G} (H₁ H₂ : Subgroup Γ) : Subgroup Γ where
  mem := fun g => H₁.mem g ∧ H₂.mem g
  one_mem := ⟨H₁.one_mem, H₂.one_mem⟩
  mul_mem := fun ha hb => ⟨H₁.mul_mem ha.1 hb.1, H₂.mul_mem ha.2 hb.2⟩
  inv_mem := fun ha => ⟨H₁.inv_mem ha.1, H₂.inv_mem ha.2⟩

def Subgroup.interList {G : Type u} (Γ : FinGroup G) : List (Subgroup Γ) → Subgroup Γ
  | [] => topSubgroup Γ
  | H :: rest => Subgroup.inter H (Subgroup.interList Γ rest)

theorem Subgroup.mem_interList_iff {G : Type u} (Γ : FinGroup G)
    (Hs : List (Subgroup Γ)) (g : G) :
    (Subgroup.interList Γ Hs).mem g ↔ ∀ H ∈ Hs, H.mem g := by
  induction Hs with
  | nil =>
      constructor
      · intro _ H hmem; cases hmem
      · intro _; trivial
  | cons H rest ih =>
      constructor
      · intro ⟨hH, hRest⟩ H' hmem
        rcases List.mem_cons.mp hmem with rfl | hmemRest
        · exact hH
        · exact (ih.mp hRest) H' hmemRest
      · intro hAll
        exact ⟨hAll H (List.mem_cons_self _ _),
          ih.mpr (fun H' hm => hAll H' (List.mem_cons_of_mem _ hm))⟩

/-- Group action of `Γ` on a carrier `X`, inducing anchor stabilizers. -/
structure GroupAction {G : Type u} (Γ : FinGroup G) (X : Type v) where
  act : G → X → X
  act_one : ∀ x, act Γ.one x = x
  act_mul : ∀ g h x, act (Γ.mul g h) x = act g (act h x)

def stabilizerSubgroup {G : Type u} {Γ : FinGroup G} {X : Type v} {Y : Type w}
    (A : GroupAction Γ X) (probe : X → Y) : Subgroup Γ where
  mem := fun g => ∀ x, probe (A.act g x) = probe x
  one_mem := fun x => by rw [A.act_one]
  mul_mem := fun {a b} ha hb x => by
    rw [A.act_mul, ha (A.act b x), hb x]
  inv_mem := fun {a} ha x => by
    have h1 := ha (A.act (Γ.inv a) x)
    rw [← A.act_mul, Γ.mul_right_inv, A.act_one] at h1
    exact h1.symm

theorem stabilizer_interList {G : Type u} {Γ : FinGroup G} {X : Type v} {Y : Type w}
    (A : GroupAction Γ X) (probes : List (X → Y)) (g : G) :
    (Subgroup.interList Γ (probes.map (stabilizerSubgroup A))).mem g ↔
      ∀ p ∈ probes, ∀ x, p (A.act g x) = p x := by
  rw [Subgroup.mem_interList_iff]
  constructor
  · intro h p hp
    exact h (stabilizerSubgroup A p) (List.mem_map_of_mem (stabilizerSubgroup A) hp)
  · intro h H hH
    rcases List.mem_map.mp hH with ⟨p, hp, rfl⟩
    exact h p hp

/-! ## Section 1: Cover Cech H^1, Gauge-Gluing Criterion & 1 -> H -> G -> G/H Exact Sequence -/

/-- Context cover nerve (`overlap`: pairwise `U_i ∩ U_j ≠ ∅`; `overlap3`: triple `U_i ∩ U_j ∩ U_k ≠ ∅`). -/
structure CoverGraph (I : Type v) where
  overlap : I → I → Prop
  overlap_refl : ∀ i, overlap i i
  overlap_symm : ∀ {i j}, overlap i j → overlap j i
  overlap3 : I → I → I → Prop
  overlap3_diag : ∀ i, overlap3 i i i

/-- An `H`-valued 1-cocycle on overlapping contexts of `E` (cocycle law on non-empty triple overlaps). -/
structure Cocycle1 {G : Type u} (Γ : FinGroup G) (H : Subgroup Γ)
    {I : Type v} (E : CoverGraph I) where
  val : I → I → G
  in_H : ∀ {i j}, E.overlap i j → H.mem (val i j)
  cocycle : ∀ {i j k}, E.overlap3 i j k →
    Γ.mul (val i j) (val j k) = val i k

/-- Trivial class in `H^1(E; H)`: `c i j = (u i)⁻¹ * (u j)` with `u i ∈ H`. -/
def IsCoboundary {G : Type u} (Γ : FinGroup G) (H : Subgroup Γ)
    {I : Type v} (E : CoverGraph I) (c : Cocycle1 Γ H E) : Prop :=
  ∃ u : I → G, (∀ i, H.mem (u i)) ∧
    ∀ {i j}, E.overlap i j → c.val i j = Γ.mul (Γ.inv (u i)) (u j)

theorem cocycle_diag_one {G : Type u} {Γ : FinGroup G} {H : Subgroup Γ}
    {I : Type v} {E : CoverGraph I} (c : Cocycle1 Γ H E) (i : I) :
    c.val i i = Γ.one := by
  have hc := c.cocycle (E.overlap3_diag i)
  apply mul_left_cancel Γ (a := c.val i i)
  rw [hc, Γ.mul_one]

/-- Gluing equivalence on a general 1-cocycle over `E`. -/
theorem globalRealization_iff_coboundary {G : Type u} (Γ : FinGroup G) (H : Subgroup Γ)
    {I : Type v} (E : CoverGraph I) (c : Cocycle1 Γ H E) :
    IsCoboundary Γ H E c ↔
      ∃ u : I → G, (∀ i, H.mem (u i)) ∧
        ∀ {i j}, E.overlap i j → Γ.mul (u i) (c.val i j) = u j := by
  constructor
  · rintro ⟨u, hu, hcov⟩
    refine ⟨u, hu, fun {i j} hij => ?_⟩
    rw [hcov hij, mul_inv_cancel_left Γ]
  · rintro ⟨u, hu, hact⟩
    refine ⟨u, hu, fun {i j} hij => ?_⟩
    calc
      c.val i j = Γ.mul (Γ.inv (u i)) (Γ.mul (u i) (c.val i j)) :=
        (inv_mul_cancel_left Γ (u i) (c.val i j)).symm
      _ = Γ.mul (Γ.inv (u i)) (u j) := by rw [hact hij]

/-- Sheaf-style context cover with constructive witness selector `pick`. -/
structure VarContextCover (Ctx : Type v) (Var : Type w) where
  inCtx : Ctx → Var → Prop
  pick : ∀ x : Var, { c : Ctx // inCtx c x }

def LocalSection {G : Type u} {Ctx : Type v} {Var : Type w}
    (S : VarContextCover Ctx Var) (c : Ctx) :=
  ∀ x : Var, S.inCtx c x → G

def contextTransition {G : Type u} (Γ : FinGroup G) {Ctx : Type v} {Var : Type w}
    {S : VarContextCover Ctx Var} (s : ∀ c : Ctx, LocalSection (G := G) S c)
    {c₁ c₂ : Ctx} {x : Var} (h₁ : S.inCtx c₁ x) (h₂ : S.inCtx c₂ x) : G :=
  Γ.mul (Γ.inv (s c₁ x h₁)) (s c₂ x h₂)

/-- A family of local sections glues modulo `H`-gauge adjustments on patches iff
    there exist patch gauges `u c ∈ H` aligning overlaps (`s c x h * u c = r x`). -/
def GluesByGauge {G : Type u} (Γ : FinGroup G) (H : Subgroup Γ)
    {Ctx : Type v} {Var : Type w} (S : VarContextCover Ctx Var)
    (s : ∀ c : Ctx, LocalSection (G := G) S c) : Prop :=
  ∃ (r : Var → G) (u : Ctx → G),
    (∀ c, H.mem (u c)) ∧
    ∀ c x (hc : S.inCtx c x), r x = Γ.mul (s c x hc) (u c)

def IsTransitionCoboundary {G : Type u} (Γ : FinGroup G) (H : Subgroup Γ)
    {Ctx : Type v} {Var : Type w} (S : VarContextCover Ctx Var)
    (s : ∀ c : Ctx, LocalSection (G := G) S c) : Prop :=
  ∃ u : Ctx → G, (∀ c, H.mem (u c)) ∧
    ∀ c₁ c₂ x (h₁ : S.inCtx c₁ x) (h₂ : S.inCtx c₂ x),
      contextTransition Γ s h₁ h₂ = Γ.mul (u c₁) (Γ.inv (u c₂))

/-- **Fundamental Gluing-vs-Transition Obstruction Theorem (Constructive):**
    Local `G`-sections on a context cover admit a gauge-adjusted global gluing
    in `H` if and only if their overlap transition elements `(s c₁ x)⁻¹ * (s c₂ x)`
    form an `H`-coboundary `u c₁ * (u c₂)⁻¹`. -/
theorem gluesByGauge_iff_transition_coboundary {G : Type u} (Γ : FinGroup G) (H : Subgroup Γ)
    {Ctx : Type v} {Var : Type w} (S : VarContextCover Ctx Var)
    (s : ∀ c : Ctx, LocalSection (G := G) S c) :
    GluesByGauge Γ H S s ↔ IsTransitionCoboundary Γ H S s := by
  constructor
  · rintro ⟨r, u, hu, hglue⟩
    refine ⟨u, hu, fun c₁ c₂ x h₁ h₂ => ?_⟩
    have hr1 : r x = Γ.mul (s c₁ x h₁) (u c₁) := hglue c₁ x h₁
    have hr2 : r x = Γ.mul (s c₂ x h₂) (u c₂) := hglue c₂ x h₂
    have heq : Γ.mul (s c₁ x h₁) (u c₁) = Γ.mul (s c₂ x h₂) (u c₂) := hr1.symm.trans hr2
    have hinv := congrArg (Γ.mul (Γ.inv (s c₁ x h₁))) heq
    rw [inv_mul_cancel_left Γ] at hinv
    have hmul := congrArg (fun z => Γ.mul z (Γ.inv (u c₂))) hinv
    dsimp only at hmul
    have hright : Γ.mul (Γ.mul (Γ.inv (s c₁ x h₁)) (Γ.mul (s c₂ x h₂) (u c₂))) (Γ.inv (u c₂)) =
        Γ.mul (Γ.inv (s c₁ x h₁)) (s c₂ x h₂) := by
      rw [Γ.mul_assoc (Γ.inv (s c₁ x h₁)), Γ.mul_assoc (s c₂ x h₂), Γ.mul_right_inv, Γ.mul_one]
    rw [hright] at hmul
    exact hmul.symm
  · rintro ⟨u, hu, hcob⟩
    refine ⟨fun x => Γ.mul (s (S.pick x).1 x (S.pick x).2) (u (S.pick x).1), u, hu, ?_⟩
    intro c x hc
    have htr := hcob (S.pick x).1 c x (S.pick x).2 hc
    dsimp [contextTransition] at htr
    have h1 := congrArg (Γ.mul (s (S.pick x).1 x (S.pick x).2)) htr
    rw [mul_inv_cancel_left Γ] at h1
    have h2 := congrArg (fun z => Γ.mul z (u c)) h1
    dsimp only at h2
    have hrhs : Γ.mul (Γ.mul (s (S.pick x).1 x (S.pick x).2)
        (Γ.mul (u (S.pick x).1) (Γ.inv (u c)))) (u c) =
        Γ.mul (s (S.pick x).1 x (S.pick x).2) (u (S.pick x).1) := by
      rw [Γ.mul_assoc (s (S.pick x).1 x (S.pick x).2), Γ.mul_assoc (u (S.pick x).1),
        Γ.mul_left_inv, Γ.mul_one]
    rw [hrhs] at h2
    exact h2.symm

/-- Discrete `CoverGraph` connecting cocycle and exactness at `H^1(E; H)`. -/
def CompatibleQuotientSection {G : Type u} (Γ : FinGroup G) (H : Subgroup Γ)
    {I : Type v} (E : CoverGraph I) (σ : I → G) : Prop :=
  ∀ {i j}, E.overlap i j → H.mem (Γ.mul (Γ.inv (σ i)) (σ j))

def connectingCocycle {G : Type u} (Γ : FinGroup G) (H : Subgroup Γ)
    {I : Type v} (E : CoverGraph I) (σ : I → G)
    (hσ : CompatibleQuotientSection Γ H E σ) : Cocycle1 Γ H E where
  val := fun i j => Γ.mul (Γ.inv (σ i)) (σ j)
  in_H := fun hij => hσ hij
  cocycle := fun {_i _j _k} _ => by
    calc
      Γ.mul (Γ.mul (Γ.inv (σ _i)) (σ _j)) (Γ.mul (Γ.inv (σ _j)) (σ _k))
          = Γ.mul (Γ.inv (σ _i)) (Γ.mul (σ _j) (Γ.mul (Γ.inv (σ _j)) (σ _k))) :=
        Γ.mul_assoc _ _ _
      _ = Γ.mul (Γ.inv (σ _i)) (σ _k) := by rw [mul_inv_cancel_left Γ]

def HasLocallyConstantLift {G : Type u} (Γ : FinGroup G) (H : Subgroup Γ)
    {I : Type v} (E : CoverGraph I) (σ : I → G) : Prop :=
  ∃ l : I → G, (∀ {i j}, E.overlap i j → l i = l j) ∧
    ∀ i, H.mem (Γ.mul (Γ.inv (l i)) (σ i))

theorem connecting_trivial_iff_lift {G : Type u} (Γ : FinGroup G) (H : Subgroup Γ)
    {I : Type v} (E : CoverGraph I) (σ : I → G)
    (hσ : CompatibleQuotientSection Γ H E σ) :
    IsCoboundary Γ H E (connectingCocycle Γ H E σ hσ) ↔
      HasLocallyConstantLift Γ H E σ := by
  constructor
  · rintro ⟨u, hu, hcob⟩
    refine ⟨fun i => Γ.mul (σ i) (Γ.inv (u i)), ?_, ?_⟩
    · intro i j hij
      have hc := hcob hij
      dsimp [connectingCocycle] at hc
      have h1 : Γ.mul (σ i) (Γ.mul (Γ.inv (σ i)) (σ j)) =
          Γ.mul (σ i) (Γ.mul (Γ.inv (u i)) (u j)) := congrArg (Γ.mul (σ i)) hc
      rw [mul_inv_cancel_left Γ] at h1
      have h2 := congrArg (fun z => Γ.mul z (Γ.inv (u j))) h1
      calc
        Γ.mul (σ i) (Γ.inv (u i))
            = Γ.mul (σ i) (Γ.mul (Γ.inv (u i)) (Γ.mul (u j) (Γ.inv (u j)))) := by
              rw [Γ.mul_right_inv, Γ.mul_one]
        _ = Γ.mul (σ i) (Γ.mul (Γ.mul (Γ.inv (u i)) (u j)) (Γ.inv (u j))) := by
              rw [Γ.mul_assoc (Γ.inv (u i)) (u j) (Γ.inv (u j))]
        _ = Γ.mul (Γ.mul (σ i) (Γ.mul (Γ.inv (u i)) (u j))) (Γ.inv (u j)) := by
              rw [← Γ.mul_assoc (σ i)]
        _ = Γ.mul (σ j) (Γ.inv (u j)) := h2.symm
    · intro i
      have hi : Γ.mul (Γ.inv (Γ.mul (σ i) (Γ.inv (u i)))) (σ i) = u i := by
        rw [inv_mul_rev Γ, inv_inv Γ, Γ.mul_assoc, Γ.mul_left_inv, Γ.mul_one]
      rw [hi]
      exact hu i
  · rintro ⟨l, hl, hmem⟩
    refine ⟨fun i => Γ.mul (Γ.inv (l i)) (σ i), hmem, fun {i j} hij => ?_⟩
    have hli : l i = l j := hl hij
    dsimp [connectingCocycle]
    rw [inv_mul_rev Γ, inv_inv Γ, Γ.mul_assoc]
    calc
      Γ.mul (Γ.inv (σ i)) (σ j)
          = Γ.mul (Γ.inv (σ i)) (Γ.mul (Γ.mul (l i) (Γ.inv (l j))) (σ j)) := by
            rw [hli, Γ.mul_right_inv, Γ.one_mul]
      _ = Γ.mul (Γ.inv (σ i)) (Γ.mul (l i) (Γ.mul (Γ.inv (l j)) (σ j))) := by
            rw [Γ.mul_assoc]

theorem exactness_at_H1_H {G : Type u} (Γ : FinGroup G) (H : Subgroup Γ)
    {I : Type v} (E : CoverGraph I) (c : Cocycle1 Γ H E) :
    (∃ σ : I → G, ∀ {i j}, E.overlap i j → c.val i j = Γ.mul (Γ.inv (σ i)) (σ j)) ↔
      ∃ σ : I → G, ∃ hσ : CompatibleQuotientSection Γ H E σ,
        ∀ {i j}, E.overlap i j → c.val i j = (connectingCocycle Γ H E σ hσ).val i j := by
  constructor
  · rintro ⟨σ, hcob⟩
    have hσ : CompatibleQuotientSection Γ H E σ := by
      intro i j hij
      rw [← hcob hij]
      exact c.in_H hij
    exact ⟨σ, hσ, fun hij => hcob hij⟩
  · rintro ⟨σ, _hσ, heq⟩
    exact ⟨σ, fun hij => heq hij⟩

/-! ## Section 2: Anchor-Induced Contextual Obstruction on the C4 Specker Triangle -/

inductive C4 where
  | c0 | c1 | c2 | c3
  deriving DecidableEq, Repr

def c4Mul : C4 → C4 → C4
  | .c0, y => y
  | x, .c0 => x
  | .c1, .c1 => .c2
  | .c1, .c2 => .c3
  | .c1, .c3 => .c0
  | .c2, .c1 => .c3
  | .c2, .c2 => .c0
  | .c2, .c3 => .c1
  | .c3, .c1 => .c0
  | .c3, .c2 => .c1
  | .c3, .c3 => .c2

def c4Inv : C4 → C4
  | .c0 => .c0
  | .c1 => .c3
  | .c2 => .c2
  | .c3 => .c1

def c4Group : FinGroup C4 where
  one := .c0
  mul := c4Mul
  inv := c4Inv
  mul_assoc := by intro a b c; cases a <;> cases b <;> cases c <;> rfl
  one_mul := by intro a; cases a <;> rfl
  mul_one := by intro a; cases a <;> rfl
  mul_left_inv := by intro a; cases a <;> rfl
  mul_right_inv := by intro a; cases a <;> rfl

def c2InC4 : Subgroup c4Group where
  mem := fun a => a = .c0 ∨ a = .c2
  one_mem := Or.inl rfl
  mul_mem := by
    intro a b ha hb
    rcases ha with rfl | rfl <;> rcases hb with rfl | rfl <;> simp [c4Group, c4Mul]
  inv_mem := by
    intro a ha
    rcases ha with rfl | rfl <;> simp [c4Group, c4Inv]

inductive Tri where
  | v0 | v1 | v2
  deriving DecidableEq, Repr

def triInCtx : Tri → Tri → Prop
  | .v0, .v0 => True
  | .v0, .v1 => True
  | .v1, .v1 => True
  | .v1, .v2 => True
  | .v2, .v2 => True
  | .v2, .v0 => True
  | _, _ => False

def triPick (x : Tri) : { c : Tri // triInCtx c x } :=
  match x with
  | .v0 => ⟨.v0, trivial⟩
  | .v1 => ⟨.v1, trivial⟩
  | .v2 => ⟨.v2, trivial⟩

def speckerVarCover : VarContextCover Tri Tri where
  inCtx := triInCtx
  pick := triPick

def triOverlapBool : Tri → Tri → Bool
  | .v0, .v0 => true
  | .v1, .v1 => true
  | .v2, .v2 => true
  | .v0, .v1 => true
  | .v1, .v0 => true
  | .v1, .v2 => true
  | .v2, .v1 => true
  | .v2, .v0 => true
  | .v0, .v2 => true

def triOverlap3 (i j k : Tri) : Prop :=
  i = j ∨ j = k ∨ i = k

def triangleCover : CoverGraph Tri where
  overlap := fun i j => triOverlapBool i j = true
  overlap_refl := fun i => by cases i <;> rfl
  overlap_symm := by
    intro i j h
    cases i <;> cases j <;> exact h
  overlap3 := triOverlap3
  overlap3_diag := fun i => Or.inl rfl

def ValidTriangleRealization (r : Tri → C4) : Prop :=
  c4Mul (r .v0) (r .v1) = .c2 ∧
  c4Mul (r .v1) (r .v2) = .c2 ∧
  c4Mul (r .v2) (r .v0) = .c2

theorem unanchored_triangle_has_two_realizations :
    ValidTriangleRealization (fun _ => C4.c1) ∧
    ValidTriangleRealization (fun _ => C4.c3) :=
  ⟨⟨rfl, rfl, rfl⟩, ⟨rfl, rfl, rfl⟩⟩

theorem c2InC4_acts_on_realizations (r : Tri → C4) (h : C4)
    (hr : ValidTriangleRealization r) (hh : c2InC4.mem h) :
    ValidTriangleRealization (fun v => c4Mul (r v) h) := by
  rcases hr with ⟨e01, e12, e20⟩
  rcases hh with rfl | rfl
  · have hm : ∀ x : C4, c4Mul x .c0 = x := fun x => c4Group.mul_one x
    exact ⟨by simp only [hm]; exact e01,
           by simp only [hm]; exact e12,
           by simp only [hm]; exact e20⟩
  · have step : ∀ x y : C4, c4Mul x y = .c2 → c4Mul (c4Mul x .c2) (c4Mul y .c2) = .c2 := by
      intro x y hxy
      cases x <;> cases y <;> simp [c4Mul] at hxy ⊢ <;> cases hxy
    exact ⟨step _ _ e01, step _ _ e12, step _ _ e20⟩

/-- Local edge sections in coset `0 mod 2` (`c2InC4`): each context edge gets
    `left = c0, right = c2`, solving `c0 + c2 = c2` locally on every edge. -/
def speckerCoset0Local (c : Tri) : LocalSection (G := C4) speckerVarCover c :=
  fun x _hx => if x == c then C4.c0 else C4.c2

theorem speckerCoset0Local_valid_edges :
    c4Mul (speckerCoset0Local .v0 .v0 trivial) (speckerCoset0Local .v0 .v1 trivial) = .c2 ∧
    c4Mul (speckerCoset0Local .v1 .v1 trivial) (speckerCoset0Local .v1 .v2 trivial) = .c2 ∧
    c4Mul (speckerCoset0Local .v2 .v2 trivial) (speckerCoset0Local .v2 .v0 trivial) = .c2 := by
  exact ⟨rfl, rfl, rfl⟩

/-- Non-vacuous proof that `speckerCoset0Local` fails `IsTransitionCoboundary`
    (its transitions around `v0 -> v1 -> v2 -> v0` sum to `c2 != c0`) and hence fails `GluesByGauge`. -/
theorem speckerCoset0Local_not_transition_coboundary :
    ¬ IsTransitionCoboundary c4Group c2InC4 speckerVarCover speckerCoset0Local := by
  rintro ⟨u, hu, hcob⟩
  have h01 := hcob .v0 .v1 .v1 trivial trivial
  have h12 := hcob .v1 .v2 .v2 trivial trivial
  have h20 := hcob .v2 .v0 .v0 trivial trivial
  rcases hu .v0 with p0 | p0 <;> rcases hu .v1 with p1 | p1 <;> rcases hu .v2 with p2 | p2
  all_goals
    simp [contextTransition, speckerCoset0Local, c4Group, c4Mul, c4Inv, p0, p1, p2] at h01 h12 h20

theorem speckerCoset0Local_not_gluesByGauge :
    ¬ GluesByGauge c4Group c2InC4 speckerVarCover speckerCoset0Local := by
  intro hg
  exact speckerCoset0Local_not_transition_coboundary
    ((gluesByGauge_iff_transition_coboundary
        c4Group c2InC4 speckerVarCover speckerCoset0Local).mp hg)

/-- No choice of coset-`0` assignments (`r v ∈ {c0, c2}`) realizes all 3 triangle constraints globally. -/
theorem c4_triangle_coset0_anchor_no_global_realization :
    ¬ ∃ r : Tri → C4, ValidTriangleRealization r ∧ ∀ v, c2InC4.mem (r v) := by
  rintro ⟨r, ⟨e01, e12, e20⟩, hc⟩
  rcases hc .v0 with h0 | h0 <;> rcases hc .v1 with h1 | h1 <;> rcases hc .v2 with h2 | h2
  all_goals
    simp [h0, h1, h2, c4Mul] at e01 e12 e20

/-- Explicit `C2`-valued 1-cocycle on the 3-context triangle nerve (`U_0 ∩ U_1 ∩ U_2 = ∅`):
    monodromy around `(v0 -> v1 -> v2 -> v0)` is `c2 != c0`, refuting coboundary triviality. -/
def speckerC2Val : Tri → Tri → C4
  | .v0, .v1 => .c2
  | .v1, .v0 => .c2
  | .v1, .v2 => .c2
  | .v2, .v1 => .c2
  | .v2, .v0 => .c2
  | .v0, .v2 => .c2
  | _, _ => .c0

def speckerC2Cocycle : Cocycle1 c4Group c2InC4 triangleCover where
  val := speckerC2Val
  in_H := by
    intro i j _hij
    cases i <;> cases j <;> simp [speckerC2Val, c2InC4]
  cocycle := by
    intro i j k hijk
    rcases hijk with rfl | rfl | rfl
    · cases i <;> cases k <;> rfl
    · cases i <;> cases j <;> rfl
    · cases i <;> cases j <;> rfl

theorem speckerC2Cocycle_nontrivial :
    ¬ IsCoboundary c4Group c2InC4 triangleCover speckerC2Cocycle := by
  rintro ⟨u, hu, hcob⟩
  have h01 := hcob (show triangleCover.overlap .v0 .v1 from rfl)
  have h12 := hcob (show triangleCover.overlap .v1 .v2 from rfl)
  have h20 := hcob (show triangleCover.overlap .v2 .v0 from rfl)
  rcases hu .v0 with p0 | p0 <;> rcases hu .v1 with p1 | p1 <;> rcases hu .v2 with p2 | p2
  all_goals
    simp [speckerC2Cocycle, speckerC2Val, c4Group, c4Mul, c4Inv, p0, p1, p2] at h01 h12 h20

/-- Contrasting coset `1 mod 2` local constant section `c1` DOES glue via `H = {c0, c2}`! -/
def speckerCoset1Local (c : Tri) : LocalSection (G := C4) speckerVarCover c :=
  fun _ _ => .c1

theorem speckerCoset1Local_gluesByGauge :
    GluesByGauge c4Group c2InC4 speckerVarCover speckerCoset1Local :=
  ⟨fun _ => .c1, fun _ => .c0, fun _ => Or.inl rfl, fun _ _ _ => rfl⟩

/-! ## Section 3: Monolith / Partial-Anchor Impossibility Theorem (`Q8` vs `C2^3`) -/

def PartialSubgroup {G : Type u} (Γ : FinGroup G) (H : Subgroup Γ) : Prop :=
  ∃ x : G, x ≠ Γ.one ∧ H.mem x

def PartialAnchorAdequate {G : Type u} (Γ : FinGroup G) : Prop :=
  ∃ Hs : List (Subgroup Γ),
    (∀ H ∈ Hs, PartialSubgroup Γ H) ∧
    ∀ g : G, (∀ H ∈ Hs, H.mem g) → g = Γ.one

def HasMonolith {G : Type u} (Γ : FinGroup G) : Prop :=
  ∃ z : G, z ≠ Γ.one ∧ ∀ H : Subgroup Γ, PartialSubgroup Γ H → H.mem z

/-- **General Monolith Partial-Anchor Impossibility Theorem:**
    If `G` has a monolith `z ≠ 1`, then NO finite collection of nontrivial
    partial anchor subgroups can intersect to `{1}`. -/
theorem hasMonolith_not_partialAnchorAdequate {G : Type u} (Γ : FinGroup G)
    (hmono : HasMonolith Γ) : ¬ PartialAnchorAdequate Γ := by
  rintro ⟨Hs, hpart, hinter⟩
  rcases hmono with ⟨z, hzOne, hzAll⟩
  have hzIn : ∀ H ∈ Hs, H.mem z := fun H hH => hzAll H (hpart H hH)
  exact hzOne (hinter z hzIn)

theorem c4_hasMonolith : HasMonolith c4Group := by
  refine ⟨.c2, by decide, fun H ⟨x, hxOne, hxMem⟩ => ?_⟩
  cases x
  · exact absurd rfl hxOne
  · exact H.mul_mem hxMem hxMem
  · exact hxMem
  · exact H.mul_mem hxMem hxMem

theorem c4_not_partialAnchorAdequate : ¬ PartialAnchorAdequate c4Group :=
  hasMonolith_not_partialAnchorAdequate c4Group c4_hasMonolith

/-- Explicit 8-element non-abelian Quaternion group `Q8`. -/
inductive Q8 where
  | one | negOne | i | negI | j | negJ | k | negK
  deriving DecidableEq, Repr

def q8Mul : Q8 → Q8 → Q8
  | .one, x => x
  | x, .one => x
  | .negOne, .negOne => .one
  | .negOne, .i => .negI
  | .negOne, .negI => .i
  | .negOne, .j => .negJ
  | .negOne, .negJ => .j
  | .negOne, .k => .negK
  | .negOne, .negK => .k
  | .i, .negOne => .negI
  | .negI, .negOne => .i
  | .j, .negOne => .negJ
  | .negJ, .negOne => .j
  | .k, .negOne => .negK
  | .negK, .negOne => .k
  | .i, .i => .negOne
  | .i, .negI => .one
  | .i, .j => .k
  | .i, .negJ => .negK
  | .i, .k => .negJ
  | .i, .negK => .j
  | .negI, .i => .one
  | .negI, .negI => .negOne
  | .negI, .j => .negK
  | .negI, .negJ => .k
  | .negI, .k => .j
  | .negI, .negK => .negJ
  | .j, .i => .negK
  | .j, .negI => .k
  | .j, .j => .negOne
  | .j, .negJ => .one
  | .j, .k => .i
  | .j, .negK => .negI
  | .negJ, .i => .k
  | .negJ, .negI => .negK
  | .negJ, .j => .one
  | .negJ, .negJ => .negOne
  | .negJ, .k => .negI
  | .negJ, .negK => .i
  | .k, .i => .j
  | .k, .negI => .negJ
  | .k, .j => .negI
  | .k, .negJ => .i
  | .k, .k => .negOne
  | .k, .negK => .one
  | .negK, .i => .negJ
  | .negK, .negI => .j
  | .negK, .j => .i
  | .negK, .negJ => .negI
  | .negK, .k => .one
  | .negK, .negK => .negOne

def q8Inv : Q8 → Q8
  | .one => .one
  | .negOne => .negOne
  | .i => .negI
  | .negI => .i
  | .j => .negJ
  | .negJ => .j
  | .k => .negK
  | .negK => .k

def q8Group : FinGroup Q8 where
  one := .one
  mul := q8Mul
  inv := q8Inv
  mul_assoc := by
    intro a b c
    cases a <;> cases b <;> cases c <;> rfl
  one_mul := by intro a; cases a <;> rfl
  mul_one := by intro a; cases a <;> rfl
  mul_left_inv := by intro a; cases a <;> rfl
  mul_right_inv := by intro a; cases a <;> rfl

theorem q8_nonabelian : q8Group.mul .i .j ≠ q8Group.mul .j .i := by
  decide

theorem q8_hasMonolith : HasMonolith q8Group := by
  refine ⟨.negOne, by decide, fun H ⟨x, hxOne, hxMem⟩ => ?_⟩
  cases x
  · exact absurd rfl hxOne
  · exact hxMem
  · exact H.mul_mem hxMem hxMem
  · exact H.mul_mem hxMem hxMem
  · exact H.mul_mem hxMem hxMem
  · exact H.mul_mem hxMem hxMem
  · exact H.mul_mem hxMem hxMem
  · exact H.mul_mem hxMem hxMem

theorem q8_not_partialAnchorAdequate : ¬ PartialAnchorAdequate q8Group :=
  hasMonolith_not_partialAnchorAdequate q8Group q8_hasMonolith

/-- Contrasting elementary abelian group `C2^3` of the exact same order `8`. -/
abbrev C2Cubed := Bool × Bool × Bool

def c2CubedGroup : FinGroup C2Cubed where
  one := (false, false, false)
  mul := fun a b => (xor a.1 b.1, xor a.2.1 b.2.1, xor a.2.2 b.2.2)
  inv := fun a => a
  mul_assoc := by
    intro a b c
    rcases a with ⟨a1, a2, a3⟩
    rcases b with ⟨b1, b2, b3⟩
    rcases c with ⟨c1, c2, c3⟩
    cases a1 <;> cases a2 <;> cases a3 <;>
    cases b1 <;> cases b2 <;> cases b3 <;>
    cases c1 <;> cases c2 <;> cases c3 <;> rfl
  one_mul := by
    intro a
    rcases a with ⟨a1, a2, a3⟩
    cases a1 <;> cases a2 <;> cases a3 <;> rfl
  mul_one := by
    intro a
    rcases a with ⟨a1, a2, a3⟩
    cases a1 <;> cases a2 <;> cases a3 <;> rfl
  mul_left_inv := by
    intro a
    rcases a with ⟨a1, a2, a3⟩
    cases a1 <;> cases a2 <;> cases a3 <;> rfl
  mul_right_inv := by
    intro a
    rcases a with ⟨a1, a2, a3⟩
    cases a1 <;> cases a2 <;> cases a3 <;> rfl

def c2Ker1 : Subgroup c2CubedGroup where
  mem := fun a => a.1 = false
  one_mem := rfl
  mul_mem := by
    intro a b ha hb
    rcases a with ⟨a1, a2, a3⟩
    rcases b with ⟨b1, b2, b3⟩
    dsimp at ha hb ⊢
    rw [ha, hb]; rfl
  inv_mem := fun ha => ha

def c2Ker2 : Subgroup c2CubedGroup where
  mem := fun a => a.2.1 = false
  one_mem := rfl
  mul_mem := by
    intro a b ha hb
    rcases a with ⟨a1, a2, a3⟩
    rcases b with ⟨b1, b2, b3⟩
    dsimp at ha hb ⊢
    rw [ha, hb]; rfl
  inv_mem := fun ha => ha

def c2Ker3 : Subgroup c2CubedGroup where
  mem := fun a => a.2.2 = false
  one_mem := rfl
  mul_mem := by
    intro a b ha hb
    rcases a with ⟨a1, a2, a3⟩
    rcases b with ⟨b1, b2, b3⟩
    dsimp at ha hb ⊢
    rw [ha, hb]; rfl
  inv_mem := fun ha => ha

theorem c2cubed_partialAnchorAdequate : PartialAnchorAdequate c2CubedGroup := by
  refine ⟨[c2Ker1, c2Ker2, c2Ker3], ?_, ?_⟩
  · intro H hH
    rcases List.mem_cons.mp hH with rfl | hrest
    · exact ⟨(false, true, false), by decide, rfl⟩
    · rcases List.mem_cons.mp hrest with rfl | hrest2
      · exact ⟨(true, false, false), by decide, rfl⟩
      · rcases List.mem_cons.mp hrest2 with rfl | hnil
        · exact ⟨(true, false, false), by decide, rfl⟩
        · cases hnil
  · intro g hg
    rcases g with ⟨g1, g2, g3⟩
    have h1 : g1 = false := hg c2Ker1 (by simp)
    have h2 : g2 = false := hg c2Ker2 (by simp)
    have h3 : g3 = false := hg c2Ker3 (by simp)
    simp [c2CubedGroup, h1, h2, h3]

end Cerp.ObstructionExactSequence
