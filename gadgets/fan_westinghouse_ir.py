from gadgets.fan import Fan, Characteristic, GadgetIdentifier


class FanWestinghouseIR(Fan):
    def __init__(self,
                 name: str,
                 host_client: str,
                 status: Characteristic,
                 fan_speed: Characteristic):
        super().__init__(name,
                         host_client,
                         [status, fan_speed])
