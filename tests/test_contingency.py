from dataclasses import replace

import numpy as np
import pytest

from enerqit.contingency import audit_outages, solve_preventive_dispatch
from enerqit.network import Line, solve_dispatch
from enerqit.network_study import network_case


def test_triangle_independent_cut_reference():
    # Removing direct 0-2 line forces all transfer through 40 MW line 0-1.
    r = solve_preventive_dispatch(network_case())
    assert r["cost_eur"] == pytest.approx(11000)
    assert r["audit"]["secure_for_selected_outages"]
    assert r["audit"]["states"][0]["renewable_mw"][0] == pytest.approx(40)
    # Independent exhaustive scalar reference, not LP matrices.
    feasible = [v for v in range(151) if v / 3 <= 40 and 2 * v / 3 <= 100 and v <= 40 and v <= 100]
    assert r["cost_eur"] == (150 - max(feasible)) * 100


def test_base_dispatch_fails_outage_audit():
    p = network_case()
    base = solve_dispatch(p)["physical"]
    r = audit_outages(p, base["renewable_mw"], base["firm_mw"])
    assert not r["secure_for_selected_outages"]
    assert r["worst_overload_mw"] == pytest.approx(80)


@pytest.mark.parametrize("ids,transfer", [([], 120), ([0], 100), ([1], 40), ([2], 100)])
def test_outage_selection_ablation(ids, transfer):
    r = solve_preventive_dispatch(network_case(), ids)
    assert r["cost_eur"] == pytest.approx((150 - transfer) * 100)
    assert r["outages"] == ids


@pytest.mark.parametrize("ids", [[True], [3], [-1], [0, 0]])
def test_invalid_outages(ids):
    with pytest.raises(ValueError):
        solve_preventive_dispatch(network_case(), ids)


def test_islanding_rejected_and_shortage_infeasible():
    p = network_case()
    radial = replace(p, lines=(p.lines[0], p.lines[2]))
    with pytest.raises(ValueError, match="island"):
        solve_preventive_dispatch(radial)
    short = replace(p, firm_capacity_mw=(0, 0, 50))
    assert solve_preventive_dispatch(short)["status"] == "infeasible"


def test_parallel_lines_and_orientation():
    from enerqit.network import DispatchCase

    p = DispatchCase(
        (0, 100), (100, 0), (0, 100), (100, 100), (Line(0, 1, 1000, 60), Line(1, 0, 1000, 60))
    )
    r = solve_preventive_dispatch(p)
    assert r["cost_eur"] == pytest.approx(4000)
    for state in r["audit"]["states"][1:]:
        assert abs(state["line_flows_mw"][0]) == pytest.approx(60)


@pytest.mark.parametrize("hours", [0.25, 2])
def test_duration_and_reversed_orientation(hours):
    p = network_case()
    p = replace(
        p,
        hours=hours,
        lines=tuple(replace(line, source=line.target, target=line.source) for line in p.lines),
    )
    r = solve_preventive_dispatch(p)
    assert r["cost_eur"] == pytest.approx(11000 * hours)
    np.testing.assert_allclose(r["audit"]["states"][0]["renewable_mw"], [40, 0, 0])


def test_agent_run():
    pytest.importorskip("energy_agents.quantum_ml.studies")
    from enerqit.contingency_study import run_contingency_engineer

    r = run_contingency_engineer()
    assert r["success"] and r["role"]["id"] == "career_quantum_ml_engineer"
    assert [v["tool"] for v in r["trace"]] == [
        "inspect_evidence",
        "benchmark_methods",
        "assess_sensitivity",
        "prepare_handoff",
        "finish",
    ]
    assert r["reports"]["prepare_handoff"]["modeled_security_premium_eur"] == pytest.approx(8000)
