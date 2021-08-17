import json
import threading
import random
import paho.mqtt.client as mqtt
from queue import Queue
from datetime import timedelta, datetime
from typing import Optional, Callable

from logging_interface import LoggingInterface
from network.mqtt_credentials_container import MqttCredentialsContainer
from smarthome_bridge.gadget_publishers.homebridge_request import HomeBridgeRequest
from smarthome_bridge.gadgets.gadget import Gadget
from smarthome_bridge.gadget_publishers.homebridge_encoder import HomebridgeEncoder, GadgetEncodeError
from thread_manager import ThreadManager


class MqttConnectionError(Exception):
    def __init__(self, ip: str, port: int):
        super().__init__(f"Cannot connect to mqtt server {ip}:{port}")


class NoResponseError(Exception):
    def __init__(self, req: HomeBridgeRequest):
        super().__init__(f"Received no response to '{req.topic}': {req.message}")


class NoAckError(Exception):
    def __init__(self, req: HomeBridgeRequest):
        super().__init__(f"Received a response with no 'ack' flag from '{req.topic}': {req.message}")


class AckFalseError(Exception):
    def __init__(self, req: HomeBridgeRequest):
        super().__init__(f"Received a 'False' ack flag from '{req.topic}': {req.message}")


CharacteristicUpdateCallback = Callable[[str, str, int], None]


class HomebridgeNetworkConnector(LoggingInterface):

    _send_lock: threading.Lock
    _network_name: str
    _mqtt_client = mqtt.Client
    _mqtt_credentials: MqttCredentialsContainer

    _received_responses: Queue
    _received_messages: Queue
    _response_timeout: Optional[int]

    _thread_manager: ThreadManager

    _characteristic_update_callback: Optional[CharacteristicUpdateCallback]

    def __init__(self, network_name: str, mqtt_credentials: MqttCredentialsContainer,
                 response_timeout: Optional[int] = None):
        super().__init__()
        self._response_timeout = response_timeout
        self._send_lock = threading.Lock()
        self._network_name = network_name
        self._mqtt_credentials = mqtt_credentials
        self._characteristic_update_callback = None
        self._received_responses = Queue()
        self._received_messages = Queue()

        self._mqtt_client = mqtt.Client(self._network_name + "_HomeBridge")
        self._logger.info("Connecting to homebridge mqtt broker")
        if self._mqtt_credentials.has_auth():
            self._mqtt_client.username_pw_set(self._mqtt_credentials.username, self._mqtt_credentials.password)
            self._logger.info("Using auth for mqtt connection")
        try:
            self._mqtt_client.connect(self._mqtt_credentials.ip, self._mqtt_credentials.port, 15)
        except OSError:
            raise MqttConnectionError(self._mqtt_credentials.ip, self._mqtt_credentials.port)
        self._mqtt_client.on_message = self._gen_message_handler()
        self._mqtt_client.subscribe("homebridge/from/response")
        self._mqtt_client.subscribe("homebridge/from/set")
        self._mqtt_client.loop_start()

        self._thread_manager = ThreadManager()
        self._thread_manager.add_thread("received_request_handler", self._request_handler_thread)
        self._thread_manager.start_threads()

    def __del__(self):
        self._thread_manager.__del__()
        self._mqtt_client.disconnect()
        self._mqtt_client.__del__()

    def _gen_message_handler(self):
        """
        Generates a response method to attach to the mqtt-connector as 'on_message' callback

        :return: The function handler
        """
        def on_message(client, userdata, message):
            self._logger.info(f"Received message at {message.topic}")
            topic = message.topic
            json_str = message.payload.decode("utf-8")

            try:
                body = json.loads(json_str)
            except json.decoder.JSONDecodeError:
                self._logger.error("Couldn't decode json: '{}'".format(json_str))
                return

            buf_req = HomeBridgeRequest(topic, body)
            if buf_req.topic == "homebridge/from/response":
                self._received_responses.put(buf_req)
            else:
                self._received_messages.put(buf_req)
        return on_message

    def _request_handler_thread(self):
        if not self._received_messages.empty():
            req = self._received_messages.get()
            self._handle_request(req)

    def _handle_request(self, req: HomeBridgeRequest):
        """
        Handles a request received by the mqtt client

        :param req: Request to handle
        :return: None
        """
        # Check handle characteristic updates
        if req.topic == "homebridge/from/set":
            # TODO: validate with json schema
            if self._characteristic_update_callback:
                self._characteristic_update_callback(req.message["name"],
                                                     req.message["characteristic"],
                                                     req.message["value"])

    def _send_request(self, req: HomeBridgeRequest, wait_for_response: Optional[int] = None) ->\
            Optional[HomeBridgeRequest]:
        """
        Sends a homebridge request and waits for an answer if wanted

        :param req: Request to be sent
        :param wait_for_response: The time that should be waited to receive an response before NoResponseError is raised
        :return: The response that was received
        :raises AckFalseError: If wait_for_response != None and ack 'False' was sent back
        :raises NoResponseError: If wait_for_response != None and no response was received
        """
        with self._send_lock:
            req_id = random.randint(0, 10000)
            if wait_for_response is not None:
                req.set_request_id(req_id)
                self._received_responses = Queue()
            info = self._mqtt_client.publish(topic=req.topic, payload=json.dumps(req.message))
            info.wait_for_publish()
            if wait_for_response is None:
                return None
            else:
                start_time = datetime.now()
                while start_time + timedelta(seconds=wait_for_response) > datetime.now():
                    if not self._received_responses.empty():
                        res: HomeBridgeRequest = self._received_responses.get()
                        if res.get_request_id() == req_id:
                            return res
                raise NoResponseError(req)

    def attach_characteristic_update_callback(self, callback: CharacteristicUpdateCallback):
        """
        Attaches a callback to the connector to receive characteristic updates triggered on the external data source

        :param callback: Callback function to attach
        :return: None
        """
        self._characteristic_update_callback = callback

    def add_gadget(self, gadget: Gadget) -> bool:
        try:
            buf_payload = HomebridgeEncoder().encode_gadget(gadget)
        except GadgetEncodeError as err:
            self._logger.error(err.args[0])
            return False
        buf_req = HomeBridgeRequest("homebridge/to/add", buf_payload)
        try:
            response = self._send_request(buf_req, self._response_timeout)
            if response.get_ack() is True:
                return True
            return False
        except NoResponseError as err:
            self._logger.error(err.args[0])
            return False

    def remove_gadget(self, gadget_name: str) -> bool:
        """
        Removes the gadget from the external data source

        :param gadget_name: Name of the gadget that should be deleted
        :return: Whether deleting the gadget was successful or not
        """
        buf_req = HomeBridgeRequest("homebridge/to/remove", {"name": gadget_name})
        try:
            response = self._send_request(buf_req, self._response_timeout)
            if response.get_ack() is True:
                return True
            return False
        except NoResponseError as err:
            self._logger.error(err.args[0])
            return False

    def get_gadget_info(self, gadget_name: str) -> Optional[dict]:
        """
        Gets information about the selected gadget from the external source

        :param gadget_name: Name of the gadget to get information for
        :return: The information received about the gadget
        """
        buf_req = HomeBridgeRequest("homebridge/to/get", {"name": "*_props"})
        try:
            response = self._send_request(buf_req, self._response_timeout)
            if gadget_name not in response.message:
                return None
            return response.message[gadget_name]
        except NoResponseError as err:
            self._logger.error(err.args[0])
            return None

    def update_characteristic(self, gadget_name: str, characteristic: str, value: int):
        """
        Updates a characteristic of the selected gadget on the external data source

        :param gadget_name: Name of the gadget the characteristic belongs to
        :param characteristic: The characteristic to change
        :param value: The new value of the characteristic
        :return: Whether the change of the characteristic was successful or not
        """
        buf_payload = {"name": gadget_name,
                       "service_name": gadget_name,
                       "characteristic": characteristic,
                       "value": value}
        buf_req = HomeBridgeRequest("homebridge/to/set", buf_payload)
        self._send_request(buf_req, None)
