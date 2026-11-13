"""Spike 07: CSIR v0.1 -- one schema across fragments, re-verifiable, composable."""

import copy
import json

import pytest

from cerp import csir, kernel
from cerp.benchmarks import carry_prefix, carry_ripple
from cerp.demo import ALARM, SENSORS_AGREE
from cerp.epistemics.inquiry import inquire
from cerp.epistemics.ontologies import CANDIDATES
from cerp.epistemics.world import ALL_ACTIONS, Interface
from cerp.ledger import Ledger
from cerp.lts import bisim_quotient, bisimulation, lts, random_lts, trace_equivalence
from cerp.pipeline import analyze
from cerp.sat import prove_equivalence

KC = {"basis": ["kernel-checked"], "trusted_base": ["cerp/kernel.py"], "conditions": []}


def spike01_bundle():
    rep = analyze(ALARM, ["a", "b", "c", "d"], care=SENSORS_AGREE)
    return csir.from_pipeline(rep, ALARM, care=SENSORS_AGREE)


def test_spike01_outputs_export_validate_and_recheck():
    b = spike01_bundle()
    assert csir.validate(b) == []
    assert b["links"] and all(s == "verified" for _, s in csir.recheck(b))
    # bundles are plain data: a JSON round trip changes nothing
    assert all(s == "verified" for _, s in csir.recheck(json.loads(json.dumps(b))))


def test_tampering_is_detected():
    b = spike01_bundle()
    t = copy.deepcopy(b)
    tgt = next(n for n in t["nodes"] if n["artifact"]["kind"] == "expr" and n["id"] != "source")
    tgt["artifact"]["body"] = ["const", 1]
    assert any(s.startswith("FAILED") for _, s in csir.recheck(t))


def test_rup_and_lts_links_recheck_from_bundle_alone():
    (l, vs), (r, _) = carry_ripple(24), carry_prefix(24)
    st, lemmas, _ = prove_equivalence({"vars": vs, "left": l, "right": r})
    P = lts("p0", [("p0", "a", "p1"), ("p1", "b", "p2"), ("p1", "c", "p3")])
    Q = lts("q0", [("q0", "a", "q1"), ("q0", "a", "q2"), ("q1", "b", "q3"), ("q2", "c", "q4")])
    A = random_lts(__import__("random").Random(4), 4)
    nodes = [csir.node("ripple", l, {"vars": vs}), csir.node("prefix", r, {"vars": vs}),
             csir.node("P", P, {"actions": ["a", "b", "c"]}), csir.node("Q", Q, {"actions": ["a", "b", "c"]}),
             csir.node("A", A, {"actions": ["a", "b"]}), csir.node("Aq", bisim_quotient(A), {"actions": ["a", "b"]})]
    links = [csir.link("ripple", "prefix", "extensional", {"vars": vs},
                       certificate={"method": "rup", "lemmas": lemmas}, warrant=KC),
             csir.link("P", "Q", "trace", {"actions": ["a", "b", "c"]},
                       certificate={"pairs": trace_equivalence(P, Q)[1]}, warrant=KC),
             csir.link("A", "Aq", "bisimulation", {"actions": ["a", "b"]},
                       certificate={"relation": bisimulation(A, bisim_quotient(A))[1]}, warrant=KC)]
    b = csir.bundle(nodes, links)
    assert csir.validate(b) == []
    assert [s for _, s in csir.recheck(b)] == ["verified"] * 3


def test_composition_follows_the_relation_order_and_matching_protocols():
    ext = csir.link("a", "b", "extensional", {"vars": ["x"]}, warrant=KC)
    task1 = csir.link("b", "c", "task", {"vars": ["x"], "care": "c1"}, warrant=KC)
    task2 = csir.link("c", "d", "task", {"vars": ["x"], "care": "c2"}, warrant=KC)
    # protocols must match exactly: ext's protocol has no care set, so even ext∘task needs alignment
    ext_c1 = dict(ext, protocol={"vars": ["x"], "care": "c1"})
    l, why = csir.compose(ext_c1, task1)
    assert l["relation"] == "task" and why is None             # ext ⊆ task: coarser wins
    assert csir.compose(task1, task2)[0] is None               # different care sets: refused
    bis = csir.link("p", "q", "bisimulation", {"actions": ["a"]}, warrant=KC)
    tr = csir.link("q", "r", "trace", {"actions": ["a"]}, warrant=KC)
    assert csir.compose(bis, tr)[0]["relation"] == "trace"
    adq = csir.link("m", "w", "adequate-to", {"protocols": []}, warrant=KC)
    assert csir.compose(csir.link("k", "m", "adequate-to", {"protocols": []}, warrant=KC), adq)[0] is None


def test_validator_rejects_dishonest_or_ill_typed_bundles():
    n1 = csir.node("x", {"kind": "expr", "body": ["var", "x"]}, {"vars": ["x"]},
                   resources={"cost": {"gates": 1}})                             # no cost model
    n2 = csir.node("y", {"kind": "expr", "body": ["var", "x"]}, {"vars": ["x"]})
    errs = csir.validate(csir.bundle([n1, n2], [
        csir.link("x", "y", "bisimulation", {}, warrant=KC),                      # wrong kind, no cert
        csir.link("x", "y", "task", {"vars": ["x"]}, warrant=KC, certificate={"method": "exhaustive"}),
        csir.link("x", "y", "extensional", {"vars": ["x"]})]))                    # no warrant
    text = " | ".join(errs)
    for frag in ("cost model", "does not apply", "no certificate", "care set", "no warrant"):
        assert frag in text, frag


@pytest.mark.slow
def test_world_models_export_with_commitments_and_stay_empirical():
    rep = inquire(Interface("latent_causal", ALL_ACTIONS, seed=1), CANDIDATES, seed=1)
    b = csir.from_inquiry(rep, [str(a) for a in ALL_ACTIONS])
    assert csir.validate(b) == []
    models = [n for n in b["nodes"] if n["artifact"]["kind"] == "causal-model"]
    assert models and all(n["ontology"]["commitments"] for n in models)
    assert all(s.startswith("not kernel-checkable") for _, s in csir.recheck(b))
