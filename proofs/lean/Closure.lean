/-
  Closure.lean — Plato and Aristotle in the deterministic case, and Peirce's law.
  Core Lean 4, no Mathlib. See charter/FOUNDATIONS.md §9–§10.

  Part A. A coarse-graining π of the states of an input-driven deterministic
  system has its own (macro) dynamics iff it is a congruence (closure). The
  coarsest congruence that still decides an output o is the Myhill–Nerode
  relation x ≈ y ↔ ∀ w, o (run w x) = o (run w y): it is closed, it refines o,
  and every closed coarse-graining that decides o refines it.

  Part B. Peirce's law ((P → Q) → P) → P is equivalent to excluded middle,
  holds constructively for decidable P, and is never refutable (its double
  negation is intuitionistically provable).
-/

namespace Closure

variable {α β γ σ : Type}

/-! ## Part A: closure -/

/-- π is a congruence of the letter actions T. -/
def Congruence (T : σ → α → α) (π : α → β) : Prop :=
  ∀ a x y, π x = π y → π (T a x) = π (T a y)

/-- π carries its own macro dynamics. -/
def HasMacroDynamics (T : σ → α → α) (π : α → β) : Prop :=
  ∃ Tbar : σ → β → β, ∀ a x, π (T a x) = Tbar a (π x)

theorem macro_of_congruence (T : σ → α → α) (π : α → β)
    (h : Congruence T π) : HasMacroDynamics T π := by
  refine ⟨fun a b => @dite _ (∃ x, π x = b) (Classical.propDecidable _)
      (fun hb => π (T a (Classical.choose hb))) (fun _ => b), ?_⟩
  intro a x
  have hb : ∃ x', π x' = π x := ⟨x, rfl⟩
  show π (T a x) = @dite _ (∃ x', π x' = π x) (Classical.propDecidable _)
      (fun hb => π (T a (Classical.choose hb))) (fun _ => π x)
  rw [@dif_pos _ (Classical.propDecidable _) hb]
  exact (h a _ _ (Classical.choose_spec hb)).symm

theorem congruence_of_macro (T : σ → α → α) (π : α → β)
    (h : HasMacroDynamics T π) : Congruence T π := by
  intro a x y hxy
  obtain ⟨Tbar, hT⟩ := h
  rw [hT a x, hT a y, hxy]

/-- Plato–Aristotle, deterministic form: a macrostate has its own dynamics iff it is closed. -/
theorem closure_iff (T : σ → α → α) (π : α → β) :
    HasMacroDynamics T π ↔ Congruence T π :=
  ⟨congruence_of_macro T π, macro_of_congruence T π⟩

/-- Closed coarse-grainings are closed under meet (pairing). -/
theorem congruence_meet (T : σ → α → α) (π₁ : α → β) (π₂ : α → γ)
    (h₁ : Congruence T π₁) (h₂ : Congruence T π₂) :
    Congruence T (fun x => (π₁ x, π₂ x)) := by
  intro a x y hxy
  have e₁ : π₁ x = π₁ y := congrArg Prod.fst hxy
  have e₂ : π₂ x = π₂ y := congrArg Prod.snd hxy
  show (π₁ (T a x), π₂ (T a x)) = (π₁ (T a y), π₂ (T a y))
  rw [h₁ a x y e₁, h₂ a x y e₂]

/-- Running a word (letters applied left to right). -/
def run (T : σ → α → α) : List σ → α → α
  | [], x => x
  | a :: w, x => run T w (T a x)

/-- The Myhill–Nerode relation of output o. -/
def MN (T : σ → α → α) (o : α → γ) (x y : α) : Prop :=
  ∀ w, o (run T w x) = o (run T w y)

theorem MN_closed (T : σ → α → α) (o : α → γ) (a : σ) (x y : α)
    (h : MN T o x y) : MN T o (T a x) (T a y) :=
  fun w => h (a :: w)

theorem MN_decides (T : σ → α → α) (o : α → γ) (x y : α)
    (h : MN T o x y) : o x = o y :=
  h []

/-- Every closed coarse-graining that decides o refines Myhill–Nerode:
    the Myhill–Nerode relation is the coarsest closed macrostate deciding o. -/
theorem MN_coarsest (T : σ → α → α) (o : α → γ) (π : α → β)
    (hc : Congruence T π) (hd : ∀ x y, π x = π y → o x = o y) :
    ∀ x y, π x = π y → MN T o x y := by
  intro x y hxy w
  induction w generalizing x y with
  | nil => exact hd x y hxy
  | cons a w ih => exact ih (T a x) (T a y) (hc a x y hxy)

/-! ## Part B: Peirce's law -/

def Peirce : Prop := ∀ P Q : Prop, ((P → Q) → P) → P
def ExcludedMiddle : Prop := ∀ P : Prop, P ∨ ¬P

theorem em_of_peirce (h : Peirce) : ExcludedMiddle := by
  intro P
  exact h (P ∨ ¬P) False (fun k => Or.inr (fun p => k (Or.inl p)))

theorem peirce_of_em (h : ExcludedMiddle) : Peirce := by
  intro P Q f
  cases h P with
  | inl p => exact p
  | inr np => exact f (fun p => absurd p np)

/-- Peirce's law and excluded middle are interderivable, intuitionistically. -/
theorem peirce_iff_em : Peirce ↔ ExcludedMiddle :=
  ⟨em_of_peirce, peirce_of_em⟩

/-- On a decidable proposition (every proposition about a finite atlas) Peirce's law holds constructively. -/
theorem peirce_decidable (P Q : Prop) [Decidable P] : ((P → Q) → P) → P := by
  intro f
  by_cases hp : P
  · exact hp
  · exact f (fun p => absurd p hp)

/-- Peirce's law is never refutable: its double negation is intuitionistically provable (Glivenko). -/
theorem not_not_peirce (P Q : Prop) : ¬¬(((P → Q) → P) → P) := by
  intro h
  apply h
  intro f
  apply f
  intro p
  exact absurd (fun _ => p) h

end Closure
