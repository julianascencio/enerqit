"""
Frozen storage design on a chronological holdout
================================================

This offline gallery uses authored synthetic profiles with varying daily shapes.
The command in the validation-lab guide runs the same workflow on OPSD Germany's
2018/2019 aggregate observations without bundling third-party raw data.

Normalize and size only on training data. Replay the later holdout with fixed
capacity and 50% initial SOC, then stress a declared calendar capacity fade.
The causal replay reports shortfall rather than resizing on the held-out period.
The illustrative cost scenario includes energy/power capital, renewable capital,
other initial costs, opex and discounted replacements. It is not a price quote.
"""

import matplotlib.pyplot as plt

from enerqit.chronological import run_chronological_study
from enerqit.validation_study import illustrative_costs, synthetic_profiles

frame = synthetic_profiles()
result = run_chronological_study(
    frame,
    split_at="2025-01-21T00:00:00Z",
    provenance={"synthetic": True},
    costs=illustrative_costs(),
)
fig, axes = plt.subplots(1, 2, figsize=(11, 4))
axes[0].plot(result["holdout"]["energy_mwh"], label="Beginning of life")
axes[0].plot(result["aged_holdout"]["energy_mwh"], label="10-year calendar fade scenario")
axes[0].set(
    xlabel="Held-out elapsed hours",
    ylabel="Stored DC energy (MWh)",
    title="Fixed design, causal dispatch",
)
axes[0].legend(fontsize=8)
flows = result["economics"]["cashflows"]
axes[1].bar([r["year"] for r in flows], [r["present_eur"] / 1e6 for r in flows])
axes[1].set(
    xlabel="Project year",
    ylabel="Discounted cost (million EUR)",
    title="Illustrative configured cash flows",
)
fig.tight_layout()
assert result["holdout"]["physical_feasible"]
assert result["aged_holdout"]["physical_feasible"]
print(
    {
        "capacity_mwh": result["training"]["capacity_mwh"],
        "held_out_shortfall_mwh": result["holdout"]["unserved_mwh"],
        "aged_shortfall_mwh": result["aged_holdout"]["unserved_mwh"],
        "cost_basis": "authored assumptions, not market prices",
    }
)

plt.show()
