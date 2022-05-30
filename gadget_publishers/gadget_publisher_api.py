from gadget_publishers.gadget_publisher import GadgetPublisher
from gadgets.gadget_update_container import GadgetUpdateContainer


class GadgetPublisherApi(GadgetPublisher):
    def receive_gadget_update(self, update_container: GadgetUpdateContainer):
        pass

    # TODO: weitermachen