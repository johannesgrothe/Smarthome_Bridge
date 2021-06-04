import socket
import logging
import requests
import json
import enum
from typing import Optional, Callable
from queue import Queue

from socket_connector import SocketClient
from pubsub import Subscriber, Request


class SerialPortAdapterState(enum.IntEnum):
    pending = 0,
    succeeded = 1,
    failed = 2


class SocketReader(Subscriber):

    _state: SerialPortAdapterState
    _callback: Optional[Callable[[dict], None]]
    _logger: logging.Logger
    _msg_queue: Queue

    def __init__(self, callback: Optional[Callable[[dict], None]], socket_client: SocketClient):
        super().__init__()
        self._callback = callback
        self._msg_queue = Queue()
        self._state = SerialPortAdapterState.pending
        self._logger = logging.getLogger("SerialPortAdapter")
        socket_client.subscribe(self)

    def get_state(self) -> SerialPortAdapterState:
        return self._state

    def receive(self, req: Request):
        self._msg_queue.put(req)

    def read_until(self, sender: str, success_codes: list, fail_codes: list) -> bool:
        self._state = SerialPortAdapterState.pending
        self._msg_queue = Queue()

        while True:
            if not self._msg_queue.empty():
                req: Request = self._msg_queue.get()

                if not req.get_sender() == sender:
                    continue

                data = req.get_payload()

                if not ("message" in data and "status" in data):
                    continue

                self._callback(data)

                if data["status"] in success_codes:
                    self._state = SerialPortAdapterState.succeeded
                    return True

                if data["status"] in fail_codes:
                    self._state = SerialPortAdapterState.failed
                    return False


class BridgeRestApiException(Exception):
    def __init__(self):
        super().__init__("An Error with the Bridge REST API occurred")


class BridgeSocketApiException(Exception):
    def __init__(self):
        super().__init__("An Error with the Socket API occurred")


class ClientDoesNotExistException(Exception):
    def __init__(self, name: str):
        super().__init__(f"No client named '{name}' was found")


class GadgetDoesNotExistException(Exception):
    def __init__(self, name: str):
        super().__init__(f"No gadget named '{name}' was found")


class ConfigWritingFailedException(Exception):
    def __init__(self):
        super().__init__(f"Failed to write the selected config")


class SoftwareWritingFailedException(Exception):
    def __init__(self):
        super().__init__(f"Failed to write the software to the client")


class BridgeConnector:
    _socket_client: Optional[SocketClient]
    _logger: logging.Logger

    _connected: bool

    _address: str
    _rest_port: int
    _socket_port: int

    _bridge_name: str
    _running_since: str
    _git_branch: Optional[str]
    _git_commit: Optional[str]

    _clients: dict
    _connectors: dict
    _gadgets: dict
    _configs: dict
    _serial_ports: list

    def __init__(self, address: str, rest_port: int, socket_port: int):
        self._logger = logging.getLogger("BridgeConnector")
        self._address = address
        self._rest_port = rest_port
        self._socket_port = socket_port
        self._connected = False
        self._socket_client = None

    def __del__(self):
        self._disconnect()

    @staticmethod
    def _format_url(url: str):
        if not url.startswith("http"):
            url = "http://" + url
        return url

    @staticmethod
    def _add_params_to_url(url: str, url_args: Optional[dict]) -> str:
        if not url_args:
            return url

        url = url + "?"

        for key in url_args:
            url = url + f"{key}={url_args[key]}&"

        return url[:-1]

    def _send_api_request(self, url: str) -> (int, dict):
        url = self._format_url(url)

        self._logger.info(f"Sending GET request to '{url}'")
        response = requests.get(url)
        body = response.content.decode()
        try:
            res_data = json.loads(body)
        except json.decoder.JSONDecodeError:
            self._logger.error(f"Failed to parse received payload to json")
            self._logger.error(body)
            return 1200, {}
        return response.status_code, res_data

    def _send_api_command(self, url: str, payload: Optional[dict]) -> (int, dict):
        url = self._format_url(url)

        self._logger.info(f"Sending POST request to '{url}'")

        if payload:
            response = requests.post(url, json=payload)
        else:
            response = requests.post(url)

        body = response.content.decode()
        try:
            res_data = json.loads(body)
        except json.decoder.JSONDecodeError:
            self._logger.error(f"Failed to parse received payload to json")
            self._logger.error(body)
            return 1200, {}
        return response.status_code, res_data

    def _disconnect(self):
        self._logger.info("Closing all active connections")
        self._connected = False
        if self._socket_client:
            self._socket_client.__del__()
            self._socket_client = None

    def _fetch_data(self, path: str, url_args: Optional[dict] = None) -> Optional[dict]:
        full_path = f"{self._address}:{self._rest_port}/{path}"

        full_path = self._add_params_to_url(full_path, url_args)

        status, data = self._send_api_request(full_path)

        if status != 200:
            self._logger.error(f"Could not load information from the bridge at '{full_path}'")
            raise BridgeRestApiException

        return data

    def _send_data(self, path: str, payload: Optional[dict], url_args: Optional[dict] = None) -> Optional[dict]:
        full_path = f"{self._address}:{self._rest_port}/{path}"

        full_path = self._add_params_to_url(full_path, url_args)

        status, data = self._send_api_command(full_path, payload)

        if status != 200:
            self._logger.error(f"Could not load information from the bridge at '{full_path}'")
            raise BridgeRestApiException

        return data

    def _load_info(self):
        self._logger.info("Fetching bridge info")
        bridge_info = self._fetch_data(f"info")

        self._bridge_name = bridge_info["bridge_name"]
        self._running_since = bridge_info["running_since"]
        self._git_branch = bridge_info["software_branch"]
        self._git_commit = bridge_info["software_commit"]

    def _load_configs(self):
        self._logger.info("Fetching client config data from bridge")
        config_name_data = self._fetch_data("system/configs")
        self._remote_configs = config_name_data["config_names"]

    def _load_clients(self):
        self._clients = {}
        client_data_res = self._fetch_data("clients")

        for client_data in client_data_res["clients"]:
            try:
                buf_name = client_data["name"]

                if buf_name in self._clients:
                    self._logger.error(f"Received data for two clients named '{buf_name}'")

                buf_client = {"boot_mode": client_data["boot_mode"],
                              "is_active": client_data["is_active"],
                              "sw_branch": client_data["sw_branch"],
                              "sw_version": client_data["sw_version"],
                              "sw_uploaded": client_data["sw_uploaded"]}

                self._clients[buf_name] = buf_client
            except KeyError:
                self._logger.error("A client property could not be loaded")

    def _load_gadgets(self):
        self._gadgets = {}
        gadget_data_res = self._fetch_data("gadgets")

        for gadget_data in gadget_data_res["gadgets"]:
            try:
                buf_name = gadget_data["name"]

                if buf_name in self._clients:
                    self._logger.error(f"Received data for two gadgets named '{buf_name}'")

                buf_gadget = {"type": gadget_data["type"],
                              "characteristics": gadget_data["characteristics"]}

                self._gadgets[buf_name] = buf_gadget
            except KeyError:
                self._logger.error("A gadget property could not be loaded")

    def _load_connectors(self):
        self._connectors = {}

    def _load_serial_ports(self):
        serial_port_data = self._fetch_data("system/get_serial_ports")
        self._serial_ports = serial_port_data["serial_ports"]

    def load_data(self):
        self._load_info()
        self._load_configs()
        self._load_clients()
        self._load_gadgets()
        self._load_connectors()
        self._load_serial_ports()

    def connect(self):
        self._disconnect()

        try:
            self._fetch_data("")
            self._logger.info("REST-API is responding")
        except requests.exceptions.ConnectionError:
            self._logger.error("Could not connect to remote api")
            raise BridgeRestApiException

        try:
            self._socket_client = SocketClient("<bridge>", self._address, self._socket_port)
        except ConnectionRefusedError:
            self._logger.error("Could not connect to remote socket")
            raise BridgeSocketApiException
        self._logger.info("Connected to the Socket API")

        self._connected = True

    def get_address(self) -> str:
        return self._address

    def get_rest_port(self) -> int:
        return self._rest_port

    def get_socket_port(self) -> int:
        return self._socket_port

    def get_name(self) -> str:
        return self._bridge_name

    def get_launch_time(self) -> str:
        return self._running_since

    def get_commit(self) -> str:
        return self._git_commit

    def get_branch(self) -> str:
        return self._git_branch

    def get_client_names(self) -> list:
        out_list = []
        for client_name in self._clients:
            out_list.append(client_name)
        return out_list

    def get_client_data(self, name: str) -> dict:
        try:
            return self._clients[name]
        except KeyError:
            raise ClientDoesNotExistException

    def get_gadget_names(self) -> list:
        out_list = []
        for gadget_name in self._gadgets:
            out_list.append(gadget_name)
        return out_list

    def get_gadget_data(self, name: str) -> dict:
        try:
            return self._gadgets[name]
        except KeyError:
            raise GadgetDoesNotExistException

    def get_connector_types(self) -> list:
        out_list = []
        for connector_type in self._connectors:
            out_list.append(connector_type)
        return out_list

    def get_connector_data(self, connector_type: str) -> dict:
        try:
            return self._connectors[connector_type]
        except KeyError:
            raise GadgetDoesNotExistException

    def get_serial_ports(self) -> list:
        return self._serial_ports

    def write_software_to_client(self, branch: str, serial_port: Optional[str] = None,
                                 callback: Optional[Callable[[dict], None]] = None):
        url_args = {'branch_name': branch}
        if serial_port:
            url_args['serial_port'] = serial_port

        try:
            self._send_data("system/flash_software", {}, url_args)
        except BridgeRestApiException:
            print(f"Software flashing could no be started.")
            raise SoftwareWritingFailedException

        print("Software writing started.\n")

        listener = SocketReader(callback, self._socket_client)
        write_ok = listener.read_until("SOFTWARE_UPLOAD", [6], [-1, -2, -3, -4, -5, -6])
        if not write_ok:
            raise SoftwareWritingFailedException

    def write_config_to_network_client(self, name: str, config: dict,
                                       callback: Optional[Callable[[dict], None]] = None):
        flash_path = f"clients/{name}/write_config"

        try:
            self._send_data(flash_path, config)
        except BridgeRestApiException:
            raise ConfigWritingFailedException

        print("Config writing started.\n")

        listener = SocketReader(callback, self._socket_client)
        write_ok = listener.read_until("CONFIG_UPLOAD", [1], [-1])
        if not write_ok:
            raise ConfigWritingFailedException

    def write_config_to_serial_client(self, config: dict, serial_port: Optional[str],
                                      callback: Optional[Callable[[dict], None]] = None):
        req_args = {}
        if serial_port:
            req_args["serial_port"] = serial_port

        flash_path = f"system/write_config"

        try:
            self._send_data(flash_path, config, req_args)
        except BridgeRestApiException:
            raise ConfigWritingFailedException

        print("Config writing started.\n")

        listener = SocketReader(callback, self._socket_client)
        write_ok = listener.read_until("CONFIG_UPLOAD", [1], [-1])
        if not write_ok:
            raise ConfigWritingFailedException


def script_main():
    # logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    connector = BridgeConnector(socket.gethostname(), 4999, 5007)

    connector.connect()
    connector.load_data()

    print(connector.get_name())
    print(connector.get_commit())
    print(connector.get_branch())
    print(connector.get_address())
    print(connector.get_socket_port())
    print(connector.get_rest_port())


if __name__ == "__main__":
    script_main()
