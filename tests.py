from mqtt_connector import MQTTConnector


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


if __name__ == '__main__':
    test_mqtt_connector()
