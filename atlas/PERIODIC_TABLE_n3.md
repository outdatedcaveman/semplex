# Periodic table of 3-input threshold circuits

Family: strictly layered threshold networks (see `cerp/atlas.py`). One row per NPN class (14 classes cover all 256 functions). Every witness net is kernel-verified; every neuron count is exact (all first layers of width <= 3 were enumerated).

| Period (neurons) | Element | Truth table | Functions in class | Shape | Min. determining width w* | Distinct minimal first layers | Witness (weights; threshold per neuron) |
|---|---|---|---|---|---|---|---|
| 1 | constant | 0x00 | 2 | (1,) | 0 | 1 | `[0, 0, 0]>=1` |
| 1 | AND3 | 0x01 | 16 | (1,) | 1 | 1 | `[-1, -1, -1]>=0` |
| 1 | AND2 | 0x03 | 24 | (1,) | 1 | 1 | `[0, -1, -1]>=0` |
| 1 | x0 AND (x1 OR x2) | 0x07 | 48 | (1,) | 1 | 1 | `[-1, -1, -2]>=-1` |
| 1 | x0 (projection) | 0x0f | 6 | (1,) | 1 | 1 | `[0, 0, -1]>=0` |
| 1 | MAJ3 (majority) | 0x17 | 8 | (1,) | 1 | 1 | `[-1, -1, -1]>=-1` |
| 3 | x0 AND (x1 XOR x2) | 0x06 | 24 | (2, 1) | 2 | 26 | `[-1, -1, -1]>=0 [-1, -1, -2]>=-1; [-1, 1]>=1` |
| 3 | exactly-two-of-3 | 0x16 | 16 | (2, 1) | 2 | 4 | `[-1, -1, -1]>=0 [-1, -1, -1]>=-1; [-1, 1]>=1` |
| 3 | all-equal (x0=x1=x2) | 0x18 | 8 | (2, 1) | 2 | 13 | `[-1, -1, -2]>=-1 [-1, -1, -2]>=-2; [-1, 1]>=1` |
| 3 | (unnamed) | 0x1c | 48 | (2, 1) | 2 | 11 | `[0, -1, -1]>=0 [-1, -1, -2]>=-2; [-1, 1]>=1` |
| 3 | MUX (x0 ? x1 : x2) | 0x2e | 24 | (2, 1) | 2 | 18 | `[-1, -1, -1]>=0 [1, -1, -2]>=-1; [-1, 1]>=1` |
| 3 | (x0 AND x1) XOR x2 | 0x1e | 24 | (2, 1) | 2 | 7 | `[-1, -1, -1]>=0 [-1, -1, -2]>=-2; [-1, 1]>=1` |
| 3 | XOR2 | 0x3c | 6 | (2, 1) | 2 | 13 | `[0, -1, -1]>=0 [0, -1, -1]>=-1; [-1, 1]>=1` |
| 4 | XOR3 (parity) | 0x96 | 2 | (3, 1) | 3 | 201 | `[-1, -1, -1]>=0 [-1, -1, -1]>=-1 [-1, -1, -1]>=-2; [-2, 1, -1]>=0` |
