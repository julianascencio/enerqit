"""Run the validation lab offline, or on an explicitly supplied historical CSV."""

import argparse
import json
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd

from enerqit.chronological import (
    OPSD_COLUMNS,
    LifecycleCosts,
    read_profiles,
    run_chronological_study,
)
from enerqit.experiments import ExperimentRecord, fingerprint, write_records
from enerqit.scaling import run_scaling_benchmark


def synthetic_profiles(days=30):
    """Deterministic varying daily/weather fixture; explicitly not observations."""
    index = pd.date_range("2025-01-01", periods=24 * days, freq="h", tz="UTC")
    t = np.arange(len(index))
    solar = np.maximum(0, np.sin(np.pi * (t % 24 - 6) / 12)) * (1 + 0.2 * np.cos(t / 80))
    wind = 0.5 + 0.3 * np.sin(t / 25) + 0.1 * np.cos(t / 9)
    load = 1 + 0.15 * np.sin(t / 5)
    return pd.DataFrame({"solar_mw": solar, "wind_mw": wind, "demand_mw": load}, index=index)


def illustrative_costs():
    """Authored scenario assumptions, not sourced quotes or financial advice."""
    return LifecycleCosts(200000, 150000, 4000000, 250000, 100000)


def compact_study(result):
    """Keep aggregate evidence while omitting long dispatch arrays from a report."""
    arrays = {"charge_mw", "discharge_mw", "energy_mwh"}
    return {
        key: {k: v for k, v in value.items() if k not in arrays}
        if isinstance(value, dict)
        else value
        for key, value in result.items()
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="results/validation-lab")
    parser.add_argument("--csv", help="Local CSV; no network access occurs in this command")
    parser.add_argument("--opsd", action="store_true", help="Use OPSD Germany column mapping")
    parser.add_argument("--start", default="2018-01-01T00:00:00Z")
    parser.add_argument("--end", default="2020-01-01T00:00:00Z")
    parser.add_argument("--split-at", default="2019-01-01T00:00:00Z")
    parser.add_argument("--benchmark-seconds", type=float, default=0.2)
    parser.add_argument("--reference-seconds", type=float, default=5.0)
    parser.add_argument("--storage-seconds", type=float, default=30.0)
    parser.add_argument(
        "--agent", action="store_true", help="Run installed registered-agent comparison"
    )
    parser.add_argument("--skip-scaling", action="store_true")
    args = parser.parse_args(argv)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    started = perf_counter()
    if args.csv:
        frame, provenance = read_profiles(
            args.csv, columns=OPSD_COLUMNS if args.opsd else None, start=args.start, end=args.end
        )
        provenance["synthetic"] = False
        provenance["source"] = (
            "https://doi.org/10.25832/time_series/2020-10-06" if args.opsd else "user supplied CSV"
        )
        split = args.split_at
    else:
        frame = synthetic_profiles()
        provenance = {"synthetic": True, "source": "authored deterministic fixture"}
        split = "2025-01-21T00:00:00Z"
    preprocessing = perf_counter() - started
    run_start = perf_counter()
    result = run_chronological_study(
        frame,
        split_at=split,
        provenance=provenance,
        costs=illustrative_costs(),
        time_limit_s=args.storage_seconds,
    )
    study_s = perf_counter() - run_start
    report = compact_study(result)
    report["cost_basis"] = (
        "Illustrative user-editable assumptions; no market quote or achieved savings"
    )
    (output / "firming.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    training = result["training"]
    record = ExperimentRecord(
        experiment="chronological-firming",
        method="sparse_physical_lp_and_causal_holdout",
        execution_kind="classical",
        input_sha256=fingerprint(
            {
                "study": result["input_sha256"],
                "economics": report.get("economics"),
                "aging": report.get("aging_assumption"),
                "initial_soc": 0.5,
                "reserve": 0.0,
            }
        ),
        seed=None,
        status="completed" if training["status"] == "optimal" else training["status"],
        feasible=None if result["holdout"] is None else result["holdout"]["full_load_served"],
        objective=training.get("capacity_mwh"),
        timings_s={
            "preprocessing": preprocessing,
            "study_including_audits": study_s,
            "total": preprocessing + study_s,
        },
        resources={
            "constraint_matrix_bytes": training["matrix_bytes"],
            "scope": "CSC arrays, not process peak",
        },
        metrics={
            "training_status": training["status"],
            "holdout": report["holdout"],
            "aged_holdout": report["aged_holdout"],
            "cost_basis": report["cost_basis"],
        },
        provenance=provenance,
    )
    write_records([record], output / "firming-record.jsonl")
    if not args.skip_scaling:
        run_scaling_benchmark(
            output / "scaling.jsonl",
            seconds=args.benchmark_seconds,
            reference_seconds=args.reference_seconds,
        )
    if args.agent:
        from enerqit.workflow_evaluation import compare_firming_workflows

        workflows = compare_firming_workflows()
        write_records(workflows["records"], output / "workflows.jsonl")
        (output / "workflow-summary.json").write_text(
            json.dumps(workflows["summary"], indent=2) + "\n"
        )
    print(
        json.dumps(
            {
                "output": str(output),
                "training_status": training["status"],
                "training_intervals": len(frame.loc[frame.index < pd.Timestamp(split)]),
                "capacity_mwh": training.get("capacity_mwh"),
                "holdout_unserved_mwh": None
                if result["holdout"] is None
                else result["holdout"]["unserved_mwh"],
            }
        )
    )


if __name__ == "__main__":
    main()
