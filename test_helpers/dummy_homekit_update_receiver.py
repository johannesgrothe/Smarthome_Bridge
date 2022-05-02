from typing import Optional, Tuple

from gadget_publishers.homekit.homekit_gadget_update_interface import GadgetPublisherHomekitInterface


class DummyHomekitUpdateReceiver(GadgetPublisherHomekitInterface):
    last_update: Optional[Tuple[str, dict]]

    def __init__(self):
        super().__init__()
        self.last_update = None

    def receive_update(self, gadget_name: str, update_data: dict) -> None:
        self.last_update = (gadget_name, update_data)
