import unittest
import json
from mqtt_connector import MQTTConnector, Request

from mqtt_connector_tests import request_long

# Data for the MQTT Broker
BROKER_IP = "192.168.178.111"
BROKER_PORT = 1883
BROKER_USER = None
BROKER_PW = None


class ClientTest(unittest.TestCase):
    # return True or False
    def base_test(self):
        self.assertTrue(True)

    def split_req_test(self):
        print("Testing")
        self.assertTrue(False)


if __name__ == '__main__':
    print("Launching")

    k_gadget = MQTTConnector("tester",
                             BROKER_IP,
                             BROKER_PORT,
                             BROKER_USER,
                             BROKER_PW)

    with open("../configs/testconfig.json", "r") as file_h:
        config_data = json.load(file_h)

        k_req = Request("smarthome/config/write",
                        12345678,
                        "tester",
                        "YoloChip14",
                        {"type": "complete",
                         "reset_config": True,
                         "reset_gadgets": True,
                         "config": config_data})

        success, resp = k_gadget.send_request_split(k_req,
                                                    50,
                                                    5)
        print(resp)

        print(success)
