"""
OPC-UA Client — Subscription Handler

Connects to the simulator's OPC-UA server, discovers all turbine nodes,
and subscribes to data changes. On every change, calls the provided
callback (which writes to InfluxDB).

This is the "data acquisition" part of SCADA — the system that pulls
telemetry from field devices into the central database.
"""

import asyncio
import datetime
import logging
from collections.abc import Callable

from asyncua import Client, Node
from asyncua.common.subscription import DataChangeNotif, SubHandler

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

    def datachange_notification(self, node: Node, val: float, data: DataChangeNotif) -> None:
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
            turbine_id, sensor_name = self.node_map[node_id]
            timestamp = data.monitored_item.Value.SourceTimestamp
            if not timestamp:
                timestamp = datetime.datetime.utcnow()

            self.callback(turbine_id, sensor_name, float(val), timestamp)
        except Exception as e:
            logger.warning(
                f"Fail to datachange_notifiation node={node}, val={val}, data={data}%, error={e}"
            )
            pass

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

        """
        Objects/
        └── Farm/           ← added under objects node, namespace idx = ns_idx (2)
            ├── Turbine01/
            │   ├── WindSpeed
            │   └── ...
            └── Turbine10/

        """
        # Connect
        await self.client.connect()

        # Get namespace index (uri from opcua_server.py)
        ns_idx = await self.client.get_namespace_index("urn:windfarm:scada:sim")

        # Browse the "Farm" folder
        objects = self.client.get_objects_node()
        farm = await objects.get_child([f"{ns_idx}:Farm"])

        # Browse turbine folders
        turbine_folders = await farm.get_children()

        # Init node_map
        node_map = {}

        # Init collect sensor nodes
        all_sensor_nodes = []

        # For each turbine folder, get sensor nodes
        for turbine_folder in turbine_folders:
            turbine_name = (await turbine_folder.read_browse_name()).Name
            sensor_nodes = await turbine_folder.get_children()
            for sensor_node in sensor_nodes:
                sensor_name = (await sensor_node.read_browse_name()).Name
                node_id_str = sensor_node.nodeid.to_string()
                node_map[node_id_str] = (turbine_name, sensor_name)
                all_sensor_nodes.append(sensor_node)

        # Create subscription
        handler = DataChangeHandler(node_map, self.on_data_change)
        self.subscription = await self.client.create_subscription(self.interval_ms, handler)

        max_retries = 5
        for retry in range(1, max_retries + 1):
            try:
                await self.subscription.subscribe_data_change(all_sensor_nodes)
                break
            except Exception as e:
                logging.warning(
                    f"Subscribing failed. Attempt #{retry}. Retrying in 5 seconds... ({e})"
                )
                if retry == max_retries:
                    raise
                await asyncio.sleep(5)

        logging.info(f"Subscription success, connected to {len(node_map)} nodes")
        pass

    async def disconnect(self) -> None:
        """Clean up subscription and client connection."""
        if self.subscription:
            await self.subscription.delete()
        await self.client.disconnect()
