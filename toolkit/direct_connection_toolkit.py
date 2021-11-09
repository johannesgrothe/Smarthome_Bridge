from clients.client_controller import ClientController, ConfigEraseError, ConfigWriteError, ClientRebootError
from client_config_manager import ClientConfigManager
from loading_indicator import LoadingIndicator

from network.request import NoClientResponseException
from smarthome_bridge.network_manager import NetworkManager

from toolkit.cli_helpers import select_option, ask_for_continue
from toolkit.toolkit_exceptions import ToolkitException

from abc import ABCMeta, abstractmethod
from typing import Optional


class DirectConnectionToolkit(metaclass=ABCMeta):
    _network: NetworkManager
    _client_name: Optional[str]

    def __init__(self):
        self._network = NetworkManager()
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

        erase_controller = ClientController(self._client_name, self._network)

        try:
            erase_controller.erase_config()
            print("Config was successfully erased\n")

        except NoClientResponseException:
            print("Received no Response to Reset Request\n")
            return
        except ConfigEraseError:
            print("Failed to reset EEPROM\n")

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

        write_controller = ClientController(self._client_name, self._network)

        w_system = False
        w_event = False
        w_gadget = False
        has_error = False

        write_option = select_option(["Write complete config",
                                      "System only",
                                      "Gadgets only",
                                      "Events only"],
                                     "writing task",
                                     "back")

        if write_option == -1:
            return
        elif write_option == 0:
            w_system = True
            w_event = True
            w_gadget = True
        elif write_option == 1:
            w_system = True
        elif write_option == 2:
            w_event = True
        elif write_option == 3:
            w_gadget = True

        if w_system:
            print("Writing system config...")

            try:
                with LoadingIndicator():
                    write_controller.write_system_config(config_data["system"])
                print("Config was successfully written\n")

            except NoClientResponseException:
                print("Received no response to config write request\n")
                has_error = True
            except ConfigWriteError:
                print("Failed to write config on chip\n")
                has_error = True

        if w_gadget:
            print("Writing gadget config...")

            try:
                with LoadingIndicator():
                    write_controller.write_gadget_config(config_data["gadgets"])
                print("Config was successfully written\n")

            except NoClientResponseException:
                print("Received no response to config write request\n")
                has_error = True
            except ConfigWriteError:
                print("Failed to write config on chip\n")
                has_error = True

        if w_event:
            print("Writing event config...")

            try:
                with LoadingIndicator():
                    write_controller.write_event_config(config_data["events"])
                print("Config was successfully written\n")

            except NoClientResponseException:
                print("Received no response to config write request\n")
                has_error = True
            except ConfigWriteError:
                print("Failed to write config on chip\n")
                has_error = True

        if not has_error:
            print("All writing efforts were successful\n")
        else:
            print("Completed with errors\n")

    def _reboot_client(self):
        print()
        print("Rebooting Client:")

        reboot_controller = ClientController(self._client_name, self._network)

        try:
            with LoadingIndicator():
                reboot_controller.reboot_client()
            print("Client reboot successful\n")

        except NoClientResponseException:
            print("Received no response to reboot request\n")
            return
        except ClientRebootError:
            print("Failed to reboot client\n")
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
