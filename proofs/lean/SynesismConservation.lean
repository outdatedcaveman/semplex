/-!
Spike 17 — Synesism's binary partition/conservation example.

This is a deliberately small dyadic model of the source's example:
one zeroth-order semon (1) partitions into two first-order sema (1/2 each).
The model keeps value-equivalence separate from structural configuration.
It is not yet a general definition of molarity or a model of the full Worldtree.
-/

namespace SynesismConservation

structure PartitionProfile where
  order : Nat
  count : Nat
  signatureCode : Nat
  deriving DecidableEq, Repr

/-- Cross-multiplication comparison for the dyadic aggregate count / 2^order. -/
def molarityEquivalent (a b : PartitionProfile) : Prop :=
  a.count * 2 ^ b.order = b.count * 2 ^ a.order

/-- Half-value relation, expressed without introducing a rational-number library. -/
def halfMolarityOf (a b : PartitionProfile) : Prop :=
  2 * a.count * 2 ^ b.order = b.count * 2 ^ a.order

/-- Structural sameness is stronger: order, multiplicity, and signature must agree. -/
def sameConfiguration (a b : PartitionProfile) : Prop :=
  a.order = b.order ∧ a.count = b.count ∧ a.signatureCode = b.signatureCode

/-- A binary partition doubles the number of equal-order constituents. -/
def binaryPartition (p : PartitionProfile) : PartitionProfile :=
  { order := p.order + 1
    count := 2 * p.count
    signatureCode := p.signatureCode + 1 }

theorem binaryPartition_preserves_molarity (p : PartitionProfile) :
    molarityEquivalent p (binaryPartition p) := by
  unfold molarityEquivalent binaryPartition
  simp [Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]

theorem nat_ne_succ (n : Nat) : n ≠ n + 1 :=
  Nat.ne_of_lt (Nat.lt_succ_self n)


theorem molarityEquivalent_refl (p : PartitionProfile) :
    molarityEquivalent p p := by
  rfl

theorem molarityEquivalent_symm {a b : PartitionProfile}
    (h : molarityEquivalent a b) : molarityEquivalent b a :=
  h.symm

theorem molarityEquivalent_trans {a b c : PartitionProfile}
    (hab : molarityEquivalent a b) (hbc : molarityEquivalent b c) :
    molarityEquivalent a c := by
  unfold molarityEquivalent at *
  have h1 : (a.count * 2 ^ b.order) * 2 ^ c.order =
      (b.count * 2 ^ a.order) * 2 ^ c.order :=
    congrArg (fun n => n * 2 ^ c.order) hab
  have h2 : (b.count * 2 ^ c.order) * 2 ^ a.order =
      (c.count * 2 ^ b.order) * 2 ^ a.order :=
    congrArg (fun n => n * 2 ^ a.order) hbc
  have hcalc :
      (a.count * 2 ^ c.order) * 2 ^ b.order =
      (c.count * 2 ^ a.order) * 2 ^ b.order := by
    calc
      (a.count * 2 ^ c.order) * 2 ^ b.order =
          (a.count * 2 ^ b.order) * 2 ^ c.order := by ac_rfl
      _ = (b.count * 2 ^ a.order) * 2 ^ c.order := h1
      _ = (b.count * 2 ^ c.order) * 2 ^ a.order := by ac_rfl
      _ = (c.count * 2 ^ b.order) * 2 ^ a.order := h2
      _ = (c.count * 2 ^ a.order) * 2 ^ b.order := by ac_rfl
  have hpos : 0 < 2 ^ b.order := Nat.pow_pos (by decide)
  exact Nat.mul_right_cancel hpos hcalc

def molaritySetoid : Setoid PartitionProfile where
  r := molarityEquivalent
  iseqv := ⟨molarityEquivalent_refl, molarityEquivalent_symm, molarityEquivalent_trans⟩

theorem binaryPartition_changes_order (p : PartitionProfile) :
    p.order ≠ (binaryPartition p).order :=
  nat_ne_succ p.order

def zerothOrderParent : PartitionProfile :=
  ⟨0, 1, 0⟩

def twoFirstOrderOffspring : PartitionProfile :=
  ⟨1, 2, 1⟩

def oneFirstOrderOffspring : PartitionProfile :=
  ⟨1, 1, 1⟩

theorem each_first_order_offspring_has_half_value :
    halfMolarityOf oneFirstOrderOffspring zerothOrderParent := by
  simp [halfMolarityOf, oneFirstOrderOffspring, zerothOrderParent]

theorem parent_and_two_offspring_are_value_equivalent :
    molarityEquivalent zerothOrderParent twoFirstOrderOffspring := by
  simp [molarityEquivalent, zerothOrderParent, twoFirstOrderOffspring]

theorem parent_and_two_offspring_are_not_structurally_identical :
    ¬ sameConfiguration zerothOrderParent twoFirstOrderOffspring := by
  simp [sameConfiguration, zerothOrderParent, twoFirstOrderOffspring]


/-- Molarity-equivalence does not preserve structural order, so order cannot descend
through the quotient by molarity alone. -/
theorem order_not_constant_on_molarity_classes :
    ¬ ∀ a b, molarityEquivalent a b → a.order = b.order := by
  intro h
  have horder := h zerothOrderParent twoFirstOrderOffspring
    parent_and_two_offspring_are_value_equivalent
  simp [zerothOrderParent, twoFirstOrderOffspring] at horder

/-- The same counterexample shows that multiplicity is not preserved. -/
theorem count_not_constant_on_molarity_classes :
    ¬ ∀ a b, molarityEquivalent a b → a.count = b.count := by
  intro h
  have hcount := h zerothOrderParent twoFirstOrderOffspring
    parent_and_two_offspring_are_value_equivalent
  simp [zerothOrderParent, twoFirstOrderOffspring] at hcount

/-- A system state carries a persistent synod anchor separately from its configuration. This token models the source's system invariant, not ordinary numerical identity. -/
structure SystemState (Synod : Type) where
  synodAnchor : Synod
  profile : PartitionProfile

/-- A coherent transition preserves the system's synod and total semonic value. -/
def CoherentEvolution {Synod : Type}
    (before after : SystemState Synod) : Prop :=
  before.synodAnchor = after.synodAnchor ∧ molarityEquivalent before.profile after.profile

def partitionState {Synod : Type} (s : SystemState Synod) : SystemState Synod :=
  { s with profile := binaryPartition s.profile }

theorem binary_partition_is_coherent {Synod : Type}
    (s : SystemState Synod) :
    CoherentEvolution s (partitionState s) := by
  constructor
  · rfl
  · exact binaryPartition_preserves_molarity s.profile

theorem binary_partition_changes_state {Synod : Type}
    (s : SystemState Synod) :
    s ≠ partitionState s := by
  intro h
  have hOrder : s.profile.order = (partitionState s).profile.order :=
    congrArg (fun state => state.profile.order) h
  exact binaryPartition_changes_order s.profile hOrder

end SynesismConservation
