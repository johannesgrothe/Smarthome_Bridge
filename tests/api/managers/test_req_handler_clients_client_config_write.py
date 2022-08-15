from clients.client_controller import ClientRebootError, ConfigEraseError
from network.request import NoClientResponseException
from smarthome_bridge.api.api_manager import ApiManager
from system.api_definitions import ApiURIs
from test_helpers.dummy_client_controller import DummyClientController
from test_helpers.dummy_network_connector import DummyNetworkManager
from tests.api.managers.api_test_templates import request_execute_error, request_execute_status


def test_req_handler_clients_client_config_write(f_validator, f_api_manager: ApiManager, f_network: DummyNetworkManager,
                                                 f_credentials, f_client, f_client_config):
    # request_execute_status(ApiURIs.client_config_write.uri,
    #                        {"config": f_client_config},
    #                        f_network,
    #                        f_credentials,
    #                        f_validator)

    request_execute_error(ApiURIs.client_config_write.uri,  # TODO: fix
                          "NotImplementedError",
                          {"config": f_client_config},
                          f_network,
                          f_credentials,
                          f_validator)


# def test_req_handler_clients_client_config_write_validation_error(f_validator, f_api_manager: ApiManager,
#                                                                   f_network: DummyNetworkManager,
#                                                                   f_credentials, f_client):
#     request_execute_error(ApiURIs.client_config_write.uri,
#                           "ValidationError",
#                           {"test": 1234},
#                           f_network,
#                           f_credentials,
#                           f_validator)
