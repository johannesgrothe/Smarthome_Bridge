from smarthome_bridge.api.api_manager import ApiManager
from smarthome_bridge.update.bridge_update_manager import UpdateNotPossibleException, NoUpdateAvailableException
from system.api_definitions import ApiURIs


def test_req_handler_system_check_update(f_req_tester, f_api_manager: ApiManager, f_update_manager):
    f_req_tester.request_execute_payload(ApiURIs.bridge_update_check.uri,
                                         "api_bridge_update_check_response",
                                         None,
                                         {})


def test_req_handler_system_check_update_not_available(f_req_tester, f_api_manager: ApiManager, f_update_manager):
    f_update_manager.mock_exception = NoUpdateAvailableException()
    f_req_tester.request_execute_status(ApiURIs.bridge_update_check.uri,
                                        {})


def test_req_handler_system_check_update_validation_error(f_req_tester, f_api_manager: ApiManager, f_update_manager):
    f_req_tester.request_execute_error(ApiURIs.bridge_update_check.uri,
                                       "ValidationError",
                                       {"yolo": 123})


def test_req_handler_system_check_update_not_possible(f_req_tester, f_api_manager: ApiManager, f_update_manager):
    f_update_manager.mock_exception = UpdateNotPossibleException()
    f_req_tester.request_execute_error(ApiURIs.bridge_update_check.uri,
                                       "UpdateNotPossibleException",
                                       {})


def test_req_handler_system_check_update_no_updater(f_req_tester, f_api_manager: ApiManager, f_update_manager):
    f_api_manager.request_handler_bridge._updater = None
    f_req_tester.request_execute_error(ApiURIs.bridge_update_check.uri,
                                       "UpdateNotPossibleException",
                                       {})
