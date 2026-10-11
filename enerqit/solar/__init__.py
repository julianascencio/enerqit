"""Initial solar-energy application of the EnerQit research toolkit.

Physics and inverse estimators currently execute on classical computers.
Generic quantum-inspired solvers are available in :mod:`enerqit.solvers`.
"""

from enerqit.inference import candidate_problem, fit_orientation, fit_tracker
from enerqit.inverter import efficiency_curve, fit_efficiency
from enerqit.ivtools import ModuleParameters, fit_iv, fit_mpp, iv_current, operating_points
from enerqit.pvsystem import fixed_ac, tracker_ac
from enerqit.thermal import derating_cap, fit_derating
from enerqit.topology import fit_string_counts

__all__ = [
    "ModuleParameters",
    "candidate_problem",
    "derating_cap",
    "efficiency_curve",
    "fit_derating",
    "fit_efficiency",
    "fit_iv",
    "fit_mpp",
    "fit_orientation",
    "fit_string_counts",
    "fit_tracker",
    "fixed_ac",
    "iv_current",
    "operating_points",
    "tracker_ac",
]
