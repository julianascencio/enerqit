import numpy as np
import pytest
from scipy.integrate import quad

from enerqit.ramp_energy import audit_linear_ramps


def audit(p, d, h, **kw):
    return audit_linear_ramps(p, d, h, capacity_mw=100, ramp_mw_per_hour=100, **kw)


def test_triangle_and_crossing():
    r = audit([0, 40], [40, 40], [1])
    assert r["total_shortage_mwh"] == 20
    assert r["total_generation_mwh"] == 20
    r = audit([0, 40], [20, 20], [1])
    assert r["total_shortage_mwh"] == 5
    assert r["total_spill_mwh"] == 5


@pytest.mark.parametrize("seed", range(6))
def test_independent_quadrature(seed):
    rng = np.random.default_rng(seed)
    p, d = rng.uniform(0, 100, (2, 11))
    h = rng.uniform(0.1, 3, 10)
    r = audit(p, d, h)
    for i in range(10):

        def f(t):
            return max(0, d[i] + (d[i + 1] - d[i]) * t - p[i] - (p[i + 1] - p[i]) * t)

        expected = quad(f, 0, 1, epsabs=1e-9, epsrel=1e-10, points=np.linspace(0, 1, 101), limit=300)[0] * h[i]
        assert r["shortage_mwh"][i] == pytest.approx(expected, abs=1e-5)
    assert sum(r["generation_mwh"]) + sum(r["shortage_mwh"]) == pytest.approx(
        sum(r["demand_mwh"]) + sum(r["spill_mwh"])
    )


def test_subdivision_and_reversal():
    coarse = audit([0, 40], [20, 20], [2])
    fine = audit([0, 20, 40], [20] * 3, [1, 1])
    reverse = audit([40, 0], [20, 20], [2])
    for key in ("objective_eur", "total_shortage_mwh", "total_spill_mwh"):
        assert coarse[key] == pytest.approx(fine[key])
        assert coarse[key] == pytest.approx(reverse[key])


def test_limits():
    r = audit_linear_ramps([0, 40], [40, 40], [1], capacity_mw=30, ramp_mw_per_hour=20)
    assert not r["feasible"]
    assert r["capacity_violation_mw"] == 10
    assert r["ramp_violation_mw_per_hour"] == 20


@pytest.mark.parametrize(
    "p,d,h",
    [
        ([0], [0], []),
        ([0, 1], [0], [1]),
        ([0, 1], [0, 1], [0]),
        ([0, np.nan], [0, 1], [1]),
        ([-1, 1], [0, 1], [1]),
    ],
)
def test_bad_input(p, d, h):
    with pytest.raises(ValueError):
        audit(p, d, h)


def test_agent_execution():
    pytest.importorskip('energy_agents.quantum_ml')
    from enerqit.ramp_energy_study import run_ramp_energy_study
    r = run_ramp_energy_study()
    assert r['success'] and r['human_review_required'] and not r['execution_authorized']
    assert len(r['trace']) == 5
    assert r['reports']['benchmark_methods']['continuous']['total_shortage_mwh'] == 20
    assert not r['reports']['assess_sensitivity']['duration']['0.5']['feasible']
