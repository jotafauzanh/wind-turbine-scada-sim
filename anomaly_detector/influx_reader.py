"""
InfluxDB Reader

Queries telemetry data from InfluxDB for the anomaly detector.
Also provides a write_alert method so the anomaly detector can
write alerts back to the same database.
"""

import logging
from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

logger = logging.getLogger("influx_reader")


class InfluxReader:
    def __init__(self, url: str, token: str, org: str, bucket: str):
        self.bucket = bucket
        self.org = org
        self.client = InfluxDBClient(url=url, token=token, org=org)
        self.query_api = self.client.query_api()
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

    def get_latest_per_turbine(self, sensor_name: str) -> dict[str, float]:
        """
        Get the most recent value of a sensor for each turbine.

        Returns: {turbine_id: latest_value}

        TODO: Implement:
        1. Build a Flux query:
           from(bucket: "{self.bucket}")
             |> range(start: -5m)
             |> filter(fn: (r) => r._measurement == "telemetry")
             |> filter(fn: (r) => r.sensor == "{sensor_name}")
             |> group(columns: ["turbine_id"])
             |> last()

        2. Execute: tables = self.query_api.query(query, org=self.org)

        3. Parse results into dict:
           For each record in tables:
             result[record.values["turbine_id"]] = record.get_value()

        4. Return the dict. Handle empty results gracefully.
        """
        # TODO: implement query
        return {}

    def get_recent_values(
        self, sensor_name: str, turbine_id: str, minutes: int = 5
    ) -> list[tuple[datetime, float]]:
        """
        Get recent time-series values for a specific turbine and sensor.

        Returns: [(timestamp, value), ...]

        TODO: Implement similar to above but return full time series
        instead of just the latest value. Useful for trend-based detection.
        """
        # TODO: implement query
        return []

    def write_alert(
        self,
        turbine_id: str,
        alert_type: str,
        severity: str,
        message: str,
        timestamp: datetime | None = None,
    ) -> None:
        """
        Write an alert point to InfluxDB.

        TODO: Implement:
        1. Create point with measurement "alerts"
        2. Tags: farm, turbine_id, alert_type, severity
        3. Field: message
        4. Write with error handling
        """
        # TODO: implement alert write
        pass

    def close(self) -> None:
        self.write_api.close()
        self.client.close()
