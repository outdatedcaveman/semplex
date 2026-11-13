/-
  The Protocol-Frame Theory (PFT) of canonical epistemology — core theorems.
  Lean 4 core, no Mathlib. See THEORY.md for the informal account.

  A protocol frame is (H, P, obs): hypotheses H (worlds, systems, inputs,
  processes…), protocols P (measurements, interventions, variables, tests…),
  and obs : P → H → O, what protocol p reveals about hypothesis h.
  An observational power is a set of protocols Ω (a predicate on P).
-/

namespace PFT

universe u v w x

variable {H : Type u} {P : Type v} {O : Type w} {A : Type x}

/-! ## §1 Indistinguishability and the Galois connection -/

/-- h and h' cannot be told apart by any protocol in Ω. -/
def Indist (obs : P → H → O) (Ω : P → Prop) (h h' : H) : Prop :=
  ∀ p, Ω p → obs p h = obs p h'

theorem indist_equivalence (obs : P → H → O) (Ω : P → Prop) :
    (∀ h, Indist obs Ω h h) ∧ (∀ h h', Indist obs Ω h h' → Indist obs Ω h' h) ∧
    (∀ h₁ h₂ h₃, Indist obs Ω h₁ h₂ → Indist obs Ω h₂ h₃ → Indist obs Ω h₁ h₃) :=
  ⟨fun _ _ _ => rfl, fun _ _ hi p hp => (hi p hp).symm,
   fun _ _ _ a b p hp => (a p hp).trans (b p hp)⟩

/-- Theorem 1 (antitonicity): more observational power, finer distinctions. -/
theorem indist_antitone (obs : P → H → O) {Ω Ω' : P → Prop} (hsub : ∀ p, Ω p → Ω' p)
    {h h' : H} : Indist obs Ω' h h' → Indist obs Ω h h' :=
  fun hi p hp => hi p (hsub p hp)

/-- The protocols that cannot see through a relation R. -/
def Blind (obs : P → H → O) (R : H → H → Prop) (p : P) : Prop :=
  ∀ h h', R h h' → obs p h = obs p h'

/-- Theorem 2 (Galois connection): R ⊆ ≡_Ω  ↔  Ω ⊆ Blind(R).
    Observational power and indistinguishability determine each other. -/
theorem galois (obs : P → H → O) (Ω : P → Prop) (R : H → H → Prop) :
    (∀ h h', R h h' → Indist obs Ω h h') ↔ (∀ p, Ω p → Blind obs R p) :=
  ⟨fun hR p hp h h' hr => hR h h' hr p hp, fun hB h h' hr p hp => hB p hp h h' hr⟩

/-! ## §2 Determinacy and the discernibility duality -/

/-- Ω determines the query q on the hypothesis set S. -/
def Determines (obs : P → H → O) (Ω : P → Prop) (S : H → Prop) (q : H → A) : Prop :=
  ∀ h h', S h → S h' → Indist obs Ω h h' → q h = q h'

/-- Ω hits every conflict: each relevant pair (different answers) is separated in Ω. -/
def HitsConflicts (obs : P → H → O) (Ω : P → Prop) (S : H → Prop) (q : H → A) : Prop :=
  ∀ h h', S h → S h' → q h ≠ q h' → ∃ p, Ω p ∧ obs p h ≠ obs p h'

/-- Theorem 3 (discernibility duality). Determining a query is the same as
    hitting every conflict set D(h,h') = {p | obs p h ≠ obs p h'} of a relevant
    pair. Instances: minimal sufficient features (P = variables), minimal
    discriminating experiment sets (P = interventions), distinguishing test
    suites (P = contexts). -/
theorem duality (obs : P → H → O) (Ω : P → Prop) (S : H → Prop) (q : H → A) :
    Determines obs Ω S q ↔ HitsConflicts obs Ω S q := by
  constructor
  · intro hd h h' hs hs' hq
    apply Classical.byContradiction
    intro hno
    apply hq
    apply hd h h' hs hs'
    intro p hp
    apply Classical.byContradiction
    intro hne
    exact hno ⟨p, hp, hne⟩
  · intro hh h h' hs hs' hi
    apply Classical.byContradiction
    intro hq
    obtain ⟨p, hp, hne⟩ := hh h h' hs hs' hq
    exact hne (hi p hp)

/-- Determinacy is monotone in observational power. -/
theorem determines_mono (obs : P → H → O) {Ω Ω' : P → Prop} (hsub : ∀ p, Ω p → Ω' p)
    (S : H → Prop) (q : H → A) : Determines obs Ω S q → Determines obs Ω' S q :=
  fun hd h h' hs hs' hi => hd h h' hs hs' (indist_antitone obs hsub hi)

/-! ## §3 The least determining set -/

/-- p is decisive: it ALONE separates some relevant pair (a singleton conflict). -/
def Decisive (obs : P → H → O) (S : H → Prop) (q : H → A) (p : P) : Prop :=
  ∃ h h', S h ∧ S h' ∧ q h ≠ q h' ∧ obs p h ≠ obs p h' ∧
    ∀ p', obs p' h ≠ obs p' h' → p' = p

/-- Every determining set contains every decisive protocol. -/
theorem decisive_necessary (obs : P → H → O) (S : H → Prop) (q : H → A)
    {Ω : P → Prop} (hd : Determines obs Ω S q) : ∀ p, Decisive obs S q p → Ω p := by
  intro p ⟨h, h', hs, hs', hq, _, honly⟩
  obtain ⟨p', hΩ, hne⟩ := (duality obs Ω S q).mp hd h h' hs hs' hq
  rw [honly p' hne] at hΩ
  exact hΩ

/-- Theorem 4 (least determining set). A least determining set exists iff the
    decisive protocols determine q — and then it IS the set of decisive
    protocols. So uniqueness of the minimal representation / experiment plan /
    test suite is equivalent to: every relevant pair is split by some
    individually decisive protocol. -/
theorem least_iff (obs : P → H → O) (S : H → Prop) (q : H → A) :
    (∃ L : P → Prop, Determines obs L S q ∧ ∀ Ω, Determines obs Ω S q → ∀ p, L p → Ω p) ↔
    Determines obs (Decisive obs S q) S q := by
  constructor
  · intro ⟨L, hL, hleast⟩
    -- every p ∈ L is decisive; otherwise P \ {p} would still determine q
    have hsub : ∀ p, L p → Decisive obs S q p := by
      intro p hp
      apply Classical.byContradiction
      intro hnd
      have hdet : Determines obs (fun p' => p' ≠ p) S q := by
        apply (duality obs _ S q).mpr
        intro h h' hs hs' hq
        obtain ⟨p₀, _, hne₀⟩ := (duality obs L S q).mp hL h h' hs hs' hq
        apply Classical.byContradiction
        intro hnone
        -- then p is the only protocol separating h, h': p is decisive
        apply hnd
        refine ⟨h, h', hs, hs', hq, ?_, ?_⟩
        · have : p₀ = p := by
            apply Classical.byContradiction
            intro hneq; exact hnone ⟨p₀, hneq, hne₀⟩
          rw [← this]; exact hne₀
        · intro p' hne'
          apply Classical.byContradiction
          intro hneq; exact hnone ⟨p', hneq, hne'⟩
      exact (hleast _ hdet p hp) rfl
    exact determines_mono obs hsub S q hL
  · intro hN
    exact ⟨Decisive obs S q, hN, fun Ω hΩ => decisive_necessary obs S q hΩ⟩

/-! ## §4 Realizability: planning is exactly hitting set -/

/-- Theorem 5. Every family of conflict sets is realized by some frame: for any
    family E : ι → (P → Prop) there is a frame and query whose determining sets
    are exactly the transversals of E. Hence choosing a minimum set of
    measurements / experiments / features is, in general, exactly the
    minimum-hitting-set problem. -/
theorem realizable {ι : Type u} (E : ι → P → Prop) (Ω : P → Prop) :
    let obs : P → Option ι → Prop := fun p h => match h with
      | none => False
      | some i => E i p
    let q : Option ι → Bool := fun h => h.isSome
    Determines obs Ω (fun _ => True) q ↔ ∀ i, ∃ p, Ω p ∧ E i p := by
  intro obs q
  rw [duality]
  constructor
  · intro hh i
    obtain ⟨p, hp, hne⟩ := hh none (some i) trivial trivial (by simp [q])
    refine ⟨p, hp, ?_⟩
    apply Classical.byContradiction
    intro hn
    apply hne
    simp only [obs]
    exact propext ⟨False.elim, fun h => hn h⟩
  · intro hall h h' _ _ hq
    cases h with
    | none =>
        cases h' with
        | none => exact absurd rfl hq
        | some j =>
            obtain ⟨p, hp, he⟩ := hall j
            refine ⟨p, hp, ?_⟩
            intro heq
            have : obs p (some j) := he
            rw [← heq] at this
            exact this
    | some i =>
        cases h' with
        | none =>
            obtain ⟨p, hp, he⟩ := hall i
            refine ⟨p, hp, ?_⟩
            intro heq
            have : obs p (some i) := he
            rw [heq] at this
            exact this
        | some j => exact absurd rfl hq

/-! ## §5 Determinacy-gated inquiry -/

/-- Survivors: hypotheses in S consistent (in Ω) with the true world h⋆. -/
def Survivors (obs : P → H → O) (Ω : P → Prop) (S : H → Prop) (hstar : H) (h : H) : Prop :=
  S h ∧ Indist obs Ω h hstar

/-- Theorem 6a (soundness). If the truth is among the candidates and the agent
    answers only when all survivors agree, its answer is the true one. -/
theorem gated_sound (obs : P → H → O) (Ω : P → Prop) (S : H → Prop) (q : H → A)
    {hstar : H} (hin : S hstar) (a : A)
    (hagree : ∀ h, Survivors obs Ω S hstar h → q h = a) : q hstar = a :=
  hagree hstar ⟨hin, fun _ _ => rfl⟩

/-- Theorem 6b (completeness). If Ω determines q on S, survivors always agree. -/
theorem gated_complete (obs : P → H → O) (Ω : P → Prop) (S : H → Prop) (q : H → A)
    (hd : Determines obs Ω S q) {hstar : H} (hin : S hstar) :
    ∀ h, Survivors obs Ω S hstar h → q h = q hstar :=
  fun h ⟨hs, hi⟩ => hd h hstar hs hin hi

/-- Theorem 6c (no flip). In the exact regime, gaining protocols never changes
    an answer already given; it can only resolve an abstention. Retractions in
    practice therefore signal a failed closed world or statistical error. -/
theorem no_flip (obs : P → H → O) {Ω Ω' : P → Prop} (hsub : ∀ p, Ω p → Ω' p)
    (S : H → Prop) (q : H → A) (hstar : H) (a : A)
    (hagree : ∀ h, Survivors obs Ω S hstar h → q h = a) :
    ∀ h, Survivors obs Ω' S hstar h → q h = a :=
  fun h ⟨hs, hi⟩ => hagree h ⟨hs, indist_antitone obs hsub hi⟩

/-- Theorem 6d (the closed world is necessary). Without it, a gated agent can
    answer wrongly: soundness genuinely depends on the premise the ledger
    records as a named condition. -/
theorem closed_world_necessary :
    ∃ (obs : Unit → Bool → Bool) (S : Bool → Prop) (q : Bool → Bool) (hstar : Bool),
      ¬ S hstar ∧ (∀ h, Survivors obs (fun _ => True) S hstar h → q h = false) ∧ q hstar ≠ false :=
  ⟨fun _ _ => true, fun h => h = false, fun h => h, true,
   by simp, fun h ⟨hs, _⟩ => by simp [hs], by simp⟩

/-- Theorem 7 (underdetermination). If two candidates are Ω-indistinguishable
    but differ on q (e.g. "a hidden entity exists"), then every procedure that
    uses only Ω-observations is wrong about q on one of them. -/
theorem underdetermination (obs : P → H → O) (Ω : P → Prop) (q : H → A) {h₁ h₂ : H}
    (hi : Indist obs Ω h₁ h₂) (hq : q h₁ ≠ q h₂)
    (g : H → A) (hg : ∀ h h', Indist obs Ω h h' → g h = g h') :
    g h₁ ≠ q h₁ ∨ g h₂ ≠ q h₂ := by
  apply Classical.byContradiction
  intro hboth
  have e1 : g h₁ = q h₁ := Classical.byContradiction fun hn => hboth (Or.inl hn)
  have e2 : g h₂ = q h₂ := Classical.byContradiction fun hn => hboth (Or.inr hn)
  exact hq (e1.symm.trans ((hg h₁ h₂ hi).trans e2))

/-! ## §6 The warrant calculus: weakest-link combination is optimal -/

section Warrants
variable {M T C : Type u} (le : M → M → Prop) (tle : T → T → Prop)

/-- A warrant: method basis, trusted base, open conditions (all as sets). -/
structure Warrant (M T C : Type u) where
  basis : M → Prop
  trust : T → Prop
  conds : C → Prop

/-- w ⪰ w' (w is at least as strong): each of w's method links dominates some
    link of w'; each of w's trusted components is at least as trustworthy as
    some component of w'; w has no condition w' lacks. `le a b` reads "b is at
    least as strong as a"; `tle s t` reads "t is at least as trustworthy as s". -/
def Stronger (w w' : Warrant M T C) : Prop :=
  (∀ a, w.basis a → ∃ b, w'.basis b ∧ le b a) ∧
  (∀ t, w.trust t → ∃ s, w'.trust s ∧ tle s t) ∧
  (∀ c, w.conds c → w'.conds c)

/-- Combination for a claim resting on two others: union of everything. -/
def join (w w' : Warrant M T C) : Warrant M T C :=
  ⟨fun a => w.basis a ∨ w'.basis a, fun t => w.trust t ∨ w'.trust t, fun c => w.conds c ∨ w'.conds c⟩

theorem stronger_refl (hle : ∀ a, le a a) (htle : ∀ t, tle t t) (w : Warrant M T C) :
    Stronger le tle w w :=
  ⟨fun a ha => ⟨a, ha, hle a⟩, fun t ht => ⟨t, ht, htle t⟩, fun _ hc => hc⟩

theorem stronger_trans (hle : ∀ a b c, le a b → le b c → le a c)
    (htle : ∀ a b c, tle a b → tle b c → tle a c) {w₁ w₂ w₃ : Warrant M T C} :
    Stronger le tle w₁ w₂ → Stronger le tle w₂ w₃ → Stronger le tle w₁ w₃ := by
  intro ⟨b12, t12, c12⟩ ⟨b23, t23, c23⟩
  refine ⟨?_, ?_, fun c hc => c23 c (c12 c hc)⟩
  · intro a ha
    obtain ⟨b, hb, hba⟩ := b12 a ha
    obtain ⟨d, hd, hdb⟩ := b23 b hb
    exact ⟨d, hd, hle d b a hdb hba⟩
  · intro t ht
    obtain ⟨s, hs, hst⟩ := t12 t ht
    obtain ⟨r, hr, hrs⟩ := t23 s hs
    exact ⟨r, hr, htle r s t hrs hst⟩

/-- Theorem 8 (optimality of weakest-link). The combined warrant is (i) no
    stronger than either support, and (ii) the STRONGEST warrant with that
    property: any warrant below both supports is below the combination. So the
    ledger's rule never overstates, and never understates more than necessary. -/
theorem join_is_greatest_lower_bound (hle : ∀ a, le a a) (htle : ∀ t, tle t t)
    (w₁ w₂ : Warrant M T C) :
    Stronger le tle w₁ (join w₁ w₂) ∧ Stronger le tle w₂ (join w₁ w₂) ∧
    ∀ z, Stronger le tle w₁ z → Stronger le tle w₂ z → Stronger le tle (join w₁ w₂) z := by
  refine ⟨⟨fun a ha => ⟨a, Or.inl ha, hle a⟩, fun t ht => ⟨t, Or.inl ht, htle t⟩, fun c hc => Or.inl hc⟩,
          ⟨fun a ha => ⟨a, Or.inr ha, hle a⟩, fun t ht => ⟨t, Or.inr ht, htle t⟩, fun c hc => Or.inr hc⟩, ?_⟩
  intro z ⟨b1, t1, c1⟩ ⟨b2, t2, c2⟩
  refine ⟨?_, ?_, ?_⟩
  · intro a ha; cases ha with
    | inl h => exact b1 a h
    | inr h => exact b2 a h
  · intro t ht; cases ht with
    | inl h => exact t1 t h
    | inr h => exact t2 t h
  · intro c hc; cases hc with
    | inl h => exact c1 c h
    | inr h => exact c2 c h

end Warrants


/-! ## §7 Canonicity: the observation profile is the universal representation -/

/-- Theorem 10 (canonicity). A query is knowable under Ω (determined on all of H)
    iff it factors through the Ω-observation profile h ↦ (p ↦ obs p h). The
    profile is the canonical semantic object S_Ω = H/≡_Ω of charter Layer G,
    relative to Ω; every knowable query is a function of it. -/
theorem canonical_factorization (obs : P → H → O) (Ω : P → Prop) (q : H → A) [Nonempty A] :
    Determines obs Ω (fun _ => True) q ↔
    ∃ F : ((p : P) → Ω p → O) → A, ∀ h, q h = F (fun p _ => obs p h) := by
  constructor
  · intro hd
    refine ⟨fun v => @dite _ (∃ x, (fun p (_ : Ω p) => obs p x) = v) (Classical.propDecidable _)
                       (fun hv => q (Classical.choose hv)) (fun _ => Classical.choice inferInstance), ?_⟩
    intro h
    have hv : ∃ x, (fun p (_ : Ω p) => obs p x) = (fun p _ => obs p h) := ⟨h, rfl⟩
    dsimp only
    rw [dif_pos hv]
    have hx := Classical.choose_spec hv
    apply hd h (Classical.choose hv) trivial trivial
    intro p hp
    have := congrFun (congrFun hx p) hp
    exact this.symm
  · intro ⟨F, hF⟩ h h' _ _ hi
    rw [hF h, hF h']
    have : (fun p (_ : Ω p) => obs p h) = (fun p _ => obs p h') := by
      funext p hp; exact hi p hp
    rw [this]

/-! ## §8 Minimal representations can fail to exist -/

/-- point update of an assignment -/
def upd (x : Nat → Bool) (n : Nat) (b : Bool) : Nat → Bool := fun i => if i = n then b else x i

/-- the tail query: "the signal is eventually always on" -/
def EventuallyOn (x : Nat → Bool) : Prop := ∃ N, ∀ n, N ≤ n → x n = true

theorem eventuallyOn_upd (x : Nat → Bool) (k : Nat) (b : Bool) :
    EventuallyOn (upd x k b) = EventuallyOn x := by
  apply propext
  constructor
  · intro ⟨N, hN⟩
    refine ⟨max N (k + 1), fun n hn => ?_⟩
    have h1 : N ≤ n := Nat.le_trans (Nat.le_max_left _ _) hn
    have h2 : n ≠ k := by have := Nat.le_trans (Nat.le_max_right N (k+1)) hn; omega
    have := hN n h1
    simp [upd, h2] at this
    exact this
  · intro ⟨N, hN⟩
    refine ⟨max N (k + 1), fun n hn => ?_⟩
    have h1 : N ≤ n := Nat.le_trans (Nat.le_max_left _ _) hn
    have h2 : n ≠ k := by have := Nat.le_trans (Nat.le_max_right N (k+1)) hn; omega
    simp [upd, h2]
    exact hN n h1

/-- Theorem 9 (no minimal representation). In the frame of infinite binary
    signals observed one coordinate at a time, the tail query "eventually on" is
    determined by full observational power, yet (i) no protocol is decisive and
    (ii) every determining set stays determining after removing any one
    protocol — so NO minimal determining set exists. The charter anticipated
    non-unique minimal representations; existence itself can fail. -/
theorem no_minimal_representation :
    let obs : Nat → (Nat → Bool) → Bool := fun p x => x p
    Determines obs (fun _ => True) (fun _ => True) EventuallyOn ∧
    (∀ p, ¬ Decisive obs (fun _ => True) EventuallyOn p) ∧
    (∀ Ω : Nat → Prop, Determines obs Ω (fun _ => True) EventuallyOn →
       ∀ p, Determines obs (fun p' => Ω p' ∧ p' ≠ p) (fun _ => True) EventuallyOn) := by
  intro obs
  refine ⟨?_, ?_, ?_⟩
  · intro x y _ _ hi
    have : x = y := funext fun n => hi n trivial
    rw [this]
  · intro p ⟨x, y, _, _, hq, _, honly⟩
    apply hq
    -- x and y differ only at p, so y = upd x p (y p)
    have hy : y = upd x p (y p) := by
      funext n
      by_cases hn : n = p
      · simp [upd, hn]
      · simp only [upd, hn, if_false]
        apply Classical.byContradiction
        intro hne
        exact hn (honly n (fun h => hne h.symm))
    rw [hy, eventuallyOn_upd]
  · intro Ω hd p x y _ _ hi
    have hxy : EventuallyOn x = EventuallyOn (upd y p (x p)) := by
      apply hd x (upd y p (x p)) trivial trivial
      intro n hn
      by_cases hnp : n = p
      · simp [obs, upd, hnp]
      · simp only [obs, upd, hnp, if_false]
        exact hi n ⟨hn, hnp⟩
    rw [hxy, eventuallyOn_upd]


/-! ## §9 The finitary dichotomy: finite dependence ⇒ a canonical minimal set -/

/-- discrete intermediate value: a change along a path happens at some step -/
theorem step_change {B : Type x} (g : Nat → B) : ∀ m, g 0 ≠ g m → ∃ k, k < m ∧ g k ≠ g (k + 1) := by
  intro m
  induction m with
  | zero => intro h; exact absurd rfl h
  | succ m ih =>
      intro h
      by_cases hm : g 0 = g m
      · exact ⟨m, Nat.lt_succ_self m, fun he => h (hm.trans he)⟩
      · obtain ⟨k, hk, hne⟩ := ih hm
        exact ⟨k, Nat.lt_succ_of_lt hk, hne⟩

/-- hybrid of x and y: y below k, x from k on -/
def hybrid (x y : Nat → Bool) (k : Nat) : Nat → Bool := fun i => if i < k then y i else x i

/-- Theorem 11 (finitary uniqueness). If q depends only on coordinates < n, then
    every relevant pair is separated by a DECISIVE coordinate; by Theorem 4 the
    decisive coordinates form the least determining set — the unique minimal
    sufficient representation. With Theorem 9 this is a dichotomy: finite
    dependence gives a canonical minimal representation; tail dependence can
    leave none at all. (Spike 01's full-domain uniqueness is the case A = Bool.) -/
theorem finitary_least (q : (Nat → Bool) → A) (n : Nat)
    (hdep : ∀ x y, (∀ i, i < n → x i = y i) → q x = q y) :
    let obs : Nat → (Nat → Bool) → Bool := fun p x => x p
    Determines obs (Decisive obs (fun _ => True) q) (fun _ => True) q := by
  intro obs
  apply (duality obs _ _ q).mpr
  intro x y _ _ hq
  -- walk from x (k = 0) to y (k = n) one coordinate at a time
  have h0 : q (hybrid x y 0) = q x := by
    have e : hybrid x y 0 = x := by funext i; simp [hybrid]
    rw [e]
  have hn : q (hybrid x y n) = q y := by
    apply hdep; intro i hi; simp [hybrid, hi]
  have hne : q (hybrid x y 0) ≠ q (hybrid x y n) := by
    rw [h0, hn]; exact hq
  obtain ⟨k, _, hk⟩ := step_change (fun k => q (hybrid x y k)) n hne
  -- consecutive hybrids differ at most at coordinate k
  have honly : ∀ p', hybrid x y k p' ≠ hybrid x y (k + 1) p' → p' = k := by
    intro p' hp'
    apply Classical.byContradiction
    intro hpk
    apply hp'
    simp only [hybrid]
    by_cases h1 : p' < k
    · have h2 : p' < k + 1 := by omega
      simp [h1, h2]
    · have h2 : ¬ p' < k + 1 := by omega
      simp [h1, h2]
  have hdiff : hybrid x y k k ≠ hybrid x y (k + 1) k := by
    intro heq
    apply hk
    show q (hybrid x y k) = q (hybrid x y (k + 1))
    congr 1
    funext i
    by_cases hi : i = k
    · rw [hi]; exact heq
    · apply Classical.byContradiction
      intro hne'
      exact hi (honly i hne')
  refine ⟨k, ⟨hybrid x y k, hybrid x y (k + 1), trivial, trivial, hk, hdiff, honly⟩, ?_⟩
  -- and x, y themselves differ at k
  intro heq
  apply hdiff
  simp only [hybrid, Nat.lt_irrefl, Nat.lt_succ_self, if_true, if_false]
  exact heq

end PFT

/-! ## §10 Learning rules as observational powers -/

namespace PFT

universe u1 u2 u3

/-- Theorem 12 (task-blindness). Let training update a pair (s, o): s is the part
    of the parameters whose update rule observes only s itself (no task signal),
    while o may observe everything including the task t. Then after any number of
    steps s is the same for every task. A layer trained by a rule that cannot
    observe the task carries no information about it. -/
theorem task_blind {S : Type u1} {O : Type u2} {T : Type u3}
    (us : S → S) (uo : T → S → O → O) (s₀ : S) (o₀ : O) (t₁ t₂ : T) :
    ∀ k : Nat, (Nat.rec (motive := fun _ => S × O) (s₀, o₀) (fun _ p => (us p.1, uo t₁ p.1 p.2)) k).1 =
               (Nat.rec (motive := fun _ => S × O) (s₀, o₀) (fun _ p => (us p.1, uo t₂ p.1 p.2)) k).1 := by
  intro k
  induction k with
  | zero => rfl
  | succ k ih => simp only [ih]

end PFT

namespace PFT

/-- Theorem 13 (symmetry gap, core). A quantity that is unchanged when a unit's
    sign is flipped cannot equal one that changes sign, unless the latter is zero.
    Applied to learning rules: every monomial in which a hidden index occurs an
    even number of times is unchanged by flipping that unit, so no combination
    of them equals the error-broadcast term, which changes sign. -/
theorem even_span_excludes_odd (f g : Int → Int)
    (hf : ∀ y, f (-y) = f y) (hg : ∀ y, g (-y) = -g y) (h : ∀ y, f y = g y) : ∀ y, g y = 0 := by
  intro y
  have h1 := h y
  have h2 := h (-y)
  rw [hf y, hg y] at h2
  omega

/-- Flip unit `0` in a hidden-layer vector. -/
def flip0 (v : Nat → Int) : Nat → Int := fun i => if i = 0 then -v 0 else v i

/-- Sum of `v` over indices `< d`. -/
def sumVec (v : Nat → Int) : Nat → Int
  | 0 => 0
  | d + 1 => sumVec v d + v d

theorem sumVec_flip0 (v : Nat → Int) :
    ∀ d, 0 < d → sumVec (flip0 v) d = sumVec v d - 2 * v 0 := by
  intro d hd
  induction d with
  | zero => omega
  | succ d ih =>
      cases d with
      | zero => simp [sumVec, flip0]; omega
      | succ k =>
          have ih' := ih (by omega)
          change sumVec (flip0 v) (k + 1) + flip0 v (k + 1) = sumVec v (k + 1) + v (k + 1) - 2 * v 0
          rw [ih']
          have hne : k + 1 ≠ 0 := by omega
          simp [flip0, hne]
          omega

/-- Multi-unit symmetry gap (Proposition 14): any function `f` of a hidden
    vector invariant under flipping unit `0` cannot equal `E * sumVec v d`
    when `d > 0` and `E ≠ 0`. -/
theorem multi_unit_symmetry_gap (f : (Nat → Int) → Int) (E : Int) (d : Nat)
    (hd : 0 < d) (hE : E ≠ 0)
    (hinv : ∀ v, f (flip0 v) = f v) :
    ¬ (∀ v, f v = E * sumVec v d) := by
  intro h
  let v : Nat → Int := fun i => if i = 0 then 1 else 0
  have h1 := h v
  have h2 := h (flip0 v)
  rw [hinv v, h1, sumVec_flip0 v d hd] at h2
  have hv0 : v 0 = 1 := rfl
  rw [hv0] at h2
  have hmul : E * (sumVec v d - 2 * 1) = E * sumVec v d - 2 * E := by
    rw [Int.mul_sub]; simp [Int.mul_comm]
  rw [hmul] at h2
  omega

end PFT

/-! ## §11 Compositional frames (C4) -/

namespace PFT

section Compositional
universe u1 u2 v1 v2 w1 w2

def prodObs (obs₁ : P₁ → H₁ → O₁) (obs₂ : P₂ → H₂ → O₂) :
    Sum P₁ P₂ → (H₁ × H₂) → Sum O₁ O₂
  | Sum.inl p₁, (h₁, _) => Sum.inl (obs₁ p₁ h₁)
  | Sum.inr p₂, (_, h₂) => Sum.inr (obs₂ p₂ h₂)

def prodPow (Ω₁ : P₁ → Prop) (Ω₂ : P₂ → Prop) : Sum P₁ P₂ → Prop
  | Sum.inl p₁ => Ω₁ p₁
  | Sum.inr p₂ => Ω₂ p₂

theorem prod_indist (obs₁ : P₁ → H₁ → O₁) (obs₂ : P₂ → H₂ → O₂)
    (Ω₁ : P₁ → Prop) (Ω₂ : P₂ → Prop) (h₁ h₁' : H₁) (h₂ h₂' : H₂) :
    Indist (prodObs obs₁ obs₂) (prodPow Ω₁ Ω₂) (h₁, h₂) (h₁', h₂') ↔
      Indist obs₁ Ω₁ h₁ h₁' ∧ Indist obs₂ Ω₂ h₂ h₂' := by
  constructor
  · intro h
    refine ⟨fun p₁ hp₁ => ?_, fun p₂ hp₂ => ?_⟩
    · have := h (Sum.inl p₁) hp₁
      exact Sum.inl.inj this
    · have := h (Sum.inr p₂) hp₂
      exact Sum.inr.inj this
  · intro ⟨h1, h2⟩ p hp
    cases p with
    | inl p₁ => exact congrArg Sum.inl (h1 p₁ hp)
    | inr p₂ => exact congrArg Sum.inr (h2 p₂ hp)

theorem prod_determines (obs₁ : P₁ → H₁ → O₁) (obs₂ : P₂ → H₂ → O₂)
    (Ω₁ : P₁ → Prop) (Ω₂ : P₂ → Prop) (S₁ : H₁ → Prop) (S₂ : H₂ → Prop)
    (q₁ : H₁ → A₁) (q₂ : H₂ → A₂)
    (hd₁ : Determines obs₁ Ω₁ S₁ q₁) (hd₂ : Determines obs₂ Ω₂ S₂ q₂) :
    Determines (prodObs obs₁ obs₂) (prodPow Ω₁ Ω₂)
      (fun h => S₁ h.1 ∧ S₂ h.2) (fun h => (q₁ h.1, q₂ h.2)) := by
  intro ⟨h₁, h₂⟩ ⟨h₁', h₂'⟩ ⟨hs₁, hs₂⟩ ⟨hs₁', hs₂'⟩ hi
  obtain ⟨hi₁, hi₂⟩ := (prod_indist obs₁ obs₂ Ω₁ Ω₂ h₁ h₁' h₂ h₂').mp hi
  exact Prod.ext (hd₁ h₁ h₁' hs₁ hs₁' hi₁) (hd₂ h₂ h₂' hs₂ hs₂' hi₂)

theorem prod_decisive_left (obs₁ : P₁ → H₁ → O₁) (obs₂ : P₂ → H₂ → O₂)
    (S₁ : H₁ → Prop) (S₂ : H₂ → Prop) (q₁ : H₁ → A₁) (q₂ : H₂ → A₂)
    {p₁ : P₁} (hdec : Decisive obs₁ S₁ q₁ p₁) {h₂₀ : H₂} (hs₂ : S₂ h₂₀) :
    Decisive (prodObs obs₁ obs₂) (fun h => S₁ h.1 ∧ S₂ h.2) (fun h => (q₁ h.1, q₂ h.2)) (Sum.inl p₁) := by
  obtain ⟨h₁, h₁', hs₁, hs₁', hq, hdiff, honly⟩ := hdec
  refine ⟨(h₁, h₂₀), (h₁', h₂₀), ⟨hs₁, hs₂⟩, ⟨hs₁', hs₂⟩, ?_, ?_, ?_⟩
  · intro heq
    exact hq (congrArg Prod.fst heq)
  · intro heq
    exact hdiff (Sum.inl.inj heq)
  · intro p' hp'
    cases p' with
    | inl p₁' =>
        have : obs₁ p₁' h₁ ≠ obs₁ p₁' h₁' := fun heq => hp' (congrArg Sum.inl heq)
        exact congrArg Sum.inl (honly p₁' this)
    | inr p₂' =>
        exact False.elim (hp' rfl)

end Compositional

end PFT

/-! ## §12 Limit representations and ε-determinacy (C2 / H-F) -/

namespace PFT

def EpsDetermines (obs : P → H → O) (Ω : P → Prop) (S : H → Prop) (q : H → A)
    (err : H → H → Nat) (tol : Nat) : Prop :=
  ∀ h₁ h₂, S h₁ → S h₂ → Indist obs Ω h₁ h₂ → q h₁ ≠ q h₂ → err h₁ h₂ ≤ tol

theorem eps_determines_mono (obs : P → H → O) {Ω Ω' : P → Prop}
    (hsub : ∀ p, Ω p → Ω' p) (S : H → Prop) (q : H → A) (err : H → H → Nat) (tol : Nat)
    (hd : EpsDetermines obs Ω S q err tol) :
    EpsDetermines obs Ω' S q err tol :=
  fun h₁ h₂ hs₁ hs₂ hi hq => hd h₁ h₂ hs₁ hs₂ (indist_antitone obs hsub hi) hq

def Stabilizes (N : Nat) (x : Nat → Bool) : Prop :=
  (∀ i, N ≤ i → x i = true) ∨ (∀ i, N ≤ i → x i = false)

theorem eventuallyOn_stabilized (N : Nat) (x : Nat → Bool) (hs : Stabilizes N x) :
    EventuallyOn x ↔ x N = true := by
  cases hs with
  | inl ht =>
      have hev : EventuallyOn x := ⟨N, fun k hk => ht k hk⟩
      have hxN : x N = true := ht N (Nat.le_refl N)
      exact ⟨fun _ => hxN, fun _ => hev⟩
  | inr hf =>
      have hnev : ¬ EventuallyOn x := by
        rintro ⟨M, hM⟩
        have h1 := hM (max N M) (Nat.le_max_right N M)
        have h2 := hf (max N M) (Nat.le_max_left N M)
        rw [h1] at h2
        cases h2
      have hxN : x N = false := hf N (Nat.le_refl N)
      exact ⟨fun hev => absurd hev hnev, fun h => by rw [hxN] at h; cases h⟩

theorem prefix_determines_stabilized (N : Nat) :
    Determines (fun p x => x p) (fun k => k < N + 1) (Stabilizes N) EventuallyOn := by
  intro x y hx hy hi
  apply propext
  have hxy : x N = y N := hi N (Nat.lt_succ_self N)
  rw [eventuallyOn_stabilized N x hx, eventuallyOn_stabilized N y hy, hxy]

end PFT

/-! ## §13 Adaptive inquiry trees and hitting-set lower bound (C3) -/

namespace PFT

section Adaptive
universe u1 u2 u3 u4

inductive QueryTree (P : Type u1) (O : Type u2) (A : Type u3) : Type (max u1 u2 u3) where
  | leaf : A → QueryTree P O A
  | ask : P → (O → QueryTree P O A) → QueryTree P O A

def evalTree {P : Type u1} {O : Type u2} {A : Type u3} {H : Type u4}
    (obs : P → H → O) : QueryTree P O A → H → A
  | QueryTree.leaf a, _ => a
  | QueryTree.ask p k, h => evalTree obs (k (obs p h)) h

def UsesOnly {P : Type u1} {O : Type u2} {A : Type u3}
    (Ω : P → Prop) : QueryTree P O A → Prop
  | QueryTree.leaf _ => True
  | QueryTree.ask p k => Ω p ∧ ∀ o, UsesOnly Ω (k o)

theorem evalTree_indist {P : Type u1} {O : Type u2} {A : Type u3} {H : Type u4}
    (obs : P → H → O) (Ω : P → Prop) :
    ∀ (t : QueryTree P O A), UsesOnly Ω t →
      ∀ h₁ h₂, Indist obs Ω h₁ h₂ → evalTree obs t h₁ = evalTree obs t h₂
  | QueryTree.leaf _, _, _, _, _ => rfl
  | QueryTree.ask p k, ⟨hp, hk⟩, h₁, h₂, hi => by
      simp only [evalTree]
      have hobs : obs p h₁ = obs p h₂ := hi p hp
      rw [hobs]
      exact evalTree_indist obs Ω (k (obs p h₂)) (hk (obs p h₂)) h₁ h₂ hi

theorem adaptive_uses_determining {P : Type u1} {O : Type u2} {A : Type u3} {H : Type u4}
    (obs : P → H → O) (Ω : P → Prop) (S : H → Prop)
    (q : H → A) (t : QueryTree P O A) (hu : UsesOnly Ω t)
    (hacc : ∀ h, S h → evalTree obs t h = q h) :
    Determines obs Ω S q := by
  intro h₁ h₂ hs₁ hs₂ hi
  rw [← hacc h₁ hs₁, ← hacc h₂ hs₂]
  exact evalTree_indist obs Ω t hu h₁ h₂ hi

end Adaptive

end PFT

/-! ## §14 Statistical gated soundness skeleton (C1) -/

namespace PFT

theorem statistical_gated_sound (EmpSurvivors : H → Prop) (q : H → A) (hstar : H) (a : A)
    (hkeep : EmpSurvivors hstar)
    (hagree : ∀ h, EmpSurvivors h → q h = a) :
    q hstar = a :=
  hagree hstar hkeep

def sumBudget (err : H → Nat) : List H → Nat
  | [] => 0
  | h :: hs => err h + sumBudget err hs

theorem union_bound_sum (err : H → Nat) (perCand : Nat) :
    ∀ hs : List H, (∀ h, h ∈ hs → err h ≤ perCand) → sumBudget err hs ≤ hs.length * perCand
  | [], _ => by simp [sumBudget]
  | h :: hs, hle => by
      have h1 : err h ≤ perCand := hle h (List.mem_cons_self h hs)
      have h2 : sumBudget err hs ≤ hs.length * perCand :=
        union_bound_sum err perCand hs (fun x hx => hle x (List.mem_cons_of_mem h hx))
      simp only [sumBudget, List.length_cons, Nat.succ_mul]
      omega

theorem err_le_sumBudget (err : H → Nat) (hstar : H) :
    ∀ hs : List H, hstar ∈ hs → err hstar ≤ sumBudget err hs
  | [], hmem => by simp at hmem
  | h :: hs, hmem => by
      simp only [List.mem_cons] at hmem
      cases hmem with
      | inl heq => subst heq; simp [sumBudget]
      | inr htail =>
          have ih := err_le_sumBudget err hstar hs htail
          simp only [sumBudget]
          omega

end PFT

/-! ## §12b General metric ε-limit representation (C2) -/

namespace PFT

def EpsDeterminesAns (obs : P → H → O) (Ω : P → Prop) (S : H → Prop)
    (q : H → A) (dist : A → A → Nat) (tol : Nat) : Prop :=
  ∀ h₁ h₂, S h₁ → S h₂ → Indist obs Ω h₁ h₂ → dist (q h₁) (q h₂) ≤ tol

theorem metric_eps_limit (obs : P → H → O) (Ω_seq : Nat → P → Prop)
    (S : H → Prop) (q : H → A) (dist : A → A → Nat)
    (hlim : ∀ tol, ∃ k, EpsDeterminesAns obs (Ω_seq k) S q dist tol) :
    ∀ h₁ h₂, S h₁ → S h₂ → Indist obs (fun p => ∃ k, Ω_seq k p) h₁ h₂ →
      dist (q h₁) (q h₂) = 0 := by
  intro h₁ h₂ hs₁ hs₂ hi
  obtain ⟨k, hk⟩ := hlim 0
  have hik : Indist obs (Ω_seq k) h₁ h₂ := fun p hp => hi p ⟨k, hp⟩
  exact Nat.eq_zero_of_le_zero (hk h₁ h₂ hs₁ hs₂ hik)

theorem metric_eps_limit_determines (obs : P → H → O) (Ω_seq : Nat → P → Prop)
    (S : H → Prop) (q : H → A) (dist : A → A → Nat)
    (hsep : ∀ a b, dist a b = 0 → a = b)
    (hlim : ∀ tol, ∃ k, EpsDeterminesAns obs (Ω_seq k) S q dist tol) :
    Determines obs (fun p => ∃ k, Ω_seq k p) S q :=
  fun h₁ h₂ hs₁ hs₂ hi => hsep (q h₁) (q h₂) (metric_eps_limit obs Ω_seq S q dist hlim h₁ h₂ hs₁ hs₂ hi)

end PFT

/-! ## §13b Quantitative adaptive protocol lower bound (C3) -/

namespace PFT

theorem adaptive_min_protocols_lb {P : Type u1} {O : Type u2} {A : Type u3} {H : Type u4}
    (obs : P → H → O) (used : List P) (S : H → Prop)
    (q : H → A) (t : QueryTree P O A) (hu : UsesOnly (fun p => p ∈ used) t)
    (hacc : ∀ h, S h → evalTree obs t h = q h)
    (k : Nat) (hlb : ∀ L : List P, Determines obs (fun p => p ∈ L) S q → k ≤ L.length) :
    k ≤ used.length :=
  hlb used (adaptive_uses_determining obs (fun p => p ∈ used) S q t hu hacc)

end PFT

/-! ## §15 Trust-indexed escalation optimality (C5) -/

namespace PFT

def claimGain (ratio : Int) (cost impact : C → Nat) (c : C) : Int :=
  (impact c : Int) - ratio * (cost c : Int)

def optPol (ratio : Int) (cost impact : C → Nat) (c : C) : Bool :=
  decide (0 < claimGain ratio cost impact c)

def totalGain (ratio : Int) (cost impact : C → Nat) (pol : C → Bool) : List C → Int
  | [] => 0
  | c :: cs => (if pol c then claimGain ratio cost impact c else 0) + totalGain ratio cost impact pol cs

theorem term_le_opt (ratio : Int) (cost impact : C → Nat) (pol : C → Bool) (c : C) :
    (if pol c then claimGain ratio cost impact c else 0) ≤
      (if optPol ratio cost impact c then claimGain ratio cost impact c else 0) := by
  unfold optPol
  by_cases hpos : 0 < claimGain ratio cost impact c
  · simp [hpos]
    cases pol c <;> simp <;> omega
  · simp [hpos]
    cases pol c <;> simp <;> omega

theorem threshold_escalation_optimal (ratio : Int) (cost impact : C → Nat)
    (pol : C → Bool) :
    ∀ cs : List C, totalGain ratio cost impact pol cs ≤ totalGain ratio cost impact (optPol ratio cost impact) cs
  | [] => by simp [totalGain]
  | c :: cs => by
      simp only [totalGain]
      have h1 := term_le_opt ratio cost impact pol c
      have h2 := threshold_escalation_optimal ratio cost impact pol cs
      omega

theorem threshold_escalation_unique_strict (ratio : Int) (cost impact : C → Nat)
    (pol : C → Bool) :
    ∀ cs : List C,
      totalGain ratio cost impact pol cs = totalGain ratio cost impact (optPol ratio cost impact) cs →
      ∀ c, c ∈ cs → claimGain ratio cost impact c ≠ 0 → pol c = optPol ratio cost impact c := by
  intro cs heq c hmem hnz
  induction cs with
  | nil => simp at hmem
  | cons x xs ih =>
      simp only [totalGain] at heq
      have h1 := term_le_opt ratio cost impact pol x
      have h2 := threshold_escalation_optimal ratio cost impact pol xs
      have hx_eq : (if pol x then claimGain ratio cost impact x else 0) =
          (if optPol ratio cost impact x then claimGain ratio cost impact x else 0) := by omega
      have hxs_eq : totalGain ratio cost impact pol xs =
          totalGain ratio cost impact (optPol ratio cost impact) xs := by omega
      simp only [List.mem_cons] at hmem
      cases hmem with
      | inl hcx =>
          subst hcx
          unfold optPol at hx_eq ⊢
          by_cases hpos : 0 < claimGain ratio cost impact c
          · simp [hpos] at hx_eq ⊢
            cases hpc : pol c
            · simp [hpc] at hx_eq; omega
            · rfl
          · simp [hpos] at hx_eq ⊢
            cases hpc : pol c
            · rfl
            · simp [hpc] at hx_eq; omega
      | inr htail =>
          exact ih hxs_eq htail

end PFT

/-! ## §16 Compositional profile-factor compilation (Gap 1 / H-G) -/

namespace PFT

section ProfileFactor
universe u1 u2 u3 u4

theorem profile_factor_compile {H₁ : Type u1} {H₂ : Type u2} {K : Type u3} {A : Type u4}
    (f : H₁ → H₂ → A) (π : H₁ → K) (pick : K → H₁)
    (hsec : ∀ h₁, π (pick (π h₁)) = π h₁)
    (hsep : ∀ h₁ h₁', π h₁ = π h₁' → ∀ h₂, f h₁ h₂ = f h₁' h₂) :
    let decode : K → H₂ → A := fun k h₂ => f (pick k) h₂
    ∀ h₁ h₂, decode (π h₁) h₂ = f h₁ h₂ := by
  intro decode h₁ h₂
  exact hsep (pick (π h₁)) h₁ (hsec h₁) h₂

end ProfileFactor

end PFT

/-! ## §13c Adaptive local hitting-set lower bound (Gap 4 / C3 / H-I) -/

namespace PFT

section AdaptiveTrace
universe u1 u2 u3 u4

def traceProtocols {P : Type u1} {O : Type u2} {A : Type u3} {H : Type u4}
    (obs : P → H → O) : QueryTree P O A → H → List P
  | QueryTree.leaf _, _ => []
  | QueryTree.ask p k, h => p :: traceProtocols obs (k (obs p h)) h

theorem adaptive_trace_discriminates {P : Type u1} {O : Type u2} {A : Type u3} {H : Type u4}
    (obs : P → H → O) :
    ∀ (t : QueryTree P O A) (h₁ h₂ : H),
      evalTree obs t h₁ ≠ evalTree obs t h₂ →
      ∃ p, p ∈ traceProtocols obs t h₁ ∧ obs p h₁ ≠ obs p h₂
  | QueryTree.leaf _, _, _, hne => absurd rfl hne
  | QueryTree.ask p k, h₁, h₂, hne => by
      by_cases hobs : obs p h₁ = obs p h₂
      · simp only [evalTree] at hne
        rw [hobs] at hne
        obtain ⟨p', hp', hdiff⟩ := adaptive_trace_discriminates obs (k (obs p h₂)) h₁ h₂ hne
        refine ⟨p', List.mem_cons_of_mem p ?_, hdiff⟩
        simpa [traceProtocols, hobs] using hp'
      · exact ⟨p, List.mem_cons_self p _, hobs⟩

theorem adaptive_local_hitting_lb {P : Type u1} {O : Type u2} {A : Type u3} {H : Type u4}
    (obs : P → H → O) (S : H → Prop) (q : H → A) (t : QueryTree P O A)
    (hacc : ∀ h, S h → evalTree obs t h = q h)
    {h₁ h₂ : H} (hs₁ : S h₁) (hs₂ : S h₂) (hq : q h₁ ≠ q h₂) :
    ∃ p, p ∈ traceProtocols obs t h₁ ∧ obs p h₁ ≠ obs p h₂ := by
  apply adaptive_trace_discriminates obs t h₁ h₂
  rw [hacc h₁ hs₁, hacc h₂ hs₂]
  exact hq

end AdaptiveTrace

end PFT

/-! ## §14b Cross-multiplied union-bound budget (Gap 4 / C1) -/

namespace PFT

theorem uniform_budget_bound (err : H → Nat) (totalBudget : Nat) (hs : List H)
    (hle : ∀ h, h ∈ hs → err h * hs.length ≤ totalBudget) :
    sumBudget err hs ≤ totalBudget := by
  have hmul : sumBudget err hs * hs.length ≤ hs.length * totalBudget := by
    have : ∀ l : List H, (∀ h, h ∈ l → err h * hs.length ≤ totalBudget) →
        sumBudget err l * hs.length ≤ l.length * totalBudget := by
      intro l hl
      induction l with
      | nil => simp [sumBudget]
      | cons x xs ih =>
          have hx := hl x (List.mem_cons_self x xs)
          have hxs := ih (fun y hy => hl y (List.mem_cons_of_mem x hy))
          simp only [sumBudget, Nat.add_mul, List.length_cons, Nat.succ_mul]
          omega
    exact this hs hle
  cases hlen : hs.length with
  | zero =>
      have : hs = [] := List.length_eq_zero.mp hlen
      subst this
      simp [sumBudget]
  | succ m =>
      rw [hlen] at hmul
      exact Nat.le_of_mul_le_mul_left (by simpa [Nat.mul_comm] using hmul) (Nat.succ_pos m)

end PFT

/-! ## §17 Quantitative Protocol-Frame Morphisms, Composition & Lossy Obstruction (P071) -/

namespace PFT

section Morphisms
universe u1 u2 u3 u4 u5 u6 u7 u8 u9

/-- Functorial protocol-frame morphism (generalizing trace-relating translations
    from Abate et al. to protocol frames): maps source hypotheses `fH : H₁ → H₂`
    and back-translates target protocols `fP : P₂ → P₁` with observation map `fO`. -/
structure FrameHom (H₁ : Type u1) (P₁ : Type u2) (O₁ : Type u3)
    (H₂ : Type u4) (P₂ : Type u5) (O₂ : Type u6)
    (obs₁ : P₁ → H₁ → O₁) (obs₂ : P₂ → H₂ → O₂)
    (Ω₁ : P₁ → Prop) (Ω₂ : P₂ → Prop) where
  fH : H₁ → H₂
  fP : P₂ → P₁
  fO : O₁ → O₂
  power_compat : ∀ p₂, Ω₂ p₂ → Ω₁ (fP p₂)
  comm : ∀ p₂ h₁, obs₂ p₂ (fH h₁) = fO (obs₁ (fP p₂) h₁)

def FrameHom.id (obs : P → H → O) (Ω : P → Prop) :
    FrameHom H P O H P O obs obs Ω Ω where
  fH := _root_.id
  fP := _root_.id
  fO := _root_.id
  power_compat := fun _ hp => hp
  comm := fun _ _ => rfl

def FrameHom.comp
    {H₁ : Type u1} {P₁ : Type u2} {O₁ : Type u3}
    {H₂ : Type u4} {P₂ : Type u5} {O₂ : Type u6}
    {H₃ : Type u7} {P₃ : Type u8} {O₃ : Type u9}
    {obs₁ : P₁ → H₁ → O₁} {obs₂ : P₂ → H₂ → O₂} {obs₃ : P₃ → H₃ → O₃}
    {Ω₁ : P₁ → Prop} {Ω₂ : P₂ → Prop} {Ω₃ : P₃ → Prop}
    (g : FrameHom H₂ P₂ O₂ H₃ P₃ O₃ obs₂ obs₃ Ω₂ Ω₃)
    (f : FrameHom H₁ P₁ O₁ H₂ P₂ O₂ obs₁ obs₂ Ω₁ Ω₂) :
    FrameHom H₁ P₁ O₁ H₃ P₃ O₃ obs₁ obs₃ Ω₁ Ω₃ where
  fH := g.fH ∘ f.fH
  fP := f.fP ∘ g.fP
  fO := g.fO ∘ f.fO
  power_compat := fun p₃ hp₃ => f.power_compat _ (g.power_compat p₃ hp₃)
  comm := fun p₃ h₁ => by
    change obs₃ p₃ (g.fH (f.fH h₁)) = g.fO (f.fO (obs₁ (f.fP (g.fP p₃)) h₁))
    rw [g.comm p₃ (f.fH h₁), f.comm (g.fP p₃) h₁]

theorem frameHom_indist
    {obs₁ : P₁ → H₁ → O₁} {obs₂ : P₂ → H₂ → O₂} {Ω₁ : P₁ → Prop} {Ω₂ : P₂ → Prop}
    (φ : FrameHom H₁ P₁ O₁ H₂ P₂ O₂ obs₁ obs₂ Ω₁ Ω₂)
    {h₁ h₁' : H₁} (hi : Indist obs₁ Ω₁ h₁ h₁') :
    Indist obs₂ Ω₂ (φ.fH h₁) (φ.fH h₁') := by
  intro p₂ hp₂
  rw [φ.comm p₂ h₁, φ.comm p₂ h₁']
  exact congrArg φ.fO (hi (φ.fP p₂) (φ.power_compat p₂ hp₂))

theorem frameHom_determines_pullback
    {obs₁ : P₁ → H₁ → O₁} {obs₂ : P₂ → H₂ → O₂} {Ω₁ : P₁ → Prop} {Ω₂ : P₂ → Prop}
    (φ : FrameHom H₁ P₁ O₁ H₂ P₂ O₂ obs₁ obs₂ Ω₁ Ω₂)
    (S₁ : H₁ → Prop) (S₂ : H₂ → Prop) (q₁ : H₁ → A₁) (q₂ : H₂ → A₁)
    (hmap : ∀ h₁, S₁ h₁ → S₂ (φ.fH h₁))
    (hagree : ∀ h₁, S₁ h₁ → q₂ (φ.fH h₁) = q₁ h₁)
    (hd : Determines obs₂ Ω₂ S₂ q₂) :
    Determines obs₁ Ω₁ S₁ q₁ := by
  intro h₁ h₁' hs₁ hs₁' hi
  rw [← hagree h₁ hs₁, ← hagree h₁' hs₁']
  exact hd (φ.fH h₁) (φ.fH h₁') (hmap h₁ hs₁) (hmap h₁' hs₁') (frameHom_indist φ hi)

/-- Quantitative warrant loss bound across translated queries. -/
def QueryApprox {A : Type u1} (dA : A → A → Nat) (S₁ : H₁ → Prop)
    (q₁ : H₁ → A) (fH : H₁ → H₂) (q₂ : H₂ → A) (eps : Nat) : Prop :=
  ∀ h₁, S₁ h₁ → dA (q₁ h₁) (q₂ (fH h₁)) ≤ eps

/-- Warrant distortion composes additively across frames when `dA` satisfies
    the triangle inequality. -/
theorem queryApprox_comp {A : Type u1} (dA : A → A → Nat)
    (htri : ∀ a b c, dA a c ≤ dA a b + dA b c)
    (S₁ : H₁ → Prop) (S₂ : H₂ → Prop) (q₁ : H₁ → A) (q₂ : H₂ → A) (q₃ : H₃ → A)
    (f₁ : H₁ → H₂) (f₂ : H₂ → H₃) (eps₁ eps₂ : Nat)
    (hmap : ∀ h₁, S₁ h₁ → S₂ (f₁ h₁))
    (ha₁ : QueryApprox dA S₁ q₁ f₁ q₂ eps₁)
    (ha₂ : QueryApprox dA S₂ q₂ f₂ q₃ eps₂) :
    QueryApprox dA S₁ q₁ (f₂ ∘ f₁) q₃ (eps₁ + eps₂) := by
  intro h₁ hs₁
  have h1 := ha₁ h₁ hs₁
  have h2 := ha₂ (f₁ h₁) (hmap h₁ hs₁)
  have ht := htri (q₁ h₁) (q₂ (f₁ h₁)) (q₃ (f₂ (f₁ h₁)))
  exact Nat.le_trans ht (Nat.add_le_add h1 h2)

/-- End-to-end quantitative determinacy pullback: combining a `FrameHom` whose
    target frame `EpsDetermines` `q₂` with slack `tol` and an `eps`-approximate
    query correspondence `q₁ ≈ q₂ ∘ φ.fH` transfers determinacy back to `q₁`
    with explicit additive loss `2 * eps + tol`. -/
theorem frameHom_eps_determines_pullback
    {obs₁ : P₁ → H₁ → O₁} {obs₂ : P₂ → H₂ → O₂} {Ω₁ : P₁ → Prop} {Ω₂ : P₂ → Prop}
    (φ : FrameHom H₁ P₁ O₁ H₂ P₂ O₂ obs₁ obs₂ Ω₁ Ω₂)
    (dA : A → A → Nat)
    (htri : ∀ a b c, dA a c ≤ dA a b + dA b c)
    (hsym : ∀ a b, dA a b = dA b a)
    (S₁ : H₁ → Prop) (S₂ : H₂ → Prop) (q₁ : H₁ → A) (q₂ : H₂ → A)
    (eps tol : Nat)
    (hmap : ∀ h₁, S₁ h₁ → S₂ (φ.fH h₁))
    (ha : QueryApprox dA S₁ q₁ φ.fH q₂ eps)
    (hd : EpsDetermines obs₂ Ω₂ S₂ q₂ (fun x y => dA (q₂ x) (q₂ y)) tol)
    (hne_tol : ∀ h₁ h₁', q₁ h₁ ≠ q₁ h₁' → dA (q₂ (φ.fH h₁)) (q₂ (φ.fH h₁')) ≤ tol →
      dA (q₁ h₁) (q₁ h₁') ≤ 2 * eps + tol) :
    EpsDetermines obs₁ Ω₁ S₁ q₁ (fun x y => dA (q₁ x) (q₁ y)) (2 * eps + tol) := by
  intro h₁ h₁' hs₁ hs₁' hi hq
  dsimp only
  have hi₂ := frameHom_indist φ hi
  by_cases hq₂ : q₂ (φ.fH h₁) = q₂ (φ.fH h₁')
  · have h1 := ha h₁ hs₁
    have h2 := ha h₁' hs₁'
    rw [← hq₂] at h2
    have hsym2 : dA (q₂ (φ.fH h₁)) (q₁ h₁') ≤ eps := by rw [hsym]; exact h2
    have ht := htri (q₁ h₁) (q₂ (φ.fH h₁)) (q₁ h₁')
    omega
  · have htol := hd (φ.fH h₁) (φ.fH h₁') (hmap h₁ hs₁) (hmap h₁' hs₁') hi₂ hq₂
    exact hne_tol h₁ h₁' hq htol

/-- Metric triangle form of `frameHom_eps_determines_pullback` (no extra side
    condition needed when `dA` is a pseudometric). -/
theorem frameHom_eps_metric_pullback
    {obs₁ : P₁ → H₁ → O₁} {obs₂ : P₂ → H₂ → O₂} {Ω₁ : P₁ → Prop} {Ω₂ : P₂ → Prop}
    (φ : FrameHom H₁ P₁ O₁ H₂ P₂ O₂ obs₁ obs₂ Ω₁ Ω₂)
    (dA : A → A → Nat)
    (htri : ∀ a b c, dA a c ≤ dA a b + dA b c)
    (hsym : ∀ a b, dA a b = dA b a)
    (hrefl : ∀ a, dA a a = 0)
    (S₁ : H₁ → Prop) (S₂ : H₂ → Prop) (q₁ : H₁ → A) (q₂ : H₂ → A)
    (eps tol : Nat)
    (hmap : ∀ h₁, S₁ h₁ → S₂ (φ.fH h₁))
    (ha : QueryApprox dA S₁ q₁ φ.fH q₂ eps)
    (hd : EpsDetermines obs₂ Ω₂ S₂ q₂ (fun x y => dA (q₂ x) (q₂ y)) tol) :
    EpsDetermines obs₁ Ω₁ S₁ q₁ (fun x y => dA (q₁ x) (q₁ y)) (2 * eps + tol) := by
  intro h₁ h₁' hs₁ hs₁' hi _hq
  dsimp only
  have hi₂ := frameHom_indist φ hi
  have h1 := ha h₁ hs₁
  have h2 : dA (q₂ (φ.fH h₁')) (q₁ h₁') ≤ eps := by rw [hsym]; exact ha h₁' hs₁'
  have hmid : dA (q₂ (φ.fH h₁)) (q₂ (φ.fH h₁')) ≤ tol := by
    by_cases hq₂ : q₂ (φ.fH h₁) = q₂ (φ.fH h₁')
    · rw [hq₂, hrefl]; omega
    · exact hd (φ.fH h₁) (φ.fH h₁') (hmap h₁ hs₁) (hmap h₁' hs₁') hi₂ hq₂
  have t1 := htri (q₁ h₁) (q₂ (φ.fH h₁)) (q₁ h₁')
  have t2 := htri (q₂ (φ.fH h₁)) (q₂ (φ.fH h₁')) (q₁ h₁')
  omega

/-- Lossy Composition Obstruction Theorem:
    When an approximate relation drops exact naturality (`comm`) for pointwise
    1-step tolerance (`|obs_{k} - obs_{k+1}| ≤ 1`) across two consecutive lossy
    abstraction hops (`obs₀ → obs₁ → obs₂`), each individual hop strictly respects
    error ≤ 1, yet the composite observer `obs₂` violates `EpsDetermines ... tol = 1`.
    This proves why multi-hop lossy semantic abstraction strictly accumulates error
    across non-Lipschitz boundaries unless tolerance budgets add (`1 + 1 = 2`). -/
theorem lossy_composition_obstruction :
    let obs₀ : Unit → Fin 3 → Nat := fun _ x => x.val
    let obs₁ : Unit → Fin 3 → Nat := fun _ x => if x.val = 0 then 1 else x.val
    let obs₂ : Unit → Fin 3 → Nat := fun _ x => if x.val = 2 then 1 else (if x.val = 0 then 1 else x.val)
    let q : Fin 3 → Nat := fun x => x.val
    (∀ x : Fin 3, (obs₀ () x - obs₁ () x ≤ 1) ∧ (obs₁ () x - obs₀ () x ≤ 1)) ∧
    (∀ x : Fin 3, (obs₁ () x - obs₂ () x ≤ 1) ∧ (obs₂ () x - obs₁ () x ≤ 1)) ∧
    (¬ EpsDetermines obs₂ (fun _ => True) (fun _ => True) q
        (fun a b => if a.val ≤ b.val then b.val - a.val else a.val - b.val) 1) := by
  refine ⟨?_, ?_, ?_⟩
  · intro ⟨v, hv⟩
    dsimp only; split <;> omega
  · intro ⟨v, hv⟩
    dsimp only; split <;> split <;> omega
  · intro hd
    have h := hd ⟨0, by decide⟩ ⟨2, by decide⟩ trivial trivial
      (fun _ _ => by dsimp only; rfl) (by decide)
    revert h; decide

end Morphisms

end PFT

/-! ## §18 Discrete Markov Kernels & Data-Processing / TV Contraction (P072, Q-W1) -/

namespace PFT

section Markov

/-- Discrete unnormalized mass distribution over `A` (weights in `Nat`). -/
abbrev Dist (A : Type u) := List (A × Nat)

def Dist.mass {A : Type u} : Dist A → Nat
  | [] => 0
  | (_, w) :: xs => w + Dist.mass xs

def Dist.probOf {A : Type u} (E : A → Bool) : Dist A → Nat
  | [] => 0
  | (a, w) :: xs => (if E a then w else 0) + Dist.probOf E xs

def Dist.scale {A : Type u} (c : Nat) : Dist A → Dist A
  | [] => []
  | (a, w) :: xs => (a, c * w) :: Dist.scale c xs

def Dist.map {A : Type u} {B : Type v} (f : A → B) : Dist A → Dist B
  | [] => []
  | (a, w) :: xs => (f a, w) :: Dist.map f xs

def Dist.bind {A : Type u} {B : Type v} (K : A → Dist B) : Dist A → Dist B
  | [] => []
  | (a, w) :: xs => Dist.scale w (K a) ++ Dist.bind K xs

def natAbsDiff (a b : Nat) : Nat :=
  if a ≤ b then b - a else a - b

theorem natAbsDiff_triangle (a b c : Nat) :
    natAbsDiff a c ≤ natAbsDiff a b + natAbsDiff b c := by
  simp only [natAbsDiff]
  split <;> split <;> split <;> omega

theorem dist_probOf_append {A : Type u} (E : A → Bool) (μ ν : Dist A) :
    Dist.probOf E (μ ++ ν) = Dist.probOf E μ + Dist.probOf E ν := by
  induction μ with
  | nil => simp [Dist.probOf]
  | cons x xs ih =>
      rcases x with ⟨a, w⟩
      change Dist.probOf E ((a, w) :: (xs ++ ν)) = Dist.probOf E ((a, w) :: xs) + Dist.probOf E ν
      simp only [Dist.probOf, ih]
      omega

theorem dist_probOf_scale {A : Type u} (E : A → Bool) (c : Nat) (μ : Dist A) :
    Dist.probOf E (Dist.scale c μ) = c * Dist.probOf E μ := by
  induction μ with
  | nil => simp [Dist.scale, Dist.probOf]
  | cons x xs ih =>
      rcases x with ⟨a, w⟩
      simp only [Dist.scale, Dist.probOf, ih]
      by_cases h : E a <;> simp [h, Nat.mul_add]

/-- Deterministic post-processing pushes `probOf` straight into preimage events. -/
theorem dist_probOf_map {A : Type u} {B : Type v}
    (f : A → B) (E : B → Bool) (μ : Dist A) :
    Dist.probOf E (Dist.map f μ) = Dist.probOf (fun a => E (f a)) μ := by
  induction μ with
  | nil => simp [Dist.map, Dist.probOf]
  | cons x xs ih =>
      rcases x with ⟨a, w⟩
      simp [Dist.map, Dist.probOf, ih]

/-- Deterministic Data-Processing Inequality for event total variation:
    pushing forward by any `f : A → B` never increases worst-case event
    distinguishability `|μ(E) - ν(E)|`. -/
theorem tv_deterministic_dpi {A : Type u} {B : Type v}
    (f : A → B) (μ ν : Dist A) (Δ : Nat)
    (hTV : ∀ P : A → Bool, natAbsDiff (Dist.probOf P μ) (Dist.probOf P ν) ≤ Δ) :
    ∀ E : B → Bool,
      natAbsDiff (Dist.probOf E (Dist.map f μ)) (Dist.probOf E (Dist.map f ν)) ≤ Δ := by
  intro E
  rw [dist_probOf_map, dist_probOf_map]
  exact hTV (fun a => E (f a))

def weightedExpect {A : Type u} (g : A → Nat) : Dist A → Nat
  | [] => 0
  | (a, w) :: xs => w * g a + weightedExpect g xs

theorem dist_probOf_bind {A : Type u} {B : Type v}
    (K : A → Dist B) (E : B → Bool) (μ : Dist A) :
    Dist.probOf E (Dist.bind K μ) = weightedExpect (fun a => Dist.probOf E (K a)) μ := by
  induction μ with
  | nil => simp [Dist.bind, Dist.probOf, weightedExpect]
  | cons x xs ih =>
      rcases x with ⟨a, w⟩
      simp only [Dist.bind, dist_probOf_append, dist_probOf_scale, ih, weightedExpect]

def levelSum {A : Type u} (g : A → Nat) (μ : Dist A) : Nat → Nat
  | 0 => 0
  | m + 1 => levelSum g μ m + Dist.probOf (fun a => decide (m < g a)) μ

theorem levelSum_unit (k w M : Nat) :
    levelSum (fun _ : Unit => k) [((), w)] M = w * min k M := by
  induction M with
  | zero => simp [levelSum]
  | succ m ih =>
      by_cases h : m < k
      · have hmin : min k (m + 1) = m + 1 := Nat.min_eq_right (by omega)
        have hmin' : min k m = m := Nat.min_eq_right (by omega)
        simp only [levelSum, Dist.probOf, decide_eq_true_eq, h, if_true, ih, hmin, hmin', Nat.mul_succ]
        omega
      · have hmin : min k (m + 1) = k := Nat.min_eq_left (by omega)
        have hmin' : min k m = k := Nat.min_eq_left (by omega)
        simp only [levelSum, Dist.probOf, decide_eq_true_eq, h, if_false, ih, hmin, hmin']
        omega

theorem levelSum_single (k w : Nat) : ∀ M : Nat, k ≤ M →
    levelSum (fun _ : Unit => k) [((), w)] M = w * k := by
  intro M hk
  rw [levelSum_unit, Nat.min_eq_left hk]

theorem levelSum_cons {A : Type u} (g : A → Nat) (a : A) (w : Nat) (xs : Dist A) (M : Nat) :
    levelSum g ((a, w) :: xs) M =
      levelSum (fun _ : Unit => g a) [((), w)] M + levelSum g xs M := by
  induction M with
  | zero => simp [levelSum]
  | succ m ih =>
      simp only [levelSum, Dist.probOf, ih]
      by_cases hm : m < g a <;> simp [hm] <;> omega

/-- Layer-cake / Fubini identity: weighted expectation bounded by `M` decomposes
    into the sum of `M` tail-event probabilities. -/
theorem weightedExpect_eq_levelSum {A : Type u} (g : A → Nat) (M : Nat)
    (hbound : ∀ a, g a ≤ M) (μ : Dist A) :
    weightedExpect g μ = levelSum g μ M := by
  induction μ with
  | nil =>
      clear hbound
      induction M with
      | zero => simp [weightedExpect, levelSum]
      | succ m ih => simp [levelSum, Dist.probOf, ih]
  | cons x xs ih =>
      rcases x with ⟨a, w⟩
      rw [weightedExpect, ih, levelSum_cons, levelSum_single (g a) w M (hbound a)]

theorem levelSum_absDiff_le {A : Type u} (g : A → Nat) (μ ν : Dist A) (Δ : Nat)
    (hTV : ∀ P : A → Bool, natAbsDiff (Dist.probOf P μ) (Dist.probOf P ν) ≤ Δ) :
    ∀ M : Nat, natAbsDiff (levelSum g μ M) (levelSum g ν M) ≤ M * Δ := by
  intro M
  induction M with
  | zero => simp [levelSum, natAbsDiff]
  | succ m ih =>
      simp only [levelSum]
      have hlayer := hTV (fun a => decide (m < g a))
      have hadd : ∀ a₁ a₂ b₁ b₂ : Nat,
          natAbsDiff (a₁ + b₁) (a₂ + b₂) ≤ natAbsDiff a₁ a₂ + natAbsDiff b₁ b₂ := by
        intro a₁ a₂ b₁ b₂
        simp only [natAbsDiff]
        split <;> split <;> split <;> omega
      have hstep := hadd (levelSum g μ m) (levelSum g ν m)
        (Dist.probOf (fun a => decide (m < g a)) μ)
        (Dist.probOf (fun a => decide (m < g a)) ν)
      simp only [Nat.succ_mul]
      omega

theorem dist_probOf_le_mass {A : Type u} (E : A → Bool) (μ : Dist A) :
    Dist.probOf E μ ≤ Dist.mass μ := by
  induction μ with
  | nil => simp [Dist.probOf, Dist.mass]
  | cons x xs ih =>
      rcases x with ⟨a, w⟩
      simp only [Dist.probOf, Dist.mass]
      by_cases h : E a <;> simp [h] <;> omega

/-- Stochastic Markov Kernel Data-Processing Inequality (Fritz 2020 / Q-W1):
    For any Markov kernel `K : A → Dist B` whose outputs each have total mass ≤ `M`,
    if input distributions `μ, ν` satisfy event-TV distance `≤ Δ`, then pushed
    forward distributions `K_* μ, K_* ν` satisfy event-TV distance `≤ M * Δ`
    (equivalently TV does not expand when dividing by normalized mass `W * M`). -/
theorem markov_kernel_dpi {A : Type u} {B : Type v}
    (K : A → Dist B) (M : Nat) (hK : ∀ a, Dist.mass (K a) ≤ M)
    (μ ν : Dist A) (Δ : Nat)
    (hTV : ∀ P : A → Bool, natAbsDiff (Dist.probOf P μ) (Dist.probOf P ν) ≤ Δ) :
    ∀ E : B → Bool,
      natAbsDiff (Dist.probOf E (Dist.bind K μ)) (Dist.probOf E (Dist.bind K ν)) ≤ M * Δ := by
  intro E
  rw [dist_probOf_bind, dist_probOf_bind]
  have hle : ∀ a, Dist.probOf E (K a) ≤ M := fun a =>
    Nat.le_trans (dist_probOf_le_mass E (K a)) (hK a)
  rw [weightedExpect_eq_levelSum _ M hle μ, weightedExpect_eq_levelSum _ M hle ν]
  exact levelSum_absDiff_le _ μ ν Δ hTV M

/-- Compositional channel contraction across two Markov kernels `K₁` (`≤ M₁`) and
    `K₂` (`≤ M₂`): the combined TV loss scales at most by `M₁ * M₂ * Δ` (exact
    normalized non-expansion when dividing by `M₁ * M₂`). -/
theorem markov_kernel_dpi_comp {A : Type u} {B : Type v} {C : Type w}
    (K₁ : A → Dist B) (K₂ : B → Dist C) (M₁ M₂ : Nat)
    (hK₁ : ∀ a, Dist.mass (K₁ a) ≤ M₁) (hK₂ : ∀ b, Dist.mass (K₂ b) ≤ M₂)
    (μ ν : Dist A) (Δ : Nat)
    (hTV : ∀ P : A → Bool, natAbsDiff (Dist.probOf P μ) (Dist.probOf P ν) ≤ Δ) :
    ∀ E : C → Bool,
      natAbsDiff (Dist.probOf E (Dist.bind K₂ (Dist.bind K₁ μ)))
                 (Dist.probOf E (Dist.bind K₂ (Dist.bind K₁ ν))) ≤ M₂ * (M₁ * Δ) := by
  intro E
  apply markov_kernel_dpi K₂ M₂ hK₂ (Dist.bind K₁ μ) (Dist.bind K₁ ν) (M₁ * Δ)
  exact markov_kernel_dpi K₁ M₁ hK₁ μ ν Δ hTV

end Markov

end PFT

/-! ## §19 Peircean Triadic Semiosis & Anytime-Valid E-Process Ville Bound (P073) -/

namespace PFT

section SemiosisAndVille
universe u1 u2 u3 u4

/-- Peircean Triadic Semiosis:
    An Object `h : H`, under Representamen/sign-rendering protocol `rep : P → H → S`,
    induces a Pragmatic Equivalence via an Interpretant `interp : P → S → Act`. -/
def PragEquiv {H : Type u1} {P : Type u2} {S : Type u3} {Act : Type u4}
    (rep : P → H → S) (interp : P → S → Act) (Ω : P → Prop) (h₁ h₂ : H) : Prop :=
  Indist (fun p h => interp p (rep p h)) Ω h₁ h₂

/-- Coarsening law: object indistinguishability under signs always implies
    pragmatic equivalence under any Interpretant (lossy meaning coarsening). -/
theorem indist_implies_pragEquiv {H : Type u1} {P : Type u2} {S : Type u3} {Act : Type u4}
    (rep : P → H → S) (interp : P → S → Act) (Ω : P → Prop) {h₁ h₂ : H}
    (hi : Indist rep Ω h₁ h₂) : PragEquiv rep interp Ω h₁ h₂ :=
  fun p hp => congrArg (interp p) (hi p hp)

/-- Peirce's Pragmatic Maxim in PFT:
    An action/task query `q : H → Act` is determined by the sign-interpretant
    pipeline iff it conflicts nowhere within `PragEquiv` classes; and when `interp`
    is faithful on `Ω`, pragmatic determination coincides with representamen determination. -/
theorem peirce_pragmatic_maxim {H : Type u1} {P : Type u2} {S : Type u3} {Act : Type u4}
    (rep : P → H → S) (interp : P → S → Act) (Ω : P → Prop)
    (Dom : H → Prop) (q : H → Act) :
    (Determines (fun p h => interp p (rep p h)) Ω Dom q ↔
     HitsConflicts (fun p h => interp p (rep p h)) Ω Dom q) ∧
    (Determines (fun p h => interp p (rep p h)) Ω Dom q → Determines rep Ω Dom q) := by
  refine ⟨duality _ Ω Dom q, ?_⟩
  intro hd h₁ h₂ hs₁ hs₂ hi
  exact hd h₁ h₂ hs₁ hs₂ (indist_implies_pragEquiv rep interp Ω hi)

/-- Finite-horizon discrete stochastic filtration tree storing nonnegative
    wealth (e-value numerator) `w : Nat` at each node and branching transitions
    `(weight, child)` normalized to branching factor `M`. -/
inductive ProbTree : Type where
  | leaf (w : Nat) : ProbTree
  | step (w : Nat) (cs : List (Nat × ProbTree)) : ProbTree

def ProbTree.wealth : ProbTree → Nat
  | ProbTree.leaf w => w
  | ProbTree.step w _ => w

def branchSum : List (Nat × ProbTree) → Nat
  | [] => 0
  | (p, _) :: xs => p + branchSum xs

def branchWeightedWealth : List (Nat × ProbTree) → Nat
  | [] => 0
  | (p, c) :: xs => p * c.wealth + branchWeightedWealth xs

-- A valid discrete null-hypothesis supermartingale (test martingale) with
-- branching denominator `M`: branch weights sum to `M` and expected next wealth
-- never exceeds `M * current_wealth` (i.e. `E[E_{t+1} | F_t] ≤ E_t`).
mutual
  def IsSupermartingale (M : Nat) : ProbTree → Prop
    | ProbTree.leaf _ => True
    | ProbTree.step w cs =>
        branchSum cs = M ∧
        branchWeightedWealth cs ≤ M * w ∧
        IsSupermartingaleList M cs

  def IsSupermartingaleList (M : Nat) : List (Nat × ProbTree) → Prop
    | [] => True
    | (_, c) :: xs => IsSupermartingale M c ∧ IsSupermartingaleList M xs
end

/-- Adaptive stopping policy tree: at any `step` node, `stop` halts inquiry
    immediately (realizing current wealth); `cont f` continues with child-specific policies. -/
inductive StopPolicy : Type where
  | stop : StopPolicy
  | cont : (Nat → StopPolicy) → StopPolicy

mutual
  def applyStopList (next : Nat → StopPolicy) (k : Nat) :
      List (Nat × ProbTree) → List (Nat × ProbTree)
    | [] => []
    | (p, c) :: xs => (p, applyStop c (next k)) :: applyStopList next (k + 1) xs

  def applyStop : ProbTree → StopPolicy → ProbTree
    | ProbTree.leaf w, _ => ProbTree.leaf w
    | ProbTree.step w _, StopPolicy.stop => ProbTree.leaf w
    | ProbTree.step w cs, StopPolicy.cont next => ProbTree.step w (applyStopList next 0 cs)
end

theorem applyStop_wealth (t : ProbTree) (s : StopPolicy) :
    (applyStop t s).wealth = t.wealth := by
  cases t with
  | leaf w => cases s <;> rfl
  | step w cs => cases s <;> rfl

theorem applyStopList_branchSum (next : Nat → StopPolicy) :
    ∀ (k : Nat) (cs : List (Nat × ProbTree)),
      branchSum (applyStopList next k cs) = branchSum cs := by
  intro k cs
  induction cs generalizing k with
  | nil => simp [applyStopList, branchSum]
  | cons x xs ih =>
      rcases x with ⟨p, c⟩
      simp only [applyStopList, branchSum, ih (k + 1)]

theorem applyStopList_branchWeightedWealth (next : Nat → StopPolicy) :
    ∀ (k : Nat) (cs : List (Nat × ProbTree)),
      branchWeightedWealth (applyStopList next k cs) = branchWeightedWealth cs := by
  intro k cs
  induction cs generalizing k with
  | nil => simp [applyStopList, branchWeightedWealth]
  | cons x xs ih =>
      rcases x with ⟨p, c⟩
      simp only [applyStopList, branchWeightedWealth, applyStop_wealth, ih (k + 1)]

mutual
  theorem applyStopList_preserves_supermartingale (M : Nat) (next : Nat → StopPolicy) (k : Nat)
      (cs : List (Nat × ProbTree))
      (hsm : IsSupermartingaleList M cs) :
      IsSupermartingaleList M (applyStopList next k cs) := by
    cases cs with
    | nil => simp [applyStopList, IsSupermartingaleList]
    | cons x xs =>
        rcases x with ⟨q, d⟩
        rcases hsm with ⟨hd, hxs⟩
        exact ⟨applyStop_preserves_supermartingale M d (next k) hd,
               applyStopList_preserves_supermartingale M next (k + 1) xs hxs⟩

  /-- Optional Stopping preserves the supermartingale property for EVERY adaptive
      stopping policy `s`. -/
  theorem applyStop_preserves_supermartingale (M : Nat) (t : ProbTree) (s : StopPolicy)
      (hsm : IsSupermartingale M t) : IsSupermartingale M (applyStop t s) := by
    cases t with
    | leaf w =>
        cases s <;> simp [applyStop, IsSupermartingale]
    | step w cs =>
        cases s with
        | stop => simp [applyStop, IsSupermartingale]
        | cont next =>
            simp only [IsSupermartingale] at hsm
            rcases hsm with ⟨hsum, hmean, hchildren⟩
            refine ⟨?_, ?_, ?_⟩
            · simpa [applyStop] using (applyStopList_branchSum next 0 cs).trans hsum
            · simp only [applyStop, applyStopList_branchWeightedWealth]; exact hmean
            · exact applyStopList_preserves_supermartingale M next 0 cs hchildren
end

def normExpect (M : Nat) : Nat → ProbTree → Nat
  | d, ProbTree.leaf w => w * M ^ d
  | 0, ProbTree.step w _ => w
  | d + 1, ProbTree.step _ cs =>
      let rec go : List (Nat × ProbTree) → Nat
        | [] => 0
        | (p, c) :: xs => p * normExpect M d c + go xs
      go cs

def normHitMass (K M : Nat) : Nat → ProbTree → Nat
  | d, ProbTree.leaf w => if K ≤ w then M ^ d else 0
  | 0, ProbTree.step w _ => if K ≤ w then 1 else 0
  | d + 1, ProbTree.step _ cs =>
      let rec go : List (Nat × ProbTree) → Nat
        | [] => 0
        | (p, c) :: xs => p * normHitMass K M d c + go xs
      go cs

theorem normExpect_le_branch_list {M d : Nat}
    (ih : ∀ t : ProbTree, IsSupermartingale M t → normExpect M d t ≤ t.wealth * M ^ d) :
    ∀ (cs : List (Nat × ProbTree)), IsSupermartingaleList M cs →
      normExpect.go M d cs ≤ branchWeightedWealth cs * M ^ d := by
  intro cs hcs
  induction cs with
  | nil => simp [normExpect.go, branchWeightedWealth]
  | cons x xs ihxs =>
      rcases x with ⟨p, c⟩
      rcases hcs with ⟨hc_sm, hxs_sm⟩
      have hc := ih c hc_sm
      have hxs := ihxs hxs_sm
      simp only [normExpect.go, branchWeightedWealth, Nat.add_mul]
      have hmul : p * normExpect M d c ≤ p * (c.wealth * M ^ d) :=
        Nat.mul_le_mul_left p hc
      have hassoc : p * (c.wealth * M ^ d) = p * c.wealth * M ^ d :=
        (Nat.mul_assoc p c.wealth (M ^ d)).symm
      omega

theorem supermartingale_normExpect_le (M : Nat) :
    ∀ (d : Nat) (t : ProbTree), IsSupermartingale M t → normExpect M d t ≤ t.wealth * M ^ d := by
  intro d
  induction d with
  | zero =>
      intro t _
      cases t <;> simp [normExpect, ProbTree.wealth]
  | succ d ih =>
      intro t hsm
      cases t with
      | leaf w => simp [normExpect, ProbTree.wealth, Nat.pow_succ]
      | step w cs =>
          simp only [IsSupermartingale] at hsm
          rcases hsm with ⟨_, hmean, hchildren⟩
          simp only [normExpect, ProbTree.wealth]
          have hbranch := normExpect_le_branch_list ih cs hchildren
          have hscale : branchWeightedWealth cs * M ^ d ≤ (M * w) * M ^ d :=
            Nat.mul_le_mul_right (M ^ d) hmean
          have hpow : (M * w) * M ^ d = w * M ^ (d + 1) := by
            rw [Nat.pow_succ]; ac_rfl
          omega

/-- Optional Stopping Theorem (finite-horizon test supermartingales):
    For any adaptive stopping policy `s` on any supermartingale `t`,
    the stopped expected e-value at depth `d` never exceeds `t.wealth * M ^ d`. -/
theorem optional_stopping_supermartingale (M d : Nat) (t : ProbTree) (s : StopPolicy)
    (hsm : IsSupermartingale M t) :
    normExpect M d (applyStop t s) ≤ t.wealth * M ^ d := by
  have h1 := supermartingale_normExpect_le M d (applyStop t s)
    (applyStop_preserves_supermartingale M t s hsm)
  simpa [applyStop_wealth] using h1

theorem normHitMass_mul_le_normExpect (K M : Nat) :
    ∀ (d : Nat) (t : ProbTree), K * normHitMass K M d t ≤ normExpect M d t := by
  intro d
  induction d with
  | zero =>
      intro t
      cases t with
      | leaf w =>
          simp only [normHitMass, normExpect]
          by_cases h : K ≤ w <;> simp [h]
      | step w cs =>
          simp only [normHitMass, normExpect]
          by_cases h : K ≤ w <;> simp [h]
  | succ d ih =>
      intro t
      cases t with
      | leaf w =>
          simp only [normHitMass, normExpect]
          by_cases h : K ≤ w
          · simp only [h, if_true]
            have h1 : K * M ^ (d + 1) ≤ w * M ^ (d + 1) := Nat.mul_le_mul_right (M ^ (d + 1)) h
            exact h1
          · simp [h]
      | step w cs =>
          simp only [normHitMass, normExpect]
          induction cs with
          | nil => simp [normHitMass.go, normExpect.go]
          | cons x xs ihxs =>
              rcases x with ⟨p, c⟩
              have hc := ih c
              simp only [normHitMass.go, normExpect.go, Nat.mul_add]
              have hpm : K * (p * normHitMass K M d c) ≤ p * normExpect M d c := by
                have hk : K * (p * normHitMass K M d c) = p * (K * normHitMass K M d c) := by ac_rfl
                rw [hk]
                exact Nat.mul_le_mul_left p hc
              omega

/-- Safe Anytime-Valid Ville Maximal Inequality (Ramdas/Shafer E-processes):
    At ANY horizon `d`, under ANY adaptive optional-stopping / peeking rule `s`,
    for any test supermartingale `t` (starting wealth `t.wealth`), the mass of
    stopping trajectories reaching e-value `≥ K` satisfies:
      `K * normHitMass K M d (applyStop t s) ≤ t.wealth * M ^ d`.
    In particular, for an initial e-value `t.wealth = 1`, Type I rejection probability
    (`normHitMass / M^d`) is unconditionally `≤ 1 / K` regardless of data peeking. -/
theorem ville_anytime_valid_bound (K M d : Nat) (t : ProbTree) (s : StopPolicy)
    (hsm : IsSupermartingale M t) :
    K * normHitMass K M d (applyStop t s) ≤ t.wealth * M ^ d := by
  exact Nat.le_trans (normHitMass_mul_le_normExpect K M d (applyStop t s))
    (optional_stopping_supermartingale M d t s hsm)

end SemiosisAndVille

end PFT
