# Spike 65: The continuous sufficiency law: a tracked direction is a sphere, a tracked axis is a projective plane

**Date:** 2026-11-17 · **Status:** complete (pre-registered in 49242c1; results below) · **Follows:** `charter/FOUNDATIONS.md` §12.3 (harmonic analysis, continuous analogue of C31‴); Spikes 57–60 (closure, causal power, readout-determined geometry). **Conjectures:** C32 (closure) and the readout law, in a continuous setting.

## Task

- **State.** A body axis u ∈ S² starts at e_z. At each step it is rotated by a random small rotation exp([ω_t]×), with ω_t ~ N(0, 0.3² I₃) the network's input: u_t = exp([ω_t]×) u_{t−1}.
- **Signed readout (SIGN).** The network outputs u_t (3 numbers): a point of the sphere S².
- **Unsigned readout (AXIS).** The network outputs the traceless projector u_t u_tᵀ − I/3 (5 independent entries): a point of the projective plane RP².

The axis update is closed on RP², because u ↦ −u commutes with every rotation. So the minimal (Myhill–Nerode) state space is S² for SIGN and RP² for AXIS: antipodal states are distinct for SIGN and identified for AXIS.

Harmonic analysis on S² predicts the geometry:
- SIGN: degree-1 harmonics, the coordinates of u;
- AXIS: even harmonics only, degree 2 (the Veronese embedding).

## Training

- **Model.** GRU, hidden size 64, input ω_t (3), linear readout, mean-squared error.
- **Optimiser.** Adam, lr 0.003 cosine to 0, 6,000 steps, batch 64, length 30.
- **Seeds.** 5 per readout (6,500 + 10·readout + seed).
- **Fit guard.** Output R² ≥ 0.95 on 500 sequences of length 100.

## Measurements (500 sequences of length 60, steps 5–59)

- **Antipodal ratio.** Hidden states are binned by their true u into 200 bins (a Fibonacci grid of directions). r = mean ‖h̄(u) − h̄(−u)‖ / mean ‖h̄(u) − h̄(u′)‖ over random bin pairs. Here h̄ is a bin mean and −u the antipodal bin.
- **Harmonic content.** Linear regression of hidden states on harmonic features of u:
  - degree 1: 3 features;
  - degree 2: 5 features, traceless uuᵀ;
  - degree 3: 7 features, real spherical harmonics.

  R²_ℓ is the share of hidden variance explained by degree ℓ alone. The centroid of all hidden states is removed first.
- **Intervention (antipodal swap).** At a random step, replace the hidden state with a donor hidden state whose true axis is the antipode of the current one (nearest bin, within 0.1 rad), then continue the remaining 20 inputs. Compare outputs with the ground truth from u (no swap) and from −u. The outcome is the share of trials whose outputs match the no-swap truth within R² ≥ 0.9.

## Hypotheses and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H65.1 | **Closure identifies antipodes exactly when the readout cannot tell them apart** | median r ≤ 0.25 for AXIS **and** ≥ 0.75 for SIGN | AXIS median r ≥ SIGN median r |
| H65.2 | **Harmonic sufficiency:** SIGN is degree 1, AXIS is degree 2 with no degree 1 | SIGN: R²₁ ≥ 0.6 and R²₁ > R²₂; AXIS: R²₂ ≥ 0.4 and R²₁ ≤ 0.05; both in ≥ 4 of 5 fitted runs | the reverse ordering in ≥ 3 fitted runs of either readout |
| H65.3 | **Antipodal micro-difference is causally inert for AXIS, causal for SIGN** | AXIS: ≥ 90% of swaps leave outputs matching the no-swap truth; SIGN: ≤ 10% | AXIS ≤ SIGN |

Anything else is *neither*. **Guard:** a readout counts only with ≥ 3 fitted seeds.

## What this cannot show

- One architecture.
- A noisy random walk on S², not a group automaton.
- The harmonic regression is linear; nonlinear encodings of the same harmonics would be missed.

## Commands

```
python -m experiments.spike65 run
python -m experiments.spike65 analyse
```

## Results

`experiments/results/spike65.json`.

| Readout | Seed | Fit R² | R²₁ | R²₂ | R²₃ | Antipodal ratio | Swap = no-swap |
|---|---|---|---|---|---|---|---|
| SIGN | 6500 | 0.901 | 0.377 | 0.010 | 0.001 | 1.46 | 0.00 |
| SIGN | 6501 | 0.946 | 0.419 | 0.010 | 0.001 | 1.45 | 0.00 |
| SIGN | 6502 | 0.899 | 0.372 | 0.010 | 0.001 | 1.45 | 0.00 |
| SIGN | 6503 | 0.952 | 0.413 | 0.011 | 0.001 | 1.45 | 0.00 |
| SIGN | 6504 | 0.895 | 0.388 | 0.010 | 0.001 | 1.47 | 0.00 |
| AXIS | 6510 | 0.805 | 0.476 | 0.034 | 0.002 | 1.44 | 0.31 |
| AXIS | 6511 | 0.814 | 0.512 | 0.039 | 0.003 | 1.44 | 0.31 |
| AXIS | 6512 | 0.796 | 0.500 | 0.033 | 0.002 | 1.44 | 0.24 |
| AXIS | 6513 | 0.767 | 0.487 | 0.034 | 0.003 | 1.43 | 0.34 |
| AXIS | 6514 | 0.817 | 0.491 | 0.035 | 0.002 | 1.42 | 0.30 |

**Verdicts: H65.1, H65.2, H65.3 all NO VERDICT.** Fitted runs (fit R² ≥ 0.95 at length 100): SIGN 1/5 (0.952), AXIS 0/5 (0.77–0.82). Both are below the guard of 3. Tracking error accumulates over 100 steps of noisy rotation.

**Exploratory, unfitted runs included:**
- **SIGN behaves as predicted in every run:**
  - degree-1 geometry (R²₁ 0.37–0.42, R²₂ ≈ 0.01);
  - antipodes far apart (ratio 1.45);
  - swapping in the antipodal state changes the outputs in 100% of trials (match 0.00).
- **AXIS does not collapse to the projective plane:**
  - networks keep the *signed* direction (R²₁ 0.48–0.51, R²₂ 0.03–0.04);
  - antipodes stay apart (ratio 1.44);
  - antipodal swaps change outputs in about 70% of trials.

  The networks lift the task to the **double cover S² → RP²**, where SO(3) acts linearly on ℝ³ (degree 1), instead of using the minimal 5-dimensional quotient representation (degree 2). They fit the task worse for it.

**Reading.** With Spike 62, where networks kept unfaithful constituents rather than compressing, this points the same way. Learned representations follow the *simplest linear representation of the dynamics*, even when a smaller quotient would suffice for the outputs. The minimal (Myhill–Nerode) quotient is reached when it is also the simplest linear one, as in the discrete automata of Spikes 57–58. It is not reached when a covering space linearises the dynamics more cheaply.

This is a new conjecture (**C36, linearising cover**), to be tested with a formally registered design and a guard the task can pass: shorter evaluation length, or lower rotation noise.
