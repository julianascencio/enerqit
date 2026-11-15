"""
Reserve procurement when outage probabilities are uncertain
===========================================================

NESO's `14 November 2026 status report
<https://www.neso.energy/document/390236/download>`_ presents forward-looking
system and wind information. It does not calibrate this synthetic study.
We advance the uncertainty gap in the 14 November adequacy example: a planner
chooses guaranteed capacity for a four-hour window under uncertain probabilities.

Install and run (offline after installation)::

    python -m pip install -e '.[dev,docs]' -r requirements/agent-study.txt
    python -m enerqit.robust_adequacy_study
    python docs/examples/plot_probability_ambiguity.py

All capacities, probabilities, targets and EUR fees are authored assumptions.
See :doc:`method and limitations </probability_ambiguity>`.
"""

# %%
# 1. Execute the current engineer's four registered tools. This is an actual
# scripted tool workflow, with no LLM, remote hardware or dispatch permissions.
import matplotlib.pyplot as plt

from enerqit.robust_adequacy_study import run_robust_adequacy

result = run_robust_adequacy()
print(result["role"]["id"], result["trace"])
print("Installed agent:", result["agent_install"])
print("Input SHA256:", result["fixture_sha256"])
# %%
# 2. The fixture preserves the previous common-outage model's three capacities.
# We now allow probability mass to move within a total-variation radius. A radius
# of .05 permits moving five percentage points; it is NOT a 95% confidence bound.
print(result["reports"]["inspect_evidence"]["states"])
# %%
# 3. Classical LP maximizes EENS separately for each offer. The outer search
# exhausts the finite offers, using the same target and fees for all radii.
bench = result["reports"]["benchmark_methods"]
fig, ax = plt.subplots(figsize=(7, 4))
for radius, report in bench.items():
    rows = report["offers"]
    ax.plot(
        [r["firm_mw"] for r in rows],
        [r["worst_eens_mwh"] for r in rows],
        marker="o",
        label=f"TV radius {radius}",
    )
    print(radius, report["selected"])
ax.axhline(20, color="black", linestyle="--", label="Assumed EENS limit")
ax.set(xlabel="Guaranteed reserve (MW)", ylabel="Worst-case window EENS (MWh)")
ax.legend()
fig.tight_layout()
# %%
# 4. Independent analytic check at 60 MW: only the zero-capacity state loses
# energy (160 MWh). Moving .05 probability to it yields (.109+.05)*160=25.44,
# above the 20 MWh target. At 80 MW the same stress gives 12.72 MWh.
print("Analytic stressed 60 MW EENS:", (0.109 + 0.05) * 160)
# %%
# 5. Inspect scenario sensitivity and computational scaling. Timings include
# the LP solve but exclude matrix construction; they are not speedup evidence.
print(result["reports"]["assess_sensitivity"])
# %%
# 6. Nominal procurement buys 60 MW for EUR 6,000; radius .05 buys 80 MW for
# EUR 8,000. The difference is hypothetical expenditure, not observed savings.
# A different worst distribution can apply to each offer; no single forecast
# is being predicted. Support must include plausible failures before fitting.
# Obtain licensed joint-outage evidence and independent review before use.
print(result["reports"]["prepare_handoff"])
plt.show()
