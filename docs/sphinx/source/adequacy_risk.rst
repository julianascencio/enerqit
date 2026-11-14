Small-fleet adequacy and common outages
=======================================

Decision and evidence
---------------------

A planner selects the cheapest guaranteed-capacity offer that meets a specified
expected-unserved-energy target in a constant-demand four-hour window. The screen
asks whether ignoring correlated outages changes that choice. It is separate
from deterministic network contingencies and chronological storage sizing.

`ENTSO-E's Winter Outlook announcement (13 November 2026)
<https://www.entsoe.eu/news/2026/11/13/entso-e-winter-outlook-2026-2027-europe-is-prepared-some-risks-remain-in-specific-areas/>`_
reports generally favourable adequacy alongside local risks. This is an assessment
of the coming winter, not an observed outage. The study does not reproduce its
regional results. The `adequacy methodology
<https://www.entsoe.eu/outlooks/adequacy-methodology/>`_ supplies context for
probabilistic adequacy indicators.

The 72-hour research compared this primary TSO report with Ember's renewable
firming analysis (13 November, already addressed by merged storage work) and
12 November Faraday battery coverage (secondary, undisclosed contract constraints).
The first spans PV/wind growth, batteries, hydro, thermal outages, grids and
regional supply-demand risk. The last connects storage and data-centre demand.
Candidate impact, evidence, tractability, novelty and method fit are persisted.
Open PR #8's historical storage/solver validation scope was inspected and avoided.

All numeric assumptions here are synthetic and authored under MIT. ENTSO-E news
is context, not calibration. EDI was inspected at commit
``3d6000b9d981bbbf594eeee296a391c03f78c6e7``; its REE cost/BESS screen supplies no
calibrated joint-outage distribution. No connector, private code or dataset is
copied. URLs, retrieval metadata and hashes are recorded without full articles.

Model and reference
--------------------

Each unit i has MW capacity C_i and a conditional outage probability p_i given
that no common event occurs. With probability q the common event disables all
listed units. Otherwise outages are independent. Thus marginal unit outage is
q + (1-q)p_i. The independence comparator uses these matched marginals.

For state s with probability w_s and available capacity A_s, guaranteed reserve
F, demand D and duration h:

.. math::

   EENS=h\sum_s w_s\max(D-F-A_s,0),\qquad
   LOLE=h\sum_s w_s\mathbf{1}(A_s+F<D).

EENS is MWh, LOLE is hours, and LOLP is dimensionless. These describe only the
specified window, not an annual metric or a predicted outage. Probability mass
must sum to one; it is never silently normalized. The demand and state are
constant throughout the window. No repair or transition process is inferred.

Two 60 MW units with p=0.1, q=0.1 give capacities 120/60/0 MW with probabilities
0.729/0.162/0.109. At 100 MW demand over four hours the independent hand calculation
is 4*(0.162*40+0.109*100)=69.52 MWh EENS and 4*0.271=1.084 hours LOLE. Exact
state enumeration matches these references and binomial references for larger
independent fleets. No stochastic approximation or quantum method is needed.

.. list-table:: Synthetic benchmark
   :header-rows: 1

   * - Model
     - Shortfall estimate / EENS (MWh)
     - LOLE (hours)
   * - Nameplate screen
     - 0
     - Not a probabilistic metric
   * - Mean-capacity screen
     - 11.2
     - Not a probabilistic metric
   * - Matched-marginal independence
     - 63.688
     - 1.3756
   * - Common-outage model
     - 69.52
     - 1.084

Both probability models have mean available capacity 97.2 MW. Dependence changes
the distribution, not that mean. Fewer but more severe shortages can increase
EENS while reducing LOLE; the two indicators must not be conflated.

Procurement screen and uncertainty
----------------------------------

Offers are guaranteed 0/20/40/60/80/100 MW at an assumed fixed window fee of
100 EUR/MW. The assumed target is EENS <= 20 MWh, not an official standard.
Independence selects 40 MW at 4,000 EUR, but that offer yields 26.16 MWh under the
common-outage model and misses the target. The latter selects 60 MW at 6,000 EUR,
yielding 17.44 MWh. Exhaustive evaluation proves optimality only over the supplied
offers. It does not optimize a real capacity market or monetize outage damage.
The 2,000 EUR premium is hypothetical expenditure, not savings or realized revenue.

Guaranteed reserves sit outside the outage model. If they share a failure mode,
the screen is optimistic and requires a richer joint state model. Sensitivity
varies q=0/0.05/0.1/0.2 and demand=80/100/120 MW. These are uncalibrated scenarios,
not confidence bounds. Scaling records runtime and state count for 2/8/12/16
units. Enumeration is exponential and capped at 16 units (up to 65,537 states
including the common event). Single timings are not speedup claims. State
probabilities are computed in double precision; exact means exhaustive, not
symbolic arithmetic or certainty about input probabilities.

Execution and reproducibility
------------------------------

The generic Quantum ML Engineer at commit
``f465e6afb43a52f41b151c199144b53c3bbf441f`` runs its existing four registered tools.
The role and 13-skill safeguards remain unchanged. Its offline scripted planner
is an actual execution path, not a live LLM or a professional qualification.
Numerical implementation stays in ``enerqit.adequacy``. Classical enumeration and
finite search are used; SA, simulated bifurcation, circuits and hardware are unused.

.. code-block:: bash

   python -m pip install -e '.[dev,docs]' -r requirements/agent-study.txt
   python -m enerqit.adequacy_study
   python docs/examples/plot_adequacy_risk.py

The :doc:`gallery </gallery/plot_adequacy_risk>` includes data interpretation,
actual trace, benchmark, figures, sensitivity and next actions. Packaged fixture
SHA256, installed agent revision, package versions and full results are saved.
No random seed is used because no random sampling occurs. Synthetic elapsed
hours imply no measurement timestamp; future observed data must align in UTC.

Next: licensed unit availability and joint failures, chronological weather/load,
import limits, hydro constraints and storage energy. This method omits these,
network constraints and reserve activation failures. Do not annualize its risk
metrics. Human adequacy review and field validation remain outstanding;
implementation and documentation are AI-generated with automated scientific tests.
