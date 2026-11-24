import InterventionGrounding
import OperationalReference

/-!
# Stochastic intervention-relative grounding

Extends `Cerp.InterventionGrounding` from deterministic evolution `World -> Action -> World`
to discrete probabilistic transition and observation kernels via finite integer-weighted
distributions (`FinDist`). Probability equality (`distEq`) is encoded via cross-multiplication
so the entire kernel formulation, channel data-processing inequality, deterministic embedding,
and noisy hidden-bit POMDP witnesses compile in pure Lean 4 without external packages.
-/

namespace Cerp.StochasticInterventionGrounding

open Cerp.OperationalSemioticScaffold
open Cerp.InterventionGrounding

universe u v w y

/-- Finite discrete unnormalized distribution with natural-number weights. -/
abbrev FinDist (α : Type u) := List (α × Nat)

def totalWeight {α : Type u} : FinDist α → Nat
  | [] => 0
  | (_, w) :: rest => w + totalWeight rest

def weightOf {α : Type u} [DecidableEq α] (a : α) : FinDist α → Nat
  | [] => 0
  | (b, w) :: rest => (if b = a then w else 0) + weightOf a rest

def dirac {α : Type u} (a : α) : FinDist α := [(a, 1)]

def mapDist {α : Type u} {β : Type v} (f : α → β) : FinDist α → FinDist β
  | [] => []
  | (a, w) :: rest => (f a, w) :: mapDist f rest

def bindDist {α : Type u} {β : Type v} (d : FinDist α) (k : α → FinDist β) : FinDist β :=
  match d with
  | [] => []
  | (a, w) :: rest => (k a).map (fun p => (p.1, w * p.2)) ++ bindDist rest k

/-- Exact rational equality of normalized finite distributions:
    `P_d1(a) = P_d2(a)` encoded as `weightOf a d1 * totalWeight d2 = weightOf a d2 * totalWeight d1`. -/
def distEq {α : Type u} [DecidableEq α] (d1 d2 : FinDist α) : Prop :=
  ∀ a, weightOf a d1 * totalWeight d2 = weightOf a d2 * totalWeight d1

theorem totalWeight_dirac {α : Type u} (a : α) : totalWeight (dirac a) = 1 := rfl

theorem totalWeight_append {α : Type u} (d1 d2 : FinDist α) :
    totalWeight (d1 ++ d2) = totalWeight d1 + totalWeight d2 := by
  induction d1 with
  | nil => simp [totalWeight]
  | cons p rest ih =>
      rcases p with ⟨_a, w⟩
      change w + totalWeight (rest ++ d2) = (w + totalWeight rest) + totalWeight d2
      rw [ih, Nat.add_assoc]

theorem totalWeight_scale {α : Type u} (d : FinDist α) (w : Nat) :
    totalWeight (d.map (fun p => (p.1, w * p.2))) = w * totalWeight d := by
  induction d with
  | nil => simp [totalWeight]
  | cons p rest ih =>
      rcases p with ⟨_a, w'⟩
      simp only [List.map_cons, totalWeight, ih, Nat.mul_add]

theorem totalWeight_mapDist {α : Type u} {β : Type v} (f : α → β) (d : FinDist α) :
    totalWeight (mapDist f d) = totalWeight d := by
  induction d with
  | nil => rfl
  | cons p rest ih =>
      rcases p with ⟨_a, w⟩
      simp [mapDist, totalWeight, ih]

theorem totalWeight_bindDist_pos {α : Type u} {β : Type v}
    (d : FinDist α) (k : α → FinDist β)
    (hd : 0 < totalWeight d)
    (hk : ∀ a, 0 < totalWeight (k a)) :
    0 < totalWeight (bindDist d k) := by
  induction d with
  | nil => simp [totalWeight] at hd
  | cons p rest ih =>
      rcases p with ⟨a, w⟩
      simp only [bindDist, totalWeight_append, totalWeight_scale]
      simp only [totalWeight] at hd
      by_cases hw : 0 < w
      · have hkpos := hk a
        have hmul : 0 < w * totalWeight (k a) := Nat.mul_pos hw hkpos
        omega
      · have hrest : 0 < totalWeight rest := by omega
        have hrec := ih hrest
        omega

private def dedupList {α : Type u} [DecidableEq α] : List α → List α
  | [] => []
  | x :: xs => if x ∈ xs then dedupList xs else x :: dedupList xs

private theorem mem_dedupList {α : Type u} [DecidableEq α] (x : α) (xs : List α) :
    x ∈ dedupList xs ↔ x ∈ xs := by
  induction xs with
  | nil => simp [dedupList]
  | cons y ys ih =>
      dsimp [dedupList]
      by_cases hy : y ∈ ys
      · simp only [hy, ↓reduceIte, List.mem_cons]
        constructor
        · intro hx; exact Or.inr (ih.mp hx)
        · intro hx
          rcases hx with rfl | hmem
          · exact ih.mpr hy
          · exact ih.mpr hmem
      · simp only [hy, ↓reduceIte, List.mem_cons]
        rw [ih]

private theorem nodup_dedupList {α : Type u} [DecidableEq α] (xs : List α) :
    (dedupList xs).Nodup := by
  induction xs with
  | nil => simp [dedupList]
  | cons y ys ih =>
      dsimp [dedupList]
      by_cases hy : y ∈ ys
      · simp [hy, ih]
      · simp only [hy, ↓reduceIte, List.nodup_cons]
        exact ⟨fun hmem => hy ((mem_dedupList y ys).mp hmem), ih⟩

private def sumOn {α : Type u} : List α → (α → Nat) → Nat
  | [], _ => 0
  | k :: ks, g => g k + sumOn ks g

private theorem sumOn_zero {α : Type u} (ks : List α) :
    sumOn ks (fun _ => 0) = 0 := by
  induction ks with
  | nil => rfl
  | cons _ rest ih => simp [sumOn, ih]

private theorem sumOn_add {α : Type u} (ks : List α) (g h : α → Nat) :
    sumOn ks (fun a => g a + h a) = sumOn ks g + sumOn ks h := by
  induction ks with
  | nil => rfl
  | cons k rest ih =>
      simp only [sumOn, ih]
      omega

private theorem sumOn_mul_right {α : Type u} (ks : List α) (g : α → Nat) (c : Nat) :
    sumOn ks g * c = sumOn ks (fun a => g a * c) := by
  induction ks with
  | nil => simp [sumOn]
  | cons k rest ih =>
      simp only [sumOn, Nat.add_mul, ih]

private theorem sumOn_eq_of_mem {α : Type u} (ks : List α) {g h : α → Nat}
    (heq : ∀ a ∈ ks, g a = h a) :
    sumOn ks g = sumOn ks h := by
  induction ks with
  | nil => rfl
  | cons k rest ih =>
      simp only [sumOn, heq k (List.mem_cons_self _ _),
        ih (fun a ha => heq a (List.mem_cons_of_mem _ ha))]

private theorem sumOn_indicator_of_mem {α : Type u} [DecidableEq α]
    (ks : List α) (hnodup : ks.Nodup) {x : α} (hx : x ∈ ks) (c : Nat) :
    sumOn ks (fun a => if x = a then c else 0) = c := by
  induction ks with
  | nil => cases hx
  | cons k rest ih =>
      rw [List.nodup_cons] at hnodup
      rcases List.mem_cons.mp hx with rfl | hrest
      · have hzero : sumOn rest (fun a => if x = a then c else 0) = 0 := by
          calc
            sumOn rest (fun a => if x = a then c else 0) =
                sumOn rest (fun _ => 0) := by
              apply sumOn_eq_of_mem
              intro a ha
              have hne : x ≠ a := fun heq => hnodup.1 (heq ▸ ha)
              simp [hne]
            _ = 0 := sumOn_zero rest
        simp [sumOn, hzero]
      · have hne : x ≠ k := fun heq => hnodup.1 (heq ▸ hrest)
        simp [sumOn, hne, ih hnodup.2 hrest]

private theorem weightOf_mapDist_eq_sumOn {α : Type u} {β : Type v}
    [DecidableEq α] [DecidableEq β]
    (f : α → β) (b : β) (ks : List α) (hnodup : ks.Nodup)
    (d : FinDist α) (hcov : ∀ p ∈ d, p.1 ∈ ks) :
    weightOf b (mapDist f d) =
      sumOn ks (fun a => if f a = b then weightOf a d else 0) := by
  induction d with
  | nil =>
      simp only [mapDist, weightOf]
      have hzero : sumOn ks (fun a => if f a = b then 0 else 0) = 0 := by
        calc
          sumOn ks (fun a => if f a = b then 0 else 0) = sumOn ks (fun _ => 0) := by
            apply sumOn_eq_of_mem
            intro a _
            split <;> rfl
          _ = 0 := sumOn_zero ks
      exact hzero.symm
  | cons p rest ih =>
      rcases p with ⟨x, w⟩
      have hx : x ∈ ks := hcov (x, w) (List.mem_cons_self _ _)
      have hrest : ∀ q ∈ rest, q.1 ∈ ks := fun q hq => hcov q (List.mem_cons_of_mem _ hq)
      have ih' := ih hrest
      simp only [mapDist, weightOf]
      have hsplit : sumOn ks (fun a => if f a = b then (if x = a then w else 0) + weightOf a rest else 0) =
          sumOn ks (fun a => if x = a then (if f x = b then w else 0) else 0) +
          sumOn ks (fun a => if f a = b then weightOf a rest else 0) := by
        rw [← sumOn_add]
        apply sumOn_eq_of_mem
        intro a _
        by_cases hxa : x = a
        · subst hxa
          by_cases hfb : f x = b <;> simp [hfb]
        · by_cases hfb : f a = b <;> simp [hxa, hfb]
      rw [hsplit, sumOn_indicator_of_mem ks hnodup hx, ← ih']

/-- Deterministic observation channels preserve rational equivalence of distributions
    (channel data-processing invariance). -/
theorem channel_map_preserves_distEq {α : Type u} {β : Type v}
    [DecidableEq α] [DecidableEq β]
    (f : α → β) {d1 d2 : FinDist α} (heq : distEq d1 d2) :
    distEq (mapDist f d1) (mapDist f d2) := by
  intro b
  let raw := d1.map Prod.fst ++ d2.map Prod.fst
  let ks := dedupList raw
  have hnodup : ks.Nodup := nodup_dedupList raw
  have hcov1 : ∀ p ∈ d1, p.1 ∈ ks := by
    intro p hp
    exact (mem_dedupList p.1 raw).mpr (List.mem_append_left _ (List.mem_map_of_mem Prod.fst hp))
  have hcov2 : ∀ p ∈ d2, p.1 ∈ ks := by
    intro p hp
    exact (mem_dedupList p.1 raw).mpr (List.mem_append_right _ (List.mem_map_of_mem Prod.fst hp))
  rw [weightOf_mapDist_eq_sumOn f b ks hnodup d1 hcov1,
      weightOf_mapDist_eq_sumOn f b ks hnodup d2 hcov2,
      totalWeight_mapDist, totalWeight_mapDist,
      sumOn_mul_right, sumOn_mul_right]
  apply sumOn_eq_of_mem
  intro a _
  by_cases hfab : f a = b
  · simp [hfab, heq a]
  · simp [hfab]

/-- A non-homuncular stochastic operational scaffold with discrete kernel semantics. -/
structure StochasticScaffold where
  World : Type u
  Sign : Type w
  Action : Type y
  senseDist : World → FinDist Sign
  evolveDist : World → Action → FinDist World
  sense_pos : ∀ world, 0 < totalWeight (senseDist world)
  evolve_pos : ∀ world action, 0 < totalWeight (evolveDist world action)

structure StochasticProtocol (S : StochasticScaffold.{u,w,y}) where
  actionCost : S.Action → Nat

def stochasticExperimentCost {S : StochasticScaffold.{u,w,y}}
    (P : StochasticProtocol S) : List S.Action → Nat
  | [] => 0
  | a :: rest => P.actionCost a + stochasticExperimentCost P rest

/-- Multi-step stochastic observation-trace kernel induced by an intervention sequence. -/
def stochasticExperimentTrace (S : StochasticScaffold.{u,w,y}) :
    List S.Action → S.World → FinDist (List S.Sign)
  | [], world => mapDist (fun s => [s]) (S.senseDist world)
  | action :: rest, world =>
      bindDist (S.senseDist world) fun s =>
        bindDist (S.evolveDist world action) fun nextWorld =>
          mapDist (fun tr => s :: tr) (stochasticExperimentTrace S rest nextWorld)

theorem stochasticExperimentTrace_pos (S : StochasticScaffold.{u,w,y}) :
    ∀ (actions : List S.Action) (world : S.World),
      0 < totalWeight (stochasticExperimentTrace S actions world) := by
  intro actions
  induction actions with
  | nil =>
      intro world
      simp [stochasticExperimentTrace, totalWeight_mapDist, S.sense_pos world]
  | cons action rest ih =>
      intro world
      refine totalWeight_bindDist_pos (S.senseDist world) _ (S.sense_pos world) ?_
      intro s
      refine totalWeight_bindDist_pos (S.evolveDist world action) _ (S.evolve_pos world action) ?_
      intro nextWorld
      simp only [totalWeight_mapDist]
      exact ih nextWorld

/-- Two worlds are stochastically indistinguishable at budget B iff every affordable
    intervention sequence induces rationally identical trace distributions. -/
def stochasticExperimentEquivalent {S : StochasticScaffold.{u,w,y}} [DecidableEq S.Sign]
    (P : StochasticProtocol S) (budget : Nat) (w1 w2 : S.World) : Prop :=
  ∀ actions, stochasticExperimentCost P actions ≤ budget →
    distEq (stochasticExperimentTrace S actions w1) (stochasticExperimentTrace S actions w2)

theorem stochasticExperimentEquivalent_refl {S : StochasticScaffold.{u,w,y}} [DecidableEq S.Sign]
    (P : StochasticProtocol S) (budget : Nat) (w : S.World) :
    stochasticExperimentEquivalent P budget w w := by
  intro actions _ a
  rfl

theorem stochasticExperimentEquivalent_symm {S : StochasticScaffold.{u,w,y}} [DecidableEq S.Sign]
    (P : StochasticProtocol S) (budget : Nat) {w1 w2 : S.World}
    (h : stochasticExperimentEquivalent P budget w1 w2) :
    stochasticExperimentEquivalent P budget w2 w1 := by
  intro actions hcost a
  exact (h actions hcost a).symm

theorem stochasticExperimentEquivalent_trans {S : StochasticScaffold.{u,w,y}} [DecidableEq S.Sign]
    (P : StochasticProtocol S) (budget : Nat) {w1 w2 w3 : S.World}
    (h12 : stochasticExperimentEquivalent P budget w1 w2)
    (h23 : stochasticExperimentEquivalent P budget w2 w3) :
    stochasticExperimentEquivalent P budget w1 w3 := by
  intro actions hcost a
  have d1 := h12 actions hcost a
  have d2 := h23 actions hcost a
  have hpos := stochasticExperimentTrace_pos S actions w2
  have hbig :
      weightOf a (stochasticExperimentTrace S actions w1) *
        totalWeight (stochasticExperimentTrace S actions w3) *
        totalWeight (stochasticExperimentTrace S actions w2) =
      weightOf a (stochasticExperimentTrace S actions w3) *
        totalWeight (stochasticExperimentTrace S actions w1) *
        totalWeight (stochasticExperimentTrace S actions w2) := by
    calc
      weightOf a (stochasticExperimentTrace S actions w1) *
          totalWeight (stochasticExperimentTrace S actions w3) *
          totalWeight (stochasticExperimentTrace S actions w2)
        = (weightOf a (stochasticExperimentTrace S actions w1) *
            totalWeight (stochasticExperimentTrace S actions w2)) *
            totalWeight (stochasticExperimentTrace S actions w3) := by ac_rfl
      _ = (weightOf a (stochasticExperimentTrace S actions w2) *
            totalWeight (stochasticExperimentTrace S actions w1)) *
            totalWeight (stochasticExperimentTrace S actions w3) := by rw [d1]
      _ = (weightOf a (stochasticExperimentTrace S actions w2) *
            totalWeight (stochasticExperimentTrace S actions w3)) *
            totalWeight (stochasticExperimentTrace S actions w1) := by ac_rfl
      _ = (weightOf a (stochasticExperimentTrace S actions w3) *
            totalWeight (stochasticExperimentTrace S actions w2)) *
            totalWeight (stochasticExperimentTrace S actions w1) := by rw [d2]
      _ = weightOf a (stochasticExperimentTrace S actions w3) *
            totalWeight (stochasticExperimentTrace S actions w1) *
            totalWeight (stochasticExperimentTrace S actions w2) := by ac_rfl
  exact Nat.eq_of_mul_eq_mul_right hpos hbig

theorem stochasticExperimentEquivalent_antitone {S : StochasticScaffold.{u,w,y}} [DecidableEq S.Sign]
    (P : StochasticProtocol S) {b1 b2 : Nat} (hle : b1 ≤ b2) {w1 w2 : S.World}
    (h : stochasticExperimentEquivalent P b2 w1 w2) :
    stochasticExperimentEquivalent P b1 w1 w2 := by
  intro actions hcost
  exact h actions (Nat.le_trans hcost hle)

/-- Channel coarsening on traces (e.g., applying a deterministic sensor readout)
    preserves stochastic operational equivalence. -/
theorem channel_coarsening_preserves_stochasticEquivalent
    {S : StochasticScaffold.{u,w,y}} {Sign' : Type w}
    [DecidableEq S.Sign] [DecidableEq Sign']
    (P : StochasticProtocol S) (budget : Nat) (f : S.Sign → Sign')
    {w1 w2 : S.World}
    (h : stochasticExperimentEquivalent P budget w1 w2) :
    ∀ actions, stochasticExperimentCost P actions ≤ budget →
      distEq (mapDist (List.map f) (stochasticExperimentTrace S actions w1))
             (mapDist (List.map f) (stochasticExperimentTrace S actions w2)) := by
  intro actions hcost
  exact channel_map_preserves_distEq (List.map f) (h actions hcost)

/-- Embedding any deterministic `OperationalScaffold` as Dirac kernels. -/
def ofDeterministic (S : OperationalScaffold.{u,v,w,x,y}) : StochasticScaffold.{u,w,y} where
  World := S.World
  Sign := S.Sign
  Action := S.Action
  senseDist := fun world => dirac (S.sense world)
  evolveDist := fun world action => dirac (S.evolve world action)
  sense_pos := fun _ => by simp [dirac, totalWeight]
  evolve_pos := fun _ _ => by simp [dirac, totalWeight]

theorem bindDist_dirac {α : Type u} {β : Type v} (a : α) (k : α → FinDist β) :
    bindDist (dirac a) k = k a := by
  simp only [bindDist, dirac, List.append_nil]
  generalize k a = d
  induction d with
  | nil => rfl
  | cons p rest ih =>
      rcases p with ⟨_b, w⟩
      simp [Nat.one_mul, ih]

theorem ofDeterministic_trace_dirac (S : OperationalScaffold.{u,v,w,x,y}) :
    ∀ (actions : List S.Action) (world : S.World),
      stochasticExperimentTrace (ofDeterministic S) actions world =
        dirac (experimentTrace S actions world) := by
  intro actions
  induction actions with
  | nil =>
      intro world
      rfl
  | cons action rest ih =>
      intro world
      change bindDist (dirac (S.sense world)) (fun s =>
        bindDist (dirac (S.evolve world action)) (fun nextWorld =>
          mapDist (fun tr => s :: tr) (stochasticExperimentTrace (ofDeterministic S) rest nextWorld))) =
        dirac (experimentTrace S (action :: rest) world)
      rw [bindDist_dirac, bindDist_dirac, ih (S.evolve world action)]
      rfl

/-- Concrete noisy hidden-bit POMDP: visible bit is read cleanly, while the reveal
    intervention exposes the hidden bit with 3:1 (75% vs 25%) channel noise. -/
@[reducible] def noisyHiddenScaffold : StochasticScaffold.{0,0,0} where
  World := Bool × Bool
  Sign := Bool
  Action := Unit
  senseDist := fun world => dirac world.2
  evolveDist := fun world _ => [((world.1, world.1), 3), ((world.1, !world.1), 1)]
  sense_pos := fun _ => by simp [dirac, totalWeight]
  evolve_pos := fun _ _ => by simp [totalWeight]

def noisyRevealProtocol : StochasticProtocol noisyHiddenScaffold where
  actionCost := fun _ => 1

/-- Under passive sampling (budget 0), worlds with different hidden bits remain
    stochastically indistinguishable. -/
theorem noisy_hidden_indistinguishable_at_zero :
    stochasticExperimentEquivalent noisyRevealProtocol 0 (false, false) (true, false) := by
  intro actions hcost
  cases actions with
  | nil =>
      intro _a
      rfl
  | cons _a _rest =>
      simp [stochasticExperimentCost, noisyRevealProtocol, Nat.succ_add] at hcost

/-- Despite 25% channel noise on the reveal step, budget-1 active intervention
    strictly separates the two hidden-bit worlds (3/4 vs 1/4 mass on `[false, false]`). -/
theorem noisy_reveal_separates_at_one :
    ¬ stochasticExperimentEquivalent noisyRevealProtocol 1 (false, false) (true, false) := by
  intro h
  have h1 := h [()] (by decide) [false, false]
  simp [stochasticExperimentTrace, noisyHiddenScaffold, dirac, bindDist, mapDist,
        weightOf, totalWeight] at h1

/-- Noisy reveal protocol identifies all 4 world states at budget 1. -/
def StochasticSeparatingAt {S : StochasticScaffold.{u,w,y}} [DecidableEq S.Sign]
    (P : StochasticProtocol S) (budget : Nat) : Prop :=
  ∀ w1 w2, stochasticExperimentEquivalent P budget w1 w2 → w1 = w2

theorem noisy_reveal_separating_at_one :
    StochasticSeparatingAt noisyRevealProtocol 1 := by
  intro w1 w2 h
  rcases w1 with ⟨h1, v1⟩
  rcases w2 with ⟨h2, v2⟩
  have hNow := h [] (by decide) [v1]
  have hv : v1 = v2 := by
    cases v1 <;> cases v2 <;>
      simp_all [stochasticExperimentTrace, noisyHiddenScaffold, dirac, mapDist, weightOf, totalWeight]
  subst hv
  have hRev := h [()] (by decide) [v1, h1]
  have hh : h1 = h2 := by
    cases h1 <;> cases h2 <;> cases v1 <;>
      simp_all [stochasticExperimentTrace, noisyHiddenScaffold, dirac, bindDist, mapDist,
        weightOf, totalWeight]
  subst hh
  rfl

end Cerp.StochasticInterventionGrounding
