"""
Wind Turbine Physics Model

Simulates a single wind turbine generating realistic telemetry.
Uses the power equation: P = 0.5 * rho * A * v^3 * Cp

Key data points (these are what real SCADA monitors):
- wind_speed_ms:      Wind speed at hub height (m/s)
- rotor_rpm:          Rotor rotational speed (RPM)
- power_output_kw:    Electrical power output (kW)
- nacelle_temp_c:     Nacelle internal temperature (°C)
- pitch_angle_deg:    Blade pitch angle (degrees)
- yaw_angle_deg:      Nacelle yaw position (degrees)
- vibration_mm_s:     Drivetrain vibration level (mm/s RMS)
"""

import math
import random
from dataclasses import dataclass, field


# Turbine specs (loosely based on a Vestas V90-3.0 MW)
ROTOR_DIAMETER_M = 90.0
ROTOR_AREA_M2 = math.pi * (ROTOR_DIAMETER_M / 2) ** 2
AIR_DENSITY = 1.225  # kg/m³ at sea level
RATED_POWER_KW = 3000.0
CUT_IN_SPEED = 3.5  # m/s — turbine starts generating
RATED_SPEED = 12.0  # m/s — reaches full power
CUT_OUT_SPEED = 25.0  # m/s — turbine shuts down for safety
MAX_CP = 0.45  # Power coefficient (Betz limit is 0.593)


@dataclass
class TurbineState:
    """Current sensor readings for one turbine."""

    wind_speed_ms: float = 0.0
    rotor_rpm: float = 0.0
    power_output_kw: float = 0.0
    nacelle_temp_c: float = 25.0
    pitch_angle_deg: float = 0.0
    yaw_angle_deg: float = 0.0
    vibration_mm_s: float = 0.5


@dataclass
class WindTurbine:
    turbine_id: str
    state: TurbineState = field(default_factory=TurbineState)

    # Fault flags — set by FaultInjector, cleared after some time
    fault_bearing_overheat: bool = False
    fault_pitch_stuck: bool = False
    fault_yaw_misalignment: bool = False

    def update(self, wind_speed: float, ambient_temp: float) -> None:
        """
        Recalculate all sensor readings based on current wind speed
        and ambient temperature. This is called every tick.

        TODO: Implement the following logic:

        1. Store wind_speed in state.wind_speed_ms

        2. Calculate power_output_kw using the power curve:
           - Below cut_in_speed: 0 kW
           - Between cut_in and rated: P = 0.5 * rho * A * v^3 * Cp
             (clamp to RATED_POWER_KW)
           - Between rated and cut_out: RATED_POWER_KW
           - Above cut_out: 0 kW (safety shutdown)
           - Add ±2% random noise for realism

        3. Calculate rotor_rpm:
           - Proportional to wind speed when generating
           - Typical range: 8-16 RPM for this turbine size
           - 0 when not generating

        4. Calculate pitch_angle_deg:
           - 0° when below rated speed (max power extraction)
           - Increases toward 25° as wind approaches cut_out
             (feathering to limit power)
           - If fault_pitch_stuck: don't change the angle

        5. Update yaw_angle_deg:
           - Slowly track wind direction (simulate with random walk)
           - If fault_yaw_misalignment: add 15-30° offset

        6. Calculate nacelle_temp_c:
           - Base: ambient_temp + 15°C (heat from gearbox/generator)
           - Increases with power output
           - If fault_bearing_overheat: add 20-40°C extra
           - Add slight random noise

        7. Calculate vibration_mm_s:
           - Base: 0.5-2.0 mm/s (normal operating range)
           - Proportional to rotor_rpm
           - If fault_bearing_overheat: multiply by 3-5x
           - Add random noise
        """
        # TODO: implement turbine physics
        pass

    def clear_faults(self) -> None:
        """Reset all fault flags to normal operation."""
        self.fault_bearing_overheat = False
        self.fault_pitch_stuck = False
        self.fault_yaw_misalignment = False
