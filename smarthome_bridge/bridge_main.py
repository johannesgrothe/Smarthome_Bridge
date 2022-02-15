import logging
import argparse
import socket
from typing import Optional

from smarthome_bridge.bridge_launcher import BridgeLauncher
from network.mqtt_credentials_container import MqttCredentialsContainer


_default_user_default_username = "debug_admin"


def get_sender() -> str:
    """Returns the name used as sender (local hostname)"""
    return socket.gethostname()


def parse_args():
    # Argument-parser
    parser = argparse.ArgumentParser(description='Smarthome Bridge')
    parser.add_argument('--bridge_name',
                        help='Network Name for the Bridge',
                        type=str,
                        default=get_sender())

    parser.add_argument('--mqtt_ip',
                        help='IP of the MQTT Broker',
                        type=str)
    parser.add_argument('--mqtt_port',
                        help='Port of the MQTT Broker',
                        type=int)
    parser.add_argument('--mqtt_user',
                        help='Username for the MQTT Broker',
                        type=Optional[str],
                        default=None)
    parser.add_argument('--mqtt_pw',
                        help='Password for the MQTT Broker',
                        type=Optional[str],
                        default=None)

    parser.add_argument('--api_port',
                        help='Port for the REST-API',
                        type=int)
    parser.add_argument('--socket_port',
                        help='Port for the Socket Server',
                        type=int)
    parser.add_argument('--serial',
                        help='Whether serial connector should be active',
                        type=bool,
                        action="store_true")

    parser.add_argument('--static_user_name',
                        help='Sets the username for the default user',
                        type=str,
                        default=_default_user_default_username)
    parser.add_argument('--static_user_password',
                        help=f'Create user (default name: "{_default_user_default_username}") with set pw',
                        type=str)

    parser.add_argument('--dummy_data',
                        help='Adds dummy data for debugging.',
                        type=bool,
                        action="store_true")

    parser.add_argument('--logging', help='Log-Level to be set', type=str, default="INFO",
                        choices=["DEBUG", "INFO", "ERROR"])
    args = parser.parse_args()
    return args


def main():
    args = parse_args()

    if args.logging == "DEBUG":
        log = logging.DEBUG
    elif args.logging == "INFO":
        log = logging.INFO
    else:
        log = logging.ERROR
    logging.basicConfig(level=log, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # MQTT
    mqtt_credentials = None
    if args.mqtt_ip and args.mqtt_port:
        mqtt_credentials = MqttCredentialsContainer(args.mqtt_ip, args.mqtt_port, args.mqtt_user, args.mqtt_pw)

    # DEFAULT USER
    user_data = None
    if args.static_user_password:
        user_data = (args.static_user_name, args.static_user_password)

    launcher = BridgeLauncher()

    launcher.launch(name=args.bridge_name,
                    mqtt=mqtt_credentials,
                    api_port=args.api_port,
                    socket_port=args.socket_port,
                    serial_active=args.serial,
                    static_user_data=user_data,
                    add_dummy_data=args.dummy_data)

    while True:
        pass


if __name__ == "__main__":
    main()
