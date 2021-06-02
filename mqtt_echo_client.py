from typing import Optional

from mqtt_connector import MQTTConnector
from pubsub import Subscriber
from request import Request
import logging


class MQTTTestEchoClient(Subscriber):

    _mqtt_ip: str
    _mqtt_port: int
    _mqtt_user: Optional[str]
    _mqtt_pw: Optional[str]

    _name: str
    _network: MQTTConnector
    _logger: logging.Logger

    def __init__(self, name: str, mqtt_ip: str, mqtt_port: int,
                 mqtt_user: Optional[str] = None, mqtt_pw: Optional[str] = None):
        self._name = name
        self._mqtt_ip = mqtt_ip
        self._mqtt_port = mqtt_port
        self._mqtt_user = mqtt_user
        self._mqtt_pw = mqtt_pw
        self._logger = logging.getLogger("MQTTTestEchoClient")

        self._network = MQTTConnector(self.get_name(),
                                      self._mqtt_ip,
                                      self._mqtt_port,
                                      self._mqtt_user,
                                      self._mqtt_pw)
        self._network.subscribe(self)

    def __del__(self):
        self._network.__del__()

    def receive(self, req: Request):

        if req.get_receiver() == self.get_name():  # Normal Request
            self._logger.info(f"Received Request at '{req.get_path()}'")
        elif req.get_receiver() is None:  # Broadcast
            self._logger.info(f"Received Broadcast at '{req.get_path()}'")
        else:
            return

        sender = self.get_name()
        receiver = req.get_sender()

        res = Request(req.get_path(),
                      req.get_session_id(),
                      sender,
                      receiver,
                      req.get_payload())
        self._network.send_request(res, timeout=0)

    def get_name(self):
        return self._name
