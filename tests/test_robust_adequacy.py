import numpy as np
import pytest

from enerqit.robust_adequacy import robust_capacity_offers, worst_case_eens


@pytest.mark.parametrize("radius", [0, 0.01, 0.2, 0.8, 1])
def test_two_state_analytic(radius):
    s = [{"available_mw": 0, "probability": 0.2}, {"available_mw": 100, "probability": 0.8}]
    r = worst_case_eens(s, 100, hours=4, radius=radius)
    assert r["worst_eens_mwh"] == pytest.approx(400 * min(0.2 + radius, 1))
    assert r["total_variation"] <= radius + 1e-8


def test_three_state_independent_grid_reference():
    s = [{"available_mw": c, "probability": p} for c, p in [(0, 0.1), (60, 0.2), (120, 0.7)]]
    r = worst_case_eens(s, 100, hours=4, radius=0.1)
    # Exhaustive simplex lattice includes an optimal vertex for this rational case.
    values = []
    for i in range(101):
        for j in range(101 - i):
            q = np.array([i, j, 100 - i - j]) / 100
            if np.abs(q - [0.1, 0.2, 0.7]).sum() <= 0.2 + 1e-10:
                values.append(q @ [400, 160, 0])
    assert r["worst_eens_mwh"] == pytest.approx(max(values))


def test_offers_and_zero_mass_support():
    s = [
        {"available_mw": 0, "probability": 0.109},
        {"available_mw": 60, "probability": 0.162},
        {"available_mw": 120, "probability": 0.729},
    ]
    offers = [(v, v * 100) for v in range(0, 101, 20)]
    assert robust_capacity_offers(s, 100, 4, offers, 20, 0)["selected"]["firm_mw"] == 60
    assert robust_capacity_offers(s, 100, 4, offers, 20, 0.05)["selected"]["firm_mw"] == 80
    assert robust_capacity_offers(s, 100, 4, [(0, 0)], 0, 0.05)["status"] == "infeasible"
    s = [{"available_mw": 0, "probability": 0}, {"available_mw": 100, "probability": 1}]
    assert worst_case_eens(s, 100, radius=0.1)["worst_eens_mwh"] == pytest.approx(10)
    assert worst_case_eens(s, 0, radius=1)["worst_eens_mwh"] == 0


@pytest.mark.parametrize("radius", [-0.1, 1.1, float("nan"), True])
def test_invalid_radius(radius):
    with pytest.raises(ValueError):
        worst_case_eens([{"available_mw": 1, "probability": 1}], 1, radius=radius)


def test_invalid_mass():
    with pytest.raises(ValueError):
        worst_case_eens([{"available_mw": 1, "probability": 0.9}], 1)


def test_agent():
    pytest.importorskip("energy_agents.quantum_ml.studies")
    from enerqit.robust_adequacy_study import run_robust_adequacy

    r = run_robust_adequacy()
    assert r["success"]
    assert [s["tool"] for s in r["trace"]] == [
        "inspect_evidence",
        "benchmark_methods",
        "assess_sensitivity",
        "prepare_handoff",
        "finish",
    ]
