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

end PFT
