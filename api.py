import json

from flask import Flask, redirect, url_for, request, jsonify, Response
from typing import Optional


# https://pythonbasics.org/flask-http-methods/

__new_request_received = 1


def run_api(bridge, port: int):
    """Methods that launches the rest api to read, write and update gadgets via HTTP"""

    app = Flask(__name__)

    @app.route('/')
    def root():
        bridge.add_streaming_message("API", __new_request_received, "/")
        res_text = "Use /info, /gadgets, /connectors or /clients".format(bridge.get_bridge_name())
        response = jsonify(res_text)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    @app.route('/gadgets', methods=['GET'])
    def get_all_gadgets():
        bridge.add_streaming_message("API", __new_request_received, "/gadgets")
        gadget_list = bridge.get_all_gadgets()

        out_gadget_list: [dict] = []
        for gadget in gadget_list:
            json_gadget = gadget.serialized()
            out_gadget_list.append(json_gadget)

        buf_res = {"gadgets": out_gadget_list,
                   "gadget_count": len(out_gadget_list)}

        response = jsonify(buf_res)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    @app.route('/clients', methods=['GET'])
    def get_all_clients():
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
        bridge.add_streaming_message("API", __new_request_received, f"/system/serial_ports")
        return jsonify({"serial_ports": bridge.get_serial_ports()})

    @app.route('/system/flash_software', methods=['POST'])
    def flash_software():
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

    @app.route('/clients/<client_name>/write_config', methods=['POST'])
    def write_config_to_network(client_name: str):
        config_id = request.args.get('config_id')
        config = request.args.get('config')

        res_code = 200
        response = {"status": f"Writing config to client '{client_name}' was successful."}

        if config or config_id:

            config_arg = config
            if config_id:
                config_arg = config_id

            success, status = bridge.write_config_to_network_chip(config_arg, client_name)

            if not success:
                response = {"status": f"Error writing config to client '{client_name}': {status}"}
                res_code = 400
        else:
            response = {"status": f"No config selected."}
            res_code = 400

        return Response(json.dumps(response),
                        status=res_code,
                        mimetype='application/json')

    @app.route('/system/write_config', methods=['POST'])
    def write_config_to_serial():
        serial_port = request.args.get('serial_port')
        config_id = request.args.get('config_id')
        config = request.args.get('config')

        res_code = 200
        response = {"status": f"Writing config on port '{serial_port}' was successful."}

        if config or config_id:

            config_arg = config
            if config_id:
                config_arg = config_id

            success, status = bridge.write_config_to_chip(config_arg, serial_port)

            if not success:
                response = {"status": f"Error writing config on port '{serial_port}': {status}"}
                res_code = 400
        else:
            response = {"status": f"No config selected."}
            res_code = 400

        return Response(json.dumps(response),
                        status=res_code,
                        mimetype='application/json')

    # @app.route('/gadgets/all', methods=['POST', 'GET'])
    # def login():
    #     if request.method == 'POST':
    #         user = request.form['nm']
    #         return redirect(url_for('success', name=user))
    #     else:
    #         user = request.args.get('nm')
    #         return redirect(url_for('success', name=user))

    app.run(host='0.0.0.0', port=port)
