import os

from gadget_publishers.gadget_publisher_homekit import GadgetPublisherHomekit
from gadgets.lamp_neopixel_basic import LampNeopixelBasic
from system.api_definitions import ApiAccessLevel
from system.utils.software_version import SoftwareVersion

from typing import Optional, Tuple

from smarthome_bridge.bridge import Bridge

from network.mqtt_credentials_container import MqttCredentialsContainer
from network.mqtt_connector import MQTTConnector
from network.rest_server import RestServer

from gadget_publishers.homebridge_network_connector import HomebridgeNetworkConnector
from gadget_publishers.gadget_publisher_homebridge import GadgetPublisherHomeBridge

from gadgets.fan_westinghouse_ir import FanWestinghouseIR
from smarthome_bridge.characteristic import Characteristic, CharacteristicIdentifier
from smarthome_bridge.client import Client
from gadgets.gadget_event_mapping import GadgetEventMapping
from datetime import datetime


class BridgeLauncher:

    @staticmethod
    def _add_dummy_data(bridge: Bridge):

        gadget = FanWestinghouseIR("dummy_fan",
                                   "bridge",
                                   Characteristic(CharacteristicIdentifier.status,
                                                  0,
                                                  1,
                                                  1),
                                   Characteristic(CharacteristicIdentifier.fan_speed,
                                                  0,
                                                  100,
                                                  4))
        gadget.set_event_mapping([
            GadgetEventMapping("ab09d8_", [(1, 1)])
        ])
        bridge.get_gadget_manager().receive_gadget(gadget)

        gadget2 = LampNeopixelBasic("dummy_lamp",
                                    "bridge",
                                    Characteristic(CharacteristicIdentifier.status,
                                                   0,
                                                   1,
                                                   1),
                                    Characteristic(
                                        CharacteristicIdentifier.hue,
                                        0,
                                        360,
                                        value=25
                                    ),
                                    Characteristic(
                                        CharacteristicIdentifier.saturation,
                                        0,
                                        100,
                                        value=99
                                    ),
                                    Characteristic(
                                        CharacteristicIdentifier.brightness,
                                        0,
                                        100,
                                        value=88
                                    ))

        bridge.get_gadget_manager().receive_gadget(gadget2)

        date = datetime.utcnow()
        client = Client(name="dummy_client",
                        runtime_id=18298931,
                        flash_date=date,
                        software_commit="2938479384",
                        software_branch="spongo",
                        port_mapping={},
                        boot_mode=1,
                        api_version=SoftwareVersion(0, 0, 1))
        bridge.get_client_manager().add_client(client)

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
            bridge.get_network_manager().add_connector(mqtt_connector)

        # REST
        if api_port is not None:
            rest_server = RestServer(name, api_port)
            bridge.get_network_manager().add_connector(rest_server)

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
            bridge.add_gadget_publisher(hk_publisher)

        if static_user_data is not None:
            u_name, u_passwd = static_user_data
            if u_name and u_passwd:
                bridge.api.auth_manager.user_manager.add_user(username=u_name,
                                                              password=u_passwd,
                                                              access_level=ApiAccessLevel.admin,
                                                              persistent_user=False)

        # Insert dummy data if wanted
        if add_dummy_data:
            self._add_dummy_data(bridge)

        return bridge
