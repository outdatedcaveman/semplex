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

end CerpBounds
