import unittest
from serial_connector import SerialConnector
from time import sleep

from mqtt_echo_client import MQTTTestEchoClient
from mqtt_connector import MQTTConnector, Request

# Data for the MQTT Broker
BROKER_IP = "192.168.178.111"
BROKER_PORT = 1883
BROKER_USER = None
BROKER_PW = None


def test_mqtt_connector():
    connector = MQTTConnector("tester",
                              "192.168.178.111",
                              1883,
                              None,
                              None)

    i = 0

    while i < 5:
        buf_req = connector.get_request()
        if buf_req:
            print(buf_req.get_body())
            i += 1


def test_serial_connector():
    serial_port = "/dev/cu.SLAB_USBtoUART"

    connector = SerialConnector(
        "tester",
        serial_port,
        115200
    )

    if connector.connected():
        print("Connected!")
    else:
        print("NOT Connected!")


class BridgeUnitTest(unittest.TestCase):
    # return True or False
    def base_test(self):
        self.assertTrue(True)

    def test_mqtt_connector(self):
        connector = MQTTConnector("tester",
                                  "localhost",
                                  133,
                                  None,
                                  None)
        self.assertTrue(not connector.connected())

    def test_mqtt_connector_messages(self):
        self.assertTrue(mqtt_test())

    def test_mqtt_connector_messages_split(self):
        self.assertTrue(mqtt_test_split())


def mqtt_test() -> bool:
    # Start Responder
    responder = MQTTTestEchoClient(BROKER_IP,
                                   BROKER_PORT,
                                   BROKER_USER,
                                   BROKER_PW)

    connector = MQTTConnector("tester",
                              BROKER_IP,
                              BROKER_PORT,
                              BROKER_USER,
                              BROKER_PW)

    # if not connector.connected():
    #     return False

    out_payload = {"test": "main", "value": 55.6}
    out_req = Request("smarthome/test", 1334544, "tester", responder.get_name(), out_payload)

    res_ack, in_req = connector.send_request(out_req, timeout=2)

    if in_req is None:
        return False

    in_payload = in_req.get_payload()

    if in_payload != out_payload:
        return False

    return True


def mqtt_test_split() -> bool:
    # Start Responder
    responder = MQTTTestEchoClient(BROKER_IP,
                                   BROKER_PORT,
                                   BROKER_USER,
                                   BROKER_PW)

    connector = MQTTConnector("tester",
                              BROKER_IP,
                              BROKER_PORT,
                              BROKER_USER,
                              BROKER_PW)

    # if not connector.connected():
    #     return False

    out_payload = {"test": "main long test",
                   "value": 55.6,
                   "more_data": 12223222332423}
    out_req = Request("smarthome/test", 1334544, "tester", responder.get_name(), out_payload)

    res_ack, in_req = connector.send_request_split(out_req, timeout=2, part_max_size=15)

    if in_req is None:
        return False

    in_payload = in_req.get_payload()

    if in_payload != out_payload:
        return False

    return True


if __name__ == '__main__':

    unittest.main()

    print("All Tests Passed.")
