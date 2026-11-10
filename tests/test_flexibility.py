"""Independent physical accounting and small-domain scheduling certificates."""

from dataclasses import replace
from itertools import product

import numpy as np
import pytest

from enerqit.flexibility import (
    BatchJob,
    BatchProblem,
    GridScenario,
    batch_options,
    batch_schedule_qubo,
    enumerate_batch_schedules,
    evaluate_batch_bits,
    evaluate_schedule,
    solve_batch_milp,
)
from enerqit.flexibility_study import flexibility_case, problem_from_case
from enerqit.solvers import exact


def fixture():
    return problem_from_case(flexibility_case())


def test_hand_computed_energy_deadlines_and_scenario_constraints():
    p = fixture()
    r = evaluate_schedule(p, [1, 3, 4, 1])
    assert r["feasible"] and r["all_jobs_completed"]
    assert r["incremental_mw"] == [0, 3, 1, 1, 4, 0]
    assert r["work_energy_mwh"] == 9
    assert r["energy_charge_eur"] == 525
    assert r["scenarios"][1]["grid_import_mw"] == [4, 7, 6, 6, 8, 4]
    half_hour = evaluate_schedule(replace(p, step_hours=.5), [1, 3, 4, 1])
    assert half_hour["work_energy_mwh"] == 4.5
    assert half_hour["energy_charge_eur"] == 262.5
    assert evaluate_schedule(p, [2, 4, 5, 2])["all_jobs_completed"]  # Exact deadline allowed.
    for bad in [[3, 3, 4, 1], [1, 3, 6, 1], [1, 3, 4], [True, 3, 4, 1]]:
        with pytest.raises(ValueError):
            evaluate_schedule(p, bad)


def test_price_only_rebound_and_nominal_only_stress_failure():
    p = fixture()
    price = solve_batch_milp(p, enforce_grid=False)["physical"]
    assert price["energy_charge_eur"] == 105
    assert price["max_violation_mw"] == 5 and not price["feasible"]
    nominal = solve_batch_milp(replace(p, scenarios=p.scenarios[:1]))["physical"]
    assert nominal["energy_charge_eur"] == 390 and nominal["feasible"]
    stress = evaluate_schedule(p, nominal["starts"])
    assert stress["max_violation_mw"] == 1 and not stress["feasible"]
    robust = solve_batch_milp(p)["physical"]
    oracle = enumerate_batch_schedules(p)
    assert oracle["combinations"] == 144
    assert robust["energy_charge_eur"] == oracle["physical"]["energy_charge_eur"] == 525
    assert robust["work_energy_mwh"] == price["work_energy_mwh"] == nominal["work_energy_mwh"]


def test_exhaustive_energy_identity_with_negative_prices_and_invalid_states():
    p = BatchProblem("2026-11-10T00:00:00Z", 1, (-2, 3),
                     (BatchJob("a", (1,), 0, 2), BatchJob("b", (1,), 0, 2)),
                     (GridScenario("base", (0, 0), (1, 1)),))
    q = batch_schedule_qubo(p)
    assert q.size == 6
    penalty = q.metadata["penalty_eur"]
    assert penalty == 11
    for bits in product((0, 1), repeat=6):
        a0, a1, b0, b1, slack0, slack1 = bits
        residuals = [a0+a1-1, b0+b1-1, a0+b0+slack0-1, a1+b1+slack1-1]
        expected = -4 + 5*(a1+b1) + penalty*sum(r*r for r in residuals)
        assert q.energy(bits) == pytest.approx(expected)
        assert q.feasible(np.array(bits)) == all(r == 0 for r in residuals)
        physical = evaluate_batch_bits(p, bits[:4])
        if q.feasible(np.array(bits)):
            assert physical["feasible"]
            assert q.energy(bits) == pytest.approx(physical["energy_charge_eur"])
        else:
            assert q.energy(bits) > 1  # Known feasible optimum; no omitted-job profit.
    assert exact(q).energy == 1
    assert solve_batch_milp(p)["physical"]["energy_charge_eur"] == 1


def test_randomized_native_milp_and_qubo_oracles():
    rng = np.random.default_rng(71)
    for i in range(8):
        jobs = tuple(BatchJob(f"j{k}", (int(rng.integers(1, 3)),), 0, 3) for k in range(3))
        cap = tuple(int(v) for v in rng.integers(1, 5, size=3))
        p = BatchProblem("2026-11-10T00:00:00+00:00", .5,
                         tuple(float(v) for v in rng.integers(-20, 40, size=3)), jobs,
                         (GridScenario(f"s{i}", (0, 0, 0), cap),))
        oracle, native = enumerate_batch_schedules(p), solve_batch_milp(p)
        assert oracle["status"] == native["status"]
        q = batch_schedule_qubo(p)
        result = exact(q)
        assert result.feasible == (native["status"] == "optimal")
        if result.feasible:
            decoded = evaluate_batch_bits(p, result.x[:q.metadata["choice_bits"]])
            assert decoded["feasible"]
            assert result.energy == pytest.approx(oracle["physical"]["energy_charge_eur"])
            assert decoded["energy_charge_eur"] == pytest.approx(native["physical"]["energy_charge_eur"])


def test_conservative_rounding_can_exclude_physically_feasible_work():
    p = BatchProblem("2026-11-10T00:00:00Z", 1, (10,), (BatchJob("a", (.6,), 0, 1),),
                     (GridScenario("base", (0,), (.8,)),))
    assert solve_batch_milp(p)["status"] == "optimal"
    assert not exact(batch_schedule_qubo(p, step_mw=1)).feasible
    finer = batch_schedule_qubo(p, step_mw=.1)
    result = exact(finer)
    assert result.feasible and evaluate_batch_bits(p, result.x[:1])["feasible"]


def test_no_silent_repair_or_dropped_work():
    p = fixture()
    data = batch_options(p)
    x = np.zeros(len(data["options"]), dtype=int)
    r = evaluate_batch_bits(p, x)
    assert not r["feasible"] and not r["all_jobs_completed"]
    assert r["starts"] is None and r["energy_charge_eur"] is None
    for group in data["groups"]:
        x[group[0]] = 1
    x[data["groups"][0][1]] = 1
    assert evaluate_batch_bits(p, x)["selection_counts"][0] == 2


def test_infeasibility_and_bounded_exact_resources():
    p = fixture()
    tight_jobs = tuple(replace(j, deadline_slot=4) if j.id == "Batch-C" else j for j in p.jobs)
    tight = replace(p, jobs=tight_jobs)
    assert solve_batch_milp(tight)["status"] == "infeasible"
    assert enumerate_batch_schedules(tight)["physical"] is None
    broken = replace(p, scenarios=(replace(p.scenarios[0], baseline_mw=(9,)*6),))
    assert solve_batch_milp(broken)["status"] == "infeasible"
    with pytest.raises(ValueError, match="baseline"):
        batch_schedule_qubo(broken)
    with pytest.raises(ValueError, match="budget"):
        enumerate_batch_schedules(p, max_combinations=100)
    q = batch_schedule_qubo(p)
    with pytest.raises(ValueError, match="max_variables"):
        exact(q, max_variables=10)


@pytest.mark.parametrize("kwargs", [{"profile_mw": (0,)}, {"profile_mw": (-1,)},
                                  {"profile_mw": (float("nan"),)}, {"id": ""},
                                  {"release_slot": True}, {"deadline_slot": 0},
                                  {"release_slot": 3, "deadline_slot": 4}])
def test_invalid_job(kwargs):
    with pytest.raises(ValueError):
        replace(fixture().jobs[0], **kwargs)


@pytest.mark.parametrize("kwargs", [{"start_utc": "2026-11-10T00:00:00"},
                                  {"start_utc": "2026-11-10T00:00:00+01:00"},
                                  {"step_hours": 0}, {"step_hours": float("inf")},
                                  {"prices_eur_mwh": (float("nan"),)*6},
                                  {"jobs": ()}, {"scenarios": ()}])
def test_invalid_problem(kwargs):
    with pytest.raises(ValueError):
        replace(fixture(), **kwargs)


def test_duplicate_ids_bad_shapes_and_grid_steps():
    p = fixture()
    with pytest.raises(ValueError):
        replace(p, jobs=(p.jobs[0], p.jobs[0]))
    with pytest.raises(ValueError):
        replace(p, scenarios=(p.scenarios[0], p.scenarios[0]))
    with pytest.raises(ValueError):
        GridScenario("bad", (0, 0), (1,))
    with pytest.raises(ValueError):
        replace(p, scenarios=(GridScenario("short", (0,), (1,)),))
    for step in (0, -1, True, float("inf")):
        with pytest.raises(ValueError):
            batch_schedule_qubo(p, step_mw=step)


def test_current_agent_executes_new_domain_and_sensitivity():
    pytest.importorskip("energy_agents.quantum_ml.studies")
    from enerqit.flexibility_study import run_flexibility_engineer

    r = run_flexibility_engineer()
    assert r["success"] and r["role"]["id"] == "career_quantum_ml_engineer"
    assert r["mode"] == "scripted_tool_workflow" and not r["execution_authorized"]
    assert [t["tool"] for t in r["trace"]] == ["inspect_evidence", "benchmark_methods",
                                              "assess_sensitivity", "prepare_handoff", "finish"]
    for row in r["reports"]["benchmark_methods"]["records"]:
        if row["physical_feasible"]:
            assert row["native_cost_gap_eur"] >= -1e-8
        else:
            assert row["native_cost_gap_eur"] is None
    sensitivity = r["reports"]["assess_sensitivity"]
    assert sensitivity["deadline"][0]["status"] == "infeasible"
    assert sensitivity["baseline_margin"][-1]["status"] == "infeasible"
    assert [x["jobs"] for x in sensitivity["scaling"]] == [4, 8, 16]
