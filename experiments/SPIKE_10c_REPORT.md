# Spike 10c: What must a learning rule observe? (learnability across rule dictionaries)

**Date:** 2026-11-11 · **Status:** complete; results are **lower bounds** on what each dictionary can do · **Follows:** Spike 10b · **Prior-art check:** see `charter/LITERATURE_REVIEW.md` (H-A); nothing found that maps learnability per rule class against an exact table, at index level only

## Question

Spike 10b's meta-learner failed, so it could not say what each rule dictionary is capable of. With a search that works, which of the 222 four-input elements can the best rule found in each dictionary learn, and does the choice of rule change *which function* is learned on underspecified tasks?

## Method

- **Search:** cross-entropy method over the rule coefficients, scoring the final loss after a fixed 200 training steps, on half of the elements. Coefficients are in natural units (1 = same update size as backpropagation at initialization).
- **Sanity gates, both passed before the sweep:** started from backpropagation, the rule stayed working (99.4% fit); started from zero in the dictionary containing backpropagation, it found the backpropagation term (99.6%).
- **Scoring:** all 222 elements × 5 seeds; an element counts as learned if at least 4 of 5 seeds fit it. Partial tasks as in Spike 09.
- **Dictionaries:** power A (own layer), B (+ broadcast error), C (+ downstream weights); hidden symmetry O (orthogonal: trace monomials), B (signed permutations), S (permutations); orders 2–4.

## Results (`results/spike10c.json`)

| Dictionary (power, symmetry, order) | Terms | Tasks fit | Elements learned (of 222) | Cheapest completion (12 / 8 inputs given) |
|---|---|---|---|---|
| Backpropagation (reference) | — | 99.6% | 222 | 92% / 96% |
| No first-layer learning | — | 6.9% | 12 | |
| C, O, order 3 | 8 | 99.6% | 222 | 90% / 95% |
| C, O, order 4 | 30 | 58.6% | 94 | 82% / 71% |
| **B, S, order 2** | **7** | **99.6%** | **222** | 85% / 84% |
| B, S, order 3 | 23 | 97.8% | 220 | 83% / 79% |
| B, S, order 4 | 75 | 99.9% | 222 | 83% / 72% |
| B, O, order 4 (trace monomials) | 16 | 35.4% | 41 | 80% / 70% |
| B, B, order 4 | 19 | 27.5% | 24 | 80% / 71% |
| A, O, order 4 | 11 | 19.1% | 6 | |
| A, S, order 3 | 16 | 17.8% | 7 | |

## Hypotheses and verdicts

| # | Hypothesis | Verdict |
|---|---|---|
| H10c.1 | A derivative-free search at a fixed horizon finds working rules | **Held** for small dictionaries; **degrades with dictionary size** (F4) |
| H10c.2 | Downstream weights are needed to learn every element | **Broke**: a 7-term rule with only a broadcast error learns all 222 |
| H10c.3 | Trace-monomial dictionaries suffice at the broadcast-error level | **Not supported**: best found learns 41 of 222; this is a floor, not a proof |
| H10c.4 | The completion bias is independent of the rule (conjecture C6) | **Broke** in its strong form (F3) |

## Findings

**F1. Every element is learnable without downstream weights.** With a broadcast error and plain permutation symmetry, a 7-term order-2 dictionary learns all 222 elements at backpropagation's fit rate. The found rule is the error-broadcast term plus a term decorrelating the weight rows and a weight decay. Error broadcast itself is known (direct feedback alignment); what is measured here is that it reaches the *whole* table in this setting.

**F2. The symmetry assumed by the dictionary matters far more than its size.** At the same observational power (B) and a higher order, the orthogonal and signed-permutation dictionaries reached 41 and 24 elements, against 222 for the permutation dictionary at order 2. Proposition 14 explains why the working term is missing from them. Whether *some* rule in those dictionaries does better is open: these are search results.

**F3. Rules that fit equally well can generalize differently.** On tasks with 8 of 16 inputs given, backpropagation chose a table-cheapest completion in 96% of fitted runs; the meta-learned permutation-symmetric rules, which fit just as often, chose one in only 72–84%. In Spike 10b, hand-written rules without extra terms matched backpropagation. So the completion bias is not purely a property of the network: terms in the rule that act on the weights directly (row decorrelation, decay) shift it. **Conjecture C6 is withdrawn in its strong form.** The exact table makes this difference measurable, which loss alone does not.

**F4. The search is the limiting factor for large dictionaries, and the data show it.** Dictionary "C, O, order 4" contains "C, O, order 3", yet scored 94 elements against 222. Likewise the signed-permutation dictionary contains the orthogonal one but scored lower. A correct ceiling can never decrease when a dictionary grows, so every number in the table is a lower bound, and the gaps for B,O and B,B cannot be read as impossibility.

**F5. Task-blind rules do slightly better than a frozen layer, as theory allows.** Power A rules cannot use the task (Theorem 12), but they can still shape generic features: 17–19% of tasks fit against 6.9% for a frozen layer.

## Gaps

- One architecture, one horizon, one inner optimizer.
- No proof either way about the trace-monomial dictionaries at power B.
- The completion-bias difference (F3) is observed for three learned rules; the mechanism (direct weight terms) is a hypothesis.
