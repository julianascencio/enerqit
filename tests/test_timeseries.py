import json
import sqlite3

import numpy as np
import pandas as pd
import pytest

from enerqit.cli import main
from enerqit.datasets import fixed_array
from enerqit.iotools import read_csv
from enerqit.quality import validate_frame
from enerqit.results import InferenceResult
from enerqit.timeseries import StudyStore
from enerqit.uncertainty import day_block_bootstrap


def test_ingestion_idempotent_late_data_and_frozen_reference(tmp_path):
    f, _ = fixed_array(days=3)
    store = StudyStore(tmp_path / "study.sqlite")
    first = f.iloc[:96]
    assert store.ingest("plant", first)["inserted"] == 96
    assert store.ingest("plant", first)["duplicate"]
    result = InferenceResult({"tilt": 28}, "test", 0, 96)
    store.snapshot("plant", "baseline", result, reference=True)
    baseline = store.analyses("plant")[0]
    assert store.ingest("plant", f.iloc[96:])["inserted"] == 192
    revised = first.copy()
    revised.iloc[20, revised.columns.get_loc("power_ac")] += 100
    assert store.ingest("plant", revised)["replaced"] == 1
    assert len(store.frame("plant")) == len(f)
    assert store.analyses("plant")[0] == baseline
    with pytest.raises(sqlite3.IntegrityError):
        store.snapshot("plant", "other", result, reference=True)
    with pytest.raises(ValueError, match="schema"):
        store.ingest("plant", first[["power_ac"]])


def test_data_contract_and_csv(tmp_path):
    f, _ = fixed_array(days=1)
    path = tmp_path / "data.csv"
    f.to_csv(path)
    out = read_csv(path, required=["power_ac"])
    np.testing.assert_allclose(out, f)
    naive = f.copy()
    naive.index = naive.index.tz_localize(None)
    naive.to_csv(path)
    with pytest.raises(ValueError, match="offset"):
        read_csv(path)
    with pytest.raises(ValueError):
        validate_frame(pd.concat([f, f]))
    f.iloc[0, 0] = np.nan
    with pytest.raises(ValueError, match="finite"):
        validate_frame(f, ["ghi"])


def test_bootstrap_reproducibility():
    f, _ = fixed_array(days=5)

    def estimator(data):
        return {"mean": float(data.power_ac.mean())}

    a = day_block_bootstrap(f, estimator, repeats=20, seed=3)
    b = day_block_bootstrap(f, estimator, repeats=20, seed=3)
    assert a == b
    assert a["mean"]["lower"] <= a["mean"]["upper"]


def test_cli_and_strict_json(tmp_path):
    main(["demo", "--output", str(tmp_path)])
    result = json.loads((tmp_path / "orientation.json").read_text())
    assert result["provenance"]["synthetic"]
    main(
        [
            "ingest",
            str(tmp_path / "synthetic_observations.csv"),
            "--store",
            str(tmp_path / "study.sqlite"),
            "--asset",
            "demo",
        ]
    )
    missing = InferenceResult({}, "test", float("nan"), 0)
    assert json.loads(missing.to_json())["rmse"] is None
