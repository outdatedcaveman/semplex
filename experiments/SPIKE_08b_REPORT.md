# Spike 08b: Hardening and extending the circuit atlas

**Date:** 2026-11-11 · **Status:** steps 1, 3 (n=3), 4, 5 done; step 3 (n=4) and step 2 (n=5 hunt) are **still computing** in the overnight job queue · **Follows:** Spike 08

New code: `cerp/kernel_bounds.py` (trusted), `cerp/bounds.py`, `cerp/netsolve.py`, `cerp/geometry.py`, `cerp/crunch.py`; kernel v0.4 gains a general-network artifact (skip connections, ReLU).

## Step 1: lower bounds, certified

Two certificate types, both checked by the trusted kernel:
- **Not a threshold function:** k true points and k false points with equal coordinate sums. A single neuron cannot separate them.
- **Not an intersection of two halfspaces:** a list of "bad" sets of false points, each with such a witness, such that every 2-colouring of the false points leaves some bad set monochromatic. The kernel tries all colourings itself.

| Claim (4 inputs) | Before | Now |
|---|---|---|
| Exactly 1,882 functions are computable by one neuron | literature number, unverified | **kernel-checked**: 1,882 single-neuron witnesses plus 63,654 non-threshold certificates (all of size 2) |
| The 79 classes at ≥ 4 neurons really need ≥ 4 | computed, uncertified | **kernel-checked** certificates for all 79 (both the function and its complement) |
| Parity needs 5 | computed, uncertified | two independent computations agree (exhaustive enumeration; CP-SAT solver reports no width-3 net in 0.7 s). **No certificate yet** |

No false certificate could be produced for any 3-neuron class (tested).

## Step 3: other families (skip connections, ReLU)

Method: an exact solver (CP-SAT) searches for a network with given wiring and integer weights in [-3, 3]. Found networks are kernel-checked. "No network" answers are solver claims inside that weight box. The solver was validated against the exact Spike 08 table (0 mismatches on all 3-input classes).

**3 inputs, all 14 classes (complete, all exact within the weight box):**

| Family | Classes by minimum neurons |
|---|---|
| Layered threshold (Spike 08) | 1: 6 · 3: 7 · 4: 1 |
| Threshold with skip connections | 1: 6 · **2: 8** |
| One hidden ReLU layer, no skip | 1: 6 · 3: 7 · 4: 1 (identical to layered threshold) |
| ReLU hidden layer + skip to output | 1: 6 · 2: 7 · 3: 1 |

**4 inputs (partial at time of writing: about 135 of 222 classes per family; final numbers in `atlas/jobs/families.jsonl`):**

| Family | Classes by minimum neurons so far |
|---|---|
| Threshold with skip | 1: 15 · 2: 84 · 3: 37 |
| ReLU, no skip | 1: 15 · 3: 105 · 4: 12 |
| ReLU + skip | 1: 15 · 2: 102 · 3: 18 |

Findings:
- **Skip connections fill the empty period 2.** With them, every 3-input function needs at most 2 neurons, including parity (4 → 2).
- **A ReLU hidden layer without skip connections bought nothing at 3 inputs**: the table is identical to the threshold one. At 4 inputs it helped 3 of the classes seen so far (4 → 3).
- The periodic table is therefore **a family of tables indexed by wiring and activation**, and the element ordering changes between them.

## Step 4: weight-space geometry (first version of the "manifold")

Every weight setting of a small network (all weights and biases in [-W, W]) is mapped to the function it computes.

| Inputs, hidden, W | Weight settings | Functions realized | Share of settings computing a 1-neuron function | Functions whose region is disconnected | Most common Hamming distance between touching functions |
|---|---|---|---|---|---|
| 2, 2, 1 | 19,683 | 16 of 16 | 99.9% | 8 | 1 |
| 2, 2, 2 | 1,953,125 | 16 of 16 | 99.87% | 14 | 1 |
| 3, 2, 1 | 177,147 | 220 of 256 | 99.43% | 204 | 2 |

Findings:
- **Strong simplicity bias, measured exactly.** XOR occupies 0.13% of weight space at W=2; the average single-neuron function has about 109× the volume of XOR.
- **Regions are fragmented on coarse grids** (up to 96 components for one function). Part of this is symmetry (swapping hidden neurons); how much remains on finer grids is being computed overnight.
- **One weight step is not one truth-table bit.** At 3 inputs the most common border is between functions differing in 2 outputs, and single steps can flip all 8 outputs (the output neuron's bias changing sign).

## Step 5: the one-bit-flip conjecture

**Theorem (informal proof; construction kernel-checked on 26,048 instances).** In the layered threshold family, let f′ differ from f at one input point p.
- If f has a best net of depth 2, then neurons(f′) ≤ neurons(f) + 1: add one hidden neuron that fires only at p, with an output weight large enough to override the rest.
- If f is a single neuron g, then neurons(f′) ≤ 3: f′ is "g OR at-p" or "g AND NOT at-p".
- For a best net of depth d ≥ 3, the same idea costs d − 1 neurons (the new signal must be relayed through each layer).

Consequences:
- For n ≤ 4 (where all best nets have depth ≤ 2), a flip changes the count by at most 2, and a change of exactly 2 happens only between a 1-neuron and a 3-neuron function. The data agree: all 36,544 jumps of 2 at n=4 are 1 ↔ 3.
- **The original conjecture ("at most 2 for all n") is not proved** for functions whose best nets are deep; the proved bound there is d − 1.
- With skip connections the bound is +1 in every case.

## Step 2: 5 inputs (running)

The table method cannot reach 5 inputs, so the search is targeted. Any XOR of two single neurons has a 5-neuron depth-3 net. For each sampled pair, the solver decides whether a depth-2 net with ≤ 4 hidden neurons exists (weights in [-5, 5]). If none does, that function is a **depth-sensitive element**: depth 3 strictly beats depth 2. Tooling is validated; results accumulate in `atlas/jobs/n5.jsonl`. **No result to report yet.**

## Overnight computation

`python -m cerp.crunch --job all --hours H --procs P` is resumable: one JSON line per finished unit, restart any time. A scheduled task restarts it hourly in this cloud session (4 CPUs, no GPU) and pushes checkpoints. The same command runs on any machine with `pip install numpy ortools`. These jobs are combinatorial search, so a GPU would not help as written.

## Gaps

- Parity's bound of 5 still lacks a certificate.
- "No network" answers in step 3 depend on the weight box [-3, 3] and on trusting the solver.
- The 5-input hunt samples candidates; finding nothing would be evidence, not proof.
- Geometry is for one hidden layer on ≤ 3 inputs with small integer weights.
