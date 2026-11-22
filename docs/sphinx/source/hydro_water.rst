Reservoir water allocation
================================

The :doc:`offline gallery </gallery/plot_reservoir_water_budget>` uses the existing
Quantum ML Engineer to allocate a single reservoir's water. This advances the
hydro backlog beyond the initial AC energy budget in shared-export screening.

NVE's `week 46 report <https://www.nve.no/media/20550/2026_46_kraftsituasjonen.pdf>`_
was published 18 November 2026, covering 9-15 November. It is context, not plant
calibration. All model inputs are synthetic and MIT-licensed. The four-day-old
source was selected within an extended seven-day search on 22 November.

For interval inflow volume I, turbine volume q, bypass b and reservoir S:

.. math::

   S_{t+1}=S_t+I_t-q_t-b_t,\qquad
   E_t=q_t\rho g H\eta/(3.6\times10^9).

Flows in m3/s are multiplied by 3600 times elapsed hours. E is AC MWh; volume is
usable cubic metres above dead storage. Maximize sum(price times E), preserving
reservoir bounds, turbine rating, a minimum combined release and terminal floor.
`PyPSA's hydro example <https://docs.pypsa.org/latest/examples/chained-hydro-reservoirs/>`_
supplies standard reservoir modelling context, not reused code or validation.

The sparse classical LP reports an independent water/objective audit and explicit
infeasibility. Tests compare tiny integer network-flow instances with exhaustive
physical turbine/bypass enumeration. No quantum-inspired method or circuit is
needed for this continuous linear model. Timings include construction and solve;
the API limits inputs to 8760 intervals, with linear sparse matrix size.

Synthetic benchmark: a 100000 m3 reservoir retains 20000 m3 after three hours.
Reallocating 20000 m3 from EUR20/MWh to EUR100/MWh raises gross scenario value
from EUR833.85 to EUR1226.25. Generation remains 19.62 MWh. The EUR392.40 difference
is neither realized revenue nor profit. Costs and future water value are excluded.
Head, release and terminal-floor sensitivities quantify assumption dependence;
a 60000 m3 terminal floor conflicts with the required 60000 m3 releases.

Limitations: constant head and efficiency, known future inputs, unlimited bypass,
no cascade travel, evaporation, ramping, ecology, outlet limits or dispatch rights.
Turbine and bypass count at an assumed common downstream compliance point.
The floor is an engineering scenario, not a legal threshold. Obtain licensed
plant evidence and independent hydraulic/commercial review before field claims.

.. code-block:: bash

   python -m pip install -e '.[dev,docs]' -r requirements/agent-study.txt
   python -m enerqit.hydro_study
   python docs/examples/plot_reservoir_water_budget.py

Agent commit f8150df9a4272bf2b97042a61b3b785a92450057 executes the four callbacks
with its scripted planner. Human review remains required; equipment execution
remains unauthorized. The result contains fixture SHA256, versions and install
provenance. EDI inspected at e72d9d822b442f6392c80ce12dfc62f738f51ddd; no connector
reused. AI-authored, independently checked mathematically but not field validated.
