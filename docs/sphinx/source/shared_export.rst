Co-located resources behind a shared export connection
======================================================

Decision and evidence
---------------------

A portfolio operator allocates already-stored deliverable AC energy across price
intervals while respecting a common export limit. EnBW's Forbach investment
announcement, reported on 17 November 2026, motivates this mechanism. The
`English primary page
<https://www.enbw.com/press/green-light-for-enbw-battery-storage-facility-in-forbach.html>`_
states 41 MW, whereas the `German page
<https://www.enbw.com/presse/gruenes-licht-fuer-enbw-batteriespeicher-in-forbach.html>`_
states 46 MW; both state approximately 170 MWh. The primary publication date was
not verified. Neither power figure nor a guessed Forbach connection rating is
used. This study is generic and all numerical inputs are synthetic MIT fixtures.

Four candidates were compared and preserved in the news ledger. Winter adequacy
was already covered by main and pending PRs 10/11; solar-hybrid supply news and
data-centre equipment demand lacked sufficient calibration inputs. No external
connector or third-party dataset is reused. No full articles are redistributed.

Model and independent reference
-------------------------------

For resource i and interval t, choose discharge x_it in MW to maximize
sum(price_t * h_t * x_it). Bounds are 0 <= x_it <= power_i,
sum_t(h_t*x_it) <= available_AC_energy_i, and sum_i(x_it) <= connection_t.
Energy is available at the start, with no inflows or recharge. Export at negative
prices is optional. Sparse HiGHS LP uses n*T variables and n+T inequalities;
physical residuals are independently recomputed. Caps are 64 resources and 8760
intervals. Runtime includes solve and audit but not input/matrix construction.

The independent baseline omits the shared limit. Proportional clipping restores
feasibility without rescheduling; unused energy remains unused, not destroyed.
There is no terminal energy credit. Existing single-interval network dispatch
and cyclic renewable firming APIs remain unchanged: neither implements this
finite-energy multi-resource export allocation.

With two 50 MW resources holding 50/100 MWh, six one-hour prices
10/100/90/20/60/30 EUR/MWh and a 50 MW connection, independent requests value
EUR 14,500 but exceed the connection by 50 MW. Clipping yields EUR 9,500.
Coordination attains EUR 12,500: 50 MWh at each of the three highest prices,
an independently attainable upper bound. EUR 3,000 is gross scenario value,
not profit or realized savings. Independent enumeration verifies small integral
instances; variable-duration, zero-energy and negative-price cases are tested.
No quantum method is needed for this continuous linear problem.

Reproducibility and limitations
-------------------------------

.. code-block:: bash

   python -m pip install -e '.[dev,docs]' -r requirements/agent-study.txt
   python -m enerqit.shared_export_study
   python docs/examples/plot_shared_export.py

The :doc:`gallery </gallery/plot_shared_export>` runs the actual engineer's four
registered stages. Input hashes, installed agent revision, environment and
results are recorded. No random seed is needed for deterministic LP. Source
dates use UTC; the synthetic horizon uses elapsed hours, not observed timestamps.
Sensitivity varies connection and AC budgets; scaling uses 6/24/168 intervals.
A different optimal dispatch can occur on ties while objective values agree.

Known future prices make this a perfect-price scenario bound. Missing charging,
losses, reserve obligations, ramps, head-dependent hydro efficiency, terminal
values and market fees prevent trading or investment conclusions. The generic
AC budget is not a reservoir or battery conversion model. Obtain licensed site
constraints, usable budgets and price forecasts before a real study. AI-generated
methods and automated checks do not replace independent scientific review.
