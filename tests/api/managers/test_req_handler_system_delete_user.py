from smarthome_bridge.api.api_manager import ApiManager
from system.api_definitions import ApiURIs, ApiAccessLevel

# BEGIN Region test users

test_user_1 = {
    "username": "user1",
    "password": "lameUser1",
    "access_level": ApiAccessLevel.user,
    "persistent": True
}

test_user_2 = {
    "username": "user2",
    "password": "lameUser2",
    "access_level": ApiAccessLevel.user,
    "persistent": True
}

test_admin = {
    "username": "admin",
    "password": "uberAdmin",
    "access_level": ApiAccessLevel.admin,
    "persistent": True
}

# END Region test users

# BEGIN Region add test user payloads

add_regular_user_for_deletion_test_payload = {
    "username": "user",
    "password": "lameUser",
    "access_level": ApiAccessLevel.user.value,
    "persistent": True
}

add_regular_user_for_deletion_test_payload_non_persistent = {
    "username": "user",
    "password": "lameNonUser",
    "access_level": ApiAccessLevel.user.value,
    "persistent": False
}

add_regular_user_for_deletion_test_payload_2 = {
    "username": "bongolus",
    "password": "lameUser2",
    "access_level": ApiAccessLevel.user.value,
    "persistent": True
}

add_admin_user_for_deletion_test_payload = {
    "username": "admin",
    "password": "uberAdmin",
    "access_level": ApiAccessLevel.admin.value,
    "persistent": True
}

# END Region add test user payloads

# BEGIN Region deletion test payloads

test_deletion_payload_regular = {
    "username": "user",
    "access_level": ApiAccessLevel.user.value,
    "user_to_delete": "user"
}

test_deletion_payload_not_himself_or_not_admin = {
    "username": "bongolus",
    "access_level": ApiAccessLevel.user.value,
    "user_to_delete": "user"
}

test_deletion_payload_admin = {
    "username": "admin",
    "access_level": ApiAccessLevel.admin.value,
    "user_to_delete": "user"
}

# END Region deletion test payloads

# BEGIN Region broken payloads

test_deletion_broken_payload_username = {
    "username": "bo",
    "access_level": ApiAccessLevel.user.value,
    "user_to_delete": "user"
}

test_deletion_broken_payload_access_level = {
    "username": "bo",
    "access_level": ApiAccessLevel.guest.value,
    "user_to_delete": "user"
}

test_deletion_broken_payload_user_to_delete = {
    "username": "bob",
    "access_level": ApiAccessLevel.admin.value,
    "user_to_delete": "u"
}

# END Region broken payloads


def test_req_handler_delete_user(f_req_tester, f_api_manager: ApiManager):
    f_req_tester.request_execute(ApiURIs.bridge_add_user.uri, add_regular_user_for_deletion_test_payload)
    f_req_tester.request_execute(ApiURIs.bridge_add_user.uri, add_admin_user_for_deletion_test_payload)

    f_req_tester.request_execute_status(ApiURIs.bridge_delete_user.uri, test_deletion_payload_regular)
    f_req_tester.request_execute(ApiURIs.bridge_add_user.uri, add_regular_user_for_deletion_test_payload)
    f_req_tester.request_execute_status(ApiURIs.bridge_delete_user.uri, test_deletion_payload_admin)


def test_req_handler_delete_user_validation_error(f_req_tester, f_api_manager: ApiManager):
    f_req_tester.request_execute_error(ApiURIs.bridge_delete_user.uri, "ValidationError",
                                       test_deletion_broken_payload_username)
    f_req_tester.request_execute_error(ApiURIs.bridge_delete_user.uri, "ValidationError",
                                       test_deletion_broken_payload_user_to_delete)
    f_req_tester.request_execute_error(ApiURIs.bridge_delete_user.uri, "ValidationError",
                                       test_deletion_broken_payload_access_level)


def test_req_handler_delete_user_user_does_not_exist(f_req_tester, f_api_manager: ApiManager):
    f_req_tester.request_execute_error(ApiURIs.bridge_delete_user.uri, "UserDoesNotExistException",
                                       test_deletion_payload_regular)


def test_req_handler_delete_user_deletion_not_possible(f_req_tester, f_api_manager: ApiManager):
    f_req_tester.request_execute(ApiURIs.bridge_add_user.uri,
                                 add_regular_user_for_deletion_test_payload_non_persistent)
    f_req_tester.request_execute_error(ApiURIs.bridge_delete_user.uri, "DeletionNotPossibleException",
                                       test_deletion_payload_regular)


def test_req_handler_delete_user_not_himself_or_admin(f_req_tester, f_api_manager: ApiManager):
    f_req_tester.request_execute(ApiURIs.bridge_add_user.uri, add_regular_user_for_deletion_test_payload)
    f_req_tester.request_execute(ApiURIs.bridge_add_user.uri, add_regular_user_for_deletion_test_payload_2)
    f_req_tester.request_execute_error(ApiURIs.bridge_delete_user.uri, "DeletionNotPossibleException",
                                       test_deletion_payload_not_himself_or_not_admin)
