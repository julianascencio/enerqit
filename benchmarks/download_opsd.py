"""Explicit opt-in download of the frozen OPSD 2020-10-06 source (about 130 MB).

No raw data are bundled in EnerQit. OPSD attributes the underlying observations
to ENTSO-E Transparency; provider terms apply separately from EnerQit's MIT code.
"""

import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

BASE = "https://data.open-power-system-data.org/time_series/2020-10-06/"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(args.output)
    root.mkdir(parents=True, exist_ok=True)
    manifest = {
        "doi": "10.25832/time_series/2020-10-06",
        "provider": "Open Power System Data",
        "underlying_source": "ENTSO-E Transparency",
        "files": [],
        "rights": "See provider terms; no blanket MIT license asserted for observations",
    }
    for filename in ("datapackage.json", "time_series_60min_singleindex.csv"):
        target = root / filename
        if target.exists():
            raise FileExistsError(f"Refusing to overwrite {target}")
        temporary = target.with_suffix(target.suffix + ".part")
        digest = hashlib.sha256()
        try:
            with urlopen(BASE + filename, timeout=60) as response, temporary.open("wb") as stream:
                for chunk in iter(lambda: response.read(1024 * 1024), b""):
                    digest.update(chunk)
                    stream.write(chunk)
            temporary.rename(target)
        finally:
            temporary.unlink(missing_ok=True)
        manifest["files"].append(
            {"url": BASE + filename, "sha256": digest.hexdigest(), "bytes": target.stat().st_size}
        )
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
