from gadgets.remote.i_remote_gadget import IRemoteGadget
from smarthome_bridge.client_information_interface import ClientInformationInterface


class IRemoteGadgetApiEncoder:

    @classmethod
    def encode_host_attributes(cls, gadget: IRemoteGadget) -> dict:
        data = {"host_client": cls._encode_host(gadget.host_client),
                "is_local": False}
        return data

    @classmethod
    def _encode_host(cls, host: ClientInformationInterface) -> dict:
        return {
            "id": host.id,
            "is_active": host.is_active
        }
