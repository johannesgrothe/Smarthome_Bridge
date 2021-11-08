import json
import re
from typing import Optional

import serial
import threading
from jsonschema import ValidationError

from network.network_connector import REQ_VALIDATION_SCHEME_NAME
from network.network_server_client import NetworkServerClient
from network.request import Request


class SerialConnectionFailedException(Exception):
    def __init__(self):
        super().__init__()


class SerialServerClient(NetworkServerClient):
    _serial_client: serial.Serial
    _is_closed: bool

    def __init__(self, host_name: str, address: str, client: serial.Serial):
        super().__init__(host_name, address)
        self._serial_client = client
        self._is_closed = False
        self._thread_manager.start_threads()

    def __del__(self):
        super().__del__()
        self._serial_client.close()

    @staticmethod
    def _format_request(req: Request) -> str:
        json_str = json.dumps(req.get_body())

        req_line = "!r_p[{}]_b[{}]_\n".format(req.get_path(),
                                              json_str)
        return req_line

    def _send(self, req: Request):
        """Sends a request on the serial port"""

        json_str = json.dumps(req.get_body())

        req_line = "!r_p[{}]_b[{}]_\n".format(req.get_path(),
                                              json_str)
        self._logger.debug("Sending: {}".format(req_line[:-1]))
        out_data = req_line.encode()
        bytes_written = self._serial_client.write(out_data)
        if not bytes_written == len(out_data):
            self._logger.error(f"Problem sending request: only {bytes_written} of {len(out_data)} bytes written.")

    def _decode_line(self, line) -> Optional[Request]:
        """Decodes a line and extracts a request if there is any"""

        if line[:3] == "!r_":
            elems = re.findall("_([a-z])\[(.+?)\]", line)
            req_dict = {}
            for elem_type, val in elems:
                if elem_type in req_dict:
                    self._logger.warning("Double key in request: '{}'".format(elem_type))
                    return None
                else:
                    req_dict[elem_type] = val
            for key in ["p", "b"]:
                if key not in req_dict:
                    self._logger.warning("Missing key in request: '{}'".format(key))
                    return None
            try:
                json_body = json.loads(req_dict["b"])

                try:
                    self._validator.validate(json_body, REQ_VALIDATION_SCHEME_NAME)
                except ValidationError:
                    self._logger.warning("Could not decode Request, Schema Validation failed.")
                    return None

                out_req = Request(path=req_dict["p"],
                                  session_id=json_body["session_id"],
                                  sender=json_body["sender"],
                                  receiver=json_body["receiver"],
                                  payload=json_body["payload"],
                                  connection_type=f"Serial[{self._address}]")

                return out_req
            except ValueError:
                return None
        return None

    def _receive(self) -> Optional[Request]:
        try:
            ser_bytes = self._serial_client.readline().decode()
            message = ser_bytes[:-1]
            if not message:
                return None
            if message.startswith("Backtrace: 0x"):
                self._logger.info("Client crashed with {}".format(message))
                return None
            read_buf_req = self._decode_line(ser_bytes)
            if not read_buf_req:
                return None
            return read_buf_req

        except (FileNotFoundError, serial.serialutil.SerialException):
            self._is_closed = True
            return None
        except UnicodeDecodeError:
            self._logger.error("Unable to decode message")
            return None

    def is_connected(self) -> bool:
        return not self._is_closed and self._serial_client.isOpen()
