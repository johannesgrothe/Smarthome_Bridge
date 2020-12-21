from flask import Flask, redirect, url_for, request, jsonify
# from bridge import MainBridge
from typing import Optional

# https://pythonbasics.org/flask-http-methods/


def run_api(bridge, port: int):
    """Methods that launches the rest api to read, write and update gadgets via HTTP"""

    app = Flask(__name__)

    @app.route('/')
    def root():
        res_text = "Use /info, /gadgets, /connectors or /clients".format(bridge.get_bridge_name())
        response = jsonify(res_text)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    @app.route('/gadgets', methods=['GET'])
    def get_all_gadgets():
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
        bridge_name = bridge.get_bridge_name()
        gadget_list = bridge.get_all_gadgets()
        connector_list = bridge.get_all_connectors()
        client_list = bridge.get_all_clients()

        buf_res = {"bridge_name": bridge_name,
                   "gadget_count": len(gadget_list),
                   "connector_count": len(connector_list),
                   "client_count": len(client_list)}

        response = jsonify(buf_res)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    @app.route('/connectors', methods=['GET'])
    def get_all_connectors():
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

    # @app.route('/gadgets/all', methods=['POST', 'GET'])
    # def login():
    #     if request.method == 'POST':
    #         user = request.form['nm']
    #         return redirect(url_for('success', name=user))
    #     else:
    #         user = request.args.get('nm')
    #         return redirect(url_for('success', name=user))

    app.run(host='localhost', port=port)
