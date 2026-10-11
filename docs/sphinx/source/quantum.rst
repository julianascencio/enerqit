Quantum-inspired algorithms and migration
=========================================

**Quantum-inspired algorithms are classical algorithms, not quantum computing.**
Their mathematical inspiration can come from quantum physics or quantum
optimization research, while every calculation still runs on ordinary classical
hardware. The current EnerQit implementation uses a CPU. Other implementations
may use GPUs or classical accelerators; those are also classical hardware.

A classical quantum-circuit simulator numerically models a quantum computation
without executing it on physical qubits. Exporting a QUBO to a quantum SDK is
problem preparation. Actual quantum hardware execution requires an independently
implemented and verified hardware workflow. EnerQit does not currently provide
one, and none of these categories by itself establishes a performance advantage.


Encoding
--------

Candidate contributions form columns of A and binary decisions form x. The
implemented objective is

.. math::

   \min_{x\in\{0,1\}^n} \|W^{1/2}(Ax-y)\|^2
      +\lambda\|Cx-d\|^2.

This is exact for a linear combination of supplied templates, not an arbitrary
nonlinear joint physics model. One-hot groups express mutually exclusive choices;
other equalities represent known inventory. Penalties can produce infeasible
minima when too weak and poor conditioning when too strong. Feasibility is
checked separately; no solver silently repairs constraints.

The package convention is ``E(x)=x.T@Q@x+offset`` with full symmetric Q. Ising
conversion uses ``x=(s+1)/2`` and ``E=.5*s.T@J@s+h@s+constant``. Upper-triangular
QUBO exports double off-diagonal entries. Qiskit computational Z eigenvalues
use ``z=1-2x``, reversing h while preserving pair terms. Exhaustive tests verify
the constants, signs and all bitstring energies on small examples.

Simulated bifurcation
---------------------

The bSB reference solver integrates classical nonlinear oscillator dynamics
with a rising pump and inelastic walls. An auxiliary reference spin handles
linear fields. Spin assignments are read at several checkpoints. A deterministic
one-bit descent can be applied to both bSB and SA; raw and polished energy are
recorded so this contribution is visible. The implementation prioritizes
transparency over optimized throughput. It uses NumPy and a CPU, not a QPU.

It follows the ballistic algorithm concept described by
`Goto et al. (2021) <https://doi.org/10.1126/sciadv.abe7953>`_. It is not a
reproduction claim for the paper's hardware, benchmarks, or specialized
implementations. No tunneling effect or quantum speedup is simulated or claimed.

Why it might help, and why it might not
---------------------------------------

Coupled configuration selection may create many local minima and constraints.
Parallel oscillator trajectories provide a different search heuristic from
Metropolis annealing. This is a testable reason to benchmark bSB, not evidence
it will win. Strong classical competitors include MILP/MIQP, CP-SAT, branch and
bound, parallel tempering, multi-start local search, and problem decomposition.
Only exact enumeration, native group enumeration and SA are currently bundled.

The most important comparison is often with physical optimization, not generic
ML. Neural networks or boosting need representative labeled configurations to
learn inverse mappings; physical optimization can use known equations with
few labels. That advantage belongs to physics-based inference, not specifically
to quantum inspiration. With large labeled datasets, classical ML may have
superior prediction throughput. No ML benchmark or superiority claim is supplied.

For this small reference benchmark, expect classical exact/native methods to
be strong. See measured results rather than marketing claims. Different
heuristic budgets are explicitly reported and are not equal-time comparisons.

Hardware path
-------------

1. Validate physical identifiability and candidate construction on real held-out
   assets; freeze a solver-independent benchmark suite.
2. Establish native classical solutions and scaling/cost curves, including
   infeasible outcomes and all preprocessing time.
3. Export a small QUBO to dimod BQM or a Qiskit SparsePauliOp; verify energies.
4. For annealing, account for topology, embedding, chain strength and coefficient
   precision. For gate models, choose QAOA ansatz, classical optimizer, mapping,
   circuit depth, shots and mitigation. These execution paths are not bundled.
5. Compare end-to-end wall time, cost and physical output at matched quality.
   Include embedding/transpilation, queueing, repetitions and readout overhead.

Starting quantum-inspired makes sense if it builds these reusable assets and
an independent commercial result. It is not evidence that future quantum
hardware will outperform classical methods on this problem.

The NumPy QAOA demo is limited to 16 binary variables and is exponentially
expensive. It illustrates cost/mixer evolution, not scalable quantum computing.
Optional exporters do not submit jobs or use credentials. Relevant primary docs:
`D-Wave models <https://docs.dwavequantum.com/en/latest/concepts/models.html>`_
and `IBM QAOA tutorial <https://quantum.cloud.ibm.com/docs/en/tutorials/quantum-approximate-optimization-algorithm>`_.
