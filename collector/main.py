"""
Data Collector — Entry Point

Connects to the OPC-UA server, subscribes to all turbine nodes,
and writes every data change to InfluxDB. This is the SCADA
"data acquisition" layer.
"""

import asyncio
import logging
import os

from opcua_client import OpcuaSubscriber
from influx_writer import InfluxWriter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("collector")

OPCUA_ENDPOINT = os.getenv("OPCUA_ENDPOINT", "opc.tcp://localhost:4840")
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "scada-dev-token")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "scada")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "scada")
SUBSCRIPTION_INTERVAL_MS = int(os.getenv("SUBSCRIPTION_INTERVAL_MS", "1000"))


async def main():
    writer = InfluxWriter(
        url=INFLUXDB_URL,
        token=INFLUXDB_TOKEN,
        org=INFLUXDB_ORG,
        bucket=INFLUXDB_BUCKET,
    )

    subscriber = OpcuaSubscriber(
        endpoint=OPCUA_ENDPOINT,
        interval_ms=SUBSCRIPTION_INTERVAL_MS,
        on_data_change=writer.write_telemetry,
    )

    logger.info(f"Connecting to OPC-UA server at {OPCUA_ENDPOINT}")
    await subscriber.connect_and_subscribe()

    try:
        # Keep alive — the subscription handler does the work via callbacks
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        await subscriber.disconnect()
        writer.close()
        logger.info("Collector shut down.")


if __name__ == "__main__":
    asyncio.run(main())
