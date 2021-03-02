import threading
from typing import Optional

from mqtt_connector import MQTTConnector


class EchoThread(threading.Thread):

    __connector: MQTTConnector
    __kill_flag: bool
    __listener_name: str

    def __init__(self, connector: MQTTConnector, listener_name):
        super().__init__()
        self.__connector = connector
        self.__kill_flag = False
        self.__listener_name = listener_name

    def kill(self):
        self.__kill_flag = True

    def run(self):
        while not self.__kill_flag:
            buf_req = self.__connector.get_request()
            if buf_req and buf_req.get_receiver() == self.__listener_name:
                print(f"Responding to Request from '{buf_req.get_sender()}' on '{buf_req.get_path()}'")
                res = buf_req.get_response(payload=buf_req.get_payload())
                self.__connector.send_request(res, timeout=0)
        print("Exiting Responder Thread")


class MQTTTestEchoClient:

    __mqtt_ip: str
    __mqtt_port: int
    __mqtt_user: Optional[str]
    __mqtt_pw: Optional[str]

    __connector: MQTTConnector

    __client_thread: EchoThread

    def __init__(self, mqtt_ip: str, mqtt_port: int,
                 mqtt_user: Optional[str] = None, mqtt_pw: Optional[str] = None):
        self.__mqtt_ip = mqtt_ip
        self.__mqtt_port = mqtt_port
        self.__mqtt_user = mqtt_user
        self.__mqtt_pw = mqtt_pw

        self.__connector = MQTTConnector(self.get_name(),
                                         self.__mqtt_ip,
                                         self.__mqtt_port,
                                         self.__mqtt_user,
                                         self.__mqtt_pw)

        self.__client_thread = EchoThread(self.__connector, self.get_name())
        self.__client_thread.start()

    def __del__(self):
        self.quit()

    def quit(self):
        print("Shutting down Responder")
        self.__client_thread.kill()

    def get_name(self):
        return "echo_tester"
