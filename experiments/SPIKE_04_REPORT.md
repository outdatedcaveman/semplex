# Spike 04: Status as a structured warrant

**Date:** 2026-11-06 · **Charter refs:** §3.2, §10, §13.19 · **Status:** complete · **Motivated by:** Spike 01 F7, Spike 02 F8

## Question

Spikes 01 and 02 independently hit outputs with no honest §10 label, and both found that the labels are not a chain. Can a structured warrant replace the single status? It must let every output be labeled honestly, never let a derived claim look stronger than its support, and stay backward compatible with the charter's labels.

## Design (`cerp/ledger.py`)

- A claim carries a **warrant** (how well it is backed) and, separately, an **outcome** (what it says: asserted, refuted, out of scope, or undetermined).
- **Warrant = (basis, trusted base, conditions).**
  - The basis is a set of methods: proof-assistant, kernel-checked, witness-checked, exact-uncertified, empirical, assumption, rationale, heuristic.
  - The methods are partially ordered. The deductive methods form a chain; empirical is incomparable with that chain; assumption is incomparable with rationale.
- **Order:** w₁ ⪰ w₂ iff every method link of w₁ dominates some link of w₂, w₁ trusts no more, and w₁ is conditional on no more premises.
- **Derived claims** get the **join** of their dependencies' warrants: the union of bases, trusted bases and conditions.
- **Charter labels** are a lossy **projection** of (warrant, outcome). Two labels are new: WITNESSED and COMPUTED-UNCERTIFIED.

## Hypotheses and verdicts

| # | Hypothesis | Verdict | Evidence |
|---|---|---|---|
| H4.1 | Warrants form a partial order, and join is a lower bound (a derived claim can never look stronger than any of its supports) | **Held** | Property tests: order axioms on all method triples; join lower bound on 7,140 random pairs; transitivity on 6,000 triples |
| H4.2 | Every output of Spikes 01–02 gets an honest label | **Held** | Enumeration completeness → COMPUTED-UNCERTIFIED; equivalence fits → WITNESSED; closed-world-dependent answers → CONJECTURE *with the premise named*. All existing tests pass unchanged except one, which asserted the old, dishonest CONJECTURE label |
| H4.3 | The single label chain was hiding real structure | **Held, modestly** | 4.9–9.9% of asserted claim pairs in real ledgers are incomparable (`results/spike04.json`); CONJECTURE covers 2 distinct warrants |

## Findings

**F1. Outcome and warrant are different axes.** The v0 chain ranked REFUTED *below* HEURISTIC. But a kernel-decided refutation ("these two circuits are not equivalent, here is the counterexample") is among the best-warranted claims in the system. Separating outcome from warrant fixes this; see `test_kernel_refutation_is_strong_not_weak`.

**F2. CERTIFIED-REFINEMENT is not a warrant.** "Refinement" is the claim's *relation*; its backing is kernel-checked like any other claim's. The charter's §10 row mixes a semantic relation with an epistemic status, and this is now resolved by construction.

**F3. "Conditional on a premise" ≠ "unproven guess".** Both project to CONJECTURE, but their warrants are incomparable, and the ledger now names *which* premise a claim is conditional on. The Spike 02 answers now read "assumption+empirical | conditional on [E001]", where E001 is the closed-world premise. That is more honest and more actionable: refute E001 and you know exactly what falls.

**F4. Projection is necessarily lossy.** For example, {empirical} and {empirical, exact-uncertified} project to the same label but are strictly ordered. Labels are for humans skimming; decisions should read warrants.

## Migration rules (charter §13.19)

| v0 label | Becomes |
|---|---|
| PROVED / PROVED-IN-FRAGMENT | basis {proof-assistant} / {kernel-checked}, outcome asserted |
| CERTIFIED-REFINEMENT | basis {kernel-checked}; "refinement" moves into the claim's relation |
| EMPIRICALLY-SUPPORTED, CALIBRATED-PROBABILISTIC | basis {empirical}; calibration is evidence *about* the empirical method, kept in `evidence` |
| CONJECTURE | basis {rationale}, **or** {assumption} plus a named condition if it is a declared premise |
| HEURISTIC | basis {heuristic} |
| OUT-OF-SCOPE | outcome out-of-scope **or** undetermined (now distinguished) |
| REFUTED | outcome refuted, keeping the warrant of whatever refuted it |
| *(new)* | basis {exact-uncertified} → COMPUTED-UNCERTIFIED; {witness-checked} → WITNESSED |

## Gaps

- The method poset is a proposal, not a theorem. In particular, whether WITNESS_CHECKED sits *below* KERNEL_CHECKED or should be incomparable (different trusted bases) deserves argument; the trusted-base component already captures part of the difference.
- Probabilistic strength (how *much* empirical support) is not ordered. Two empirical warrants with p=10⁻² and p=10⁻¹² compare as equal on method. A quantitative layer would sit inside `evidence`. → Q-W1.
