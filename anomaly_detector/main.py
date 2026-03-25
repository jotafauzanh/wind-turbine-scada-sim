"""
Anomaly Detector — Entry Point

Periodically reads recent telemetry from InfluxDB, runs anomaly checks,
and writes alerts back to InfluxDB for Grafana to display.

This represents the "condition monitoring / predictive maintenance" layer
that sits on top of SCADA data in modern renewable energy operations.
"""

import asyncio
import logging
import os

from influx_reader import InfluxReader
from detectors import PowerCurveDetector, TemperatureDetector, VibrationDetector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("anomaly_detector")

INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "scada-dev-token")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "scada")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "scada")
CHECK_INTERVAL_S = int(os.getenv("CHECK_INTERVAL_S", "30"))
TEMP_THRESHOLD_C = float(os.getenv("TEMP_THRESHOLD_C", "80.0"))
VIBRATION_THRESHOLD = float(os.getenv("VIBRATION_THRESHOLD", "8.0"))
POWER_CURVE_DEVIATION_PCT = float(os.getenv("POWER_CURVE_DEVIATION_PCT", "20.0"))


async def main():
    reader = InfluxReader(
        url=INFLUXDB_URL,
        token=INFLUXDB_TOKEN,
        org=INFLUXDB_ORG,
        bucket=INFLUXDB_BUCKET,
    )

    detectors = [
        PowerCurveDetector(deviation_threshold_pct=POWER_CURVE_DEVIATION_PCT),
        TemperatureDetector(threshold_c=TEMP_THRESHOLD_C),
        VibrationDetector(threshold_mm_s=VIBRATION_THRESHOLD),
    ]

    logger.info(
        f"Anomaly detector started. Checking every {CHECK_INTERVAL_S}s. "
        f"Thresholds: temp={TEMP_THRESHOLD_C}°C, vibration={VIBRATION_THRESHOLD}mm/s, "
        f"power_curve_deviation={POWER_CURVE_DEVIATION_PCT}%"
    )

    try:
        while True:
            for detector in detectors:
                try:
                    alerts = detector.check(reader)
                    for alert in alerts:
                        reader.write_alert(**alert)
                        logger.warning(
                            f"ALERT [{alert['severity']}] {alert['turbine_id']}: "
                            f"{alert['message']}"
                        )
                except Exception as e:
                    logger.error(f"Detector {detector.__class__.__name__} failed: {e}")

            await asyncio.sleep(CHECK_INTERVAL_S)
    except asyncio.CancelledError:
        pass
    finally:
        reader.close()
        logger.info("Anomaly detector shut down.")


if __name__ == "__main__":
    asyncio.run(main())
