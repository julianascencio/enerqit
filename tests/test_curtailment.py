import numpy as np
import pytest
from scipy.optimize import linprog

from enerqit.curtailment import recover_curtailment


def test_independent_energy_accounting():
    r = recover_curtailment([50, 50, 0, 0], [30] * 4, [1] * 4, power_mw=20, energy_dc_mwh=40)
    assert r["captured_ac_mwh"] == pytest.approx(40)
    assert r["recovered_export_mwh"] == pytest.approx(32.4)
    assert r["conversion_loss_mwh"] == pytest.approx(7.6)
    assert r["terminal_dc_mwh"] == pytest.approx(0)
    assert r["baseline_export_mwh"] == 60


def test_no_headroom_not_revenue():
    r = recover_curtailment([50, 50, 0, 0], [30, 30, 0, 0], [1] * 4, power_mw=20, energy_dc_mwh=40)
    assert r["captured_ac_mwh"] == 40
    assert r["recovered_export_mwh"] == 0
    assert r["terminal_dc_mwh"] == 36


@pytest.mark.parametrize("seed", range(5))
def test_independent_horizon_lp(seed):
    rng = np.random.default_rng(seed)
    n = 12
    g = rng.uniform(0, 60, n)
    limit = rng.uniform(10, 50, n)
    h = rng.uniform(0.1, 2, n)
    r = recover_curtailment(g, limit, h, power_mw=20, energy_dc_mwh=30)
    # Independent continuous inventory LP: c, d and end-state variables.
    a = np.zeros((n, 3 * n))
    b = np.zeros(n)
    for t in range(n):
        a[t, t] = -0.9 * h[t]
        a[t, n + t] = h[t] / 0.9
        a[t, 2 * n + t] = 1
        if t:
            a[t, 2 * n + t - 1] = -1
    bounds = (
        [(0, min(20, max(x - y, 0))) for x, y in zip(g, limit)]
        + [(0, min(20, max(y - x, 0))) for x, y in zip(g, limit)]
        + [(0, 30)] * n
    )
    ref = linprog(
        np.r_[np.zeros(n), -h, np.zeros(n)], A_eq=a, b_eq=b, bounds=bounds, method="highs"
    )
    assert ref.success
    assert r["recovered_export_mwh"] == pytest.approx(-ref.fun)
    assert max(np.array(r["export_mw"]) - limit) < 1e-8
    assert np.all(np.array(r["charge_ac_mw"]) * r["discharge_ac_mw"] == 0)


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf")])
def test_bad_inputs(value):
    with pytest.raises(ValueError):
        recover_curtailment([value], [1], [1], power_mw=1, energy_dc_mwh=1)


def test_zero_capacity_and_efficiency():
    assert (
        recover_curtailment([2, 0], [1, 1], [1, 1], power_mw=1, energy_dc_mwh=0)[
            "recovered_export_mwh"
        ]
        == 0
    )
    with pytest.raises(ValueError):
        recover_curtailment([2], [1], [1], power_mw=1, energy_dc_mwh=1, charge_efficiency=0)


def test_agent():
    pytest.importorskip("energy_agents.quantum_ml.studies")
    from enerqit.curtailment_study import run_curtailment_study

    r = run_curtailment_study()
    assert r["success"]
    assert len(r["trace"]) == 5
    assert r["reports"]["benchmark_methods"]["illustrative_export_value_eur"][
        "40"
    ] == pytest.approx(1620)


@pytest.mark.parametrize(
    "generation,limit,hours",
    [([], [], []), ([1], [1, 2], [1]), ([1], [1], [0]), ([1], [1], [float("nan")])],
)
def test_invalid_interval_contract(generation, limit, hours):
    with pytest.raises(ValueError):
        recover_curtailment(generation, limit, hours, power_mw=1, energy_dc_mwh=1)
