# Bibliography, with verification status

Charter §13 forbids citing anything that has not been checked against a source. Each entry below records **what was verified, how, and what is still open**. These checks were made on 2026-11-06 through the Consensus index (Semantic Scholar / OpenAlex metadata plus abstracts). Crossref was not reachable from this environment.

**Status key:**
- **META+REL**: title, authors, year and venue found in the index, *and* the abstract confirms the specific claim we rely on.
- **META**: metadata found only.
- **DISCREPANCY**: the index disagrees with the commonly cited record; to be resolved against the publisher.
- **UNVERIFIED**: not checked this session.

| Used in | Reference | Status | Notes |
|---|---|---|---|
| S01 (ROBDD canonicity) | R. E. Bryant, "Graph-Based Algorithms for Boolean Function Manipulation", *IEEE Transactions on Computers* — [index entry](https://consensus.app/papers/details/b7e6604e6abe5c0c8121859a0c8affcc/?utm_source=claude_desktop) | **DISCREPANCY** + REL | Abstract confirms the ordered-variable DAG representation and its efficiency profile. The index lists **1989**; the paper is commonly cited as **1986, vol. C-35(8), pp. 677–691**. Resolve against IEEE Xplore before formal citation |
| S01 F6, S02b (don't-care simplification) | O. Coudert, J. C. Madre, "A unified framework for the formal verification of sequential circuits", *ICCAD 1990* — [index entry](https://consensus.app/papers/details/90f642546d57555399339ec9ea317a1b/?utm_source=claude_desktop) | **META+REL** | Abstract explicitly presents the "constrain" and "restrict" operators. Page numbers not verified |
| S01 F9 (sufficient sets = reducts) | A. Skowron, C. Rauszer, "The Discernibility Matrices and Functions in Information Systems", 1992 — [index entry](https://consensus.app/papers/details/7d3e021bb1f85f1e8ee4a3fed3001099/?utm_source=claude_desktop) | **META+REL** | Abstract confirms discernibility matrix/function → reducts. Index gives no venue; it is commonly cited as a chapter in *Intelligent Decision Support* (Słowiński, ed.), Kluwer, 1992. **Venue and pages unverified** |
| S01 F9 (rough sets) | Z. Pawlak, "Rough sets", 1982 | **UNVERIFIED** | The 1982 journal article was not found in the index. The index has Pawlak's 1982 ICS PAS report, "Rough sets. Algebraic and topological approach" ([entry](https://consensus.app/papers/details/a46f5c1e94cd507c8d10bfc30d8aee96/?utm_source=claude_desktop)), and Pawlak & Skowron, "Rudiments of rough sets", *Inf. Sci.* 2006 ([entry](https://consensus.app/papers/details/9cfd4ca63b77522ca0006481bed7e660/?utm_source=claude_desktop)). Cite the 2006 survey until the original is checked |
| S02 F2 (Satterthwaite tail) | F. E. Satterthwaite, "An approximate distribution of estimates of variance components", *Biometrics (Bulletin)*, 1946 — [index entry](https://consensus.app/papers/details/324ffd5f29ea52159f59a28728074ca6/?utm_source=claude_desktop) | **META** | No abstract in the index. Later work in the index describes the method as a scaled χ² approximation, which is how we use it. Note: that same work reports the approximation is *biased downward for small component df*, which is relevant to our B=30 bootstrap moments. → Q-A1 |
| S02, S02b (observational equivalence of causal models) | T. Verma, J. Pearl, "Equivalence and Synthesis of Causal Models", 1990 — [index entry](https://consensus.app/papers/details/40d31f10fb0153689c0932c37f19a57b/?utm_source=claude_desktop) | **META+REL** | Abstract: "two causal models are equivalent if there is no experiment which could distinguish one from the other"; canonical representation; extension to models with hidden variables. Supports Spike 02 F1. Venue in the index: *Probabilistic and Causal Inference* (UAI proceedings commonly cited); verify |
| S03 F3 (RUP/DRAT checking cost) | N. Wetzler, M. Heule, W. Hunt, "DRAT-trim: Efficient Checking and Trimming Using Expressive Clausal Proofs", 2014 — [index entry](https://consensus.app/papers/details/b3c5cd38166157399192ee352a3da37e/?utm_source=claude_desktop) | **META+REL** | Abstract: "Checking time of a proof is comparable to the running time of the proof-producing solver". This **independently corroborates Spike 03 F3**. Venue (SAT 2014) unverified |
| S03 Q-C1 (LRAT) | F. Pollitt, M. Fleury, A. Biere, "Faster LRAT Checking Than Solving with CaDiCaL", 2023 — [index entry](https://consensus.app/papers/details/b829ec3fddf05080bfed9436c348cdf0/?utm_source=claude_desktop) | **META+REL** | Abstract: DRAT checking "often takes even more time than solving"; LRAT is "way more efficient to check". This supports the Q-C1 direction. Author list beyond the first is from memory; verify |
| S05 F2 (testing equivalences) | R. De Nicola, M. Hennessy, "Testing Equivalences for Processes", *Theoretical Computer Science*, 1984 — [index entry](https://consensus.app/papers/details/fd17e7b9184d5f4c9e97f6a479378cff/?utm_source=claude_desktop) | **META+REL** | Abstract confirms three test-induced equivalences. The *specific* claim that must-testing coincides with failures equivalence is not stated in the abstract. **Relevance partially verified** |
| S05 F3, charter §1.3 | M. Hennessy, R. Milner, "Algebraic laws for nondeterminism and concurrency", *J. ACM*, 1985 — [index entry](https://consensus.app/papers/details/a7f9081fb1a75bd490e87766ca7ef5c2/?utm_source=claude_desktop) | **META+REL** | Abstract: the meaning of a nondeterministic program "cannot be presented naturally as an input/output function"; meaning is defined by observation congruence across contexts. This is exactly Spike 05 F1/F3 |
| S02b (DAG counts 543 / 29,281) | OEIS A003024 (labelled DAGs) | **UNVERIFIED externally** | Our enumerator reproduces these numbers, but that is not an independent check |
| Charter §17 | Leroy 2009 (CompCert) and other charter references | **UNVERIFIED** | Not re-checked this session |

## Lessons

- **Two corroborations, one discrepancy, one partial.**
  - DRAT-trim's own abstract matches our measured check ≈ solve cost.
  - Hennessy–Milner's abstract matches the F1 result that I/O semantics is inadequate under nondeterminism.
  - The Bryant year needs resolving.
  - The De Nicola–Hennessy claim about failures equivalence needs the full text.
- **Index metadata is itself evidence with a warrant, not ground truth.** The Bryant year discrepancy is a small live example of the charter's point that sources have reliability profiles.
