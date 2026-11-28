# Candidate selection — 23 November 2026

Searched the previous 72 hours, then seven days. No verified fresh story supplied
better distinct/calibrated numerical work than the documented terminal-water-value
gap. Advance that backlog using five-day-old NVE context; do not relabel it as news.
Scores are editorial 1–5: impact / technical importance / evidence-data /
tractability / novelty in EnerQit / optimization relevance.

| Candidate | Source date and event | Scores | Decision |
|---|---|---|---|
| [NVE water use and expectations](https://www.nve.no/media/20550/2026_46_kraftsituasjonen.pdf) | Published 18 Nov; observations 9–15 Nov | 4/5/4/5/5/5 | Selected backlog: continuation value absent from merged hydro model. National context only; synthetic curve. |
| [EU permitting agreement](https://ec.europa.eu/commission/presscorner/api/files/document/print/en/ip_26_2450/IP_26_2450_EN.pdf) | 18 Nov provisional agreement, formal adoption still pending in release | 5/4/4/2/3/3 | Covers PV, wind, grids, storage; no calibrated project-duration/cost dataset for a numerical contribution. Do not treat as enacted rules. |
| [Spain data-center framework coverage](https://www.pv-magazine.com/2026/11/21/spain-approves-new-data-center-rules-requiring-80-renewable-electricity/) | 21 Nov coverage of stated 20 Nov decision | 5/4/2/3/2/4 | Industrial demand, data centers, grid flexibility, electricity procurement. Secondary source; legal text not verified. Existing matching capability overlaps; no compliance claim. |
| [Wind balancing costs coverage](https://energynewsbeat.co/electrical-generation/who-pays-for-britains-wasted-wind-a-1-billion-treasury-top-up-and-a-bill-that-comes-due-in-2027-2/) | 22 Nov coverage concerning October costs | 4/4/2/3/2/4 | Requires original settlement/cost datasets. Existing network/curtailment studies overlap. Headline figures not adopted. |

Sources are context, not model parameters. No articles or provider datasets are
redistributed. NVE explicitly discusses choosing water use in response to current
versus expected prices; its missing-data caveats are not hidden. Technical context:
[PyPSA water values](https://docs.pypsa.org/latest/examples/water-value/). No PyPSA
code reuse or replication claim; standard concave LP modelling, not a novel algorithm.

Inspected main b8dbbf54bcba6f0f5ab4ae22cbf100853ae6f885, including merged PR14–17,
CONTRIBUTING, roadmap, data contracts, APIs, solvers, tests, docs/gallery and
research records. No open PR at selection. Existing hydro API is extended, not
replaced or duplicated. Agent main 9a8a56b3be12e734183a0350600bf874bdee8ff0:
role, 13 skills, four-stage tools and safeguards inspected; no adapter change
needed. EDI e72d9d822b442f6392c80ce12dfc62f738f51ddd generation contracts do not
provide continuation values; no connector/data reused.

Remaining backlog: derive continuation values from approved pre-decision data;
freeze estimation before untouched future validation; include inflow/price
uncertainty, terminal discounting and hydraulic constraints. Curves in this
contribution are engineered scenarios, not statistical estimates or fair values.
