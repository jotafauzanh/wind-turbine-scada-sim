"""
Fault Injector

Randomly injects faults into turbines to create anomalies that the
anomaly detector should catch. Each tick, there's a small probability
of injecting a fault. Faults auto-clear after a random duration.

Fault types:
- bearing_overheat:   Nacelle temp rises 20-40°C, vibration spikes 3-5x
- pitch_stuck:        Pitch angle stops responding to wind changes
- yaw_misalignment:   Nacelle points 15-30° away from wind direction
"""

import random
import logging
from turbine import WindTurbine

logger = logging.getLogger("faults")


class FaultInjector:
    def __init__(self, probability: float = 0.005):
        """
        Args:
            probability: Chance per tick per turbine of injecting a new fault.
                         0.005 ≈ one fault every ~200 ticks (~3 min at 1s interval).
        """
        self.probability = probability
        # Track active faults: {turbine_id: {fault_type: remaining_ticks}}
        self.active_faults: dict[str, dict[str, int]] = {}

    def maybe_inject(self, turbine: WindTurbine) -> None:
        """
        Roll the dice for fault injection, and count down active faults.

        TODO: Implement:
        1. Initialize tracking dict for this turbine if not present

        2. Count down active faults:
           For each active fault, decrement remaining_ticks.
           If remaining_ticks <= 0:
             - Clear the fault flag on the turbine
             - Remove from active_faults
             - Log: "Fault {type} cleared on {turbine_id}"

        3. Maybe inject a new fault:
           If random.random() < self.probability and turbine has no active faults:
             - Pick a random fault type from: bearing_overheat, pitch_stuck, yaw_misalignment
             - Set the corresponding flag on the turbine (e.g., turbine.fault_bearing_overheat = True)
             - Set duration: random.randint(30, 120) ticks
             - Store in active_faults
             - Log: "Injected {type} on {turbine_id} for {duration} ticks"
        """
        # TODO: implement fault injection
        pass
