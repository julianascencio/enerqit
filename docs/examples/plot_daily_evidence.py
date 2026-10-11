"""
Receive another 24 hours of study evidence
==========================================

An initial commissioned model remains frozen while a separately versioned
current-evidence model is refitted. No production alert or scheduling service
is created. Identical batches are idempotent; late corrections remain auditable.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import matplotlib.pyplot as plt

from enerqit.datasets import fixed_array
from enerqit.inference import fit_orientation
from enerqit.timeseries import StudyStore

frame, truth = fixed_array(days=5, noise_w=150)
estimates = []
with TemporaryDirectory() as directory:
    store = StudyStore(Path(directory) / "study.sqlite")
    for day, (_, batch) in enumerate(frame.groupby(frame.index.normalize()), start=1):
        print("Batch:", store.ingest("synthetic-asset", batch))
        evidence = store.frame("synthetic-asset")
        result = fit_orientation(evidence, 35, -5)
        result.provenance = {"synthetic": True, "evidence_days": day, "model_version": "0.1.0"}
        store.snapshot("synthetic-asset", f"day-{day}", result, reference=day == 1)
        estimates.append(result.parameters["tilt"])
    assert store.analyses("synthetic-asset")[0]["reference"]
    assert store.ingest("synthetic-asset", batch)["duplicate"]
    print("Immutable reference:", store.analyses("synthetic-asset")[0])
fig, ax = plt.subplots(figsize=(7, 3.5))
ax.plot(range(1, 6), estimates, "o-", label="Current evidence fit")
ax.axhline(truth["tilt"], color="black", linestyle="--", label="Synthetic truth")
ax.set(
    xlabel="Accumulated days",
    ylabel="Tilt (°)",
    title="Study evidence accumulates; reference remains frozen",
)
ax.legend()
fig.tight_layout()
