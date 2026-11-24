"""cerp.angelic: failing steps become sorry obligations; automation closes what it can; the rest is reported."""
import json, os, shutil, subprocess, sys
import pytest

ELAN = os.path.expanduser("~/.elan/bin")
pytestmark = pytest.mark.skipif(not (shutil.which("lean") or os.path.exists(os.path.join(ELAN, "lean"))), reason="no Lean")

TOY = """theorem toy (a b : Nat) (h : a ≤ b) : a + 0 ≤ b + 1 := by
  have h1 : a ≤ b + 1 := by
    exact Nat.le_succ_of_le_wrong h
  have h2 : a + 0 = a := by
    exact foo
  rw [h2]
  exact h1

def tri : Nat → Nat
  | 0 => 0
  | n + 1 => tri n + (n + 1)

theorem hard (n : Nat) : 2 * tri n = n * (n + 1) := by
  have key : ∀ m, 2 * tri (m + 1) = 2 * tri m + 2 * (m + 1) := by
    exact wrong_lemma
  induction n with
  | zero => rfl
  | succ k ih => exact bogus k ih
"""


def test_angelic_outline_and_residual(tmp_path):
    f = tmp_path / "Toy.lean"; f.write_text(TOY)
    subprocess.run([sys.executable, "-m", "cerp.angelic", str(f)], check=True, capture_output=True, timeout=900)
    rep = json.loads((tmp_path / "Toy.angelic.json").read_text())
    obs = rep["obligations"]
    assert rep["new_angelic_sorries"] == len(obs) == 4
    closed = {o["id"] for o in obs if o["closed_by"]}
    assert {0, 1} <= closed                                   # the two trivial steps are repaired by automation
    assert rep["essential"] and all(o["goal"] != "(goal not captured)" for o in obs)
    patched = (tmp_path / "Toy.angelic.lean").read_text()
    assert "rw [h2]" in patched and "exact h1" in patched     # the outline survives
