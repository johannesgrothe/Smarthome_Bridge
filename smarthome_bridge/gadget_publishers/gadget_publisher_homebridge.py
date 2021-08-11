import json
import threading
import random
from queue import Queue
import paho.mqtt.client as mqtt
from typing import Optional
from datetime import timedelta, datetime

from gadgetlib import CharacteristicIdentifier
from smarthome_bridge.gadget_publishers.gadget_publisher import GadgetPublisher, Gadget,\
    GadgetIdentifier, GadgetUpdateConnector
from network.mqtt_credentials_container import MqttCredentialsContainer


# https://www.npmjs.com/package/homebridge-mqtt
# https://github.com/homebridge/HAP-NodeJS/blob/master/src/lib/definitions/ServiceDefinitions.ts
# https://github.com/homebridge/HAP-NodeJS/blob/master/src/lib/definitions/CharacteristicDefinitions.ts


class HomeBridgeRequest:
    topic: str
    message: dict

    def __init__(self, topic: str, message: dict):
        self.topic = topic
        self.message = message
        if "request_id" not in self.message:
            self.message["request_id"] = 0

    def set_request_id(self, req_id: int):
        self.message["request_id"] = req_id

    def get_request_id(self) -> int:
        return self.message["request_id"]

    def get_ack(self) -> Optional[bool]:
        if "ack" not in self.message:
            return None
        return self.message["ack"]


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


class GadgetPublisherHomeBridge(GadgetPublisher):

    _send_lock: threading.Lock
    _network_name: str
    _mqtt_client = mqtt.Client
    _mqtt_credentials: MqttCredentialsContainer

    _received_responses: Queue


    def __init__(self, update_connector: GadgetUpdateConnector, network_name: str,
                 mqtt_credentials: MqttCredentialsContainer):
        super().__init__(update_connector)
        self._send_lock = threading.Lock()
        self._network_name = network_name
        self._mqtt_credentials = mqtt_credentials
        self._mqtt_client = mqtt.Client(self._network_name + "_HomeBridge")

        self._logger.info("Connecting to homebridge mqtt broker")
        if self._mqtt_credentials.has_auth():
            self._mqtt_client.username_pw_set(self._mqtt_credentials.username, self._mqtt_credentials.password)
            self._logger.info("Using auth for mqtt connection")
        try:
            self._mqtt_client.connect(self._mqtt_credentials.ip, self._mqtt_credentials.port, 15)
        except OSError:
            raise MqttConnectionError(self._mqtt_credentials.ip, self._mqtt_credentials.port)
        self._mqtt_client.loop_start()
        self._mqtt_client.on_message = self._gen_message_handler()
        self._mqtt_client.subscribe("homebridge/#")

        self._received_responses: Queue

    def update_gadget(self, gadget: Gadget):
        pass

    def remove_gadget(self, gadget_name: str):
        """Removes a gadget from the homebridge remote"""
        buf_req = HomeBridgeRequest("homebridge/to/remove", {"name": gadget_name})
        self._send_request(buf_req)

    def handle_characteristic_update(self, gadget: Gadget, characteristic: CharacteristicIdentifier):
        pass

    def _execute_characteristic_update(self):

    def _gen_message_handler(self):
        def on_message(client, userdata, message):
            topic = message.topic
            json_str = message.payload.decode("utf-8")

            try:
                body = json.loads(json_str)
            except json.decoder.JSONDecodeError:
                self._logger.error("Couldn't decode json: '{}'".format(json_str))
                return

            buf_req = HomeBridgeRequest(topic, body)
            self._handle_request(buf_req)
        return on_message

    def _send_request(self, req: HomeBridgeRequest, wait_for_response: Optional[int] = None) -> HomeBridgeRequest:
        """
        Sends a homebridge request and waits for an answer if wanted

        :param req: Request to be sent
        :param wait_for_response: The time that should be waited to receive an response before NoResponseError is raised
        :return: None
        :raises AckFalseError: If wait_for_response != None and ack 'False' was sent back
        :raises NoResponseError: If wait_for_response != None and no response was received
        """
        with self._send_lock:
            req_id: random.randint(0, 10000)
            if wait_for_response is not None:
                req.set_request_id(req_id)
            self._mqtt_client.publish(req.topic, json.dumps(req.message))
            if wait_for_response is not None:
                start_time = datetime.now()
                self._received_responses = Queue()
                while start_time + timedelta(seconds=wait_for_response) > datetime.now():
                    if not self._received_responses.empty():
                        res: HomeBridgeRequest = self._received_responses.get()
                        if res.get_request_id() == req_id:
                            return res
                raise NoResponseError(req)

    def _load_gadget_data(self) -> list[Gadget]:
        sync_req = HomeBridgeRequest("homebridge/to/get", {"name": "*"})
        try:
            gadget_data = self._send_request(sync_req)
        except NoResponseError:
            self._logger.error("Cannot sync gadget data with homebridge")

    def _decode_gadget_from_json(self, name: str, data: dict):



    def _register_gadget(self, gadget: Gadget):
        """Registers a gadget on the homebridge remote"""

        # {"name": "flex_lamp", "service_name": "flex_lamp", "service": "Lightbulb",
        #  "Brightness": {"minValue": 0, "maxValue": 100, "minStep": 1},
        #  "Hue": {"minValue": 0, "maxValue": 360, "minStep": 1},
        #  "Saturation": {"minValue": 0, "maxValue": 100, "minStep": 1}}

        gadget_service = gadget_type_to_string(gadget.get_type())
        reg_dict = {"name": gadget.get_name(), "service_name": gadget_service, "service": gadget_service}
        topic = "homebridge/to/add"

        for characteristic in gadget.get_characteristic_types():
            characteristic_str = characteristic_type_to_string(characteristic)
            if characteristic_str:
                min_v, max_v, step_v = gadget.get_characteristic_options(characteristic)
                if min_v is not None:
                    reg_dict[characteristic_str] = {"minValue": min_v, "minVal": max_v, "maxStep": step_v}
        buf_req = HomeBridgeRequest(topic, reg_dict)
        self._send_request(buf_req)

    def update_characteristic(self, name: str, g_type: GadgetIdentifier,
                              characteristic: CharacteristicIdentifier, value: int) -> bool:
        gadget_service = gadget_type_to_string(g_type)
        reg_str = {"name": name,
                   "service_name": gadget_service,
                   "service": gadget_service,
                   "characteristic": characteristic_type_to_string(characteristic),
                   "value": value}

        topic = "homebridge/to/set"
        buf_req = HomeBridgeRequest(topic, reg_str)
        with self.__lock:
            self._send_request(buf_req)
            start_time = time.time()
            while time.time() < start_time + 5:
                if not self.__status_responses.empty():
                    resp: HomeBridgeRequest = self.__status_responses.get()
                    if resp.message["ack"]:
                        print("Updating Characteristic was successful")
                        return True
                    else:
                        print("failed to update characteristic")
                        return False
        return False

    def _handle_characteristic_update_from_homebridge(self, gadget_name: str, characteristic, value):
        pass

    def _handle_request(self, req: HomeBridgeRequest):
        # Just store request in the response queue for waiting processes to access
        if req.topic == "homebridge/from/response":
            self._received_responses.put(req)
            return

        # Check handle characteristic updates
        if req.topic == "homebridge/from/set":
            # {"name": "flex_lamp", "service_name": "flex_lamp", "service_type": "Lightbulb",
            #  "characteristic": "Brightness", "value": 47}
            # TODO: validate with json schema
            self.__update_characteristic_on_bridge(req.message["name"],
                                                   req.message["characteristic"],
                                                   req.message["value"])