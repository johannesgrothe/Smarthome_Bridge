import unittest
from mqtt_connector import MQTTConnector
from serial_connector import SerialConnector
from time import sleep


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


class SampleTest(unittest.TestCase):
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

    def test_mqtt_connector_2(self):
        connector = MQTTConnector("tester",
                                  "192.168.178.111",
                                  1883,
                                  None,
                                  None)
        sleep(1)
        self.assertTrue(connector.connected())


if __name__ == '__main__':
    # test_mqtt_connector()
    # test_serial_connector()
    unittest.main()
