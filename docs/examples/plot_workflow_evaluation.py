"""
Measure registered-agent workflow overhead and repeatability
============================================================

The direct script and installed energy-agents registered study execute the same
four numerical callbacks. The agent uses its existing deterministic offline
planner; no live LLM or paid service is invoked. Each path runs three times with
the same seed. Human effort remains unmeasured, and runtime overhead is not a
measure of scientific quality or quantum advantage.
"""

import matplotlib.pyplot as plt

from enerqit.workflow_evaluation import compare_firming_workflows

result = compare_firming_workflows()
summary = result["summary"]
fig, ax = plt.subplots(figsize=(7, 4))
ax.bar(list(summary), [r["median_wall_s"] for r in summary.values()])
ax.set(ylabel="Median measured wall seconds", title="Identical numerical work, three repeats")
fig.tight_layout()
assert result["same_outcome_across_workflows"]
print(summary)
print("Human engineering effort: unmeasured. Live LLM: no.")

plt.show()
