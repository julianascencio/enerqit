# Renewable firming validation — 13 November 2026, UTC

Base EnerQit: 581d84ec721ac80a5905c5e3fac55c5c18f39bfe.
Actual installed energy-agents: e077b5f240852c7fe28c4de2ed530a52f65e8347.
Existing four-stage registered-study adapter and generic role used unchanged.

Local checks completed on Python 3.12:
- Ruff passed.
- Full pytest: 118 passed, 90% coverage; one installed anyio/pytest deprecation warning.
- All 12 examples executed successfully.
- Sphinx with -W --keep-going passed, executing the gallery.
- Wheel and sdist built successfully.
- Storage/SOC figure visually inspected; both figures generated.
- No repository type-check command is configured. No numerical dependencies added;
  the separate agent requirements Git pin was refreshed to current main.

Independent consecutive-deficit bounds and attainability checks prove capacity
2/0.9 MWh (solar/coincident) and 0.5/0.9 MWh (complementary). MILP matches both;
LP capacity lower bounds match, but any relaxed schedule remains independently
audited rather than assumed physically feasible. Rotation tests prevent an
artificial horizon-edge advantage. Input, mode, energy, power, shortage and
cyclic-boundary checks pass. The 50% joint lull is infeasible, as required.

The saved result contains full trace, actual installed agent source, input/evidence
fixture hash, package versions, dispatch arrays, residuals and sensitivities.
Repeated 4/24/96-interval problems retain the same 0.555556 MWh capacity; reported
single-run construction/solver time and dense matrix bytes are not speedup claims.
No randomness is used. These profiles are synthetic, not calibrated observations.

Primary article date (13 November) differs from listing date (12 November);
both recorded. Indexed primary article text was read; direct HTTP returned 403,
so raw response SHA256 is explicitly null. No full article is redistributed.
EDI capability file and exact repository/blob revisions are recorded; no licensed
code or dataset was copied. The assumed EUR 200,000 per usable MWh is only a
battery energy-component sensitivity, not a quote or total-project economics.

AI-generated implementation and documents with automated scientific checks;
human review and multi-year physical/economic validation remain outstanding.
GitHub checks must additionally pass on the exact published head before readiness.
