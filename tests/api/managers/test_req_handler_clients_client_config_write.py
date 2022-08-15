from smarthome_bridge.api.api_manager import ApiManager
from system.api_definitions import ApiURIs


def test_req_handler_clients_client_config_write(f_req_tester, f_api_manager: ApiManager, f_client, f_client_config):
    # request_execute_status(ApiURIs.client_config_write.uri,
    #                        {"config": f_client_config},
    #                        f_network,
    #                        f_credentials,
    #                        f_validator)

    f_req_tester.request_execute_error(ApiURIs.client_config_write.uri,  # TODO: fix
                                       "NotImplementedError",
                                       {"config": f_client_config})

# def test_req_handler_clients_client_config_write_validation_error(f_validator, f_api_manager: ApiManager,
#                                                                   f_network: DummyNetworkManager,
#                                                                   f_credentials, f_client):
#     request_execute_error(ApiURIs.client_config_write.uri,
#                           "ValidationError",
#                           {"test": 1234},
#                           f_network,
#                           f_credentials,
#                           f_validator)
