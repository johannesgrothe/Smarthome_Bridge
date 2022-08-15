from smarthome_bridge.api.api_manager import ApiManager
from system.api_definitions import ApiURIs


def test_req_handler_gadgets_update_validation_error(f_req_tester, f_api_manager: ApiManager):
    f_req_tester.request_execute_error(ApiURIs.update_gadget.uri,
                                       "ValidationError",
                                       {"test": 1234})


def test_req_handler_gadgets_update_does_not_exist(f_req_tester, f_api_manager: ApiManager):
    f_req_tester.request_execute_error(ApiURIs.update_gadget.uri,
                                       "GagdetDoesNeeExist",
                                       {"id": "spongobob",
                                        "attributes": {}})
