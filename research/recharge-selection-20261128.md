# Incremental selection — 28 November 2026

Checkpoint: PR18 and PR19 now merged; current main
054a128d81f88b6a7893cdd5e6cab05d33c4bc47. No open PR at selection. Prior contracts,
architecture, solvers, contribution rules and evidence reused where unchanged.
Agent main 142e941b879f746a3187fadb040640e1cd5f5726 has no changes to quantum_ml,
its 13-skill contract or documentation relative to the previously inspected
9a8a56b commit. Install and actual trace use the new commit. EDI main remains
0f3c90cbb13b8ecc72f5d6c6b44beb319a7d4aaf: generation contracts unchanged, no
connector reused. Generation observations cannot establish permission to recharge.

Fresh search covers PV, wind, storage, hydro, grid margins, flexibility, electricity
markets, industrial and data-center demand. Four candidates compared below.
Scores 1–5: impact / technical / evidence / tractability / repository novelty /
optimization relevance; editorial prioritization, not estimated monetary impact.

| Candidate | Dates and evidence | Scores | Decision |
|---|---|---|---|
| [NESO status](https://www.neso.energy/document/390771/download) | Published 27 Nov; status that day and forecasts. Primary source. | 5/5/5/5/4/5 | Selected context for recovery between services; no outage or activation quantities inferred. |
| [Scatec solar construction](https://www.scatec.com/en/investors/press-releases/) | Primary index: 26 Nov construction start, 126 MW South Africa | 4/3/4/2/2/3 | No operational series or dispatch constraints; existing procurement overlap. |
| [NVE water retention](https://www.nve.no/media/20570/2026_47_kraftsituasjonen.pdf) | 25 Nov publication; week 47 observations; evidence reused from prior review | 4/5/5/4/1/5 | Water-value work just merged; avoid duplication. |
| [Data-center flexibility coverage](https://www.datacenterfrontier.com/energy/article/55421530/5-things-you-didnt-know-about-baaja-and-data-centers) | 25 Nov secondary legal coverage; original event date not verified; prior review reused | 5/4/2/2/3/4 | No legal compliance or calibrated economic assumptions adopted. |

[Official notice explanation](https://www.neso.energy/electricity-explained/how-do-we-balance-grid/what-are-system-notices)
was refreshed: margin notices request more cushion, not a forecast of power cuts.
Secondary 27 Nov multi-window notice coverage motivated the question, but all
model services and prices are authored synthetic examples. No news parameters
calibrate the battery; no provider dataset or article is redistributed.

Decision: a battery operator must purchase recharge in permitted idle intervals
so mandatory later service and terminal inventory can be met. KPI is exact AC
tracking and DC feasibility; objective is recharge purchase EUR. Classical sparse
LP versus restricted early-only recharge and no-recharge replay. Reuse existing
activation replay for independent physics. No QUBO, heuristic or quantum method
is justified for this continuous linear formulation.

Remaining gaps: verified operator service obligations, import rights and network
limits, standby/degradation losses, stochastic forecast vintages and field trial.
No state reset, invented achieved revenue or automatic equipment dispatch.
