# Lean proofs

| File | Contents |
|---|---|
| `Cerp.lean` | Spike 06: deciders for expression and task equivalence (sound and complete); RUP checker (sound); Tseitin encoder (sound and complete) and miter; LRAT checker; `TNode` threshold nets with exhaustive and LRAT equivalence routes (Part D) |
| `Theory.lean` | Protocol-Frame Theory: Theorems 1–12 and the core of Proposition 14 (§1–10); partial results for conjectures C1–C5 (§11–16); frame morphisms, finite Markov-kernel contraction, finite optional stopping and Ville's bound (§17–19) |
| `Bounds.lean` | Soundness of the "not a threshold function" certificate used by `cerp/kernel_bounds.py`; parity3 and parity4 are not realizable by two halfspaces |
| `Audit.lean`, `AuditTheory.lean`, `AuditBounds.lean` | `#print axioms` for every core theorem |
| `CHECK_LOG.txt`, `THEORY_CHECK_LOG.txt`, `BOUNDS_CHECK_LOG.txt` | Recorded audit output |

Checked with Lean 4.12.0 (official `leanprover/lean4` release), core library only.

```bash
lean Cerp.lean && lean Theory.lean                       # proofs
mkdir -p build && lean --root=. -o build/Cerp.olean Cerp.lean && lean --root=. -o build/Theory.olean Theory.lean
lean --root=. -o build/Bounds.olean Bounds.lean
LEAN_PATH=build lean Audit.lean && LEAN_PATH=build lean AuditTheory.lean && LEAN_PATH=build lean AuditBounds.lean   # axiom audit
```
