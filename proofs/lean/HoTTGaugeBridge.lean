import Lean

namespace Cerp.HoTTGaugeBridge

universe u

class GroupLike (G : Type u) where
  mul : G → G → G
  inv : G → G
  one : G
  mul_assoc : ∀ a b c : G, mul (mul a b) c = mul a (mul b c)
  one_mul : ∀ a : G, mul one a = a
  mul_one : ∀ a : G, mul a one = a
  inv_mul_cancel : ∀ a : G, mul (inv a) a = one
  mul_inv_cancel : ∀ a : G, mul a (inv a) = one
  inv_mul : ∀ a b : G, inv (mul a b) = mul (inv b) (inv a)
  inv_inv : ∀ a : G, inv (inv a) = a

variable {G : Type u} [GroupLike G]
local infixl:70 " ⋆ " => GroupLike.mul
local postfix:max "⁻¹" => GroupLike.inv
local notation "𝟙" => GroupLike.one

theorem inv_mul_left_cancel (a b : G) :
    a⁻¹ ⋆ (a ⋆ b) = b := by
  calc
    a⁻¹ ⋆ (a ⋆ b) = (a⁻¹ ⋆ a) ⋆ b := by rw [← GroupLike.mul_assoc]
    _ = 𝟙 ⋆ b := by rw [GroupLike.inv_mul_cancel]
    _ = b := GroupLike.one_mul b

theorem mul_inv_left_cancel (a b : G) :
    a ⋆ (a⁻¹ ⋆ b) = b := by
  calc
    a ⋆ (a⁻¹ ⋆ b) = (a ⋆ a⁻¹) ⋆ b := by rw [← GroupLike.mul_assoc]
    _ = 𝟙 ⋆ b := by rw [GroupLike.mul_inv_cancel]
    _ = b := GroupLike.one_mul b

abbrev Connection (G : Type u) := G × G × G
abbrev VertexGauge (G : Type u) := G × G × G

def holonomy (A : Connection G) : G :=
  A.2.2 ⋆ (A.2.1 ⋆ A.1)

def gaugeTransform (A : Connection G) (g : VertexGauge G) : Connection G :=
  (g.2.1 ⋆ A.1 ⋆ g.1⁻¹,
   g.2.2 ⋆ A.2.1 ⋆ g.2.1⁻¹,
   g.1 ⋆ A.2.2 ⋆ g.2.2⁻¹)

theorem holonomy_gauge_covariant
    (A : Connection G) (g : VertexGauge G) :
    holonomy (gaugeTransform A g) =
      g.1 ⋆ holonomy A ⋆ g.1⁻¹ := by
  simp [holonomy, gaugeTransform, GroupLike.mul_assoc,
    inv_mul_left_cancel, GroupLike.mul_one, GroupLike.one_mul]

def SameConjugacyClass (x y : G) : Prop :=
  ∃ k : G, y = k ⋆ x ⋆ k⁻¹

theorem gauge_related_holonomies_same_class
    (A : Connection G) (g : VertexGauge G) :
    SameConjugacyClass (holonomy A) (holonomy (gaugeTransform A g)) :=
  ⟨g.1, holonomy_gauge_covariant A g⟩

theorem stabilizer_maps_to_centralizer
    (A : Connection G) (g : VertexGauge G)
    (hfix : gaugeTransform A g = A) :
    g.1 ⋆ holonomy A = holonomy A ⋆ g.1 := by
  have hcov := holonomy_gauge_covariant A g
  rw [hfix] at hcov
  have h := hcov
  calc
    g.1 ⋆ holonomy A =
        (g.1 ⋆ holonomy A ⋆ g.1⁻¹) ⋆ g.1 := by
          simp [GroupLike.mul_assoc, GroupLike.inv_mul_cancel, GroupLike.mul_one]
    _ = holonomy A ⋆ g.1 := by rw [← h]

end Cerp.HoTTGaugeBridge
