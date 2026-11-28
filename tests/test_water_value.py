import itertools
import json
from importlib.resources import files

import numpy as np
import pytest

from enerqit.hydro import TerminalWaterValue, dispatch_reservoir


def fixture():
    return json.loads(files("enerqit").joinpath("data/water_value_20261123.json").read_text())


def test_depletion_and_default_regression():
    d = fixture()
    a = d["inputs"]
    c = TerminalWaterValue(**d["terminal_curve"])
    zero = dispatch_reservoir(**a)
    assert zero["gross_value_eur"] == pytest.approx(1373.4)
    assert zero["reservoir_m3"][-1] == pytest.approx(0)
    assert zero["objective_value_eur"] == zero["gross_value_eur"]
    flat = dispatch_reservoir(**a, terminal_value=TerminalWaterValue((0, 100000), (0, 0)))
    assert flat["gross_value_eur"] == pytest.approx(zero["gross_value_eur"])
    r = dispatch_reservoir(**a, terminal_value=c)
    assert r["reservoir_m3"][-1] == pytest.approx(40000)
    assert r["turbine_m3"] == pytest.approx([10000, 40000, 10000])
    assert r["gross_value_eur"] == pytest.approx(1103.625)
    assert r["terminal_value_eur"] == pytest.approx(1200)
    assert r["objective_value_eur"] == pytest.approx(2303.625)


@pytest.mark.parametrize("seed", range(6))
def test_independent_enumeration(seed):
    rng = np.random.default_rng(seed)
    prices = rng.integers(-10, 100, 2)
    inflow = rng.integers(0, 2, 2)
    curve = TerminalWaterValue((0, 2, 5), (0, 0.04, 0.046))
    best = -np.inf
    for q in itertools.product(range(3), repeat=2):
        for b in itertools.product(range(6), repeat=2):
            s = 3
            valid = True
            for t in range(2):
                s += inflow[t] - q[t] - b[t]
                valid &= 0 <= s <= 5 and q[t] + b[t] >= 1
            if valid:
                # Explicit independent two-segment value, not the production evaluator.
                v = 0.02 * min(s, 2) + 0.002 * max(s - 2, 0)
                best = max(best, np.dot(q, prices) * 0.00024525 + v)
    r = dispatch_reservoir(
        inflow / 3600,
        prices,
        [1, 1],
        [1 / 3600] * 2,
        initial_m3=3,
        capacity_m3=5,
        terminal_min_m3=0,
        turbine_m3_s=2 / 3600,
        head_m=100,
        terminal_value=curve,
    )
    assert r["objective_value_eur"] == pytest.approx(best, abs=1e-8)


@pytest.mark.parametrize(
    "x,y",
    [
        ([1, 2], [0, 1]),
        ([0, 0], [0, 1]),
        ([0, 1], [1, 2]),
        ([0, 1, 2], [0, 1, 3]),
        ([0, 1, 2], [0, 1e-13, 3e-13]),
        ([0, 1], [0, -1]),
        ([0, 1], [0, np.nan]),
        ([0], [0]),
    ],
)
def test_curve_validation(x, y):
    with pytest.raises(ValueError):
        TerminalWaterValue(x, y)


def test_domain_and_equal_slopes():
    c = TerminalWaterValue([0, 2, 4], [0, 4, 8])
    assert c.evaluate(3) == 6
    for v in (-1, 5, np.nan, True):
        with pytest.raises(ValueError):
            c.evaluate(v)
    with pytest.raises(ValueError):
        dispatch_reservoir(**fixture()["inputs"], terminal_value=c)
    with pytest.raises(ValueError):
        dispatch_reservoir(**fixture()["inputs"], terminal_value=1)


def test_agent_and_common_scoring():
    pytest.importorskip("energy_agents.quantum_ml")
    from enerqit.water_value_study import run_water_value_study

    r = run_water_value_study()
    assert r["success"] and r["human_review_required"] and not r["execution_authorized"]
    assert len(r["trace"]) == 5
    b = r["reports"]["benchmark_methods"]
    assert b["water_value"]["common_score_eur"] > b["cash_only"]["common_score_eur"]
    assert b["water_value"]["common_score_eur"] > b["fixed_floor"]["common_score_eur"]
