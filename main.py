import serial
import time
import argparse
import json
import re
from pprint import pprint

parser = argparse.ArgumentParser(description='Script to upload configs to the controller')
parser.add_argument('--port', help='serial port to connect to.')
parser.add_argument('--baudrate', help='baudrate for the serial connection.')
parser.add_argument('--config_file', help='path to the config that should be uploaded.')
parser.add_argument('--wifi_ssid', help='ssid to be uploaded.')
parser.add_argument('--wifi_pw', help='password to be uploaded.')
parser.add_argument('--mqtt_ip', help='mqtt ip to be uploaded.')
parser.add_argument('--mqtt_port', help='port to be uploaded.')
parser.add_argument('--mqtt_user', help='mqtt username to be uploaded.')
parser.add_argument('--mqtt_pw', help='mqtt password to be uploaded.')

parser.add_argument('--network_only', action='store_true', help='needs a config file. uploads only the network config.')
parser.add_argument('--id_only', action='store_true', help='needs a config file. uploads only the id.')
ARGS = parser.parse_args()


def decode_line(line):
    if line[:3] == "!r_":
        elems = re.findall("_([a-z])\[(.+?)\]", line)
        req_dict = {}
        for type, val in elems:
            if type in req_dict:
                print("Double key in request: '{}'".format(type))
                return False
            else:
                req_dict[type] = val
        pprint(req_dict)
        for key in ["p", "b"]:
            if key not in req_dict:
                print("Missig key in request: '{}'".format(key))
                return False
        try:
            json_body = json.loads(req_dict["b"])
            req_dict["b"] = json_body
            return req_dict
        except ValueError:
            return False
    return False


def read_serial(timeout=5):
    print("Reading from serial port...")
    timeout_time = time.time() + timeout
    while True:
        try:
            ser_bytes = ser.readline().decode("utf-8")
            buf_req = decode_line(ser_bytes)
            if buf_req:
                return buf_req
        except (FileNotFoundError, serial.serialutil.SerialException):
            print("Lost connection to serial port")
            return False
        if time.time() > timeout_time:
            print("Connection timed out")
            return False


if __name__ == '__main__':

    print(decode_line("!r_p[yolokopter]_b[{}]_"))

    if ARGS.port:
        serial_port = ARGS.port
    else:
        serial_port = '/dev/cu.SLAB_USBtoUART'

    if ARGS.baudrate:
        serial_baudrate = ARGS.baudrate
    else:
        serial_baudrate = 115200

    serial_active = False
    try:
        ser = serial.Serial(port=serial_port, baudrate=serial_baudrate)
        ser.flushInput()
        serial_active = True
    except (FileNotFoundError, serial.serialutil.SerialException) as e:
        print("Unable to connect to serial port '{}'".format(serial_port))

    if serial_active:
        read_buffer = read_serial()
        if (read_buffer):
            pprint(read_buffer)
