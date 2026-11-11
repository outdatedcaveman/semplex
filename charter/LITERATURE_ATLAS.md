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

## Two further items requested on 2026-11-11

### e-means (Meta FAIR; arXiv:2611.09501; code in FAISS `contrib/e_means`) — PARTLY READ

Read: title, abstract, introduction and related-work sections of the alphaXiv full text, plus a keyword scan of the rest; **not** the experiments or appendices. Checked directly: `faiss-cpu` 1.16.0 on PyPI contains `faiss.contrib.e_means` (with a `NumpyEmeans` class).

- **What it is:** a faster way to solve the standard k-means clustering problem on large sets of continuous vectors. It replaces Lloyd's full-pass updates with mini-batch exponential-moving-average updates, plus rules that set batch size and decay automatically.
- **Authors' claims (self-reported):** reaches Lloyd's 25-epoch loss in 1.4–2.6 epochs; 10–45× GPU wall-clock speedups. The paper states its rules were tuned for high-dimensional embeddings.
- **Independent check:** one third-party blog post reports only about 1.5× in a reimplementation. Not verified by us either way.
- **Use for this project now: none.** Our objects are exact and discrete (truth tables, integer-weight circuits); we classify them by exact canonical forms, not by clustering.
- **Possible use later:** when the atlas idea is applied to large trained networks, exact canonicalization stops being possible, and clustering hidden units or activations is the obvious way to define approximate "elements". A fast k-means would matter there. A codebook is also a partition of activation space, so "smallest codebook that still determines the task" is a Protocol-Frame question worth trying at that stage.

### Perin, Anselmi, Deny, "A method to automatically discover symbolic local learning rules" (arXiv:2611.12248) — READ IN FULL (alphaXiv full text, including appendices)

- **What it does:** for each layer, it builds a dictionary of scalar "trace monomials" from the layer's local variables (inputs, weights, outputs, and those of layers up to d steps downstream), generated systematically with Penrose tensor-diagram notation up to order 4. A local loss is a weighted sum of these monomials. The weights are meta-learned so that following the local gradients lowers a chosen global loss.
- **Reported results (small 3-layer networks, sliced MNIST):**
  - Classification: discovered rule 67% accuracy, backpropagation 71%, first layer frozen 63%, frozen to PCA 68%, frozen to ICA 65%. The rule beat the frozen and ICA baselines, not the PCA baseline.
  - Reconstruction loss: rule 1.90, frozen 3.35, backpropagation 1.27.
  - Self-supervised loss: rule 17.11, frozen 22.47, backpropagation 5.50.
- **Limitations the authors state:** the meta-optimization is numerically delicate and sensitive to hyperparameters; global-degree rules did not recover backpropagation even when its terms were available; transfer to a differently sized network was only partial; all experiments are small.
- **Relevance to this project:**
  - **Scoring learning rules against ground truth.** They judge a rule by the global loss it reaches. The atlas allows a sharper test on tiny tasks: which element the rule reaches, whether it picks a table-cheapest completion (Spike 09 found backpropagation does in 88–95% of runs), and which of the equivalent minimal circuits it lands on. A local rule could match backpropagation's loss while having a different simplicity bias, and only this kind of test would show it.
  - **"Degree" is an observational power.** Their neighbourhood degree is how much of the downstream network a layer may observe. Their finding that classification needs degree 2 while reconstruction manages with degree 1 is a statement of the same shape as our determinacy results: which information suffices for which task. It may be expressible as a Protocol-Frame question.
  - **Their dictionary enumeration parallels our circuit enumeration**: a finite, symmetry-aware list of all candidates up to a size bound. Their appendix code is short and reusable.
- **Not established:** that any of this carries over. Their networks are real-valued with ReLU on 28-dimensional inputs; ours are threshold circuits on 4 bits.
- **Concrete follow-up (roadmap 10b):** implement their order-4 dictionary for our 4-input tanh networks and run Spike 09's measurements with a discovered local rule in place of backpropagation.
