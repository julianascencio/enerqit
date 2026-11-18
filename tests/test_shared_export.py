from itertools import product

import numpy as np
import pytest

from enerqit.shared_export import compare_independent_export, coordinate_export


def test_business_case():
    r = compare_independent_export(
        [50, 50], [50, 100], [10, 100, 90, 20, 60, 30], [1] * 6, [50] * 6
    )
    assert r["independent_requested"]["gross_value_eur"] == pytest.approx(14500)
    assert max(r["independent_overload_mw"]) == pytest.approx(50)
    assert r["clipped_gross_value_eur"] == pytest.approx(9500)
    assert r["coordinated"]["gross_value_eur"] == pytest.approx(12500)
    assert r["coordination_value_eur"] == pytest.approx(3000)


@pytest.mark.parametrize("prices", [[1, 3, 2], [-1, 0, 2], [0, 0, 0]])
def test_independent_integer_reference(prices):
    # Integer capacities yield an integral flow-polytope optimum for unit durations.
    best = 0
    for bits in product((0, 1), repeat=6):
        x = np.array(bits).reshape(2, 3)
        if np.all(x.sum(axis=1) <= [1, 2]) and np.all(x.sum(axis=0) <= 1):
            best = max(best, float(x.sum(axis=0) @ prices))
    r = coordinate_export([1, 1], [1, 2], prices, [1] * 3, [1] * 3)
    assert r["gross_value_eur"] == pytest.approx(best)


def test_duration_and_energy_units():
    r = coordinate_export([2], [1], [100, 50], [0.25, 1], [2, 2])
    assert r["gross_value_eur"] == pytest.approx(75)
    assert r["used_ac_mwh"] == pytest.approx([1])
    assert coordinate_export([2], [0], [10], [1], [2])["gross_value_eur"] == 0
    assert coordinate_export([2], [2], [-10], [1], [2])["gross_value_eur"] == 0


@pytest.mark.parametrize(
    "field,value",
    [
        ("hours", [0]),
        ("prices_eur_mwh", [float("nan")]),
        ("energy_ac_mwh", [-1]),
        ("connection_mw", [-1]),
        ("power_mw", []),
    ],
)
def test_validation(field, value):
    a = dict(power_mw=[1], energy_ac_mwh=[1], prices_eur_mwh=[1], hours=[1], connection_mw=[1])
    a[field] = value
    with pytest.raises(ValueError):
        coordinate_export(**a)


def test_agent_trace():
    pytest.importorskip("energy_agents.quantum_ml.studies")
    from enerqit.shared_export_study import run_shared_export_study

    r = run_shared_export_study()
    assert r["success"]
    assert [x["tool"] for x in r["trace"]] == [
        "inspect_evidence",
        "benchmark_methods",
        "assess_sensitivity",
        "prepare_handoff",
        "finish",
    ]
