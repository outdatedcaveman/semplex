# Spike 05: Fragment F1, stateful systems

**Date:** 2026-11-06 · **Charter refs:** §1.3 ("do not collapse all semantics into input-output functions"), Layer E/F, §5.3 · **Status:** complete

## Question

Spike 01 lived in a world of functions. The charter warns that state, traces and contexts can matter. In the smallest stateful fragment (finite labelled transition systems), do the equivalences really come apart? Can each still be *certified* by a small trusted checker? And is the right equivalence fixed by the observation protocol Ω, as charter §5.2 claims?

## What was built

- **`cerp/lts.py` (untrusted):**
  - bisimulation by fixpoint refinement, emitting a bisimulation relation or a distinguishing Hennessy–Milner formula
  - trace and completed-trace equivalence by on-the-fly determinization, emitting a closed relation over state-sets or a witness trace
  - CSP parallel composition
  - the bisimulation quotient
- **`cerp/kernel_lts.py` (trusted, stdlib-only, may import only the core kernel):** checks each of those certificates locally, and decides deadlock of P ∥ T *itself* by exploring the product, so it doesn't trust the untrusted product construction.

## Hypotheses and verdicts

| # | Hypothesis | Verdict |
|---|---|---|
| H5.1 | The hierarchy bisimilarity ⊂ completed-trace ⊂ trace equivalence is strict, and the gaps are real in random systems | **Held** (F1) |
| H5.2 | Each verdict, positive or negative, has a certificate the kernel can check cheaply | **Held**: 6,000 random pairs, every verdict certified. The kernel also caught a mislabeled witness in the *untrusted* code (F4) |
| H5.3 | The finer distinctions matter operationally: some context observes them | **Held, with a twist**: 68/70 gap pairs separated by a random deadlock test, 2 not (F2) |
| H5.4 | For deterministic systems the hierarchy collapses, so I/O-style semantics is exact there | **Held**: 0 of 3,000 deterministic pairs split (F3) |

## Results (`results/spike05.json`; 3,000 random pairs per class, 2–3 states, actions {a, b})

| Class | Different traces | Trace-eq only | + completed-trace-eq, not bisimilar | Bisimilar |
|---|---|---|---|---|
| Nondeterministic | 2,734 | 28 | 42 | 196 |
| Deterministic | 2,725 | 0 | 0 | 275 |

## Findings

**F1. Equivalence is protocol-indexed, concretely.** The textbook pair is a.(b+c) vs a.b + a.c.
- They are trace-equivalent *and* completed-trace-equivalent; both certificates are kernel-checked.
- They are not bisimilar. The kernel checks the distinguishing formula ⟨a⟩(⟨b⟩⊤ ∧ ⟨c⟩⊤).
- **The difference becomes observable in a context.** Composed with the test "do a, then b", a.b + a.c *can deadlock* and a.(b+c) cannot. The kernel decides both by exploring the product itself.

So "are these the same system?" has no protocol-free answer. It depends on whether the observer can only record traces, or can also put the system in contexts. This is charter §5.2 (Ω-relative equivalence) made executable.

**F2. Bisimulation can be finer than any deadlock test.** For 2 of the 70 trace-equivalent, non-bisimilar pairs, no test among 300 random ones exposed a deadlock difference. This is consistent with the known result that deadlock-observing (must) testing characterizes *failures* equivalence, which is strictly coarser than bisimilarity (De Nicola & Hennessy 1984; metadata verified, but this specific claim is not stated in the abstract, see `charter/BIBLIOGRAPHY.md`). The consequence for the charter is that **the "right" equivalence is the coarsest one that the declared protocol can still observe.** Bisimulation is the safe default when every context is admissible, and it is *over-distinguishing* when observers are limited to deadlock tests. Layer F needs Ω → relation as a declared mapping, not a fixed choice.

**F3. The I/O-function view is exact exactly when there is no hidden choice.** For deterministic systems, trace equivalence equals bisimilarity (0/3,000 splits). The charter's non-goal "do not collapse semantics into I/O functions" therefore has a precise scope: the collapse is safe for deterministic systems and unsafe as soon as choice is internal. The same pattern appeared twice before:
- Spike 01 F4: multiplicity of minimal sets arises only under domain restriction.
- Spike 02 F4: the existence of hidden entities stays model-relative.

In each case, **distinctions are created by what the observer cannot see.**

**F4. The kernel caught a bug in the untrusted search.** In completed-trace mode the search sometimes found a *plain* trace difference but labeled it as a completed-trace witness. The kernel rejected it, and the search now reports the kind of witness it found. This is the separation of discovery and verification (§7.5) paying off on its first real bug.

**F5. A canonical *object* exists; a canonical *string* is harder.** The bisimulation quotient is the unique minimal system up to isomorphism (idempotence is tested). But turning it into a canonical serialized form requires graph canonization, for which no polynomial algorithm is known in general. That contrasts with F0, where the ROBDD gave a canonical string for free. This sharpens charter Layer G's caveat ("a quotient class … need not have a computable canonical syntax"): here the syntax is computable, but not obviously efficiently.

## Gaps

- No probabilistic systems, timing or continuous state. These are the next semantics the charter names.
- Contexts are limited to deadlock tests. Failures and readiness semantics are not implemented, so F2 is a consistency observation, not a proof.
- Systems are tiny (2–3 states). Partition refinement and determinization scale differently (polynomial vs exponential), and that is not measured here.
