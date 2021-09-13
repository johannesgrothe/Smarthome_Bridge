from gadgets.gadget import Gadget


class DummyGadget(Gadget):

    def __init__(self, name: str):
        super().__init__(name=name,
                         host_client="unittest",
                         characteristics=[])
