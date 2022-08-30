from smarthome_bridge.api.api_manager import ApiManager
from system.api_definitions import ApiURIs, ApiAccessLevel
from utils.user_manager import DEFAULT_USER

test_payload = {
    "username": "bongo",
    "password": "spongo",
    "access_level": ApiAccessLevel.user.value,
    "persistent": False
}

test_payload_default_name = {
    "username": DEFAULT_USER,
    "password": "bongolo",
    "access_level": ApiAccessLevel.user.value,
    "persistent": True
}

broken_test_payload = {
    "username": "bongo",
    "password": "dongo",
}


def test_req_handler_system_add_user(f_req_tester, f_api_manager: ApiManager):
    f_req_tester.request_execute_status(ApiURIs.bridge_add_user.uri, test_payload)


def test_req_handler_system_add_user_validation_error(f_req_tester, f_api_manager: ApiManager):
    f_req_tester.request_execute_error(ApiURIs.bridge_add_user.uri, "ValidationError", broken_test_payload)


def test_req_handler_system_add_user_already_exists(f_req_tester, f_api_manager: ApiManager):
    f_req_tester.request_execute(ApiURIs.bridge_add_user.uri, test_payload)
    f_req_tester.request_execute_error(ApiURIs.bridge_add_user.uri, "UserAlreadyExistsException", test_payload)


def test_req_handler_system_add_user_no_user_manager(f_req_tester, f_api_manager: ApiManager):
    f_api_manager.request_handler_bridge._user_manager = None
    f_req_tester.request_execute_error(ApiURIs.bridge_add_user.uri, "UserCreationNotPossibleException", test_payload)


def test_req_handler_system_add_user_username_is_default(f_req_tester, f_api_manager: ApiManager):
    f_req_tester.request_execute(ApiURIs.bridge_add_user.uri, test_payload)
    f_req_tester.request_execute_error(ApiURIs.bridge_add_user.uri, "UserCreationNotPossibleException",
                                       test_payload_default_name)
