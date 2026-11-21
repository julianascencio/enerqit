"""
Battery readiness needs charging headroom as well as stored energy
====================================================================

1. Problem and evidence
-------------------------
AEMO's `20 November 2026 summer outlook release
<https://www.aemo.com.au/newsroom/media-release/aemo-prepares-for-summer-as-energy-supplies-forecast-to-remain-sufficient>`_
expects sufficient supply under forecast conditions while identifying high and
low operational demand as preparation challenges. This does not establish a
shortage or calibrate a battery. A storage operator's narrow question here is:
what starting inventory guarantees exact tracking of every signed activation in
a declared two-hour range, and can the battery reach it before service starts?

2. Offline data and preprocessing
-----------------------------------
All numerical inputs are authored synthetic MIT data. Ordered one-hour UTC
intervals, AC MW signs and usable DC MWh are explicit in the fixture. No
interpolation, network retrieval or provider observations are used. The existing
EDI generation connectors were inspected at the commit recorded in the fixture;
instantaneous aggregate MW cannot identify battery SOC or service requirements.

Run from a checkout with::

    python -m pip install -e '.[docs]' -r requirements/agent-study.txt
    python -m enerqit.activation_study
    python docs/examples/plot_storage_headroom.py

The first command installs dependencies; both examples then execute offline.
"""

import json
from importlib.resources import files

import matplotlib.pyplot as plt

from enerqit.activation_study import run_activation_study
from enerqit.storage_envelope import ActivationWindow, initial_energy_envelope

raw = files("enerqit").joinpath("data/activation_20261121.json").read_text()
data = json.loads(raw)
case = ActivationWindow(**data["inputs"])
envelope = initial_energy_envelope(case)
print("Admissible initial DC MWh:", envelope)

# %%
# 3. Reusable methods and actual engineer invocation
# -----------------------------------------------------
# The existing career_quantum_ml_engineer executes four registered callbacks.
# This is its scripted tool workflow, not a live LLM evaluation. Numerical code
# stays in EnerQit. The trace, fixture hash, installed agent commit and package
# versions are exported by the CLI. Execution success is not scientific approval.
result = run_activation_study()
print("Actual agent trace:", result["trace"])
print("Agent install:", result["agent_install"])
bench = result["reports"]["benchmark_methods"]
print("Independent LP gap (MWh):", bench["max_reference_gap_mwh"])
print("Preparation:", bench["preparation"])

# %%
# 4. Benchmark and physical accounting
# ---------------------------------------
# Cumulative monotonic bounds give an exact O(n) solution for the declared box.
# An independent classical LP enumerates all small-case corner paths using
# separate boundary-state variables. No QUBO, annealing, quantum-inspired method,
# circuit simulation or hardware execution is justified for this analytic task.
# The shown probe is one path; the envelope certifies all paths under assumptions.
# Clipped replay is a diagnostic failure, never successful service.
fig, axes = plt.subplots(1, 2, figsize=(10, 4), constrained_layout=True)
for name, row in bench["probe_replays"].items():
    axes[0].plot([0, 1, 2], row["energy_dc_mwh"], marker="o", label=name)
axes[0].set(xlabel="Hours from activation start", ylabel="Usable DC energy (MWh)",
            title="Synthetic request: absorb 20, export 20 MW", ylim=(0, 42))
axes[0].legend()
labels = list(bench["probe_replays"])
axes[1].bar(labels, [r["missed_absorption_ac_mwh"] for r in bench["probe_replays"].values()],
            label="Missed absorption")
axes[1].bar(labels, [r["missed_discharge_ac_mwh"] for r in bench["probe_replays"].values()],
            bottom=[r["missed_absorption_ac_mwh"] for r in bench["probe_replays"].values()],
            label="Missed discharge")
axes[1].set(ylabel="Untracked AC energy (MWh)", title="Physical tracking failures")
axes[1].legend()

# %%
# 5. Sensitivity and business decision
# ---------------------------------------
# The preparation step exports 16.2 AC MWh over at least 0.54 h at 30 MW, moving
# initial inventory from 40 to 22 DC MWh. The assumed EUR5/AC-MWh throughput fee
# is EUR81, a budget component only: energy settlement, inventory opportunity
# value and actual wear are excluded. Comparing terminal states is necessary
# before claiming net economic benefit; no savings or revenue are claimed here.
# Uncertainty radii are engineering scenarios, not statistical confidence levels.
# More uncertainty can make preparation impossible at any starting inventory.
sensitivity = result["reports"]["assess_sensitivity"]
print("Preparation fee only (EUR):", bench["preparation_fee_eur"])
print("Uncertainty sensitivity:", sensitivity["uncertainty_radius_mw"])
print("Scaling runtimes (seconds):", {n: r["runtime_s"] for n, r in sensitivity["scaling"].items()})

# %%
# 6. Limits and next practical action
# ---------------------------------------
# A Cartesian box can be conservative for correlated activations and gives no
# probability of failure outside its bounds. Constant efficiencies, unlimited
# preparation energy access and permitted grid import/export are assumptions.
# Ramp, thermal, network, standby loss, competing obligations and terminal targets
# are absent. Validate licensed activation/SOC measurements and preparation
# permissions, then independently review technical and commercial constraints.
# This is neither an AEMO compliance assessment nor equipment dispatch.
plt.show()
