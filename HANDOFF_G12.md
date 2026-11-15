# HANDOFF G12 — Primary-Source Spot-Check of Literature Flags (+ `75caa33` Supplemental Refs)

**Branch:** `gemini/G12` (cut cleanly from `cb37616`)
**Scope:** Spot-check verbatim quotations and exact paper locations in `charter/LITERATURE_REVIEW.md` §5 for the three unverified critical flags from `HANDOFF_G7.md` (`arXiv:2602.16823`, `arXiv:2507.08802`, `arXiv:2006.15191`), plus carry forward the 10-reference supplemental audit (`75caa33`) onto `cb37616`. No frozen files (`THEORY.md` §5, `claims/GAPS.json`, `claims/REGISTER.md`, `experiments/FROZEN.json`) were modified, and no `Pnnn` claim IDs were assigned.

---

## Flag Corrections & Clarifications First

Checking the primary LaTeX sources (`iclr2026_conference.tex`, `main.tex`, `sample.tex`, `appendices.tex`) surfaced two location/hypothesis inaccuracies in `HANDOFF_G7.md` (and `charter/LITERATURE_REVIEW.md` / `charter/PRIOR_ART.md` / `claims/PROPOSED.md`):

1. **`arXiv:2006.15191` (Mingard et al., JMLR 22, 2021) — Section/Appendix Location & Macro Clarification:**
   - **Correction:** `HANDOFF_G7.md` (Item 5) cited `appendices.tex §E L724–726` for the 20% label-corruption comparison (`GP 5.80% vs SGD 13.4%`) and `§G` for 7-bit Boolean nets. In `appendices.tex`, line `683` (`%\section{Further results for randomised labelling on MNIST}\label{app:rand_label}`) is **commented out**, so `fig:appendix_corrupted_mnist` (`L719–730`) compiles inside **Appendix D** (`\section{Further results comparing \popt to \pb}`, `\label{appendix:further_results}`, `L487`), immediately *before* **Appendix E** (`app:CSR`, *Critical Sample Ratio*, `L732`). The 7-bit Boolean networks (`L762–768`) are in **Appendix F** (`app:bool_func`).
   - **Primary-text location:** The same 20% MNIST label-corruption result also appears in the main paper at **Section 5** (`\label{sec:heuristic_arguments}`, `fig:random` caption, `sample.tex` `L731–732`). Note also that `2006.15191`'s macro `\eg` expands to `\langle \epsilon_G \rangle` (`sample.tex` `L103`) and that the experiment uses a 2-layer 1024-wide FCN on **MNIST with MSE loss, `10,000` train / `50` test, and `20%` randomised training labels** (whereas the Appendix F 7-bit Boolean experiment tests uncorrupted data on `32/128` inputs).
   - Fixed in `charter/LITERATURE_REVIEW.md` §5 (L144), `charter/PRIOR_ART.md` §1, and `claims/PROPOSED.md` (`G12-1`).

2. **`arXiv:2507.08802` (Sutter et al., 2025) — Section & Full Five-Assumption List:**
   - **Clarification:** `theorem:existing_causalmap_for_any_algorithm` appears in **Section 4** (`\section{Unbounded Abstractions are Vacuous}`, `\label{sec:main_theorem}`, `main.tex` `L579–581`). `HANDOFF_G7.md` (Item 4) abbreviated the hypotheses to *"layer-injective, output-surjective task-solving network"* and omitted two explicit formal hypotheses stated in `main.tex` `L562–576`: **`assumption:Countable_infinite`** (countable input-space $\mathcal{X}$) and **`assumption:minimalrequirements`** (matchable partial-orderings between $\mathcal{A}$ and $\mathcal{N}$), and summarized the conclusion loosely rather than `"input-restricted distributed abstraction"`.
   - Fixed in `charter/LITERATURE_REVIEW.md` §5 (L155) and `claims/PROPOSED.md` (`G12-1`).

3. **`arXiv:2602.16823` (Hadad, Katz & Bassan, ICLR 2026) — Confirmed Verbatim:**
   - `lem:blocking_sets_equivalence` and `mhs_main_theorem_appendix` match `HANDOFF_G7.md` accurately and appear in **Appendix B** (`\label{app:proofs}`), **Subsection B.7** (`\label{app:proof_of_prop_mhs_duality}`, `iclr2026_conference.tex` `L2769–2791`).

---

## Verbatim Quotations & Locations (`charter/LITERATURE_REVIEW.md` §5)

### 1. Hadad, Katz & Bassan (`arXiv:2602.16823` / ICLR 2026)
- **Location:** **Appendix B** (`\section{Proofs of Main Results}`, `\label{app:proofs}`), **Subsection B.7** (`\subsection{Proof of Proposition~\ref{mhs_main_theorem_appendix}}`, `\label{app:proof_of_prop_mhs_duality}`), `iclr2026_conference.tex` `L2769–2791`.
- **Verbatim (`lem:blocking_sets_equivalence`, `L2786–2791`):**
  > `Under a monotone predicate \Phi, the set of circuit blocking sets with respect to G coincides exactly with the sets whose removal breaks faithfulness of the full model, i.e., C' \subseteq G is a blocking set if and only if \neg \Phi(G \setminus C', G).`
- **Verbatim (`mhs_main_theorem_appendix`, `L2769–2772`):**
  > `Given some model f_G, and a monotonic predicate \Phi, the MHS of all circuit blocking-sets concerning \Phi is a cardinally minimal circuit C for which \Phi(C, G) is true. Moreover, the MHS of all circuits C\subseteq G for which \Phi(C, G) is true, is a cardinally minimal blocking-set w.r.t \Phi.`

### 2. Sutter, Minder, Hofmann & Pimentel (`arXiv:2507.08802`, 2025)
- **Location:** **Section 4** (`\section{Unbounded Abstractions are Vacuous}`, `\label{sec:main_theorem}`), `main.tex` `L560–581` (theorem at `L579–581`).
- **Verbatim (`theorem:existing_causalmap_for_any_algorithm`, `L579–581`; macros `\alg = A`, `\dnn = N`):**
  > `Given any algorithm \alg and any neural network \dnn such that \cref{assumption:injectivity,assumption:Countable_infinite,assumption:surjectivety,assumption:minimalrequirements,assumption:dnnalgsolve} hold, we can show that \alg is an input-restricted distributed abstraction of \dnn.`
- **Supporting text (`L562–576`, `Abstract` `L207`):** The five cited assumptions are countable input-space (`assumption:Countable_infinite`), input-injectivity in all layers (`assumption:injectivity`), strict output-surjectivity in all layers (`assumption:surjectivety`), matchable partial-orderings (`assumption:minimalrequirements`), and solving the task `f^*` (`assumption:dnnalgsolve`); `Abstract` `L207` states `"under reasonable assumptions, \emph{any} neural network can be mapped to \emph{any} algorithm, rendering this unrestricted notion of causal abstraction trivial and uninformative"`.

### 3. Mingard, Valle-Pérez, Skalse & Louis (`arXiv:2006.15191` / JMLR 22, 2021)
- **Locations:**
  - **Main text Section 5** (`\label{sec:heuristic_arguments}`, Figure caption `\label{fig:random}`), `sample.tex` `L731–732` (note source caption repeats `(b)` twice).
  - **Appendix D** (`\section{Further results comparing \popt to \pb.}`, `\label{appendix:further_results}`, Figure caption `\label{fig:appendix_corrupted_mnist}`), `appendices.tex` `L723–726` (compiled in Appendix D because `L683` `%\section` is commented out, right before Appendix E `app:CSR` at `L732`).
- **Macros (`sample.tex` `L95–103`):** `\eg = \langle \epsilon_G \rangle`, `\pb = P_{\textrm{B}}(f|S)`, `\psgd = P_{\textrm{SGD}}(f|S)`.
- **Verbatim (`sample.tex` §5 `fig:random`, `L731–732`):**
  > `(b) $\psgd$ v.s.\ $\pb$ on MNIST with a 2-layer 1024 node wide FCN with MSE loss, test set size 50, and 20\% of the training labels randomised ($\eg_{SGD}=13.4\%$ and $\eg_{GP}=5.80\%$). ... Let $F$ be the set of functions found by both the optimiser and under GP sampling. Then $\sum_{f\in F}\pb=99.3\%$, and $\sum_{f\in F}\psgd=24.3\%$.`
- **Verbatim (`appendices.tex` Appendix D `fig:appendix_corrupted_mnist`, `L723–726`):**
  > `(c) $\pb$ v.s. $\psgd$ for 20\% corruption (as \cref{fig:random}(c), but included for ease of comparison). ($\eg=13.4\%$ for SGD and $\eg_{GP}=5.80\%$ for the GP). Here we included functions with frequency $<10$. $n=10^5$ ... Here $\sum_{f\in F}\pb=99.3\%$, and $\sum_{f\in F}\psgd=24.3\%$, indicating that while SGD finds almost all functions with high $\pb$, it also finds many functions with low $\pb$.`

---

## Supplemental References Carried Forward (`75caa33` -> `gemini/G12`)

Replayed the post-merge supplemental audit commits from `origin/gemini/G7` (`75caa33`, originally committed after `4ea4f35` was merged to `cb37616`) cleanly onto `cb37616`:
- `charter/LITERATURE_REVIEW.md`: updated Rosas `2512.00984` row (`L168`) with the published *Science Advances* journal version (`10.1126/sciadv.aeh0773`) and added 9 rows (`L193–201`) covering `2210.10749` (Krohn–Rhodes shortcuts), `2611.17309` (`CRAM` Potts energy descent), `2611.14418` (`AUC 0.93` bit-escalation hardware bound), `2611.14413` (`C_4` cyclic orbit averaging), `WSP-Gym` (weight-space repair vs random-edit negative control), Montalbán (`CSTpart1.pdf`) & Downey–Melnikov (Springer 2026 `Theorem A` / `Theorem B` effective Stone duality), `2601.06002` (`0` formal theorems), `alphaXiv:2611.latent-feedback-transformers-scaling-law` (`Abstract only`), and `2609.12303` / `2611.16267` (`Causals`).
- `charter/PRIOR_ART.md`: updated §5 to reflect the 6th area summary across lines `164–201`.
- `claims/PROPOSED.md`: added `# Proposed Claims & Literature Corrections — Branch gemini/G12` at the bottom (`G12-1` and `G12-2`).

---

## Rule 7 Acceptance Checks

- **`python -m cerp.register check`:** `0 problem(s), 33 status note(s); report: claims\LEDGER_CHECK.md` (`EXIT=0`).
- **`python -m cerp.status --check`:** `EXIT=0`.
- **`python -m pytest -q` (`$env:TEMP\semplex_extras_venv\Scripts\python.exe`):** `158 passed, 1 failed in 969.22s (0:16:09)`. The single failure is `tests/test_lean.py::test_proof_files_compile_and_use_only_standard_axioms`, which hit its `600s` per-subprocess timeout in `tests/test_lean.py:75` while compiling `Bounds.lean` (`Cerp.lean` and `Theory.lean` passed inside that test). Verified separately (`task-4072`: `1 failed, 8 deselected in 689.58s` hitting the same `600s` `Bounds.lean` subprocess timeout).
- **Standalone Lean 4.12 compilation & axiom audits (no `sorryAx`, no `Lean.ofReduceBool`):**
  - `Cerp.lean`: `EXIT=0` (`64.52s`)
  - `Theory.lean`: `EXIT=0` (`31.76s`)
  - `Bounds.lean`: `EXIT=0` (`650.85s` — `> 600s` explains the pytest subprocess timeout on this 8 GB host; no Lean file was modified in `G12`)
  - `Audit.lean`: `EXIT=0` (`3.28s`) — standard axioms only
  - `AuditTheory.lean`: `EXIT=0` (`2.56s`) — standard axioms only
  - `AuditBounds.lean`: `EXIT=0` (`1.97s`) — standard axioms only
