from abc import abstractmethod, ABCMeta

from gadgets.gadget_update_container import GadgetUpdateContainer


class GadgetStatusReceiver(metaclass=ABCMeta):
    @abstractmethod
    def receive_gadget_update(self, update_container: GadgetUpdateContainer):
        """
        Receive and handle a gadget

        :param update_container: Container with the update information
        :return: None
        """
        pass

    @abstractmethod
    def add_gadget(self, gadget_id: str):
        """
        Get notified about a new gadget

        :param gadget_id: ID of the new gadget
        :return: None
        """
        pass

    @abstractmethod
    def remove_gadget(self, gadget_id: str):
        """
        Get notified about the removal of a gadget

        :param gadget_id: ID of the deleted gadget
        :return: None
        """
        pass
