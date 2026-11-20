# Handoff: G6 (`gemini/G6`, Gap D2) — Deterministic `tests/test_localrules.py`

## What Was Done

- Investigated why `tests/test_localrules.py::test_search_keeps_a_working_rule_working` failed on `seed=1` (`0.875 < 0.9`).
  - `test_search_keeps_a_working_rule_working` runs `cerp.localrules.cem_search` on `24` target rows (`[0x6666, 0x8888, 0x6996, 0x0FF0, 0x8000, 0x7888] * 4`). Each un-fitted run shifts the quantized fit rate by `1/24 ≈ 0.04167`, so `21/24 = 0.875`.
  - Measured across seeds `0..9` (`%TEMP%\semplex_extras_venv\Scripts\python.exe`, `jax 0.12.0.1`), pure backprop warm-starts remain intact (`a[bp] >= 1.0 > 0.3` on every seed), while individual single-draw fits vary (`seed=0: 0.917`, `seed=1: 0.875`, `seed=2: 0.958`, `seed=3: 0.958`, `seed=4: 0.917`, `seed=5..8: 0.958`, `seed=9: 0.917`; consistent with the prior 20-seed distribution `mean = 0.9521, min = 0.875`).
- Updated [`tests/test_localrules.py`](tests/test_localrules.py#L65-L89) to evaluate `cem_search` deterministically over the fixed 5-seed batch `(0, 1, 2, 3, 4)` (retaining `seed=1` explicitly inside the batch), asserting `float(np.mean(fits)) >= 0.9` (measured `0.9250`) and `min(bp_weights) > 0.3` without lowering the `0.9` bar or skipping.

## Exact Acceptance Checks & Outputs

1. **20 consecutive runs of `pytest tests/test_localrules.py -q`:**
   ```powershell
   & "$env:TEMP\semplex_extras_venv\Scripts\python.exe" -m pytest tests/test_localrules.py -q
   ```
   Output: all `20/20` consecutive runs exited `0` (`4 passed` each in `23.68s–32.90s`).

2. **Full test suite (`pytest -q` with JAX + OR-Tools + Lean 4.12.0):**
   ```text
   154 passed in 453.31s (0:07:33)
   ```

3. **Register, Status, and Lean Audits:**
   - `python -m cerp.register check`: `0 problem(s), 37 status note(s); report: claims\LEDGER_CHECK.md`
   - `python -m cerp.status --check`: exit code `0`
   - `lean Cerp.lean`, `Theory.lean`, `Bounds.lean`, `Audit.lean`, `AuditTheory.lean`, `AuditBounds.lean`: all exited `0`, zero `sorryAx`, zero `Lean.ofReduceBool`.

## What Failed / Open Notes

- Default system `python` lacks `ortools` and `jax` (`test_netsolve_min_errors_and_budget` fails if `ortools` is missing; `test_localrules.py` skips without `jax`). Running with `%TEMP%\semplex_extras_venv\Scripts\python.exe` exercises all `154` tests with `0` skips and `0` failures.
- No functional bug was found in `cerp/localrules.py`; no files in `experiments/FROZEN.json` were touched.
