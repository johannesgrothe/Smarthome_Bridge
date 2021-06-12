import logging
from network_connector import NetworkConnector, Request, response_callback_type
from typing import Optional, Callable
import paho.mqtt.client as mqtt
import json
from jsonschema import ValidationError


class MQTTConnector(NetworkConnector):
    """Class to implement a MQTT connection module"""

    __client: mqtt.Client
    __ip: str
    __port: int

    __mqtt_username: Optional[str]
    __mqtt_password: Optional[str]

    def __init__(self, own_name: str, mqtt_ip: str, mqtt_port: int, mqtt_user: Optional[str] = None,
                 mqtt_pw: Optional[str] = None):
        super().__init__(own_name)
        self.__client = mqtt.Client(self._name)
        self.__ip = mqtt_ip
        self.__port = mqtt_port
        self.__mqtt_username = mqtt_user
        self.__mqtt_password = mqtt_pw

        if self.__mqtt_username and self.__mqtt_password:
            self.__client.username_pw_set(self.__mqtt_username, self.__mqtt_password)
        try:
            self.__client.on_message = self.generate_callback(self._validate_request,
                                                              self._logger,
                                                              self._respond_to,
                                                              self._handle_request)
            self.__client.on_disconnect = self.generate_disconnect_callback(self._logger)
            self.__client.on_connect = self.generate_connect_callback(self._logger)

            try:
                self.__client.connect(self.__ip, self.__port, 10)
            except OSError:
                self._logger.error("Could not connect to MQTT Server.")

            self.__client.loop_start()
            self.__client.subscribe("smarthome/#")
            self._thread_manager.start_threads()

        except ConnectionRefusedError as err:
            self._logger.error(err)

    def __del__(self):
        super().__del__()
        self.__client.disconnect()

    @staticmethod
    def generate_callback(validate_function: Callable, logger: logging.Logger, respond_method, handler_function):
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
                validate_function(body)
            except ValidationError:
                logger.warning("Could not decode Request, Schema Validation failed.")

            try:
                inc_req = Request(topic,
                                  body["session_id"],
                                  body["sender"],
                                  body["receiver"],
                                  body["payload"])
                inc_req.set_callback_method(respond_method)

                handler_function(inc_req)

            except ValueError:
                logger.error("Error creating Request")

        # Return closured callback
        return buf_callback

    @staticmethod
    def generate_connect_callback(logger: logging.Logger):

        def connect_callback(client, userdata, reasonCode, properties=None):
            logger.info("MQTT connected.")

        return connect_callback

    @staticmethod
    def generate_disconnect_callback(logger: logging.Logger):

        def disconnect_callback(client, userdata, reasonCode, properties=None):
            logger.info("MQTT disconnected.")

        return disconnect_callback

    def _send_data(self, req: Request):
        self.__client.publish(req.get_path(), json.dumps(req.get_body()))
