/-!
Spike 17 — finite module overlap and gluing.

A global profile has coordinates (x,y,z). Module A sees (x,z), Module B
sees (y,z), and their overlap sees z. Compatible local sections glue to a
unique global section. This is a concrete finite matching-family/descent model,
not a proof that all Synesism modules form a sheaf.
-/

namespace ModuleDescent

abbrev Global := Bool × Bool × Bool
abbrev ModuleA := Bool × Bool
abbrev ModuleB := Bool × Bool
abbrev Overlap := Bool

def restrictA (g : Global) : ModuleA := (g.1, g.2.2)
def restrictB (g : Global) : ModuleB := (g.2.1, g.2.2)

def toOverlapA (a : ModuleA) : Overlap := a.2
def toOverlapB (b : ModuleB) : Overlap := b.2

def Compatible (a : ModuleA) (b : ModuleB) : Prop :=
  toOverlapA a = toOverlapB b

def glue (a : ModuleA) (b : ModuleB) (_h : Compatible a b) : Global :=
  (a.1, b.1, a.2)

theorem restrictions_are_compatible (g : Global) :
    Compatible (restrictA g) (restrictB g) := rfl

theorem glue_restrictA (a : ModuleA) (b : ModuleB) (h : Compatible a b) :
    restrictA (glue a b h) = a := by
  cases a
  cases b
  rfl

theorem glue_restrictB (a : ModuleA) (b : ModuleB) (h : Compatible a b) :
    restrictB (glue a b h) = b := by
  cases a with
  | mk ax az =>
    cases b with
    | mk byY bz =>
      cases h
      rfl

/-- A compatible pair of local sections has a global amalgamation. -/
theorem compatible_sections_glue (a : ModuleA) (b : ModuleB)
    (h : Compatible a b) :
    ∃ g : Global, restrictA g = a ∧ restrictB g = b :=
  ⟨glue a b h, glue_restrictA a b h, glue_restrictB a b h⟩

/-- A global section is unique once both local restrictions are fixed. -/
theorem glue_unique (g : Global) (a : ModuleA) (b : ModuleB)
    (h : Compatible a b)
    (ha : restrictA g = a) (hb : restrictB g = b) :
    g = glue a b h := by
  cases g with
  | mk gx rest =>
    cases rest with
    | mk gy gz =>
      cases a with
      | mk ax az =>
        cases b with
        | mk byY bz =>
          simp [restrictA, restrictB] at ha hb
          rcases ha with ⟨rfl, rfl⟩
          rcases hb with ⟨rfl, rfl⟩
          rfl

/-- Existence of a global amalgamation is equivalent to overlap compatibility. -/
theorem global_exists_iff_compatible (a : ModuleA) (b : ModuleB) :
    (∃ g : Global, restrictA g = a ∧ restrictB g = b) ↔ Compatible a b := by
  constructor
  · rintro ⟨g, ha, hb⟩
    cases g with
    | mk gx rest =>
      cases rest with
      | mk gy gz =>
        cases a with
        | mk ax az =>
          cases b with
          | mk byY bz =>
            simp [restrictA, restrictB] at ha hb
            rcases ha with ⟨rfl, rfl⟩
            rcases hb with ⟨rfl, rfl⟩
            rfl
  · exact compatible_sections_glue a b

/-- Incompatible local descriptions cannot be the restrictions of one global being. -/
theorem incompatible_sections_do_not_glue :
    ¬ ∃ g : Global,
      restrictA g = (true, false) ∧ restrictB g = (false, true) := by
  intro h
  have hc := (global_exists_iff_compatible (true, false) (false, true)).mp h
  exact Bool.noConfusion hc

end ModuleDescent
