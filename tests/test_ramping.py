import itertools

import numpy as np
import pytest

from enerqit.ramping import plan_ramping


def test_preposition():
    r = plan_ramping(
        [0, 40, 40], [1] * 3, [1] * 3, capacity_mw=40, initial_mw=0, ramp_mw_per_hour=20
    )
    assert r["optimized"]["objective_eur"] == pytest.approx(5000)
    assert r["optimized"]["spill_mwh"] == pytest.approx(20)
    assert r["causal"]["objective_eur"] == 23000
    assert r["causal"]["unserved_mwh"] == 20
    assert r["capacity_only"]["unserved_mwh"] == 0


@pytest.mark.parametrize("seed", range(5))
def test_independent_integer_lattice(seed):
    d = np.random.default_rng(seed).integers(0, 5, 4)
    r = plan_ramping(d, [1] * 4, [1] * 4, capacity_mw=4, initial_mw=0, ramp_mw_per_hour=1)
    costs = []
    for p in itertools.product(range(5), repeat=4):
        if max(abs(np.diff([0, *p]))) <= 1:
            costs.append(sum(50 * x + 1000 * max(y - x, 0) for x, y in zip(p, d)))
    # Integer bounds/RHS and network difference constraints admit integral optimum.
    assert r["optimized"]["objective_eur"] == pytest.approx(min(costs))


def test_time_and_down_ramp():
    r = plan_ramping(
        [0, 0], [0.5, 2], [0.5, 1], capacity_mw=40, initial_mw=40, ramp_mw_per_hour=20
    )
    assert r["optimized"]["dispatch_mw"] == pytest.approx([30, 10])
    assert r["optimized"]["spill_mwh"] == pytest.approx(35)


def test_zero_ramp_and_capacity():
    r = plan_ramping([20], [2], [1], capacity_mw=0, initial_mw=0, ramp_mw_per_hour=0)
    assert r["optimized"]["unserved_mwh"] == 40


@pytest.mark.parametrize(
    "kw",
    [
        {"initial_mw": 41},
        {"ramp_mw_per_hour": -1},
        {"generation_eur_mwh": float("nan")},
        {"hours": [0]},
        {"demand_mw": []},
        {"ramp_window_hours": [1, 2]},
    ],
)
def test_invalid(kw):
    a = dict(
        demand_mw=[20],
        hours=[1],
        ramp_window_hours=[1],
        capacity_mw=40,
        initial_mw=0,
        ramp_mw_per_hour=20,
    )
    a.update(kw)
    with pytest.raises(ValueError):
        plan_ramping(**a)


def test_agent_execution():
    pytest.importorskip("energy_agents")
    from enerqit.ramping_study import run_ramping_study

    r = run_ramping_study()
    assert r["success"] and len(r["trace"]) == 5
