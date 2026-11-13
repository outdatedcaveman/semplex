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

/-- Boolean equality on the first `n` coordinates. -/
def eqPrefix (x x₀ : Nat → Int) : Nat → Bool
  | 0 => true
  | n + 1 => eqPrefix x x₀ n && decide (x n = x₀ n)

theorem eqPrefix_true_iff (x x₀ : Nat → Int) :
    ∀ n, eqPrefix x x₀ n = true ↔ ∀ j, j < n → x j = x₀ j := by
  intro n
  induction n with
  | zero => simp [eqPrefix]
  | succ n ih =>
      simp only [eqPrefix, Bool.and_eq_true, decide_eq_true_eq, ih]
      constructor
      · intro ⟨hprev, hn⟩ j hj
        by_cases hjn : j < n
        · exact hprev j hjn
        · have : j = n := by omega
          rw [this]; exact hn
      · intro hall
        exact ⟨fun j hj => hall j (Nat.lt_succ_of_lt hj), hall n (Nat.lt_succ_self n)⟩

/-- Flipping a single point `x₀` in a single-neuron function `f(x) = [w·x ≥ t]`
    is realized by combining `(w, t)` with the point-selector neuron `(ptWeight x₀, ptThresh x₀ n)` (P042). -/
theorem one_bit_flip_add_point_neuron (n : Nat) (w x₀ x : Nat → Int) (t : Int)
    (hx0 : ∀ j, j < n → x₀ j = 0 ∨ x₀ j = 1)
    (hx : ∀ j, j < n → x j = 0 ∨ x j = 1) :
    let f := fun y => decide (t ≤ dot n w y)
    let p := fun y => decide (ptThresh x₀ n ≤ dot n (ptWeight x₀) y)
    let flipped := if eqPrefix x x₀ n then !(f x) else f x
    (f x₀ = false → flipped = (f x || p x)) ∧
    (f x₀ = true → flipped = (f x && !(p x))) := by
  intro f p flipped
  have hp : p x = true ↔ ∀ j, j < n → x j = x₀ j := by
    simp only [p, decide_eq_true_eq]
    exact ptDot_ge_iff x₀ x n hx0 hx
  have heq : eqPrefix x x₀ n = true ↔ ∀ j, j < n → x j = x₀ j := eqPrefix_true_iff x x₀ n
  have hpe : p x = eqPrefix x x₀ n := by
    cases hpx : p x <;> cases hex : eqPrefix x x₀ n
    · rfl
    · have h1 : p x = true := hp.mpr (heq.mp hex)
      rw [hpx] at h1; cases h1
    · have h1 : eqPrefix x x₀ n = true := heq.mpr (hp.mp hpx)
      rw [hex] at h1; cases h1
    · rfl
  constructor
  · intro hf0
    by_cases hmatch : eqPrefix x x₀ n = true
    · have hall := heq.mp hmatch
      have hfx : f x = f x₀ := by
        simp only [f, dot_congr w x x₀ n hall]
      have hpx : p x = true := by rw [hpe, hmatch]
      simp [flipped, hmatch, hfx, hf0, hpx]
    · have hmatchf : eqPrefix x x₀ n = false := by
        cases h : eqPrefix x x₀ n <;> simp_all
      have hpx : p x = false := by rw [hpe, hmatchf]
      simp [flipped, hmatchf, hpx]
  · intro hf0
    by_cases hmatch : eqPrefix x x₀ n = true
    · have hall := heq.mp hmatch
      have hfx : f x = f x₀ := by
        simp only [f, dot_congr w x x₀ n hall]
      have hpx : p x = true := by rw [hpe, hmatch]
      simp [flipped, hmatch, hfx, hf0, hpx]
    · have hmatchf : eqPrefix x x₀ n = false := by
        cases h : eqPrefix x x₀ n <;> simp_all
      have hpx : p x = false := by rw [hpe, hmatchf]
      simp [flipped, hmatchf, hpx]

private def pt3 (a b c : Int) : Nat → Int
  | 0 => a
  | 1 => b
  | 2 => c
  | _ => 0

private def pos3 : List (Nat → Int) :=
  [pt3 1 0 0, pt3 0 1 0, pt3 0 0 1, pt3 1 1 1]

private def neg3 : List (Nat → Int) :=
  [pt3 0 0 0, pt3 1 1 0, pt3 1 0 1, pt3 0 1 1]

/-- 3-bit parity is not computable by any single linear threshold neuron. -/
theorem parity3_not_threshold :
    ¬ ∃ (w : Nat → Int) (t : Int),
      (∀ p, p ∈ pos3 → t ≤ dot 3 w p) ∧ (∀ q, q ∈ neg3 → dot 3 w q < t) := by
  apply not_threshold_cert_sound 3 pos3 neg3 (by rfl) (by decide)
  intro j hj
  match j, hj with
  | 0, _ => rfl
  | 1, _ => rfl
  | 2, _ => rfl

/-- Evaluate a depth-2 OR-of-thresholds gate `⋁_{(w,t) ∈ ns} [w·x ≥ t]`. -/
def evalOr (n : Nat) (x : Nat → Int) : List ((Nat → Int) × Int) → Bool
  | [] => false
  | (w, t) :: rest => decide (t ≤ dot n w x) || evalOr n x rest

theorem evalOr_congr (n : Nat) (x y : Nat → Int) (h : ∀ j, j < n → x j = y j) :
    ∀ ns, evalOr n x ns = evalOr n y ns
  | [] => rfl
  | (w, t) :: rest => by
      simp only [evalOr, dot_congr w x y n h, evalOr_congr n x y h rest]

/-- Generalization of `one_bit_flip_add_point_neuron` to any depth-2 OR-of-thresholds
    circuit `ns` (`P040`/`P042`): flipping a false point `x₀` adds exactly one point-selector
    neuron `(ptWeight x₀, ptThresh x₀ n)` to the disjunction. -/
theorem depth2_or_flip_adds_one (n : Nat) (ns : List ((Nat → Int) × Int)) (x₀ x : Nat → Int)
    (hx0 : ∀ j, j < n → x₀ j = 0 ∨ x₀ j = 1)
    (hx : ∀ j, j < n → x j = 0 ∨ x j = 1)
    (hf0 : evalOr n x₀ ns = false) :
    let flipped := if eqPrefix x x₀ n then !(evalOr n x ns) else evalOr n x ns
    flipped = evalOr n x ((ptWeight x₀, ptThresh x₀ n) :: ns) := by
  intro flipped
  have hp : decide (ptThresh x₀ n ≤ dot n (ptWeight x₀) x) = true ↔ ∀ j, j < n → x j = x₀ j := by
    simp only [decide_eq_true_eq]
    exact ptDot_ge_iff x₀ x n hx0 hx
  have heq : eqPrefix x x₀ n = true ↔ ∀ j, j < n → x j = x₀ j := eqPrefix_true_iff x x₀ n
  by_cases hmatch : eqPrefix x x₀ n = true
  · have hall := heq.mp hmatch
    have hfx : evalOr n x ns = false := by
      rw [evalOr_congr n x x₀ hall ns, hf0]
    have hpx : decide (ptThresh x₀ n ≤ dot n (ptWeight x₀) x) = true := hp.mpr hall
    simp [flipped, evalOr, hmatch, hfx, hpx]
  · have hmatchf : eqPrefix x x₀ n = false := by
      cases h : eqPrefix x x₀ n <;> simp_all
    have hpx : decide (ptThresh x₀ n ≤ dot n (ptWeight x₀) x) = false := by
      cases h : decide (ptThresh x₀ n ≤ dot n (ptWeight x₀) x)
      · rfl
      · exfalso; exact hmatch (heq.mpr (hp.mp h))
    simp [flipped, evalOr, hmatchf, hpx]

private def pt4 (a b c d : Int) : Nat → Int
  | 0 => a
  | 1 => b
  | 2 => c
  | 3 => d
  | _ => 0

private def bad4 : List (List (Nat → Int) × List (Nat → Int)) :=
  [ ([pt4 1 0 0 0, pt4 0 1 0 0], [pt4 0 0 0 0, pt4 1 1 0 0])
  , ([pt4 1 0 0 0, pt4 0 0 1 0], [pt4 0 0 0 0, pt4 1 0 1 0])
  , ([pt4 1 1 1 0, pt4 1 0 0 0], [pt4 1 1 0 0, pt4 1 0 1 0])
  ]

/-- 4-bit parity cannot be separated by two halfspaces (P040/P048):
    three distance-2 even points form a triangle whose pairs each match
    an odd-parity pair with equal coordinate sums. -/
theorem parity4_not_two_halfspaces :
    ¬ ∃ (w₁ w₂ : Nat → Int) (t₁ t₂ : Int),
      (∀ b, b ∈ bad4 → (∀ p, p ∈ b.1 → t₁ ≤ dot 4 w₁ p) ∧ (∀ p, p ∈ b.1 → t₂ ≤ dot 4 w₂ p)) ∧
      (∀ b, b ∈ bad4 → ∀ q, q ∈ b.2 → dot 4 w₁ q < t₁ ∨ dot 4 w₂ q < t₂) := by
  apply not_two_halfspaces_cert_sound 4 bad4
  · intro b hb
    simp only [bad4, List.mem_cons, List.not_mem_nil, or_false] at hb
    rcases hb with rfl | rfl | rfl <;> refine ⟨rfl, by decide, fun j hj => ?_⟩ <;>
      match j, hj with
      | 0, _ => rfl
      | 1, _ => rfl
      | 2, _ => rfl
      | 3, _ => rfl
  · intro col
    cases h0 : col (pt4 0 0 0 0) <;> cases h1 : col (pt4 1 1 0 0) <;> cases h2 : col (pt4 1 0 1 0)
    · exact ⟨_, List.mem_cons_self _ _, Or.inr (fun q hq => by simp only [List.mem_cons, List.not_mem_nil, or_false] at hq; rcases hq with hq | hq <;> rw [hq] <;> assumption)⟩
    · exact ⟨_, List.mem_cons_self _ _, Or.inr (fun q hq => by simp only [List.mem_cons, List.not_mem_nil, or_false] at hq; rcases hq with hq | hq <;> rw [hq] <;> assumption)⟩
    · exact ⟨_, List.mem_cons_of_mem _ (List.mem_cons_self _ _), Or.inr (fun q hq => by simp only [List.mem_cons, List.not_mem_nil, or_false] at hq; rcases hq with hq | hq <;> rw [hq] <;> assumption)⟩
    · exact ⟨_, List.mem_cons_of_mem _ (List.mem_cons_of_mem _ (List.mem_cons_self _ _)), Or.inl (fun q hq => by simp only [List.mem_cons, List.not_mem_nil, or_false] at hq; rcases hq with hq | hq <;> rw [hq] <;> assumption)⟩
    · exact ⟨_, List.mem_cons_of_mem _ (List.mem_cons_of_mem _ (List.mem_cons_self _ _)), Or.inr (fun q hq => by simp only [List.mem_cons, List.not_mem_nil, or_false] at hq; rcases hq with hq | hq <;> rw [hq] <;> assumption)⟩
    · exact ⟨_, List.mem_cons_of_mem _ (List.mem_cons_self _ _), Or.inl (fun q hq => by simp only [List.mem_cons, List.not_mem_nil, or_false] at hq; rcases hq with hq | hq <;> rw [hq] <;> assumption)⟩
    · exact ⟨_, List.mem_cons_self _ _, Or.inl (fun q hq => by simp only [List.mem_cons, List.not_mem_nil, or_false] at hq; rcases hq with hq | hq <;> rw [hq] <;> assumption)⟩
    · exact ⟨_, List.mem_cons_self _ _, Or.inl (fun q hq => by simp only [List.mem_cons, List.not_mem_nil, or_false] at hq; rcases hq with hq | hq <;> rw [hq] <;> assumption)⟩

/-- Flipping a true point `x₀` to false in `evalOr` is realized by conjoining
    with the negated point-selector neuron `!(ptWeight x₀ · x ≥ ptThresh x₀ n)`. -/
theorem depth2_or_flip_true_to_false (n : Nat) (ns : List ((Nat → Int) × Int)) (x₀ x : Nat → Int)
    (hx0 : ∀ j, j < n → x₀ j = 0 ∨ x₀ j = 1)
    (hx : ∀ j, j < n → x j = 0 ∨ x j = 1)
    (ht0 : evalOr n x₀ ns = true) :
    let flipped := if eqPrefix x x₀ n then !(evalOr n x ns) else evalOr n x ns
    flipped = (evalOr n x ns && !(decide (ptThresh x₀ n ≤ dot n (ptWeight x₀) x))) := by
  intro flipped
  have hp : decide (ptThresh x₀ n ≤ dot n (ptWeight x₀) x) = true ↔ ∀ j, j < n → x j = x₀ j := by
    simp only [decide_eq_true_eq]
    exact ptDot_ge_iff x₀ x n hx0 hx
  have heq : eqPrefix x x₀ n = true ↔ ∀ j, j < n → x j = x₀ j := eqPrefix_true_iff x x₀ n
  by_cases hmatch : eqPrefix x x₀ n = true
  · have hall := heq.mp hmatch
    have hfx : evalOr n x ns = true := by rw [evalOr_congr n x x₀ hall ns, ht0]
    have hpx : decide (ptThresh x₀ n ≤ dot n (ptWeight x₀) x) = true := hp.mpr hall
    simp [flipped, hmatch, hfx, hpx]
  · have hmatchf : eqPrefix x x₀ n = false := by cases h : eqPrefix x x₀ n <;> simp_all
    have hpx : decide (ptThresh x₀ n ≤ dot n (ptWeight x₀) x) = false := by
      cases h : decide (ptThresh x₀ n ≤ dot n (ptWeight x₀) x)
      · rfl
      · exfalso; exact hmatch (heq.mpr (hp.mp h))
    simp [flipped, hmatchf, hpx]

end CerpBounds
