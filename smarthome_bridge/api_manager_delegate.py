from abc import ABCMeta, abstractmethod

from gadgets.gadget import Gadget
from smarthome_bridge.smarthomeclient import SmarthomeClient
from smarthome_bridge.bridge_information_container import BridgeInformationContainer


class ApiManagerDelegate(metaclass=ABCMeta):

    @abstractmethod
    def handle_heartbeat(self, client_name: str, runtime_id: int):
        """
        Handles an incoming heartbeat request

        :param client_name: Name of the client sending the heartbeat
        :param runtime_id: Runtime id of the client (random id changing everytime the client is restarted)
        :return: None
        """

    @abstractmethod
    def handle_gadget_update(self, gadget: Gadget):
        """
        Handles an incoming gadget update request by applying changes the passed gadget contains to the gadget manager

        :param gadget: Gadget containing the incoming update data
        :return: None
        """

    @abstractmethod
    def handle_client_update(self, client: SmarthomeClient):
        """
        Handles an incoming client update request by applying changes the passed gadget contains to the client manager

        :param client: Client containing the update information
        :return: None
        """

    @abstractmethod
    def get_bridge_info(self) -> BridgeInformationContainer:
        """
        Returns the bridge information

        :return: Information about the bridge
        """

    @abstractmethod
    def get_client_info(self) -> list[SmarthomeClient]:
        """
        Returns information about all the clients

        :return: All of the saved clients
        """

    @abstractmethod
    def get_gadget_info(self) -> list[Gadget]:
        """
        Returns information about all the gadgets

        :return: All of the saved gadgets
        """