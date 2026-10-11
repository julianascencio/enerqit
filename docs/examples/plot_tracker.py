"""
Tracker settings and their excitation
=====================================

Known axis geometry and backtracking are assumed. Dawn and dusk distinguish
GCR/rotation settings. The classical global fit is compared with an exact
candidate scan and bSB on a discretized version of the same physical task.
"""

import matplotlib.pyplot as plt
import numpy as np

from enerqit.datasets import weather
from enerqit.inference import candidate_problem, fit_tracker
from enerqit.pvsystem import tracker_ac
from enerqit.solvers import group_exact, simulated_bifurcation

frame = weather(days=2)
frame["power_ac"] = tracker_ac(frame, 35, -5, max_angle=52, gcr=0.38)
result = fit_tracker(frame, 35, -5, seed=2, maxiter=60)
print(result.to_json())
settings = [(gcr, angle) for gcr in (0.28, 0.38, 0.48) for angle in (45, 52, 60)]
predicted = np.column_stack([tracker_ac(frame, 35, -5, gcr=g, max_angle=a) for g, a in settings])
problem = candidate_problem(predicted, frame.power_ac)
for solution in (group_exact(problem), simulated_bifurcation(problem, seed=3)):
    print(solution.method, "feasible:", solution.feasible, "energy:", solution.energy)
    if solution.feasible:
        print(settings[np.argmax(solution.x)])
fig, ax = plt.subplots(figsize=(8, 3.5))
for angle in (40, 52, 70):
    ac = tracker_ac(frame, 35, -5, max_angle=angle, gcr=0.38)
    ax.plot(frame.index[:96], ac[:96] / 1000, label=f"Limit {angle}°")
ax.set(ylabel="AC power (kW)", title="Tracker rotation-limit sensitivity")
ax.legend()
fig.autofmt_xdate()
fig.tight_layout()
