# G15 Handoff — Extending the `n = 5` Orbit Census Beyond `cost <= 3` (`gemini/G15`)

**Branch:** `gemini/G15` (cut from `origin/claude/practical-shannon-oqg60y` @ `7be5346`)
**Target:** Complete `100%` of `n = 5, cost <= 3` up to weight bound `|w| <= 4` (`54 + 11,487 = 11,541` NPN classes vs G9's partial `3,725/7,295` at `|w| <= 3` [`42 + 7,253`]), and extend the `n = 5` circuit & `G_f`-orbit census to **`cost = 4` (`|w| <= 3`)** using a bitset + `G_f`-symmetry exact enumerator, cross-checked against independent brute force (`enumerate_class_bruteforce`) and `W = 4` cost-collapse audits.

## Pre-Registered Scope & Criteria (Rule 5 — Committed Prior to Execution)

1. **`H15.1` (`n = 5, cost <= 3, |w| <= 4` completeness):** `enumerate_n5_cost_le3_parallel(W=4, workers=2, time_limit=900.0)` finishes all `11,541 / 11,541` NPN classes (`stopped_reason == "completed"`), preserving `n = 4` untouched (`222` classes, `65/222` unoriented 1-orbit, `15/222` oriented 1-orbit).
2. **`H15.2` (Exact symmetric `cost = 4` slice at `n = 5`):** Enumerate 100% of all `64` symmetric 5-variable Boolean functions reduced mod NPN (`<= 24` NPN classes), partition strictly into `cost 1`, `cost 3`, `cost 4 (W=3)`, and `cost >= 5 (W=3)`, compute exact unoriented and oriented orbit counts on every `cost = 4` symmetric class, and check whether any drop to `cost <= 3` when `|w| = 4` is permitted.
3. **`H15.3` (Deterministic general `cost = 4, |w| <= 3` stream):** Discover balanced general `cost = 4 (W=3)` NPN classes across all oriented `cost = 1` templates (`{AND3, AND_OR, MAJ3}` excluding `cost <= 3 (W=3)`, `max_general_discover = 1500`), process deterministically balanced-Hamming-weight first (`key = (-min(hw, 32-hw), rep)`) across `workers = 2` up to `time_limit = 900.0s` (with compact exact histograms in JSON for `>64` orbits), verifying `cost3_circuits_at_W == 0` and `num_circuits > 0` on every completed class, auditing `drops_to_cost3_at_W4`, and reporting exact stopping point/reason.
4. **`H15.4` (Brute-force & equivariance verification):** `_enumerate_cost4_circuits_for_rep_fast` matches `_enumerate_cost4_circuits_for_rep` on all `78` `n = 4, cost = 4` classes + `parity3` (`|w| <= 3`), and matches literal brute force `enumerate_class_bruteforce` on closed `n = 5, |w|_1 <= 2` (`92` LTFs) `cost = 3` (`5` classes) and `cost = 4` (`3` classes) samples.

*(Status: Benchmark executed AND full Rule 7 verified.)*

## Measured Results (`experiments/results/g15_orbits.json`)

### 1. Complete `n = 5, cost <= 3, |w| <= 4` (`100%` exhaustive under `W <= 4`)
- **Threshold basis:** `62,572` LTFs (`31,286` hyperplane pairs) at `|w| <= 4`, vs `32,812` LTFs (`16,406` pairs) at `|w| <= 3`.
- **NPN classes:** `11,541 / 11,541` completed (`54` `cost = 1`, `11,487` `cost = 3`; `discovery_seconds = 44.323s`, `total_seconds = 207.97s` on 2 workers, `stopped_reason = "completed"`).
- **1-orbit uniqueness fractions (`H15.1` HELD):**
  - Overall (`cost <= 3`): **`5,373 / 11,541` (`0.465558`)** unoriented 1-orbit; **`54 / 11,541` (`0.004679`)** oriented 1-orbit.
  - Non-trivial (`cost = 3` only, `11,487` classes): **`5,319 / 11,487` (`0.463045`)** unoriented 1-orbit (`1,135,708` unoriented circuits -> `380,170` orbits); **`0 / 11,487` (`0.0`)** oriented 1-orbit (`4,542,832` oriented circuits -> `1,517,291` orbits).

### 2. Exhaustive Symmetric `n = 5` Slice (`100%` of all `64` symmetric functions -> `20` NPN classes, `H15.2` HELD)
- Partition at `W = 3` (`and at W = 4`): **`4` `cost = 1`**, **`6` `cost = 3`**, **`6` `cost = 4` (`0 / 6` drop to `cost <= 3` at `W = 4`)**, **`4` `cost >= 5` at `W = 3`** (`0x16696996`, `0x16698116`, `0x16818168`, `0x69969669` [parity5]).
- Exact `cost = 4 (W = 3)` symmetric table (`2 / 6 = 0.333333` unoriented 1-orbit, `0 / 6` oriented 1-orbit):

| Rep (`hex`) | Weight Signatures | `|G_f|` (`np`) | Circuits (`u` / `o`) | Orbits (`u` / `o`) | Drops to `cost <= 3` at `W = 4`? |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `0x16686881` | `100100,110110,001001,011011` | `120 (120)` | **`1`** / `8` | **`1`** / `8` | `False` |
| `0x168181e8` | `101100,110010,001101,010011` | `120 (120)` | **`1`** / `8` | **`1`** / `8` | `False` |
| `0x1161669` | `101000,111010,000101,010111` | `120 (120)` | `6` / `48` | `2` / `16` | `False` |
| `0x16696997` | `110100,001011` | `240 (120)` | `6` / `48` | `2` / `8` | `False` |
| `0x177e8117` | `100110,011001` | `240 (120)` | `6,221` / `49,768` | `85` / `480` | `False` |
| `0x1168001` | `100010,101110,010001,011101` | `120 (120)` | `24,211` / `193,688` | `310` / `2,480` | `False` |

### 3. Deterministic Balanced-Weight General `n = 5, cost = 4, |w| <= 3` Slice (`H15.3`)
- **Discovery & coverage:** Discovered `1,500` general `cost = 4 (W = 3)` NPN classes across all oriented `cost = 1` templates (`discovery_seconds = 314.311s` including reference & symmetric slice); completed **`12 / 1,500`** balanced (`w = 16`) classes in `1,015.545s` before stopping cleanly at **`stopped_at_rep = "0x79bff"`**, **`stopped_reason = "time_limit_900.0s_at_general_idx_12_of_1500"`**. All `12` passed `cost3_circuits_at_W == 0` and `num_circuits > 0`.
- **Combinatorial explosion & 1-orbit drop:** Even restricted to `|w| <= 3`, single balanced `w = 16` `cost = 4` functions admit **`62,226` to `1,607,449`** minimal width-3 unoriented circuits (`6,521,189` unoriented / `52,169,512` oriented circuits total across 12 classes; **`0 / 12` (`0.0`)** 1-orbit unoriented or oriented).
- **Exact `W = 3 -> W = 4` weight-artifact finding:** **`6 / 12` (`50.0%`)** of these `W = 3, cost = 4` classes (`0x37dff`, `0x37eff`, `0x73dff`, `0x73eff`, `0x77bfb`, `0x797ff`) actually drop to `cost = 3` at `W = 4`, whereas **`6 / 12`** (`0x3dffd`, `0x67bff`, `0x69fff`, `0x6b7ff`, `0x6f9ff`, `0x76bff`) remain true `cost >= 4` against `W = 4` (with `0 / 6` 1-orbit).

## What This Does NOT Show

- **Full `n = 5` `cost = 4` completeness:** Only `12 / 1,500` discovered general `cost = 4 (W = 3)` classes finished within the `900s` worker cap due to `~10^5–1.6×10^6` minimal width-3 circuits per balanced `w = 16` class; the full `n = 5` `cost = 4` catalog (`>10^5` NPN classes) is computationally infeasible for exhaustive circuit-by-circuit enumeration without structural orbit-only counting.
- **Unrestricted `|w|` at `n = 5`:** Exhaustive `cost <= 3` holds under `|w| <= 4` (`62,572` LTFs), NOT all `94,572` `n = 5` LTFs (some `|w| >= 5` LTFs still omitted; hence `drops_to_cost3_at_W4` is a lower bound on true `cost = 3` collapse, and the `4` `cost >= 5 (W = 3)` symmetric functions are confirmed `cost >= 4` at `W = 4`, not proved `cost >= 5` at `W = 4`).
- **Lean formalization of `n = 5` orbit counts:** All `G15` enumerations are Python/NumPy empirical enumerations audited against brute force on closed subfamilies (`|w|_1 <= 2`, `92` LTFs) in `tests/test_g15_orbits.py`, not Lean kernel theorems (`proofs/lean/` unchanged).

## Rule 7 Verification (Observed Outputs)

- `python -m cerp.register check`: `exit=0` (`0 problem(s), 46 status note(s)`).
- `python -m cerp.status --check`: `exit=0`.
- `git diff origin/claude/practical-shannon-oqg60y -- proofs/lean/`: empty (`LEAN_DIFF_LEN=0`).
- Standalone Lean `v4.12.0` (`proofs/lean/` -> temporary `.olean` directory):
  - `Cerp.lean` (`46.89s`), `Theory.lean` (`18.1s`), `Bounds.lean` (`546.87s`), `Inference.lean` (`1.13s`), `Closure.lean` (`0.85s`) -> all `exit=0`.
  - `Audit.lean`, `AuditTheory.lean`, `AuditBounds.lean`, `AuditInference.lean`, `AuditClosure.lean` -> all `exit=0`, standard axioms only (`[]`, `[propext]`, `[propext, Quot.sound]`, `[propext, Classical.choice, Quot.sound]`); `leftover_oleans=0`.
- `SEMPLEX_LEAN_TIMEOUT=900 pytest -q`: **`172 passed in 1190.56s (0:19:50)`** (`exit=0`).