API Reference
=============

Public entry points
-------------------

Start with ``enerqit.solar`` for the solar application and ``enerqit.solvers``
for interchangeable binary solvers. These modules re-export the functions
documented below from their implementation modules; their signatures and
return values are the same.

.. code-block:: python

   from enerqit.datasets import fixed_array
   from enerqit.solar import fit_orientation

   observations, truth = fixed_array(seed=42)
   result = fit_orientation(observations, latitude=35, longitude=-5)
   print(result.to_dict())

.. list-table:: API map
   :header-rows: 1
   :widths: 35 65

   * - Entry point
     - Use
   * - ``enerqit.solar``
     - Forward PV predictions, orientation/tracker fits and equipment
       characterization.
   * - ``enerqit.qubo``
     - Binary quadratic models, physical template encoding and Ising conversion.
   * - ``enerqit.solvers``
     - Exact, grouped exact, simulated annealing and simulated bifurcation solvers.
   * - ``enerqit.solvers.quantum``
     - Classical QAOA simulation and optional quantum SDK model exports.
   * - ``enerqit.datasets`` and ``enerqit.timeseries``
     - Synthetic inputs and a local study evidence store.
   * - ``enerqit.InferenceResult`` and ``enerqit.SolverResult``
     - Serializable result containers, defined in ``enerqit.results``.

For input units and operating assumptions, read the :doc:`data_contract` and
:doc:`methods`. The :doc:`example gallery </gallery/index>` demonstrates these
interfaces together.

Forward physics and inference
-----------------------------

.. automodule:: enerqit.pvsystem
   :members:

.. automodule:: enerqit.inference
   :members:

.. automodule:: enerqit.ivtools.sdm
   :members:

.. automodule:: enerqit.topology
   :members:

.. automodule:: enerqit.inverter
   :members:

.. automodule:: enerqit.thermal
   :members:

Optimization
------------

.. automodule:: enerqit.qubo
   :members:

.. automodule:: enerqit.solvers.classical
   :members:

.. automodule:: enerqit.solvers.bifurcation
   :members:

.. automodule:: enerqit.solvers.quantum
   :members:

Evidence and reproducibility
----------------------------

.. automodule:: enerqit.timeseries
   :members:

.. automodule:: enerqit.iotools.csv
   :members:

.. automodule:: enerqit.quality
   :members:

.. automodule:: enerqit.uncertainty
   :members:

.. automodule:: enerqit.results
   :members:

.. automodule:: enerqit.datasets
   :members:

.. automodule:: enerqit.benchmarking
   :members:
