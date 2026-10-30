Nomenclature
============

These terms describe the current EnerQit implementation. Input channel names
and units are specified separately in the :doc:`/data_contract`.

.. glossary::

   AC and DC
      Alternating-current and direct-current quantities. EnerQit uses watts
      for power. Measured AC output and DC input must refer to a documented,
      consistent equipment boundary when fitting inverter efficiency.

   Forward model
      A model that predicts observations from specified system parameters.
      EnerQit uses pvlib for PV physics in its current solar application.

   Inverse problem
      Estimating unknown parameters from observations and a forward model.
      A good fit does not by itself establish a unique physical explanation.

   Identifiability
      Whether the available evidence can distinguish the quantities being
      estimated under the chosen assumptions. EnerQit's local diagnostics
      are screening checks, not a general proof of uniqueness.

   GCR
      Ground coverage ratio. The tracker fit uses GCR in the backtracking
      geometry with other axis properties held fixed.

   IV curve
      Current as a function of voltage under specified irradiance and cell
      temperature. A measured sweep and a model-derived operational curve
      provide different levels of evidence.

   MPP and MPPT
      Maximum power point and maximum power point tracking. Operational IV
      reconstruction requires confirmed MPP voltage/current observations;
      arbitrary operating points are not interchangeable with MPP evidence.

   QUBO
      Quadratic unconstrained binary optimization. EnerQit stores a full
      symmetric matrix and evaluates ``E(x) = x.T @ Q @ x + offset`` for
      binary decisions ``x``. The offset is retained in comparisons and
      exports.

   Ising model
      The spin form of a binary quadratic objective. EnerQit uses
      ``x = (s + 1) / 2`` and
      ``E(s) = 0.5 * s.T @ J @ s + h @ s + offset``. Exporter conventions
      are described in :doc:`/quantum`.

   One-hot constraint
      An equality requiring exactly one candidate in a group to be selected.
      Penalty terms encourage this condition; feasibility is checked
      independently after solving.

   SA
      Simulated annealing, a classical stochastic search baseline included
      in ``enerqit.solvers``.

   bSB
      Ballistic simulated bifurcation, a classical oscillator-based search
      heuristic. EnerQit's transparent NumPy implementation runs on a CPU.

   QAOA
      Quantum approximate optimization algorithm. EnerQit includes a small
      classical statevector demonstration, limited to 16 binary variables.
      It does not submit a circuit to quantum hardware.

   Feasibility
      Satisfaction of the explicit constraints recorded with a problem.
      A low penalized QUBO energy and a feasible engineering configuration
      are separate checks.

   RMSE
      Root mean squared error. Its physical meaning depends on the channel
      units and normalization used in the fit or benchmark.

   Provenance
      Records that describe the source evidence, settings, seeds, environment
      and analysis context needed to inspect or reproduce a result.

   Synthetic data
      Observations generated from a declared model rather than collected
      from an operating asset. All bundled EnerQit datasets are synthetic.

See :doc:`/methods` for physical assumptions and :doc:`/benchmarking` for
how objective values, feasibility and runtime are interpreted together.
