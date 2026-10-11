Start here
==========

EnerQit is a research toolkit for testing energy-system hypotheses with physical
models and reproducible optimization. You can read every example on this site
without installing Python. Download a script or notebook when you want to run it.

Choose a route
--------------

**I want to understand the engineering applications.** Start with the
:doc:`use-case register <use_cases>`, then open the
:doc:`orientation example <auto_examples/plot_orientation>` or
:doc:`inverter curves example <auto_examples/plot_inverter_curves>`.
Check the input channels and assumptions before interpreting the fitted values.

**I want to evaluate quantum-inspired algorithms.** Read
:doc:`the quantum distinction <quantum>` and
:doc:`the benchmark protocol <benchmarking>`, then run the
:doc:`coupled configuration example <auto_examples/plot_coupled_benchmark>`.
Compare feasibility, physical error and total runtime, not just QUBO energy.

**I want to build a study or contribute code.** Follow :doc:`installation`,
the :doc:`data contract <data_contract>` and the :doc:`API reference <api>`.
Use the :doc:`project guide <project>` to find the relevant source module.

Your first inference
--------------------

After :doc:`installing EnerQit <installation>`, recover a synthetic fixed-array
orientation with a classical physical fit:

.. code-block:: python

   from enerqit.datasets import fixed_array
   from enerqit.solar import fit_orientation

   observations, truth = fixed_array(seed=42)
   result = fit_orientation(observations, latitude=35, longitude=-5)
   print(result.parameters)
   print(truth)

This example establishes a physical baseline. The
:doc:`orientation gallery page <auto_examples/plot_orientation>` also compares
discrete candidate selection using exact enumeration and simulated bifurcation.
For a small candidate list, enumeration is the natural baseline.

What to look for in a result
----------------------------

1. **Evidence:** which sensors, units, time periods and operating regimes were used?
2. **Assumptions:** which quantities were fitted and which were fixed?
3. **Ambiguity:** could a different configuration explain the same observations?
4. **Comparison:** did the method improve on a suitable classical baseline?
5. **Reproduction:** are seeds, model settings and result records retained?

If a new 24-hour export arrives every day, use the
:doc:`daily evidence workflow <workflow>` and
:doc:`worked ingestion example <auto_examples/plot_daily_evidence>`.
More days only help if they add informative irradiance, temperature, load or
geometry conditions. A daily refit is not automatically evidence of a physical
change in the plant.

.. note::

   Version 0.1.0 is validated on synthetic examples. Estimated field response
   curves are conditional models, not manufacturer-certified OEM curves.
   No quantum hardware execution or advantage is claimed.
