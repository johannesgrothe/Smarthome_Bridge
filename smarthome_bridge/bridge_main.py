import os
import sys

from system.utils.software_version import SoftwareVersion

sys.path.append(os.getcwd())
import logging
import argparse
import socket
from typing import Optional

from smarthome_bridge.bridge import Bridge

from network.mqtt_credentials_container import MqttCredentialsContainer
from network.mqtt_connector import MQTTConnector
from network.rest_server import RestServer

from gadget_publishers.homebridge_network_connector import HomebridgeNetworkConnector
from gadget_publishers.gadget_publisher_homebridge import GadgetPublisherHomeBridge


def get_sender() -> str:
    """Returns the name used as sender (local hostname)"""
    return socket.gethostname()


def parse_args():
    # Argument-parser
    parser = argparse.ArgumentParser(description='Smarthome Bridge')
    parser.add_argument('--bridge_name', help='Network Name for the Bridge', type=str)
    parser.add_argument('--mqtt_ip', help='IP of the MQTT Broker', type=str)
    parser.add_argument('--mqtt_port', help='Port of the MQTT Broker', type=int)
    parser.add_argument('--mqtt_user', help='Username for the MQTT Broker', type=Optional[str], default=None)
    parser.add_argument('--mqtt_pw', help='Password for the MQTT Broker', type=Optional[str], default=None)
    parser.add_argument('--dummy_data', help='Adds dummy data for debugging.', action="store_true")
    parser.add_argument('--api_port', help='Port for the REST-API', type=int)
    parser.add_argument('--socket_port', help='Port for the Socket Server', type=int)
    parser.add_argument('--serial_baudrate', help='Baudrate of the Serial Server', type=int)
    args = parser.parse_args()
    return args


def main():
    args = parse_args()

    if args.bridge_name:
        bridge_name = args.bridge_name
    else:
        bridge_name = get_sender()

    # Create Bridge
    bridge = Bridge(bridge_name)

    # MQTT
    mqtt_credentials = None
    if args.mqtt_ip and args.mqtt_port:
        mqtt_credentials = MqttCredentialsContainer(args.mqtt_ip, args.mqtt_port, args.mqtt_user, args.mqtt_pw)
        mqtt = MQTTConnector(bridge_name, mqtt_credentials, "smarthome")
        bridge.get_network_manager().add_connector(mqtt)

    # REST
    if args.api_port:
        rest_server = RestServer(bridge_name, args.api_port)
        bridge.get_network_manager().add_connector(rest_server)

    # SOCKET
    if args.socket_port:
        pass
        # socket_connector = SocketServer(bridge_name, args.socket_port)
        # bridge.get_network_manager().add_connector(socket_connector)

    # SERIAL
    if args.serial_baudrate:
        pass
        # serial = SerialServer(bridge_name, args.serial_baudrate)
        # bridge.get_network_manager().add_connector(serial)

    # HOMEBRIDGE GADGET PUBLISHER
    if mqtt_credentials:
        hb_network = HomebridgeNetworkConnector(bridge_name, mqtt_credentials, 3)
        hb_publisher = GadgetPublisherHomeBridge(hb_network)
        bridge.get_gadget_manager().add_gadget_publisher(hb_publisher)

    # Insert dummy data if wanted
    if args.dummy_data:
        from gadgets.fan_westinghouse_ir import FanWestinghouseIR
        from smarthome_bridge.characteristic import Characteristic, CharacteristicIdentifier
        from smarthome_bridge.client import Client
        from gadgets.gadget_event_mapping import GadgetEventMapping
        from datetime import datetime

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

    while True:
        pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    main()
