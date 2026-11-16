Energy-limited reserve adequacy
===============================

A planner chooses one battery availability offer meeting a scenario-weighted
unserved-energy limit over four sequential hours. The 13 November 2026
`ENTSO-E winter outlook
<https://www.entsoe.eu/news/2026/11/13/entso-e-winter-outlook-2026-2027-europe-is-prepared-some-risks-remain-in-specific-areas/>`_
is context for advancing the storage-energy gap documented on 14 November.
This is a two-day-old backlog item, not a new observed outage. Candidate evidence
and deferrals are persisted in the fixture and research ledger. No connector or
external dataset is reused; all numeric inputs are authored synthetic MIT data.

Physics and optimality
----------------------

Existing BatteryOffer and deliverable_capacity determine usable AC energy from
DC capacity, health, initial/minimum SOC, reserved energy and discharge efficiency.
At each consecutive interval with deficit D, duration h, remaining AC energy E
and power/export limit P, dispatch is min(D,P,E/h); subtract dispatch*h once.
No recharge or resetting SOC is allowed. Each mutually exclusive scenario starts
from the specified initial SOC. Expected unserved MWh weights whole trajectories,
not independently sampled hours. UTC dates identify sources, while fixture times
are synthetic elapsed hours with no claimed observation timestamp.

For one battery, constant efficiency, no recharge and equal value per MWh,
maximum delivered energy is min(initial usable AC energy, sum(min(D,P)*h)).
Greedy replay attains this bound without future information. Independent LP tests
also verify it. This does not prove optimal shortage hours, time-varying costs,
fleet allocation or charge/discharge scheduling. Existing chronological firming
models address different recharge/cyclic-boundary problems; they are not copied.

Decision and limits
-------------------

Two equally probable paths need 50 MW for two or four hours. Both offers have
50 MW power; the short offer has 100 MWh DC and GBP 1,000 fixed fee; the long
has 200 MWh and GBP 1,800. At ideal efficiency and full SOC, the short offer's
EENS is 50 MWh; the long offer's is zero. A power-only screen reports zero for
both and selects the cheaper offer incorrectly against an assumed 20 MWh limit.
The energy-aware screen buys the long offer. GBP 800 is hypothetical additional
expenditure, not savings. No quantum approach is needed for this O(T) calculation.

Sensitivity tests start SOC .5/.75/1; scaling covers 4/24/168/8760 intervals.
Exact means a closed-form bound for the restricted physical model, not certainty
about scenario probabilities. No LOLE or annual/regional forecast is reported.
Real failure correlations, initial SOC telemetry, recharge opportunities,
contracts, network constraints and independent human review remain necessary.

Reproduce
---------

.. code-block:: bash

   python -m pip install -e '.[dev,docs]' -r requirements/agent-study.txt
   python -m enerqit.reserve_study
   python docs/examples/plot_reserve_depletion.py

The :doc:`gallery </gallery/plot_reserve_depletion>` executes the current generic
engineer with evidence, benchmark, sensitivity and handoff tools. Actual agent
installation, input hash, package versions and results are recorded. The planner
is scripted, not a live LLM. No random seed is required for deterministic replay;
independent LP comparison tests use fixed seeds 0 through 4. AI-generated code
and documentation have automated scientific checks, not independent human review.
