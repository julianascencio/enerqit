Data contract
=============

Input CSV has an ISO-8601 ``timestamp`` with an explicit UTC offset and numeric
columns. Internally timestamps are timezone-aware, unique and ordered. Naive
timestamps, duplicate rows, missing required channels and nonfinite values are
rejected. No unit or timezone is inferred. Resampling, calibration, meter-boundary
alignment and clock correction belong to the study preparation stage.

.. list-table:: Channels
   :header-rows: 1
   :widths: 25 15 60

   * - Channel
     - Unit
     - Meaning
   * - ghi, dni, dhi
     - W/m²
     - Ground horizontal, direct normal and diffuse horizontal irradiance
   * - temp_air, temperature
     - °C
     - Defined air, cell or inverter sensor; do not substitute implicitly
   * - wind_speed
     - m/s
     - Wind speed used by the thermal model
   * - power_ac, power_dc
     - W
     - Actual measured power at a documented boundary
   * - available_ac
     - W
     - Independent unconstrained estimate used only for limiting inference
   * - voltage, current
     - V, A
     - Synchronized module/string/array electrical measurement, scope declared
   * - command_limit
     - W
     - Applicable active-power ceiling; nonbinding must be demonstrated

Start with 1–5 minute data where available, but choose cadence based on dynamics
and telemetry quality; this is not a hard API requirement. Irradiance effective
at the cell and cell temperature are required by electrical inference and differ
from raw GHI and ambient temperature. The caller provides their validated
transformation. Periods of scanning, curtailment, clipping and faults should be
classified before MPP fitting; this package does not auto-label all regimes.

StudyStore accepts one stable numeric schema per asset. One (asset,timestamp)
has one current row. A later batch replaces that whole row; partial-channel
uploads are rejected. Identical canonical batches are no-ops. Original batch
payloads remain in SQLite, and analyses preserve evidence hashes and results.
The store is local, lacks authentication/encryption and is not a production
multi-tenant database. Apply client data governance in the deployment environment.
