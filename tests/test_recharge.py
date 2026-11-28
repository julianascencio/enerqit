from itertools import product

import numpy as np
import pytest

from enerqit.recharge import plan_recharge


def case(**kw):
    a = dict(
        discharge_mw=[1, 0, 0, 1],
        charge_limit_mw=[0, 1, 1, 0],
        hours=[1] * 4,
        price_eur_mwh=[50, 100, 20, 50],
        capacity_dc_mwh=1,
        initial_dc_mwh=1,
        discharge_limit_mw=1,
        charge_efficiency=1,
        discharge_efficiency=1,
    )
    return dict(a, **kw)


def test_cheapest_and_infeasible():
    r = plan_recharge(**case())
    assert r["charge_mw"] == pytest.approx([0, 0, 1, 0])
    assert r["cost_eur"] == 20
    assert plan_recharge(**case(charge_limit_mw=[0] * 4))["status"] == "infeasible"
    assert plan_recharge(**case(discharge_limit_mw=0.5))["status"] == "infeasible"


@pytest.mark.parametrize("seed", range(6))
def test_independent_integer_enumeration(seed):
    rng = np.random.default_rng(seed)
    prices = rng.integers(1, 100, 4)
    a = case(price_eur_mwh=prices, capacity_dc_mwh=2, terminal_dc_mwh=0)
    feasible = []
    for q in product(range(2), repeat=2):
        s = 1
        cost = 0
        for d, c, p in zip([1, 0, 0, 1], [0, *q, 0], prices):
            s += c - d
            cost += c * p
            if not 0 <= s <= 2:
                break
        else:
            if s >= 0:
                feasible.append(cost)
    assert plan_recharge(**a)["cost_eur"] == pytest.approx(min(feasible))


def test_losses_terminal_and_zero():
    r = plan_recharge(
        **case(
            capacity_dc_mwh=2, initial_dc_mwh=2, charge_efficiency=0.8, discharge_efficiency=0.5
        )
    )
    assert r["status"] == "infeasible"
    r = plan_recharge(
        **case(discharge_mw=[0] * 4, initial_dc_mwh=0, terminal_dc_mwh=0.8, charge_efficiency=0.8)
    )
    assert r["purchase_ac_mwh"] == pytest.approx(1)
    assert r["audit"]["conversion_loss_mwh"] == pytest.approx(0.2)
    assert plan_recharge(**case(discharge_mw=[0] * 4))["cost_eur"] == 0


@pytest.mark.parametrize(
    "kw",
    [
        {"hours": [0] * 4},
        {"price_eur_mwh": [-1] * 4},
        {"charge_limit_mw": [1] * 4},
        {"discharge_mw": [np.nan] * 4},
        {"initial_dc_mwh": 3},
        {"charge_efficiency": 0},
        {"hours": [1]},
    ],
)
def test_invalid(kw):
    with pytest.raises(ValueError):
        plan_recharge(**case(**kw))


def test_agent():
    pytest.importorskip("energy_agents.quantum_ml")
    from enerqit.recharge_study import run_recharge_study

    r = run_recharge_study()
    assert r["success"] and r["human_review_required"] and not r["execution_authorized"]
    assert len(r["trace"]) == 5
