import Mathlib.Probability.Kernel.Composition
import Mathlib.MeasureTheory.Constructions.Polish.Basic
import Mathlib.MeasureTheory.Constructions.Prod.Basic

/-!
# Continuum Measurable, Polish, and Standard-Borel Markov-Kernel Causal Covariance

Lifts Semplex's finite causal representation covariance (`StochasticCausalCovariance`)
to uncountable measurable, Polish, and Standard Borel spaces using Mathlib's Giry monad
and `ProbabilityTheory.Kernel`:

1. Defines finite-horizon outcome trajectory spaces `TraceSpace O n` with pushforward maps
   `traceMap h n`, proving measurability, `MeasurableEmbedding` inheritance via
   `MeasurableEmbedding.prod_mk`, and measure-pushforward injectivity.
2. Constructs sequential causal experiment Markov kernels `traceKernel E n actions` and
   initial-state pushforward laws `externalTraceMeasure E e n actions`.
3. Proves kernel functoriality lemmas (`kernel_map_comp_of_comm`, `kernel_map_prod_of_comm`),
   exact trace-kernel covariance (`continuum_traceKernel_transport`), exact pushforward
   trace-measure transport (`continuum_externalTraceMeasure_transport`), monotone-budget
   forward preservation, and exact profile covariance for arbitrary measurable embeddings,
   continuous injective Polish encodings, and measurable injective Standard Borel encodings.
4. Proves continuum event-probability variation equality and exhibits a sharp real-line
   counterexample (`fun x : ℝ => |x|`) separating injective from lossy codings.
-/

open MeasureTheory ProbabilityTheory Function Set
open scoped ENNReal ProbabilityTheory

namespace Semplex.ContinuumKernelCovariance

section TraceSpaces

@[reducible] def TraceSpace (O : Type*) : ℕ → Type _
  | 0 => O
  | n + 1 => O × TraceSpace O n

instance measurableSpaceTraceSpace (O : Type*) [mO : MeasurableSpace O] :
    ∀ n, MeasurableSpace (TraceSpace O n)
  | 0 => mO
  | n + 1 => @Prod.instMeasurableSpace O (TraceSpace O n) mO (measurableSpaceTraceSpace O n)

def traceMap {O O' : Type*} (h : O → O') :
    ∀ n, TraceSpace O n → TraceSpace O' n
  | 0 => h
  | n + 1 => Prod.map h (traceMap h n)

theorem traceMap_measurable {O O' : Type*} [MeasurableSpace O] [MeasurableSpace O']
    {h : O → O'} (hh : Measurable h) :
    ∀ n, Measurable (traceMap h n)
  | 0 => hh
  | n + 1 =>
      (hh.comp measurable_fst).prod_mk ((traceMap_measurable hh n).comp measurable_snd)

theorem traceMap_measurableEmbedding {O O' : Type*} [MeasurableSpace O] [MeasurableSpace O']
    {h : O → O'} (hh : MeasurableEmbedding h) :
    ∀ n, MeasurableEmbedding (traceMap h n)
  | 0 => hh
  | n + 1 => MeasurableEmbedding.prod_mk hh (traceMap_measurableEmbedding hh n)

theorem measure_map_injective_of_measurableEmbedding
    {α β : Type*} [MeasurableSpace α] [MeasurableSpace β]
    {f : α → β} (hf : MeasurableEmbedding f)
    {μ ν : Measure α} (hmap : μ.map f = ν.map f) : μ = ν := by
  ext s hs
  have hfs : MeasurableSet (f '' s) := hf.measurableSet_image.mpr hs
  have heq : μ.map f (f '' s) = ν.map f (f '' s) := Measure.ext_iff.mp hmap (f '' s) hfs
  rw [Measure.map_apply hf.measurable hfs, Measure.map_apply hf.measurable hfs,
    hf.injective.preimage_image s] at heq
  exact heq

theorem traceMap_measure_injective
    {O O' : Type*} [MeasurableSpace O] [MeasurableSpace O']
    {h : O → O'} (hh : MeasurableEmbedding h) (n : ℕ)
    {μ ν : Measure (TraceSpace O n)}
    (hmap : μ.map (traceMap h n) = ν.map (traceMap h n)) :
    μ = ν :=
  measure_map_injective_of_measurableEmbedding (traceMap_measurableEmbedding hh n) hmap

end TraceSpaces

section ContinuumExperiments

structure MeasurableCausalExperiment
    (External State Intervention Outcome : Type*)
    [MeasurableSpace State] [MeasurableSpace Outcome] where
  initial : External → Measure State
  initial_prob : ∀ e, IsProbabilityMeasure (initial e)
  observe : Kernel State Outcome
  observe_markov : IsMarkovKernel observe
  evolve : Intervention → Kernel State State
  evolve_markov : ∀ a, IsMarkovKernel (evolve a)
  interventionCost : Intervention → ℕ

noncomputable def traceKernel
    {External State Intervention Outcome : Type*}
    [MeasurableSpace State] [MeasurableSpace Outcome]
    (E : MeasurableCausalExperiment External State Intervention Outcome) :
    (n : ℕ) → (Fin n → Intervention) → Kernel State (TraceSpace Outcome n)
  | 0, _ => E.observe
  | n + 1, actions =>
      E.observe ×ₖ ((traceKernel E n (fun i => actions i.succ)) ∘ₖ (E.evolve (actions 0)))

instance traceKernel_isMarkov
    {External State Intervention Outcome : Type*}
    [MeasurableSpace State] [MeasurableSpace Outcome]
    (E : MeasurableCausalExperiment External State Intervention Outcome) :
    ∀ (n : ℕ) (actions : Fin n → Intervention), IsMarkovKernel (traceKernel E n actions)
  | 0, _ => E.observe_markov
  | n + 1, actions => by
      haveI := E.observe_markov
      haveI := E.evolve_markov (actions 0)
      haveI := traceKernel_isMarkov E n (fun i => actions i.succ)
      dsimp [traceKernel]
      infer_instance

noncomputable def externalTraceMeasure
    {External State Intervention Outcome : Type*}
    [MeasurableSpace State] [MeasurableSpace Outcome]
    (E : MeasurableCausalExperiment External State Intervention Outcome)
    (e : External) (n : ℕ) (actions : Fin n → Intervention) :
    Measure (TraceSpace Outcome n) :=
  (E.initial e).bind (traceKernel E n actions)

def continuumExperimentCost
    {External State Intervention Outcome : Type*}
    [MeasurableSpace State] [MeasurableSpace Outcome]
    (E : MeasurableCausalExperiment External State Intervention Outcome)
    (n : ℕ) (actions : Fin n → Intervention) : ℕ :=
  ∑ i : Fin n, E.interventionCost (actions i)

theorem continuumExperimentCost_mem_le
    {External State Intervention Outcome : Type*}
    [MeasurableSpace State] [MeasurableSpace Outcome]
    (E : MeasurableCausalExperiment External State Intervention Outcome)
    {n : ℕ} (actions : Fin n → Intervention) (i : Fin n) :
    E.interventionCost (actions i) ≤ continuumExperimentCost E n actions := by
  change E.interventionCost (actions i) ≤ ∑ j : Fin n, E.interventionCost (actions j)
  exact Finset.single_le_sum (f := fun j => E.interventionCost (actions j))
    (fun _ _ => Nat.zero_le _) (Finset.mem_univ i)

def ContinuumObsEqual
    {External State Intervention Outcome : Type*}
    [MeasurableSpace State] [MeasurableSpace Outcome]
    (E : MeasurableCausalExperiment External State Intervention Outcome)
    (budget : ℕ) (e e' : External) : Prop :=
  ∀ (n : ℕ) (actions : Fin n → Intervention),
    continuumExperimentCost E n actions ≤ budget →
    externalTraceMeasure E e n actions = externalTraceMeasure E e' n actions

structure MeasurableRepMap
    {External State Intervention Outcome State' Intervention' Outcome' : Type*}
    [MeasurableSpace State] [MeasurableSpace Outcome]
    [MeasurableSpace State'] [MeasurableSpace Outcome']
    (E : MeasurableCausalExperiment External State Intervention Outcome)
    (E' : MeasurableCausalExperiment External State' Intervention' Outcome')
    (scale : ℕ) where
  stateMap : State → State'
  interventionMap : Intervention → Intervention'
  outcomeMap : Outcome → Outcome'
  stateMap_measurable : Measurable stateMap
  outcomeMap_measurable : Measurable outcomeMap
  initial_commute : ∀ e, E'.initial e = (E.initial e).map stateMap
  observe_commute :
    Kernel.map E.observe outcomeMap =
      Kernel.comap E'.observe stateMap stateMap_measurable
  evolve_commute : ∀ a,
    Kernel.map (E.evolve a) stateMap =
      Kernel.comap (E'.evolve (interventionMap a)) stateMap stateMap_measurable
  cost_le : ∀ a, E'.interventionCost (interventionMap a) ≤ scale * E.interventionCost a

end ContinuumExperiments

section KernelFunctoriality

theorem kernel_map_comp_of_comm
    {α α' β β' γ γ' : Type*}
    [MeasurableSpace α] [MeasurableSpace α']
    [MeasurableSpace β] [MeasurableSpace β']
    [MeasurableSpace γ] [MeasurableSpace γ']
    {κ : Kernel α β} {κ' : Kernel α' β'}
    {η : Kernel β γ} {η' : Kernel β' γ'} [IsSFiniteKernel η']
    {f₁ : α → α'} (hf₁ : Measurable f₁)
    {f₂ : β → β'} (hf₂ : Measurable f₂)
    {g : γ → γ'} (hg : Measurable g)
    (hκ : Kernel.map κ f₂ = Kernel.comap κ' f₁ hf₁)
    (hη : Kernel.map η g = Kernel.comap η' f₂ hf₂) :
    Kernel.map (η ∘ₖ κ) g = Kernel.comap (η' ∘ₖ κ') f₁ hf₁ := by
  refine Kernel.ext_fun fun a φ hφ => ?_
  have hcg : Measurable fun c => φ (g c) := hφ.comp hg
  rw [Kernel.lintegral_map _ hg a hφ, Kernel.lintegral_comp _ _ a hcg,
    Kernel.lintegral_comap _ hf₁ a φ]
  have hη_pt : ∀ b, ∫⁻ c, φ (g c) ∂η b = ∫⁻ c, φ c ∂η' (f₂ b) := by
    intro b
    have hb := congrArg (fun k : Kernel β γ' => ∫⁻ c, φ c ∂k b) hη
    dsimp only at hb
    rw [Kernel.lintegral_map _ hg b hφ, Kernel.lintegral_comap _ hf₂ b φ] at hb
    exact hb
  simp_rw [hη_pt]
  have hinner : Measurable fun b' => ∫⁻ c, φ c ∂η' b' := hφ.lintegral_kernel
  have hκa := congrArg (fun k : Kernel α β' => ∫⁻ b', (∫⁻ c, φ c ∂η' b') ∂k a) hκ
  dsimp only at hκa
  rw [Kernel.lintegral_map _ hf₂ a hinner, Kernel.lintegral_comap _ hf₁ a _] at hκa
  rw [hκa, Kernel.lintegral_comp _ _ (f₁ a) hφ]

theorem kernel_map_prod_of_comm
    {α α' β₁ β₂ γ₁ γ₂ : Type*}
    [MeasurableSpace α] [MeasurableSpace α']
    [MeasurableSpace β₁] [MeasurableSpace β₂]
    [MeasurableSpace γ₁] [MeasurableSpace γ₂]
    {κ : Kernel α β₁} [IsSFiniteKernel κ]
    {η : Kernel α β₂} [IsSFiniteKernel η]
    {κ' : Kernel α' γ₁} [IsSFiniteKernel κ']
    {η' : Kernel α' γ₂} [IsSFiniteKernel η']
    {f : α → α'} (hf : Measurable f)
    {g₁ : β₁ → γ₁} (hg₁ : Measurable g₁)
    {g₂ : β₂ → γ₂} (hg₂ : Measurable g₂)
    (hκ : Kernel.map κ g₁ = Kernel.comap κ' f hf)
    (hη : Kernel.map η g₂ = Kernel.comap η' f hf) :
    Kernel.map (κ ×ₖ η) (Prod.map g₁ g₂) = Kernel.comap (κ' ×ₖ η') f hf := by
  have hmap : Measurable (Prod.map g₁ g₂) :=
    (hg₁.comp measurable_fst).prod_mk (hg₂.comp measurable_snd)
  refine Kernel.ext_fun fun a φ hφ => ?_
  have hcmap : Measurable fun bc : β₁ × β₂ => φ (Prod.map g₁ g₂ bc) := hφ.comp hmap
  rw [Kernel.lintegral_map _ hmap a hφ, Kernel.lintegral_prod _ _ a hcmap,
    Kernel.lintegral_comap _ hf a φ]
  have hη_pt : ∀ b₁,
      ∫⁻ b₂, φ (Prod.map g₁ g₂ (b₁, b₂)) ∂η a = ∫⁻ c₂, φ (g₁ b₁, c₂) ∂η' (f a) := by
    intro b₁
    have hm : Measurable fun c₂ => φ (g₁ b₁, c₂) :=
      hφ.comp (measurable_const.prod_mk measurable_id)
    have hηa := congrArg (fun k : Kernel α γ₂ => ∫⁻ c₂, φ (g₁ b₁, c₂) ∂k a) hη
    dsimp only at hηa
    rw [Kernel.lintegral_map _ hg₂ a hm, Kernel.lintegral_comap _ hf a _] at hηa
    simpa [Prod.map] using hηa
  simp_rw [hη_pt]
  have hinner : Measurable fun c₁ => ∫⁻ c₂, φ (c₁, c₂) ∂η' (f a) := by
    refine Measurable.lintegral_kernel_prod_right (κ := Kernel.const γ₁ (η' (f a))) ?_
    simpa [Function.uncurry] using hφ
  have hκa := congrArg (fun k : Kernel α γ₁ =>
    ∫⁻ c₁, (∫⁻ c₂, φ (c₁, c₂) ∂η' (f a)) ∂k a) hκ
  dsimp only at hκa
  rw [Kernel.lintegral_map _ hg₁ a hinner, Kernel.lintegral_comap _ hf a _] at hκa
  rw [hκa, Kernel.lintegral_prod _ _ (f a) hφ]

end KernelFunctoriality

section CovarianceTheorems

theorem continuum_experimentCost_le_of_monotone
    {External State Intervention Outcome State' Intervention' Outcome' : Type*}
    [MeasurableSpace State] [MeasurableSpace Outcome]
    [MeasurableSpace State'] [MeasurableSpace Outcome']
    {E : MeasurableCausalExperiment External State Intervention Outcome}
    {E' : MeasurableCausalExperiment External State' Intervention' Outcome'}
    {scale : ℕ}
    (R : MeasurableRepMap E E' scale)
    (n : ℕ) (actions : Fin n → Intervention) :
    continuumExperimentCost E' n (R.interventionMap ∘ actions) ≤
      scale * continuumExperimentCost E n actions := by
  calc
    continuumExperimentCost E' n (R.interventionMap ∘ actions)
        = ∑ i : Fin n, E'.interventionCost (R.interventionMap (actions i)) := rfl
    _ ≤ ∑ i : Fin n, scale * E.interventionCost (actions i) :=
        Finset.sum_le_sum fun i _ => R.cost_le (actions i)
    _ = scale * ∑ i : Fin n, E.interventionCost (actions i) := by
        rw [← Finset.mul_sum]

theorem continuum_traceKernel_transport
    {External State Intervention Outcome State' Intervention' Outcome' : Type*}
    [MeasurableSpace State] [MeasurableSpace Outcome]
    [MeasurableSpace State'] [MeasurableSpace Outcome']
    {E : MeasurableCausalExperiment External State Intervention Outcome}
    {E' : MeasurableCausalExperiment External State' Intervention' Outcome'}
    {scale : ℕ}
    (R : MeasurableRepMap E E' scale) :
    ∀ (n : ℕ) (actions : Fin n → Intervention),
      Kernel.map (traceKernel E n actions) (traceMap R.outcomeMap n) =
        Kernel.comap (traceKernel E' n (R.interventionMap ∘ actions))
          R.stateMap R.stateMap_measurable
  | 0, _ => by
      simpa [traceKernel, traceMap] using R.observe_commute
  | n + 1, actions => by
      haveI := E.observe_markov
      haveI := E.evolve_markov (actions 0)
      haveI := traceKernel_isMarkov E n (fun i => actions i.succ)
      haveI := E'.observe_markov
      haveI := E'.evolve_markov (R.interventionMap (actions 0))
      haveI := traceKernel_isMarkov E' n (R.interventionMap ∘ fun i => actions i.succ)
      have ih := continuum_traceKernel_transport R n (fun i => actions i.succ)
      have hcomp :
          Kernel.map ((traceKernel E n (fun i => actions i.succ)) ∘ₖ (E.evolve (actions 0)))
            (traceMap R.outcomeMap n) =
          Kernel.comap
            ((traceKernel E' n (R.interventionMap ∘ fun i => actions i.succ)) ∘ₖ
              (E'.evolve (R.interventionMap (actions 0))))
            R.stateMap R.stateMap_measurable :=
        kernel_map_comp_of_comm R.stateMap_measurable R.stateMap_measurable
          (traceMap_measurable R.outcomeMap_measurable n)
          (R.evolve_commute (actions 0)) ih
      simpa [traceKernel, traceMap, Function.comp] using
        kernel_map_prod_of_comm R.stateMap_measurable R.outcomeMap_measurable
          (traceMap_measurable R.outcomeMap_measurable n)
          R.observe_commute hcomp

theorem continuum_externalTraceMeasure_transport
    {External State Intervention Outcome State' Intervention' Outcome' : Type*}
    [MeasurableSpace State] [MeasurableSpace Outcome]
    [MeasurableSpace State'] [MeasurableSpace Outcome']
    {E : MeasurableCausalExperiment External State Intervention Outcome}
    {E' : MeasurableCausalExperiment External State' Intervention' Outcome'}
    {scale : ℕ}
    (R : MeasurableRepMap E E' scale)
    (e : External) (n : ℕ) (actions : Fin n → Intervention) :
    (externalTraceMeasure E e n actions).map (traceMap R.outcomeMap n) =
      externalTraceMeasure E' e n (R.interventionMap ∘ actions) := by
  have hmap : Measurable (traceMap R.outcomeMap n) :=
    traceMap_measurable R.outcomeMap_measurable n
  ext S hS
  rw [Measure.map_apply hmap hS, externalTraceMeasure,
    Measure.bind_apply (hmap hS) (Kernel.measurable _)]
  have htr := continuum_traceKernel_transport R n actions
  have hpt : ∀ s,
      traceKernel E n actions s (traceMap R.outcomeMap n ⁻¹' S) =
        traceKernel E' n (R.interventionMap ∘ actions) (R.stateMap s) S := by
    intro s
    have hs := congrArg (fun k : Kernel State (TraceSpace Outcome' n) => k s S) htr
    dsimp only at hs
    rw [Kernel.map_apply' _ hmap _ hS, Kernel.comap_apply' _ _ _ S] at hs
    exact hs
  simp_rw [hpt]
  have hmcoe : Measurable fun s' =>
      traceKernel E' n (R.interventionMap ∘ actions) s' S :=
    Kernel.measurable_coe _ hS
  rw [← MeasureTheory.lintegral_map hmcoe R.stateMap_measurable, ← R.initial_commute e,
    externalTraceMeasure, Measure.bind_apply hS (Kernel.measurable _)]

theorem continuum_profile_preserved_scaled
    {External State Intervention Outcome State' Intervention' Outcome' : Type*}
    [MeasurableSpace State] [MeasurableSpace Outcome]
    [MeasurableSpace State'] [MeasurableSpace Outcome']
    {E : MeasurableCausalExperiment External State Intervention Outcome}
    {E' : MeasurableCausalExperiment External State' Intervention' Outcome'}
    {scale : ℕ}
    (R : MeasurableRepMap E E' scale)
    (budget : ℕ) (e e' : External)
    (hobs : ContinuumObsEqual E budget e e') :
    ∀ (n : ℕ) (actions : Fin n → Intervention),
      continuumExperimentCost E n actions ≤ budget →
      externalTraceMeasure E' e n (R.interventionMap ∘ actions) =
        externalTraceMeasure E' e' n (R.interventionMap ∘ actions) := by
  intro n actions hcost
  rw [← continuum_externalTraceMeasure_transport R e n actions,
    ← continuum_externalTraceMeasure_transport R e' n actions,
    hobs n actions hcost]

theorem continuum_profile_reflected_embedding
    {External State Intervention Outcome State' Intervention' Outcome' : Type*}
    [MeasurableSpace State] [MeasurableSpace Outcome]
    [MeasurableSpace State'] [MeasurableSpace Outcome']
    {E : MeasurableCausalExperiment External State Intervention Outcome}
    {E' : MeasurableCausalExperiment External State' Intervention' Outcome'}
    (R : MeasurableRepMap E E' 1)
    (hemb : MeasurableEmbedding R.outcomeMap)
    (budget : ℕ) (e e' : External)
    (hobs' : ContinuumObsEqual E' budget e e') :
    ContinuumObsEqual E budget e e' := by
  intro n actions hcost
  have hcost' : continuumExperimentCost E' n (R.interventionMap ∘ actions) ≤ budget := by
    have h1 := continuum_experimentCost_le_of_monotone R n actions
    rw [Nat.one_mul] at h1
    exact Nat.le_trans h1 hcost
  have heq' := hobs' n (R.interventionMap ∘ actions) hcost'
  rw [← continuum_externalTraceMeasure_transport R e n actions,
    ← continuum_externalTraceMeasure_transport R e' n actions] at heq'
  exact traceMap_measure_injective hemb n heq'

theorem continuum_profile_iff_affordable_embedding
    {External State Intervention Outcome State' Intervention' Outcome' : Type*}
    [MeasurableSpace State] [MeasurableSpace Outcome]
    [MeasurableSpace State'] [MeasurableSpace Outcome']
    {E : MeasurableCausalExperiment External State Intervention Outcome}
    {E' : MeasurableCausalExperiment External State' Intervention' Outcome'}
    (R : MeasurableRepMap E E' 1)
    (budget : ℕ)
    (haffSurj : ∀ a', E'.interventionCost a' ≤ budget →
      ∃ a, R.interventionMap a = a' ∧ E.interventionCost a ≤ E'.interventionCost a')
    (hemb : MeasurableEmbedding R.outcomeMap)
    (e e' : External) :
    ContinuumObsEqual E budget e e' ↔ ContinuumObsEqual E' budget e e' := by
  constructor
  · intro hobs n actions' hcost'
    have hpt : ∀ i : Fin n,
        ∃ a, R.interventionMap a = actions' i ∧ E.interventionCost a ≤ E'.interventionCost (actions' i) :=
      fun i => haffSurj (actions' i) (Nat.le_trans (continuumExperimentCost_mem_le E' actions' i) hcost')
    let actions : Fin n → Intervention := fun i => (hpt i).choose
    have hcomp : R.interventionMap ∘ actions = actions' := funext fun i => (hpt i).choose_spec.1
    have hcost : continuumExperimentCost E n actions ≤ budget := by
      have hle : continuumExperimentCost E n actions ≤ continuumExperimentCost E' n actions' :=
        Finset.sum_le_sum fun i _ => (hpt i).choose_spec.2
      exact Nat.le_trans hle hcost'
    have hEq := continuum_profile_preserved_scaled R budget e e' hobs n actions hcost
    simpa [hcomp] using hEq
  · exact continuum_profile_reflected_embedding R hemb budget e e'

theorem continuum_profile_reflected_polish
    {External State Intervention Outcome State' Intervention' Outcome' : Type*}
    [MeasurableSpace State]
    [TopologicalSpace Outcome] [PolishSpace Outcome] [MeasurableSpace Outcome] [BorelSpace Outcome]
    [MeasurableSpace State']
    [TopologicalSpace Outcome'] [T2Space Outcome'] [MeasurableSpace Outcome'] [BorelSpace Outcome']
    {E : MeasurableCausalExperiment External State Intervention Outcome}
    {E' : MeasurableCausalExperiment External State' Intervention' Outcome'}
    (R : MeasurableRepMap E E' 1)
    (hcont : Continuous R.outcomeMap)
    (hinj : Function.Injective R.outcomeMap)
    (budget : ℕ) (e e' : External)
    (hobs' : ContinuumObsEqual E' budget e e') :
    ContinuumObsEqual E budget e e' :=
  continuum_profile_reflected_embedding R (hcont.measurableEmbedding hinj) budget e e' hobs'

theorem continuum_profile_iff_polish
    {External State Intervention Outcome State' Intervention' Outcome' : Type*}
    [MeasurableSpace State]
    [TopologicalSpace Outcome] [PolishSpace Outcome] [MeasurableSpace Outcome] [BorelSpace Outcome]
    [MeasurableSpace State']
    [TopologicalSpace Outcome'] [T2Space Outcome'] [MeasurableSpace Outcome'] [BorelSpace Outcome']
    {E : MeasurableCausalExperiment External State Intervention Outcome}
    {E' : MeasurableCausalExperiment External State' Intervention' Outcome'}
    (R : MeasurableRepMap E E' 1)
    (budget : ℕ)
    (haffSurj : ∀ a', E'.interventionCost a' ≤ budget →
      ∃ a, R.interventionMap a = a' ∧ E.interventionCost a ≤ E'.interventionCost a')
    (hcont : Continuous R.outcomeMap)
    (hinj : Function.Injective R.outcomeMap)
    (e e' : External) :
    ContinuumObsEqual E budget e e' ↔ ContinuumObsEqual E' budget e e' :=
  continuum_profile_iff_affordable_embedding R budget haffSurj (hcont.measurableEmbedding hinj) e e'

theorem continuum_profile_reflected_standardBorel
    {External State Intervention Outcome State' Intervention' Outcome' : Type*}
    [MeasurableSpace State] [MeasurableSpace Outcome] [StandardBorelSpace Outcome]
    [MeasurableSpace State'] [MeasurableSpace Outcome']
    [MeasurableSpace.CountablySeparated Outcome']
    {E : MeasurableCausalExperiment External State Intervention Outcome}
    {E' : MeasurableCausalExperiment External State' Intervention' Outcome'}
    (R : MeasurableRepMap E E' 1)
    (hinj : Function.Injective R.outcomeMap)
    (budget : ℕ) (e e' : External)
    (hobs' : ContinuumObsEqual E' budget e e') :
    ContinuumObsEqual E budget e e' :=
  continuum_profile_reflected_embedding R (R.outcomeMap_measurable.measurableEmbedding hinj)
    budget e e' hobs'

theorem continuum_profile_iff_standardBorel
    {External State Intervention Outcome State' Intervention' Outcome' : Type*}
    [MeasurableSpace State] [MeasurableSpace Outcome] [StandardBorelSpace Outcome]
    [MeasurableSpace State'] [MeasurableSpace Outcome']
    [MeasurableSpace.CountablySeparated Outcome']
    {E : MeasurableCausalExperiment External State Intervention Outcome}
    {E' : MeasurableCausalExperiment External State' Intervention' Outcome'}
    (R : MeasurableRepMap E E' 1)
    (budget : ℕ)
    (haffSurj : ∀ a', E'.interventionCost a' ≤ budget →
      ∃ a, R.interventionMap a = a' ∧ E.interventionCost a ≤ E'.interventionCost a')
    (hinj : Function.Injective R.outcomeMap)
    (e e' : External) :
    ContinuumObsEqual E budget e e' ↔ ContinuumObsEqual E' budget e e' :=
  continuum_profile_iff_affordable_embedding R budget haffSurj
    (R.outcomeMap_measurable.measurableEmbedding hinj) e e'

end CovarianceTheorems

section EventVariationAndCounterexample

theorem continuum_event_variation_pushforward_eq
    {α β : Type*} [MeasurableSpace α] [MeasurableSpace β]
    (μ ν : Measure α) {f : α → β} (hf : Measurable f)
    {s : Set β} (hs : MeasurableSet s) :
    |(μ.map f s).toReal - (ν.map f s).toReal| =
      |(μ (f ⁻¹' s)).toReal - (ν (f ⁻¹' s)).toReal| := by
  rw [Measure.map_apply hf hs, Measure.map_apply hf hs]

theorem continuum_noninjective_real_counterexample :
    (Measure.dirac (1 : ℝ) ≠ Measure.dirac (-1 : ℝ)) ∧
    ((Measure.dirac (1 : ℝ)).map (fun x : ℝ => |x|) =
      (Measure.dirac (-1 : ℝ)).map (fun x : ℝ => |x|)) := by
  constructor
  · intro h
    have h1 : Measure.dirac (1 : ℝ) ({(1 : ℝ)} : Set ℝ) =
        Measure.dirac (-1 : ℝ) ({(1 : ℝ)} : Set ℝ) :=
      Measure.ext_iff.mp h {(1 : ℝ)} (measurableSet_singleton (1 : ℝ))
    have hm1 : (-1 : ℝ) ∉ ({(1 : ℝ)} : Set ℝ) := by norm_num
    have h1m : (1 : ℝ) ∈ ({(1 : ℝ)} : Set ℝ) := rfl
    rw [Measure.dirac_apply' (1 : ℝ) (measurableSet_singleton (1 : ℝ)),
      Measure.dirac_apply' (-1 : ℝ) (measurableSet_singleton (1 : ℝ)),
      Set.indicator_of_mem h1m, Set.indicator_of_not_mem hm1] at h1
    norm_num at h1
  · have hmeas : Measurable (fun x : ℝ => |x|) := continuous_abs.measurable
    rw [Measure.map_dirac hmeas (1 : ℝ), Measure.map_dirac hmeas (-1 : ℝ)]
    norm_num

end EventVariationAndCounterexample

end Semplex.ContinuumKernelCovariance
