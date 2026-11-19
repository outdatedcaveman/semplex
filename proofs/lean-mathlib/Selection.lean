import Mathlib

/-!
# Selection-rule identities (C43), first drafts for angelic checking (`python -m cerp.angelic`)

1. `chord_sq_sum`: the kinetic cost of Spike 80. For an orthogonal action R, the mean of ‖R x − x‖² over an
   orthonormal basis is 2 (1 − tr R / d), twice the character cost c = 1 − χ/d.
2. `fourier_laplacian`: the cost is a Laplacian eigenvalue (heat-kernel reading of exp(−λ c)). On ℤ/n with step
   set S, the Fourier mode χ_k is an eigenfunction of the random-walk Laplacian, eigenvalue 1 − |S|⁻¹ Σ_s χ_k(s).
3. `mediant_max`: semisimple reduction of the Harder–Narasimhan filtration. With an additive charge θ and positive
   dimensions, the slope of any nonempty union of blocks is at most the largest block slope.
-/

open Matrix BigOperators

theorem chord_sq_sum {d : ℕ} (R : Matrix (Fin d) (Fin d) ℝ) (hR : Rᵀ * R = 1) :
    ∑ i, ∑ j, (R j i - (1 : Matrix (Fin d) (Fin d) ℝ) j i) ^ 2 = 2 * (d - R.trace) := by
  have h1 : ∀ i, ∑ j, R j i ^ 2 = 1 := by
    intro i
    have := congrFun (congrFun hR i) i
    simpa [Matrix.mul_apply, Matrix.transpose_apply, sq] using this
  have h2 : ∀ i j, (R j i - (1 : Matrix (Fin d) (Fin d) ℝ) j i) ^ 2
      = R j i ^ 2 - 2 * R j i * (1 : Matrix (Fin d) (Fin d) ℝ) j i + (1 : Matrix (Fin d) (Fin d) ℝ) j i := by
    intro i j
    by_cases h : j = i <;> simp [Matrix.one_apply, h] <;> ring
  simp_rw [h2, Finset.sum_add_distrib, Finset.sum_sub_distrib, h1]
  simp [Matrix.trace, Matrix.one_apply, Finset.mul_sum]
  ring

theorem fourier_laplacian {n : ℕ} [NeZero n] (S : Finset (ZMod n)) (k : ℤ) (x : ZMod n) :
    let χ : ZMod n → ℂ := fun y => Complex.exp (2 * Real.pi * Complex.I * k * (y.val : ℂ) / n)
    χ x - (S.card : ℂ)⁻¹ * ∑ s in S, χ (x + s) = (1 - (S.card : ℂ)⁻¹ * ∑ s in S, χ s) * χ x := by
  intro χ
  have key : ∀ s, χ (x + s) = χ x * χ s := by
    intro s
    simp only [χ, ← Complex.exp_add]
    rw [Complex.exp_eq_exp_iff_exists_int]
    refine ⟨-k * ((x.val + s.val) / n : ℕ), ?_⟩
    rw [ZMod.val_add]
    have hn : (n : ℂ) ≠ 0 := by exact_mod_cast NeZero.ne n
    have hdiv := Nat.mod_add_div (x.val + s.val) n
    field_simp
    push_cast
    linear_combination hdiv
  simp_rw [key, ← Finset.mul_sum]
  ring

theorem mediant_max {ι : Type*} (s : Finset ι) (hs : s.Nonempty) (θ d : ι → ℝ) (hd : ∀ i ∈ s, 0 < d i) :
    (∑ i in s, θ i) / (∑ i in s, d i) ≤ s.sup' hs (fun i => θ i / d i) := by
  set M := s.sup' hs (fun i => θ i / d i)
  have hpos : 0 < ∑ i in s, d i := Finset.sum_pos hd hs
  rw [div_le_iff hpos, Finset.mul_sum]
  apply Finset.sum_le_sum
  intro i hi
  have h : θ i / d i ≤ M := Finset.le_sup' (fun i => θ i / d i) hi
  rw [div_le_iff (hd i hi)] at h
  linarith
