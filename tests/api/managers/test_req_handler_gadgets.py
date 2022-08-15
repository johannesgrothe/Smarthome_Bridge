from smarthome_bridge.api.api_manager import ApiManager
from system.api_definitions import ApiURIs


def test_req_handler_gadgets_info(f_req_tester, f_api_manager: ApiManager):
    f_req_tester.request_execute_payload(ApiURIs.info_gadgets.uri,
                                         "api_get_all_gadgets_response",
                                         None,
                                         {})
