# from flask import Flask, redirect, url_for, request
# from bridge import MainBridge
# from typing import Optional
#
# # https://pythonbasics.org/flask-http-methods/
#
#
# def run_webinterface(bridge: MainBridge, port: int):
#     """Methods that launches the webinterface"""
#
#     app = Flask(__name__)
#     print("Launching webinterface")
#
#     @app.route('/')
#     def root():
#         return "<html><body><center><h1>Webinterface</h1><h2>{}</h2></body></html>".format(bridge.get_bridge_name())
#
#     # @app.route('/gadgets/all', methods=['POST', 'GET'])
#     # def login():
#     #     if request.method == 'POST':
#     #         user = request.form['nm']
#     #         return redirect(url_for('success', name=user))
#     #     else:
#     #         user = request.args.get('nm')
#     #         return redirect(url_for('success', name=user))
#
#     app.run(host='localhost', port=port)
