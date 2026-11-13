"""Common experiment records for measured outcomes, including failed attempts."""

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

import numpy as np

from enerqit.benchmarking import environment

ExecutionKind = Literal["classical", "quantum_inspired", "circuit_simulation", "quantum_hardware"]


def fingerprint(value) -> str:
    """Hash strict, sorted JSON; callers must include all inputs and constraints."""
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


@dataclass
class ExperimentRecord:
    """Versioned evidence, with unknown values represented by null rather than zero.

    Durations are nonnegative wall seconds. Memory is explicitly scoped; Python
    allocator measurements exclude native solver allocations. Costs are supplied
    estimates or receipts, never inferred from runtime without a declared tariff.
    A hardware record requires device and job identifiers, not just an SDK name.
    """

    experiment: str
    method: str
    execution_kind: ExecutionKind
    input_sha256: str
    seed: int | None
    status: str
    feasible: bool | None
    objective: float | None = None
    timings_s: dict = field(default_factory=dict)
    resources: dict = field(default_factory=dict)
    costs: dict = field(
        default_factory=lambda: {"amount": None, "currency": None, "basis": "unknown"}
    )
    metrics: dict = field(default_factory=dict)
    provenance: dict = field(default_factory=dict)
    error: str | None = None
    schema_version: str = "1.0"
    environment: dict = field(default_factory=environment)

    def to_dict(self) -> dict:
        """Validate and return strict JSON-compatible data."""
        if self.execution_kind not in {
            "classical",
            "quantum_inspired",
            "circuit_simulation",
            "quantum_hardware",
        }:
            raise ValueError("Unknown execution kind")
        if self.status not in {
            "optimal",
            "feasible",
            "infeasible",
            "timeout",
            "failed",
            "completed",
        }:
            raise ValueError("Unknown experiment status")
        if len(self.input_sha256) != 64 or any(
            c not in "0123456789abcdef" for c in self.input_sha256
        ):
            raise ValueError("input_sha256 must be a SHA256 hex digest")
        if self.feasible is not None and type(self.feasible) is not bool:
            raise ValueError("feasible must be boolean or null")
        if self.execution_kind == "quantum_hardware" and not all(
            self.provenance.get(k) for k in ("device_id", "job_id")
        ):
            raise ValueError("Quantum hardware needs device_id and job_id evidence")
        for value in self.timings_s.values():
            if value is not None and (not np.isfinite(value) or value < 0):
                raise ValueError("Timing values must be nonnegative or null")
        amount = self.costs.get("amount")
        if amount is not None and (
            not np.isfinite(amount)
            or amount < 0
            or not self.costs.get("currency")
            or self.costs.get("basis") in {None, "unknown"}
        ):
            raise ValueError("Known costs need nonnegative amount, currency and an explicit basis")
        value = asdict(self)
        json.dumps(value, allow_nan=False)
        return value


def write_records(records, path) -> None:
    """Write JSONL after validating every record, preserving failed outcomes."""
    rows = [
        r.to_dict() if isinstance(r, ExperimentRecord) else ExperimentRecord(**r).to_dict()
        for r in records
    ]
    content = "".join(json.dumps(row, sort_keys=True, allow_nan=False) + "\n" for row in rows)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
