Continuous-ramp energy audit
============================

The :doc:`worked example </gallery/plot_continuous_ramp_energy>` extends the
ramp-deliverability backlog with exact energy reconciliation, without changing
``plan_ramping`` or its documented discrete-setpoint semantics.

``enerqit.ramp_energy.audit_linear_ramps`` accepts n+1 instantaneous nonnegative
power boundaries and n positive elapsed UTC hour durations. Both generation and
demand interpolate linearly. Integrating generation and demand uses trapezoids;
shortage integrates the positive part of demand minus generation, splitting at
zero crossings. Spill follows the energy balance. Capacity and slope violations
are returned separately; infeasible trajectories are never silently repaired.

The `26 November NESO report <https://www.neso.energy/document/390646/download>`_
is context, not calibration. All scenario numbers are authored synthetic MIT
inputs. Forecast chart values are not observations. No provider dataset is
redistributed; the raw-response hash is explicitly unavailable. Input SHA256,
agent trace, environment, scenario sensitivity and runtime are recorded.

A one-hour 0-to-40 MW ramp against 40 MW demand supplies 20 MWh and leaves 20 MWh
shortage. Held output at its final endpoint instead accounts for 40 MWh and no
shortage. Both calculations follow their respective conventions. At assumed
EUR50/MWh generation and EUR1000/MWh shortage, objectives are EUR21000 and EUR2000.
This is a risk-screening difference, not realized loss or an optimized continuous
schedule. No quantum method is needed for exact O(n) integration.

The existing engineer at commit 9a8a56b3be12e734183a0350600bf874bdee8ff0 executes
four registered callbacks. Source evidence and all bounded numerical tools remain
separate; successful execution is not independent scientific review.

Reproduce with ``python -m enerqit.ramp_energy_study`` after installing the project
and ``requirements/agent-study.txt``. See the gallery for plotting commands.

Limits: linear interpolation, constant costs, no startups, network constraints or
forecast uncertainty model. Interval-average telemetry cannot identify ramps.
Next: verify trajectory assumptions on approved instantaneous measurements, then
review any proposed continuous optimization model independently. AI-authored;
human review and real-asset validation remain outstanding.
