from network_connector import Request
from network_connector_threaded import ThreadedNetworkConnector
from typing import Optional
import serial
import re
import time
import json
from jsonschema import validate, ValidationError


class SerialConnectionFailedException(Exception):
    def __init__(self):
        super().__init__()


class SerialConnector(ThreadedNetworkConnector):
    """Class to implement a MQTT connection module"""

    __client: serial.Serial
    __own_name: str
    __baud_rate: int
    __port: str
    __connected: bool

    def __init__(self, own_name: str, port: str, baud_rate: int):
        super().__init__()
        self.__own_name = own_name
        self.__baud_rate = baud_rate
        self.__port = port
        try:
            self.__client = serial.Serial(port=self.__port, baudrate=self.__baud_rate, timeout=1)
        except (FileNotFoundError, serial.serialutil.SerialException) as e:
            raise SerialConnectionFailedException
        self.__connected = True

        self._start_thread()

    def __del__(self):
        self._logger.info("destr33")
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
                    validate(json_body, self._request_validation_schema)
                except ValidationError:
                    self._logger.warning("Could not decode Request, Possible Reasons:"
                                         "Missing key(s) in request, Illegal Values for keys")
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
            # if ser_bytes.startswith("!"):
            # print("   -> {}".format(ser_bytes[:-1]))
            if monitor_mode:
                print(ser_bytes[:-1])
            else:
                if ser_bytes.startswith("Backtrace: 0x"):
                    print("Client crashed with {}".format(ser_bytes[:-1]))
                    return None
                read_buf_req = self.__decode_line(ser_bytes)
                if read_buf_req:
                    return read_buf_req
        except (FileNotFoundError, serial.serialutil.SerialException):
            print("Lost connection to serial port")
            return None
        if (timeout > 0) and (time.time() > timeout_time):
            return None

    def _send_data(self, req: Request):
        """Sends a request on the serial port"""

        json_str = json.dumps(req.get_body())

        req_line = "!r_p[{}]_b[{}]_\n".format(req.get_path(),
                                              json_str)
        # print("Sending '{}'".format(req_line[:-1]))
        self.__client.write(req_line.encode())
        return True

    def _receive_data(self) -> Optional[Request]:
        return self.__read_serial()

    def monitor(self):
        self.__read_serial(0, True)

    def connected(self) -> bool:
        return self.__connected


def main():
    import sys

    port = '/dev/cu.usbserial-0001'
    baudrate = 115200
    try:
        network_gadget = SerialConnector("TesTeR", port, baudrate)
    except OSError as e:
        print("Cannot connect to '{}'".format(port))
        sys.exit(1)

    buf_req = Request("smarthome/debug",
                      125543,
                      "me",
                      "you",
                      {"yolo": "blub"})

    network_gadget.send_request(buf_req)


if __name__ == '__main__':
    main()
