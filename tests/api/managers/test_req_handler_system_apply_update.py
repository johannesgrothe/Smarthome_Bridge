from smarthome_bridge.api.api_manager import ApiManager
from smarthome_bridge.update.bridge_update_manager import UpdateNotSuccessfulException
from system.api_definitions import ApiURIs


def test_req_handler_system_apply_update(f_req_tester, f_api_manager: ApiManager, f_update_manager):
    f_req_tester.request_execute_status(ApiURIs.bridge_update_execute.uri,
                                        {})


def test_req_handler_system_apply_update_validation_error(f_req_tester, f_api_manager: ApiManager, f_update_manager):
    f_req_tester.request_execute_error(ApiURIs.bridge_update_execute.uri,
                                       "ValidationError",
                                       {"yolo": 123})


def test_req_handler_system_apply_update_no_updater(f_req_tester, f_api_manager: ApiManager, f_update_manager):
    f_api_manager.request_handler_bridge._updater = None
    f_req_tester.request_execute_error(ApiURIs.bridge_update_execute.uri,
                                       "UpdateNotPossibleException",
                                       {})


def test_req_handler_system_apply_update_not_successful(f_req_tester, f_api_manager: ApiManager, f_update_manager):
    f_update_manager.mock_exception = UpdateNotSuccessfulException()
    f_req_tester.request_execute_error(ApiURIs.bridge_update_execute.uri,
                                       "UpdateNotSuccessfulException",
                                       {})
