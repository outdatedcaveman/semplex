# Master reference index

One row per external source used anywhere in the project. Details and discussion live in the two notes files:
- `BIBLIOGRAPHY.md`: Spikes 01–07 (per-claim verification notes).
- `LITERATURE_ATLAS.md`: circuit atlas, Spikes 08–10b.

**Rule (charter §13):** nothing is cited as support unless its verification level says so.

| Level | Meaning |
|---|---|
| FULL | Full text read (via alphaXiv full text) |
| REPORT | alphaXiv AI-generated report of the paper read, not the paper itself |
| ABSTRACT | Title, authors, venue and abstract confirmed in an index; abstract supports the specific use |
| META | Bibliographic record confirmed only |
| INDEX | Seen as a search hit (title and snippet); relevance is a guess |
| MEMORY | Recalled, not looked up. Never cite as support |

| Key | Reference | Level | Used in | Used for |
|---|---|---|---|---|
| Bryant86 | R. E. Bryant, "Graph-Based Algorithms for Boolean Function Manipulation", IEEE Trans. Computers | ABSTRACT (year discrepancy: index says 1989, usually cited 1986) | S01 | ROBDD canonicity |
| CoudertMadre90 | O. Coudert, J. C. Madre, "A unified framework for the formal verification of sequential circuits", ICCAD 1990 | ABSTRACT | S01, S02b | `restrict` operator |
| SkowronRauszer92 | A. Skowron, C. Rauszer, "The Discernibility Matrices and Functions in Information Systems", 1992 | ABSTRACT (venue unverified) | S01, THEORY Thm 3–4 | Reducts as hitting sets; precedent for the duality |
| Pawlak82 | Z. Pawlak, "Rough sets", 1982 | MEMORY (only a related report and a 2006 survey found) | S01 | Rough sets |
| Satterthwaite46 | F. E. Satterthwaite, "An approximate distribution of estimates of variance components", Biometrics | META | S02 | Scaled chi-square tail |
| VermaPearl90 | T. Verma, J. Pearl, "Equivalence and Synthesis of Causal Models", 1990 | ABSTRACT | S02, S02b | Observational equivalence of causal models |
| Wetzler14 | N. Wetzler, M. Heule, W. Hunt, "DRAT-trim", 2014 | ABSTRACT | S03 | Proof checking costs about as much as solving |
| Pollitt23 | F. Pollitt et al., "Faster LRAT Checking Than Solving with CaDiCaL", 2023 | ABSTRACT | S03 | LRAT as the cheaper-to-check format |
| DeNicolaHennessy84 | R. De Nicola, M. Hennessy, "Testing Equivalences for Processes", TCS 1984 | ABSTRACT (specific claim not in abstract) | S05 | Testing equivalences |
| HennessyMilner85 | M. Hennessy, R. Milner, "Algebraic laws for nondeterminism and concurrency", J. ACM 1985 | ABSTRACT | S05 | I/O semantics inadequate under nondeterminism |
| OEIS-A003024 | Number of labelled DAGs | MEMORY (reproduced by our enumerator) | S02b | 543 and 29,281 |
| OEIS-A000609 | Number of threshold functions | MEMORY; **superseded**: the n ≤ 4 counts are now kernel-checked (P039) | S08 | 104 and 1,882 |
| Leroy09 | X. Leroy, "Formal verification of a realistic compiler", CACM 52(7), 2009 | META (confirmed in CompCert's own documentation, v3.18) | Charter §17, Review §3 | Verified compilation |
| Nanda23 | N. Nanda, L. Chan, T. Lieberum, J. Smith, J. Steinhardt, "Progress measures for grokking via mechanistic interpretability", arXiv:2301.05217 | REPORT | S09, S10b | Grokking phases; reverse-engineered circuits |
| Bessa26 | S. Bessa et al., "e-means: outperforming k-means (in one-tenth the epochs)", arXiv:2611.09501 | Abstract, introduction and related work read in full text; experiments not read. Code presence checked in `faiss-cpu` 1.16.0 | Notes only | Possible future clustering tool |
| Perin26 | A. Perin, F. Anselmi, S. Deny, "A method to automatically discover symbolic local learning rules", arXiv:2611.12248 | FULL | S10b | Local learning rules; motivates scoring rules against the table |
| Chughtai23 | "A Toy Model of Universality: Reverse Engineering How Networks Learn Group Operations", arXiv:2302.03025 | INDEX | Notes | Universality of circuits |
| CombInterp25 | "Towards Combinatorial Interpretability of Neural Computation", arXiv:2504.08842 | INDEX | Notes | Sign-pattern analysis of weights |
| ReLUIdent26 | "Complete Identification of Deep ReLU Networks through Łukasiewicz Logic", arXiv:2602.00266 | INDEX | Notes | Non-uniqueness of ReLU networks |
| ReLUDepth26 | "Depth Lower Bounds for ReLU Networks with Binary Inputs", arXiv:2606.18540 | INDEX | Notes | Depth vs size on Boolean inputs |
| Occam26 | "Deep-layered machines have a built-in Occam's razor", arXiv:2603.01217 | INDEX | Notes | Simplicity bias |
| UnitGap26 | "The Unit Gap: How Sharing Works in Boolean Circuits", arXiv:2603.08033 | INDEX | Notes | Circuit vs formula size |
| BoolThresh26 | "Learning with Boolean threshold functions", arXiv:2602.17493 | INDEX | Notes | Training ±1 networks |
| InterpBench24 | "InterpBench", arXiv:2407.14494 | INDEX | Notes | Ground-truth circuits for interpretability |
| ACDC23 | "Towards Automated Circuit Discovery for Mechanistic Interpretability", arXiv:2304.14997 | INDEX | Notes | Automated circuit discovery |
| Monotone22 | "Size and depth of monotone neural networks", arXiv:2207.05275 | INDEX | Notes | Monotone threshold networks |
| Muroga | S. Muroga, threshold-logic tables and optimal threshold networks | MEMORY | S08 caution | Likely prior art for small-n minima |
| Knuth4A | D. Knuth, TAOCP vol. 4A §7.1.2, optimal Boolean chains | MEMORY | S08 caution | Closest classical "periodic table" |
| Hajnal93 | Hajnal, Maass, Pudlák, Szegedy, Turán, threshold circuits of bounded depth | MEMORY | S08 | Depth separations |
| VallePerez18 | G. Valle-Pérez, C. Camargo, A. Louis, simplicity bias of the parameter-function map | MEMORY | S08b, S10b | Volume hypothesis tested in S10b |
| Lillicrap16 | T. Lillicrap et al., "Random synaptic feedback weights support error backpropagation for deep learning", Nature Communications 2016 | META (as cited in Perin26's reference list) | S10b | Feedback alignment rule |
| Weyl-FFT | First fundamental theorem of invariant theory for the orthogonal group (invariants are generated by contractions); partition-indexed invariants for the symmetric group | MEMORY | THEORY §3.6, S10b F3 | Why trace monomials = orthogonal invariants |
| FCA | R. Wille; B. Ganter & R. Wille, Formal Concept Analysis (Galois connection between objects and attributes) | ABSTRACT (via several FCA papers that state it; originals not opened) | THEORY Thm 1–2 | Prior art for the Galois connection |
| Hyttinen13 | A. Hyttinen, F. Eberhardt, P. Hoyer, "Experiment selection for causal discovery", JMLR 2013 | ABSTRACT | THEORY Thm 3 | Experiment selection as a combinatorial (separating-system) problem |
| Shanmugam15 | K. Shanmugam et al., "Learning Causal Graphs with Small Interventions", 2015 | ABSTRACT | THEORY Thm 3 | Separating systems are necessary |
| Zilles11 | S. Zilles et al., "Models of Cooperative Teaching and Learning", JMLR 2011 | ABSTRACT | THEORY Thm 3 | Teaching dimension / teaching sets |
| ReiterDeKleer87 | R. Reiter, J. de Kleer, "Foundations of Assumption-based Truth Maintenance Systems", 1987 | ABSTRACT | THEORY Thm 8, S04 | Premise-labelled conclusions |
| Cameron64 | S. Cameron, "The Generation of Minimal Threshold Nets by an Integer Program", IEEE Trans. Electronic Computers 1964 | ABSTRACT | S08, S08b | Prior art for exact minimal threshold nets on partially specified functions |
| HopcroftMattson65 | J. Hopcroft, R. Mattson, "Synthesis of Minimal Threshold Logic Networks", IEEE Trans. Electronic Computers 1965 | ABSTRACT | S08 | Prior art |
| Celinski01 | P. Celinski et al., threshold-gate synthesis for functions of up to 4 variables, 2001 | ABSTRACT | S08 | Prior art at our exact scale |
| Maron18 | H. Maron et al., "Invariant and Equivariant Graph Networks", 2018 | ABSTRACT | THEORY Prop 14, S10b | Permutation invariants counted by Bell numbers |
| Omnigrok22 | Z. Liu, E. Michaud, M. Tegmark, "Omnigrok: Grokking Beyond Algorithmic Data", arXiv:2210.01117 | INDEX | S10b F6 | Grokking from initialization scale and weight decay |
| Volume-2606 | "Revisiting the Volume Hypothesis", arXiv:2606.31282 | INDEX | S10b F2 | Volume hypothesis, current debate |
| Volume-2506 | "Do Neural Networks Need Gradient Descent to Generalize? A Theoretical Study", arXiv:2506.03931 | INDEX | S10b F2 | Volume hypothesis |
| Volume-2402 | "How Uniform Random Weights Induce Non-uniform Bias", arXiv:2402.06323 | INDEX | S10b F2 | Random interpolating networks |
| Volume-2407 | "Bias of Stochastic Gradient Descent or the Architecture", arXiv:2407.03848 | INDEX | S10b F1 | Rule vs architecture |
| Mingard21 | C. Mingard et al., "Is SGD a Bayesian sampler? Well, almost" | MEMORY | S10b F2 | Volume hypothesis |
| Chiang23 | P. Chiang et al., "Loss landscapes are all you need" (guess and check) | MEMORY | S10b F2 | Random fitting networks generalize |
| Nokland16 | A. Nøkland, direct feedback alignment | MEMORY | S10b | Error broadcast |
| BaldiSadowski15 | P. Baldi, P. Sadowski, "A theory of local learning, the learning channel, and the optimality of backpropagation" | META (cited in Perin26) | THEORY Thm 12 | Backward channel is necessary |
| Cammarata26 | N. Cammarata, "Neural Networks Are Already Clean", Goodfire essay, 15 Oct 2026 | Opening "Short Version" read from the primary source; remainder keyword-scanned only | Review §3b, H-D | Neuron-level legibility; recursive generalization; width claim |
| Abate19 | C. Abate, R. Blanco, Ș. Ciobâcă, A. Durier, D. Garg, C. Hrițcu, M. Patrignani, É. Tanter, J. Thibault, "Trace-Relating Compiler Correctness and Secure Compilation", arXiv:1907.05320 / ACM TOPLAS (2021) | ABSTRACT (arXiv abstract + web search summary) | Review §3, §3c, S07 | Prior art for relation-indexed certified translation |
| SEP-SR | Stanford Encyclopedia of Philosophy, "Structural Realism" | Introduction and Newman passage read | THEORY §3.4 correction | Newman's objection |
| SEP-ScR | Stanford Encyclopedia of Philosophy, "Scientific Realism" | Underdetermination / Duhem passage read | THEORY §3.4, S02b | Auxiliary assumptions |
| SEP-Comp, SEP-Cat | Stanford Encyclopedia of Philosophy, "Compositionality", "Category Theory" | Introductions + web search synthesis (functorial semantics, topos $\Omega$) | Charter §17, Review §3c | Categorical functoriality baseline |
| Smith10 | B. Smith, W. Ceusters, "Ontological realism: A methodology for coordinated evolution of scientific ontologies", Applied Ontology 5(3–4), 139–188, 2010 | ABSTRACT / summary verified via search | Charter §17, Review §3c | Universals/particulars separation vs schemas |
| ObsCalculi15 | M. Schmidt-Schauß, D. Sabel, J. Niehren, J. Schwinghammer, "Observational program calculi and the correctness of translations", TCS 577, 98–124, 2015 | ABSTRACT / summary verified via search | Charter §17, Review §3c | Prior art for observational translation correctness |
| Fritz20 | T. Fritz, "A synthetic approach to Markov kernels, conditional independence and theorems on sufficient statistics", Adv. Math. 370, 107239, 2020 (arXiv:1908.07021) | ABSTRACT / summary verified via search | Review §3c, Theory §17 | Markov categories & synthetic sufficiency baseline |
| Ramdas23 | G. Shafer, V. Vovk, A. Ramdas et al., Game-theoretic statistics, anytime-valid e-values, and Safe Anytime-Valid Inference (SAVI) / Ville's inequality | Web search summary verified (arXiv survey + papers) | Review §3c, Theory §19 | Anytime-valid sequential e-processes & betting |
| CompCertDoc | CompCert documentation, version 3.18 (2026-08-31) | Index page read | Review §3 | Benchmark for verified translation |
