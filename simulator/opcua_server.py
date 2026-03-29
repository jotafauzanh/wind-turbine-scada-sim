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
        # Init the OPC-UA Server, uses asyncua
        await self.server.init()

        self.server.set_endpoint(f"opc.tcp://0.0.0.0:{self.port}")
        self.server.set_server_name("WindFarm SCADA Simulator")

        uri = "urn:windfarm:scada:sim"
        self.ns_idx = await self.server.register_namespace(uri)

        pass

    async def register_turbines(self, turbines: list[WindTurbine]) -> None:
        # Create the OPC-UA node tree for all turbines.

        objects = self.server.nodes.objects
        farm = await objects.add_folder(self.ns_idx, "Farm")

        for sensor_name in SENSOR_NAMES:
            turbine_folder = await farm.add_folder(self.ns_idx, turbines.turbine_id)
            node = await turbine_folder.add_variable(self.ns_idx, sensor_name, 0.0)
            await node.set_writeable(False)
            self.turbine_nodes[turbines.turbine_id][sensor_name] = node

        pass

    async def update_turbine_nodes(self, turbine: WindTurbine) -> None:
        # Push current turbine state to OPC-UA node values.

        nodes = self.turbine_nodes[turbine.turbine_id]
        await nodes[SENSOR_NAMES[0]].write_value(turbine.wind_speed_ms)
        await nodes[SENSOR_NAMES[1]].write_value(turbine.rotor_rpm)
        await nodes[SENSOR_NAMES[2]].write_value(turbine.power_output_kw)
        await nodes[SENSOR_NAMES[3]].write_value(turbine.nacelle_temp_c)
        await nodes[SENSOR_NAMES[4]].write_value(turbine.pitch_angle_deg)
        await nodes[SENSOR_NAMES[5]].write_value(turbine.yaw_angle_deg)
        await nodes[SENSOR_NAMES[6]].write_value(turbine.vibration_mm_s)
        pass

    async def start(self) -> None:
        await self.server.start()

    async def stop(self) -> None:
        await self.server.stop()
