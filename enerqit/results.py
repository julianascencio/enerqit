"""Serializable results with evidence, limitations and reproducibility metadata."""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np


def _json_value(value):
    if isinstance(value, np.ndarray):
        return [_json_value(v) for v in value.tolist()]
    if isinstance(value, np.generic):
        return _json_value(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    if isinstance(value, dict):
        return {str(k): _json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(v) for v in value]
    return value


@dataclass
class InferenceResult:
    """A fit, including identifiability caveats rather than just a point estimate."""

    parameters: dict[str, float]
    method: str
    rmse: float
    n_observations: int
    status: str = "estimated"
    units: dict[str, str] = field(default_factory=dict)
    diagnostics: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-compatible values; nonfinite diagnostics become null."""
        return _json_value(asdict(self))

    def to_json(self, path=None):
        """Serialize the result, optionally writing to a file."""
        content = json.dumps(self.to_dict(), indent=2, allow_nan=False)
        if path is not None:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_text(content + "\n", encoding="utf-8")
        return content


@dataclass
class SolverResult:
    """A binary candidate; success is never equivalent to certified optimality."""

    x: np.ndarray
    energy: float
    method: str
    seed: int | None
    elapsed_s: float
    feasible: bool
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return _json_value(asdict(self))
