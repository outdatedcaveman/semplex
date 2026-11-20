# Lean proofs

| File | Contents |
|---|---|
| `Cerp.lean` | Spike 06: deciders for expression equivalence and task equivalence (sound and complete), and a RUP certificate checker (sound) |
| `Theory.lean` | Protocol-Frame Theory: Theorems 1–11 of `THEORY.md` |
| `Bounds.lean` | Soundness of the "not a threshold function" certificate used by `cerp/kernel_bounds.py` |
| `Distinction.lean` | Spike 17: quotient factorization, congruence, identity substitution, Tarski satisfaction invariance, and resource-sensitive contraction fragment |
| `SmallFibration.lean` | Spike 17: two-context Grothendieck construction with discrete fibers and cartesian factorization |\n| `ModuleDescent.lean` | Spike 17: finite two-module overlap model; compatible local profiles glue uniquely, incompatible profiles do not glue |\n| `SynesismConservation.lean` | Spike 17: dyadic partition/value conservation; equal molarity does not imply structural identity; synod-anchored coherent evolution |
| `Audit.lean`, `AuditTheory.lean`, `AuditBounds.lean`, `AuditDistinction.lean`, `AuditFibration.lean`, `AuditModuleDescent.lean`, `AuditSynesismConservation.lean` | `#print axioms` for every core theorem |
| `CHECK_LOG.txt`, `THEORY_CHECK_LOG.txt`, `BOUNDS_CHECK_LOG.txt` | Recorded audit output |

Checked with Lean 4.12.0 (official `leanprover/lean4` release), core library only.

```bash
lean Cerp.lean && lean Theory.lean && lean Distinction.lean && lean SmallFibration.lean                       # proofs
mkdir -p build && lean --root=. -o build/Cerp.olean Cerp.lean && lean --root=. -o build/Theory.olean Theory.lean
LEAN_PATH=build lean Audit.lean && LEAN_PATH=build lean AuditTheory.lean && LEAN_PATH=build lean AuditDistinction.lean && LEAN_PATH=build lean AuditFibration.lean   # axiom audit
```
