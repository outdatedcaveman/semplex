"""Spike 02: world-facing sandbox, rival ontologies, evidence, revision."""

import ast
import math
import pathlib
import random

import pytest

from cerp.epistemics import inquiry
from cerp.epistemics.approx_sufficiency import minimal_eps_sufficient
from cerp.epistemics.bayesnet import distribution, em_fit, loglik
from cerp.epistemics.inquiry import adequacy_test, inquire
from cerp.epistemics.ontologies import (CANDIDATES, O1_LATENT_CAUSAL, O2_INDEPENDENT, O4_COPY_CHAIN,
                                        O3_LATENT_CONFOUNDED)
from cerp.epistemics.world import ALL_ACTIONS, WORLDS, Interface
from cerp.ledger import Ledger, Status


def answers(rep):
    return {k: (v["status"], v["statement"].split(":")[0]) for k, v in rep["answers"].items()}


# ------------------------------------------------------------ sandbox integrity

def test_latent_worlds_are_observationally_identical():
    d1 = distribution(*WORLDS["latent_causal"])
    d3 = distribution(*WORLDS["latent_confounded"])
    assert max(abs(d1[c] - d3[c]) for c in d1) < 1e-12
    # ...but differ under intervention
    i = WORLDS["latent_causal"][0].observables.index("Y")
    y = lambda w: sum(p for c, p in distribution(*WORLDS[w], {"A": 1}).items() if c[i])
    assert abs(y("latent_causal") - y("latent_confounded")) > 0.1


def test_agent_has_no_access_to_truth():
    """inquiry.py may not import the world module; it only gets an Interface."""
    src = pathlib.Path(inquiry.__file__).read_text()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.ImportFrom):
            assert "world" not in (node.module or ""), "agent imports the world"
        if isinstance(node, ast.Import):
            assert all("world" not in a.name for a in node.names)
    iface = Interface("latent_causal")
    public = {k: v for k, v in vars(iface).items() if not k.startswith("_")}
    assert not any(isinstance(v, dict) and "Z" in v for v in public.values())


def test_interface_enforces_protocols_and_budget():
    iface = Interface("latent_causal", actions=ALL_ACTIONS[:1], budget=100)
    with pytest.raises(PermissionError):
        iface.run({"A": 1}, 10)
    iface.run({}, 100)
    with pytest.raises(Exception):
        iface.run({}, 1)


# ------------------------------------------------------------ fitting & tests

def test_em_fit_is_a_witness_at_least_as_good_as_truth():
    rng = random.Random(0)
    iface = Interface("latent_causal", seed=2)
    data = {(): iface.run({}, 4000)}
    s, p = WORLDS["latent_causal"]
    params, ll = em_fit(O1_LATENT_CAUSAL, data, rng)
    assert math.isclose(ll, loglik(O1_LATENT_CAUSAL, params, data))  # recomputable witness
    assert ll >= loglik(s, p, data) - 1.0


@pytest.mark.slow
def test_calibrated_adequacy_does_not_reject_the_true_model():
    """The naive G-test did (spike-02 finding F2). Calibrated test: p not tiny."""
    ps = []
    for seed in range(4):
        rng = random.Random(seed)
        iface = Interface("latent_causal", seed=seed)
        train = {(): iface.run({}, 1500)}
        params = em_fit(O1_LATENT_CAUSAL, train, rng)[0]
        batch = iface.run({"S1": 1}, 1500)
        ps.append(adequacy_test(O1_LATENT_CAUSAL, params, train, {"S1": 1}, batch, rng)[2])
    assert min(ps) > 1e-3, ps


def test_calibrated_adequacy_still_rejects_a_wrong_model():
    rng = random.Random(1)
    iface = Interface("latent_causal", seed=1)
    train = {(): iface.run({}, 1500)}
    params = em_fit(O3_LATENT_CONFOUNDED, train, rng)[0]
    batch = iface.run({"A": 1}, 1500)
    assert adequacy_test(O3_LATENT_CONFOUNDED, params, train, {"A": 1}, batch, rng)[2] < 1e-6


# ------------------------------------------------------------ the loop

@pytest.mark.slow
def test_observation_alone_leaves_causal_question_undetermined():
    for world in ("latent_causal", "latent_confounded"):
        rep = inquire(Interface(world, ALL_ACTIONS[:1], seed=3), CANDIDATES, seed=3)
        a = answers(rep)
        assert a["intervening on A changes Y"] == ("OUT-OF-SCOPE", "UNDETERMINED")
        assert set(rep["survivors"]) == {O1_LATENT_CAUSAL.name, O3_LATENT_CONFOUNDED.name}
        assert any(v["witnessed"] for v in rep["equivalence"].values())


@pytest.mark.slow
def test_interventions_resolve_it_correctly():
    for world, expected in (("latent_causal", "YES"), ("latent_confounded", "NO")):
        rep = inquire(Interface(world, ALL_ACTIONS[:3], seed=4), CANDIDATES, seed=4)
        assert answers(rep)["intervening on A changes Y"] == ("EMPIRICALLY-SUPPORTED", expected)


@pytest.mark.slow
def test_untested_interventions_are_only_conjectures():
    rep = inquire(Interface("latent_causal", ALL_ACTIONS[:3], seed=4), CANDIDATES, seed=4)
    st, _ = answers(rep)["intervening on S1 changes S2"]
    assert st == "CONJECTURE"


@pytest.mark.slow
def test_truth_outside_candidates_refutes_closed_world_and_retracts():
    cands = (O1_LATENT_CAUSAL, O2_INDEPENDENT, O3_LATENT_CONFOUNDED)
    rep = inquire(Interface("copy_chain", ALL_ACTIONS, seed=5), cands, seed=5)
    assert rep["survivors"] == []
    a = answers(rep)
    assert a["S1 and S2 measure a shared hidden quantity"] == ("OUT-OF-SCOPE", "UNDETERMINED")
    L = rep["ledger"]
    earlier = [c for c in L.claims.values() if c.category == "answer" and "shared hidden" in c.statement]
    assert any(L.effective_status(c.id) is Status.RETRACTED for c in earlier)  # history kept
    assert a["intervening on A changes Y"] == ("EMPIRICALLY-SUPPORTED", "YES")  # tested directly


@pytest.mark.slow
def test_revisions_are_recorded_with_commitment_diffs():
    rep = inquire(Interface("copy_chain", ALL_ACTIONS, seed=6), CANDIDATES, seed=6)
    L = rep["ledger"]
    revs = [c for c in L.claims.values() if c.category == "ontology-revision"]
    assert revs
    for r in revs:
        ev = r.evidence
        assert {"dropped", "surviving", "commitments_settled", "commitments_still_open"} <= set(ev)
        assert r.depends_on  # motivated by recorded evidence


# ------------------------------------------------------------ ledger retraction

def test_retraction_propagates():
    L = Ledger()
    a = L.conjecture("a", rationale="r", open_obligation="o")
    b = L.derived("b", depends_on=[a.id], rule="r", category="t")
    c = L.derived("c", depends_on=[b.id], rule="r", category="t")
    rev = L.boundary("revision", reason="x")
    assert L.affected_by(a.id) == [b.id, c.id]
    L.retract(a.id, by=rev.id)
    assert L.effective_status(c.id) is Status.RETRACTED
    assert a.id in L.claims  # history preserved


# ------------------------------------------------------------ H2.3

def test_sufficiency_signature_screening_off_vs_complementarity():
    obs = ("A", "S1", "S2", "Y")
    lat = minimal_eps_sufficient(Interface("latent_causal", seed=1).run({}, 20000),
                                 obs, ("A", "S1", "S2"), "Y", 0.0)
    cop = minimal_eps_sufficient(Interface("copy_chain", seed=1).run({}, 20000),
                                 obs, ("A", "S1", "S2"), "Y", 0.0)
    assert lat["sets"] == [["A", "S1", "S2"]]  # noisy channels are complementary
    assert cop["sets"] == [["S1"]]             # S1 screens off S2 and A
    assert lat["substitutable"] == cop["substitutable"] == []


def test_direct_measurement_survives_collapse_of_every_ontology():
    """Spike-02 finding F5: measured facts must not be hostage to theory."""
    from cerp.epistemics.ontologies import O4_COPY_CHAIN
    cands = (O2_INDEPENDENT, O3_LATENT_CONFOUNDED, O4_COPY_CHAIN)  # truth (O1) missing
    rep = inquire(Interface("latent_causal", ALL_ACTIONS[:3], seed=7), cands, seed=7)
    assert rep["survivors"] == []
    st, head = answers(rep)["intervening on A changes Y"]
    assert (st, head) == ("EMPIRICALLY-SUPPORTED", "YES")
    assert "no ontology" in rep["answers"]["intervening on A changes Y"]["statement"]


# ------------------------------------------------------------ Spike 02b: generation

def test_dag_enumeration_count_matches_known_values():
    from cerp.epistemics.generate import enumerate_dags
    assert sum(1 for _ in enumerate_dags(("a", "b", "c", "d"))) == 543       # OEIS A003024
    assert sum(1 for _ in enumerate_dags(("a", "b", "c"))) == 25


@pytest.mark.slow
def test_generation_respects_measured_facts_and_refutations():
    from cerp.epistemics.generate import _reach, canon_of_structure, constrained_structures
    facts = [("A", "Y", True), ("S1", "Y", False)]
    refuted = {canon_of_structure(O4_COPY_CHAIN)}
    out, counts = constrained_structures(("A", "S1", "S2", "Y"), facts, refuted)
    assert counts["after_measured_facts"] < counts["after_hygiene"]
    for edges, lat in out:
        assert "Y" in _reach(edges, "A") and "Y" not in _reach(edges, "S1")
        assert all(sum(a == z for a, _ in edges) >= 2 for z in lat)


@pytest.mark.slow
def test_generation_recovers_a_truth_outside_every_candidate_and_stays_conditional():
    from cerp.epistemics.generate import canon_of_structure
    from cerp.epistemics.inquiry import EXTENDED_QUERIES
    from cerp.epistemics.world import truth
    rep = inquire(Interface("direct_and_latent", ALL_ACTIONS, seed=11), CANDIDATES, seed=11,
                  queries=EXTENDED_QUERIES, generate_on_refutation=True, max_rounds=40)
    true_c = canon_of_structure(truth("direct_and_latent")[0])
    gs = rep["generated_structures"]
    assert any(canon_of_structure(gs[n]) == true_c for n in rep["survivors"])
    L = rep["ledger"]
    gen = [c for c in L.claims.values() if c.category == "ontology-generation"]
    assert gen and gen[0].depends_on  # provenance: measured facts + faithfulness premise
    assert any("Faithfulness" in L.claims[d].statement for d in gen[0].depends_on)
    # model-derived answers are conditional on the GENERATED closed world, by name
    for a in rep["answers"].values():
        if a["status"] == "CONJECTURE":
            conds = L.effective_warrant(a["claim"]).conditions
            assert any("generation" in L.claims[c].statement for c in conds)
