from dataclasses import replace
from itertools import product

import numpy as np
import pandas as pd
import pytest

from enerqit.chronological import (
    LifecycleCosts,
    read_profiles,
    replay_storage,
    run_chronological_study,
    validate_profiles,
)
from enerqit.decomposition import block_coordinate, conditioned_block
from enerqit.experiments import ExperimentRecord, fingerprint, write_records
from enerqit.qubo import QUBO
from enerqit.scaling import benchmark_case, problem_fingerprint
from enerqit.solvers.milp import native_milp
from enerqit.storage_sizing import FirmingCase, minimum_storage
from enerqit.workflow_evaluation import compare_firming_workflows, evaluate_workflows


def test_native_linearization_matches_exhaustive_feasible_domain():
    rng = np.random.default_rng(51)
    problem = QUBO(rng.normal(size=(6, 6)), 8.3, constraints=((np.ones((1, 6)), np.array([3])),))
    reference = min(problem.energy(x) for x in product((0, 1), repeat=6) if problem.feasible(x))
    solved = native_milp(problem)
    assert solved["status"] == "optimal"
    assert solved["energy"] == pytest.approx(reference)
    assert solved["lower_bound"] == pytest.approx(reference)
    assert problem.feasible(solved["x"])


def test_native_enforces_equalities_without_relying_on_penalties():
    problem = QUBO(np.eye(3), constraints=((np.ones((1, 3)), [2]),))
    assert problem.energy(np.zeros(3)) == 0  # Encoded unconstrained minimum is infeasible.
    solved = native_milp(problem)
    assert solved["energy"] == pytest.approx(2)
    assert sum(solved["x"]) == 2
    assert native_milp(problem, time_limit_s=1e-12)["status"] == "timeout"
    with pytest.raises(ValueError):
        native_milp(problem, time_limit_s=np.nan)


def test_conditioned_blocks_preserve_full_objective_and_constraints():
    q = np.array([[1, -2, 3], [-2, 4, 5], [3, 5, -6]])
    problem = QUBO(q, 9, constraints=((np.ones((1, 3)), [2]),))
    outside = np.array([1, 0, 1])
    sub = conditioned_block(problem, outside, [0, 2])
    for local in product((0, 1), repeat=2):
        full = outside.copy()
        full[[0, 2]] = local
        assert sub.energy(local) == pytest.approx(problem.energy(full))
        assert sub.feasible(local) == problem.feasible(full)
    with pytest.raises(ValueError):
        conditioned_block(problem, [0.5, 0, 1], [0, 2])
    with pytest.raises(ValueError):
        conditioned_block(problem, outside, [0, 0])


def test_decomposition_does_not_lose_coupling_or_invent_feasibility():
    problem = QUBO(np.array([[1, -3, 0], [-3, 2, -2], [0, -2, 1]]))
    result = block_coordinate(problem, np.zeros(3), block_size=3, passes=1)
    reference = min(problem.energy(x) for x in product((0, 1), repeat=3))
    assert result.energy == pytest.approx(reference)
    assert result.feasible
    assert not result.metadata["certified"]
    assert result.energy <= result.metadata["initial_energy"]
    with pytest.raises(ValueError):
        block_coordinate(problem, [0.5, 0, 1])


def test_sparse_year_has_linear_memory_and_known_capacity():
    case = FirmingCase((0, 3, 3, 0) * 2190, (1,) * 8760, 2, 10)
    result = minimum_storage(case, exclusive=False)
    assert result["capacity_mwh"] == pytest.approx(2 / 0.9)
    assert result["matrix_bytes"] < 3_000_000
    assert result["matrix_nnz"] < 20 * 8760


@pytest.mark.parametrize("seed", range(10))
def test_physical_lp_reduction_matches_milp_and_independent_audit(seed):
    rng = np.random.default_rng(seed)
    case = FirmingCase(
        tuple(rng.uniform(0, 3, 24)),
        tuple(rng.uniform(0.7, 1.3, 24)),
        2,
        20,
        charge_efficiency=0.83,
        discharge_efficiency=0.92,
    )
    mip = minimum_storage(case)
    lp = minimum_storage(case, net_balance_modes=True)
    assert lp["status"] == mip["status"]
    if lp["status"] == "optimal":
        assert lp["capacity_mwh"] == pytest.approx(mip["capacity_mwh"], abs=1e-7)
        assert lp["audit"]["feasible"]
        assert lp["binary_variables"] == 0


def fixture():
    return pd.DataFrame(
        {"solar_mw": [0, 3, 3, 0] * 4, "wind_mw": [1] * 16, "demand_mw": [1] * 16},
        index=pd.date_range("2024-01-01", periods=16, freq="h", tz="UTC"),
    )


@pytest.mark.parametrize("kind", ["naive", "gap", "duplicate", "negative", "nan", "unordered"])
def test_chronological_data_contract_rejects_unsafe_inputs(kind):
    frame = fixture()
    if kind == "naive":
        frame.index = frame.index.tz_localize(None)
    elif kind == "gap":
        frame = frame.drop(frame.index[5])
    elif kind == "duplicate":
        frame.index = pd.DatetimeIndex([frame.index[0], *frame.index[:-1]])
    elif kind == "negative":
        frame.iloc[0, 0] = -1
    elif kind == "nan":
        frame.iloc[0, 0] = float("nan")
    else:
        frame = frame.iloc[::-1]
    with pytest.raises(ValueError):
        validate_profiles(frame)


def test_csv_hashes_and_timezone_requirement(tmp_path):
    path = tmp_path / "input.csv"
    frame = fixture()
    frame.to_csv(path, index_label="timestamp")
    loaded, metadata = read_profiles(path)
    pd.testing.assert_frame_equal(loaded, frame.astype(float), check_freq=False, check_names=False)
    assert len(metadata["source_sha256"]) == 64
    path.write_text(path.read_text().replace("+00:00", ""))
    with pytest.raises(ValueError, match="explicit timezone"):
        read_profiles(path)


def test_holdout_changes_never_retune_capacity_or_training_scales():
    frame = fixture()
    split = frame.index[8]
    original = run_chronological_study(frame, split_at=split, provenance={"synthetic": True})
    shifted = frame.copy()
    shifted.loc[split:, ["solar_mw", "wind_mw"]] = 0
    changed = run_chronological_study(shifted, split_at=split, provenance={"synthetic": True})
    assert original["frozen_parameters"] == changed["frozen_parameters"]
    assert original["training"]["capacity_mwh"] == changed["training"]["capacity_mwh"]
    assert changed["holdout"]["unserved_mwh"] > original["holdout"]["unserved_mwh"]
    assert changed["holdout"]["physical_feasible"]
    assert not changed["holdout"]["full_load_served"]


def test_replay_energy_conservation_initial_energy_and_reserve():
    case = FirmingCase((0, 0), (1, 1), 2, 10, discharge_efficiency=0.5)
    r = replay_storage(case, 4, initial_soc_fraction=0.5, reserve_fraction=0.25)
    assert r["initial_energy_mwh"] == 2
    assert r["final_energy_mwh"] == 1
    assert r["served_mwh"] == pytest.approx(0.5)
    assert r["unserved_mwh"] == pytest.approx(1.5)
    assert r["physical_feasible"]
    assert r["max_energy_residual_mwh"] < 1e-9
    assert replay_storage(case, 0)["unserved_mwh"] == 2
    with pytest.raises(ValueError):
        replay_storage(case, 4, initial_soc_fraction=0.1, reserve_fraction=0.2)


def test_lifecycle_costs_independent_cashflow_arithmetic():
    costs = LifecycleCosts(
        100,
        50,
        1000,
        30,
        10,
        years=3,
        discount_rate=0,
        replacement_years=(2,),
        replacement_energy_fraction=0.5,
    )
    result = costs.evaluate(2, 1)
    assert result["net_present_cost_eur"] == 200 + 50 + 1000 + 30 + 30 + 100
    assert result["cashflows"][2]["replacement_eur"] == 100
    discounted = replace(costs, discount_rate=0.1).evaluate(2, 1)
    assert discounted["net_present_cost_eur"] == pytest.approx(
        1280 + 10 / 1.1 + 110 / 1.1**2 + 10 / 1.1**3
    )
    with pytest.raises(ValueError):
        replace(costs, replacement_years=(2, 2))


def test_record_retains_unknown_cost_and_requires_hardware_evidence(tmp_path):
    record = ExperimentRecord(
        "test", "CPU", "classical", fingerprint({}), 1, "failed", None, error="intentional failure"
    )
    assert record.to_dict()["costs"]["amount"] is None
    write_records([record], tmp_path / "records.jsonl")
    assert "intentional failure" in (tmp_path / "records.jsonl").read_text()
    with pytest.raises(ValueError, match="device_id"):
        replace(record, execution_kind="quantum_hardware").to_dict()
    with pytest.raises(ValueError):
        replace(record, timings_s={"search": -1}).to_dict()


def test_hash_includes_feasibility_and_budget_rejects_late_results():
    a = QUBO(np.eye(3), constraints=((np.ones((1, 3)), [1]),))
    b = QUBO(np.eye(3), constraints=((np.ones((1, 3)), [2]),))
    assert problem_fingerprint(a) != problem_fingerprint(b)
    records = benchmark_case(a, seconds=1e-6, seeds=(0,))
    assert len(records) == 4
    for record in records:
        assert record["feasible"]
        assert record["objective"] == pytest.approx(1)
        assert record["metrics"]["initial_objective"] == pytest.approx(1)
        assert record["metrics"]["time_to_target_s"] == 0  # Shared warm start already optimal.


def test_workflow_failures_and_repeatability_are_measured():
    count = [0]

    def fail(_):
        raise RuntimeError("deliberate failure")

    def changing(_):
        count[0] += 1
        return {"outcome": count[0], "feasible": True, "tool_calls": 1}

    result = evaluate_workflows({"failed": fail, "changing": changing}, inputs={}, repeats=2)
    assert result["summary"]["failed"]["failed_runs"] == 2
    assert not result["summary"]["changing"]["identical_successful_outcomes"]
    assert all(r["metrics"]["reported_human_minutes"] is None for r in result["records"])


def test_actual_registered_agent_matches_direct_script():
    pytest.importorskip("energy_agents.quantum_ml.studies")
    result = compare_firming_workflows(repeats=2)
    assert result["same_outcome_across_workflows"]
    assert all(r["metrics"]["tool_calls"] == 4 for r in result["records"])
    assert all(r["provenance"]["live_llm"] is False for r in result["records"])
