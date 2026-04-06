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
TIP_SPEED_RATIO = 7.5  # The ratio between the tangential speed of a wind turbine blade tip and the actual speed of the wind
YAW_RATE = 0.5  # degrees per update step (how fast the yaw motor turns)

# Nacelle
TEMP_RISE_PER_KW = 0.01  # Celcius per kW of power output
COOLING_RATE = 0.05  # how fast temp returns to ambient (0-1)
MAX_NACELLE_TEMP = 80.0  # Celcius upper bound

# Vibration
VIBRATION_BASE = 0.05  # mm/s
VIBRATION_PER_RPM = 0.15  # mm/s per RPM
VIBRATION_PER_KW = 0.001  # mm/s per kW (drivetrain load)
VIBRATION_SMOOTHING = 0.1  # how fast vibration changes


@dataclass
class TurbineState:
    """Current sensor readings for one turbine."""

    wind_speed_ms: float = 0.0
    wind_direction: float = 0.0
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
    fault_nacelle_cooling: bool = False
    fault_high_vibration: bool = False

    def update(self, wind_speed: float, ambient_temp: float) -> None:
        """
        Recalculate all sensor readings based on current wind speed
        and ambient temperature. This is called every tick.
        """

        # Store wind speed
        self.state.wind_speed_ms = wind_speed

        """
        Calculate power_output_kw using the power curve:
            - Below cut_in_speed: 0 kW
            - Between cut_in and rated: P = 0.5 * rho * A * v^3 * Cp
            (clamp to RATED_POWER_KW)
            - Between rated and cut_out: RATED_POWER_KW
            - Above cut_out: 0 kW (safety shutdown)
            - Add ±2% random noise for realism
        """

        if wind_speed < CUT_IN_SPEED:
            self.state.power_output_kw = 0
        elif CUT_IN_SPEED <= wind_speed <= RATED_SPEED:
            wind_power = 0.5 * AIR_DENSITY * ROTOR_AREA_M2 * pow(wind_speed, 3) * MAX_CP

            # clamped
            self.state.power_output_kw = min(wind_power, RATED_POWER_KW)

            # add noise
            self.state.power_output_kw += random.uniform(
                (self.state.power_output_kw * -0.02), self.state.power_output_kw * 0.02
            )
        elif RATED_SPEED < wind_speed < CUT_OUT_SPEED:
            self.state.power_output_kw = RATED_POWER_KW
        elif wind_speed > CUT_OUT_SPEED:
            # Safety shutdown
            self.state.power_output_kw = 0

        """
        Calculate rotor_rpm:
            - Proportional to wind speed when generating
            - Typical range: 8-16 RPM for this turbine size
            - 0 when not generating

        Tip Speed Ratio (TSR or λ)
        λ = (ω × R) / v
        Rearranging to get RPM:
        RPM = (λ × v × 60) / (π × D)

        Where:
        λ (lambda) = Tip Speed Ratio, typically 6–8 for modern 3-blade turbines
        v = wind speed (m/s)
        D = rotor diameter (m)
        """

        if self.state.power_output_kw == 0:
            # If not generating, its not spinning
            self.state.rotor_rpm = 0
        else:
            self.state.rotor_rpm = (TIP_SPEED_RATIO * wind_speed * 60) / (
                math.pi * ROTOR_DIAMETER_M
            )

        """
        Calculate pitch_angle_deg:
            - 0° when below rated speed (max power extraction)
            - Increases toward 25° as wind approaches cut_out
              (feathering to limit power)
            - If fault_pitch_stuck: don't change the angle
        """
        if self.fault_pitch_stuck:
            # Don't change
            self.state.pitch_angle_deg = self.state.pitch_angle_deg
        elif wind_speed < RATED_SPEED:
            self.state.pitch_angle_deg = 0.0
        elif RATED_SPEED <= wind_speed < CUT_OUT_SPEED:
            # range of 0.0 to 25.0 between RATED_SPEED and CUT_OUT_SPEED
            pole = (wind_speed - RATED_SPEED) / (CUT_OUT_SPEED - RATED_SPEED)
            self.state.pitch_angle_deg = pole * 25
        elif wind_speed > CUT_OUT_SPEED:
            # TODO: What do? I will just set 25, for now
            self.state.pitch_angle_deg = 25.0

        """
        Update yaw_angle_deg:
            - Slowly track wind direction (simulate with random walk)
            - If fault_yaw_misalignment: add 15-30° offset
        """

        # Simulate wind direction with a random walk
        self.state.wind_direction += random.uniform(-2.0, 2.0)  # slow drift
        self.state.wind_direction %= 360  # keep within 360 deg

        # Slowly track toward wind direction
        # get shortest signed angle difference (wrap around 0deg / 360deg)
        yaw_move = (self.state.wind_direction - self.state.yaw_angle_deg + 180) % 360 - 180

        if abs(yaw_move) > YAW_RATE:
            # Move toward wind direction at limited speed
            self.state.yaw_angle_deg += YAW_RATE * (1 if yaw_move > 0 else -1)
        else:
            self.state.yaw_angle_deg = self.state.wind_direction

        self.state.yaw_angle_deg %= 360

        # fault_yaw_misalignment
        if self.fault_yaw_misalignment:
            self.state.yaw_angle_deg += random.uniform(15.0, 30.0)
            self.state.yaw_angle_deg %= 360  # still keep within 360 de

        """
        Calculate nacelle_temp_c:
            - Base: ambient_temp + 15°C (heat from gearbox/generator)
            - Increases with power output
            - If fault_bearing_overheat: add 20-40°C extra
            - Add slight random noise
        """

        temp_base = ambient_temp + 15
        temp_power = temp_base + (self.state.power_output_kw * TEMP_RISE_PER_KW)
        temp_cooling_rate = COOLING_RATE

        # fault_nacelle_cooling, simulates cooling failure
        if self.fault_nacelle_cooling:
            temp_cooling_rate *= 0.1

        # Smooth transition (exponential moving avg)
        self.state.nacelle_temp_c += temp_cooling_rate * (temp_power - self.state.nacelle_temp_c)

        # add slight noise
        self.state.nacelle_temp_c += random.uniform(-0.3, 0.3)

        # fault_bearing_overheat
        if self.fault_bearing_overheat:
            self.state.nacelle_temp_c += random.uniform(20.0, 40.0)

        # Clamp
        self.state.nacelle_temp_c = min(self.state.nacelle_temp_c, MAX_NACELLE_TEMP)

        """
        Calculate vibration_mm_s:
            - Base: 0.5-2.0 mm/s (normal operating range)
            - Proportional to rotor_rpm
            - If fault_bearing_overheat: multiply by 3-5x
            - Add random noise
        """

        vibration = (
            VIBRATION_BASE
            + (self.state.rotor_rpm * VIBRATION_PER_RPM)
            + (self.state.power_output_kw * VIBRATION_PER_KW)
        )

        # fault_yaw_misalignment adds vibration (aerodyanmic imbalance)
        if self.fault_yaw_misalignment:
            vibration *= 1.3

        # smooth transition
        self.state.vibration_mm_s += VIBRATION_SMOOTHING * (vibration - self.state.vibration_mm_s)

        # Add noise
        self.state.vibration_mm_s += random.uniform(-0.2, 0.2)

        # fault_high_vibration
        if self.fault_high_vibration:
            self.state.vibration_mm_s += random.uniform(3.0, 6.0)

        # fault_bearing_overheat
        if self.fault_bearing_overheat:
            self.state.vibration_mm_s *= random.uniform(3.0, 5.0)

        # floor
        self.state.vibration_mm_s = max(0.0, self.state.vibration_mm_s)

        pass

    def clear_faults(self) -> None:
        """Reset all fault flags to normal operation."""
        self.fault_bearing_overheat = False
        self.fault_pitch_stuck = False
        self.fault_yaw_misalignment = False
        self.fault_nacelle_cooling = False
        self.fault_high_vibration = False
