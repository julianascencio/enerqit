Physical inference and limits
=============================

Configuration
-------------

The forward model combines pvlib solar position, isotropic irradiance
transposition, Faiman temperature, PVWatts DC and PVWatts inverter conversion.
Latitude/longitude, capacity, temperature coefficient and measurement scale are
fixed. No shading, bifacial gain, soiling, snow or curtailment is modeled. Such
unmodeled effects can bias recovered geometry. A small residual does not prove
that the geometry is correct. Estimate or constrain nuisance parameters in a
site-specific extension and validate across held-out seasons.

``fit_orientation`` uses bounded nonlinear least squares; ``fit_tracker`` uses
differential evolution over GCR and maximum rotation with fixed axis azimuth
and enabled backtracking. Tracker GCR affects the present model through tracker
angle rather than an explicit row-shading irradiance model. A local Jacobian
rank is a screening diagnostic only. Single-season candidate equivalence can
persist despite a full local rank. Multi-start fitting and profile likelihood
are appropriate extensions for multimodal cases.

Electrical topology
-------------------

For uniform strings at known MPPT conditions, array voltage approximately
scales with modules in series and current with strings in parallel. The module
model must be known. The implementation enumerates positive integer candidates
and ranks normalized voltage/current error. Gain errors, mixed strings,
unavailable strings and mismatch can defeat this inference. Aggregate AC
does not independently determine the number of inverters or modules.

IV reconstruction
-----------------

The single-diode model is

.. math::

   I = I_L - I_0\left[\exp\left(\frac{V+IR_s}{a}\right)-1\right]
       - \frac{V+IR_s}{R_{sh}}.

pvlib translates the reference parameters using De Soto equations. The sweep
fit uses log-transformed positive parameters. The MPP fit matches model MPP
voltage and current across known irradiance and cell temperature, fitting two
parameters by default. Five-parameter operational fitting is possible via
``free``, but can be poorly identified even with abundant points. MPPT points
do not directly trace a complete IV curve. All off-MPP reconstruction is
conditional on physics and fixed parameters. The implementation is not PVPRO;
PVPRO is a relevant published alternative for an external benchmark.

Inverter and thermal curves
---------------------------

The efficiency estimator fits nonnegative normalized loss coefficients:

.. math::

   P_{loss}/P_r = a+b(P_{dc}/P_r)+c(P_{dc}/P_r)^2.

Use actual converter input/output at a consistent meter boundary. Thermal
derating instead fits ``Pcap = Pr * clip(1-slope*max(T-knee,0),0,1)``. It uses
only independently estimated available power above rating and command limits
at or above rating. The high-power threshold is conservative and excludes
useful partially loaded evidence; extend the observation model for such data.
Insufficient coverage returns ``not_identifiable``. Multiple competing limits,
sensor dynamics and cooling state need site-specific causal discrimination.

The curves are effective field estimates, not recovered proprietary OEM
specifications or accredited certification results. Voltage dependence,
thermal hysteresis and multi-state cooling are not implemented.

Uncertainty
-----------

Reports contain residuals, sample counts, assumptions and local rank diagnostics.
They do not provide universally calibrated confidence intervals. Day-block
resampling is provided as a generic utility, preserving within-day dependence.
Use held-out days/seasons and stress tests for meteorology, sensor bias and
model mismatch. Do not randomly split autocorrelated adjacent points. Repeated
bootstrap timestamps need weighted or residual-based fitting when an estimator
requires unique time indices.

Primary sources
---------------

* `pvlib documentation <https://pvlib-python.readthedocs.io/en/stable/>`_
* `De Soto parameter translation <https://pvlib-python.readthedocs.io/en/stable/reference/generated/pvlib.pvsystem.calcparams_desoto.html>`_
* `PVPRO source and references <https://github.com/DuraMAT/pvpro>`_
* `Sandia inverter model <https://pvlib-python.readthedocs.io/en/stable/reference/generated/pvlib.inverter.sandia.html>`_

Sandia fitting is a stronger multi-voltage alternative for inverter studies;
the initial EnerQit implementation uses the explicitly simpler loss model.
