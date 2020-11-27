from network_connector import NetworkConnector, Request
from typing import Optional
from queue import Queue
import paho.mqtt.client as mqtt
import time
import json

# Global queue for mqtt results
mqtt_res_queue = Queue()


class MQTTConnector(NetworkConnector):
    """Class to implement a MQTT connection module"""

    __client: mqtt.Client
    __own_name: str
    __ip: str
    __port: int

    __mqtt_username: Optional[str]
    __mqtt_password: Optional[str]

    def __init__(self, own_name: str, mqtt_ip: str, mqtt_port: int, mqtt_user: Optional[str], mqtt_pw: Optional[str]):
        self.__own_name = own_name
        self.__client = mqtt.Client(self.__own_name)
        self.__ip = mqtt_ip
        self.__port = mqtt_port
        self.__mqtt_username = mqtt_user
        self.__mqtt_password = mqtt_pw

        if self.__mqtt_username and self.__mqtt_password:
            self.__client.username_pw_set(self.__mqtt_username, self.__mqtt_password)
        self.__client.connect(self.__ip, self.__port, 60)
        self.__client.loop_start()
        self.__client.on_message = self.__on_message
        self.__client.subscribe("smarthome/#")

    def __del__(self):
        self.__client.disconnect()

    @staticmethod
    def __on_message(client, userdata, message):
        global mqtt_res_queue

        topic = message.topic

        try:
            json_str = message.payload.decode("utf-8").replace("'", '"').replace("None", "null")
        except Exception:
            print("Couldn't format json string")
            return

        try:
            body = json.loads(json_str)
        except json.decoder.JSONDecodeError:
            print("Couldn't decode json: '{}'".format(json_str))
            return

        if not ("session_id" in body and "sender" in body and "receiver" in body and "payload" in body):
            print("Missing key(s) in request")
            return

        try:
            inc_req = Request(topic,
                              body["session_id"],
                              body["sender"],
                              body["receiver"],
                              body["payload"])
            print("Received: {}".format(inc_req.to_string()))

            mqtt_res_queue.put(inc_req)

        except ValueError:
            print("Error creating Request")

    def get_request(self) -> Optional[bool]:
        """Returns a request if there is one"""
        if not mqtt_res_queue.empty():
            return mqtt_res_queue.get()
        return None

    def send_request(self, req: Request, timeout: int = 6) -> (Optional[bool], Optional[Request]):
        global mqtt_res_queue

        self.__client.publish(req.get_path(), str(req.get_body()))
        if timeout > 0:
            timeout_time = time.time() + timeout
            while time.time() < timeout_time:
                if not mqtt_res_queue.empty():
                    res: Request = mqtt_res_queue.get()
                    # print("Got from Queue: {}".format(res.to_string()))
                    if res.get_session_id() == req.get_session_id() and req.get_sender() != res.get_sender():
                        res_ack = res.get_ack()
                        res_status_msg = res.get_status_msg()
                        if res_status_msg is None:
                            res_status_msg = "no status message received"
                        return res_ack, res_status_msg, res
        return None, "no response received", None

    def send_broadcast(self, req: Request, timeout: int = 6) -> [Request]:
        global mqtt_res_queue

        responses: [Request] = []
        json_str = json.dumps(req.get_body())
        self.__client.publish(req.get_path(), json_str)
        timeout_time = time.time() + timeout
        while time.time() < timeout_time:
            if not mqtt_res_queue.empty():
                res: Request = mqtt_res_queue.get()
                # print("Got from Queue: {}".format(res.to_string()))
                if res.get_path() == "smarthome/broadcast/res" and res.get_session_id() == req.get_session_id():
                    responses.append(res)
        return responses


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
                      {"yolo": "blub"})

    mqtt_gadget.send_request(buf_req)
