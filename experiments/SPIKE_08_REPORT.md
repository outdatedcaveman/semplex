# Spike 08: A verifiable periodic table of threshold circuits, and compiler v1

**Date:** 2026-11-11 · **Charter refs:** Layers G, H, I, J; §5.7; THEORY.md Thm 3, 4, 10 · **Status:** complete for n ≤ 4

## Question

Can we enumerate *every* circuit in a declared finite family, classify the functions it computes into "elements", attach to each element its optimal circuit with a checkable guarantee, and then compile tasks by lookup? And does the Protocol-Frame Theory actually describe the structure that comes out?

## Scope (what "every finite arrangement" means in v1)

- **Family T:** strictly layered networks of threshold neurons on n binary inputs, one output. A neuron outputs 1 iff Σ wᵢ·inᵢ ≥ t (integer weights) and reads only the previous layer.
- **Elements:** Boolean functions up to NPN equivalence (permute or negate inputs, negate the output). T is closed under these, so cost is a class invariant. There are 14 classes for n=3 and 222 for n=4.
- **Cost:** (neurons, depth).
- **Not in v1:** skip connections, ReLU or real-valued activations, multiple outputs, n ≥ 5.

## Method (`cerp/atlas.py`)

**Layer peeling.** A net with first-layer width w computes f = Ψ(g₁,…,g_w), where each gᵢ is a threshold function of the inputs and Ψ is computed by the rest of the net, which is itself a net of family T on w inputs. So:

> neurons_n(f) = min over w, g, Ψ with f = Ψ∘g of w + neurons_w(Ψ)

The table for n inputs is therefore built from the tables for fewer inputs. Width w = n refers to the table being built, so it is solved by fixpoint iteration.

**What makes entries checkable:**
- **Upper bound:** a witness net, checked by the trusted kernel against the function's truth table (kernel v0.3 gained `tnet` and `table` artifacts, about 30 lines).
- **Lower bound:** every first layer of width ≤ 3 is enumerated up to symmetry. Anything not found needs width ≥ 4, hence ≥ 5 neurons.
- **Completeness anchor:** the enumeration of single-neuron functions reproduces the commonly cited counts 4, 14, 104, 1882 (OEIS A000609; not independently re-verified this session).

## Results (`results/spike08.json`, `atlas/PERIODIC_TABLE_n3.md`, `atlas/table_n4.json`)

| Inputs | Functions | Classes | Classes by minimum neurons | Exact entries | Witnesses kernel-verified |
|---|---|---|---|---|---|
| 2 | 16 | 4 | 1 neuron: 3 · 3 neurons: 1 | 4/4 | all |
| 3 | 256 | 14 | 1: 6 · 3: 7 · 4: 1 | 14/14 | all 256 functions |
| 4 | 65,536 | 222 | 1: 15 · 3: 128 · 4: 78 · 5: 1 | 222/222 | all 222 classes + 2,000 random functions via symmetry transport |

The n=4 table builds in about 50 s.

## Hypotheses and verdicts

| # | Hypothesis | Verdict |
|---|---|---|
| H8.1 | The family can be enumerated exhaustively for n ≤ 4 with exact minima | **Held**: every one of the 222 classes has matching lower and upper bounds |
| H8.2 | Every table entry carries a kernel-checkable witness | **Held**: 0 failures |
| H8.3 | The first layer behaves as a Protocol-Frame observational power | **Held for n=3**: neurons = (minimum determining width) + 1 for every non-threshold function. Not yet checked for n=4 |
| H8.4 | A table-driven compiler returns verified, provably optimal task circuits | **Held**: 1,200 random tasks, all kernel-verified, all certified optimal within T |
| H8.5 | Depth buys neurons | **Broke**: for n ≤ 4, depth beyond 2 never reduces the neuron count (F3) |

## Findings

**F1. The table has periods 1, 3, 4, 5, and period 2 is empty.** A second neuron stacked on one neuron can only pass or negate it, so nothing has cost 2. For 4 inputs, **every function except parity needs at most 4 neurons**, and 4-input parity is the single period-5 element. Its lower bound comes from the enumeration (not computable with any first layer of width ≤ 3), and its upper bound from the standard counting construction, kernel-checked.

**F2. The first layer is an observational power (theory ↔ table).** In Protocol-Frame terms, take the inputs as hypotheses and threshold functions as protocols. "f is computable above a first layer {g₁..g_w}" is exactly "the layer determines f" (THEORY.md Thm 3 and 10). For n=3 the table matches this exactly: neurons = w* + 1, where w* is the minimum number of threshold functions that determine f. Choosing a minimal first layer is the minimum hitting-set problem on f's conflict pairs, with hyperplane cuts as the hitting sets.

**F3. Depth never helps for n ≤ 4.** For all 65,536 4-input functions, the best depth-2 net has the same neuron count as the best net of any depth in T. Depth is expected to matter in this family eventually (deep nets realize parity-like functions with fewer units at larger n), so the open question is **where the first depth-sensitive element appears**. That is a concrete target for n=5.

**F4. Elements have "isomers", and no non-threshold element has a canonical first layer.** The number of distinct minimal first layers ranges from 4 (exactly-two-of-three) to 201 (3-input parity). By THEORY.md Thm 4, a unique minimal layer exists only if decisive protocols alone determine f. They never do here, so optimal circuits are unique only up to a large family of interchangeable first layers. The isomer count is a new, computable invariant of an element.

**F5. The cost landscape is smooth.** Flipping one truth-table bit changes the minimum neuron count by at most 2 in every table. For n=4: no change 72.5%, ±1 24.1%, ±2 3.5%. *Conjecture:* in family T a one-bit flip changes cost by at most 2 for all n. (The flipped point can be isolated by one extra hidden neuron, which suggests a proof.)

**F6. Compiler v1 works by lookup.** Given a target and a care set, it searches every completion of the don't-cares in the table and returns the cheapest net. On 300 random 4-input tasks per setting:

| Care-set density | Mean neurons, exact function | Mean neurons, task-optimal | Tasks made cheaper |
|---|---|---|---|
| 90% | 3.26 | 3.07 | 16% |
| 75% | 3.29 | 2.67 | 41% |
| 50% | 3.37 | 1.74 | 77% |
| 25% | 3.27 | 1.11 | 94% |

Every result was kernel-checked under the task relation and certified optimal within T, because the table is exact. This replaces Spike 01's heuristic don't-care handling with an exact optimum, for this family and size.

**F7. Small weights suffice.** Every witness for n ≤ 4 uses integer weights of magnitude ≤ 3.

## Warrants (what kind of claim each number is)

| Claim | Warrant |
|---|---|
| Upper bounds (witness computes the function) | kernel-checked, exhaustive over 2ⁿ inputs |
| Lower bounds, exactness, "depth never helps" | exact but uncertified computation (`cerp/atlas.py`), conditional on the 1,882 count |
| F5 for all n, first depth-sensitive element | conjecture / open |
| Compiler savings | empirical, random tasks |

The lower bounds are the weakest link. Certifying them (a proof per class that no narrower layer determines it, checked by the kernel or Lean) is the natural hardening step.

## Gaps

- **n = 5 is out of reach for this method**: 2³² functions and, by the commonly cited count, 616,126 classes. It needs class-level algorithms (work on representatives and conflict hypergraphs, not on all functions).
- **The "manifold" is so far thin**: one-bit-flip adjacency and isomer counts. The weight-space geometry (which weight changes move between elements, how many weight settings realize each element) is not yet built.
- **Family restrictions**: no skip connections, no ReLU, single output. Each is a parameter to add; the layer-peeling recursion needs restating for skip connections.
- **Prior art not surveyed**: minimal threshold networks for small n are a classical topic. The exact-table and PFT-linked presentation is ours, but the individual numbers may be known. A literature check is needed before any priority claim.
