import itertools
import json
from importlib.resources import files

import numpy as np
import pytest

from enerqit.hydro import dispatch_reservoir


def inputs():
    return json.loads(files('enerqit').joinpath('data/hydro_20261122.json').read_text())['inputs']


def test_analytic_allocation():
    r = dispatch_reservoir(**inputs())
    assert r['turbine_m3'] == pytest.approx([20000,40000,20000])
    assert r['reservoir_m3'][-1] == pytest.approx(20000)
    assert r['gross_value_eur'] == pytest.approx(1226.25)
    assert r['max_water_residual_m3'] < 1e-6


@pytest.mark.parametrize('seed', range(6))
def test_independent_discrete_reference(seed):
    rng = np.random.default_rng(seed)
    prices = rng.integers(-20,100,3)
    inflow = rng.integers(0,3,3)
    # Integer flow volumes give an integral network-flow polytope. Enumerate
    # turbine and bypass separately, directly conserving water at each step.
    best = -np.inf
    for q in itertools.product(range(3),repeat=3):
        for b in itertools.product(range(5),repeat=3):
            s=3
            valid=True
            for t in range(3):
                s += inflow[t]-q[t]-b[t]
                valid &= 0 <= s <= 5 and q[t]+b[t] >= 1
            if valid and s >= 1:
                best=max(best,np.dot(q,prices))
    r=dispatch_reservoir(inflow/3600,prices,[1]*3,[1/3600]*3,
        initial_m3=3,capacity_m3=5,terminal_min_m3=1,turbine_m3_s=2/3600,head_m=100)
    if not np.isfinite(best):
        assert r['status'] == 'infeasible'
    else:
        assert r['gross_value_eur']/r['mwh_per_m3'] == pytest.approx(best)


def test_negative_prices_bypass_and_infeasibility():
    a=inputs()
    r=dispatch_reservoir(**dict(a,prices_eur_mwh=[-10]*3))
    assert sum(r['generation_mwh']) == 0
    assert sum(r['bypass_m3']) >= 60000-1e-6
    assert dispatch_reservoir(**dict(a,terminal_min_m3=60000))['status']=='infeasible'


def test_unequal_duration_inflow_and_overflow():
    r=dispatch_reservoir([1,0],[10,20],[.5,1],[0,0],initial_m3=0,
        capacity_m3=1000,terminal_min_m3=100,turbine_m3_s=0,head_m=50)
    assert sum(r['bypass_m3']) >= 800
    assert r['reservoir_m3'][-1] >= 100
    assert r['feasible']


@pytest.mark.parametrize('change', [dict(hours=[0,1,1]),dict(inflow_m3_s=[-1,0,0]),
    dict(prices_eur_mwh=[np.nan]*3),dict(efficiency=1.1),dict(head_m=0),
    dict(initial_m3=200000),dict(terminal_min_m3=-1),dict(hours=[1]),dict(turbine_m3_s=True)])
def test_invalid(change):
    with pytest.raises(ValueError):
        dispatch_reservoir(**dict(inputs(),**change))


def test_agent():
    pytest.importorskip('energy_agents.quantum_ml')
    from enerqit.hydro_study import run_hydro_study
    r=run_hydro_study()
    assert r['success'] and r['human_review_required']
    assert not r['execution_authorized']
    assert len(r['trace'])==5
    assert r['reports']['benchmark_methods']['baseline_gross_eur']==pytest.approx(833.85)
