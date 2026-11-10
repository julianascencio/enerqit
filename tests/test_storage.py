"""Physical conservation, independent optima and exhaustive QUBO semantics."""

from dataclasses import replace
from itertools import product

import numpy as np
import pytest

from enerqit.solvers import exact
from enerqit.storage import (
    BatteryOffer,
    deliverable_capacity,
    enumerate_cover,
    evaluate_portfolio,
    portfolio_qubo,
    solve_cover_milp,
)
from enerqit.storage_study import (
    battery_portfolio_case,
    benchmark_portfolio,
    portfolio_sensitivity,
)


def offer(**kwargs):
    return replace(BatteryOffer("test", 100, 200, .8, .1, .9, .95, 10, 80, 1000), **kwargs)


def test_energy_accounting_export_headroom_and_duration():
    # 180 DC MWh effective; (0.8-0.1)*180 - 10 = 116 DC MWh; 110.2 AC MWh.
    assert deliverable_capacity([offer()], 2)[0]["deliverable_mw"] == pytest.approx(55.1)
    assert deliverable_capacity([offer()], 1)[0]["deliverable_mw"] == 80
    physical = evaluate_portfolio([offer()], np.array([1], dtype=np.int8), 50, 2)
    assert physical["feasible"] and physical["reservation_cost_gbp"] == 1000
    assert physical["scheduled_ac_mwh"] == [100]
    assert physical["ending_soc"][0] == pytest.approx(.8 - 100/.95/180)
    assert physical["ending_soc"][0] >= .1 + 10/180


def test_unavailable_exhausted_and_zero_target():
    for battery in (offer(available=False), offer(start_soc=.1), offer(reserved_dc_mwh=200)):
        result = evaluate_portfolio([battery], [1], 50, 3)
        assert not result["feasible"] and result["shortfall_mw"] == 50
        assert result["block_shortfall_equivalent_mwh"] == 150
        assert result["ending_soc"] == [battery.start_soc]
    assert evaluate_portfolio([offer()], [0], 0, 3)["feasible"]
    assert solve_cover_milp([10], [5], 0)["cost_gbp"] == 0


def test_duration_and_soc_buffer_monotonicity():
    batteries = [BatteryOffer(**r) for r in battery_portfolio_case()["offers"]]
    previous = np.full(len(batteries), np.inf)
    for duration in [1, 2, 3, 6, 12]:
        power = np.array([r["deliverable_mw"] for r in deliverable_capacity(batteries, duration)])
        assert np.all(power <= previous)
        previous = power
    base = deliverable_capacity(batteries, 3)
    buffered = deliverable_capacity(batteries, 3, soc_haircut=.1)
    assert all(a["deliverable_mw"] >= b["deliverable_mw"] for a, b in zip(base, buffered))


@pytest.mark.parametrize("kwargs", [{"start_soc": float("nan")}, {"energy_mwh": 0},
                                  {"minimum_soc": .9}, {"discharge_efficiency": 0},
                                  {"state_of_health": 1.1}, {"available": 1},
                                  {"reservation_cost_gbp": -1}, {"id": ""}])
def test_reject_invalid_offers(kwargs):
    with pytest.raises(ValueError):
        offer(**kwargs)


def test_reject_invalid_portfolios():
    for duration in [0, float("inf"), -1, True]:
        with pytest.raises(ValueError):
            deliverable_capacity([offer()], duration)
    with pytest.raises(ValueError):
        deliverable_capacity([offer(), offer()], 1)
    with pytest.raises(ValueError):
        evaluate_portfolio([offer()], [.5], 50, 1)
    with pytest.raises(ValueError):
        evaluate_portfolio([offer()], [1], float("nan"), 1)
    for solver in (solve_cover_milp, enumerate_cover, portfolio_qubo):
        for capacities, costs in [([], []), ([1], [1, 2]), ([-1], [2]), ([1], [float("inf")])]:
            with pytest.raises(ValueError):
                solver(capacities, costs, 1)


def test_explicit_infeasibility_and_conservative_rounding():
    assert solve_cover_milp([1, 2], [1, 1], 4)["status"] == "infeasible"
    assert enumerate_cover([1, 2], [1, 1], 4)["selected"] is None
    # Physical cover exists (5.9 + 5.9 >= 11) but 5-MW encoding excludes it.
    assert solve_cover_milp([5.9, 5.9], [1, 1], 11)["status"] == "optimal"
    with pytest.raises(ValueError, match="infeasible"):
        portfolio_qubo([5.9, 5.9], [1, 1], 11, step_mw=5)
    with pytest.raises(ValueError):
        portfolio_qubo([1e100], [1], 1)


def test_every_encoded_state_matches_original_equation_and_feasibility():
    capacities, costs, target = [5.9, 10.1, 15.2], [3.0, 4.0, 5.0], 14
    q = portfolio_qubo(capacities, costs, target, step_mw=5)
    m = q.metadata
    for candidate in product((0, 1), repeat=q.size):
        x = np.array(candidate)
        residual = np.dot(m["capacity_units"], x[:3]) - np.dot(m["slack_weights"], x[3:]) - m["target_units"]
        expected = np.dot(costs, x[:3]) + m["penalty_gbp"] * residual**2
        assert q.energy(x) == pytest.approx(expected, abs=1e-9)
        assert q.feasible(x) == (residual == 0)
        if q.feasible(x):
            assert np.dot(capacities, x[:3]) >= target
    result = exact(q)
    assert result.feasible and result.energy == 5  # Third offer alone.


def test_randomized_milp_native_and_encoded_oracles_agree():
    rng = np.random.default_rng(42)
    for _ in range(12):
        capacity = rng.integers(1, 12, size=5)
        costs = rng.integers(0, 20, size=5)
        target = int(rng.integers(1, capacity.sum()+1))
        native = enumerate_cover(capacity, costs, target)
        milp = solve_cover_milp(capacity, costs, target)
        result = exact(portfolio_qubo(capacity, costs, target, step_mw=1))
        assert result.feasible
        assert result.energy == pytest.approx(native["cost_gbp"])
        assert milp["cost_gbp"] == native["cost_gbp"]
        assert np.dot(capacity, result.x[:5]) >= target


def test_case_scientific_findings_and_reported_solver_failures():
    case = battery_portfolio_case()
    result = benchmark_portfolio(case)
    assert result["native_milp"]["cost_gbp"] == result["native_enumeration"]["cost_gbp"] == 25000
    baseline = result["power_only_baseline"]["physical"]
    assert baseline["shortfall_mw"] == pytest.approx(157.87291666666667)
    assert not baseline["feasible"]
    assert result["qubo"]["variables"] == 14
    # Check accounting, not a claim that a heuristic must find a particular optimum.
    for row in result["records"]:
        assert row["total_s"] >= row["elapsed_s"] >= 0
        if row["physical_feasible"]:
            assert row["native_cost_gap_gbp"] >= -1e-8
        else:
            assert row["native_cost_gap_gbp"] is None
    assert not result["quantum_advantage_established"]
    events = case["evidence"]["events"]
    assert [e["indicated_margin_shortfall_mw"] for e in events] == [1388, 500, 200, None]
    sensitivity = portfolio_sensitivity(case)
    assert sensitivity["duration"][-1]["status"] == "infeasible"
    assert sensitivity["discretization"][-1]["cost_gbp"] == 26000


def test_actual_energy_agents_integration():
    pytest.importorskip("energy_agents.quantum_ml.studies")
    from enerqit.storage_study import run_battery_engineer

    run = run_battery_engineer()
    assert run["success"] and run["role"]["id"] == "career_quantum_ml_engineer"
    assert run["mode"] == "scripted_tool_workflow"
    assert [r["tool"] for r in run["trace"]] == ["inspect_evidence", "benchmark_methods",
            "assess_sensitivity", "prepare_handoff", "finish"]
    assert run["reports"]["prepare_handoff"]["portfolio"]["feasible"]
    assert not run["execution_authorized"]
