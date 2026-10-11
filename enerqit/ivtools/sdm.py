"""De Soto single-diode parameter recovery using pvlib forward calculations."""

from dataclasses import asdict, dataclass, replace

import numpy as np
import pvlib
from scipy.optimize import least_squares

from enerqit.quality import finite_vectors
from enerqit.results import InferenceResult
from enerqit.uncertainty import jacobian_diagnostics


@dataclass(frozen=True)
class ModuleParameters:
    """Synthetic module reference at 1000 W/m² and 25°C; not an OEM dataset.

    ``a_ref`` is n*Ns*k*Tref/q in V; alpha_sc is A/°C.
    """

    photocurrent: float = 9.5
    saturation_current: float = 1e-10
    resistance_series: float = 0.35
    resistance_shunt: float = 400.0
    a_ref: float = 1.55
    alpha_sc: float = 0.0045

    def __post_init__(self):
        if any(not np.isfinite(v) for v in asdict(self).values()):
            raise ValueError("parameters must be finite")
        if any(getattr(self, n) <= 0 for n in _FIT_NAMES):
            raise ValueError("diode parameters must be positive")


_FIT_NAMES = (
    "photocurrent",
    "saturation_current",
    "resistance_series",
    "resistance_shunt",
    "a_ref",
)
_BOUNDS = {
    "photocurrent": (0.1, 30),
    "saturation_current": (1e-14, 1e-4),
    "resistance_series": (0.001, 5),
    "resistance_shunt": (10, 1e5),
    "a_ref": (0.3, 5),
}


def _translated(module, irradiance, temperature):
    g, t = np.asarray(irradiance, float), np.asarray(temperature, float)
    if not np.isfinite(g).all() or not np.isfinite(t).all() or np.any(g <= 0):
        raise ValueError("finite temperature and positive effective irradiance required")
    if np.any(t <= -273.15):
        raise ValueError("temperature must exceed absolute zero")
    return pvlib.pvsystem.calcparams_desoto(
        g,
        t,
        module.alpha_sc,
        module.a_ref,
        module.photocurrent,
        module.saturation_current,
        module.resistance_shunt,
        module.resistance_series,
    )


def iv_current(voltage, irradiance, temperature, module=None):
    """Calculate model-based IV current in A, given voltage V and cell temperature °C."""
    module = ModuleParameters() if module is None else module
    voltage = np.asarray(voltage, float)
    if not np.isfinite(voltage).all():
        raise ValueError("voltage must be finite")
    return np.asarray(
        pvlib.pvsystem.i_from_v(voltage, *_translated(module, irradiance, temperature))
    )


def operating_points(irradiance, temperature, module=None):
    """Return single-diode Isc, Voc and MPP values from pvlib."""
    module = ModuleParameters() if module is None else module
    return pvlib.pvsystem.singlediode(*_translated(module, irradiance, temperature))


def _fit(residual, initial, free, n, method, warnings, scales):
    if not free or len(set(free)) != len(free) or any(k not in _FIT_NAMES for k in free):
        raise ValueError(f"free must be a unique subset of {_FIT_NAMES}")
    x0 = np.log([getattr(initial, k) for k in free])
    bounds = np.log(np.array([_BOUNDS[k] for k in free])).T

    def unpack(x):
        return replace(initial, **dict(zip(free, np.exp(x))))

    opt = least_squares(
        lambda x: residual(unpack(x)),
        x0,
        bounds=bounds,
        xtol=1e-11,
        ftol=1e-11,
        gtol=1e-11,
        max_nfev=500,
    )
    diag = jacobian_diagnostics(opt.jac)
    identified = diag["rank"] == len(free) and diag["condition_number"] < 1e6
    if not identified:
        warnings.append("Local rank/conditioning does not support all free parameters.")
    return InferenceResult(
        asdict(unpack(opt.x)),
        method,
        float(np.sqrt(np.mean(opt.fun**2))),
        n,
        status="estimated" if identified and opt.success else "not_identifiable",
        units={
            "photocurrent": "A",
            "saturation_current": "A",
            "resistance_series": "ohm",
            "resistance_shunt": "ohm",
            "a_ref": "V",
            "alpha_sc": "A/degC",
            "rmse": scales,
        },
        diagnostics={
            **diag,
            "free_parameters": list(free),
            "optimizer_success": bool(opt.success),
        },
        warnings=warnings,
    )


def fit_iv(voltage, current, irradiance, temperature, *, initial=None, free=_FIT_NAMES):
    """Recover reference parameters from IV sweeps at known effective G and cell T.

    Inputs are flattened samples, each with V, I, G and T. Broad voltage coverage
    including near Isc and Voc is needed to recover all five reference parameters.
    alpha_sc is held fixed. RMSE is in A; sweep correlation is not modeled.
    """
    v, i, g, t = finite_vectors(voltage, current, irradiance, temperature, minimum_rows=12)
    initial = ModuleParameters() if initial is None else initial
    return _fit(
        lambda m: iv_current(v, g, t, m) - i,
        initial,
        free,
        len(v),
        "classical_iv_least_squares",
        ["Model-derived curves are not OEM-certified curves."],
        "A",
    )


def fit_mpp(
    voltage,
    current,
    irradiance,
    temperature,
    *,
    initial=None,
    free=("photocurrent", "resistance_series"),
):
    """Estimate selected parameters from confirmed MPPT operating points.

    This fits model-predicted MPP voltage and current across changing conditions,
    not an IV sweep. Default fits two parameters and fixes the others. Curtailment,
    clipping, scan transients and non-MPPT periods must be removed by the caller.
    This is a simple reference estimator, not an implementation of PVPRO.
    """
    v, i, g, t = finite_vectors(voltage, current, irradiance, temperature, minimum_rows=12)
    if np.any(v <= 0) or np.any(i <= 0):
        raise ValueError("MPP voltage/current must be positive")
    initial = ModuleParameters() if initial is None else initial
    vs, cs = np.median(v), np.median(i)

    def residual(m):
        predicted = operating_points(g, t, m)
        return np.r_[
            (np.asarray(predicted["v_mp"]) - v) / vs, (np.asarray(predicted["i_mp"]) - i) / cs
        ]

    return _fit(
        residual,
        initial,
        free,
        len(v),
        "classical_mpp_least_squares",
        [
            "Requires verified MPPT samples and known effective irradiance/cell temperature.",
            "Reconstructed IV curves are conditional on fixed parameters and diode physics.",
            "AC power alone does not identify a full IV curve.",
        ],
        "normalized V/I",
    )
