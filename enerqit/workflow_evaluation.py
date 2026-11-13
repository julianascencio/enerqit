"""Paired scripted/agent workflow evaluation, with no inferred human-time savings."""

import importlib.metadata
import json
from time import perf_counter

import numpy as np

from enerqit.experiments import ExperimentRecord, fingerprint
from enerqit.storage_sizing import FirmingCase, minimum_storage


def evaluate_workflows(workflows, *, inputs, repeats=3, effort_minutes=None):
    """Measure repeated workflows returning an outcome plus actual trace metadata.

    Each callable gets the same integer seed and must return ``outcome`` (strict
    JSON semantics without timestamps), ``feasible`` and ``tool_calls``. Failures
    remain records. Reproducibility compares semantic outcome hashes, not timing.
    Human effort is unmeasured unless explicitly supplied per workflow by a user.
    """
    if type(repeats) is not int or repeats < 2:
        raise ValueError("At least two repeats are required")
    effort_minutes = effort_minutes or {}
    if any(not np.isfinite(v) or v < 0 for v in effort_minutes.values()):
        raise ValueError("Reported human effort must be finite and nonnegative")
    rows, summaries = [], {}
    for name, workflow in workflows.items():
        digests, elapsed, successes = [], [], 0
        for repeat in range(repeats):
            start = perf_counter()
            error, feasible, result = None, None, {}
            try:
                result = workflow(0)  # Fixed seed: repeatability, not stochastic robustness.
                if type(result["feasible"]) is not bool:
                    raise ValueError("Workflow must return a boolean feasibility audit")
                if type(result["tool_calls"]) is not int or result["tool_calls"] < 0:
                    raise ValueError("Workflow tool_calls must be an observed nonnegative integer")
                feasible = result["feasible"]
                digest = fingerprint(result["outcome"])
                digests.append(digest)
                successes += int(feasible)
                status = "completed" if feasible else "infeasible"
            except Exception as exc:
                error, digest, status = f"{type(exc).__name__}: {exc}", None, "failed"
            seconds = perf_counter() - start
            elapsed.append(seconds)
            rows.append(
                ExperimentRecord(
                    experiment="workflow-repeatability",
                    method=name,
                    execution_kind="classical",
                    input_sha256=fingerprint(inputs),
                    seed=0,
                    status=status,
                    feasible=feasible,
                    timings_s={"total": seconds},
                    error=error,
                    metrics={
                        "repeat": repeat,
                        "outcome_sha256": digest,
                        "tool_calls": result.get("tool_calls"),
                        "tool_trace": result.get("tool_trace"),
                        "outcome": result.get("outcome"),
                        "reported_human_minutes": effort_minutes.get(name),
                    },
                    provenance={
                        "live_llm": result.get("live_llm"),
                        "human_effort_basis": "user supplied"
                        if name in effort_minutes
                        else "unmeasured",
                    },
                ).to_dict()
            )
        summaries[name] = {
            "runs": repeats,
            "feasible_runs": successes,
            "failed_runs": sum(r["status"] == "failed" for r in rows if r["method"] == name),
            "median_wall_s": float(np.median(elapsed)),
            "identical_successful_outcomes": len(digests) == repeats and len(set(digests)) == 1,
            "reported_human_minutes": effort_minutes.get(name),
        }
    return {"records": rows, "summary": summaries}


def compare_firming_workflows(*, repeats=3):
    """Execute the installed energy-agents registered study and a direct baseline.

    Both invoke identical callbacks and numerical work. The agent is its existing
    deterministic offline planner, not a live LLM or an autonomous scientist.
    Missing optional dependencies raise explicitly instead of fabricating a run.
    """
    from energy_agents.quantum_ml import run_quantum_research_study

    inputs = {
        "renewable_mw": [0, 3, 3, 0],
        "demand_mw": [1, 1, 1, 1],
        "power_mw": 2,
        "max_energy_mwh": 10,
    }
    case = FirmingCase(**inputs)

    def handoff(context):
        result = context["reports"]["benchmark_methods"]
        return {
            "capacity_mwh": round(result["capacity_mwh"], 9),
            "feasible": result["audit"]["feasible"],
            "sensitivity_infeasible": context["reports"]["assess_sensitivity"]["status"]
            == "infeasible",
        }

    callbacks = {
        "inspect_evidence": lambda _: {"synthetic": True, "inputs": inputs},
        "benchmark_methods": lambda _: minimum_storage(case),
        "assess_sensitivity": lambda _: minimum_storage(FirmingCase((0.5,) * 4, (1,) * 4, 2, 10)),
        "prepare_handoff": handoff,
    }

    def direct(_):
        reports = {}
        for name, callback in callbacks.items():
            reports[name] = callback({"reports": reports})
        return {
            "outcome": reports["prepare_handoff"],
            "feasible": reports["prepare_handoff"]["feasible"],
            "tool_calls": len(callbacks),
            "tool_trace": list(callbacks),
            "live_llm": False,
        }

    def agent(_):
        actual_calls = []

        def wrapped(name, callback):
            def invoke(context):
                actual_calls.append(name)
                return callback(context)

            return invoke

        run = run_quantum_research_study(
            {"objective": "Evaluate the same cyclic firming case", "classification": "mixed"},
            {name: wrapped(name, callback) for name, callback in callbacks.items()},
        )
        if not run["success"]:
            raise RuntimeError(str(run["trace"]))
        return {
            "outcome": run["reports"]["prepare_handoff"],
            "feasible": run["reports"]["prepare_handoff"]["feasible"],
            "tool_calls": len(actual_calls),
            "tool_trace": actual_calls,
            "live_llm": False,
        }

    result = evaluate_workflows(
        {"direct_script": direct, "registered_agent": agent}, inputs=inputs, repeats=repeats
    )
    hashes = {
        r["metrics"]["outcome_sha256"] for r in result["records"] if r["status"] == "completed"
    }
    result["same_outcome_across_workflows"] = len(hashes) == 1 and all(
        r["status"] == "completed" for r in result["records"]
    )
    distribution = importlib.metadata.distribution("energy-agents")
    install = json.loads(distribution.read_text("direct_url.json") or "{}")
    for row in result["records"]:
        row["provenance"]["agent_package_version"] = distribution.version
        row["provenance"]["agent_commit"] = install.get("vcs_info", {}).get("commit_id")
        row["provenance"]["agent_role"] = "career_quantum_ml_engineer"
    return result
