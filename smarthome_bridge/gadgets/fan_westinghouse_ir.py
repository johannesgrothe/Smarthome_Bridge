from smarthome_bridge.gadgets.fan import Fan, Characteristic, GadgetIdentifier


class FanWestinghouseIR(Fan):
    def __init__(self,
                 name: str,
                 host_client: str,
                 characteristics: list[Characteristic]):
        super().__init__(name,
                         GadgetIdentifier.fan_westinghouse_ir,
                         host_client,
                         characteristics)
