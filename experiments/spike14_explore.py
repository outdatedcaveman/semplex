"""Spike 14 exploratory screen of new candidate principles on ALREADY-SEEN data (Spikes 12-13).
Hypothesis generation only; nothing here decides a verdict.  python -m experiments.spike14_explore"""
import json, math
import numpy as np
from collections import defaultdict
from cerp import atlas, mechvol
from experiments import spike12 as S12, spike13 as S13

FULL = 0xFFFF


def stab_group(g, T):
    """Automorphisms and anti-automorphisms of g in the hyperoctahedral group (input perm/negation),
    as index arrays. Training is equivariant under these (init and loss are invariant), so the
    distribution over isomers must be constant on their orbits."""
    G = []
    for perm, neg, idx in T:
        h = atlas.apply_T(g, idx, False, 4)
        if h == g or h == FULL ^ g:
            G.append(idx)
    return G


def act(t, idx):
    return int(mechvol.canon(atlas.apply_T(t, idx, False, 4)))


def orbits(iso, G):
    key = {}
    for a, b in iso:
        key[f"{a}-{b}"] = min(tuple(sorted((act(a, idx), act(b, idx)))) for idx in G)
    return key


def main():
    tb, els, iso = S12.elements()
    T = atlas.transforms(4)
    data = {f"S12:{p.stem}": json.loads(p.read_text()) for p in sorted(S12.RAW.glob("*.json"))}
    data.update({p.stem: json.loads(p.read_text()) for p in sorted(S13.RAW.glob("*.json"))})
    info = {}
    for e in els:
        G = stab_group(e, T)
        ok = orbits(iso[e], G)
        deg = defaultdict(int)
        for a, b in iso[e]:
            deg[a] += 1; deg[b] += 1
        info[e] = (G, ok, deg)
    print("stabilizer sizes", sorted({len(v[0]) for v in info.values()}),
          "isomers/orbits mean", np.mean([len(iso[e]) / len(set(info[e][1].values())) for e in els]).round(2))
    for n, d in data.items():
        rho = defaultdict(list); chi = []
        for e in els:
            G, ok, deg = info[e]
            c = d["counts"]["R2"][str(e)]
            tot = {f"{a}-{b}": c[0].get(f"{a}-{b}", 0) + c[1].get(f"{a}-{b}", 0) for a, b in iso[e]}
            N = sum(tot.values())
            if N == 0:
                continue
            osz = defaultdict(int)
            for k in tot: osz[ok[k]] += 1
            keys = list(tot); y = np.array([tot[k] for k in keys])
            # within-orbit uniformity: share of variance of counts that is within orbits
            om = defaultdict(list)
            for k in keys: om[ok[k]].append(tot[k])
            within = sum(np.var(v) * len(v) for v in om.values()); total = np.var(y) * len(y)
            if total > 0: chi.append(within / total)
            feats = {"orbit_uniform": [-math.log(osz[ok[k]]) for k in keys],
                     "hub_sum": [deg[int(k.split('-')[0])] + deg[int(k.split('-')[1])] for k in keys],
                     "hub_max": [max(deg[int(k.split('-')[0])], deg[int(k.split('-')[1])]) for k in keys]}
            for f, x in feats.items():
                rho[f].append(mechvol._spearman(y, np.array(x, float)))
        print(n.ljust(12), {f: round(float(np.nanmedian(v)), 2) for f, v in rho.items()},
              "within-orbit share of count variance", round(float(np.mean(chi)), 2))


if __name__ == "__main__":
    main()


def orbit_level():
    """Orbit masses vs orbit sizes: mass ~ |orbit|^beta. beta=1: every circuit equal (entropy);
    beta=0: every symmetry TYPE equal (equipartition over types)."""
    tb, els, iso = S12.elements()
    T = atlas.transforms(4)
    data = {f"S12:{p.stem}": json.loads(p.read_text()) for p in sorted(S12.RAW.glob("*.json"))}
    data.update({p.stem: json.loads(p.read_text()) for p in sorted(S13.RAW.glob("*.json"))})
    pc = lambda t: bin(t).count("1")
    pre = {}
    for e in els:
        ok = orbits(iso[e], stab_group(e, T))
        osz = defaultdict(int)
        for k in ok.values(): osz[k] += 1
        ag = {k: max(max(16 - pc(t ^ e), pc(t ^ e)) for t in k) for k in osz}
        pre[e] = (ok, osz, ag)
    for n, d in data.items():
        X, Y, A, rag = [], [], [], []
        for e in els:
            ok, osz, ag = pre[e]
            c = d["counts"]["R2"][str(e)]
            mass = defaultdict(float)
            for k, o in ok.items():
                mass[o] += c[0].get(k, 0) + c[1].get(k, 0)
            N = sum(mass.values()); K = len(osz)
            if N == 0 or K < 2:
                continue
            ls = np.log([osz[o] for o in osz]); ls -= ls.mean()
            for o in osz:
                X.append(math.log(osz[o]) - np.mean([math.log(osz[q]) for q in osz]))
                Y.append(mass[o] / N * K)          # 1 = equipartition over types
            y = np.array([mass[o] / osz[o] for o in osz]); x = np.array([ag[o] for o in osz])
            rag.append(mechvol._spearman(np.array([mass[o] for o in osz]), x))
        X, Y = np.array(X), np.array(Y)
        # beta by binned log-log on relative orbit size
        q = np.quantile(X, np.linspace(0, 1, 7)); bx, by = [], []
        for i in range(6):
            m = (X >= q[i]) & ((X <= q[i + 1]) if i == 5 else (X < q[i + 1]))
            if m.sum() and Y[m].mean() > 0:
                bx.append(X[m].mean()); by.append(math.log(Y[m].mean()))
        beta = np.polyfit(bx, by, 1)[0] if len(bx) > 1 else float("nan")
        print(n.ljust(12), "beta", round(float(beta), 2), "orbit-level spearman(mass, agreement)", round(float(np.nanmedian(rag)), 2))


if __name__ == "__main__":
    orbit_level()
