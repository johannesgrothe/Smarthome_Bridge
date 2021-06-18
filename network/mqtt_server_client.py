import json
from queue import Queue
from typing import Optional

from jsonschema import ValidationError

from network.network_connector import req_validation_scheme_name
from network.request import Request
from network.network_server import NetworkServerClient
import paho.mqtt.client as mqtt


class MQTTServerClient(NetworkServerClient):

    _client: mqtt.Client
    _buf_queue: Queue

    def __init__(self, host_name: str, address: str, mqtt_client: mqtt.Client):
        super().__init__(host_name, address)
        self._buf_queue = Queue()
        self._client = mqtt_client
        self._client.on_message = self.generate_callback()
        self._client.on_disconnect = self.generate_disconnect_callback()
        self._client.on_connect = self.generate_connect_callback()
        self._thread_manager.start_threads()

    def __del__(self):
        super().__del__()
        self._client.disconnect()

    def _add_req_to_queue(self, req: Request):
        self._buf_queue.put(req)

    def generate_callback(self):
        """Generates a callback with captured queue"""

        logger = self._logger
        respond_method = self._respond_to
        handler_function = self._add_req_to_queue
        validator = self._validator

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
                validator.validate(body, req_validation_scheme_name)
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

        # Return callback
        return buf_callback

    def generate_connect_callback(self):
        logger = self._logger

        def connect_callback(client, userdata, reasonCode, properties=None):
            logger.info("MQTT connected.")

        return connect_callback

    def generate_disconnect_callback(self):
        logger = self._logger

        def disconnect_callback(client, userdata, reasonCode, properties=None):
            logger.info("MQTT disconnected.")

        return disconnect_callback

    def _send(self, req: Request):
        self._client.publish(req.get_path(), json.dumps(req.get_body()))

    def _receive(self) -> Optional[Request]:
        if not self._buf_queue.empty():
            buf_req = self._buf_queue.get()
            return buf_req
        return None

    def is_connected(self) -> bool:
        return self._client.is_connected()
