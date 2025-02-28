from typing import Optional

import typer

from toolkit.direct_mqtt_connection_toolkit import DirectMqttConnectionToolkit
from toolkit.direct_serial_connection_toolkit import DirectSerialConnectionToolkit


def main():
    app = typer.Typer()

    @app.command()
    def connect_via_serial():
        toolkit_instance = DirectSerialConnectionToolkit()
        toolkit_instance.run()

    @app.command()
    def connect_via_mqtt(ip: str = "localhost", port: int = 1883, username: Optional[str] = None,
                         password: Optional[str] = None):
        toolkit_instance = DirectMqttConnectionToolkit(
            ip,
            port,
            username,
            password
        )
        toolkit_instance.run()

    app()


if __name__ == "__main__":
    main()
