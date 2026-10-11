"""
Recover fixed-array orientation
===============================

Compare a continuous physical fit with discrete candidate selection solved by
direct enumeration and quantum-inspired simulated bifurcation. A direct scan is
the appropriate strong baseline for this single-group problem.
"""

import matplotlib.pyplot as plt
import numpy as np

from enerqit.datasets import fixed_array
from enerqit.inference import candidate_problem, fit_orientation
from enerqit.pvsystem import fixed_ac
from enerqit.solvers import group_exact, simulated_bifurcation

frame, truth = fixed_array(seed=42)
result = fit_orientation(frame, 35, -5)
print(result.to_json())
tilts = np.array([15, 22, 28, 35, 42])
predictions = np.column_stack([fixed_ac(frame, 35, -5, tilt, 172) for tilt in tilts])
problem = candidate_problem(predictions, frame.power_ac)
classical = group_exact(problem)
quantum_inspired = simulated_bifurcation(problem, seed=7)
for solver_result in (classical, quantum_inspired):
    print(solver_result.method, solver_result.to_dict())
    if solver_result.feasible:
        print("Selected tilt:", tilts[np.argmax(solver_result.x)])

fitted = fixed_ac(frame, 35, -5, result.parameters["tilt"], result.parameters["azimuth"])
fig, ax = plt.subplots(figsize=(8, 3.5))
ax.plot(frame.index[:96], frame.power_ac.iloc[:96] / 1000, ".", label="Synthetic measurements")
ax.plot(frame.index[:96], fitted[:96] / 1000, label="Classical physical fit")
ax.set(ylabel="AC power (kW)", title="Orientation recovery: one day of the five-day fit")
ax.legend()
fig.autofmt_xdate()
fig.tight_layout()
