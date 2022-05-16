from typing import Callable, Optional

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from multiprocessing import Process
from werkzeug.serving import make_server
import threading

from network.auth_container import CredentialsAuthContainer
from network.network_server import NetworkServer
from network.rest_server_request_manager import RestServerRequestManager, NoResponseReceivedError
from system.api_definitions import ApiURIs
from system.utils.api_endpoint_definition import ApiAccessType


# TODO: make get_endpoints() public
GET_ROUTES = [x.uri for x in ApiURIs.get_endpoints() if x.access_type == ApiAccessType.read]
UPDATE_ROUTES = [x.uri for x in ApiURIs.get_endpoints() if x.access_type == ApiAccessType.write]


class RestServerThread(threading.Thread):

    def __init__(self, app, port):
        threading.Thread.__init__(self)
        self.server = make_server('0.0.0.0', port, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()


class RestServer(NetworkServer):
    _port: int
    _app: Flask
    _cors: CORS
    _server_thread: Process

    def __init__(self, hostname: str, port: int):
        super().__init__(hostname)
        self._port = port
        self._logger.info(f"Rest api running at {self._port}")
        self._create_api()
        self._server = RestServerThread(self._app, self._port)
        self._server.start()
        self._thread_manager.start_threads()

    def __del__(self):
        super().__del__()
        self._server.shutdown()

    @staticmethod
    def _generate_response(json_body: dict, status_code: int = 200) -> Response:
        """
        Generates a http response out of the given body and status code

        :param json_body: Json body of the response
        :param status_code: Status code to attach
        :return: The flask response object
        """

        response = jsonify(json_body)
        response.status_code = status_code
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    def _generate_get_method(self, path: str) -> Callable[[], Response]:
        def method():
            auth = self._extract_credentials_method()
            response_manager = RestServerRequestManager(self.get_hostname(), path, {}, auth)
            self._publish(response_manager.get_request())
            try:
                response_req = response_manager.await_response()
                return self._generate_response(response_req.get_payload(), 200)
            except NoResponseReceivedError as err:
                return self._generate_response({"status": err.args[0]}, 500)

        return method

    def _generate_update_method(self, path: str) -> Callable[[], Response]:
        def method():
            auth = self._extract_credentials_method()
            payload = request.json
            response_manager = RestServerRequestManager(self.get_hostname(), path, payload, auth)
            self._publish(response_manager.get_request())
            return self._generate_response({}, 200)

        return method

    @staticmethod
    def _extract_credentials_method() -> Optional[CredentialsAuthContainer]:
        auth = request.authorization
        if not auth:
            return None
        user = auth.get("username")
        pw = auth.get("password")
        if not user or not pw:
            return None
        return CredentialsAuthContainer(user, pw)

    def _create_api(self):
        self._logger.info("Launching API")
        self._app = Flask(__name__)

        self._app.config['CORS_HEADERS'] = ['Content-Type', 'access-control-allow-origin']

        self._cors = CORS(self._app)

        @self._app.route('/test')
        def test_path():
            res_body = {"test": "hello"}
            return self._generate_response(res_body)

        for route in GET_ROUTES:
            flask_route = f"/{route}"
            self._app.add_url_rule(flask_route, route, self._generate_get_method(route))

        for route in UPDATE_ROUTES:
            flask_route = f"/{route}"
            self._app.add_url_rule(flask_route, route, self._generate_update_method(route), methods=["POST"])
