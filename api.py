import json

from flask import Flask, redirect, url_for, request, jsonify, Response
from jsonschema import validate, ValidationError
from typing import Optional


# https://pythonbasics.org/flask-http-methods/

__new_request_received = 1


def generate_valid_response(json_body, json_schema_file) -> Response:
    try:
        with open(json_schema_file, 'r') as file:
            json_schema = json.load(file)
            validate(json_body, json_schema)
            response = jsonify(json_body)

            response.headers.add('Access-Control-Allow-Origin', '*')
            return response

    except FileNotFoundError:
        print(f"Json Schema'{json_schema_file}' was not found")
        response = {"status": f"Internal Server Error while validating response: "
                              f"Validation failed. Please file a bug report."}

    except ValidationError:
        print(f"Validating response with '{json_schema_file}' failed.")
        response = {"status": f"Internal Server Error while validating response: "
                              f"Validation schema not found. Please file a bug report."}

    res_code = 500
    response = Response(json.dumps(response),
                        status=res_code,
                        mimetype='application/json')

    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


def run_api(bridge, port: int):
    """Methods that launches the rest api to read, write and update gadgets via HTTP"""

    app = Flask(__name__)

    @app.route('/')
    def root():
        """
        Flask API response method
        Category: Clients
        Title: Root
        Description: Sends back some example paths to get actual information from
        Input Schema: None
        Output Schema: None
        :return: Response to the request
        """
        bridge.add_streaming_message("API", __new_request_received, "/")
        res_text = "Use /info, /gadgets, /connectors or /clients".format(bridge.get_bridge_name())
        response = jsonify(res_text)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    @app.route('/gadgets', methods=['GET'])
    def get_all_gadgets():
        """
        Flask API response method
        Category: Clients
        Title: Read Gadget Information
        Description: Reads information for all the gadgets from the bridge
        Input Schema: 'api_get_all_gadgets_response.json'
        Output Schema: None
        :return: Response to the request
        """
        bridge.add_streaming_message("API", __new_request_received, "/gadgets")
        gadget_list = bridge.get_all_gadgets()

        out_gadget_list: [dict] = []
        for gadget in gadget_list:
            json_gadget = gadget.serialized()
            out_gadget_list.append(json_gadget)

        buf_res = {"gadgets": out_gadget_list,
                   "gadget_count": len(out_gadget_list)}

        return generate_valid_response(buf_res, 'api_get_all_gadgets_response.json')

    @app.route('/clients', methods=['GET'])
    def get_all_clients():
        """
        Flask API response method
        Category: Clients
        Title: Read Client Information
        Description: Reads information for all the clients from the bridge
        Input Schema: None
        Output Schema: 'api_get_all_clients_response.json'
        :return: Response to the request
        """
        bridge.add_streaming_message("API", __new_request_received, "/clients")
        client_list = bridge.get_all_clients()

        out_client_list: [dict] = []
        for client in client_list:
            json_client = client.serialized()
            out_client_list.append(json_client)

        buf_res = {"clients": out_client_list,
                   "client_count": len(out_client_list)}

        response = jsonify(buf_res)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    @app.route('/info', methods=['GET'])
    def get_info():
        """
        Flask API response method
        Category: Bridge
        Title: Read Bridge Information
        Description: Reads information for the bridge
        Input Schema: None
        Output Schema: 'api_get_info_response.json'
        :return: Response to the request
        """
        bridge.add_streaming_message("API", __new_request_received, "/info")
        bridge_name = bridge.get_bridge_name()
        gadget_list = bridge.get_all_gadgets()
        connector_list = bridge.get_all_connectors()
        client_list = bridge.get_all_clients()

        buf_res = {"bridge_name": bridge_name,
                   "software_commit": bridge.get_sw_commit(),
                   "software_branch": bridge.get_sw_branch(),
                   "running_since": bridge.get_time_launched().strftime("%Y-%m-%d %H:%M:%S"),
                   "gadget_count": len(gadget_list),
                   "connector_count": len(connector_list),
                   "client_count": len(client_list)}

        response = jsonify(buf_res)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    @app.route('/connectors', methods=['GET'])
    def get_all_connectors():
        """
        Flask API response method
        Category: Connectors
        Title: Read Connector Information
        Description: Reads information for all the connectors configured on the bridge
        Input Schema: None
        Output Schema: None
        :return: Response to the request
        """
        bridge.add_streaming_message("API", __new_request_received, "/connectors")
        connector_list = bridge.get_all_connectors()

        out_gadget_list: [dict] = []
        for connector in connector_list:
            json_connector = connector.serialized()
            out_gadget_list.append(json_connector)

        buf_res = {"connectors": out_gadget_list,
                   "connector_count": len(out_gadget_list)}

        response = jsonify(buf_res)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    @app.route('/clients/<client_name>/restart', methods=['POST'])
    def restart_client(client_name):
        """
        Category: Clients
        Title: Restart Client
        Description: Restarts the client specified in the url parameter
        Input Schema: None
        Output Schema: None
        Param <client_name>: Name of the client that should be rebooted.
        :return: Response to the request
        """
        bridge.add_streaming_message("API", __new_request_received, f"/clients/{client_name}/restart")
        gadget = bridge.get_client(client_name)
        if gadget is None:
            return Response('{"status": "Gadget name was not found"}', status=404, mimetype='application/json')
        success = bridge.restart_client(gadget)
        if success:
            return Response('{"status": "Reboot was successful"}', status=200, mimetype='application/json')
        return Response('{"status": "Error triggering reboot on client"}', status=400, mimetype='application/json')

    @app.route('/system/get_serial_ports', methods=['GET'])
    def get_serial_ports():
        """
        Category: Bridge
        Title: Read Serial Ports
        Description: Reads all of the available serial ports to the bridge
        Input Schema: None
        Output Schema: None
        :return: Response to the request
        """
        bridge.add_streaming_message("API", __new_request_received, f"/system/serial_ports")
        return jsonify({"serial_ports": bridge.get_serial_ports()})

    @app.route('/system/flash_software', methods=['POST'])
    def flash_software():
        """
        Category: Clients
        Title: Flash Software
        Description: Flashes the newest software commit of the selected branch to the chip connected to the selected serial port
        Output Schema: None
        Param 'branch_name': Software-branch shat should be flashed to the chip
        Param 'serial_port': Serial port the chip is connected to
        :return: Response to the request
        """
        bridge.add_streaming_message("API", __new_request_received, "/system/flash_software")
        branch_name = request.args.get('branch_name')
        serial_port = request.args.get('serial_port')

        success, status = bridge.flash_software(branch_name, serial_port)

        str_branch = branch_name if branch_name is not None else "master"
        str_port = serial_port if serial_port is not None else "default"

        suc_resp = f"Flashing software from '{str_branch}' on port '{str_port}'started."
        suc_resp += f"Connect to port {bridge.get_socket_api_port()} to view progress."

        response: dict = {"status": suc_resp}
        res_code = 200

        if not success:
            response = {"status": f"Error flashing software from '{str_branch}' on port '{str_port}': {status}"}
            res_code = 400

        return Response(json.dumps(response),
                        status=res_code,
                        mimetype='application/json')

    @app.route('/system/configs', methods=['GET'])
    def get_config_names():
        """
        Category: Bridge
        Title: Read Bridge Configs
        Description: Reads the names of the stored client configs from the bridge
        Input Schema: None
        Output Schema: None
        :return: Response to the request
        """
        config_names = bridge.load_config_names()
        return jsonify({"config_names": config_names})

    @app.route('/system/configs/<config_name>', methods=['GET'])
    def get_config(config_name: str):
        """
        Category: Bridge
        Title: Read Config
        Description: Reads the config with the selected name from the bridge
        Input Schema: None
        Output Schema: 'client_config.json'
        Param <config_name>: Name of the config to read
        :return: Response to the request
        """
        config_data = bridge.load_config(config_name)
        return jsonify({"config_data": config_data})

    @app.route('/clients/<client_name>/write_config', methods=['POST'])
    def write_config_to_network(client_name: str):
        """
        Category: Client
        Title: Write Config not Network Client
        Description: Writes the config contained in the request body to the selected client
        Input Schema: 'client_config.json'
        Output Schema: None
        Param <client_name>: Name of the client to write the config to
        :return: Response to the request
        """
        json_payload = request.json
        config = json_payload

        res_code = 200
        response = {"status": f"Writing config to client '{client_name}' was successful."}

        if config:

            success, status = bridge.write_config_to_network_chip(config, client_name)

            if not success:
                response = {"status": f"Error writing config to client '{client_name}': {status}"}
                res_code = 400
        else:
            response = {"status": f"No config selected."}
            res_code = 400

        response_str = json.dumps(response)

        return Response(response_str,
                        status=res_code,
                        mimetype='application/json')

    @app.route('/system/write_config', methods=['POST'])
    def write_config_to_serial():
        """
        Category: Client
        Title: Write Config not Serial Client
        Description: Writes the config contained in the request body to the client connected via serial
        Input Schema: 'client_config.json'
        Output Schema: None
        Param 'serial_port': Can be set to manually select the serial port the client is connected to
        :return: Response to the request
        """
        serial_port = request.args.get('serial_port')

        json_payload = request.json
        config = json_payload

        res_code = 200
        response: dict = {"status": f"Writing config on port '{serial_port}' was successful."}

        if config:

            success, status = bridge.write_config_to_chip(config, serial_port)

            if not success:
                response = {"status": f"Error writing config on port '{serial_port}': {status}"}
                res_code = 400
        else:
            response = {"status": f"No config selected."}
            res_code = 400

        response_str = json.dumps(response)

        return Response(response_str,
                        status=res_code,
                        mimetype='application/json')

    # @app.route('/gadgets/all/<yolo>/<xxx>', methods=['POST', 'GET'])
    # def login():
    #     if request.method == 'POST':
    #         user = request.form['nm']
    #         return redirect(url_for('success', name=user))
    #     else:
    #         user = request.args.get('nm')
    #         return redirect(url_for('success', name=user))
    #
    # app.run(host='0.0.0.0', port=port)
