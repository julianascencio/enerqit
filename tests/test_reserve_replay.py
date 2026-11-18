import numpy as np
import pytest
from scipy.optimize import linprog

from enerqit.reserve_replay import replay_reserve, screen_reserve_offers
from enerqit.storage import BatteryOffer


def offer(energy=100, **kwargs):
    d = dict(
        id="a",
        power_mw=50,
        energy_mwh=energy,
        start_soc=1,
        minimum_soc=0,
        state_of_health=1,
        discharge_efficiency=1,
        reserved_dc_mwh=0,
        export_limit_mw=50,
        reservation_cost_gbp=100,
    )
    d.update(kwargs)
    return BatteryOffer(**d)


def test_depletion_not_reset():
    r = replay_reserve(offer(), [50] * 4, [1] * 4)
    assert r["dispatch_mw"] == [50, 50, 0, 0]
    assert r["unserved_mwh"] == 100
    assert r["power_only_unserved_mwh"] == 0
    assert r["soc_after"] == [0.5, 0, 0, 0]


@pytest.mark.parametrize("seed", range(5))
def test_independent_dispatch_lp(seed):
    rng = np.random.default_rng(seed)
    d = rng.uniform(0, 100, 20)
    h = rng.uniform(0.1, 2, 20)
    o = offer(120, discharge_efficiency=0.9, start_soc=0.8, minimum_soc=0.1, reserved_dc_mwh=3)
    r = replay_reserve(o, d, h)
    energy = (120 * 0.7 - 3) * 0.9
    ref = linprog(
        -h,
        A_ub=h[None, :],
        b_ub=[energy],
        bounds=list(zip(np.zeros(20), np.minimum(d, 50))),
        method="highs",
    )
    assert ref.success
    assert r["delivered_mwh"] == pytest.approx(-ref.fun)
    assert min(r["soc_after"]) >= 0.1 + 3 / 120 - 1e-9
    assert r["delivered_mwh"] == pytest.approx(r["analytic_max_delivery_mwh"])


def test_export_unavailability_and_duration():
    assert replay_reserve(offer(export_limit_mw=10), [50], [2])["delivered_mwh"] == 20
    assert replay_reserve(offer(available=False), [50], [2])["delivered_mwh"] == 0
    assert replay_reserve(offer(), [0], [2])["unserved_mwh"] == 0


@pytest.mark.parametrize(
    "d,h", [([], []), ([1], [0]), ([-1], [1]), ([float("nan")], [1]), ([1, 2], [1])]
)
def test_bad_inputs(d, h):
    with pytest.raises(ValueError):
        replay_reserve(offer(), d, h)


def test_probability_and_infeasibility():
    with pytest.raises(ValueError):
        screen_reserve_offers([offer()], [[50]], [0.5], [1], 0)
    assert screen_reserve_offers([offer()], [[50] * 4], [1], [1] * 4, 0)["status"] == "infeasible"


def test_agent():
    pytest.importorskip("energy_agents.quantum_ml.studies")
    from enerqit.reserve_study import run_reserve_study

    r = run_reserve_study()
    assert r["success"]
    assert r["reports"]["benchmark_methods"]["selected"]["id"] == "long"
    assert [x["tool"] for x in r["trace"]] == [
        "inspect_evidence",
        "benchmark_methods",
        "assess_sensitivity",
        "prepare_handoff",
        "finish",
    ]
