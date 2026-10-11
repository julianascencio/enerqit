"""Command line entry points for local reproducible studies."""

import argparse
import json
from pathlib import Path


def main(argv=None):
    """Run synthetic demo, benchmark or one explicit CSV ingestion."""
    parser = argparse.ArgumentParser(prog="enerqit", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    demo = sub.add_parser("demo", help="recover a synthetic fixed-array orientation")
    demo.add_argument("--output", default="results/demo")
    demo.add_argument("--seed", default=42, type=int)
    bench = sub.add_parser("benchmark", help="run exact, SA and bSB synthetic comparisons")
    bench.add_argument("--output", default="results/benchmark.jsonl")
    ingest = sub.add_parser("ingest", help="ingest one daily CSV into a local study")
    ingest.add_argument("csv")
    ingest.add_argument("--store", required=True)
    ingest.add_argument("--asset", required=True)
    args = parser.parse_args(argv)
    if args.command == "demo":
        from enerqit.benchmarking import environment
        from enerqit.datasets import fixed_array
        from enerqit.inference import fit_orientation

        output = Path(args.output)
        output.mkdir(parents=True, exist_ok=True)
        frame, truth = fixed_array(seed=args.seed)
        frame.to_csv(output / "synthetic_observations.csv")
        result = fit_orientation(frame, truth["latitude"], truth["longitude"])
        result.provenance = {"synthetic": True, "truth": truth, "environment": environment()}
        result.to_json(output / "orientation.json")
        print(result.to_json())
    elif args.command == "benchmark":
        from enerqit.benchmarking import run_benchmark

        records = run_benchmark(args.output)
        print(json.dumps({"output": args.output, "runs": len(records)}))
    else:
        from enerqit.iotools import read_csv
        from enerqit.timeseries import StudyStore

        print(json.dumps(StudyStore(args.store).ingest(args.asset, read_csv(args.csv))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
