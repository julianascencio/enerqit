from math import comb

import pytest

from enerqit.adequacy import CapacityUnit, capacity_states, screen_firm_capacity, window_risk


def fleet():
    return (CapacityUnit(60, 0.1),) * 2


def test_hand_calculated_correlated_states():
    # P(120)=.9*.9*.9=.729; P(60)=.162; P(0)=.1+.9*.1*.1=.109.
    s = capacity_states(fleet(), 0.1)
    r = window_risk(s, 100, hours=4)
    assert r["probability_mass"] == pytest.approx(1)
    assert r["eens_mwh"] == pytest.approx((0.162 * 40 + 0.109 * 100) * 4)
    assert r["lole_hours"] == pytest.approx((0.162 + 0.109) * 4)
    assert r["mean_available_mw"] == pytest.approx(97.2)


def test_same_marginals_different_tail_risk():
    r = window_risk(capacity_states((CapacityUnit(60, 0.19),) * 2), 100, hours=4)
    assert r["eens_mwh"] == pytest.approx(63.688)
    assert r["lole_hours"] == pytest.approx(1.3756)
    assert r["mean_available_mw"] == pytest.approx(97.2)


@pytest.mark.parametrize("n", [1, 3, 8, 12])
def test_binomial_reference(n):
    s = capacity_states((CapacityUnit(10, 0.2),) * n)
    demand = n * 8
    reference = sum(
        comb(n, k) * 0.8**k * 0.2 ** (n - k) * max(demand - 10 * k, 0) for k in range(n + 1)
    )
    assert window_risk(s, demand)["eens_mwh"] == pytest.approx(reference)


def test_firm_screen_reference_and_infeasible_target():
    offers = [(v, v * 100) for v in range(0, 101, 20)]
    s = capacity_states(fleet(), 0.1)
    r = screen_firm_capacity(s, 100, 4, offers, 20)
    assert r["selected"]["firm_mw"] == 60
    assert r["selected"]["fee_eur"] == 6000
    assert r["selected"]["eens_mwh"] == pytest.approx(17.44)
    assert window_risk(s, 100, hours=4, firm_mw=40)["eens_mwh"] == pytest.approx(26.16)
    assert screen_firm_capacity(s, 100, 4, [(0, 0)], 0)["status"] == "infeasible"


@pytest.mark.parametrize("q", [0, 1])
def test_extreme_probabilities(q):
    r = window_risk(capacity_states((CapacityUnit(100, 0),), q), 100, hours=2)
    assert r["eens_mwh"] == 200 * q
    assert r["lole_hours"] == 2 * q


def test_no_demand_and_duration_units():
    s = capacity_states(fleet(), 0.1)
    assert window_risk(s, 0)["eens_mwh"] == 0
    assert window_risk(s, 100, hours=0.25)["eens_mwh"] == pytest.approx(
        window_risk(s, 100)["eens_mwh"] / 4
    )
    assert window_risk(s, 100, firm_mw=100)["lolp"] == 0


@pytest.mark.parametrize("p", [-0.1, 1.1, float("nan"), True])
def test_bad_probability(p):
    with pytest.raises(ValueError):
        CapacityUnit(1, p)
    with pytest.raises(ValueError):
        capacity_states(fleet(), p)


def test_bad_mass_and_size():
    with pytest.raises(ValueError):
        window_risk([{"available_mw": 1, "probability": 0.5}], 1)
    with pytest.raises(ValueError):
        capacity_states(())
    with pytest.raises(ValueError):
        capacity_states(fleet() * 9)
    with pytest.raises(ValueError):
        window_risk(capacity_states(fleet()), 100, hours=0)


def test_agent_and_independent_procurement():
    pytest.importorskip("energy_agents.quantum_ml.studies")
    from enerqit.adequacy_study import run_adequacy_engineer

    r = run_adequacy_engineer()
    assert r["success"] and r["role"]["id"] == "career_quantum_ml_engineer"
    assert [v["tool"] for v in r["trace"]] == [
        "inspect_evidence",
        "benchmark_methods",
        "assess_sensitivity",
        "prepare_handoff",
        "finish",
    ]
    b = r["reports"]["benchmark_methods"]
    assert b["independent_procurement"]["selected"]["firm_mw"] == 40
    assert b["correlated_procurement"]["selected"]["firm_mw"] == 60
