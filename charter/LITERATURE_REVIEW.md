# Literature review and novelty audit

**Date:** 2026-11-11 · **Scope:** every result in `THEORY.md` and Spikes 08–10b that was described as possibly new.

**What this is.** A first-pass review from index searches (alphaXiv, Consensus, web search), mostly at abstract level, plus direct reads of the sources listed in the charter's §17 (the dossier) and of Nick Cammarata's essay, once the session's network was opened to those sites.

**Read directly on 2026-11-11:**
- Cammarata, "Neural Networks Are Already Clean" (Goodfire): the opening "Short Version" (about the first 2,500 of 43,000 words) in full; the rest only by keyword scan.
- Stanford Encyclopedia entries on Structural Realism, Scientific Realism, Compositionality and Category Theory: introductions and the passages quoted below, not the whole entries.
- Abate et al., "Trace-Relating Compiler Correctness and Secure Compilation" (arXiv:1907.05320, the conference version of the TOPLAS paper in the dossier): abstract.
- CompCert documentation index (version 3.18, 2026-08-31).
- Not reachable: `doi.org` links (Smith 2010; "Observational program calculi", TCS 2015).

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

## 3. The dossier's own sources (charter §17) against our results

| Dossier source | What it says (as read) | Consequence for us |
|---|---|---|
| Abate et al., trace-relating compiler correctness | Compiler correctness generalized to source and target traces from different sets, connected by an arbitrary relation; characterizes which target property a source property guarantees, and the reverse | **Prior art for the CSIR's central idea** (Spike 07): a certified link is a relation between differently-typed semantics, and what it preserves depends on that relation. Our "relation order" and composition rule should be restated in their terms before any claim |
| CompCert (Leroy 2009; docs v3.18) | A compiler written and proved correct in Coq: generated code is semantically equivalent to its source | The benchmark for "verified translation". Our kernel-checked translations (Spikes 01, 03, 06) are translation *validation* on tiny languages, far short of this. No novelty there |
| SEP, Structural Realism | Epistemic structural realism: we can know only the structure of the unobservable world. **Newman's objection** (1928; Demopoulos & Friedman 1985): structure alone is not sufficient to pick out any relations; any collection of the right size can be given that structure, so a purely structural claim reduces to its observational consequences plus a cardinality claim | **Corrects THEORY §3.4.** We wrote that "the empirically secure part of an ontology is its Ω-profile" and called this a structural-realist reading. By Newman's objection, that is no more than empirical adequacy relative to Ω. It is a restatement of Thm 7, not support for realism about structure. Text corrected |
| SEP, Scientific Realism | Underdetermination of theory by data; Duhem: a hypothesis yields predictions only together with auxiliary assumptions, so a failed prediction does not say which assumption failed | Our named premises (closed world, faithfulness, parsimony) are Duhem's auxiliaries made explicit. Our retraction rule blames a named premise; Duhem's point is that the blame is not determined by the data. Spike 02b assumed one culprit; that needs stating as a policy |
| SEP, Compositionality; Category Theory | Not examined beyond the introductions | Open: charter §14 asks for a compositional semantics across system classes; nothing here addresses it yet |
| Smith 2010 (ontological realism); "Observational program calculi" (TCS 2015) | Not reachable | To read |

## 3b. Cammarata, "Neural Networks Are Already Clean" (opening section read from the primary source)

The essay describes itself as "an informal research essay and working hypothesis". Its claims, as stated there:
- "A network's own mechanisms are its legible building blocks." The canonical evidence for polysemanticity and superposition "was misread".
- **Recursive generalization**: "as a neuron grows, it sprouts offshoots the way a tree branch sprouts sub-branches" (example: a neuron for "iy" grows to "diy", then "do it yourself"). "Generalization is fractal."
- On running out of room: "With less room, the network doesn't fold unrelated things together; its neurons just cover coarser-grained concepts"; with more room, a broad neuron "differentiates into many specific" ones. He reports training InceptionV1 variants across a 300× size range.
- Numbers: with ordinary architectural fixes, "99-100% of neurons" in InceptionV1's last layer are "easily interpretable"; for Qwen3-32B, "roughly 90% of neuron poles have one main job", about 7% two related jobs, 2–4% not yet understood. He cautions that a single cleanliness score depends on thresholds and should be read as "a broad pointer".
- A technical companion paper is promised.

**Why it matters here:**
- The atlas is a neuron-level object. If neurons are the right unit in large models, an exact neuron-level theory at small scale is more relevant than it would be under strong superposition.
- The essay makes a specific, testable claim about width: fewer neurons give *coarser* neurons, not arbitrary mixtures. In our setting "coarser" has an exact meaning (a unit whose threshold function is a union of the cells that a wider minimal layer separates), so the claim can be tested with a certified notion of the features. This sharpens H-D below.
- His method of watching neurons grow over training matches what Spike 09's trajectories measure only crudely.

## 4. Where the frontier appears to be: proposed new hypotheses

Each is stated so it can fail, and each needs its own prior-art check before work starts.

| # | Hypothesis | Why it may be new | Test we can run exactly |
|---|---|---|---|
| H-A | **Learnability atlas.** Which elements a rule can learn is governed by what the rule observes and by the layer's symmetry, and this ordering differs from the circuit-cost ordering | The volume literature studies which function is chosen, not which are reachable per rule class; needs exact ground truth, which we have | Spike 10c (running): 9 dictionaries × 222 elements |
| H-B | **Volume law for mechanisms.** Among the many minimal circuits of one function, the one training lands on is predicted by each circuit's own weight-space volume | The volume hypothesis is stated for functions; extending it to *which circuit* speaks directly to the universality question | Count each isomer's volume on the weight grid (`cerp/geometry.py`), compare with Spike 09's observed isomer frequencies |
| H-C | **Grokking delay law.** The delay between fitting and generalizing scales with the log ratio of the memorizing and generalizing regions' volumes at the current weight norm | Omnigrok gives the qualitative picture; an exact, predictive law at a scale where both volumes are computable was not found | 6-input runs across planted functions and initialization scales |
| H-D | **Coarser, not folded (Cammarata's width claim, exactly).** When hidden width is reduced, trained units become *coarsenings* of the units of a wider minimal layer (unions of its cells), not unrelated mixtures; cleanness, defined as membership in some minimal determining set, falls only below the function's minimum width | The essay asserts this from large vision models; no exact test with a certified feature set was found | Train at widths from 2 to 16 on all 222 elements; classify each unit as minimal-set member, coarsening, or neither |
| H-E | **First depth-sensitive element.** Find and certify the smallest function for which three layers beat two | Asymptotic separations are known; the first exact instance in this family was not found | Solver search at 5 and 6 inputs over more depth-3 shapes |
| H-F | **Limit representations.** For tail properties (no minimal representation), minimal ε-determining sets exist and converge | Follows from our Thm 9; statistics has related results to check first | Lean plus a constructive example |

## 3c. Prior-art closure for Charter §17 & quantitative categorical/statistical foundations (2026-11-13)

Targeted literature retrieval resolved the four §17 dossier gaps and established the exact boundary between prior art and genuinely original space for `semplex`:

1. **Trace-relating compilation (`Abate19` / TOPLAS 2021, *Trace-Relating Compiler Correctness and Secure Compilation*):** Establishes generic trace relations between heterogeneous source and target languages, characterizing target guarantees from source properties (and vice versa) plus full-abstraction / robust-property preservation with Coq mechanization. **Implication:** Relation-indexed CSIR adequacy between discrete languages is *prior art*, not novel.
2. **Observational program calculi (`ObsCalculi15`, Schmidt-Schauß, Sabel, Niehren & Schwinghammer, TCS 577, 2015):** Provides abstract observational calculi and proof methods for adequacy and full abstraction of translations across functional/contextual-equivalence calculi. **Implication:** Observational preservation under language translation is *prior art*.
3. **Categorical probability & sufficiency (`Fritz20`, Adv. Math. 370, 2020, arXiv:1908.07021):** Formalizes Markov kernels, conditional independence, disintegration, and classical sufficiency theorems (Fisher–Neyman, Basu, Bahadur) diagrammatically inside symmetric monoidal categories (Markov categories). **Implication:** Synthetic sufficiency & stochastic kernels have an established categorical home, though without compiler trace relations or quantitative protocol-obstruction budgets.
4. **Ontological realism & SEP compositionality (`Smith10`, Applied Ontology 5(3–4), 2010; `SEP-Comp`, `SEP-Cat`):** Smith & Ceusters defend separating objective reality (universals/particulars) from internal database/conceptual schemes; SEP *Compositionality* and *Category Theory* formulate Fregean meaning homomorphisms as functors from syntactic categories to semantic categories/toposes.
5. **Anytime-valid statistics & Peircean triadic semiosis (`Ramdas23` / Shafer–Vovk game-theoretic statistics, e-values & test martingales; Peirce Sign–Object–Interpretant):** Safe anytime-valid inference (SAVI) proves Ville's inequality for nonnegative supermartingales / e-processes under arbitrary optional stopping, while Peirce's triadic semiosis models meaning via operational/pragmatic *Interpretants*.

**Genuine original mathematical niche (not yet unified in any retrieved source):** Coupling Abate-style heterogeneous protocol/trace morphisms with **explicit quantitative warrant contraction** (total variation data-processing under post-processing kernels + additive protocol distortion budgets), an explicit **obstruction theorem showing where naive lossy composition fails**, **Peircean `Interpretant` quotients** inducing task-relative observational equivalences, and **machine-checked finite anytime-valid e-process stopping bounds (`Ville`)** inside one Lean 4 development (`proofs/lean/Theory.lean`).

