# Variational Master Principle: exact interface, singular-support issue, and HoTT placement

**Date:** 2026-11-22  
**Status:** theorem candidate and proof obligations; not yet adopted as the canonical Master Principle. Antigravity is formalizing a version in the isolated worktree `semplex-gemini-wt`.

## 1. The candidate variational principle

For positive-definite matrices (A,B) and a positive-semidefinite kinetic/resource operator (L), consider
[
J_\lambda(X)=\operatorname{Tr}((A+\lambda L)X)+\operatorname{Tr}(BX^{-1}),
\qquad X\in\mathrm{SPD}(m).
]
Writing (A_\lambda=A+\lambda L), the stationarity condition is
[
A_\lambda-X^{-1}BX^{-1}=0
\quad\Longleftrightarrow\quad
XA_\lambda X=B.
]
The unique SPD solution is
[
X_*(\lambda)=A_\lambda^{-1}\# B,
]
where (#) denotes the Kubo–Ando operator geometric mean. The minimum value is
[
\Phi(\lambda)=2\operatorname{Tr}
\left((A_\lambda^{1/2}BA_\lambda^{1/2})^{1/2}\right).
]

This is the natural noncommutative replacement for minimizing a scalar product (ax+b/x). It does not require (A,B,L,X) to commute. The positivity/invertibility assumptions are essential to the SPD optimization statement.

## 2. Exact Hankel connection

For a finite weighted history/future factorization
[
\widetilde H=R_wO_w,
\quad
W_c=R_w^TR_w,
\quad
W_o=O_wO_w^T,
]
a solution of
[
XW_cX=W_o
]
satisfies
[
(R_wXR_w^T)^2=\widetilde H\widetilde H^T.
]
Since (R_wXR_w^T) is positive semidefinite, it is the positive square root:
[
R_wXR_w^T=(\widetilde H\widetilde H^T)^{1/2}.
]
Consequently
[
\operatorname{Tr}(R_wXR_w^T)=\|\widetilde H\|_*.
]
The variational minimum at (lambda=0) is therefore twice the nuclear norm of the weighted Hankel operator, when the factorization is minimal and the Gramians are positive definite.

There are two coordinate descriptions:
- **Dual belief basis:** (A=W_c, B=W_o), giving (X_* = W_c^{-1}\#W_o).
- **Primal state basis:** (A=W_c^{-1}, B=W_o), giving (X_* = W_c\#W_o).

The corresponding GL(m) covariance and invariant lifted history operator are useful because the internal realization coordinates are not semantic observables.

## 3. Critical issue: reduce to the minimal predictive support first

The ordinary SPD formula cannot be applied blindly to raw Gramians. In Spike 26:
- (W_c) and (W_o) can be singular;
- their ranks can differ;
- the centered Hankel operator has ranks (0,2,0) across the three tested resource/noise regimes.

The appropriate sequence is:

1. Construct the protected, policy-weighted centered Hankel operator (H_c).
2. Compute its rank (r), the minimal predictive dimension.
3. Pass to a minimal factorization (H_c=R_{min}O_{min}) with full column/row rank (r).
4. Define the positive weighted Gramians on that (r)-dimensional state.
5. Apply the SPD Riccati/geometric-mean theorem there.

At (r=0), the centered semantics is trivial; no inverse or SPD matrix should be fabricated. At the informative Spike26 setting (r=2), the variational object belongs on a two-dimensional minimal predictive state, not the original three-state hidden simplex.

This reduction is not merely a numerical trick. It is the realization-theoretic counterpart of quotienting by response equivalence before assigning coordinates to semantic states.

## 4. The centered-sum counterexample

The exact centered diagnostics are:
[
\operatorname{rank}(H_c)=(0,2,0),
\qquad
\operatorname{rank}((W_c)_c+(W_o)_c)=(1,2,2).
]
Thus the centered Gram sum retains one spurious mode below the probe threshold and two modes under uniform observation erasure. It is not the centered Hankel operator, nor a balanced realization Gramian by identity.

The geometric-mean/Riccati construction is promising precisely because it combines past and future information through a nonlinear balancing equation rather than adding the Gramians.

## 5. Resource monotonicity

If (Asucc0), (Bsucc0), (L\succeq0), and (A+\lambda Lsucc0) on the parameter domain, define
[
\Phi(\lambda)=\inf_{X\succ0}J_\lambda(X).
]
As an infimum of affine functions of (lambda), (Phi) is concave. Under differentiability/unique minimizer conditions, the envelope theorem gives
[
\Phi'(\lambda)=\operatorname{Tr}(LX_*(\lambda)).
]
Concavity therefore implies that the kinetic/resource expectation is non-increasing in (lambda). Strict monotonicity requires additional nondegeneracy; it does not follow from (L\succeq0) alone.

The parameter (lambda) has the interpretation of a Lagrange multiplier only after the constraint/cost model is specified. The matrix (L) must be derived from an operationally defined resource, not inserted by analogy.

## 6. Proof obligations before adoption

The isolated Mathlib development should explicitly settle:

1. **Polar factor existence:** the square-completion identity assumes an orthogonal (U) and (M=U^TR_BR_A^T). Prove the relevant polar decomposition under stated rank assumptions.
2. **Positive square root:** an algebraic identity (M^2=R_ABR_A^T) does not alone make (M) the principal positive square root. The geometric-midpoint/minimizer theorem needs (M) symmetric positive definite (or a clearly equivalent principal-root hypothesis).
3. **SPD domain:** show (X_*(\lambda)) belongs to the SPD domain and is the unique global minimizer, not merely an algebraic Riccati solution.
4. **Rank-deficient case:** reduce to the minimal Hankel support or develop a careful pseudoinverse/semidefinite extension. Do not invert singular raw (W_c,W_o).
5. **Policy weighting:** uniform weights over syntactic histories/tests are a mathematical sampling choice, not necessarily the physical law. Specify an admissible intervention policy and use its induced history/test weights; remove zero-probability histories or state support conditions.
6. **Kinetic assumptions:** state (L\succeq0), (A+\lambda L\succ0), the allowed (lambda)-domain, and strictness conditions for monotonicity.
7. **Basis covariance:** distinguish invariant lifted operators from coordinate-covariant (X_*), and verify the transformation law for every weighted Gramian.

## 7. Relation to HoTT and higher categorical semantics

The finite Hankel operator is a linear, set-level response representation. The minimal predictive quotient is the 0-truncated layer: histories are identified when every admissible future test agrees. The gauge action groupoid from the preceding research note retains the arrows and stabilizers discarded by that set quotient.

A plausible foundational hierarchy is:
- a groupoid/(infty)-groupoid of physical configurations and admissible transformations;
- a resource-indexed family of probes and response functors;
- a set-truncated predictive quotient for each fixed probe family;
- a minimal linear realization of the centered response operator;
- the variational SPD geometry on that minimal support.

The variational theorem can optimize a linear realization after a semantic quotient has been defined. It cannot itself justify which distinctions are physically admissible, which histories should be weighted, or whether the chosen probe category is dense. Those are prior grounding and categorical-descent obligations.

In higher settings, mapping spaces and coherence data may carry information not visible to a scalar character or finite Hankel matrix. The variational realization should therefore be treated as a controlled linear shadow of a richer response object, not as a replacement for its (infty)-categorical semantics.

## 8. Coordination status

Antigravity's independent audit event 151805 proposed this variational direction and is formalizing it in the isolated branch `gemini/master-principle-variational`. A follow-up review request (event 151815) asks it to resolve the positivity, polar-decomposition, minimal-support, and policy-weighting obligations. The canonical Semplex tree has not imported or merged those isolated files. Its 100-run empirical showdown is not duplicated here.
