"""
Wind Turbine Simulator — Entry Point

Starts N simulated turbines and exposes their telemetry via a single OPC-UA server.
Each turbine updates its sensor readings every UPDATE_INTERVAL_MS milliseconds.
Faults are randomly injected based on FAULT_PROBABILITY.
"""

import asyncio
import logging
import os

from opcua_server import ScadaOpcuaServer
from turbine import WindTurbine
from weather import WeatherSimulator
from faults import FaultInjector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("simulator")

NUM_TURBINES = int(os.getenv("NUM_TURBINES", "10"))
UPDATE_INTERVAL_MS = int(os.getenv("UPDATE_INTERVAL_MS", "1000"))
OPCUA_PORT = int(os.getenv("OPCUA_PORT", "4840"))
FAULT_PROBABILITY = float(os.getenv("FAULT_PROBABILITY", "0.005"))


async def main():
    weather = WeatherSimulator()
    fault_injector = FaultInjector(probability=FAULT_PROBABILITY)

    turbines = [
        WindTurbine(turbine_id=f"Turbine{i+1:02d}")
        for i in range(NUM_TURBINES)
    ]

    server = ScadaOpcuaServer(port=OPCUA_PORT)
    await server.init()
    await server.register_turbines(turbines)
    await server.start()

    logger.info(
        f"OPC-UA server running on opc.tcp://0.0.0.0:{OPCUA_PORT} "
        f"with {NUM_TURBINES} turbines"
    )

    try:
        while True:
            wind_speed = weather.get_wind_speed()
            ambient_temp = weather.get_ambient_temperature()

            for turbine in turbines:
                fault_injector.maybe_inject(turbine)
                turbine.update(wind_speed=wind_speed, ambient_temp=ambient_temp)
                await server.update_turbine_nodes(turbine)

            weather.step()
            await asyncio.sleep(UPDATE_INTERVAL_MS / 1000.0)
    except asyncio.CancelledError:
        pass
    finally:
        await server.stop()
        logger.info("Simulator shut down.")


if __name__ == "__main__":
    asyncio.run(main())
