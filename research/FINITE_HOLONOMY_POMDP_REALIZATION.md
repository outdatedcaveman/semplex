# Finite holonomy POMDP: an exact causal-realization benchmark

**Status:** executable finite controlled partially observed model; exact rational verification; no physical hardware experiment yet.  
**Connection:** extends the posterior/Hankel realization in Spike 23 with gauge-invariant global holonomy and explicit intervention costs.

## 1. Physical state and gauge symmetry

Take a three-vertex ring with gauge group \(\mathbb Z_3\). A discrete connection is
\[
A=(a_0,a_1,a_2)\in\mathbb Z_3^3.
\]
A vertex gauge transformation \(g\in\mathbb Z_3^3\) acts by
\[
a_i\mapsto a_i+g_{i+1}-g_i\pmod 3.
\]
The Wilson-loop holonomy
\[
\theta(A)=a_0+a_1+a_2\pmod 3
\]
is invariant. Exhaustive enumeration verifies that the 27 connections fall into exactly three gauge orbits, each of size 9, classified by \(\theta\).

## 2. Primitive controlled dynamics

The physical controller has two primitive actions:

- \(+\): traverse the next edge clockwise;
- \(-\): traverse the previous edge counterclockwise.

Each edge traversal costs one unit. The internal physical state is
\[
(v,\phi)\in\mathbb Z_3\times\mathbb Z_3,
\]
where \(v\) is the current vertex and \(\phi\) is the accumulated parallel-transport phase. Starting at \((0,0)\):

- action \(+\) traverses edge \(v\), adds \(a_v\) to \(\phi\), and sends \(v\mapsto v+1\);
- action \(-\) traverses edge \(v-1\) backwards, subtracts \(a_{v-1}\) from \(\phi\), and sends \(v\mapsto v-1\).

An open path has no gauge-invariant scalar readout at its endpoint. A closed path based at vertex 0 does: its phase is
\[
\phi=w\theta\pmod 3,
\]
where \(w\) is its integer winding number. The shortest noncontractible closed paths are \(+++\) and \(---\), each of cost 3. Two-step backtracks have winding zero and return phase zero.

The code exhaustively checks this gauge-invariant closed-path identity for all 27 connections, all 27 gauge transformations, and every closed control word up to length six.

## 3. Partial observation and belief state

The hidden sector is the static holonomy \(\theta\in\{0,1,2\}\). The agent's information state is a belief
\[
b=(b_0,b_1,b_2)\in\Delta^2.
\]
When a closed path of winding \(w\) is completed, the observed outcome \(y\in\mathbb Z_3\) is drawn from
\[
K_\eta(y\mid w\theta)=
\begin{cases}
1-2\eta,&y=w\theta\pmod3,\\
\eta,&y\ne w\theta\pmod3,
\end{cases}
\qquad 0\le\eta\le\tfrac12.
\]
Open paths expose no gauge-invariant outcome. Contractible closed paths expose only the deterministic zero phase. The clockwise Wilson loop has \(w=1\) and directly probes \(\theta\).

The one-loop predictive distribution is
\[
p_b(y)=\sum_\theta b_\theta K_\eta(y\mid\theta).
\]
For repeated clockwise loops, the joint law is
\[
p_b(y_1,\ldots,y_n)=
\sum_\theta b_\theta\prod_{j=1}^n K_\eta(y_j\mid\theta).
\]
The product is inside the sum: all observations share one static hidden sector and are not independent after marginalizing over it.

## 4. Exact theorem: resource and noise thresholds

The clockwise observation matrix is
\[
K_\eta=\eta\mathbf 1\mathbf 1^T+(1-3\eta)I,
\qquad
\det K_\eta=(1-3\eta)^2.
\]

**Proposition.** For this controlled probe family:

1. If budget \(B<3\), every affordable closed path is contractible. All beliefs therefore have identical response profiles; the semantic quotient has one class.
2. If \(B\ge3\) and \(\eta\ne1/3\), equality of clockwise-loop response distributions implies equality of beliefs. The posterior-belief representation is fully abstract for this response family.
3. If \(\eta=1/3\), the observation channel is uniform. Every loop outcome is independent of \(\theta\), so all beliefs remain predictively equivalent at every budget, including under repeated loops.
4. Bayesian updating preserves predictive sufficiency: after observing a loop outcome, the posterior is sufficient for predicting every future loop outcome.

**Proof.** Below cost three, the only nonempty closed paths are backtracks with winding zero, so their responses do not depend on \(\theta\). At cost three, the clockwise loop is affordable and its response map is \(b\mapsto bK_\eta\). It is injective iff \(\det K_\eta\ne0\), which is equivalent to \(\eta\ne1/3\). At \(\eta=1/3\), every row of \(K_\eta\) is uniform; hence every finite outcome-sequence likelihood is independent of the hidden sector and of the prior. The final claim is Bayes' rule for a static hidden state. \(\square\)

This connects physical intervention, hidden-state inference, resource-relative semantic equivalence, and predictive-state realization in one exact finite model.

## 5. Verification

Run:
~~~powershell
python -m pytest -q tests/test_finite_holonomy_pomdp.py
python experiments/finite_holonomy_pomdp.py
~~~

The 10 tests check:

- all 27 gauge configurations and 27 gauge transformations;
- the three gauge orbits and their size;
- gauge invariance of every closed control path through length six;
- the minimum three-step cost of a nontrivial Wilson-loop probe;
- collapse of all beliefs below that threshold;
- separation at the threshold for every non-uniform channel;
- the exact noise-rank threshold;
- exact Bayesian updating and predictive sufficiency;
- dependence between repeated observations induced by the shared static hidden state.

All probabilities use rational arithmetic. The benchmark is a mathematical model, not a new physical discovery. A hardware extension would require a controllable phase/holonomy platform and a prospective comparison against local-only predictors at matched observation and compute budgets.


## 6. Explicit instantiation of the causal-realization interface

Let H be the set of finite action-observation histories and let
\[
\mu:H\to\Delta^2
\]
map each history to its Bayesian posterior over the hidden Wilson-loop sector. Let Test_B be the set of closed control words of length at most B. Define:
- cost(w) = length(w);
- Outcome = probability distributions on Z3;
- response(h,w) = the predictive outcome distribution for path w under posterior mu(h);
- encode(h) = mu(h);
- decode(b,w) = the same predictive distribution computed from belief b.

This is exactly the type signature of the generic causal-realization construction: histories, costed tests, response profiles, and an internal representation with a decoder.

For B<3, all reachable affordable closed paths have winding zero. The response quotient of histories is therefore a singleton, even if their Bayesian posteriors differ. For B>=3 and eta != 1/3, the clockwise Wilson-loop response map is injective on the entire belief simplex. Consequently,
\[
h\sim_B h'\quad\Longleftrightarrow\quad \mu(h)=\mu(h').
\]
The quotient of histories is isomorphic to the image of the reachable-posterior map; if the state space is taken to be all beliefs, the quotient is the full two-simplex. At eta=1/3, the quotient is again a singleton at every budget.

This verifies the two directions required by full abstraction for this model:
- sufficiency: equal posteriors induce equal distributions for every future closed-path test;
- separation: the affordable clockwise loop distinguishes any two unequal posteriors exactly when eta != 1/3.

The abstract Lean module already states the corresponding generic sufficiency/separation theorem. This experiment supplies a concrete mathematical instantiation and exact Python verification; it does **not** yet provide a Lean-checked adapter specialized to the Z3 model.


## 7. Exact posterior-Hankel factorization and balanced spectrum

For the uniform prior and one-loop observation histories y in Z3, the posterior-history matrix is R=K_eta because the channel is symmetric and its columns sum to one. The future-test matrix is O=K_eta. Hence the history-future Hankel matrix factors exactly:
\[
H=RO=K_\eta^2.
\]
Let P_perp=I-(1/3)11^T and lambda=1-3 eta. Since
\[
K_\eta=P_0+\lambda P_\perp,\qquad P_0=(1/3)11^T,
\]
we obtain
\[
P_\perp H P_\perp=\lambda^2P_\perp.
\]
The posterior-history and future-test Gramians are both
\[
W_c=W_o=\lambda^2P_\perp,
\]
so the balanced Gram product is
\[
W_c^{1/2}W_oW_c^{1/2}=\lambda^4P_\perp.
\]
The two nonzero squared singular values of the centered Hankel matrix are exactly lambda^4, matching the two nonzero eigenvalues of the balanced Gram product.

At eta=1/6, lambda=1/2:
- centered Hankel = (1/4) P_perp;
- Wc = Wo = (1/4) P_perp;
- balanced Gram = (1/16) P_perp.

At eta=1/3, all centered quantities vanish. This gives a gauge-theoretic counterpart to the posterior-Hankel results in Spikes 23 and 24. The exact matrices are included in the JSON artifact.
