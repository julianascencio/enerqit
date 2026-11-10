"""Analytic/physical references independent of LP constraint assembly."""

from dataclasses import replace

import numpy as np
import pytest

from enerqit.network import DispatchCase, Line, evaluate_dispatch, solve_dispatch
from enerqit.network_study import network_case


@pytest.mark.parametrize(
    "model,cost,overload", [("dc", 3000, 0), ("transport", 1000, 20 / 3), ("copperplate", 0, 10)]
)
def test_equal_reactance_triangle_analytic_reference(model, cost, overload):
    # Kirchhoff: indirect path carries R/3, direct path 2R/3.
    # Therefore passive-grid renewable maximum is 3*40=120 MW.
    row = solve_dispatch(network_case(), model=model)["physical"]
    assert row["firm_energy_cost_eur"] == pytest.approx(cost)
    assert row["max_overload_mw"] == pytest.approx(overload)
    f = row["line_flows_mw"]
    assert f[0] + f[2] - f[1] == pytest.approx(0, abs=1e-9)
    assert row["dc_feasible"] == (model == "dc")


def test_independent_upgrade_reference():
    p = network_case()
    for i, expected in enumerate([0, 3000, 3000]):
        lines = list(p.lines)
        lines[i] = replace(lines[i], limit_mw=lines[i].limit_mw + 10)
        assert solve_dispatch(replace(p, lines=tuple(lines)))["physical"][
            "firm_energy_cost_eur"
        ] == pytest.approx(expected)


def test_radial_transport_equals_dc_and_orientation_invariance():
    p = replace(network_case(), lines=(Line(0, 1, 1000, 40), Line(1, 2, 500, 100)))
    for model in ("dc", "transport"):
        result = solve_dispatch(p, model=model)["physical"]
        assert result["dc_feasible"]
        assert result["firm_energy_cost_eur"] == pytest.approx(11000)
    rev = replace(p, lines=tuple(replace(x, source=x.target, target=x.source) for x in p.lines))
    np.testing.assert_allclose(solve_dispatch(rev)["physical"]["line_flows_mw"], [-40, -40])


@pytest.mark.parametrize("hours", [0.25, 1, 4])
def test_duration_scales_energy_not_dispatch(hours):
    result = solve_dispatch(replace(network_case(), hours=hours))["physical"]
    assert result["curtailed_mwh"] == pytest.approx(30 * hours)
    assert result["firm_energy_cost_eur"] == pytest.approx(3000 * hours)
    np.testing.assert_allclose(result["line_flows_mw"], [40, 80, 40])


def test_shortage_is_infeasible_not_hidden_shedding():
    p = replace(network_case(), firm_capacity_mw=(0, 0, 0))
    assert solve_dispatch(p)["status"] == "infeasible"
    assert solve_dispatch(p)["physical"] is None


def test_balance_and_bounds_are_checked():
    p = network_case()
    with pytest.raises(ValueError, match="balance"):
        evaluate_dispatch(p, [0, 0, 0], [0, 0, 0])
    assert not evaluate_dispatch(p, [160, 0, 0], [0, 0, -10])["generation_bounds_met"]
    with pytest.raises(ValueError):
        evaluate_dispatch(p, [float("nan"), 0, 0], [0, 0, 150])


@pytest.mark.parametrize(
    "changes",
    [
        {"hours": 0},
        {"hours": float("inf")},
        {"hours": True},
        {"demand_mw": (-1, 0, 150)},
        {"renewable_mw": (float("nan"), 0, 0)},
        {"firm_capacity_mw": (0, 0)},
        {"lines": (Line(0, 1, 1, 10),)},
        {"lines": (Line(0, 3, 1, 10),)},
        {"lines": (Line(0, 1, 0, 10), Line(1, 2, 1, 10))},
        {"lines": (Line(0, 1, 1, -1), Line(1, 2, 1, 10))},
    ],
)
def test_invalid_inputs(changes):
    with pytest.raises(ValueError):
        replace(network_case(), **changes)


@pytest.mark.parametrize("scale", [0.1, 1, 10])
def test_physical_scaling_reference(scale):
    p = network_case()
    p = DispatchCase(
        tuple(v * scale for v in p.demand_mw),
        tuple(v * scale for v in p.renewable_mw),
        tuple(v * scale for v in p.firm_capacity_mw),
        p.firm_cost_eur_mwh,
        tuple(
            replace(
                x, susceptance_mw_rad=x.susceptance_mw_rad * scale, limit_mw=x.limit_mw * scale
            )
            for x in p.lines
        ),
    )
    r = solve_dispatch(p)["physical"]
    assert r["firm_energy_cost_eur"] == pytest.approx(3000 * scale)
    np.testing.assert_allclose(r["angles_rad"], [0, -0.04, -0.08], atol=1e-9)


def test_actual_agent_trace():
    pytest.importorskip("energy_agents.quantum_ml.studies")
    from enerqit.network_study import run_network_engineer

    run = run_network_engineer()
    assert run["success"] and run["role"]["id"] == "career_quantum_ml_engineer"
    assert [t["tool"] for t in run["trace"]] == [
        "inspect_evidence",
        "benchmark_methods",
        "assess_sensitivity",
        "prepare_handoff",
        "finish",
    ]
    assert not run["reports"]["prepare_handoff"]["quantum_method_used"]
    assert run["reports"]["benchmark_methods"]["dc"]["physical"]["dc_feasible"]
