"""
Weather Simulator

Generates realistic wind speed and ambient temperature that evolve over time.
All turbines in the farm share the same weather (with slight per-turbine noise
added in the turbine model itself).

Wind speed uses a mean-reverting random walk (Ornstein-Uhlenbeck process)
to create realistic patterns — sustained gusts, calm periods, and gradual changes.
"""

import math
import random


class WeatherSimulator:
    def __init__(
        self,
        mean_wind_speed: float = 9.0,  # m/s — typical North Sea average
        wind_volatility: float = 0.5,  # How much wind changes per step
        mean_reversion_rate: float = 0.02,  # How strongly wind returns to mean
        base_ambient_temp: float = 12.0,  # °C — typical Danish annual average
    ):
        self.mean_wind_speed = mean_wind_speed
        self.wind_volatility = wind_volatility
        self.mean_reversion_rate = mean_reversion_rate
        self.base_ambient_temp = base_ambient_temp

        self.current_wind_speed = mean_wind_speed
        self.current_ambient_temp = base_ambient_temp
        self.tick = 0

    def step(self) -> None:
        """
        Advance weather by one tick.
        """

        """
        1. Wind speed — Ornstein-Uhlenbeck process:
        drift = mean_reversion_rate * (mean_wind_speed - current_wind_speed)
        noise = wind_volatility * random.gauss(0, 1)
        current_wind_speed += drift + noise
        Clamp to [0, 35] m/s
        """
        drift = self.mean_reversion_rate * (
            self.mean_wind_speed - self.current_wind_speed
        )
        noise = self.wind_volatility * random.gauss(0, 1)
        self.current_wind_speed += drift + noise

        if self.current_wind_speed < 0.0:
            self.current_wind_speed = 0.0
        elif self.current_wind_speed > 35.0:
            self.current_wind_speed = 35.0

        """
        2. Ambient temperature — slow sinusoidal variation:
        Add a slow sine wave (period ~3600 ticks ≈ 1 hour at 1s ticks)
        to simulate day/night temperature swing of ±5°C
        Plus small random noise ±0.2°C
        """
        sine = math.sin(math.radians((self.tick / 10) % 360))
        ambient_offset = sine * 5
        ambient_offset = ambient_offset + (random.uniform(-0.2, 0.2))
        self.current_ambient_temp = self.base_ambient_temp + ambient_offset

        """
        3. Increment self.tick
        """
        self.tick += 1

        pass

    def get_wind_speed(self) -> float:
        """Return current wind speed in m/s."""
        return self.current_wind_speed

    def get_ambient_temperature(self) -> float:
        """Return current ambient temperature in °C."""
        return self.current_ambient_temp
