Adaptive solver evidence and lineage
=====================================

This addition considers **Genesis AiX, Hybrid Quantum-Classical Intelligence
Architecture: An Evidence-Driven Middleware and Adaptive Reliability Framework
for Quantum Computing**, research white paper v0.3, November 2026, Genesis AiX,
LLC. The user supplied a 27-page PDF on 13 November 2026. It is a conceptual
proposal, not experimental evidence that the proposed architecture improves
quantum reliability. No affiliation or implementation of Genesis products is
implied.

The source PDF has SHA-256
``2f3b9a0f8fef410301cd3764ffa5ef45f534706c9d72a98ec031c05435e01c5a``.
No verified public URL or redistribution license was supplied. The PDF and its
figures are not redistributed. This page paraphrases the relevant concepts and
records an independently written, limited EnerQit implementation.

What fits EnerQit
------------------

The useful connection is an evidence layer around experiments. A result can be
numerically better while its interpretation is unsupported: perhaps the input
changed, the proposed configuration was never applied, or the new run used
more compute. Keeping those facts separate improves inspectability, without
assuming the additional layer improves the solver itself.

.. list-table:: Source-to-implementation map
   :header-rows: 1
   :widths: 25 40 35

   * - Paper sections
     - EnerQit implementation
     - Boundary
   * - 3.5, 5: evidence and fault lineage
     - Immutable recommendation values, observation fingerprints, explicit
       parent links in a local SQLite ``LineageStore``.
     - Solver experiment lineage; no quantum syndrome ingestion or fault causality.
   * - 6.2-6.3, 7.1: currentness and exact authority scope
     - Compare workload, provider, stack, calibration, model, boundary,
       evidence age, validity interval and exact recommendation digest.
     - Pure offline assessment; no authenticated authority, automatic dispatch
       or atomic authorization-to-effect enforcement.
   * - 6.4: effect witness
     - Distinguish no evidence, acknowledgment, full target readback and
       corroboration by a separately declared channel.
     - The adapter supplies provenance; a channel name cannot prove independence.
   * - 9.3, 10.1: negative controls and honest outcomes
     - Hold stale, changed, incomplete, contradictory, revoked or replayed
       recommendations; preserve improvement, regression, no-change and
       inconclusive outcomes.
     - Tests establish the declared Python semantics only.
   * - 3.4, 9.3: timing isolation and architecture value
     - Report offline gate time, solver time and serialized evidence size.
     - No real-time queue, QEC deadline guarantee, hardware validation or
       proof of architecture-level benefit.

Runnable PV experiment
----------------------

.. code-block:: bash

   python -m pip install -e '.[dev,docs]'
   python -m enerqit.lineage_study --output results/adaptation-evidence.json \
       --store results/adaptation-evidence.sqlite
   python docs/examples/plot_adaptation_evidence.py

The :doc:`executable gallery </gallery/plot_adaptation_evidence>` reuses
``coupled_inventory(seed=42)``, a 12-variable synthetic PV template-selection
problem. Exact enumeration supplies a reference optimum. Eight fixed seed
pairs compare classical simulated annealing with 1 and 16 reads, holding 80
sweeps and local polishing fixed. The proposed change is scripted; no LLM,
quantum circuit, quantum hardware or physical energy asset is controlled.

The comparison protocol declares a materiality threshold of ``1e-6`` synthetic
QUBO objective units before running. For two feasible candidates on the same
workload, improvement is baseline energy minus candidate energy. Values above
the threshold are described as improved, below its negative as regressed, and
inside the band as no material change. Missing/invalid metrics, unsupported
comparability or unconfirmed effects are inconclusive. These are descriptive
labels, not statistical significance or causal attribution.

Both QUBO gap and independent signal RMSE are retained. Every seed is recorded;
there is no cherry-picking of successful adaptations. Increasing the read count
changes compute and random-number consumption. Matching seed numbers does not
make trajectories identical. Results cannot establish speedup, quantum
advantage, generalization or the value of cross-execution learning. Infeasible
candidates are retained and excluded from affirmative outcome comparisons.

The local solver metadata reports the settings it used. This is a declared W2
readback from the applying component, not independent telemetry. A separate
acknowledgment-only control remains W1 and unverified. Partial settings,
different targets/requests or contradictory channels cannot establish success.
Request-bound, post-effect measurement provenance is the adapter's obligation;
the library requires a declared observation time at or after the request but
does not independently authenticate or timestamp that channel.

Storage and timing domains
--------------------------

The CLI writes finite JSON and a local SQLite research store with one run record,
eight observation records and eight linked adaptation records. A new invocation
gets a new run ID, preserving previous runs. Identical record retries are
idempotent; changing an existing record ID or linking to a missing parent fails.
Content fingerprints detect accidental edits unless an editor also recomputes
the fingerprints. They are neither signatures nor a tamper-proof audit log.

This module uses the same lightweight SQLite approach as ``StudyStore`` but
keeps solver episodes separate from its asset time-series schema. It introduces
no database service or dependency. Existing result objects are retained inside
the evidence records.

Historical persistence happens after the local experiment. That placement does
not demonstrate mechanically isolated real-time operation. A future provider
adapter would need bounded telemetry queues, overload/loss accounting, clock
uncertainty, dispatch-time revalidation and provider-specific effect witnesses.
Those are intentionally deferred. The replay check uses a caller-supplied set
and does not reserve an ID or prevent concurrent dispatch.

Research decisions still open
-----------------------------

Before claiming historical-learning value, compare a no-history baseline,
advisory history and governed adaptation under matched resources on held-out
instances. Predeclare acceptable quality, latency and storage thresholds, plus
stopping criteria. Preserve failures and inconclusive trials. Actual QEC or
calibration work additionally needs a noise model, provider-supported interfaces
and measured real-time isolation. This example does not establish paper
hypotheses H1, H2 or H6; it exercises bounded semantic controls related to H3-H5.

CUDA-Q's `official documentation <https://developer.nvidia.com/cuda-q>`_ describes
an existing CPU/GPU/QPU programming platform. IBM's `dynamic-circuit guide
<https://quantum.cloud.ibm.com/docs/en/guides/classical-feedforward-and-control-flow>`_
describes mid-circuit measurement and classical feed-forward. These provide
context for the paper's novelty boundary; neither is integrated by this change.

See ``enerqit.lineage`` and ``enerqit.lineage_study`` in the :doc:`API <api>`.
