from dataclasses import replace

import numpy as np
import pytest

from enerqit.datasets import fixed_array, weather
from enerqit.inference import candidate_problem, fit_orientation, fit_tracker
from enerqit.inverter import efficiency_curve, fit_efficiency
from enerqit.ivtools import ModuleParameters, fit_iv, fit_mpp, iv_current, operating_points
from enerqit.pvsystem import fixed_ac, tracker_ac
from enerqit.solvers import group_exact
from enerqit.thermal import derating_cap, fit_derating
from enerqit.topology import fit_string_counts


def test_orientation_recovery_and_candidate_baseline():
    f, truth = fixed_array(noise_w=20)
    result = fit_orientation(f, 35, -5)
    assert abs(result.parameters["tilt"] - truth["tilt"]) < 0.1
    assert abs(result.parameters["azimuth"] - truth["azimuth"]) < 0.1
    assert result.status == "estimated"
    a = np.column_stack([fixed_ac(f, 35, -5, t, 172) for t in (15, 28, 40)])
    q = candidate_problem(a, f.power_ac)
    np.testing.assert_array_equal(group_exact(q).x, [0, 1, 0])


def test_tracker_recovery_and_night():
    f = weather(days=2)
    f["power_ac"] = tracker_ac(f, 35, -5, max_angle=52, gcr=0.38)
    result = fit_tracker(f, 35, -5, seed=2, maxiter=60)
    assert result.parameters["gcr"] == pytest.approx(0.38, abs=0.005)
    assert result.parameters["max_angle"] == pytest.approx(52, abs=0.3)
    assert np.isfinite(f.power_ac).all()
    assert (f.loc[f.ghi == 0, "power_ac"] == 0).all()


def test_iv_parameter_recovery_and_curve():
    module = ModuleParameters()
    v = np.tile(np.linspace(0, 38, 60), 3)
    g = np.repeat([400, 750, 1000], 60)
    t = np.repeat([15, 35, 50], 60)
    i = iv_current(v, g, t, module)
    guess = replace(
        module, photocurrent=9, resistance_series=0.45, resistance_shunt=500, a_ref=1.6
    )
    result = fit_iv(v, i, g, t, initial=guess)
    assert result.rmse < 1e-5
    for key in ("photocurrent", "resistance_series", "resistance_shunt", "a_ref"):
        assert result.parameters[key] == pytest.approx(getattr(module, key), rel=1e-3)
    curve = iv_current(np.linspace(0, 35, 100), 1000, 25, module)
    assert np.all(np.diff(curve) < 0)


def test_operational_mpp_and_integer_topology():
    g, t = np.linspace(250, 1000, 30), np.linspace(20, 55, 30)
    module = ModuleParameters(photocurrent=9.1, resistance_series=0.42)
    points = operating_points(g, t, module)
    result = fit_mpp(points["v_mp"], points["i_mp"], g, t)
    assert result.parameters["photocurrent"] == pytest.approx(9.1, abs=0.001)
    assert result.parameters["resistance_series"] == pytest.approx(0.42, abs=0.001)
    count = fit_string_counts(20 * points["v_mp"], 6 * points["i_mp"], g, t, module=module)
    assert count.parameters["module_count"] == 120
    assert count.parameters["modules_per_string"] == 20


def test_efficiency_recovery_and_nonidentifiability():
    dc = np.linspace(8000, 90_000, 100)
    coefficients = [0.004, 0.009, 0.012]
    ac = dc * efficiency_curve(dc, 100_000, coefficients)
    result = fit_efficiency(dc, ac, rated_power=100_000)
    np.testing.assert_allclose(list(result.parameters.values()), coefficients, atol=1e-7)
    r = fit_efficiency(np.full(20, 50_000), np.full(20, 49_000), rated_power=100_000)
    assert r.status == "not_identifiable"
    with pytest.raises(ValueError):
        fit_efficiency(dc, dc * 1.1, rated_power=100_000)


def test_thermal_excitation_and_command_exclusion():
    t = np.linspace(30, 85, 100)
    available = np.full(100, 120_000.0)
    ac = derating_cap(t, 100_000, 58, 0.015)
    result = fit_derating(t, ac, available, rated_power=100_000)
    assert result.parameters["knee"] == pytest.approx(58, abs=0.01)
    assert result.parameters["slope"] == pytest.approx(0.015, abs=1e-5)
    result = fit_derating(t, np.full(100, 100_000), available, rated_power=100_000)
    assert result.status == "not_identifiable"
    assert not result.parameters
    result = fit_derating(
        t, ac, available, rated_power=100_000, command_limit=np.full(100, 50_000)
    )
    assert result.status == "not_identifiable"


def test_power_alone_is_insufficient():
    f, _ = fixed_array()
    with pytest.raises(ValueError, match="missing channels"):
        fit_orientation(f[["power_ac"]], 35, -5)
