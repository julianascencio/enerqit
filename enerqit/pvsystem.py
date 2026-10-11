"""Small pvlib-backed forward models for explicitly conditional inverse studies."""

import numpy as np
import pvlib

from enerqit.quality import validate_frame

WEATHER_CHANNELS = ("ghi", "dni", "dhi", "temp_air", "wind_speed")


def solar_position(weather, latitude, longitude):
    """Get solar position after validating the weather contract."""
    validate_frame(weather, WEATHER_CHANNELS)
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError("invalid site coordinates")
    if (weather[["ghi", "dni", "dhi", "wind_speed"]] < 0).any().any():
        raise ValueError("irradiance and wind speed must be nonnegative")
    return pvlib.solarposition.get_solarposition(weather.index, latitude, longitude)


def _ac_from_orientation(
    weather, position, tilt, azimuth, *, dc_capacity, ac_capacity, gamma_pdc=-0.0035, albedo=0.2
):
    if min(dc_capacity, ac_capacity) <= 0:
        raise ValueError("capacities must be positive watts")
    poa = pvlib.irradiance.get_total_irradiance(
        tilt,
        azimuth,
        position.apparent_zenith,
        position.azimuth,
        weather.dni,
        weather.ghi,
        weather.dhi,
        albedo=albedo,
        model="isotropic",
    )["poa_global"]
    poa = np.maximum(np.nan_to_num(poa), 0)
    temp = pvlib.temperature.faiman(poa, weather.temp_air, weather.wind_speed)
    dc = pvlib.pvsystem.pvwatts_dc(poa, temp, dc_capacity, gamma_pdc)
    ac = pvlib.inverter.pvwatts(np.maximum(dc, 0), ac_capacity / 0.96)
    return np.asarray(np.maximum(ac, 0))


def fixed_ac(
    weather,
    latitude,
    longitude,
    tilt,
    azimuth,
    *,
    dc_capacity=100_000,
    ac_capacity=90_000,
    gamma_pdc=-0.0035,
    albedo=0.2,
    position=None,
):
    """Predict fixed-array AC power in W using isotropic POA and PVWatts.

    Tilt and azimuth are degrees (azimuth north=0, east=90). No shading,
    bifacial contribution, soiling, curtailment or sensor bias is modeled.
    """
    if not 0 <= tilt <= 90 or not 0 <= azimuth <= 360:
        raise ValueError("tilt must be 0..90 and azimuth 0..360 degrees")
    if position is None:
        position = solar_position(weather, latitude, longitude)
    return _ac_from_orientation(
        weather,
        position,
        tilt,
        azimuth,
        dc_capacity=dc_capacity,
        ac_capacity=ac_capacity,
        gamma_pdc=gamma_pdc,
        albedo=albedo,
    )


def tracker_ac(
    weather,
    latitude,
    longitude,
    *,
    axis_tilt=0,
    axis_azimuth=180,
    max_angle=60,
    gcr=0.35,
    backtrack=True,
    dc_capacity=100_000,
    ac_capacity=90_000,
    position=None,
):
    """Predict single-axis tracker AC power; tracker settings are in degrees.

    GCR affects this model through backtracking geometry, not an explicit
    row-shading irradiance calculation. GCR is unidentifiable with backtrack=False.
    """
    if not 0 < gcr <= 1 or not 0 < max_angle <= 90:
        raise ValueError("gcr must be in (0,1] and max_angle in (0,90]")
    if position is None:
        position = solar_position(weather, latitude, longitude)
    angles = pvlib.tracking.singleaxis(
        position.apparent_zenith,
        position.azimuth,
        axis_tilt=axis_tilt,
        axis_azimuth=axis_azimuth,
        max_angle=max_angle,
        backtrack=backtrack,
        gcr=gcr,
    )
    return _ac_from_orientation(
        weather,
        position,
        angles.surface_tilt.fillna(0),
        angles.surface_azimuth.fillna(180),
        dc_capacity=dc_capacity,
        ac_capacity=ac_capacity,
    )
