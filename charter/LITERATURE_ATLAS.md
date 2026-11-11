# Literature notes for the circuit atlas (Spike 08 / 08b)

Verification levels, per charter §13:
- **READ**: content obtained through the alphaXiv report of the paper (an AI-generated structured summary, not the PDF itself).
- **INDEX**: found in the alphaXiv index; only title and abstract snippet seen. Relevance is a guess to be checked.
- **MEMORY**: recalled, not looked up this session. Do not cite without verification.

## Starting point: Nanda et al., "Progress measures for grokking via mechanistic interpretability" (arXiv:2301.05217) — READ

What the paper does, per the report:
- Trains a one-layer ReLU transformer on addition modulo 113 and fully reverse-engineers the learned algorithm: inputs are embedded as sines and cosines at a few key frequencies, combined with trigonometric identities, and decoded by constructive interference.
- Confirms it with ablations in Fourier space.
- Defines two progress measures from that understanding ("restricted loss": performance of the generalizing circuit alone; "excluded loss": performance without it).
- Finds that grokking is three continuous phases: memorization, circuit formation, cleanup. Weight decay removes the memorizing components once the generalizing circuit exists.

How it relates to the atlas:

| Their setting | Ours | What each could give the other |
|---|---|---|
| One trained network, one task; the circuit is *discovered after training* | Every circuit of a small family, *enumerated before training* | The atlas is ground truth at tiny scale: an interpretability method can be scored against known optima |
| Progress measures need the algorithm to be known first | The table knows the optimal circuits for every tiny task | For tiny tasks, a task-independent progress measure exists: distance in weight space to the nearest optimal circuit |
| Memorizing and generalizing solutions compete; regularization picks the efficient one | Elements have measurable weight-space volume; cheap elements dominate (Spike 08b, step 4) | Test whether "cleanup" is movement from a large-volume region to a low-cost element |
| Open question they raise: do different runs find the same circuit? | Isomer counts: 3-input parity has 201 minimal first layers | Predicts *how many* distinct circuits training could land on |

Caveat: their regime is continuous weights, attention and a 113-way output. Ours is threshold neurons on at most 4 bits. Nothing in the atlas is evidence about transformers yet.

**Proposed experiment (Spike 09):** train small real-valued networks on every 4-input task with and without weight decay. Record which element and which isomer they converge to, whether they pass through costlier elements first, and whether the table's optimum predicts the post-grokking circuit.

## Related work found in the index — INDEX only

| Paper | Why it may matter |
|---|---|
| Towards Combinatorial Interpretability of Neural Computation (arXiv:2504.08842) | Analyses networks through the sign pattern of weights; closest in spirit to a discrete atlas |
| A Toy Model of Universality: Reverse Engineering How Networks Learn Group Operations (arXiv:2302.03025) | Whether different networks learn the same circuits; our isomer counts bear on it |
| Complete Identification of Deep ReLU Networks through Łukasiewicz Logic (arXiv:2602.00266) | Characterizes when different ReLU networks compute the same function; the continuous analogue of isomers |
| Depth Lower Bounds for ReLU Networks with Binary Inputs (arXiv:2606.18540) | Depth vs size on Boolean inputs; bears on our "depth never helps for n ≤ 4" finding |
| Deep-layered machines have a built-in Occam's razor (arXiv:2603.01217) | Simplicity bias of input-output maps; bears on our volume measurements |
| The Unit Gap: How Sharing Works in Boolean Circuits (arXiv:2603.08033) | Circuit (shared) vs formula (tree) size; analogous to our skip vs layered comparison |
| Learning with Boolean threshold functions (arXiv:2602.17493) | Training networks whose nodes are strictly ±1 |
| InterpBench (arXiv:2407.14494) | Networks with known ground-truth circuits for evaluating interpretability methods |
| Towards Automated Circuit Discovery (arXiv:2304.14997) | Automated circuit discovery; a consumer of ground-truth tables |
| Size and depth of monotone neural networks (arXiv:2207.05275) | Threshold networks with non-negative weights |

## Classical prior art to check — MEMORY

- Muroga's threshold-logic work: tables of threshold functions, minimal integer weights, and optimal threshold networks by integer programming. Our counts (104, 1,882; weights ≤ 2 and ≤ 3) are expected to match; our census is now independently certified.
- Knuth, TAOCP vol. 4A §7.1.2: optimal Boolean chains for all functions of up to 5 variables (2-input gates). The closest classical "periodic table"; a different gate basis.
- Depth-2 vs depth-3 threshold circuit separations (Hajnal, Maass, Pudlák, Szegedy, Turán) and parity bounds: asymptotic versions of our depth question.
- Valle-Pérez, Camargo, Louis on the parameter-function map's simplicity bias: our volume numbers are an exact small-scale instance.

**Priority caution:** given this prior art, exact minima for threshold networks on ≤ 4 inputs are plausibly already known. What we add is the verified table with kernel-checked certificates, the Protocol-Frame reading, the cross-family comparison and the compiler.
