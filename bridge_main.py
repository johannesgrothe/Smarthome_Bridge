import logging
import argparse
import os
import socket
from typing import Optional, Tuple
from dotenv import load_dotenv

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
                        type=str)

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
                        action="store_true")

    parser.add_argument('--homekit_active',
                        help='Activates the homekit connector.',
                        action="store_true")

    parser.add_argument('--logging', help='Log-Level to be set', type=str, default="INFO",
                        choices=["DEBUG", "INFO", "ERROR"])
    args = parser.parse_args()
    return args


def load_parameters() -> Tuple[dict, argparse.Namespace]:
    args = parse_args()
    load_dotenv()
    out_data = {}
    for arg_name, argparse_val, env_key, param_type in [
        ("log_lvl", args.logging, "LOG_LEVEL", str),
        ("bridge_name", args.bridge_name, "BRIDGE_NAME", str),
        ("mqtt_ip", args.mqtt_ip, "MQTT_IP", str),
        ("mqtt_port", args.mqtt_port, "MQTT_PORT", int),
        ("mqtt_user", args.mqtt_user, "MQTT_USERNAME", str),
        ("mqtt_pw", args.mqtt_pw, "MQTT_PASSWORD", str),
        ("rest_port", args.api_port, "REST_API_PORT", int),
        ("socket_port", args.socket_port, "SOCKET_API_PORT", int),
        ("serial_active", args.serial, "SERIAL_ACTIVE", bool),
        ("homekit_active", args.homekit_active, "HOMEKIT_ACTIVE", bool)
    ]:
        buf_val = argparse_val
        if buf_val is None or (buf_val is False and param_type is bool):
            env_val = os.getenv(env_key)
            if env_val is not None:
                if param_type == bool:
                    if env_val in ["true", "True", "TRUE"]:
                        buf_val = True
                    else:
                        buf_val = False
                else:
                    buf_val = param_type(env_val)
        out_data[arg_name] = buf_val
    return out_data, args


def main():
    params, args = load_parameters()

    if params["log_lvl"] == "DEBUG":
        log = logging.DEBUG
    elif params["log_lvl"] == "INFO":
        log = logging.INFO
    else:
        log = logging.ERROR
    logging.basicConfig(level=log, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # NAME
    bridge_name = params["bridge_name"]
    if bridge_name is None:
        bridge_name = get_sender()

    # MQTT
    mqtt_credentials = None
    mqtt_ip = params["mqtt_ip"]
    mqtt_port = params["mqtt_port"]
    if mqtt_ip and mqtt_port:
        mqtt_credentials = MqttCredentialsContainer(mqtt_ip, mqtt_port,
                                                    params["mqtt_user"], params["mqtt_pw"])

    # DEFAULT USER
    user_data = None
    if args.static_user_password:
        user_data = (args.static_user_name, args.static_user_password)

    # HOMEKIT
    homekit_active = params["homekit_active"]
    if homekit_active is None:
        homekit_active = False

    # Serial
    serial_active = params["serial_active"]
    if serial_active is None:
        serial_active = False

    launcher = BridgeLauncher()

    launcher.launch(name=bridge_name,
                    mqtt=mqtt_credentials,
                    api_port=params["rest_port"],
                    socket_port=params["socket_port"],
                    serial_active=serial_active,
                    static_user_data=user_data,
                    homekit_active=homekit_active,
                    add_dummy_data=args.dummy_data)

    while True:
        pass


if __name__ == "__main__":
    main()
