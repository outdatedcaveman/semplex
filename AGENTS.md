# Agent guide for semplex

semplex studies why learning works and which mechanisms training builds, on an exact atlas of small Boolean functions and their minimal threshold circuits. Theory is in `THEORY.md`, claims in `claims/REGISTER.md`, plan in `ROADMAP.md`, charter and literature in `charter/`.

## Non-negotiable research rules

1. **Pre-register.** Every experiment is a spike, `experiments/SPIKE_NN_REPORT.md`, with hypotheses and numeric held/broken criteria. Commit it before any run.
2. **Freeze answered spikes.** After verdicts, never edit a spike's code or criteria. A follow-up is a new spike that names its parent ("Follows:"). Fixing a measurement bug before any verdict is allowed; record the bug and keep both values. After the verdicts, freeze the spike's script and results: `python -m cerp.register freeze experiments/spikeNN*.py experiments/results/spikeNN*.json`. The check then reports any later change as a problem.
3. **Report every verdict as it came out:** held, broken, or neither. A refuted conjecture is stated as refuted in `THEORY.md`, and gets a claim row in `claims/REGISTER.md`.
4. **Grow the tree downward.** Fan out over the options of one decision, then descend onto what that round established (`experiments/TREE.md`).
5. **Keep the register on the ledger.** After editing `claims/REGISTER.md`, run `python -m cerp.register check`. It must report 0 problems. Re-read every claim it lists under a correction. The check also resolves evidence: cited `experiments/...` paths must exist, a `file.json:a.b` citation must name a real field, and every "Spike NN" cited must have a report.
6. **Switch basins on purpose.** After every 4–5 spikes on one question, run at least one spike on a different front of the charter (`ROADMAP.md`). Spikes 11–34 refined one basin; the switch to the compiler at n = 6 (Spike 35) gave the largest gain of the series. This matches Bespoke Labs' finding that new-idea switches gain about 9× a refinement step.
7. **Read before you cite.** Literature goes into `charter/LITERATURE_REVIEW.md` §5 with what was read and what it changes here.

## Running

- Fixed run command (OpenResearch-compatible): `python -m experiments.orx_run`. It executes the node named in the committed `experiments/orx_node.json`.
- Individual spikes: `python -m experiments.spikeNN run …` then `python -m experiments.spikeNN analyse`.
- Fit log-linear laws with `cerp/loglin.py` (exact Newton), not Nelder-Mead.

## OpenResearch

This repository follows the OpenResearch conventions and can be imported into it directly. See `charter/OPENRESEARCH.md`; the vendored modules are in `third_party/openresearch/agent-skills/`. Turn OpenResearch telemetry off before use.
