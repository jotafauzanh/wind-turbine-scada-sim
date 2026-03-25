"""
Anomaly Detectors

Each detector reads recent telemetry from InfluxDB and returns a list of
alerts (dicts) to be written back. Keep these simple — the point is to
demonstrate you understand *why* SCADA data is collected, not to build
a production ML pipeline.

Detector types:
1. PowerCurveDetector — compares actual power vs expected for given wind speed
2. TemperatureDetector — flags nacelle temps above threshold
3. VibrationDetector — flags vibration levels above threshold
"""

import math
import logging
from datetime import datetime
from influx_reader import InfluxReader

logger = logging.getLogger("detectors")

# Same constants as turbine.py — expected power curve
ROTOR_DIAMETER_M = 90.0
ROTOR_AREA_M2 = math.pi * (ROTOR_DIAMETER_M / 2) ** 2
AIR_DENSITY = 1.225
RATED_POWER_KW = 3000.0
CUT_IN_SPEED = 3.5
RATED_SPEED = 12.0
CUT_OUT_SPEED = 25.0
MAX_CP = 0.45


def expected_power(wind_speed: float) -> float:
    """Calculate expected power output for a given wind speed."""
    if wind_speed < CUT_IN_SPEED or wind_speed > CUT_OUT_SPEED:
        return 0.0
    if wind_speed >= RATED_SPEED:
        return RATED_POWER_KW
    return min(0.5 * AIR_DENSITY * ROTOR_AREA_M2 * wind_speed**3 * MAX_CP / 1000.0, RATED_POWER_KW)


class PowerCurveDetector:
    """
    Detects when a turbine's actual power output deviates significantly
    from what the power curve predicts for the current wind speed.

    This is one of the most common real-world SCADA analytics checks.
    A turbine producing less power than expected at a given wind speed
    may have blade icing, pitch system faults, or yaw misalignment.
    """

    def __init__(self, deviation_threshold_pct: float = 20.0):
        self.threshold = deviation_threshold_pct / 100.0

    def check(self, reader: InfluxReader) -> list[dict]:
        """
        TODO: Implement:
        1. Query reader.get_latest_per_turbine("WindSpeed") -> {turbine_id: value}
        2. Query reader.get_latest_per_turbine("PowerOutput") -> {turbine_id: value}
        3. For each turbine that has both values:
           a. Calculate expected = expected_power(wind_speed)
           b. If expected > 100 kW (skip low-wind situations):
              deviation = abs(actual - expected) / expected
              If deviation > self.threshold:
                Append alert dict:
                {
                    "turbine_id": turbine_id,
                    "alert_type": "power_curve_deviation",
                    "severity": "warning",
                    "message": f"Power {actual:.0f}kW vs expected {expected:.0f}kW ({deviation:.0%} deviation)"
                }
        4. Return list of alerts
        """
        # TODO: implement power curve check
        return []


class TemperatureDetector:
    """
    Flags turbines with nacelle temperature above threshold.
    High nacelle temps can indicate bearing failure, cooling system
    issues, or gearbox problems.
    """

    def __init__(self, threshold_c: float = 80.0):
        self.threshold = threshold_c

    def check(self, reader: InfluxReader) -> list[dict]:
        """
        TODO: Implement:
        1. Query reader.get_latest_per_turbine("NacelleTemp")
        2. For each turbine where temp > self.threshold:
           severity = "critical" if temp > self.threshold + 10 else "warning"
           Append alert dict
        3. Return list of alerts
        """
        # TODO: implement temperature check
        return []


class VibrationDetector:
    """
    Flags turbines with excessive vibration levels.
    High vibration often precedes mechanical failure in bearings,
    gearbox, or generator — catching it early prevents catastrophic damage.
    """

    def __init__(self, threshold_mm_s: float = 8.0):
        self.threshold = threshold_mm_s

    def check(self, reader: InfluxReader) -> list[dict]:
        """
        TODO: Implement:
        1. Query reader.get_latest_per_turbine("Vibration")
        2. For each turbine where vibration > self.threshold:
           severity = "critical" if value > self.threshold * 1.5 else "warning"
           Append alert dict
        3. Return list of alerts
        """
        # TODO: implement vibration check
        return []
