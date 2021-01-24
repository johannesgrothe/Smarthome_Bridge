from mqtt_connector import MQTTConnector
from serial_connector import SerialConnector


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


if __name__ == '__main__':
    # test_mqtt_connector()
    test_serial_connector()
