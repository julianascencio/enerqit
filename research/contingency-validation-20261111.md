# Preventive security validation, 11 November 2026 (UTC)

Base: 2aeaee888d1039e178992946c5bf9093bd467def. Actual installed agent Git revision:
700d9b84c62f191e3328a39c6b08e06714c8a8d3, pinned in requirements/agent-study.txt.
Existing registered-study runner reused; no energy-agents changes needed.

Local Python 3.12: ruff passed; full pytest 99 passed, 90% overall coverage;
all 11 examples executed; warnings-as-errors Sphinx/gallery build passed;
wheel and sdist built. No repository type checker is configured. The environment
emitted one anyio/pytest deprecation warning; no test failures. No numerical
runtime dependencies added; the separate agent Git pin was refreshed.

Independent reference: direct-edge outage leaves a 40 MW series cut. Scalar
exhaustive enumeration proves 40 MW renewable transfer is optimal, requiring
110 MW firm supply, EUR 11,000 for the synthetic hour. LP reference gap zero.
Base optimum has 80 MW worst overload; 70% margin dispatch has 44 MW. Security
premium EUR 8,000 is not expected loss, annual benefit or realized revenue.

Tests cover ablations, parallel edges, orientation, hours, island rejection,
infeasible supply and malformed outage sets. Ring size scenarios (5/10/20 buses)
all matched the independent EUR 11,000 cut reference; runtimes and matrix sizes
are in the results JSON. Deterministic LP has no random seed. Fixture and raw
source response hashes, data boundaries and versions are recorded. The first
gallery comparison figure was visually inspected; both figures executed.

AI-generated code/documentation with automated physical checks. Human review,
licensed topology calibration, AC voltage/stability and corrective-response
validation remain outstanding. No operational N-1 certification is implied.
GitHub CI must be verified separately on the exact published head; this document
records local checks, not merge or deployed documentation.
