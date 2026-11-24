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


def _row(evidence):
    return R.Row(id="P999", statement="", status="EXPLORATORY", scope="", evidence=evidence,
                 depends=[], caveats="", next="")


def test_evidence_citations_resolve(tmp_path):
    (tmp_path / "experiments" / "results").mkdir(parents=True)
    (tmp_path / "experiments" / "results" / "s.json").write_text('{"a": {"b": [1, 2]}}')
    (tmp_path / "experiments" / "SPIKE_07_REPORT.md").write_text("x")
    ok = _row("`experiments/results/s.json:a.b.1`; Spike 07 F2")
    assert R.evidence_problems([ok], root=tmp_path) == []
    bad = _row("`experiments/results/s.json:a.c`; `experiments/nope.py`; Spike 08")
    probs = R.evidence_problems([bad], root=tmp_path)
    assert len(probs) == 3 and any("no field a.c" in p for p in probs)


def test_frozen_file_change_is_a_problem(tmp_path):
    (tmp_path / "experiments").mkdir()
    f = tmp_path / "experiments" / "spike99.py"
    f.write_text("print(1)\n")
    R.freeze([f], root=tmp_path)
    assert R.frozen_problems(root=tmp_path) == []
    f.write_text("print(2)\n")
    assert len(R.frozen_problems(root=tmp_path)) == 1


def test_partly_mechanized_counts_as_rationale():
    row = _row("Lean lemma in `Theory.lean`")
    row.status = "PROVED (paper) + PARTLY MECHANIZED"
    assert R.methods_for(row) == {R.Method.RATIONALE}
