"""Offline adaptation evidence; no hardware control or security enforcement.

Inspired by the user-supplied Genesis AiX research white paper v0.3 (November
2026). This is a semantic research model. Caller-supplied authority, clocks,
readback sources and replay history are not authenticated by this module.
"""

import hashlib
import json
import math
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path


def canonical_json(value) -> str:
    """Encode finite JSON deterministically for local evidence fingerprints."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def fingerprint(value) -> str:
    """SHA-256 of canonical JSON; a fingerprint is not a signature or authority."""
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def _text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _finite(value) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def _parameters(values) -> tuple[tuple[str, float], ...]:
    pairs = tuple(tuple(pair) for pair in values)
    if not pairs or any(
        len(pair) != 2 or not _text(pair[0]) or not _finite(pair[1]) for pair in pairs
    ):
        raise ValueError("Parameters require nonempty names and finite numeric values")
    if len({pair[0] for pair in pairs}) != len(pairs):
        raise ValueError("Parameter names must be unique")
    return tuple(sorted((key, float(value)) for key, value in pairs))


@dataclass(frozen=True)
class ExecutionContext:
    """Exact identities required at an adaptive execution boundary.

    Unknown values may be represented by None; the gate refuses them. A workload
    ID should fingerprint all relevant inputs and constraints, not just a name.
    """

    workload_id: str | None
    provider: str | None
    control_stack: str | None
    calibration_id: str | None
    model_version: str | None
    boundary_id: str | None


@dataclass(frozen=True)
class Recommendation:
    """Immutable candidate change linked to its observation and validity window.

    All timestamps are UTC Unix seconds in a caller-declared common clock.
    Interval semantics are [valid_from_s, valid_until_s).
    """

    id: str
    version: str
    target: str
    parameters: tuple[tuple[str, float], ...]
    context: ExecutionContext
    evidence_id: str
    evidence_at_s: float
    valid_from_s: float
    valid_until_s: float

    def __post_init__(self):
        if not all(_text(v) for v in (self.id, self.version, self.target, self.evidence_id)):
            raise ValueError("Recommendation identities must be nonempty")
        times = (self.evidence_at_s, self.valid_from_s, self.valid_until_s)
        if not all(_finite(v) for v in times) or not times[0] <= times[1] < times[2]:
            raise ValueError("Require finite evidence <= valid-from < valid-until")
        object.__setattr__(self, "parameters", _parameters(self.parameters))

    @property
    def digest(self) -> str:
        """Bind identity, version, exact settings, context and evidence together."""
        return fingerprint(asdict(self))


@dataclass(frozen=True)
class Authority:
    """Declared approval for one exact proposal; not an authenticated credential."""

    principal: str
    policy: str
    recommendation_digest: str
    valid_from_s: float
    valid_until_s: float
    active: bool = True


@dataclass(frozen=True)
class GateDecision:
    """Eligibility for an offline experiment, never permission to control hardware."""

    status: str
    reasons: tuple[str, ...]
    recommendation_digest: str
    checked_at_s: float
    atomic_enforcement: str = "NOT_ESTABLISHED"


def assess_currentness(
    recommendation: Recommendation,
    current: ExecutionContext | None,
    authority: Authority | None,
    *,
    now_s: float,
    max_evidence_age_s: float,
    consumed_ids: frozenset[str] = frozenset(),
    evidence_complete: bool = True,
    contradictory: bool = False,
    clock_certain: bool = True,
    simulation: bool = False,
) -> GateDecision:
    """Fail closed on missing/stale/changed/replayed evidence or exact scope.

    This pure function neither dispatches nor reserves a recommendation ID.
    Callers must refresh state at dispatch; concurrent/distributed replay and
    authorization-to-effect atomicity are explicitly NOT ESTABLISHED.
    """
    if not _finite(now_s) or not _finite(max_evidence_age_s) or max_evidence_age_s < 0:
        raise ValueError("Use finite time and nonnegative maximum evidence age")
    if type(simulation) is not bool:
        raise ValueError("simulation must be boolean")
    reasons = []
    if evidence_complete is not True:
        reasons.append("incomplete_evidence")
    if contradictory is not False:
        reasons.append("contradictory_or_unknown_evidence")
    if clock_certain is not True:
        reasons.append("uncertain_clock")
    expected = asdict(recommendation.context)
    actual = asdict(current) if current is not None else {}
    for key, value in expected.items():
        if not _text(value) or not _text(actual.get(key)):
            reasons.append(f"unknown_context:{key}")
        elif actual[key] != value:
            reasons.append(f"changed_context:{key}")
    age = now_s - recommendation.evidence_at_s
    if age < 0 or age > max_evidence_age_s:
        reasons.append("stale_or_future_evidence")
    if not recommendation.valid_from_s <= now_s < recommendation.valid_until_s:
        reasons.append("outside_recommendation_window")
    if recommendation.id in consumed_ids:
        reasons.append("replayed_recommendation")
    if authority is None:
        reasons.append("missing_authority")
    else:
        if authority.active is not True:
            reasons.append("inactive_authority")
        if not _text(authority.principal) or not _text(authority.policy):
            reasons.append("unknown_authority")
        if authority.recommendation_digest != recommendation.digest:
            reasons.append("authority_scope_mismatch")
        if (
            not _finite(authority.valid_from_s)
            or not _finite(authority.valid_until_s)
            or not authority.valid_from_s <= now_s < authority.valid_until_s
        ):
            reasons.append("outside_authority_window")
    status = (
        "HOLD_REVALIDATE"
        if reasons
        else ("ELIGIBLE_FOR_SIMULATION" if simulation else "ADVISORY_ONLY")
    )
    return GateDecision(status, tuple(reasons), recommendation.digest, now_s)


@dataclass(frozen=True)
class EffectWitness:
    """Evidence from a command, target readback and optional corroborating channel.

    A distinct source label is necessary but cannot prove channel independence.
    Grades describe declared evidence, not verified trust in a provider.
    """

    request_id: str
    recommendation_digest: str
    target: str
    acknowledged: bool = False
    readback: tuple[tuple[str, float], ...] | None = None
    readback_source: str | None = None
    corroboration: tuple[tuple[str, float], ...] | None = None
    corroboration_source: str | None = None
    contradictory: bool = False
    observed_at_s: float | None = None

    def __post_init__(self):
        for field in ("readback", "corroboration"):
            value = getattr(self, field)
            if value is not None:
                object.__setattr__(self, field, _parameters(value))


def assess_effect(
    recommendation: Recommendation,
    request_id: str,
    witness: EffectWitness | None,
    *,
    request_at_s: float | None = None,
) -> dict:
    """Derive W0-W3 without converting acceptance or partial changes into success.

    The adapter must supply request-bound, post-effect readback. This routine
    compares complete numeric settings exactly; provider-specific tolerances and
    instrument authentication belong in the adapter, which is not implemented.
    """
    result = {"grade": "W0", "status": "UNVERIFIED_EFFECT", "confirmed": False}
    if witness is None:
        return result
    if (
        not _text(request_id)
        or witness.request_id != request_id
        or witness.recommendation_digest != recommendation.digest
        or witness.target != recommendation.target
    ):
        return {**result, "status": "UNBOUND_EVIDENCE"}
    if witness.contradictory is not False:
        return {**result, "status": "DISPUTED"}
    if witness.acknowledged is True:
        result["grade"] = "W1"
    if witness.readback is not None or witness.corroboration is not None:
        if (
            not _finite(request_at_s)
            or not _finite(witness.observed_at_s)
            or witness.observed_at_s < request_at_s
        ):
            return {**result, "status": "UNVERIFIED_TIME_ORDER"}
    if witness.readback is not None:
        if witness.readback != recommendation.parameters:
            return {**result, "status": "PARTIAL_OR_DIFFERENT_EFFECT"}
        if not _text(witness.readback_source):
            return result
        result = {"grade": "W2", "status": "TARGET_STATE_OBSERVED", "confirmed": True}
    if witness.corroboration is not None:
        if witness.corroboration != recommendation.parameters:
            return {**result, "status": "DISPUTED", "confirmed": False}
        if (
            result["grade"] == "W2"
            and _text(witness.corroboration_source)
            and witness.corroboration_source != witness.readback_source
        ):
            result["grade"] = "W3"
            result["status"] = "CORROBORATED_BY_DECLARED_CHANNEL"
    return result


def classify_outcome(
    baseline: float | None,
    candidate: float | None,
    *,
    materiality: float,
    comparable: bool,
    effect_confirmed: bool,
    lower_is_better: bool = True,
) -> dict:
    """Descriptive single-trial change, not significance or causal attribution.

    Caller must establish matching workload, metric, units and evaluation scope.
    Missing/invalid metrics, comparability or effect evidence yield INCONCLUSIVE.
    """
    if not _finite(materiality) or materiality < 0 or type(lower_is_better) is not bool:
        raise ValueError("Use a nonnegative finite materiality and boolean direction")
    if (
        not _finite(baseline)
        or not _finite(candidate)
        or comparable is not True
        or effect_confirmed is not True
    ):
        return {"status": "INCONCLUSIVE", "improvement": None, "causation": "NOT_ESTABLISHED"}
    improvement = (baseline - candidate) * (1 if lower_is_better else -1)
    status = "NO_MATERIAL_CHANGE"
    if improvement > materiality:
        status = "IMPROVED"
    elif improvement < -materiality:
        status = "REGRESSED"
    return {"status": status, "improvement": improvement, "causation": "NOT_ESTABLISHED"}


class LineageStore:
    """Append-only API for local research episodes and explicit parent links.

    Like StudyStore this uses SQLite without a service. It is not tamper-proof:
    a filesystem writer can alter the database. No real-time control calls belong
    in this historical store, and it is not a distributed replay registry.
    """

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as con:
            con.execute("""CREATE TABLE IF NOT EXISTS lineage (
                id TEXT PRIMARY KEY, parent_id TEXT REFERENCES lineage(id),
                digest TEXT NOT NULL, payload TEXT NOT NULL)""")

    @contextmanager
    def _connection(self):
        con = sqlite3.connect(self.path)
        try:
            con.execute("PRAGMA foreign_keys=ON")
            with con:
                yield con
        finally:
            con.close()

    def append(self, record_id: str, payload: dict, *, parent_id: str | None = None) -> str:
        """Append finite JSON; identical retries are no-ops, revisions are refused."""
        if not _text(record_id) or not isinstance(payload, dict):
            raise ValueError("Use a nonempty record ID and dictionary payload")
        if parent_id is not None and (not _text(parent_id) or parent_id == record_id):
            raise ValueError("A parent must be an existing different record")
        encoded = canonical_json(payload)
        digest = fingerprint({"id": record_id, "parent_id": parent_id, "payload": payload})
        with self._connection() as con:
            # Reserve a writer before the read/insert idempotency check.
            con.execute("BEGIN IMMEDIATE")
            old = con.execute("SELECT digest FROM lineage WHERE id=?", (record_id,)).fetchone()
            if old:
                if old[0] != digest:
                    raise ValueError("Record IDs are immutable; append a new revision")
                return digest
            con.execute(
                "INSERT INTO lineage VALUES (?,?,?,?)", (record_id, parent_id, digest, encoded)
            )
        return digest

    def records(self) -> list[dict]:
        """Read in append order, checking content fingerprints for accidental edits."""
        with self._connection() as con:
            rows = con.execute("SELECT id,parent_id,digest,payload FROM lineage ORDER BY rowid")
            output = []
            for record_id, parent_id, digest, payload in rows:
                record = {"id": record_id, "parent_id": parent_id, "payload": json.loads(payload)}
                if fingerprint(record) != digest:
                    raise ValueError(f"Evidence fingerprint mismatch: {record_id}")
                output.append({**record, "digest": digest})
        return output
