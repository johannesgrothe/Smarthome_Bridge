import threading

import socket_connector
from network_server import NetworkServer, NetworkServerClient, Request,\
    response_callback_type, ClientDisconnectedException
from typing import Optional, Callable
import serial
import re
import os
import time
import json
from jsonschema import ValidationError


class SerialConnectionFailedException(Exception):
    def __init__(self):
        super().__init__()


class SerialServerClient(NetworkServerClient):

    _serial_client: serial.Serial

    def __init__(self, address: str, thread_method: Callable, client: serial.Serial):
        super().__init__(address, thread_method)
        self._socket_client = client

    @staticmethod
    def _format_request(req: Request) -> str:
        json_str = json.dumps(req.get_body())

        req_line = "!r_p[{}]_b[{}]_\n".format(req.get_path(),
                                              json_str)
        return req_line

    def send_request(self, req: Request):
        req_str = self._format_request(req)
        try:
            self._serial_client.write(req_str)
        except serial.PortNotOpenError:
            raise ClientDisconnectedException


class SerialServer(NetworkServer):

    _baud_rate: int

    def __init__(self, name: str, baud_rate: int):
        super().__init__(name)
        self._baud_rate = baud_rate

    def __del__(self):
        super().__del__()
        for client_address in self._clients:
            self._remove_client(client_address)

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
                    self._validate_request(json_body)
                except ValidationError:
                    self._logger.warning("Could not decode Request, Schema Validation failed.")
                    return None

                out_req = Request(path=req_dict["p"],
                                  session_id=json_body["session_id"],
                                  sender=json_body["sender"],
                                  receiver=json_body["receiver"],
                                  payload=json_body["payload"])

                return out_req
            except ValueError:
                return None
        return None

    @staticmethod
    def get_serial_ports() -> [str]:
        """Returns a list of all serial ports available to the system"""
        detected_ports = os.popen(f"ls /dev/tty*").read().strip("\n").split()
        valid_ports = []
        for port in detected_ports:
            if "usb" in port.lower():
                valid_ports.append(port)
        return valid_ports

    def _read_serial(self, serial_adapter: serial.Serial, timeout: int = 0) -> Optional[Request]:
        """Tries to read a line from the serial port"""

        timeout_time = time.time() + timeout
        try:
            ser_bytes = serial_adapter.readline().decode()
            message = ser_bytes[:-1]
            if message:
                self._logger.debug(f"Received: {message}")
            else:
                if message.startswith("Backtrace: 0x"):
                    self._logger.error("Client crashed with {}".format(message))
                    return None
                read_buf_req = self._decode_line(ser_bytes)
                if read_buf_req:
                    return read_buf_req
        except (FileNotFoundError, serial.serialutil.SerialException):
            self._logger.error("Lost connection to serial ports")
            return None
        except UnicodeDecodeError:
            self._logger.error("Unable to decode message")
            return None
        if (timeout > 0) and (time.time() > timeout_time):
            return None

    def _send_request_to_port(self, req: Request, serial_adapter: serial.Serial):
        json_str = json.dumps(req.get_body())

        req_line = "!r_p[{}]_b[{}]_\n".format(req.get_path(),
                                              json_str)
        self._logger.debug("Sending: {}".format(req_line[:-1]))
        serial_adapter.write(req_line.encode())

    def _accept_new_clients(self):
        for port in self.get_serial_ports():
            print(f"checking {port}")
            new_client = serial.Serial(port, self._baud_rate)
            client_thread_method = self._create_client_handler_thread(new_client)
            thread_name = f"client_receiver_{port}"
            client_thread_controller = self._thread_manager.add_thread(thread_name, client_thread_method)
            client_thread_controller.start()
            self._add_client(new_client, str(address))

    def _add_client(self, client: serial.Serial, address: str):
        self._clients[address] = client

    def _send_data(self, req: Request):
        pass


class SerialConnector(NetworkConnector):
    """Class to implement a MQTT connection module"""

    __client: serial.Serial
    __baud_rate: int
    __port: str
    __connected: bool

    def __init__(self, own_name: str, port: str, baud_rate: int):
        super().__init__(own_name)
        self.__baud_rate = baud_rate
        self.__port = port
        try:
            self.__client = serial.Serial(port=self.__port, baudrate=self.__baud_rate, timeout=1)
        except (FileNotFoundError, serial.serialutil.SerialException) as e:
            raise SerialConnectionFailedException
        self.__connected = True

        self._start_threads()

    def __del__(self):
        super().__del__()
        try:
            self.__client.close()
        except AttributeError:
            pass
        print(f"Closing Serial Connection to '{self.__port}@{self.__baud_rate}'")
        pass

    def __decode_line(self, line) -> Optional[Request]:
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
                    self._validate_request(json_body)
                except ValidationError:
                    self._logger.warning("Could not decode Request, Schema Validation failed.")
                    return None

                out_req = Request(path=req_dict["p"],
                                  session_id=json_body["session_id"],
                                  sender=json_body["sender"],
                                  receiver=json_body["receiver"],
                                  payload=json_body["payload"])

                return out_req
            except ValueError:
                return None
        return None

    def __read_serial(self, timeout: int = 0, monitor_mode: bool = False) -> Optional[Request]:
        """Tries to read a line from the serial port"""

        timeout_time = time.time() + timeout
        try:
            ser_bytes = self.__client.readline().decode()
            message = ser_bytes[:-1]
            if message:
                self._logger.debug(f"Received: {message}")
            if monitor_mode:
                print(message)
            else:
                if message.startswith("Backtrace: 0x"):
                    print("Client crashed with {}".format(message))
                    return None
                read_buf_req = self.__decode_line(ser_bytes)
                if read_buf_req:
                    return read_buf_req
        except (FileNotFoundError, serial.serialutil.SerialException):
            self._logger.error("Lost connection to serial ports")
            return None
        except UnicodeDecodeError:
            self._logger.error("Unable to decode message")
            return None
        if (timeout > 0) and (time.time() > timeout_time):
            return None

    def _send_data(self, req: Request):
        """Sends a request on the serial port"""

        json_str = json.dumps(req.get_body())

        req_line = "!r_p[{}]_b[{}]_\n".format(req.get_path(),
                                              json_str)
        self._logger.debug("Sending: {}".format(req_line[:-1]))
        self.__client.write(req_line.encode())
        return True

    def _receive_data(self) -> Optional[Request]:
        return self.__read_serial()
