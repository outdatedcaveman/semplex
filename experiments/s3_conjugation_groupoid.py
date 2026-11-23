"""Exhaustive S3 conjugation groupoid / centralizer calculation.

Permutations are tuples p with p[i] the image of i. Composition is p after q.
This finite experiment checks the exact orbit/isotropy decomposition used by
ConjugationSemanticGroupoid.lean; it is not a substitute for that theorem.
"""
from __future__ import annotations

from collections import Counter
from itertools import permutations
import json
from pathlib import Path


def compose(p: tuple[int, ...], q: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(p[q[i]] for i in range(len(p)))


def inverse(p: tuple[int, ...]) -> tuple[int, ...]:
    out = [0] * len(p)
    for i, j in enumerate(p):
        out[j] = i
    return tuple(out)


def conjugate(g: tuple[int, ...], x: tuple[int, ...]) -> tuple[int, ...]:
    return compose(compose(g, x), inverse(g))


def cycle_type(p: tuple[int, ...]) -> str:
    seen: set[int] = set()
    lengths = []
    for i in range(len(p)):
        if i not in seen:
            j, n = i, 0
            while j not in seen:
                seen.add(j)
                n += 1
                j = p[j]
            if n > 1:
                lengths.append(n)
    if not lengths:
        return "identity"
    if sorted(lengths) == [2]:
        return "transposition"
    if sorted(lengths) == [3]:
        return "3-cycle"
    return "cycle-type-" + "-".join(map(str, sorted(lengths)))


def main() -> dict:
    G = list(permutations(range(3)))
    identity = tuple(range(3))
    assert len(G) == 6
    # Group closure and inverse sanity.
    for a in G:
        assert compose(a, inverse(a)) == identity
        for b in G:
            assert compose(a, b) in G

    centralizers = {
        x: [g for g in G if compose(g, x) == compose(x, g)]
        for x in G
    }
    orbits: list[set[tuple[int, ...]]] = []
    unseen = set(G)
    while unseen:
        x = min(unseen)
        orbit = {conjugate(g, x) for g in G}
        orbits.append(orbit)
        unseen -= orbit

    orbit_sizes = sorted(len(o) for o in orbits)
    centralizer_sizes = Counter(len(centralizers[x]) for x in G)
    class_summary = []
    for orbit in sorted(orbits, key=lambda o: (len(o), sorted(o))):
        rep = min(orbit)
        centralizer = centralizers[rep]
        centralizer_abelian = all(
            compose(a, b) == compose(b, a)
            for a in centralizer for b in centralizer
        )
        class_summary.append({
            "cycle_type": cycle_type(rep),
            "class_size": len(orbit),
            "centralizer_size": len(centralizer),
            "centralizer_abelian": centralizer_abelian,
            "centralizer_element_cycle_types": sorted(cycle_type(g) for g in centralizer),
            "centralizer_group_type": (
                "S3" if len(centralizer) == 6 and not centralizer_abelian
                else f"C{len(centralizer)}" if centralizer_abelian
                else "unclassified"
            ),
            "orbit_stabilizer_product": len(orbit) * len(centralizer),
        })

    hom_count = 0
    pair_hom_counts = {}
    for x in G:
        for y in G:
            arrows = [g for g in G if conjugate(g, x) == y]
            pair_hom_counts[f"{G.index(x)}->{G.index(y)}"] = len(arrows)
            if arrows:
                assert len(arrows) == len(centralizers[x])
                assert len(centralizers[x]) == len(centralizers[y])
            hom_count += len(arrows)

    result = {
        "group": "S3",
        "group_order": len(G),
        "conjugacy_class_count": len(orbits),
        "orbit_sizes": orbit_sizes,
        "class_summary": class_summary,
        "centralizer_size_distribution": dict(sorted(centralizer_sizes.items())),
        "ordered_object_pairs": len(G) ** 2,
        "nonempty_hom_pairs": sum(v > 0 for v in pair_hom_counts.values()),
        "total_groupoid_arrows": hom_count,
        "sum_centralizer_sizes": sum(len(v) for v in centralizers.values()),
        "pair_hom_counts": pair_hom_counts,
        "checks": {
            "class_sizes_sum_to_group_order": sum(orbit_sizes) == len(G),
            "orbit_stabilizer": all(
                c["class_size"] * c["centralizer_size"] == len(G)
                for c in class_summary
            ),
            "total_arrows_equals_object_count_times_group_order":
                hom_count == len(G) * len(G),
            "loop_count_equals_sum_centralizers": sum(
                len(v) for v in centralizers.values()
            ) == 18,
            "three_conjugacy_classes": len(orbits) == 3,
            "centralizer_sizes_are_6_2_3": sorted(
                len(centralizers[x]) for x in G
            ) == [2, 2, 2, 3, 3, 6],
        },
    }
    assert all(result["checks"].values())
    return result


if __name__ == "__main__":
    data = main()
    out = Path(__file__).resolve().parents[1] / "artifacts" / "s3-conjugation-groupoid-20261122.json"
    out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(data, indent=2))
