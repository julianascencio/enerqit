import json

from enerqit.benchmarking import run_benchmark


def test_benchmark_records_original_and_encoded_objectives(tmp_path):
    records = run_benchmark(tmp_path / "runs.jsonl", seeds=(7,), instance_seeds=(42,))
    assert len(records) == 4
    assert records[0]["absolute_energy_gap"] == 0
    assert all(r["elapsed_s"] >= 0 and r["construction_s"] >= 0 for r in records)
    assert all("feasible" in r and "signal_rmse" in r and "environment" in r for r in records)
    assert len({r["qubo_sha256"] for r in records}) == 1
    loaded = [json.loads(line) for line in (tmp_path / "runs.jsonl").read_text().splitlines()]
    assert len(loaded) == len(records)
