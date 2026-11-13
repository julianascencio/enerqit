from dataclasses import replace

import numpy as np
import pytest

from enerqit.storage_sizing import FirmingCase, audit_firming, minimum_storage


def solar():
    return FirmingCase((0, 3, 3, 0), (1, 1, 1, 1), 2, 10)


@pytest.mark.parametrize(
    "profile,expected", [((0, 3, 3, 0), 2 / 0.9), ((0.75, 2.25, 2.25, 0.75), 0.5 / 0.9)]
)
def test_independent_cyclic_deficit_reference(profile, expected):
    # Two consecutive deficit intervals straddle the cycle boundary. Their
    # DC discharge requirement bounds capacity; daylight charge can replenish it.
    p = replace(solar(), renewable_mw=profile)
    r = minimum_storage(p)
    assert r["capacity_mwh"] == pytest.approx(expected)
    assert r["audit"]["feasible"]
    assert r["audit"]["cycle_residual_mwh"] == pytest.approx(0, abs=1e-8)
    assert minimum_storage(p, exclusive=False)["capacity_mwh"] <= expected + 1e-7


def test_no_free_energy_and_power_shortage():
    assert (
        minimum_storage(replace(solar(), renewable_mw=(0.5, 0.5, 0.5, 0.5)))["status"]
        == "infeasible"
    )
    assert minimum_storage(replace(solar(), power_mw=0.5))["status"] == "infeasible"
    assert minimum_storage(replace(solar(), max_energy_mwh=1))["status"] == "infeasible"


def test_flat_supply_needs_zero_storage():
    r = minimum_storage(replace(solar(), renewable_mw=(1, 1, 1, 1)))
    assert r["capacity_mwh"] == pytest.approx(0)


@pytest.mark.parametrize("shift", [0, 1, 2, 3])
def test_rotation_cannot_create_free_boundary_energy(shift):
    p = solar()
    r = minimum_storage(replace(p, renewable_mw=tuple(np.roll(p.renewable_mw, shift))))
    assert r["capacity_mwh"] == pytest.approx(2 / 0.9)


@pytest.mark.parametrize("hours", [0.25, 2])
def test_duration_scaling(hours):
    r = minimum_storage(replace(solar(), hours=hours))
    assert r["capacity_mwh"] == pytest.approx(hours * 2 / 0.9)


def test_independent_energy_and_mode_audit():
    p = FirmingCase((1,), (1,), 2, 10, charge_efficiency=1, discharge_efficiency=1)
    a = audit_firming(p, [1], [1], [0, 0], 0)
    assert not a["feasible"] and a["simultaneous_mw"] == 1
    assert not audit_firming(p, [0], [0], [1, 0], 1)["feasible"]
    with pytest.raises(ValueError):
        audit_firming(p, [float("nan")], [0], [0, 0], 1)


@pytest.mark.parametrize(
    "change",
    [
        {"power_mw": 0},
        {"hours": True},
        {"charge_efficiency": 1.1},
        {"max_energy_mwh": float("inf")},
        {"renewable_mw": (-1, 0, 0, 0)},
        {"demand_mw": (1,)},
        {"renewable_mw": ()},
    ],
)
def test_validation(change):
    with pytest.raises(ValueError):
        replace(solar(), **change)


def test_agent():
    pytest.importorskip("energy_agents.quantum_ml.studies")
    from enerqit.firming_study import run_firming_engineer

    r = run_firming_engineer()
    assert r["success"] and r["role"]["id"] == "career_quantum_ml_engineer"
    assert len(r["trace"]) == 5
    b = r["reports"]["benchmark_methods"]
    assert b["coincident_mix"]["physical"]["capacity_mwh"] == pytest.approx(
        b["solar_only"]["physical"]["capacity_mwh"]
    )
    assert r["reports"]["assess_sensitivity"]["lull"]["status"] == "infeasible"
