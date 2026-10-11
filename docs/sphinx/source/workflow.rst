Business workflow and daily evidence
====================================

The initial product hypothesis is a specialist inverse-engineering study with
a quantum-optimization R&D component: reconstruct a defensible configuration
or field response model, report ambiguity, and identify the next useful test.
Potential buyers include independent engineers, asset owners with incomplete
records, inverter/module teams, and parties assessing a retrofit. These are
buyer hypotheses to validate, not established market demand.

Sell a defined engineering decision and evidence package: configuration audit,
equipment characterization, or paid algorithm benchmark. Deliver fitted
parameters/curves, data-domain limits, uncertainty, model assumptions and a
reproducible notebook. Recurring value can be a time-limited study retainer
while seasonal evidence accrues, or an SDK license after validation. Pricing
requires actual willingness-to-pay discovery; no invented revenue projection
is built into the code.

Daily sequence
--------------

1. Receive the latest 24-hour export for the commissioned assets. Check units,
   timestamps, stable channel schema and client permission to use the evidence.
2. Canonicalize and ingest idempotently. Keep raw batch history; record late
   corrections. Accumulated coverage, not simply row count, determines value.
3. Review operating regimes. Exclude non-MPPT points for IV work; distinguish
   actual power from available power for curve studies.
4. Update a separately versioned evidence fit only when new conditions add
   information. Freeze the reference instead of allowing daily adaptation to
   absorb genuine equipment changes or modeling errors.
5. Validate on held-out days and compare candidate ambiguity. Rerun a coupled
   quantum-inspired study when the defined hypothesis set meaningfully changes.
6. Issue a scheduled study milestone or recommend an informative measurement
   (for example an IV sweep or calibrated irradiance check). Expert review
   remains part of the service; no field control command is emitted.

StudyStore implements ingestion and immutable result versions, not automatic
regime labeling, data governance, billing, authentication or scheduling. A new
day may add almost no information about an unvisited temperature/load domain.

Application scope
-----------------

The initial implementation focuses on explicitly scoped inverse-engineering
studies and equipment characterization using authorized data exports. Domain
extensions should preserve physical assumptions, reproducibility, validation
and honest comparisons. See the repository roadmap for planned energy domains.

Suggested first engagement: one known plant with trusted metadata, a blinded
geometry/topology recovery exercise, and one converter efficiency or thermal
characterization study. Establish data sufficiency and customer usefulness
before a multi-asset product rollout. The current package is a starting SDK
for such work, not a replacement operational analytics platform.
