"""The status board is generated, consistent with its sources, and up to date."""
from cerp import status as S


def test_sources_are_consistent():
    d = S.collect()
    assert d["errs"] == [], d["errs"]
    assert {x["status"] for x in d["g"]["gaps"]} <= set(S.STATES)


def test_status_board_is_up_to_date():
    assert S.main(["--check"]) == 0, "run: python -m cerp.status"


def test_every_gap_serves_a_criterion_and_has_a_closing_test():
    d = S.collect()
    for x in d["g"]["gaps"]:
        assert x["closes_when"].strip() and x["missing"].strip() and x["next"].strip(), x["id"]


def test_conjecture_states_parse():
    c = {x["id"]: x["state"] for x in S.conjectures(
        "- **C1, a (CONJECTURE, unchanged; a bound is PROVED).** x\n- **C9, b (temperature form REFUTED by Spike 20).** y\n"
        "- **C18, c (NOT SUPPORTED, Spike 33; not refuted).** z\n- **C19, Occam (cost) as prior (NOT SUPPORTED at n = 4).** w\n")}
    assert c == {"C1": "Open", "C9": "Refuted", "C18": "Not supported", "C19": "Not supported"}
