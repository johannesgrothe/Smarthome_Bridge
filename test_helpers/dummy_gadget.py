from gadgets.remote.i_remote_gadget import IRemoteGadget


class DummyRemoteGadget(IRemoteGadget):

    def __init__(self, name: str):
        super().__init__(name=name,
                         host_client="unittest",
                         characteristics=[])
