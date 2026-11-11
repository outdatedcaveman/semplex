# Literature review and novelty audit

**Date:** 2026-11-11 · **Scope:** every result in `THEORY.md` and Spikes 08–10b that was described as possibly new.

**What this is not.** It is a first-pass review from index searches (alphaXiv, Consensus, web search), mostly at abstract level. Two requested starting points could not be used:
- **The Codex dossier** is not in the repository or in this session's uploads. Please add it (for example as `charter/dossier.md`) and this review will be redone against its links.
- **Nick Cammarata's essay** "Neural Networks Are Already Clean" (Goodfire, 15 Oct 2026) could not be opened: its site is outside this session's allowed network. Everything below about it is from secondary write-ups and is marked as such.

Verification levels are those of `REFERENCES.md`.

## 1. Verdict per claim

| Our result | Closest prior work found | Level | Verdict |
|---|---|---|---|
| Galois connection between observational power and indistinguishability (Thm 1–2) | Formal Concept Analysis (Wille; Ganter & Wille): a binary relation between objects and attributes induces a Galois connection and a concept lattice | ABSTRACT (several FCA papers state exactly this) | **Known.** Our Thm 2 is the FCA derivation operators applied to pairs of hypotheses |
| Determining a query = hitting every conflict set (Thm 3) | Rough-set discernibility (Skowron & Rauszer 1992) for features; **separating systems** for experiments: Hyttinen, Eberhardt, Hoyer, "Experiment selection for causal discovery" (JMLR 2013) translates combinatorics results into experiment selection; Shanmugam et al. 2015 prove any adaptive algorithm needs a separating system; teaching dimension / teaching sets for examples | ABSTRACT | **Each instance known.** The three-way identification is at best a repackaging; no novelty claim |
| Least determining set ⇔ decisive protocols determine (Thm 4) | Rough sets: core and unique reduct | ABSTRACT / MEMORY | **Known in the finite case**; ours is a mild generalization |
| Minimal representations can fail to exist (Thm 9) | Non-existence of minimal sufficient statistics in statistics | MEMORY, not searched | **Probably known in another form**; needs a targeted search |
| Gated answering is sound, complete, never flips (Thm 6); underdetermination (Thm 7) | Version spaces; selective classification; identification in causal discovery (Verma & Pearl 1990) | ABSTRACT for the last | **Known in spirit** |
| Warrants with named premises; weakest-link combination (Thm 8) | Assumption-based truth maintenance (de Kleer; Reiter & de Kleer 1987): every conclusion is labelled with the assumption sets it rests on; provenance semirings | ABSTRACT for ATMS | **The premise-tracking part is known.** The method × trust × premise order and its optimality statement were not found, but this is a small step |
| Minimal threshold networks by exact search, including partially specified functions (Spike 08 compiler, 08b solver) | **S. Cameron, "The Generation of Minimal Threshold Nets by an Integer Program" (IEEE Trans. Electronic Computers, 1964)**: minimum-neuron cycle-free threshold network for a *partially specified* Boolean function as an integer-program feasibility question; Hopcroft & Mattson, "Synthesis of Minimal Threshold Logic Networks" (1965); Celinski et al. 2001 (functions of up to 4 variables) | ABSTRACT | **Known since 1964.** Our solver formulation is Cameron's idea with a modern solver. Exact 4-input tables very likely exist (Muroga, MEMORY) |
| Non-threshold certificates (equal point sums) | Asummability (Elgot; Chow) | MEMORY | **Classical** |
| Simplicity bias comes from weight-space volume, not the learning rule (Spike 10b F1–F2) | The **volume hypothesis** literature: "Is SGD a Bayesian sampler?" (Mingard et al.), "guess and check" random sampling (Chiang et al.) (both MEMORY); found in index: "Revisiting the Volume Hypothesis" (arXiv:2606.31282), "Do Neural Networks Need Gradient Descent to Generalize?" (arXiv:2506.03931), "How Uniform Random Weights Induce Non-uniform Bias" (arXiv:2402.06323), "Bias of SGD or the Architecture" (arXiv:2407.03848) | INDEX | **Known and actively debated.** Ours is an exact small-scale replication against a ground-truth cost |
| Grokking from large initialization plus weight decay (Spike 10b F6) | Liu, Michaud, Tegmark, "Omnigrok: Grokking Beyond Algorithmic Data" (arXiv:2210.01117) | INDEX | **Known.** Our addition: the end point is a solver-certified cheapest completion |
| Error broadcast as a learning rule | Direct feedback alignment (Nøkland, MEMORY; several 2026 DFA papers in index) | INDEX | **Known**; ours is the all-ones special case |
| A rule that cannot see the task learns nothing about it (Thm 12) | Baldi & Sadowski, "A theory of local learning, the learning channel, and the optimality of backpropagation" (cited by Perin26) | META | **Known** (a backward channel is necessary) |
| Permutation-invariant monomials are indexed by partitions (basis of the symmetry-gap argument) | Maron et al., "Invariant and Equivariant Graph Networks" (2018): invariant/equivariant linear layers counted by Bell numbers; partition algebra | ABSTRACT | **The invariant theory is known.** Applying it to criticise trace-monomial rule dictionaries (Prop 14) was not found; Perin26 is days old |
| Many equivalent minimal circuits ("isomers"); seeds disagree on the circuit | Universality studies (arXiv:2302.03025); hidden symmetries of ReLU networks (arXiv:2306.06179); parameter-space symmetries (arXiv:2609.33527, 2609.39078) | INDEX | **Known theme**; exact isomer counts for tiny threshold nets not found |

## 2. What this means

- **The theory core is a synthesis of known results, not new mathematics.** `THEORY.md` §6 now says so explicitly and names FCA, separating systems, ATMS and Cameron 1964.
- **What is ours:** the integration (one framework, machine-checked, tied to running code with kernel-checked certificates), and exact small-scale measurements against a certified optimum.
- **Process failure to record:** several of these should have been found before the experiments were run. The spike protocol now has a prior-art gate (`ROADMAP.md`).

## 3. Cammarata, "Neural Networks Are Already Clean" (secondary sources only)

As reported by secondary write-ups (IBM Think, Wikipedia's polysemanticity article, others of lower quality):
- Most neurons in current large models have one clear role (a figure of about 90% for Qwen3-32B is quoted, from preliminary audits).
- Earlier polysemanticity is attributed to ordinary, fixable causes rather than superposition; some sources name a "recursive generalization" hypothesis in which related concepts form branches of a shared tree.
- The essay calls itself an informal working hypothesis; a technical companion is promised.

**Why it matters here:** the atlas is a neuron-level object. If neurons are the right unit in large models, an exact neuron-level theory at small scale is more relevant than it would be under strong superposition. The tiny exact setting can also *test* the disagreement (H-D below). None of this can be relied on until the essay itself is read.

## 4. Where the frontier appears to be: proposed new hypotheses

Each is stated so it can fail, and each needs its own prior-art check before work starts.

| # | Hypothesis | Why it may be new | Test we can run exactly |
|---|---|---|---|
| H-A | **Learnability atlas.** Which elements a rule can learn is governed by what the rule observes and by the layer's symmetry, and this ordering differs from the circuit-cost ordering | The volume literature studies which function is chosen, not which are reachable per rule class; needs exact ground truth, which we have | Spike 10c (running): 9 dictionaries × 222 elements |
| H-B | **Volume law for mechanisms.** Among the many minimal circuits of one function, the one training lands on is predicted by each circuit's own weight-space volume | The volume hypothesis is stated for functions; extending it to *which circuit* speaks directly to the universality question | Count each isomer's volume on the weight grid (`cerp/geometry.py`), compare with Spike 09's observed isomer frequencies |
| H-C | **Grokking delay law.** The delay between fitting and generalizing scales with the log ratio of the memorizing and generalizing regions' volumes at the current weight norm | Omnigrok gives the qualitative picture; an exact, predictive law at a scale where both volumes are computable was not found | 6-input runs across planted functions and initialization scales |
| H-D | **Clean vs superposed, exactly.** Define a hidden unit as clean if its threshold function belongs to some minimal determining set. Cleanness stays high until the hidden width falls below the function's minimum width, then drops sharply | Gives the superposition debate a setting with a certified notion of "the features" | Train at widths from 2 to 16 on all 222 elements |
| H-E | **First depth-sensitive element.** Find and certify the smallest function for which three layers beat two | Asymptotic separations are known; the first exact instance in this family was not found | Solver search at 5 and 6 inputs over more depth-3 shapes |
| H-F | **Limit representations.** For tail properties (no minimal representation), minimal ε-determining sets exist and converge | Follows from our Thm 9; statistics has related results to check first | Lean plus a constructive example |
