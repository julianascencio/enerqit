# Selection — 22 November 2026

Searched 72 hours first, extended to seven days for a distinct evidence-backed
case. Scores 1–5 are editorial judgments, not forecasts: impact / technical
importance / evidence and data / tractability / repository novelty / optimization.

| Candidate | Publication vs event | Scores | Decision |
|---|---|---|---|
| [NVE week 46](https://www.nve.no/media/20550/2026_46_kraftsituasjonen.pdf) | 18 Nov; 9–15 Nov observations | 4/5/4/5/5/5 | Selected: water timing and retention advance the hydro backlog. National context is primary, plant inputs remain synthetic. |
| [AEMO summer outlook](https://www.aemo.com.au/newsroom/media-release/aemo-prepares-for-summer-as-energy-supplies-forecast-to-remain-sufficient) | 20 Nov; summer 2026–27 forecast | 5/5/4/5/1/5 | PV, storage, wind, grids and flexibility; already addressed in open PR16. |
| [IEEFA construction scorecard](https://ieefa.org/articles/wind-and-battery-projects-catapult-australian-states-towards-2030-renewable-target) | 19 Nov; Q3 commitments | 4/4/3/3/2/4 | Wind, batteries, industrial PPAs; not operating generation. Contract data needed; overlaps PR15. |
| [Data-center peak charging](https://www.reuters.com/legal/litigation/us-data-centers-slash-electric-bills-with-brief-demand-cuts-raising-questions-2026-11-17/) | 17 Nov; tariff practices and prior filings | 5/4/2/3/4/5 | Electricity markets and industrial/data-center demand; defer until primary tariffs and interval billing rules verified. No legal conclusion made. |

NVE reports changing hydro production, low inflows and falling reservoir levels.
Its PDF notes missing Danish observations and substituted forecasts in some
aggregates; none is used numerically here. No national statistics are translated
into a hypothetical plant's capacity or inflow. Source body not redistributed;
no raw response hash claimed. Standard hydraulic conversion and water balance,
with [PyPSA hydro context](https://docs.pypsa.org/latest/examples/chained-hydro-reservoirs/),
not a new scientific algorithm. Author-generated fixture is MIT-licensed.

Main inspected: f8ab496eb9c53c048d541b95ef5b9c7685df97a2.
Agent executed: f8150df9a4272bf2b97042a61b3b785a92450057; role/13 skills and
registered-study safeguards inspected. EDI generation contracts inspected at
e72d9d822b442f6392c80ce12dfc62f738f51ddd. No connector reused: MW generation cannot
identify inflows, head or outlet permissions. Open PR14/15/16 were left untouched.
Main's shared-export model has initial AC energy budgets; this adds explicit
water, inflows, downstream release and terminal volume constraints.

Backlog: plant inflow and stage-volume calibration, variable head, finite outlet
capacity, cascades and travel time, stochastic inflows and terminal water values.
These require licensed plant observations and hydraulic/commercial review.
