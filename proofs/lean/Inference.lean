/-!
# Learning as rational nonmonotonic inference, for any (possibly infinite) hypothesis space

`H` is an arbitrary type of hypotheses (functions, programs, concepts), `rank : H → Nat` a cost
(circuit size, description length). Evidence is a predicate `D : H → Prop` (the hypotheses
consistent with it). The learner concludes `φ` from `D` when every least-cost hypothesis
consistent with `D` satisfies `φ`:

  `Entails rank D φ  :↔  ∀ f, Pref rank D f → φ f`.

Because `Nat` is well-founded, minimal elements exist whenever `D` is inhabited, so the relation
is rational (Kraus–Lehmann–Magidor 1990; Lehmann–Magidor 1992) with no finiteness assumption.
Core Lean 4 only; no Mathlib.
-/

namespace Inference

variable {H : Type} (rank : H → Nat)

/-- `f` is a least-cost hypothesis consistent with the evidence `D`. -/
def Pref (D : H → Prop) (f : H) : Prop := D f ∧ ∀ g, D g → rank f ≤ rank g

/-- `D |~ φ`: every least-cost hypothesis consistent with `D` satisfies `φ`. -/
def Entails (D φ : H → Prop) : Prop := ∀ f, Pref rank D f → φ f

/-- Evidence `D` extended by the conclusion `a`. -/
def And' (D a : H → Prop) : H → Prop := fun f => D f ∧ a f

/-- Well-foundedness: any inhabited evidence set has a least-cost element. -/
theorem exists_pref (D : H → Prop) (h : ∃ f, D f) : ∃ m, Pref rank D m := by
  have key : ∀ n, ∀ f, D f → rank f = n → ∃ m, Pref rank D m := by
    intro n
    induction n using Nat.strongRecOn with
    | _ n ih =>
      intro f hf hr
      apply Classical.byContradiction
      intro hno
      have hmin : ∀ g, D g → rank f ≤ rank g := by
        intro g hg
        apply Classical.byContradiction
        intro hlt
        have hlt' : rank g < n := by omega
        exact hno (ih (rank g) hlt' g hg rfl)
      exact hno ⟨f, hf, hmin⟩
  obtain ⟨f, hf⟩ := h
  exact key (rank f) f hf rfl

/-- Reflexivity: the evidence is concluded. -/
theorem reflexivity (D : H → Prop) : Entails rank D D := fun _ h => h.1

/-- Right weakening. -/
theorem right_weakening (D φ ψ : H → Prop) (himp : ∀ f, φ f → ψ f)
    (h : Entails rank D φ) : Entails rank D ψ := fun f hf => himp f (h f hf)

/-- Cut: what follows from evidence plus a conclusion follows from the evidence. -/
theorem cut (D a b : H → Prop) (ha : Entails rank D a) (hb : Entails rank (And' D a) b) :
    Entails rank D b := by
  intro f hf
  apply hb f
  exact ⟨⟨hf.1, ha f hf⟩, fun g hg => hf.2 g hg.1⟩

/-- Cautious monotony: adding a conclusion as evidence keeps every other conclusion.
    This is the step that needs well-foundedness (`exists_pref`). -/
theorem cautious_monotony (D a b : H → Prop) (ha : Entails rank D a) (hb : Entails rank D b) :
    Entails rank (And' D a) b := by
  intro f hf
  apply hb f
  refine ⟨hf.1.1, fun g hg => ?_⟩
  obtain ⟨m, hm⟩ := exists_pref rank D ⟨g, hg⟩
  have hfm : rank f ≤ rank m := hf.2 m ⟨hm.1, ha m hm⟩
  exact Nat.le_trans hfm (hm.2 g hg)

/-- Rational monotony: adding anything not ruled out keeps every conclusion. -/
theorem rational_monotony (D a b : H → Prop) (hb : Entails rank D b)
    (hnot : ¬ Entails rank D (fun f => ¬ a f)) : Entails rank (And' D a) b := by
  intro f hf
  have : ∃ m, Pref rank D m ∧ a m := by
    apply Classical.byContradiction
    intro hno
    exact hnot (fun m hm ham => hno ⟨m, hm, ham⟩)
  obtain ⟨m, hm, ham⟩ := this
  apply hb f
  refine ⟨hf.1.1, fun g hg => ?_⟩
  exact Nat.le_trans (hf.2 m ⟨hm.1, ham⟩) (hm.2 g hg)

/-- Nonmonotonicity: classical monotony fails. Two hypotheses, `true` (cost 0) and `false`
    (cost 1). With no evidence the learner concludes "true"; the evidence "false" retracts it. -/
theorem not_monotone :
    ∃ (H : Type) (rank : H → Nat) (D a b : H → Prop),
      Entails rank D b ∧ ¬ Entails rank (And' D a) b := by
  refine ⟨Bool, fun x => if x then 0 else 1, fun _ => True, fun x => x = false,
    fun x => x = true, ?_, ?_⟩
  · intro f hf
    have h := hf.2 true trivial
    cases f with
    | true => rfl
    | false => simp at h
  · intro h
    have := h false ⟨⟨trivial, rfl⟩, fun g hg => by rw [hg.2]; exact Nat.le_refl _⟩
    simp at this

end Inference
