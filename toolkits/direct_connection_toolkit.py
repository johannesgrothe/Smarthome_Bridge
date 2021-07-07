

from client_controller import ClientController
from client_config_manager import ClientConfigManager
from loading_indicator import LoadingIndicator

from network.network_connector import NetworkConnector
from network.request import NoClientResponseException

from toolkits.toolkit_helpers import select_option, ask_for_continue
from toolkits.toolkit_meta import TOOLKIT_NETWORK_NAME
from toolkits.toolkit_exceptions import ToolkitException

from abc import ABCMeta, abstractmethod
from typing import Optional


class DirectConnectionToolkit(metaclass=ABCMeta):
    _network: Optional[NetworkConnector]
    _client_name: Optional[str]

    def __init__(self):
        self._network = None
        self._client_name = None

    def __del__(self):
        if self._network:
            self._network.__del__()

    def run(self):
        """Runs the toolkit, accepting user inputs and executing the selcted tasks"""

        self._get_ready()

        self._connect_to_client()

        print("Connected to '{}'".format(self._client_name))

        while True:
            if not self._select_task():
                break

    def _select_task(self) -> bool:
        task_option = select_option(["Overwrite EEPROM", "Write Config", "Reboot"],
                                    "what to do",
                                    "Quit")

        if task_option == -1:
            return False

        elif task_option == 0:  # Overwrite EEPROM
            self._erase_config()
            return True

        elif task_option == 1:  # Write Config
            self._write_config()
            return True

        elif task_option == 2:  # Reboot
            self._reboot_client()
            print("Reconnecting might be required.")
            return True

    def _erase_config(self):
        print()
        print("Overwriting EEPROM:")

        erase_controller = ClientController(self._client_name, TOOLKIT_NETWORK_NAME, self._network)

        try:
            ack = erase_controller.reset_config()
            if ack is False:
                print("Failed to reset EEPROM\n")
                return

            print("Config was successfully erased\n")

        except NoClientResponseException:
            print("Received no Response to Reset Request\n")
            return

    def _write_config(self):

        manager = ClientConfigManager()
        config_names = manager.get_config_names()

        config_path: Optional[str]
        config_data: Optional[dict] = None

        while not config_data:

            config_index = select_option(config_names,
                                         "which config to write",
                                         "Quit")

            if config_index == -1:
                return

            config_data = manager.get_config(config_names[config_index])

            if not config_data:
                response = ask_for_continue("Config file could either not be loaded, isn no valid json file or"
                                            "no valid config. Try again?")
                if not response:
                    return
                else:
                    continue

        print(f"Loaded config '{config_data['name']}'")
        print()
        print("Writing config:")

        write_controller = ClientController(self._client_name, TOOLKIT_NETWORK_NAME, self._network)

        try:
            with LoadingIndicator():
                ack = write_controller.write_config(config_data)
            if ack is False:
                print("Failed to write config\n")
                return

            print("Config was successfully written\n")

        except NoClientResponseException:
            print("Received no response to config write request\n")
            return

    def _reboot_client(self):
        print()
        print("Rebooting Client:")

        reboot_controller = ClientController(self._client_name, TOOLKIT_NETWORK_NAME, self._network)

        try:
            with LoadingIndicator():
                ack = reboot_controller.reboot_client()
            if ack is False:
                print("Failed to reboot client\n")
                return

            print("Client reboot successful\n")

        except NoClientResponseException:
            print("Received no response to reboot request\n")
            return

    def _connect_to_client(self):
        """Scans for clients and lets the user select one if needed and possible."""
        while not self._client_name:

            with LoadingIndicator():
                client_id = None
                client_list = self._scan_for_clients()

                if len(client_list) == 0:
                    pass
                elif len(client_list) > 1:
                    client_id = select_option(client_list, "client to connect to")
                else:
                    client_id = client_list[0]
                self._client_name = client_id

            if not self._client_name:
                response = ask_for_continue("Could not find any gadget. Try again?")
                if not response:
                    raise ToolkitException

    @abstractmethod
    def _get_ready(self):
        pass

    @abstractmethod
    def _scan_for_clients(self) -> [str]:
        """Sends a broadcast and waits for clients to answer.

        Returns a list containing the names of all available clients."""
        pass
