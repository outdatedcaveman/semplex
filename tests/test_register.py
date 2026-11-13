"""The claims register loads into the ledger cleanly, and corrections propagate."""
from cerp import register as R


def test_register_parses_every_row():
    rows = R.parse()
    assert len(rows) >= 123
    assert all(r.id.startswith("P") and len(r.id) == 4 for r in rows)


def test_no_problems_in_register():
    problems, notes, led = R.check()
    assert problems == [], problems


def test_corrections_reach_their_dependents():
    _, led, _ = R.load()
    assert "P113" in led.affected_by("P110")        # Spike 30's confound correction depends on Spike 29's claim
    assert "P117" in led.affected_by("P110")        # label-imbalance caveat too


def test_dependency_ranges_expand():
    rows = {r.id: r for r in R.parse()}
    assert {"P087", "P090", "P093"} <= set(rows["P099"].depends)
