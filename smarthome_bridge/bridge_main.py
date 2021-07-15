import logging
import argparse

from smarthome_bridge.bridge import Bridge


def parse_args():
    # Argument-parser
    parser = argparse.ArgumentParser(description='Smarthome Bridge')
    parser.add_argument('--bridge_name', help='Network Name for the Bridge', type=str)
    parser.add_argument('--mqtt_ip', help='IP of the MQTT Broker', type=str)
    parser.add_argument('--mqtt_port', help='Port of the MQTT Broker', type=int)
    parser.add_argument('--mqtt_user', help='Username for the MQTT Broker', type=str)
    parser.add_argument('--mqtt_pw', help='mPassword for the MQTT Broker', type=str)
    parser.add_argument('--dummy_data', help='Adds dummy data for debugging.', action="store_true")
    parser.add_argument('--api_port', help='Port for the REST-API', type=int)
    parser.add_argument('--socket_port', help='Port for the Socket Server', type=int)
    args = parser.parse_args()
    return args


def main():
    args = parse_args()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    main()
