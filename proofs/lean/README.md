# Lean proofs

| File | Contents |
|---|---|
| `Cerp.lean` | Spike 06: deciders for expression equivalence and task equivalence (sound and complete), and a RUP certificate checker (sound) |
| `Theory.lean` | Protocol-Frame Theory: Theorems 1–11 of `THEORY.md` |
| `Bounds.lean` | Soundness of the "not a threshold function" certificate used by `cerp/kernel_bounds.py` |
| `Audit.lean`, `AuditTheory.lean`, `AuditBounds.lean` | `#print axioms` for every core theorem |
| `CHECK_LOG.txt`, `THEORY_CHECK_LOG.txt`, `BOUNDS_CHECK_LOG.txt` | Recorded audit output |

Checked with Lean 4.12.0 (official `leanprover/lean4` release), core library only.

```bash
lean Cerp.lean && lean Theory.lean                       # proofs
mkdir -p build && lean --root=. -o build/Cerp.olean Cerp.lean && lean --root=. -o build/Theory.olean Theory.lean
LEAN_PATH=build lean Audit.lean && LEAN_PATH=build lean AuditTheory.lean   # axiom audit
```
