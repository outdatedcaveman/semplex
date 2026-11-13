/-
  Soundness of the "not a threshold function" certificate checked by
  cerp/kernel_bounds.py (Spike 08b), proved in Lean 4 core.

  Certificate: k points where f is true and k points where f is false, with
  equal coordinate-wise sums. Claim: no neuron [w.x >= t] is true on all of
  the first and false on all of the second.
-/

namespace CerpBounds

/-- w . p over the first n coordinates -/
def dot : Nat → (Nat → Int) → (Nat → Int) → Int
  | 0, _, _ => 0
  | n + 1, w, p => dot n w p + w n * p n

/-- sum of w . p over a list of points -/
def sdot (n : Nat) (w : Nat → Int) : List (Nat → Int) → Int
  | [] => 0
  | p :: ps => dot n w p + sdot n w ps

/-- coordinate-wise sum of a list of points -/
def csum (j : Nat) : List (Nat → Int) → Int
  | [] => 0
  | p :: ps => p j + csum j ps

theorem dot_add (w a b : Nat → Int) : ∀ n, dot n w (fun j => a j + b j) = dot n w a + dot n w b := by
  intro n
  induction n with
  | zero => simp [dot]
  | succ n ih => simp only [dot, ih, Int.mul_add]; omega

theorem dot_zero (w : Nat → Int) : ∀ n, dot n w (fun _ => 0) = 0 := by
  intro n
  induction n with
  | zero => rfl
  | succ n ih => simp [dot, ih]

theorem dot_congr (w a b : Nat → Int) : ∀ n, (∀ j, j < n → a j = b j) → dot n w a = dot n w b := by
  intro n
  induction n with
  | zero => intro _; rfl
  | succ n ih =>
      intro h
      simp only [dot]
      rw [ih (fun j hj => h j (Nat.lt_succ_of_lt hj)), h n (Nat.lt_succ_self n)]

/-- linearity: the sum of dot products is the dot product with the coordinate sums -/
theorem sdot_eq (n : Nat) (w : Nat → Int) : ∀ ps, sdot n w ps = dot n w (fun j => csum j ps) := by
  intro ps
  induction ps with
  | nil => simp [sdot, csum, dot_zero]
  | cons p ps ih =>
      simp only [sdot, csum, ih]
      exact (dot_add w p (fun j => csum j ps) n).symm

theorem sdot_ge (n : Nat) (w : Nat → Int) (t : Int) :
    ∀ ps, (∀ p, p ∈ ps → t ≤ dot n w p) → (ps.length : Int) * t ≤ sdot n w ps := by
  intro ps
  induction ps with
  | nil => intro _; simp [sdot]
  | cons p ps ih =>
      intro h
      have h1 := h p (List.mem_cons_self p ps)
      have h2 := ih (fun q hq => h q (List.mem_cons_of_mem p hq))
      have hl : (((p :: ps).length : Nat) : Int) * t = (ps.length : Int) * t + t := by
        simp only [List.length_cons, Int.natCast_add, Int.add_mul]
        simp
      rw [hl]
      simp only [sdot]
      omega

theorem sdot_lt (n : Nat) (w : Nat → Int) (t : Int) :
    ∀ ps, (∀ p, p ∈ ps → dot n w p < t) → sdot n w ps + (ps.length : Int) ≤ (ps.length : Int) * t := by
  intro ps
  induction ps with
  | nil => intro _; simp [sdot]
  | cons p ps ih =>
      intro h
      have h1 := h p (List.mem_cons_self p ps)
      have h2 := ih (fun q hq => h q (List.mem_cons_of_mem p hq))
      have hl : (((p :: ps).length : Nat) : Int) * t = (ps.length : Int) * t + t := by
        simp only [List.length_cons, Int.natCast_add, Int.add_mul]
        simp
      have hc : (((p :: ps).length : Nat) : Int) = (ps.length : Int) + 1 := by
        simp only [List.length_cons, Int.natCast_add]
        simp
      rw [hl, hc]
      simp only [sdot]
      omega

/-- The certificate is sound: equal point sums on a nonempty, equally sized pair of
    lists rule out every neuron that accepts all of `pos` and rejects all of `neg`. -/
theorem not_threshold_cert_sound (n : Nat) (pos neg : List (Nat → Int))
    (hlen : pos.length = neg.length) (hne : 0 < pos.length)
    (hsum : ∀ j, j < n → csum j pos = csum j neg) :
    ¬ ∃ (w : Nat → Int) (t : Int), (∀ p, p ∈ pos → t ≤ dot n w p) ∧ (∀ q, q ∈ neg → dot n w q < t) := by
  intro ⟨w, t, hp, hq⟩
  have h1 := sdot_ge n w t pos hp
  have h2 := sdot_lt n w t neg hq
  have he : sdot n w pos = sdot n w neg := by
    rw [sdot_eq, sdot_eq]
    exact dot_congr w _ _ n hsum
  rw [hlen] at h1
  omega

/-- Soundness of the two-halfspace coloring certificate (P048): if every
    2-colouring of the negative points makes at least one certified bad set
    `b.2` monochromatic, then no two threshold neurons can both accept all
    corresponding `b.1` points while covering all `b.2` points. -/
theorem not_two_halfspaces_cert_sound (n : Nat)
    (bad : List (List (Nat → Int) × List (Nat → Int)))
    (hcert : ∀ b, b ∈ bad → b.1.length = b.2.length ∧ 0 < b.1.length ∧
      ∀ j, j < n → csum j b.1 = csum j b.2)
    (hforce : ∀ col : (Nat → Int) → Bool, ∃ b, b ∈ bad ∧
      ((∀ q, q ∈ b.2 → col q = true) ∨ (∀ q, q ∈ b.2 → col q = false))) :
    ¬ ∃ (w₁ w₂ : Nat → Int) (t₁ t₂ : Int),
      (∀ b, b ∈ bad → (∀ p, p ∈ b.1 → t₁ ≤ dot n w₁ p) ∧ (∀ p, p ∈ b.1 → t₂ ≤ dot n w₂ p)) ∧
      (∀ b, b ∈ bad → ∀ q, q ∈ b.2 → dot n w₁ q < t₁ ∨ dot n w₂ q < t₂) := by
  intro ⟨w₁, w₂, t₁, t₂, hpos, hneg⟩
  let col : (Nat → Int) → Bool := fun q => decide (dot n w₁ q < t₁)
  obtain ⟨b, hb, hmono⟩ := hforce col
  obtain ⟨hlen, hne, hsum⟩ := hcert b hb
  obtain ⟨hp1, hp2⟩ := hpos b hb
  cases hmono with
  | inl htrue =>
      have hq1 : ∀ q, q ∈ b.2 → dot n w₁ q < t₁ := by
        intro q hq
        have ht := htrue q hq
        exact of_decide_eq_true ht
      exact not_threshold_cert_sound n b.1 b.2 hlen hne hsum ⟨w₁, t₁, hp1, hq1⟩
  | inr hfalse =>
      have hq2 : ∀ q, q ∈ b.2 → dot n w₂ q < t₂ := by
        intro q hq
        have hf := hfalse q hq
        have hn : ¬ (dot n w₁ q < t₁) := of_decide_eq_false hf
        cases hneg b hb q hq with
        | inl h1 => exact absurd h1 hn
        | inr h2 => exact h2
      exact not_threshold_cert_sound n b.1 b.2 hlen hne hsum ⟨w₂, t₂, hp2, hq2⟩

/-- Point-indicator weight vector for a binary point `x₀` (P042 constructive core). -/
def ptWeight (x₀ : Nat → Int) : Nat → Int :=
  fun j => if x₀ j = 1 then 1 else -1

/-- Sum of `x₀` over coordinates `< n`. -/
def ptThresh (x₀ : Nat → Int) : Nat → Int
  | 0 => 0
  | n + 1 => ptThresh x₀ n + x₀ n

theorem ptDot_le (x₀ x : Nat → Int) :
    ∀ n, (∀ j, j < n → x₀ j = 0 ∨ x₀ j = 1) → (∀ j, j < n → x j = 0 ∨ x j = 1) →
      dot n (ptWeight x₀) x ≤ ptThresh x₀ n := by
  intro n hx0 hx
  induction n with
  | zero => simp [dot, ptThresh]
  | succ n ih =>
      have ih' := ih (fun j hj => hx0 j (Nat.lt_succ_of_lt hj)) (fun j hj => hx j (Nat.lt_succ_of_lt hj))
      have h0 := hx0 n (Nat.lt_succ_self n)
      have h1 := hx n (Nat.lt_succ_self n)
      simp only [dot, ptThresh, ptWeight]
      rcases h0 with h0 | h0 <;> rcases h1 with h1 | h1 <;> simp [h0, h1] <;> omega

theorem ptDot_ge_iff (x₀ x : Nat → Int) :
    ∀ n, (∀ j, j < n → x₀ j = 0 ∨ x₀ j = 1) → (∀ j, j < n → x j = 0 ∨ x j = 1) →
      (ptThresh x₀ n ≤ dot n (ptWeight x₀) x ↔ ∀ j, j < n → x j = x₀ j) := by
  intro n hx0 hx
  induction n with
  | zero =>
      simp [dot, ptThresh]
  | succ n ih =>
      have hx0' : ∀ j, j < n → x₀ j = 0 ∨ x₀ j = 1 := fun j hj => hx0 j (Nat.lt_succ_of_lt hj)
      have hx' : ∀ j, j < n → x j = 0 ∨ x j = 1 := fun j hj => hx j (Nat.lt_succ_of_lt hj)
      have ih' := ih hx0' hx'
      have hle := ptDot_le x₀ x n hx0' hx'
      have h0 := hx0 n (Nat.lt_succ_self n)
      have h1 := hx n (Nat.lt_succ_self n)
      constructor
      · intro hge j hj
        have hstep : ptThresh x₀ n ≤ dot n (ptWeight x₀) x ∧ x n = x₀ n := by
          simp only [dot, ptThresh, ptWeight] at hge
          rcases h0 with h0 | h0 <;> rcases h1 with h1 | h1 <;> simp [h0, h1] at hge ⊢ <;> omega
        by_cases hjn : j < n
        · exact ih'.mp hstep.1 j hjn
        · have : j = n := by omega
          rw [this]; exact hstep.2
      · intro heq
        have hprev := ih'.mpr (fun j hj => heq j (Nat.lt_succ_of_lt hj))
        have hn := heq n (Nat.lt_succ_self n)
        simp only [dot, ptThresh, ptWeight, hn]
        rcases h0 with h0 | h0 <;> simp [h0] <;> omega

end CerpBounds
