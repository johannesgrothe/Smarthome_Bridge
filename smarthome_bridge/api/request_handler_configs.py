from typing import Callable, Optional

from jsonschema.exceptions import ValidationError

from network.request import Request
from smarthome_bridge.api.request_handler import RequestHandler
from smarthome_bridge.api.response_creator import ResponseCreator
from smarthome_bridge.network_manager import NetworkManager
from system.api_definitions import ApiURIs
from utils.client_config_manager import ClientConfigManager, ConfigAlreadyExistsException, ConfigDoesNotExistException


class RequestHandlerConfigs(RequestHandler):
    _configs: Optional[ClientConfigManager]

    def __init__(self, network: NetworkManager, configs: Optional[ClientConfigManager]):
        super().__init__(network)
        self._configs = configs

    def handle_request(self, req: Request) -> None:
        switcher = {
            ApiURIs.config_storage_get_all.uri: self._handle_get_all_configs,
            ApiURIs.config_storage_get.uri: self._handle_get_config,
            ApiURIs.config_storage_save.uri: self._handle_save_config,
            ApiURIs.config_storage_delete.uri: self._handle_delete_config
        }
        handler: Callable[[Request], None] = switcher.get(req.get_path(), None)
        if handler is not None:
            handler(req)

    def _handle_get_all_configs(self, req: Request):
        """
        Responds with the names and descriptions of all available configs

        :param req: empty Request
        :return: None
        """
        try:
            self._validator.validate(req.get_payload(), "api_empty_request")
        except ValidationError:
            ResponseCreator.respond_with_error(req, "ValidationError",
                                               f"Request validation error at '{ApiURIs.config_storage_get_all.uri}'")
            return

        if not self._configs:
            ResponseCreator.respond_with_error(req, "ConfigsNotAvailableError",
                                               f"Config-Storage is not available")
            return

        config_names = self._configs.get_config_names()
        all_configs = {}
        self._logger.info("fetching all configs")
        for config in config_names:
            if not config == "Example":
                conf = self._configs.get_config(config)
                all_configs[config] = conf["description"]
        payload = {"configs": all_configs}
        req.respond(payload)

    def _handle_get_config(self, req: Request):
        """
        Responds with the config for a given name, if there is none an error is returned

        :param req: Request containing the name of the requested config
        :return: None
        """
        try:
            self._validator.validate(req.get_payload(), "api_config_get_request")
        except ValidationError:
            ResponseCreator.respond_with_error(req, "ValidationError",
                                               f"Request validation error at '{ApiURIs.config_storage_get.uri}'")
            return

        if not self._configs:
            ResponseCreator.respond_with_error(req, "ConfigsNotAvailableError",
                                               f"Config-Storage is not available")
            return

        try:
            name = req.get_payload()["config"]
            config = self._configs.get_config(name)
            payload = {"config": config}
            req.respond(payload)
        except ConfigDoesNotExistException as err:
            ResponseCreator.respond_with_error(req=req, err_type="ConfigDoesNotExistException", message=err.args[0])

    def _handle_save_config(self, req: Request):
        """
        Saves the given config or overwrites an already existing config

        :param req: Request containing the config
        :return: None
        """
        try:
            self._validator.validate(req.get_payload(), "api_config_save")
        except ValidationError:
            ResponseCreator.respond_with_error(req, "ValidationError",
                                               f"Request validation error at '{ApiURIs.config_storage_save.uri}'")
            return

        if not self._configs:
            ResponseCreator.respond_with_error(req, "ConfigsNotAvailableError",
                                               f"Config-Storage is not available")
            return

        config = req.get_payload()["config"]
        overwrite = req.get_payload()["overwrite"]
        try:
            self._configs.write_config(config, overwrite=overwrite)
        except ConfigAlreadyExistsException as err:
            ResponseCreator.respond_with_error(req=req, err_type="ConfigAlreadyExistsException", message=err.args[0])
            return
        ResponseCreator.respond_with_success(req, "Config was saved successfully")

    def _handle_delete_config(self, req: Request):
        """
        Deletes the config for a given name, if there is no config, an error is returned

        :param req: Request containing name of the config
        :return: None
        """
        try:
            self._validator.validate(req.get_payload(), "api_config_delete_get")
        except ValidationError:
            ResponseCreator.respond_with_error(req, "ValidationError",
                                               f"Request validation error at '{ApiURIs.config_storage_delete.uri}'")
            return

        if not self._configs:
            ResponseCreator.respond_with_error(req, "ConfigsNotAvailableError",
                                               f"Config-Storage is not available")
            return

        name = req.get_payload()["name"]
        try:
            self._configs.delete_config_file(name)
        except ConfigDoesNotExistException as err:
            ResponseCreator.respond_with_error(req=req, err_type="ConfigDoesNotExistException", message=err.args[0])
            return
        ResponseCreator.respond_with_success(req, "Config was deleted successfully")
