from flask import Flask, redirect, url_for, request
from bridge import MainBridge
from typing import Optional

# https://pythonbasics.org/flask-http-methods/


def run_api(name: str, bridge: MainBridge):
    """Methods that launches the rest api to read, write and update gadgets via HTTP"""

    app = Flask(name)

    @app.route('/')
    def hello_world():
        return "<html><body><h1>{}</h1></body></html>".format(bridge.get_bridge_name())

    @app.route('/login', methods=['POST', 'GET'])
    def login():
        if request.method == 'POST':
            user = request.form['nm']
            return redirect(url_for('success', name=user))
        else:
            user = request.args.get('nm')
            return redirect(url_for('success', name=user))

    app.run()
