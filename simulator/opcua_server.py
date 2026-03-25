"""
OPC-UA Server

Exposes all turbine data points as OPC-UA nodes in a structured address space.

Node structure:
  Farm/
  ├── Turbine01/
  │   ├── WindSpeed        (Double, m/s)
  │   ├── RotorRPM         (Double, RPM)
  │   ├── PowerOutput      (Double, kW)
  │   ├── NacelleTemp      (Double, °C)
  │   ├── PitchAngle       (Double, degrees)
  │   ├── YawAngle         (Double, degrees)
  │   └── Vibration        (Double, mm/s)
  ├── Turbine02/
  │   └── ...
  └── Turbine10/
      └── ...

This is the part interviewers will care about most — it proves you
understand OPC-UA information modeling, not just the concept.
"""

from asyncua import Server, ua
from turbine import WindTurbine

# Node IDs for each sensor type per turbine
SENSOR_NAMES = [
    "WindSpeed",
    "RotorRPM",
    "PowerOutput",
    "NacelleTemp",
    "PitchAngle",
    "YawAngle",
    "Vibration",
]


class ScadaOpcuaServer:
    def __init__(self, port: int = 4840):
        self.port = port
        self.server = Server()
        # Maps turbine_id -> {sensor_name: ua_variable_node}
        self.turbine_nodes: dict[str, dict[str, any]] = {}

    async def init(self) -> None:
        """
        Initialize the OPC-UA server.

        TODO: Implement:
        1. Call await self.server.init()
        2. Set endpoint: self.server.set_endpoint(f"opc.tcp://0.0.0.0:{self.port}")
        3. Set server name: self.server.set_server_name("WindFarm SCADA Simulator")
        4. Register a namespace: uri = "urn:windfarm:scada:sim"
           idx = await self.server.register_namespace(uri)
           Store idx as self.ns_idx for use in register_turbines
        """
        # TODO: implement server initialization
        pass

    async def register_turbines(self, turbines: list[WindTurbine]) -> None:
        """
        Create the OPC-UA node tree for all turbines.

        TODO: Implement:
        1. Get the Objects node: objects = self.server.nodes.objects
        2. Create a "Farm" folder: farm = await objects.add_folder(self.ns_idx, "Farm")
        3. For each turbine:
           a. Create a folder: turbine_folder = await farm.add_folder(self.ns_idx, turbine.turbine_id)
           b. For each sensor in SENSOR_NAMES:
              - Create a variable node with initial value 0.0:
                node = await turbine_folder.add_variable(self.ns_idx, sensor_name, 0.0)
              - Make it readable: await node.set_writable(False)
           c. Store nodes in self.turbine_nodes[turbine.turbine_id][sensor_name] = node
        """
        # TODO: implement node registration
        pass

    async def update_turbine_nodes(self, turbine: WindTurbine) -> None:
        """
        Push current turbine state to OPC-UA node values.

        TODO: Implement:
        1. Get nodes dict for this turbine: nodes = self.turbine_nodes[turbine.turbine_id]
        2. Write each value:
           await nodes["WindSpeed"].write_value(turbine.state.wind_speed_ms)
           await nodes["RotorRPM"].write_value(turbine.state.rotor_rpm)
           ... etc for all 7 sensors
        """
        # TODO: implement node updates
        pass

    async def start(self) -> None:
        await self.server.start()

    async def stop(self) -> None:
        await self.server.stop()
