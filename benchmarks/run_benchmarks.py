"""Run from the repository root after installation."""

import argparse

from enerqit.benchmarking import run_benchmark

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="benchmarks/results/reference.jsonl")
    args = parser.parse_args()
    rows = run_benchmark(args.output)
    print(f"Wrote {len(rows)} benchmark records to {args.output}")
