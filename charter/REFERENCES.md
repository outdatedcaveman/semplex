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
| Leroy09 | X. Leroy, "Formal verification of a realistic compiler", CACM 2009 | MEMORY (charter reference) | Charter | Verified compilation |
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
