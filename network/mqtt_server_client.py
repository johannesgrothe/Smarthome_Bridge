import json
from queue import Queue
from typing import Optional

from jsonschema import ValidationError

from network.network_connector import REQ_VALIDATION_SCHEME_NAME
from network.request import Request
from network.network_server import NetworkServerClient
import paho.mqtt.client as mqtt


class MQTTServerClient(NetworkServerClient):
    _client: mqtt.Client
    _buf_queue: Queue
    _channel: str

    def __init__(self, host_name: str, address: str, mqtt_client: mqtt.Client, channel: str):
        super().__init__(host_name, address)
        self._buf_queue = Queue()
        self._channel = channel
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

        def buf_callback(client, userdata, message):
            """Callback to attach to mqtt object, mqtt_res_queue gets catched in closure"""
            topic = message.topic

            try:
                # json_str = message.payload.decode("utf-8").replace("'", '"').replace("None", "null")
                json_str = message.payload.decode("utf-8")

            except UnicodeDecodeError:
                self._logger.warning("Couldn't format json string")
                return

            try:
                body = json.loads(json_str)
            except json.decoder.JSONDecodeError:
                self._logger.warning("Couldn't decode json: '{}'".format(json_str))
                return

            try:
                self._validator.validate(body, REQ_VALIDATION_SCHEME_NAME)
            except ValidationError:
                self._logger.warning("Could not decode Request, Schema Validation failed.")

            topic_without_channel = topic[len(self._channel):].strip("/")

            try:
                inc_req = Request(topic_without_channel,
                                  body["session_id"],
                                  body["sender"],
                                  body["receiver"],
                                  body["payload"],
                                  connection_type=f"MQTT")
                inc_req.set_callback_method(self._respond_to)

                self._add_req_to_queue(inc_req)

            except ValueError:
                self._logger.error("Error creating Request")

        # Return callback
        return buf_callback

    def generate_connect_callback(self):
        def connect_callback(client, userdata, reasonCode, properties=None):
            self._logger.info("MQTT connected.")

        return connect_callback

    def generate_disconnect_callback(self):
        def disconnect_callback(client, userdata, reasonCode, properties=None):
            self._logger.info("MQTT disconnected.")

        return disconnect_callback

    def _send(self, req: Request):
        topic_with_channel = f"{self._channel}/{req.get_path().strip('/')}"
        self._client.publish(topic_with_channel, json.dumps(req.get_body()))

    def _receive(self) -> Optional[Request]:
        if not self._buf_queue.empty():
            buf_req = self._buf_queue.get()
            return buf_req
        return None

    def is_connected(self) -> bool:
        return self._client.is_connected()
