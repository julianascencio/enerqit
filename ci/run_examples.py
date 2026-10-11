"""Execute every gallery example and save plots/logs in a chosen directory."""

import argparse
import contextlib
import json
import runpy
from pathlib import Path
from time import perf_counter

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results/examples")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    manifest = []
    for example in sorted((root / "docs/examples").glob("plot_*.py")):
        start = perf_counter()
        with (output / f"{example.stem}.log").open("w") as log, contextlib.redirect_stdout(log):
            runpy.run_path(str(example), run_name="__main__")
        figures = []
        for number in plt.get_fignums():
            path = output / f"{example.stem}_{number}.png"
            plt.figure(number).savefig(path, dpi=140, bbox_inches="tight")
            figures.append(path.name)
        plt.close("all")
        manifest.append(
            {
                "example": example.name,
                "seconds": perf_counter() - start,
                "figures": figures,
                "status": "passed",
            }
        )
        print(f"Passed: {example.name}")
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
