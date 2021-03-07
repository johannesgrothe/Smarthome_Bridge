import unittest
from mqtt_connector import MQTTConnector, Request

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

    k_req = Request("smarthome/test",
                    12345678,
                    "tester",
                    "YoloChip14",
                    {"yolokopter": 1234, "tester": "longteststringfortestingpurposes"})

    k_gadget.send_request_split(k_req,
                                20,
                                0)
