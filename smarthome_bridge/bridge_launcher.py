import os

from gadget_publishers.gadget_publisher_homekit import GadgetPublisherHomekit
from gadgets.local.denon_remote_control_gadget import DenonRemoteControlGadget
from gadgets.remote.remote_fan import Fan
from gadgets.remote.remote_lamp_rgb import RemoteLampRGB
from system.api_definitions import ApiAccessLevel
from system.utils.software_version import SoftwareVersion

from typing import Optional, Tuple

from smarthome_bridge.bridge import Bridge

from network.mqtt_credentials_container import MqttCredentialsContainer
from network.mqtt_connector import MQTTConnector
from network.rest_server import RestServer

from smarthome_bridge.client import Client, ClientSoftwareInformationContainer
from datetime import datetime


class BridgeLauncher:

    @staticmethod
    def _add_dummy_data(bridge: Bridge):

        date = datetime.utcnow()
        client = Client(client_id="dummy_client",
                        runtime_id=18298931,
                        software=ClientSoftwareInformationContainer(
                            "2938479384",
                            "spongo",
                            date
                        ),
                        port_mapping={},
                        boot_mode=1,
                        api_version=SoftwareVersion(0, 0, 1))
        bridge.clients.add_client(client)

        gadget = Fan("dummy_fan",
                     client,
                     3)
        bridge.gadgets.add_gadget(gadget)
        client.add_gadget(gadget)

        # gadget2 = LampRGB("dummy_lamp",
        #                   client)
        #
        # bridge.gadgets.add_gadget(gadget2)
        # client.add_gadget(gadget2)

        gadget3 = DenonRemoteControlGadget("denon_tester", "192.168.178.155")
        bridge.gadgets.add_gadget(gadget3)

    def launch(self,
               name: str,
               mqtt: Optional[MqttCredentialsContainer],
               api_port: Optional[int],
               socket_port: Optional[int],
               serial_active: bool,
               static_user_data: Optional[Tuple[str, str]],
               homekit_active: bool,
               add_dummy_data: bool = False,
               data_directory: str = "bridge_data") -> Bridge:

        if not os.path.isdir(data_directory):
            os.mkdir(data_directory)

        # Create Bridge
        bridge = Bridge(name, data_directory)

        # MQTT
        if mqtt is not None:
            mqtt_connector = MQTTConnector(name, mqtt, "smarthome")
            bridge.network.add_connector(mqtt_connector)

        # REST
        if api_port is not None:
            rest_server = RestServer(name, api_port)
            bridge.network.add_connector(rest_server)

        # SOCKET
        if socket_port is not None:
            pass
            # socket_connector = SocketServer(name, socket_port)
            # bridge.get_network_manager().add_connector(socket_connector)

        # SERIAL
        if serial_active:
            pass
            # serial = SerialServer(name, 115200)
            # bridge.get_network_manager().add_connector(serial)

        # APPLE HOME PUBLISHER
        if homekit_active:
            config_file = os.path.join(data_directory, "homekit_server_settings.json")
            hk_publisher = GadgetPublisherHomekit(config_file)
            bridge.gadgets.add_gadget_publisher(hk_publisher)

        if static_user_data is not None:
            u_name, u_passwd = static_user_data
            if u_name and u_passwd:
                bridge.api.auth_manager.users.add_user(username=u_name,
                                                       password=u_passwd,
                                                       access_level=ApiAccessLevel.admin,
                                                       persistent_user=False)

        # Insert dummy data if wanted
        if add_dummy_data:
            self._add_dummy_data(bridge)

        return bridge
