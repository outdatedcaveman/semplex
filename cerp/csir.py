"""CSIR v0.1 -- Canonical Semantic Intermediate Representation (Spike 07).

Extracted (rule of three) from what Spikes 01, 02/02b, 03, 04 and 05 all
needed, rather than designed up front. A CSIR *bundle* is plain JSON:

  {"csir": "0.1",
   "nodes": [Node...], "links": [Link...]}

  Node  -- one computational or world-model object
    id, artifact {kind, body},
    interface    {"vars": [...]} | {"actions": [...]} | {"observables", "latents", "protocols"}
    ontology     optional: typed commitments (Spike 02: what the model posits)
    resources    optional: cost vector + the cost model it is measured in
    provenance   source / produced_by (translator, generator) / parents

  Link  -- a claimed semantic relation between two nodes
    from, to, relation, protocol (the Omega it is relative to),
    certificate  whatever the kernel needs to RE-CHECK it from the bundle alone
    warrant      basis / trusted_base / conditions (Spike 04)

Semantic relations are a registry, ordered by inclusion (finer => coarser):
  extensional ⊆ task[care]         (Spike 01 F6)
  bisimulation ⊆ completed-trace ⊆ trace   (Spike 05)
  interventional[protocols] ⊆ interventional[subset]   (Spike 02: Omega-indexed)
Chains compose only along this order and only under the SAME protocol
(charter §7.3); otherwise `compose` refuses with a reason.
"""

from __future__ import annotations

from . import kernel, kernel_lts
from .ledger import Ledger, Warrant

CSIR_VERSION = "0.1"

# relation -> (artifact kinds it applies to, relations it is finer than)
RELATIONS = {
    "extensional": ({"expr", "circuit", "dfa", "bdd"}, {"task"}),
    "task": ({"expr", "circuit", "dfa", "bdd"}, set()),
    "bisimulation": ({"lts"}, {"completed-trace", "trace"}),
    "completed-trace": ({"lts"}, {"trace"}),
    "trace": ({"lts"}, set()),
    "interventional": ({"causal-model", "world"}, set()),
    "adequate-to": ({"causal-model", "world"}, set()),
    "distills": ({"causal-model", "lts", "expr", "circuit"}, set()),
}


class CSIRError(Exception):
    pass


# ------------------------------------------------------------ construction

def node(id, artifact, interface, *, ontology=None, resources=None, provenance=None):
    return {"id": id, "artifact": artifact, "interface": interface, "ontology": ontology,
            "resources": resources, "provenance": provenance or {}}


def warrant_dict(w: Warrant):
    return {"basis": sorted(m.value for m in w.basis), "trusted_base": sorted(w.trusted_base),
            "conditions": sorted(w.conditions)}


def link(frm, to, relation, protocol, *, certificate=None, warrant=None, claim=None):
    return {"from": frm, "to": to, "relation": relation, "protocol": protocol,
            "certificate": certificate, "warrant": warrant, "claim": claim}


def bundle(nodes, links):
    return {"csir": CSIR_VERSION, "nodes": nodes, "links": links}


# ------------------------------------------------------------ relation order

def finer_or_equal(r1, r2):
    return r1 == r2 or r2 in RELATIONS[r1][1]


def _proto_key(rel, proto):
    return repr(sorted((proto or {}).items()))


def compose(l1, l2):
    """Compose l1: A -> B and l2: B -> C. Returns (link, None) or (None, reason)."""
    if l1["to"] != l2["from"]:
        return None, "links do not meet"
    p1, p2 = l1["protocol"] or {}, l2["protocol"] or {}
    if l1["relation"] in ("interventional", "adequate-to") or l2["relation"] in ("interventional", "adequate-to"):
        return None, "empirical relations do not compose by transitivity (adequacy is not transitive)"
    if _proto_key(None, p1) != _proto_key(None, p2):
        return None, f"protocols differ: {p1} vs {p2} (contracts must match, charter §7.3)"
    r1, r2 = l1["relation"], l2["relation"]
    if finer_or_equal(r1, r2):
        rel = r2
    elif finer_or_equal(r2, r1):
        rel = r1
    else:
        return None, f"relations {r1} and {r2} are incomparable"
    w = None
    if l1.get("warrant") and l2.get("warrant"):
        w = {k: sorted(set(l1["warrant"][k]) | set(l2["warrant"][k])) for k in ("basis", "trusted_base", "conditions")}
    return link(l1["from"], l2["to"], rel, p1, warrant=w,
                certificate={"composed_of": [l1.get("claim"), l2.get("claim")]}), None


# ------------------------------------------------------------ validation

def validate(b):
    """Structural well-formedness. Returns a list of problems (empty = valid)."""
    errs = []
    if b.get("csir") != CSIR_VERSION:
        errs.append(f"unsupported CSIR version {b.get('csir')!r}")
    ids = {}
    for n in b.get("nodes", []):
        for f in ("id", "artifact", "interface"):
            if f not in n:
                errs.append(f"node missing {f}: {n.get('id')}")
        if n.get("id") in ids:
            errs.append(f"duplicate node id {n['id']}")
        ids[n.get("id")] = n
        if n.get("resources") and "cost_model" not in n["resources"]:
            errs.append(f"{n['id']}: resources without a declared cost model (Spike 01 F5)")
    for l in b.get("links", []):
        rel = l.get("relation")
        if rel not in RELATIONS:
            errs.append(f"unknown relation {rel!r}")
            continue
        for end in ("from", "to"):
            if l.get(end) not in ids:
                errs.append(f"link endpoint {l.get(end)!r} is not a node")
        kinds = RELATIONS[rel][0]
        for end in ("from", "to"):
            n = ids.get(l.get(end))
            if n and n["artifact"]["kind"] not in kinds:
                errs.append(f"relation {rel} does not apply to a {n['artifact']['kind']} ({n['id']})")
        if rel == "task" and not (l.get("protocol") or {}).get("care"):
            errs.append("task relation without a care set in its protocol")
        if not l.get("warrant"):
            errs.append(f"link {l.get('from')}->{l.get('to')} has no warrant")
        elif "kernel-checked" in l["warrant"]["basis"] and not l.get("certificate"):
            errs.append(f"link {l['from']}->{l['to']} claims kernel-checked but carries no certificate")
    return errs


# ------------------------------------------------------------ re-verification

def recheck(b):
    """Re-verify every kernel-checked link FROM THE BUNDLE ALONE (charter §12.3:
    independently inspectable artifacts). Returns [(link index, status)]."""
    ids = {n["id"]: n for n in b["nodes"]}
    out = []
    for i, l in enumerate(b["links"]):
        basis = (l.get("warrant") or {}).get("basis", [])
        if "kernel-checked" not in basis:
            out.append((i, "not kernel-checkable: " + "+".join(basis)))
            continue
        A, B, cert, rel, proto = ids[l["from"]]["artifact"], ids[l["to"]]["artifact"], l["certificate"], \
            l["relation"], l["protocol"] or {}
        try:
            out.append((i, _recheck_one(A, B, cert, rel, proto)))
        except (kernel.KernelError, KeyError, TypeError) as exc:
            out.append((i, f"FAILED (malformed: {exc!r})"))
    return out


def _recheck_one(A, B, cert, rel, proto):
    if rel in ("extensional", "task"):
        claim = {"vars": proto["vars"], "left": A, "right": B}
        if rel == "task":
            claim["care"] = proto["care"]
        if cert.get("method") == "exhaustive":
            v = kernel.check({**claim, "relation": rel})
        elif cert.get("method") == "rup":
            v = kernel.check_rup({**claim, "certificate": cert["lemmas"]})
        else:
            return "unknown certificate method"
    elif rel == "bisimulation":
        v = kernel_lts.check_bisimulation(A, B, cert["relation"])
    elif rel in ("trace", "completed-trace"):
        v = kernel_lts.check_trace_cert(A, B, cert["pairs"], completed=rel == "completed-trace")
    else:
        return "no kernel route"
    return "verified" if v.ok else "FAILED"


# ------------------------------------------------------------ exporters

def from_pipeline(rep, source, care=None):
    """Spike 01 pipeline report -> bundle (source node + every verified candidate)."""
    L: Ledger = rep["ledger"]
    vars_ = rep["vars"]
    nodes = [node("source", source, {"vars": vars_}, provenance={"produced_by": "user"})]
    links = []
    for k, c in enumerate(rep["candidates"]):
        if c["translator"] == "identity" or c["artifact"]["kind"] not in RELATIONS[c["relation"]][0]:
            continue
        nid = f"cand{k}"
        nodes.append(node(nid, c["artifact"], {"vars": vars_},
                          resources={"cost": c["cost"], "cost_model": f"F0/{c['substrate']}"},
                          provenance={"produced_by": c["translator"], "parents": ["source"]}))
        proto = {"vars": vars_}
        if c["relation"] == "task":
            proto["care"] = care
        links.append(link("source", nid, c["relation"], proto, certificate={"method": "exhaustive"},
                          warrant=warrant_dict(L.effective_warrant(c["claim"])), claim=c["claim"]))
    return bundle(nodes, links)


def from_inquiry(rep, protocols):
    """Spike 02 inquiry report -> bundle: the world as a node reachable only by
    protocol, surviving models as nodes carrying their ontological commitments."""
    L: Ledger = rep["ledger"]
    nodes = [node("world", {"kind": "world", "body": None},
                  {"observables": ["A", "S1", "S2", "Y"], "protocols": protocols},
                  provenance={"produced_by": "measurement interface"})]
    links = []
    structs = {**{m.name: m for m in rep.get("candidate_structures", [])}, **rep.get("generated_structures", {})}
    for name in rep["survivors"]:
        s = structs.get(name)
        nid = name.split(":")[0]
        nodes.append(node(nid, {"kind": "causal-model", "body": {"parents": {k: list(v) for k, v in s.parents.items()},
                                                                 "latents": list(s.latents)}} if s else
                          {"kind": "causal-model", "body": name},
                          {"observables": ["A", "S1", "S2", "Y"], "latents": list(s.latents) if s else []},
                          ontology={"commitments": sorted(map(list, s.commitments()))} if s else None,
                          provenance={"produced_by": "generation" if name in rep.get("generated_structures", {})
                                      else "researcher"}))
        ad = [c for c in L.claims.values() if c.category == "adequacy" and c.statement.startswith(name)
              and "NOT" not in c.statement]
        if ad:
            links.append(link(nid, "world", "adequate-to", {"protocols": rep["tested_protocols"]},
                              certificate={"evidence": [c.evidence for c in ad]},
                              warrant=warrant_dict(L.effective_warrant(ad[-1].id)), claim=ad[-1].id))
    return bundle(nodes, links)


def distill_causal_rule(structure, params, target="Y", *, features=None, do=None,
                      model_id="model", threshold=0.5):
    """Spike 12 bridge: distill a causal Bayes net's Bayes-optimal decision rule
    P(target=1 | features, do) >= threshold into a canonical F0 expr + circuit,
    exporting a CSIR bundle with a kernel-checked expr <-> circuit link."""
    from .epistemics.bayesnet import distribution
    from .semantics import TruthTable
    from .substrates import cost
    from .translate import bdd_to_circuit, bdd_to_expr, truthtable_to_bdd

    obs = list(structure.observables)
    if target not in obs:
        raise CSIRError(f"target {target!r} not in observables {obs}")
    feats = list(features) if features is not None else [v for v in obs if v != target]
    t_idx = obs.index(target)
    f_idxs = [obs.index(v) for v in feats]
    dist = distribution(structure, params, do=do)

    def predict(env):
        key = tuple(env[v] for v in feats)
        p1, pt = 0.0, 0.0
        for cell, prob in dist.items():
            if tuple(cell[i] for i in f_idxs) == key:
                pt += prob
                if cell[t_idx] == 1:
                    p1 += prob
        return int(pt > 0 and (p1 / pt) >= threshold)

    tt = TruthTable.from_function(feats, predict)
    bdd_art = truthtable_to_bdd(tt)
    expr_art = bdd_to_expr(bdd_art)
    circ_art = bdd_to_circuit(bdd_art, feats)
    v = kernel.check({"relation": "extensional", "vars": feats, "left": expr_art, "right": circ_art})
    if not v.ok:
        raise CSIRError("distilled circuit failed kernel equivalence check")

    m_node = node(
        model_id,
        {"kind": "causal-model", "body": {"parents": {k: list(v_) for k, v_ in structure.parents.items()},
                                          "latents": list(structure.latents)}},
        {"observables": obs, "latents": list(structure.latents)},
        ontology={"commitments": sorted(map(list, structure.commitments()))},
        provenance={"produced_by": "causal-model"},
    )
    e_id, c_id = f"{model_id}_rule", f"{model_id}_circuit"
    e_node = node(e_id, expr_art, {"vars": feats}, provenance={"produced_by": "bayes-optimal-distill", "parents": [model_id]})
    c_node = node(c_id, circ_art, {"vars": feats},
                  resources={"cost": cost(circ_art), "cost_model": "F0/circuit"},
                  provenance={"produced_by": "bdd_to_circuit", "parents": [e_id]})
    l_distill = link(
        model_id, e_id, "distills",
        {"target": target, "features": feats, "threshold": threshold, "do": do or {}},
        warrant={"basis": ["empirical"], "trusted_base": ["cerp/epistemics/bayesnet.py"],
                 "conditions": ["model-adequacy", f"threshold={threshold}"]},
    )
    l_equiv = link(
        e_id, c_id, "extensional", {"vars": feats},
        certificate={"method": "exhaustive"},
        warrant={"basis": ["kernel-checked"], "trusted_base": ["cerp/kernel.py"], "conditions": []},
    )
    return bundle([m_node, e_node, c_node], [l_distill, l_equiv])
