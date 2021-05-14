import logging

from network_connector import NetworkConnector, Request
from network_connector_threaded import ThreadedNetworkConnector
from typing import Optional
from queue import Queue
import paho.mqtt.client as mqtt
import time
import json
from jsonschema import validate, ValidationError


class MQTTConnector(ThreadedNetworkConnector):
    """Class to implement a MQTT connection module"""

    __client: mqtt.Client
    __own_name: str
    __ip: str
    __port: int

    __mqtt_username: Optional[str]
    __mqtt_password: Optional[str]

    __buf_queue: Queue

    def __init__(self, own_name: str, mqtt_ip: str, mqtt_port: int, mqtt_user: Optional[str] = None,
                 mqtt_pw: Optional[str] = None):
        super().__init__()
        self.__own_name = own_name
        self.__client = mqtt.Client(self.__own_name)
        self.__ip = mqtt_ip
        self.__port = mqtt_port
        self.__mqtt_username = mqtt_user
        self.__mqtt_password = mqtt_pw

        self.__buf_queue = Queue()

        if self.__mqtt_username and self.__mqtt_password:
            self.__client.username_pw_set(self.__mqtt_username, self.__mqtt_password)
        try:
            self.__client.on_message = self.generate_callback(self.__buf_queue,
                                                              self._request_validation_schema,
                                                              self._logger)
            self.__client.on_disconnect = self.generate_disconnect_callback(self._logger)
            self.__client.on_connect = self.generate_connect_callback(self._logger)

            try:
                self.__client.connect(self.__ip, self.__port, 10)
            except OSError:
                print("Could not connect to MQTT Server.")

            self.__client.loop_start()
            self.__client.subscribe("smarthome/#")
            self._start_thread()

        except ConnectionRefusedError as err:
            print(err)

    def __del__(self):
        super().__del__()
        self.__client.disconnect()

    @staticmethod
    def generate_callback(request_queue: Queue, request_schema: dict, logger: logging.Logger):
        """Generates a callback with captured queue"""

        def buf_callback(client, userdata, message):
            """Callback to attach to mqtt object, mqtt_res_queue gets catched in closure"""
            topic = message.topic

            try:
                json_str = message.payload.decode("utf-8").replace("'", '"').replace("None", "null")
            except UnicodeDecodeError:
                logger.warning("Couldn't format json string")
                return

            try:
                body = json.loads(json_str)
            except json.decoder.JSONDecodeError:
                logger.warning("Couldn't decode json: '{}'".format(json_str))
                return

            try:
                validate(body, request_schema)
            except ValidationError:
                logger.warning("Could not decode Request, Schema Validation failed.")

            try:
                inc_req = Request(topic,
                                  body["session_id"],
                                  body["sender"],
                                  body["receiver"],
                                  body["payload"])
                # print("Received: {}".format(inc_req.to_string()))

                request_queue.put(inc_req)

            except ValueError:
                logger.error("Error creating Request")

        # Return closured callback
        return buf_callback

    @staticmethod
    def generate_connect_callback(logger: logging.Logger):

        def connect_callback(client, userdata, flags, reason_code, properties=None):
            logger.info("MQTT connected.")

        return connect_callback

    @staticmethod
    def generate_disconnect_callback(logger: logging.Logger):

        def disconnect_callback(client, userdata, flags, reason_code, properties=None):
            logger.info("MQTT disconnected.")

        return disconnect_callback

    def _receive_data(self) -> Optional[Request]:
        if not self.__buf_queue.empty():
            return self.__buf_queue.get()
        return None

    def _send_data(self, req: Request):
        self.__client.publish(req.get_path(), json.dumps(req.get_body()))

    def connected(self) -> bool:
        return self.__client.is_connected()


if __name__ == '__main__':
    import sys

    ip = "192.168.178.111"
    port = 1883
    try:
        mqtt_gadget = MQTTConnector("TesTeR", ip, port)
    except OSError as e:
        print("Cannot connect to '{}:{}'".format(ip, port))
        sys.exit(1)

    buf_req = Request("smarthome/debug",
                      125543,
                      "me",
                      "you",
                      {"yolo": "hallo"})

    mqtt_gadget.send_request(buf_req)
