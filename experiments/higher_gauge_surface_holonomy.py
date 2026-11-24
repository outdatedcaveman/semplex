#!/usr/bin/env python3
"""Exact finite 2-groupoid test for a Z2 2-form gauge field on S^2.

The base is the boundary complex of a tetrahedron. Objects are face
2-cochains B; 1-morphisms are edge gauge parameters Lambda; 2-morphisms
are vertex gauge-of-gauge parameters eta. All arithmetic is over F_2.
"""
from collections import Counter
from itertools import combinations, product
import json


VERTICES = tuple(range(4))
EDGES = tuple(combinations(VERTICES, 2))
FACES = tuple(combinations(VERTICES, 3))
EDGE_INDEX = {edge: i for i, edge in enumerate(EDGES)}


def parity(bits):
    return sum(bits) % 2


def delta0(vertex_field):
    """C^0 -> C^1: (d eta)(uv) = eta(u) + eta(v)."""
    return tuple(vertex_field[u] ^ vertex_field[v] for u, v in EDGES)


def delta1(edge_field):
    """C^1 -> C^2: (d Lambda)(f) = sum of its three boundary edges."""
    out = []
    for face in FACES:
        value = 0
        for edge in combinations(face, 2):
            value ^= edge_field[EDGE_INDEX[edge]]
        out.append(value)
    return tuple(out)


def xor_vectors(left, right):
    return tuple(a ^ b for a, b in zip(left, right))


def all_bits(n):
    return product((0, 1), repeat=n)


def marginal_counts(configurations, selected_faces):
    return Counter(tuple(config[i] for i in selected_faces)
                   for config in configurations)


def main():
    assert len(VERTICES) == 4 and len(EDGES) == 6 and len(FACES) == 4

    fields = tuple(all_bits(len(FACES)))
    one_forms = tuple(all_bits(len(EDGES)))
    zero_forms = tuple(all_bits(len(VERTICES)))
    zero_edge = (0,) * len(EDGES)
    zero_face = (0,) * len(FACES)

    # Cochain complex: C^0 --d0--> C^1 --d1--> C^2.
    d0_image = {delta0(eta) for eta in zero_forms}
    d1_image = {delta1(lam) for lam in one_forms}
    ker_d0 = {eta for eta in zero_forms if delta0(eta) == zero_edge}
    ker_d1 = {lam for lam in one_forms if delta1(lam) == zero_face}
    even_face_fields = {b for b in fields if parity(b) == 0}
    assert len(d0_image) == 8
    assert len(d1_image) == 8
    assert d1_image == even_face_fields

    # Homotopy groups of the finite 2-groupoid at any object:
    # pi_0 = H^2 = C^2 / im(d1) = Z_2 (two components);
    # pi_1 = H^1 = ker(d1) / im(d0) = 0;
    # pi_2 = H^0 = ker(d0) = Z_2 (a nontrivial 2-automorphism).
    assert ker_d1 == d0_image
    assert len(ker_d1) == 8
    assert len(ker_d0) == 2
    assert ker_d0 == {(0, 0, 0, 0), (1, 1, 1, 1)}
    pi0_size = len(fields) // len(d1_image)
    pi1_size = len(ker_d1) // len(d0_image)
    pi2_size = len(ker_d0)
    assert (pi0_size, pi1_size, pi2_size) == (2, 1, 2)

    # The defining higher-coherence equation d1 o d0 = 0.
    assert all(delta1(delta0(eta)) == zero_face for eta in zero_forms)

    # 1-morphisms: Lambda : B -> B + d1(Lambda).
    def one_morphism(source, target, lam):
        return xor_vectors(source, delta1(lam)) == target

    # Identity, inverse, and composition for all objects and 1-morphisms.
    for source in fields:
        assert one_morphism(source, source, zero_edge)
        for lam in one_forms:
            target = xor_vectors(source, delta1(lam))
            assert one_morphism(source, target, lam)
            assert one_morphism(target, source, lam)  # F_2 inverse
            for mu in one_forms:
                final = xor_vectors(target, delta1(mu))
                composite = xor_vectors(lam, mu)
                assert one_morphism(source, final, composite)

    # Associativity and unit laws of 1-morphism composition.
    for lam in one_forms:
        assert xor_vectors(lam, zero_edge) == lam
        assert xor_vectors(zero_edge, lam) == lam
        for mu in one_forms:
            for nu in one_forms:
                assert xor_vectors(xor_vectors(lam, mu), nu) == \
                       xor_vectors(lam, xor_vectors(mu, nu))

    # 2-morphisms: eta : Lambda ==> Lambda + d0(eta).
    def two_morphism(lam, lam_prime, eta):
        return xor_vectors(lam, delta0(eta)) == lam_prime

    for lam in one_forms:
        assert two_morphism(lam, lam, (0,) * len(VERTICES))
        for eta in zero_forms:
            lam_prime = xor_vectors(lam, delta0(eta))
            assert two_morphism(lam, lam_prime, eta)
            assert two_morphism(lam_prime, lam, eta)  # F_2 inverse

            # Vertical composition: eta then theta is eta + theta.
            for theta in zero_forms:
                lam_double = xor_vectors(lam_prime, delta0(theta))
                eta_vertical = xor_vectors(eta, theta)
                assert two_morphism(lam, lam_double, eta_vertical)

    # Horizontal composition: (eta : lam=>lam') and
    # (theta : mu=>mu') induce eta+theta : lam+mu => lam'+mu'.
    horizontal_checks = 0
    for lam in one_forms:
        for mu in one_forms:
            for eta in zero_forms:
                lam_prime = xor_vectors(lam, delta0(eta))
                for theta in zero_forms:
                    mu_prime = xor_vectors(mu, delta0(theta))
                    assert two_morphism(
                        xor_vectors(lam, mu),
                        xor_vectors(lam_prime, mu_prime),
                        xor_vectors(eta, theta),
                    )
                    horizontal_checks += 1

    # Interchange law follows from commutativity/associativity of F_2 addition.
    interchange_checks = 0
    for eta1 in zero_forms:
        for eta2 in zero_forms:
            for theta1 in zero_forms:
                for theta2 in zero_forms:
                    vertical_then_horizontal = xor_vectors(
                        xor_vectors(eta1, eta2),
                        xor_vectors(theta1, theta2),
                    )
                    horizontal_then_vertical = xor_vectors(
                        xor_vectors(eta1, theta1),
                        xor_vectors(eta2, theta2),
                    )
                    assert vertical_then_horizontal == horizontal_then_vertical
                    interchange_checks += 1

    # Gauge orbits are exactly the two cohomology/surface-holonomy sectors.
    sectors = {}
    for h in (0, 1):
        base = (h, 0, 0, 0)
        sectors[h] = {
            xor_vectors(base, boundary) for boundary in d1_image
        }
        expected = {b for b in fields if parity(b) == h}
        assert sectors[h] == expected
        assert len(sectors[h]) == 8

    # All proper face-subset marginals are uniform and identical in both sectors.
    marginal_checks = 0
    for k in range(len(FACES)):
        for selected in combinations(range(len(FACES)), k):
            counts0 = marginal_counts(sectors[0], selected)
            counts1 = marginal_counts(sectors[1], selected)
            expected_count = 2 ** (3 - k)
            expected_patterns = set(all_bits(k))
            assert set(counts0) == expected_patterns
            assert set(counts1) == expected_patterns
            assert all(c == expected_count for c in counts0.values())
            assert all(c == expected_count for c in counts1.values())
            assert counts0 == counts1
            marginal_checks += 1

    # Global surface holonomy is gauge-invariant and separates the sectors.
    holonomy = {h: {parity(b) for b in sectors[h]} for h in (0, 1)}
    assert holonomy == {0: {0}, 1: {1}}

    result = {
        "model": "tetrahedral S^2, Z2 2-form gauge field, strict 2-groupoid",
        "vertices": len(VERTICES),
        "edges": len(EDGES),
        "faces": len(FACES),
        "d0_image_size": len(d0_image),
        "d1_image_size": len(d1_image),
        "homotopy_groups_at_each_object": {
            "pi0_H2": pi0_size,
            "pi1_H1": pi1_size,
            "pi2_H0": pi2_size,
        },
        "nontrivial_2_automorphisms_of_identity": len(ker_d0),
        "d1_d0_zero_for_all_vertex_gauges": True,
        "one_morphism_identity_inverse_composition": "PASS",
        "one_morphism_associativity_unit": "PASS",
        "two_morphism_identity_inverse_vertical_composition": "PASS",
        "horizontal_composition_checks": horizontal_checks,
        "interchange_law_checks": interchange_checks,
        "gauge_orbit_sizes": {str(h): len(sectors[h]) for h in (0, 1)},
        "proper_face_subset_marginals_checked": marginal_checks,
        "proper_face_marginals_identical": True,
        "surface_holonomy_by_sector": {str(h): next(iter(holonomy[h]))
                                       for h in (0, 1)},
        "all_exact_assertions_passed": True,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
