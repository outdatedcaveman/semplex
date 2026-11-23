import Lean

/-!
The response-profile quotient is the coarsest sufficient representation.

This is the elementary Set-level universal property underlying the
causal-semantic state construction. It does not assume a particular
physical model; the response map must be supplied and grounded separately.
-/

namespace Cerp.ResponseQuotient

variable {H Z R : Type}

/-- Histories are equivalent exactly when their protected response profiles agree. -/
def responseRel (Φ : H → R) (h h' : H) : Prop :=
  Φ h = Φ h'

def responseSetoid (Φ : H → R) : Setoid H where
  r := responseRel Φ
  iseqv := {
    refl := fun _ => rfl
    symm := fun h => h.symm
    trans := fun h₁ h₂ => h₁.trans h₂
  }

/-- The canonical map from histories to their semantic response class. -/
def quotientMap (Φ : H → R) (h : H) : Quotient (responseSetoid Φ) :=
  Quotient.mk (responseSetoid Φ) h

/-- The response profile descends to the quotient. -/
def quotientResponse (Φ : H → R) :
    Quotient (responseSetoid Φ) → R :=
  Quotient.lift Φ (by
    intro h h' heq
    exact heq)

/-- The quotient does not identify distinct protected response profiles. -/
theorem quotientResponse_injective (Φ : H → R) :
    ∀ x y, quotientResponse Φ x = quotientResponse Φ y → x = y := by
  intro x y hxy
  induction x using Quotient.inductionOn with
  | _ h =>
    induction y using Quotient.inductionOn with
    | _ h' =>
      apply Quotient.sound
      exact hxy

/-- The image subtype of a representation map, avoiding unused implementation states. -/
def imageSubtype (r : H → Z) := {z : Z // ∃ h, r h = z}

/--
Any representation that is sufficient for the protected response profile
factors through the response quotient. The factor is defined on the image
of the representation, so unused implementation states are irrelevant.
-/
noncomputable def factorThrough
    (Φ : H → R) (r : H → Z)
    (z : imageSubtype r) : Quotient (responseSetoid Φ) :=
  Quotient.mk (responseSetoid Φ) (Classical.choose z.property)

/-- The factor map reconstructs the canonical quotient map. -/
theorem factorThrough_comp
    (Φ : H → R) (r : H → Z) (decode : Z → R)
    (hadequate : ∀ h, Φ h = decode (r h)) (h : H) :
    factorThrough Φ r ⟨r h, ⟨h, rfl⟩⟩ =
      quotientMap Φ h := by
  apply Quotient.sound
  have hEx : ∃ h', r h' = r h := ⟨h, rfl⟩
  calc
    Φ (Classical.choose hEx) =
        decode (r (Classical.choose hEx)) := hadequate _
    _ = decode (r h) := by rw [Classical.choose_spec hEx]
    _ = Φ h := (hadequate h).symm

/-- The factor map is unique on the image of r. -/
theorem factorThrough_unique
    (Φ : H → R) (r : H → Z) (decode : Z → R)
    (hadequate : ∀ h, Φ h = decode (r h))
    (g : imageSubtype r → Quotient (responseSetoid Φ))
    (hg : ∀ h, g ⟨r h, ⟨h, rfl⟩⟩ = quotientMap Φ h) :
    g = factorThrough Φ r := by
  funext z
  obtain ⟨h, hh⟩ := z.property
  have hz : z = ⟨r h, ⟨h, rfl⟩⟩ := by
    apply Subtype.ext
    exact hh.symm
  rw [hz]
  rw [hg h]
  exact (factorThrough_comp Φ r decode hadequate h).symm

end Cerp.ResponseQuotient
