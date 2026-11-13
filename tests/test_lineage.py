"""Semantic negative controls, witness integrity and offline persistence."""

import sqlite3
from dataclasses import replace

import pytest

from enerqit.lineage import (
    Authority,
    EffectWitness,
    ExecutionContext,
    LineageStore,
    Recommendation,
    assess_currentness,
    assess_effect,
    classify_outcome,
)
from enerqit.lineage_study import run_lineage_study


@pytest.fixture
def setup():
    context = ExecutionContext("workload-sha", "local", "stack-v1", "cal-v1", "model-v1", "b1")
    rec = Recommendation(
        "r1",
        "1",
        "solver",
        (("reads", 16), ("sweeps", 80)),
        context,
        "observation-sha",
        100,
        100,
        200,
    )
    auth = Authority("researcher", "policy-v1", rec.digest, 100, 200)
    return rec, context, auth


def gate(rec, context, auth, **kwargs):
    return assess_currentness(
        rec, context, auth, **{"now_s": 110, "max_evidence_age_s": 20, **kwargs}
    )


def test_advisory_default_and_no_atomic_claim(setup):
    assert gate(*setup).status == "ADVISORY_ONLY"
    assert gate(*setup, simulation=True).status == "ELIGIBLE_FOR_SIMULATION"
    assert gate(*setup).atomic_enforcement == "NOT_ESTABLISHED"


@pytest.mark.parametrize(
    "changes",
    [
        {"now_s": 99},
        {"now_s": 121},
        {"now_s": 200},
        {"evidence_complete": False},
        {"evidence_complete": None},
        {"contradictory": True},
        {"contradictory": None},
        {"clock_certain": False},
        {"consumed_ids": frozenset({"r1"})},
    ],
)
def test_negative_controls_hold(setup, changes):
    assert gate(*setup, simulation=True, **changes).status == "HOLD_REVALIDATE"


@pytest.mark.parametrize(
    "field",
    ["workload_id", "provider", "control_stack", "calibration_id", "model_version", "boundary_id"],
)
@pytest.mark.parametrize("value", [None, "", "different"])
def test_every_required_context_predicate(setup, field, value):
    rec, ctx, auth = setup
    assert gate(rec, replace(ctx, **{field: value}), auth).status == "HOLD_REVALIDATE"
    unknown_proposal = replace(rec, context=replace(ctx, **{field: None}))
    assert (
        gate(
            unknown_proposal,
            unknown_proposal.context,
            replace(auth, recommendation_digest=unknown_proposal.digest),
        ).status
        == "HOLD_REVALIDATE"
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"active": False},
        {"active": None},
        {"principal": ""},
        {"policy": ""},
        {"valid_until_s": 110},
        {"valid_from_s": 111},
        {"valid_until_s": float("nan")},
    ],
)
def test_authority_revocation_expiry_and_unknown(setup, changes):
    rec, ctx, auth = setup
    assert gate(rec, ctx, replace(auth, **changes)).status == "HOLD_REVALIDATE"
    assert gate(rec, ctx, None).status == "HOLD_REVALIDATE"


@pytest.mark.parametrize(
    "changes",
    [
        {"version": "2"},
        {"target": "other"},
        {"parameters": (("reads", 32),)},
        {"evidence_id": "new"},
    ],
)
def test_exact_recommendation_binding(setup, changes):
    rec, ctx, auth = setup
    assert "authority_scope_mismatch" in gate(replace(rec, **changes), ctx, auth).reasons


def test_dispatch_revalidation_catches_state_shift(setup):
    rec, ctx, auth = setup
    assert gate(*setup, simulation=True).status == "ELIGIBLE_FOR_SIMULATION"
    assert gate(rec, replace(ctx, boundary_id="b2"), auth).status == "HOLD_REVALIDATE"


@pytest.mark.parametrize(
    "parameters",
    [(), (("reads", float("nan")),), (("reads", True),), (("reads", 1), ("reads", 2))],
)
def test_invalid_parameters_rejected(setup, parameters):
    with pytest.raises(ValueError):
        replace(setup[0], parameters=parameters)


def test_canonical_parameters_cannot_mutate_after_binding(setup):
    values = [["sweeps", 80], ["reads", 16]]
    rec = replace(setup[0], parameters=values)
    original = rec.digest
    values[0][1] = 1
    assert rec.digest == original == setup[0].digest


def test_effect_grades_and_partial_application(setup):
    rec = setup[0]
    witness = EffectWitness(
        "command", rec.digest, rec.target, acknowledged=True, observed_at_s=111
    )

    def check(w):
        return assess_effect(rec, "command", w, request_at_s=110)

    assert check(None)["grade"] == "W0"
    assert check(witness) == {"grade": "W1", "status": "UNVERIFIED_EFFECT", "confirmed": False}
    assert (
        check(replace(witness, readback=(("reads", 16),)))["status"]
        == "PARTIAL_OR_DIFFERENT_EFFECT"
    )
    witness = replace(witness, readback=rec.parameters, readback_source="provider")
    assert check(witness)["grade"] == "W2"
    same_source = replace(witness, corroboration=rec.parameters, corroboration_source="provider")
    assert check(same_source)["grade"] == "W2"
    assert check(replace(same_source, corroboration_source="separate-channel"))["grade"] == "W3"
    assert check(replace(same_source, corroboration=(("reads", 32),)))["status"] == "DISPUTED"
    assert not check(replace(same_source, contradictory=True))["confirmed"]
    assert not check(replace(witness, request_id="different"))["confirmed"]
    assert not check(replace(witness, target="other"))["confirmed"]
    assert not check(replace(witness, recommendation_digest="old"))["confirmed"]


@pytest.mark.parametrize("observed_at", [None, 99, float("nan")])
def test_effect_requires_post_request_time_order(setup, observed_at):
    rec = setup[0]
    witness = EffectWitness(
        "command",
        rec.digest,
        rec.target,
        acknowledged=True,
        readback=rec.parameters,
        readback_source="provider",
        observed_at_s=observed_at,
    )
    result = assess_effect(rec, "command", witness, request_at_s=100)
    assert result["status"] == "UNVERIFIED_TIME_ORDER"
    assert not result["confirmed"]


@pytest.mark.parametrize(
    "candidate,status",
    [
        (1, "IMPROVED"),
        (3, "REGRESSED"),
        (2, "NO_MATERIAL_CHANGE"),
        (None, "INCONCLUSIVE"),
        (float("nan"), "INCONCLUSIVE"),
    ],
)
def test_outcome_discrimination(candidate, status):
    result = classify_outcome(
        2, candidate, materiality=0.01, comparable=True, effect_confirmed=True
    )
    assert result["status"] == status
    assert result["causation"] == "NOT_ESTABLISHED"


def test_acknowledgement_and_noncomparable_results_cannot_be_success():
    assert (
        classify_outcome(10, 1, materiality=0, comparable=True, effect_confirmed=False)["status"]
        == "INCONCLUSIVE"
    )
    assert (
        classify_outcome(10, 1, materiality=0, comparable=False, effect_confirmed=True)["status"]
        == "INCONCLUSIVE"
    )
    assert (
        classify_outcome(
            1, 10, materiality=0, comparable=True, effect_confirmed=True, lower_is_better=False
        )["status"]
        == "IMPROVED"
    )


def test_store_restart_parent_links_and_immutable_ids(tmp_path):
    path = tmp_path / "lineage.sqlite"
    store = LineageStore(path)
    digest = store.append("baseline", {"value": 2})
    assert store.append("baseline", {"value": 2}) == digest
    store.append("adaptation", {"value": 1}, parent_id="baseline")
    assert len(LineageStore(path).records()) == 2
    assert LineageStore(path).records()[1]["parent_id"] == "baseline"
    with pytest.raises(ValueError, match="immutable"):
        store.append("baseline", {"value": 3})
    with pytest.raises(sqlite3.IntegrityError):
        store.append("orphan", {}, parent_id="missing")
    with pytest.raises(ValueError):
        store.append("nan", {"value": float("nan")})
    with sqlite3.connect(path) as con:
        con.execute("UPDATE lineage SET payload='{}' WHERE id='baseline'")
    with pytest.raises(ValueError, match="fingerprint"):
        store.records()


def test_runnable_study_has_real_solver_results_and_honest_scope():
    report = run_lineage_study()
    assert report["execution_kind"] == "classical"
    assert report["comparison_protocol"]["equal_compute"] is False
    assert report["acknowledgement_only"]["confirmed"] is False
    assert len(report["records"]) == 8
    for key, value in report["negative_controls"].items():
        assert value["status"] == (
            "ELIGIBLE_FOR_SIMULATION" if key == "current" else "HOLD_REVALIDATE"
        )
    for record in report["records"]:
        assert record["effect"]["grade"] == "W2"
        assert record["post_effect"]["result"]["metadata"]["reads"] == 16
        assert record["outcome"]["causation"] == "NOT_ESTABLISHED"
