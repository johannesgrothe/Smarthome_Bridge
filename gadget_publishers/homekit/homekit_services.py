from homekit.model import get_id
from homekit.model.characteristics import OnCharacteristicMixin
from homekit.model.services import AbstractService, ServicesTypes


class SwitchService(AbstractService, OnCharacteristicMixin):

    def __init__(self):
        AbstractService.__init__(self, ServicesTypes.get_uuid('public.hap.service.switch'), get_id())
        OnCharacteristicMixin.__init__(self, get_id())
