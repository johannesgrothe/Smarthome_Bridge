from gadgets.remote.remote_gadget import RemoteGadget


class DummyRemoteGadget(RemoteGadget):

    def __init__(self, name: str):
        super().__init__(name=name,
                         host_client="unittest",
                         characteristics=[])
