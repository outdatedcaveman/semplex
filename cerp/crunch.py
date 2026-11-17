"""Resumable number-crunching jobs for the circuit atlas (Spike 08b).

    python -m cerp.crunch --job all --hours 7.5 --procs 4

Every job appends one JSON line per finished unit to atlas/jobs/<job>.jsonl
and skips units already there, so it can be stopped and restarted at any
time (kill it, reboot, re-run the same command). Nothing here is trusted:
SAT answers are kernel-checked before being written; UNSAT answers are
solver claims inside a declared weight box.

Jobs
  families   min neurons of every 3- and 4-input element in three new families:
             skip (any neuron reads everything before it), relu (one hidden
             ReLU layer), relu_skip (ReLU hidden layer, output also reads inputs)
  n5         hunt for a depth-sensitive 5-input element: f = XOR(g1, g2) of two
             single neurons (5 neurons at depth 3); is it computable at depth 2
             with 3 or 4 hidden neurons?
  geometry   weight-space geometry of larger grids
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import pathlib
import random
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
JOBS = ROOT / "atlas" / "jobs"


def _done(job):
    p = JOBS / f"{job}.jsonl"
    if not p.exists():
        return set()
    return {json.loads(l)["unit"] for l in p.read_text().splitlines() if l.strip()}


def _verify(n, f, art, care=None):
    from . import atlas, kernel
    return kernel.check({"relation": "extensional", "vars": atlas.names(n), "left": art,
                         "right": atlas.table_artifact(n, f)}).ok


# ------------------------------------------------------------ families

def _netsolve():
    from . import netsolve  # optional dependency (ortools); imported only when a family job runs
    return netsolve


FAMILY_SPECS = {
    "skip": lambda n, k: _netsolve().chain(n, k),
    "relu": lambda n, k: _netsolve().layered(n, [k - 1], act="relu"),
    "relu_skip": lambda n, k: _netsolve().layered(n, [k - 1], act="relu", skip=True),
}
FAMILY_W = {"skip": 3, "relu": 3, "relu_skip": 3}


def families_units():
    from . import atlas
    tb = atlas.build_all(4)
    units = []
    for n in (3, 4):
        for c in tb[n].classes():
            for fam in FAMILY_SPECS:
                units.append({"unit": f"{fam}:n{n}:{c}", "fam": fam, "n": n, "f": int(tb[n].exhibit[c]),
                              "cls": int(c), "layered_neurons": int(tb[n].hi[tb[n].exhibit[c]])})
    return units


def families_work(u, tl=600.0):
    from . import netsolve
    n, f, fam = u["n"], u["f"], u["fam"]
    res = {"unit": u["unit"], "fam": fam, "n": n, "cls": u["cls"], "f": f,
           "layered_neurons": u["layered_neurons"], "W": FAMILY_W[fam], "trace": []}
    for k in range(1, 7):
        if fam != "skip" and k == 1:
            spec = netsolve.chain(n, 1)       # a lone step neuron is in every family
        else:
            spec = FAMILY_SPECS[fam](n, k)
        t = time.time()
        st, art = netsolve.solve(f, n, spec, W=FAMILY_W[fam], time_limit=tl, workers=1)
        res["trace"].append([k, st, round(time.time() - t, 2)])
        if st == "sat":
            res.update(neurons=k, verified=bool(_verify(n, f, art)), net=art["body"]["neurons"],
                       lower_bounds_all_unsat=all(s == "unsat" for _, s, _ in res["trace"][:-1]))
            return res
        if st == "unknown":
            res.update(neurons=None, note=f"time limit at k={k}")
            return res
    res.update(neurons=None, note="not found with <= 6 neurons")
    return res


# ------------------------------------------------------------ n = 5 depth hunt

def _rand_neuron(rng, n=5, W=5):
    while True:
        w = [rng.randint(-W, W) for _ in range(n)]
        t = rng.randint(-sum(abs(v) for v in w), sum(abs(v) for v in w) + 1)
        bits = sum(1 << x for x in range(1 << n) if sum(w[j] * ((x >> j) & 1) for j in range(n)) >= t)
        if 0 < bin(bits).count("1") < (1 << n) and sum(1 for v in w if v) >= 4:
            return w, t, bits


def n5_units(count=100000):
    return [{"unit": f"xor:{i}", "i": i} for i in range(count)]


def n5_work(u, tl=900.0):
    from . import netsolve
    rng = random.Random(550000 + u["i"])
    w1, t1, g1 = _rand_neuron(rng)
    w2, t2, g2 = _rand_neuron(rng)
    f = g1 ^ g2
    res = {"unit": u["unit"], "f": f, "g1": [w1, t1], "g2": [w2, t2], "W": 5}
    if f == 0 or f == (1 << 32) - 1:
        res["skip"] = "constant"
        return res
    # depth-3 witness with 5 neurons, strictly layered (2, 2, 1): OR and NAND, then AND
    d3 = {"kind": "dnet", "body": {"inputs": [f"x{i}" for i in range(5)], "neurons": [
        {"in": [0, 1, 2, 3, 4], "w": w1, "b": -t1, "act": "step"},
        {"in": [0, 1, 2, 3, 4], "w": w2, "b": -t2, "act": "step"},
        {"in": [5, 6], "w": [1, 1], "b": -1, "act": "step"},
        {"in": [5, 6], "w": [-1, -1], "b": 1, "act": "step"},
        {"in": [7, 8], "w": [1, 1], "b": -2, "act": "step"}]}}
    res["depth3_5_neurons_verified"] = bool(_verify(5, f, d3))
    for width in (1, 2, 3, 4):
        t = time.time()
        st, art = netsolve.solve(f, 5, netsolve.layered(5, [width]) if width > 1 else netsolve.chain(5, 1),
                                 W=5, time_limit=tl, workers=1)
        res[f"depth2_width{width}"] = st
        res[f"secs{width}"] = round(time.time() - t, 1)
        if st == "sat":
            res["depth2_neurons"] = width + (1 if width > 1 else 0)
            res["depth2_verified"] = bool(_verify(5, f, art))
            res["depth2_net"] = art["body"]["neurons"]
            break
        if st == "unknown":
            break
    res["depth_sensitive"] = all(res.get(f"depth2_width{w}") == "unsat" for w in (1, 2, 3, 4))
    return res


# ------------------------------------------------------------ geometry

def geometry_units():
    return [{"unit": f"geo:n{n}:h{h}:W{W}", "n": n, "h": h, "W": W}
            for (n, h, W) in ((2, 2, 1), (2, 2, 2), (2, 2, 3), (3, 2, 1), (2, 3, 1), (3, 2, 2))]


def geometry_work(u):
    from . import atlas, geometry
    tb = atlas.build_all(3)
    r = geometry.analyse(u["n"], u["h"], u["W"], tb[u["n"]].canon, tb[u["n"]].hi)
    r["unit"] = u["unit"]
    return r


JOBS_TABLE = {"families": (families_units, families_work), "geometry": (geometry_units, geometry_work),
              "n5": (n5_units, n5_work)}


def _call(args):
    job, u = args
    try:
        return job, JOBS_TABLE[job][1](u)
    except Exception as exc:  # record and move on; a crash must not stop the night
        return job, {"unit": u["unit"], "error": repr(exc)}


def run(jobs, hours, procs):
    JOBS.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + hours * 3600
    todo = []
    for job in jobs:
        done = _done(job)
        todo += [(job, u) for u in JOBS_TABLE[job][0]() if u["unit"] not in done]
    print(f"{len(todo)} units to do; {procs} processes; budget {hours} h", flush=True)
    n = 0
    with mp.Pool(procs, maxtasksperchild=50) as pool:
        for job, res in pool.imap_unordered(_call, todo, chunksize=1):
            with open(JOBS / f"{job}.jsonl", "a") as fh:
                fh.write(json.dumps(res) + "\n")
            n += 1
            if n % 20 == 0:
                print(f"{n} done", flush=True)
            if time.time() > deadline:
                pool.terminate()
                break
    print(f"finished {n} units this run", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", default="all")
    ap.add_argument("--hours", type=float, default=1.0)
    ap.add_argument("--procs", type=int, default=max(1, mp.cpu_count()))
    a = ap.parse_args()
    run(["families", "geometry", "n5"] if a.job == "all" else a.job.split(","), a.hours, a.procs)
