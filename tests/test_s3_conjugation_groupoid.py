from experiments.s3_conjugation_groupoid import main


def test_s3_conjugation_groupoid_orbits_and_isotropy():
    result = main()
    assert result["group_order"] == 6
    assert result["orbit_sizes"] == [1, 2, 3]
    assert result["conjugacy_class_count"] == 3
    assert result["total_groupoid_arrows"] == 36
    assert result["sum_centralizer_sizes"] == 18
    types = {row["cycle_type"]: row["centralizer_group_type"] for row in result["class_summary"]}
    assert types == {"identity": "S3", "3-cycle": "C3", "transposition": "C2"}
    assert all(result["checks"].values())
