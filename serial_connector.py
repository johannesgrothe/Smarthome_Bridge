from network_connector_threaded import ThreadedNetworkConnector, Request, response_callback_type
from typing import Optional
import serial
import re
import time
import json
from jsonschema import ValidationError


class SerialConnectionFailedException(Exception):
    def __init__(self):
        super().__init__()


class SerialConnector(ThreadedNetworkConnector):
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

    def _get_respond_callback_for_id(self, req_id: int) -> Optional[response_callback_type]:
        return self._respond_to


def main():
    import sys

    port = '/dev/cu.usbserial-0001'
    baud_rate = 115200
    try:
        network_gadget = SerialConnector("TesTeR", port, baud_rate)
    except OSError:
        print("Cannot connect to '{}'".format(port))
        sys.exit(1)

    network_gadget.send_request("smarthome/debug", "you", {"yolo": "xD"})


if __name__ == '__main__':
    main()
