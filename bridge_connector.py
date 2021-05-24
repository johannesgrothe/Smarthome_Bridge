import socket
import logging
import requests
import json
from typing import Optional


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


class BridgeConnector:
    _socket_client: socket.socket
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

    def __init__(self, address, rest_port, socket_port):
        self._logger = logging.getLogger("BridgeConnector")
        self._socket_client = socket.socket()
        self._address = address
        self._rest_port = rest_port
        self._socket_port = socket_port
        self._connected = False

    def __del__(self):
        self._disconnect()

    def _send_api_request(self, url: str) -> (int, dict):
        if not url.startswith("http"):
            url = "http://" + url

        self._logger.info(f"Sending API request to '{url}'")
        response = requests.get(url)
        try:
            res_data = json.loads(response.content.decode())
        except json.decoder.JSONDecodeError:
            self._logger.error(f"Failed to parse received payload to json")
            return 1200, {}
        return response.status_code, res_data

    def _disconnect(self):
        self._logger.info("Closing all active connections")
        self._connected = False
        self._socket_client.close()

    def _fetch_data(self, path: str) -> Optional[dict]:
        full_path = f"{self._address}:{self._rest_port}/{path}"
        status, data = self._send_api_request(full_path)

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
        # self._disconnect()

        self._fetch_data("")
        self._logger.info("REST-API is responding")

        try:
            self._socket_client.connect((self._address, self._socket_port))  # connect to the server
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

    def get_connector_data(self, type: str) -> dict:
        try:
            return self._connectors[type]
        except KeyError:
            raise GadgetDoesNotExistException


def script_main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
