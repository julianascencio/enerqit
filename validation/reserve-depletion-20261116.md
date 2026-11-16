# Energy-limited reserve validation — 16 November 2026

Base main: 2c7f9c1fcf9432f11c6321e3d726b4febb10c58e.
Actual pinned agent: c8a61091683856c890a5059d0ff6e3d4bd94a445.

Local checks: 234 tests passed, 87% coverage; all 18 gallery examples passed;
Ruff, diff check, wheel/sdist and Sphinx warnings-as-errors passed. Two title
underlines were corrected before the successful documentation build. One external
pytest-plugin deprecation warning remains. No configured type-check command.
Figure inspected. The benchmark records actual agent installation, source/input
hashes (or explicit retrieval failure), versions, four tool stages and scaling.

Independent evidence: analytic maximum-energy bound, five seeded native LP
comparisons, variable interval durations, export limit, unavailability, zero load,
invalid input/probability mass, infeasible procurement and actual agent execution.
No stochastic optimizer, circuit or quantum hardware is used.

Synthetic two-path benchmark: short 50 MW / 100 MWh offer has EENS 50 MWh and
GBP 1,000 fee; long 50 MW / 200 MWh has EENS zero and GBP 1,800 fee. Power-only
baseline predicts zero for both, so its cheaper choice fails the 20 MWh target
under the physical model. GBP 800 is extra hypothetical expenditure, not savings.

Initial SOC .5/.75/1 sensitivity and 4/24/168/8760-interval scaling are recorded.
This advances a two-day-old documented gap; news is context, not calibration.
All numerical fixtures are authored synthetic MIT inputs. No external connector
or dataset is reused. AI-generated code and documentation; human scientific
review and real SOC/outage/contract validation remain pending. No annual risk,
network adequacy or field-performance claim. Remote CI/merge/deployment status
must be read from the PR, not inferred from this local validation record.
