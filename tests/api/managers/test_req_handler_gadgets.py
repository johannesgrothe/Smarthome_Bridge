from gadgets.gadget_update_container import GadgetUpdateContainer
from smarthome_bridge.api.api_manager import ApiManager
from system.api_definitions import ApiURIs


def test_req_handler_gadgets_info(f_req_tester, f_api_manager: ApiManager):
    f_req_tester.request_execute_payload(ApiURIs.info_gadgets.uri,
                                         "api_get_all_gadgets_response",
                                         None,
                                         {})


def test_req_handler_gadgets_receive_gadget_update(f_api_manager: ApiManager, f_network, f_validator, f_gadget):
    update_container = f_gadget.updated_properties
    update_container.set_name()
    f_api_manager.request_handler_gadget.receive_gadget_update(update_container)
    req = f_network.mock_connector.get_last_send_req()
    assert req.get_payload() is not None
    f_validator.validate(req.get_payload(), "api_gadget_update")


def test_req_handler_gadgets_add_gadget(f_api_manager):
    f_api_manager.request_handler_gadget.add_gadget('blubb')


def test_req_handler_gadgets_remove_gadget(f_api_manager):
    f_api_manager.request_handler_gadget.remove_gadget('blubb')
