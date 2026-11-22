"""Independent state-variable LP and physical boundary tests."""

from dataclasses import replace
from itertools import product

import numpy as np
import pytest

from enerqit.activation_study import run_activation_study, vertex_lp_reference
from enerqit.storage_envelope import (
    ActivationWindow,
    initial_energy_envelope,
    prepare_activation,
    replay_activation,
)


def case():
    return ActivationWindow((-20, 10), (-10, 20), (1, 1), 30, 30, 40)


def test_analytic_headroom_and_preparation():
    r = initial_energy_envelope(case())
    assert r["initial_lower_dc_mwh"] == pytest.approx(20 / .9 - 9)
    assert r["initial_upper_dc_mwh"] == pytest.approx(22)
    assert r["required_capacity_dc_mwh"] == pytest.approx(20 / .9 + 9)
    p = prepare_activation(case(), 40, 1)
    assert p["export_ac_mwh"] == pytest.approx(16.2)
    assert p["minimum_hours"] == pytest.approx(.54)
    assert p["status"] == "feasible"
    assert prepare_activation(case(), 40, .5)["status"] == "preparation_infeasible"
    assert prepare_activation(case(), 20, 0)["status"] == "feasible"


@pytest.mark.parametrize("seed", range(8))
def test_all_vertices_against_independent_state_lp(seed):
    rng = np.random.default_rng(seed)
    lower = rng.uniform(-4, 1, 4)
    upper = lower + rng.uniform(0, 5, 4)
    c = ActivationWindow(tuple(lower), tuple(upper), tuple(rng.uniform(.2, 2, 4)),
                         6, 6, 10 + seed * 3, .83, .94)
    got, ref = initial_energy_envelope(c), vertex_lp_reference(c)
    assert got["status"] == ref["status"]
    if got["status"] == "feasible":
        for k in ("initial_lower_dc_mwh", "initial_upper_dc_mwh"):
            assert got[k] == pytest.approx(ref[k], abs=1e-7)
            for path in product(*zip(c.lower_mw, c.upper_mw)):
                run = replay_activation(c, path, got[k])
                assert run["missed_absorption_ac_mwh"] < 1e-7
                assert run["missed_discharge_ac_mwh"] < 1e-7
        # Interior activations also obey the guarantee, including sign crossings.
        for _ in range(5):
            run = replay_activation(c, rng.uniform(lower, upper),
                                    (got["initial_lower_dc_mwh"] + got["initial_upper_dc_mwh"]) / 2)
            assert run["missed_absorption_ac_mwh"] + run["missed_discharge_ac_mwh"] < 1e-7


def test_energy_and_power_infeasibility_are_distinct():
    assert initial_energy_envelope(replace(case(), capacity_dc_mwh=30))["status"] == "infeasible"
    p = initial_energy_envelope(replace(case(), charge_mw=19))
    assert p["power_feasible"] is False
    assert p["energy_interval_width_mwh"] > 0
    assert prepare_activation(replace(case(), charge_mw=19), 20, 1)["status"] == "activation_infeasible"


def test_full_empty_and_losses():
    c = case()
    full = replay_activation(c, [-20, 20], 40)
    assert full["missed_absorption_ac_mwh"] == 20
    run = replay_activation(c, [-20, 20], 20)
    assert run["missed_absorption_ac_mwh"] == run["missed_discharge_ac_mwh"] == 0
    assert 20 + 20 - 20 - run["conversion_loss_mwh"] == pytest.approx(run["energy_dc_mwh"][-1])
    empty = replay_activation(c, [-10, 20], 0)
    assert empty["missed_discharge_ac_mwh"] == pytest.approx(11.9)


def test_zero_and_singleton_boundary():
    c = ActivationWindow((0,), (0,), (1,), 0, 0, 0)
    assert initial_energy_envelope(c)["status"] == "feasible"
    assert prepare_activation(c, 0, 0)["status"] == "feasible"
    c = ActivationWindow((-10, 10), (-10, 10), (1, 1), 10, 10, 10, 1, 1)
    assert initial_energy_envelope(c)["initial_upper_dc_mwh"] == 0
    assert initial_energy_envelope(c)["initial_lower_dc_mwh"] == 0


def test_preparation_charge_and_unavailable_export():
    c = ActivationWindow((5,), (5,), (2,), 5, 5, 20, .8, 1)
    p = prepare_activation(c, 0, 3)
    assert p["import_ac_mwh"] == 12.5
    assert p["minimum_hours"] == 2.5
    c = ActivationWindow((-5,), (-5,), (1,), 5, 0, 20, 1, 1)
    assert prepare_activation(c, 20, 100)["minimum_hours"] is None


@pytest.mark.parametrize("change", [
    {"hours": (0, 1)}, {"hours": (1,)}, {"lower_mw": (np.nan, 0)},
    {"upper_mw": (-30, 0)}, {"charge_mw": True}, {"capacity_dc_mwh": -1},
    {"charge_efficiency": 0}, {"discharge_efficiency": 1.01}, {"lower_mw": ()},
])
def test_reject_invalid_window(change):
    with pytest.raises(ValueError):
        replace(case(), **change)


def test_reject_invalid_replay_and_preparation():
    for p, initial in [([-21, 20], 20), ([-20], 20), ([-20, 20], 41), ([-20, np.nan], 0)]:
        with pytest.raises(ValueError):
            replay_activation(case(), p, initial)
    for initial, duration in [(np.nan, 1), (40, -1), (41, 1), (40, True)]:
        with pytest.raises(ValueError):
            prepare_activation(case(), initial, duration)
    with pytest.raises(ValueError):
        vertex_lp_reference(replace(case(), lower_mw=(0,) * 9, upper_mw=(0,) * 9, hours=(1,) * 9))


def test_actual_agent_execution():
    pytest.importorskip("energy_agents.quantum_ml")
    r = run_activation_study()
    assert r["success"] and r["human_review_required"]
    assert r["execution_authorized"] is False
    assert [s["tool"] for s in r["trace"]] == [
        "inspect_evidence", "benchmark_methods", "assess_sensitivity", "prepare_handoff", "finish"]
    assert r["reports"]["benchmark_methods"]["max_reference_gap_mwh"] < 1e-7
    assert r["reports"]["benchmark_methods"]["preparation_fee_eur"] == pytest.approx(81)
