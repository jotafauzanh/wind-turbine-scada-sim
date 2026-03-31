"""
OPC-UA Client — Subscription Handler

Connects to the simulator's OPC-UA server, discovers all turbine nodes,
and subscribes to data changes. On every change, calls the provided
callback (which writes to InfluxDB).

This is the "data acquisition" part of SCADA — the system that pulls
telemetry from field devices into the central database.
"""

import asyncio
import logging
import datetime
from typing import Callable
from asyncua import Client, Node
from asyncua.common.subscription import SubHandler

logger = logging.getLogger("opcua_client")


class DataChangeHandler(SubHandler):
    """
    Called by opcua-asyncio whenever a subscribed node value changes.
    Parses the node path to extract turbine_id and sensor_name,
    then forwards to the callback.
    """

    def __init__(self, node_map: dict[str, tuple[str, str]], callback: Callable):
        """
        Args:
            node_map: Maps node_id_string -> (turbine_id, sensor_name)
            callback: Function to call with (turbine_id, sensor_name, value, timestamp)
        """
        self.node_map = node_map
        self.callback = callback

    def datachange_notification(self, node: Node, val, data) -> None:
        """
        1. Get node_id string: node_id = node.nodeid.to_string()
        2. Look up (turbine_id, sensor_name) from self.node_map
        3. Get timestamp from data.monitored_item.Value.SourceTimestamp
            (fall back to datetime.utcnow() if None)
        4. Call self.callback(turbine_id, sensor_name, float(val), timestamp)
        5. Handle KeyError gracefully if node_id not in map
        """

        try:
            node_id = node.nodeid.to_string()
        except:
            logger.warning(
                f"Fail to datachange_notifiation "
                f"node={node}, val={val}, "
                f"data={data}%"
            )
            pass

        turbine_id, sensor_name = self.node_map[node_id]
        timestamp = data.monitored_item.Value.SourceTimestam
        if not timestamp:
            timestamp = datetime.utcnow()

        self.callback(turbine_id, sensor_name, float(val), timestamp)

        pass


class OpcuaSubscriber:
    def __init__(self, endpoint: str, interval_ms: int, on_data_change: Callable):
        self.endpoint = endpoint
        self.interval_ms = interval_ms
        self.on_data_change = on_data_change
        self.client = Client(url=endpoint)
        self.subscription = None

    async def connect_and_subscribe(self) -> None:
        """
        TODO: Implement:
        1. Connect: await self.client.connect()
        2. Browse the "Farm" folder to discover all turbine subfolders
        3. For each turbine folder, browse its children (sensor nodes)
        4. Build a node_map: {node.nodeid.to_string(): (turbine_id, sensor_name)}
        5. Create a subscription:
           handler = DataChangeHandler(node_map, self.on_data_change)
           self.subscription = await self.client.create_subscription(
               self.interval_ms, handler
           )
        6. Subscribe to all discovered nodes:
           await self.subscription.subscribe_data_change(all_nodes)
        7. Log how many nodes were subscribed

        Handle connection failures with retry logic:
        - If connection fails, wait 5 seconds and retry
        - Log each retry attempt
        """
        # TODO: implement connection and subscription

        pass

    async def disconnect(self) -> None:
        """Clean up subscription and client connection."""
        if self.subscription:
            await self.subscription.delete()
        await self.client.disconnect()
