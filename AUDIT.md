# Project audit — 2026-11-17

Scope: everything on `master` at `1d45552` (my Spikes 01–10c plus the nine commits made
from the other sessions: Ur-Compiler, Lean §§14–19, `Bounds.lean`, Spikes 11–16, handoff).
Method: every Python module read or diffed; Lean files compiled and axiom-audited; full
test suite run with Lean (`130 passed, 1 failed` before any change); `pyflakes` over all code;
each suspected bug reproduced before being called a bug.

Part 1 explains how the project fits together and where it can break. It was written and
committed before any code was changed. Part 2 lists the findings. Part 3 records what was fixed.

---

## Part 1 — How everything connects

### 1.1 The one idea the code is built around

Every claim the project makes is supposed to carry a **warrant**: what kind of evidence backs
it, which code you have to trust, and which assumptions it rests on. Code that *searches*
(solvers, translators, compilers, trainers) is untrusted. Only a few small *checkers* can mint
the strong warrants, and the ledger refuses a strong status without a token that only those
checkers can produce.

```
                   UNTRUSTED (may be wrong; never believed on its own say-so)
  ┌──────────────────────────────────────────────────────────────────────────────┐
  │ translate / bdd / substrates   sat.py (CDCL)        atlas / netsolve (CP-SAT) │
  │ pipeline / sufficiency         ur_compiler.py       train / learnrules /      │
  │ epistemics/* (EM, inquiry)     csir exporters       localrules (JAX)          │
  └───────────────┬───────────────────────┬───────────────────────┬──────────────┘
                  │ artifacts + claims    │ certificates          │ measurements
                  ▼                       ▼ (RUP / LRAT / cuts)   ▼
  ┌─────────────────────────────┐ ┌──────────────────────────┐ ┌──────────────────┐
  │ TRUSTED PYTHON KERNELS      │ │ LEAN 4.12 KERNEL         │ │ statistics       │
  │ kernel.py  kernel_lts.py    │ │ Cerp.lean   (deciders,   │ │ (bootstrap tests │
  │ kernel_bounds.py            │ │   RUP, LRAT, TNode)      │ │  in epistemics/) │
  │ stdlib only, own evaluators │ │ Theory.lean (PFT thms)   │ │                  │
  │ mint Verdict(token)         │ │ Bounds.lean (lower bds)  │ │                  │
  └──────────────┬──────────────┘ └────────────┬─────────────┘ └────────┬─────────┘
                 │ Verdict                     │ LeanCheck (via lean_bridge.py:
                 │                             │  axiom audit + round-trip render)
                 ▼                             ▼                        ▼
  ┌──────────────────────────────────────────────────────────────────────────────┐
  │ ledger.py   Warrant = (basis ⊆ Method, trusted_base, conditions)             │
  │             refuses KERNEL_CHECKED without an authentic Verdict,             │
  │             refuses PROOF_ASSISTANT without an authentic LeanCheck           │
  └───────────────────────────────────┬──────────────────────────────────────────┘
                                      ▼
  ┌──────────────────────────────────────────────────────────────────────────────┐
  │ csir.py  bundle = nodes (artifacts) + links (relation, protocol,             │
  │          certificate, warrant).  validate() = shape only.                    │
  │          recheck() = re-verify every "kernel-checked" link FROM THE BUNDLE.  │
  └──────────────────────────────────────────────────────────────────────────────┘
                                      ▼
         claims/REGISTER.md  ·  THEORY.md  ·  experiments/SPIKE_*_REPORT.md
         (human-level record; must agree with what the code and Lean actually show)
```

The weak joint: **CSIR links and the register are plain data/text.** The ledger enforces
warrants in memory, but anything written straight into a CSIR link dict or a markdown file
is only as honest as whoever wrote it. `recheck()` is the only automatic guard, and it can
only re-verify relations that have a kernel route.

### 1.2 The five pipelines

```
(A) F0 — finite Boolean functions (Spikes 01, 03, 06)
    source expr ──translators──► circuit / dfa / bdd / expr'
         │                              │
         └──── claim {left,right,vars} ─┴──► kernel.check (exhaustive, n ≤ 16)
                                         └─► sat.prove_equivalence ──RUP──► kernel.check_rup
                                         └─► lean_bridge.prove_expr_claim / prove_cnf_unsat
                                               └─► Lean: decideEquiv_correct / unsat_of_certificate

(B) Epistemics — hidden causal worlds (Spikes 02, 02b, 13, 14)
    world.Interface ──samples──► inquiry.inquire ──EM fit──► rival ontologies
         ▲ (agent may not import world truth)        │
         └──── chooses interventions by EIG ◄────────┤ calibrated adequacy (bootstrap)
                                                     ▼
                         ledger: EMPIRICAL / CONJECTURE / retractions
                         csir.from_inquiry, csir.distill_causal_rule ──► F0 circuit (A)

(C) Atlas — periodic table of threshold circuits (Spikes 08, 08b, 11, 16)
    atlas.build_all(4) ──(pickle cache atlas/.cache)──► Table per n
         │ exact min neurons + witness nets            │
         ├─► kernel.check (tnet witness ≡ function)    ├─► compile_task (lookup)
         ├─► kernel_bounds (not-threshold certificates; Lean: Bounds.lean soundness)
         └─► netsolve (OR-Tools CP-SAT) for skip/ReLU/depth families; crunch.py overnight jobs

(D) Learning (Spikes 09, 10b, 10c, 11, 13, 16)
    train.py (n=4) / learnrules.py (general n) / localrules.py (rule dictionaries, JAX, CEM)
         └─► compare learned functions/units against atlas optima (C) and Theorem 12 (Lean)

(E) Ur-Compiler (Spikes 12, 15, 16) — ur_compiler.compile_unified(spec)
    spec.kind ∈ {f0, lts, stochastic_lts, continuous, causal}
       f0 ──► compile_profile_factored
                n ≤ 14: dense truth table ─► best split (S1,S2) by profile rank r
                          encoders π_j : S1→bit  ─┐ recurse to ≤4-input leaves
                          decoder  g : (π,S2)→bit ┘   leaves = BDD expr + atlas net
                n > 14: sampled S2 probes, optional SAT-CEGAR on expr_ast
              ─► composed expr + DAG circuit + composed threshold_net
              ─► optional certify_lean: sat.*_lrat ─► lean_bridge.verify_*_lrat ─► Lean
       lts / stochastic_lts ─► one F0 problem per next-state bit and output bit
              (shared encoder across outputs) ─► CSIR bundle
       continuous ─► quantize [0,1]^d to bits ─► f0
       causal ─► csir.distill_causal_rule (B→A)
```

### 1.3 The Lean side

```
Cerp.lean   Expr, eval, decideEquiv (+correct), decideTask (+correct),
            CNF, RUP checker (unsat_of_certificate),
            Tseitin encoder (+sound,+complete) ─► tseitinMiter_unsat_implies_equiv
            LRAT checker ─► tseitinMiter_lrat_unsat_implies_equiv
            TNode / evalTNet, pbToExpr (O(2^fan-in)) ─► tseitinTNetMiter_lrat_unsat_implies_equiv
Theory.lean §1–10  PFT theorems 1–12 + symmetry-gap core (§10)
            §11–16 (+12b,13b,13c,14b) C1–C5 partial results, profile-factor compilation
            §17 FrameHom pullbacks, lossy-composition counterexample
            §18 finite Markov-kernel TV contraction
            §19 "pragmatic" equivalence, finite optional stopping, Ville bound
Bounds.lean not-threshold certificate soundness; parity3/parity4 not two halfspaces
Audit*.lean #print axioms for each audited theorem  ──► test_lean.py enforces
            ⊆ {propext, Quot.sound, Classical.choice}, no sorryAx
lean_bridge.py  writes a Claim.lean per concrete claim, runs lean, parses axioms,
            and checks that Lean's rendering of the terms equals ours (round trip)
```

### 1.4 Where it can break

Numbered so Part 2 can refer back.

| # | Joint | How it breaks | What guards it today |
|---|---|---|---|
| J1 | Untrusted code writes a CSIR link with `basis: kernel-checked` | Link claims a check that never ran | `validate()` only requires *some* certificate; `recheck()` reports "no kernel route" but nothing fails |
| J2 | Lean certificate compares the wrong two things | Proof is valid but proves something other than "compiled = spec" | Nothing; only reading the call site |
| J3 | Soundness labels on the Ur-Compiler (`exact` / `cegar-sat` / `sampled`) | Label says stronger than what was checked (timeouts, unpropagated child labels) | Nothing automatic |
| J4 | Caches (`atlas/.cache/*.pkl`, Lean `.olean` by source hash) | Stale cache silently used after source changes | Lean cache keyed by hash; **atlas cache keyed only by `m_max`** |
| J5 | Python ↔ Lean translation (`expr_to_lean`, `tnet_to_lean`) | Lean checks a different term than intended | Round-trip render for `Expr`; **none for `TNode` lists** |
| J6 | Bit-order conventions (atlas: var 0 = LSB; TruthTable: MSB-first; kernel table: `sum x_j<<j`) | Silent permutation of inputs | Exhaustive comparisons in tests |
| J7 | Randomized tests (JAX training, CEM) | Assertions on single noisy draws fail or pass by luck | Fixed seeds, which do not transfer across platforms |
| J8 | Markdown claims (REGISTER, THEORY, HANDOFF, README) vs code/Lean | Text drifts from what is proved or measured | Manual review only |
| J9 | Environment (deps, Lean path, OS) | Missing optional deps make tests error rather than skip; Windows paths in docs | `CERP_LEAN` skip for Lean only |

---

## Part 2 — Findings

Tags: **B** broken (wrong behaviour or false output), **I** inconsistent (text ≠ code/proof, or
code ≠ code), **E** inefficient, **N** no longer needed. Status column is filled in Part 3.

### Broken

| id | Where | Finding | Evidence |
|---|---|---|---|
| B1 | `tests/test_localrules.py::test_search_keeps_a_working_rule_working` | Fails on every run here (`0.875 < 0.9`). Not flaky: the assertion tests one random draw of the *loss*-best candidate's fit, which pure backprop itself misses (P076: min 0.875). The property the test is named for, "the search keeps backprop working", is never compared against backprop. | Full run, J7 |
| B2 | `ur_compiler._lean_certify_equiv` | With no `reference_expr`, the reference is computed **from the compiled expression itself**, so the Lean certificate proves `compiled ≡ BDD(compiled)`, a near-tautology, not `compiled ≡ spec`. `certify_lean=True` on `f0`/`continuous` therefore certifies nothing about the specification. | Code path; J2 |
| B3 | same | With `n > 12` and no reference, returns `ok: True, status: "unsat"` without running any check. | Code path; J3 |
| B4 | `ur_compiler._sat_cegar_refine_split` | A SAT **timeout** is treated as "equivalent", so the split can be labelled `cegar-sat` without proof. | Only `status == "sat"` is handled; J3 |
| B5 | `compile_unified` kinds `lts`, `stochastic_lts` | Every `distills` link claims `basis: kernel-checked` with an `exhaustive` certificate, but nothing was checked and `csir.recheck` answers "no kernel route" for all of them. The spec node does not even contain the transitions. | Reproduced; J1 |
| B6 | `compile_multi_profile_factored` | Output soundness label ignores the decoder's own label; for wide inputs a sampled decoder can sit under a label that does not say so. | Code path; J3 |
| B7 | `atlas.build_all` cache | Pickle cache is keyed only by `m_max`; after any change to `atlas.py` the old tables (the basis of every "optimal" claim) are silently reused. | Code path; J4 |
| B8 | `HANDOFF_CLAUDE.md`, `experiments/SPIKE_16_REPORT.md` | Links point to `file:///C:/Users/bruno/...`; broken for anyone else and on GitHub. | grep |
| B9 | `pyproject.toml` | Declares only `numpy`; tests and experiments also need `ortools`, `jax`, `pytest`, and Spike 14b needs `scikit-learn`. *(Correction after checking: the tests already `importorskip` jax and netsolve, so they skip cleanly; only the declared dependencies were wrong.)* | J9 |

### Inconsistent

| id | Where | Finding |
|---|---|---|
| I1 | `Theory.lean` §19 docstring, P073, THEORY §7.3, HANDOFF | Text says pragmatic equivalence "equals"/"coincides with" observational determinacy "when interp is faithful". The theorem has no faithfulness hypothesis and proves one direction only (pragmatic determination ⇒ representamen determination), plus the existing duality. |
| I2 | `THEORY.md` Prop 14 vs `Theory.lean` | THEORY says "[paper proof]"; Lean has its core as `even_span_excludes_odd`, labelled "Theorem 13". |
| I3 | `THEORY.md` §6 | Says "C1 and C3 are open" after §5 lists Lean results for both. |
| I4 | `README.md` | Stops at Spike 10b; says "11 theorems"; layout omits `ur_compiler`, `Bounds.lean`, `kernel_bounds`, `netsolve`, training modules; install line lacks `jax`. |
| I5 | `ROADMAP.md` | Mixed done/proposed rows; duplicate numbers (09, 10, 11, 12 reused); "(old 10b)", "(old 10c)", "08c" superseded; LRAT, Spike 12 bridge and first real case study are done but listed as proposed. |
| I6 | `proofs/lean/README.md`, `*_CHECK_LOG.txt` | README says Theory = "Theorems 1–11", Bounds = certificate soundness only; logs record 20/11/3 lines against 54/14/9 audited theorems. |
| I7 | `proofs/lean/Audit.lean` | `tseitinMiter_unsat_implies_equiv` (called by `lean_bridge.verify_expr_equiv_tseitin`), `tseitinEncode_sound`, `tseitinEncode_complete`, `tseitinTNetGo_complete` are cited but not audited. |
| I8 | `kernel.py`, `ledger.py`, `lean_bridge.py` docstrings | Kernel docstring cites a non-existent `tests/test_kernel_independence.py`, says it checks no certificates (it checks RUP), lists 4 of 7 artifact kinds. `Method.PROOF_ASSISTANT` says "(none yet)". Bridge says the Tseitin encoder is unverified; true for the RUP route, false for the LRAT routes. |
| I9 | `claims/REGISTER.md` P078, P076 | P078 says CP-SAT "establishes" a depth-3 vs depth-2 separation on parity5; the search bounds weights to \|w\| ≤ 4, so it is evidence, not a separation. P076 calls a deterministic test failure "flakiness". |
| I10 | `experiments/` | `spike16_results.json` sits outside `experiments/results/`; Spikes 12 and 15 have no report files although the register cites them. |
| I11 | `HANDOFF_CLAUDE.md` | Refers to `cerp/epistemics.py`; it is the package `cerp/epistemics/`. |
| I12 | `charter/REFERENCES.md` | New rows use verification levels outside the defined scale ("web search summary"); `Ramdas23` is a body of work, not one source. |
| I13 | `charter/LITERATURE_REVIEW.md` §3c | Claims a "genuine original niche". The components (TV data-processing inequality, Ville's inequality, optional stopping, a definitional "pragmatic" quotient) are classical; what is new is only their co-location in one Lean development. |
| I14 | `ur_compiler` kind `continuous` | `eps_bound = L·√d·2^-bits` has no stated meaning: grid points are `i/(2^bits−1)`, no input→grid map is defined, and a Lipschitz bound on `f` does not bound the error of the *thresholded* output near the threshold. |
| I15 | `lean_bridge.verify_threshold_net_equiv` | Round-trip check covers the spec expression only; the `TNode` list Lean checks is never compared with the Python net (J5). |
| I16 | `ur_compiler` field names | Composed nodes report a *sum of leaf optima* (an upper bound) under the key `atlas_min_neurons`. CSIR calls it `atlas_neuron_ub`. |

### Inefficient

| id | Where | Finding |
|---|---|---|
| E1 | `compile_unified` | `lts` and `stochastic_lts` branches duplicate ~90 lines. |
| E2 | `ur_compiler` | Dead code: `n <= max_leaf` branch after `n <= 14` return (unreachable for `max_leaf ≤ 14`); `(1 << (n1+n2)) <= 4096` branch unreachable when `n > 14`; first `x1_to_code` assignment in the multi-output path immediately overwritten; `candidates` list built and unused on that path. |
| E3 | `lean_bridge.version()` | Spawns `lean --version` on every check. |
| E4 | `sat.rup_to_lrat` | Rescans the whole clause database for every propagation: O(lemmas × clauses × propagations). Fine for tests; the bottleneck for larger LRAT proofs. |
| E5 | `csir.distill_causal_rule` | Scans the whole joint distribution for every feature row. Fine at current sizes. |
| E6 | `Cerp.pbToExpr` | O(2^fan-in) Shannon expansion; already Work Package A in the handoff. |
| E7 | `crunch.py` | Uses `__import__(...)` inside lambdas instead of a plain import. |

### No longer needed

| id | Where | Finding |
|---|---|---|
| N1 | various | Unused imports/variables (pyflakes: `pipeline`, `generate`, `geometry`, `lean_bridge` f-strings, `test_csir`, five experiment scripts). |
| N2 | `localrules.meta_learn`, `localrules.normalisation`, `learnrules.meta_learn_local` | Failed gradient meta-learning, superseded by `cem_search`; still imported by the Spike 10b scripts that regenerate published numbers. |
| N3 | `cerp/train.py` vs `cerp/learnrules.py` | `train.py` is the n=4 special case of `learnrules.py`; both are used by experiments. |
| N4 | `ROADMAP.md` | Superseded rows (see I5). |
| N5 | `decisions/ADR-0002` | "Revisit at 300 lines" trigger passed (kernel is ~470 lines). |

---

## Part 3 — What was changed

Test suite after the fixes, with Lean: **135 passed, 0 failed** (was 130 passed, 1 failed; 4 new
regression tests). All three Lean files compile; all 81 audited theorems use at most
`propext`, `Quot.sound`, `Classical.choice`, and none uses `sorryAx`. `pyflakes` is clean over
`cerp/`, `tests/` and `experiments/`.

### Fixed

| id | Fix | How it is checked |
|---|---|---|
| B1 | Test now compares the returned rule with backprop on the same 4 fresh networks (`found ≥ backprop − 0.05`, `backprop ≥ 0.85`). On those draws backprop scores 0.92, no learning 0.30, negated backprop 0.00, so the test still discriminates. | passes; P076 and THEORY §7.5 corrected |
| B2, B3 | `_lean_certify_equiv` takes the spec function and builds the reference from **it** (n ≤ 12), never from the compiled expression. With no spec it returns `ok: False, status: "no-reference"`. `compile_unified` passes `spec_fn` for `f0` and `continuous`. | `test_lean_certificate_needs_a_specification`; Lean test `test_lrat_miter_equiv_and_ur_compiler_certify_lean` still passes, now as a real spec check |
| B4 | SAT timeout returns `"unknown"`; the split keeps its `sampled(k)` label. | `test_cegar_timeout_is_not_a_proof` (fails on the old code) |
| B5, E1 | `lts` and `stochastic_lts` share `_compile_lts_steps`. Each output now has a kernel `table` node; links are `spec → table` (`distills`, basis `exact-uncertified`, the binary encoding stated as a condition), `table → expr` and `expr → net` (`extensional`, **kernel-checked when built**, exhaustive certificate). The spec node now contains the transitions. CSIR accepts every kind the kernel can evaluate (`F0_KINDS`, asserted equal to `kernel._EVAL`). `continuous` also kernel-checks its expr ↔ circuit link. | `test_lts_bundle_claims_only_what_the_kernel_rechecks`: all kernel-checked links re-verify from the bundle; flipping one table bit makes `recheck` report `FAILED` |
| — | New `threshold_net_to_dnet`: Ur-Compiler threshold nets are now checkable by the trusted Python kernel, not only by Lean. | `test_threshold_net_is_checked_by_the_python_kernel` |
| B6 | Multi-output soundness combines the split, decoder and encoder labels (`_combine_soundness`, also used by the single-output path). | code |
| B7 | Atlas cache file name includes a hash of `atlas.py`; older cache files are deleted when a new one is written. | rebuild observed after the edit |
| B8 | `file:///C:/...` links replaced by repository-relative links. | grep |
| B9 | `pyproject.toml` declares extras `solver`, `learning`, `data`, `test`; README install line updated. | — |
| I1 | Lean docstring, THEORY §7.3 and P073 now say what is proved: one direction, no faithfulness hypothesis, a corollary of Theorem 3. | Lean recompiled |
| I2 | THEORY Prop 14 cites its Lean core lemma; the Lean comment no longer calls it "Theorem 13". | — |
| I3 | THEORY §6: "C1 and C3 have partial Lean results but remain open in general". | — |
| I4 | README updated through Spike 16 and the audit; layout table lists every module. | — |
| I5, N4 | ROADMAP split into "Done (chronological)" and "Open"; duplicate and superseded rows removed; missing reports listed as open work. | — |
| I6 | `proofs/lean/README.md` updated; the three check logs regenerated from this run (18 + 54 + 9 lines). | — |
| I7 | `Audit.lean` now also audits `tseitinEncode_sound`, `tseitinEncode_complete`, `tseitinMiter_unsat_implies_equiv`, `tseitinTNetGo_complete`. | standard axioms only |
| I8 | Kernel, ledger and bridge docstrings corrected; the bridge docstring now lists, per route, exactly what is trusted. | — |
| I9 | P078 says "bounded-weight evidence, not a proof"; P076 says "deterministic, not intermittent". | — |
| I10 | `spike16_results.json` moved to `experiments/results/spike16_scale_and_coarsening.json` (script and report updated). Missing reports recorded in ROADMAP "Open". | — |
| I11 | `cerp/epistemics.py` → `cerp/epistemics/` in HANDOFF and ROADMAP. | — |
| E2 | Dead branches and assignments removed from `ur_compiler.py`; `_fn_from_expr` (now unused) removed. | — |
| E3 | `lean_bridge.version()` cached per binary. | — |
| E7 | `crunch.py` uses a plain lazy import. | — |
| N1 | Unused imports/variables removed in `cerp/`, `tests/`, `experiments/`. | `pyflakes` clean |

### Left for you to review

These are either judgment calls about the research, or changes I could not make safely
without your input.

1. **I13: novelty claim in `LITERATURE_REVIEW.md` §3c.** The "genuine original niche" combines
   classical results: the TV data-processing inequality, Ville's inequality (1939), finite
   optional stopping, and a definitional quotient. I would reword it to "new as one Lean
   development connected to running code" and drop "original mathematical niche".
   *Recommendation: reword.*
2. **I12: references.** `Ramdas23` names a body of work, not a source. "Web search summary" is
   not a level in the REFERENCES scale. *Recommendation: split into concrete papers (Ville 1939;
   Shafer–Vovk; Ramdas et al. on e-processes) and relabel them META or ABSTRACT.*
3. **I14: `continuous` eps_bound.** `L·√d·2^-bits` does not bound any stated error. Grid points
   are `i/(2^bits−1)`; there is no rule for mapping an input to a grid point; a Lipschitz bound
   on `f` says nothing about errors of `[f ≥ θ]` near θ. *Recommendation: define rounding to the
   nearest grid point, report the bound as "|f(x) − f(grid(x))| ≤ L·√d/(2(2^bits−1))", and stop
   calling it a classification error bound.* The adaptive subdivision itself is sound, given a
   true Lipschitz constant.
4. **THEORY §7.2 says the Markov-kernel theorems "ground" the `stochastic_lts` T-step bound.**
   The code's bound is `T·(1 − max p)` (a union bound over steps), which does not use the
   data-processing inequality. *Recommendation: connect them in Lean (coupling lemma), or
   say "motivates" instead of "grounds".*
5. **I15: net rendering is not round-tripped.** Lean checks a `TNode` list that is never
   compared with the Python net. Fixing it needs a `TNode.render` in `Cerp.lean` (small).
   Until then the Python-kernel check added here (`threshold_net_to_dnet`) is the independent
   cross-check. *Recommendation: add the render (WP-A territory).*
6. **I16: field name `atlas_min_neurons`** holds an upper bound on composed nodes (a sum of
   leaf optima). Renaming it changes test assertions and recorded JSON. *Recommendation:
   rename to `neuron_ub` in a separate commit.*
7. **E4: `sat.rup_to_lrat`** rescans the clause database for each propagation. It is the next
   bottleneck after `pbToExpr` for larger LRAT proofs. *Recommendation: use watched literals
   when WP-A starts.*
8. **E5: `csir.distill_causal_rule`** scans the full joint distribution per feature row.
   Fine now; marginalize once if models grow.
9. **N2: failed meta-learning code** (`localrules.meta_learn`, `localrules.normalisation`,
   `learnrules.meta_learn_local`). Superseded by `cem_search`, but the Spike 10b scripts that
   regenerate published numbers import it. *Recommendation: keep, and mark as historical.*
10. **N3: `cerp/train.py` overlaps `cerp/learnrules.py`** (n=4 special case). Both are used.
    *Recommendation: leave as is unless Spike 09 is rerun.*
11. **N5: ADR-0002's "revisit at 300 lines"** trigger has fired (kernel ~470 lines, plus two
    sibling kernels). The trusted base has grown with each spike. *Recommendation: write
    ADR-0005 that either accepts the size (each addition is a small, independent checker) or
    moves the newer checks behind Lean.*
12. **Missing reports** for Spikes 12, 13b, 14b and 15. Their numbers live only in the register
    and JSON.
13. **Earlier spike reports are not rewritten.** For example, `SPIKE_01_REPORT.md` says the
    kernel is 220 lines and `SPIKE_08_REPORT.md` predates the 08b/09 corrections. Reports are
    records of what was known then; corrections live in later reports and in the register.
