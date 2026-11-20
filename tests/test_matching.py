import numpy as np
import pytest

from enerqit.matching import procure_matching

A = dict(
    profiles=[[1, 0], [0.5, 0.5]],
    demand_mw=[1, 1],
    hours=[1, 1],
    costs_eur_per_mw=[500, 1500],
    capacity_limits_mw=[4, 4],
)


def test_total_is_not_simultaneous():
    annual = procure_matching(**A, interval_matching=False)
    hourly = procure_matching(**A)
    assert annual["cost_eur"] == pytest.approx(1000)
    assert annual["matching_fraction"] == pytest.approx(0.5)
    assert hourly["cost_eur"] == pytest.approx(3000)
    assert hourly["capacity_mw"] == pytest.approx([0, 2])


@pytest.mark.parametrize(
    "fraction,cost", [(0, 0), (0.25, 250), (0.5, 500), (0.75, 1750), (1, 3000)]
)
def test_analytic_piecewise_bound(fraction, cost):
    # First load MWh can be covered by solar at EUR500/MWh. Beyond this,
    # wind must cover the dark interval and displaces solar in the bright one.
    assert procure_matching(**A, target_fraction=fraction)["cost_eur"] == pytest.approx(cost)


def test_infeasible_dark_hour_and_zero_load():
    assert not procure_matching([[1, 0]], [1, 1], [1, 1], [500], [100])["feasible"]
    assert procure_matching(**dict(A, demand_mw=[0, 0]))["cost_eur"] == 0


def test_duration_accounting():
    r = procure_matching([[1, 0.5]], [1, 1], [0.5, 2], [100], [3])
    assert r["capacity_mw"] == pytest.approx([2])
    assert r["matched_mwh"] == pytest.approx(2.5)
    assert r["excess_mwh"] == pytest.approx(0.5)


@pytest.mark.parametrize("seed", range(3))
def test_independent_dense_grid(seed):
    rng = np.random.default_rng(seed)
    cost = rng.uniform(1, 4, 2)
    r = procure_matching(**dict(A, costs_eur_per_mw=cost), target_fraction=0.75)
    grid = np.arange(0, 4.001, 0.25)
    best = float("inf")
    for x in grid:
        for y in grid:
            if min(x + 0.5 * y, 1) + min(0.5 * y, 1) >= 1.5:
                best = min(best, x * cost[0] + y * cost[1])
    assert r["cost_eur"] == pytest.approx(best)


@pytest.mark.parametrize(
    "kw",
    [
        {"profiles": [[2, 0], [0.5, 0.5]]},
        {"hours": [0, 1]},
        {"target_fraction": 1.1},
        {"costs_eur_per_mw": [float("nan"), 1]},
        {"capacity_limits_mw": [-1, 1]},
    ],
)
def test_invalid(kw):
    with pytest.raises(ValueError):
        procure_matching(**dict(A, **kw))


def test_agent():
    pytest.importorskip("energy_agents")
    from enerqit.matching_study import run_matching_study

    r = run_matching_study()
    assert r["success"] and len(r["trace"]) == 5
