from abc import ABCMeta, abstractmethod

from gadget_publishers.gadget_publisher import GadgetPublisher
from gadgets.gadget import Gadget
from smarthome_bridge.client import Client
from smarthome_bridge.bridge_information_container import BridgeInformationContainer
from smarthome_bridge.gadget_update_information import GadgetUpdateInformation


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
    def handle_gadget_sync(self, gadget: RemoteGadget):
        """
        Handles an incoming gadget sync request by applying the changes

        :param gadget: Gadget containing the incoming update data
        :return: None
        """

    @abstractmethod
    def handle_gadget_update(self, gadget: RemoteGadget):
        """
        Handles an incoming gadget update request by applying changes from the passed container to the gadget manager

        :param gadget: Gadget update information
        :return: None
        """

    @abstractmethod
    def handle_client_sync(self, client: Client):
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
    def get_client_info(self) -> list[Client]:
        """
        Returns information about all the clients

        :return: All the saved clients
        """

    @abstractmethod
    def get_gadget_info(self) -> list[RemoteGadget]:
        """
        Returns information about all the gadgets

        :return: All the saved gadgets
        """

    @abstractmethod
    def get_gadget_publisher_info(self) -> list[GadgetPublisher]:
        """
        Returns information about all the gadget publishers

        :return: All the gadget publishers

	@abstractmethod
    def get_local_gadget_info(self) -> list[LocalGadget]:
        """
        Returns information about all the gadgets

        :return: All the saved gadgets
        """
