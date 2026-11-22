"""Registered engineer workflow for constant-head reservoir screening."""
import hashlib
import importlib.metadata
import json
from importlib.resources import files
from pathlib import Path

import numpy as np

from enerqit.benchmarking import environment
from enerqit.hydro import dispatch_reservoir


def run_hydro_study() -> dict:
    from energy_agents.quantum_ml import run_quantum_research_study
    raw = files("enerqit").joinpath("data/hydro_20261122.json").read_bytes()
    data = json.loads(raw)
    a = data["inputs"]

    def benchmark(_):
        r = dispatch_reservoir(**a)
        q = np.array(data["baseline_turbine_m3"])
        s = a["initial_m3"] - np.r_[0, np.cumsum(q)]
        assert s.min() >= a["terminal_min_m3"]
        assert np.all(q >= np.array(a["minimum_release_m3_s"])*3600)
        assert np.all(q <= a["turbine_m3_s"]*3600)
        return {"optimized": r, "baseline_reservoir_m3": s.tolist(),
                "baseline_gross_eur": float(q @ a["prices_eur_mwh"] * r["mwh_per_m3"])}

    r = run_quantum_research_study(
        {"objective":"Allocate reservoir water while retaining minimum releases and terminal inventory",
         "classification":"synthetic"},
        {"inspect_evidence":lambda _:data, "benchmark_methods":benchmark,
         "assess_sensitivity":lambda _: {
             "terminal":{str(v):dispatch_reservoir(**dict(a,terminal_min_m3=v))
                         for v in (0,20000,40000,60000)},
             "release":{str(v):dispatch_reservoir(**dict(a,minimum_release_m3_s=[v/3600]*3))
                        for v in (0,10000,20000,30000)},
             "head":{str(v):dispatch_reservoir(**dict(a,head_m=v))["gross_value_eur"]
                     for v in (50,100,150)},
             "scaling":{str(n):dispatch_reservoir(**dict(a,inflow_m3_s=[10]*n,
                 prices_eur_mwh=[50]*n,hours=[1]*n,minimum_release_m3_s=[5]*n))["runtime_s"]
                        for n in (3,24,168,8760)}},
         "prepare_handoff":lambda _: {"quantum_used":False,
             "limits":"Constant head, perfect foresight, unlimited bypass; no legal compliance or realized revenue",
             "next_action":"Obtain licensed inflow, stage-volume/head and release constraints; review terminal water value and spillway capacity"}})
    if not r["success"]:
        raise RuntimeError(r["trace"])
    r["fixture_sha256"] = hashlib.sha256(raw).hexdigest()
    r["environment"] = environment()
    r["agent_install"] = json.loads(importlib.metadata.distribution("energy-agents").read_text("direct_url.json") or "{}")
    return r


if __name__ == "__main__":
    p = Path("results/hydro.json")
    p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps(run_hydro_study(),indent=2,allow_nan=False)+"\n")
    print(p)
