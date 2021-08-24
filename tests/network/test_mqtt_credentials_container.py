import pytest

from network.mqtt_credentials_container import MqttCredentialsContainer, MqttCredentialsError


def test_mqtt_credentials_container():
    with pytest.raises(MqttCredentialsError):
        MqttCredentialsContainer(None, 1883)

    with pytest.raises(MqttCredentialsError):
        MqttCredentialsContainer("yolokopter", 1883)

    with pytest.raises(MqttCredentialsError):
        MqttCredentialsContainer("192.168.178", 1883)

    with pytest.raises(MqttCredentialsError):
        MqttCredentialsContainer("192.168.-5.44", 1883)

    with pytest.raises(MqttCredentialsError):
        MqttCredentialsContainer("192.168.111.256", 1883)

    with pytest.raises(MqttCredentialsError):
        MqttCredentialsContainer("192.168.111.256", -5)

    with pytest.raises(MqttCredentialsError):
        MqttCredentialsContainer("192.168.111.256", "yolo")

    assert MqttCredentialsContainer("192.168.178.111", 1883).has_auth() is False

    assert MqttCredentialsContainer("192.168.178.111", 1883, username="yolo").has_auth() is False

    assert MqttCredentialsContainer("192.168.178.111", 1883, password="yolo").has_auth() is False

    assert MqttCredentialsContainer("192.168.178.111", 1883, "yolo", "kopter").has_auth() is True
