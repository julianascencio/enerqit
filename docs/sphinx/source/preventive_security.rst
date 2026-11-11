Preventive line-outage security
===============================

Problem and dated evidence
--------------------------

A system planner needs one dispatch that remains feasible without corrective
redispatch after any specified single-line outage. The objective is minimum firm
energy cost for one constant hour; the engineering KPI is worst post-outage MW
overload, with all demand served. This extends the merged base-network study,
not its results or claim of real-world validity.

`Ember's interconnection report, published 10 November 2026
<https://ember-energy.org/latest-insights/turkiye-generated-500-million-in-exports-through-interconnections-in-20-months/>`_
motivates secure usable transfer. Its reported trade period is January 2025 to
August 2026, not a new outage on publication day. The modeled network is synthetic
and does not represent Türkiye, HVDC interconnectors, or market access rights.
Candidate comparison against Japan electrification and the 5 November grid guide
is preserved in ``enerqit/data/contingency_20261111.json`` and the research ledger.

The 72-hour search covered renewables, storage, hydro and grids; primary report
links also covered electrification and data-centre flexibility. Search results
with old publication dates were not treated as new evidence. The selected case
adds the previously documented security backlog capability to a current trigger.
Energy Data Insights inspection found an aggregate REE cost screen, not the
licensed topology required here; its exact revision and file hash are recorded.

Methods and physical accounting
--------------------------------

For every selected connected topology s, form its incidence A_s, flow-angle H_s
and nodal Laplacian L_s. Fix bus zero's angle and solve the reduced system to
construct T_s mapping balanced nodal injections to line flows. The LP uses common
renewable r and firm g vectors in every state:

.. math::

   \min h c^T g,\qquad \mathbf{1}^T(r+g-d)=0,
   \qquad -\bar f_s \le T_s(r+g-d)\le\bar f_s.

Generation bounds are inherited from ``DispatchCase``. A base state is always
included. Cost is charged once, not summed over mutually exclusive outages.
Ratings remain unchanged after outages; no emergency-rating uplift is assumed.
``audit_outages`` separately re-solves each reduced nodal system from the chosen
injections, checking physical balance, generation bounds and every surviving line.

This explicit-topology implementation is a classical LP, with conceptual context
from `PyPSA security-constrained power flow
<https://docs.pypsa.org/latest/user-guide/optimization/contingencies/>`_. It does
not implement PyPSA's BODF formulation or claim cross-package validation. No QUBO,
simulated annealing, simulated bifurcation, hybrid training or QPU is needed.

Results and independent reference
----------------------------------

The reused MIT synthetic fixture has 150 MW renewable availability at bus 0,
150 MW demand at bus 2 and local firm supply at 100 EUR/MWh. Three equal-reactance
lines have ratings 40/100/100 MW. A direct-line outage leaves a series path capped
at 40 MW. A transfer of 40 MW passes all three single outages, so 110 MW firm
supply and 11,000 EUR cost is both a lower bound and attainable optimum.

.. list-table:: Actual synthetic one-hour results
   :header-rows: 1

   * - Policy
     - Cost (EUR)
     - Worst outage overload (MW)
   * - Base-case DC optimum
     - 3,000
     - 80
   * - Dispatch with all ratings reduced to 70%
     - 6,600
     - 44
   * - Preventive LP
     - 11,000
     - 0

The preventive LP has zero gap to the independent series-path reference.
Its 8,000 EUR premium is the cost of this fixed-dispatch security requirement,
not expected outage loss or realized savings. Outage-set ablations distinguish
base-only, each individual outage and all three. The 70% rule is tested as a
heuristic, not presented as a standard or universally adequate reserve margin.

Rating sensitivity 30/40/50/80 MW yields costs 12,000/11,000/10,000/7,000 EUR.
Firm cost sensitivity 50/100/200 EUR/MWh yields 5,500/11,000/22,000 EUR. These are
engineered scenario ranges, without inferred probabilities. Ring networks of
5/10/20 buses test resource scaling: every single outage leaves a radial path
whose 40 MW cut independently implies 11,000 EUR cost. Construction and solver
time, matrix bytes and constraint counts are exported. Single timings do not
establish statistical speedup or transmission-scale suitability.

Contract, agent and reproduction
--------------------------------

Inputs use MW, MW/radian, EUR/MWh and hours. One constant interval has no measured
timestamp; observations for future calibration must use UTC. All synthetic
numerical values remain separate from source metadata. Input/evidence hashes,
package versions and deterministic execution (no random seed required) accompany
the results. Full source articles are not bundled.

``outages=None`` selects every line; ``[]`` explicitly selects only base topology.
Duplicate, negative, boolean and out-of-range outage IDs are rejected. An outage
that disconnects the network raises an error; it is never silently removed from
the security claim. Parallel lines remain individually identifiable by input
position. An infeasible LP returns no fabricated dispatch. Dense computation is
limited to 50 outage states plus base and the existing 100-bus/300-line bounds.

The actual ``career_quantum_ml_engineer`` runs four registered EnerQit callbacks
at energy-agents commit ``700d9b84c62f191e3328a39c6b08e06714c8a8d3``. The current
13-skill role contract and safeguards are reused without a new integration PR.
Its scripted offline planner demonstrates execution, not live LLM reasoning.

.. code-block:: bash

   python -m pip install -e '.[dev,docs]' -r requirements/agent-study.txt
   python -m enerqit.contingency_study
   python docs/examples/plot_preventive_security.py

The :doc:`gallery </gallery/plot_preventive_security>` gives step-by-step inputs,
actual trace, baselines, figures, sensitivity and handoff. Results are in
``benchmarks/results/contingency-engineer-20261111.json``. Validation includes an
independent scalar enumeration/cut reference, outage ablations, parallel edges,
orientation, hours, input rejection and explicit island handling.

Limits and next action
----------------------

This models preventive DC line-outage security for the enumerated states only.
It excludes generator outages, islands, corrective redispatch, ramp limits,
voltage, reactive power, losses, stability and probabilistic reliability. The
linear model cannot certify operational N-1 compliance. Obtain licensed network
and contingency data, compare measured flows, then validate AC and corrective
response before considering operational use. Human review remains necessary;
implementation and documentation are AI-generated with automated scientific tests.
