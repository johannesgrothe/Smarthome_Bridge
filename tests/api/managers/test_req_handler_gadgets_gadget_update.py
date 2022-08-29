from smarthome_bridge.api.api_manager import ApiManager
from smarthome_bridge.gadget_update_appliers.gadget_update_applier_super import UpdateApplyError
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


def test_req_handler_gadgets_handle_gadgets_update_error(f_req_tester, f_api_manager: ApiManager, f_gadget):
    f_api_manager.request_handler_gadget._update_applier.mock_exception = UpdateApplyError('hongo')
    f_req_tester.request_execute_error(ApiURIs.update_gadget.uri,
                                       "GadgetUpdateApplyError",
                                       {"id": f_gadget.id,
                                        "attributes": {}})


def test_req_handler_gadgets_handle_gadgets_update(f_req_tester, f_api_manager: ApiManager, f_gadget):
    f_req_tester.request_execute_status(ApiURIs.update_gadget.uri,
                                        {"id": f_gadget.id,
                                         "attributes": {"speed": 1}})
