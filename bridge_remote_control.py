import socket
import argparse
import sys
import requests
import json
from typing import Optional

CONNECTION_MODES = ["direct", "bridge"]
DIRECT_NETWORK_MODES = ["serial", "mqtt"]
BRIDGE_FUNCTIONS = ["Write software to chip", "Write config to chip", "Reboot chip"]
DEFAULT_SW_BRANCH_NAMES = ["Enter own branch name", "master", "develop"]

FLASHING_SW_FAILURE = "[SOFTWARE_UPLOAD] Flashing failed."
FLASHING_SW_SUCCESS = "[SOFTWARE_UPLOAD] Flashing was successful."


def select_option(input_list: [str], category: str = None) -> int:
    """Presents every elem from the list and lets the user select one"""

    if category is None:
        print("Please select:")
    else:
        print("Please select a {}:".format(category))
    for i in range(len(input_list)):
        print("    {}: {}".format(i, input_list[i]))
    selection = None
    while selection is None:
        selection = input("Please select an option by entering its number:\n")
        try:
            selection = int(selection)
        except TypeError:
            selection = None
        if selection < 0 or selection >= len(input_list):
            print("Illegal input, try again.")
            selection = None
    return selection


def read_serial_ports_from_bridge() -> [str]:
    res_status, serial_port_data = send_api_request(f"{bridge_addr}:{api_port}/system/get_serial_ports")
    if res_status == 200:
        if "serial_ports" in serial_port_data:
            return serial_port_data["serial_ports"]
    return []


def send_api_command(url: str, content: str = "") -> (int, dict):
    if not url.startswith("http"):
        url = "http://" + url

    # print(f"Sending API command to '{url}'")
    response = requests.post(url, content)
    res_data = {}
    try:
        res_data = json.dumps(response.content.decode())
    except json.decoder.JSONDecodeError:
        pass
    return response.status_code, res_data


def send_api_request(url: str) -> (int, dict):
    if not url.startswith("http"):
        url = "http://" + url

    # print(f"Sending API request to '{url}'")
    response = requests.get(url)
    res_data = {}
    try:
        res_data = json.dumps(response.content.decode())
    except json.decoder.JSONDecodeError:
        pass
    return response.status_code, res_data


def read_socket_data_until(client: socket, print_lines: bool, exit_on_zero: bool = True) -> (bool, Optional[dict]):
    last_data_received: Optional[dict] = None
    try:
        while True:
            buf_rec_data = client.recv(5000).decode().strip("\n").strip("'").strip('"').strip()
            data: dict = {}

            rec_message: str = buf_rec_data
            rec_status: int = -1
            rec_sender: str = "ERROR"

            try:
                data: dict = json.loads(buf_rec_data)
            except json.decoder.JSONDecodeError:
                rec_status = -2

            if "message" in data:
                rec_message = data["message"]

            if "status" in data:
                rec_status = data["status"]

            if "sender" in data:
                rec_sender = data["sender"]

            if print_lines:  # Print lines if wanted
                print(f'-> [{rec_sender} / {"?" if rec_status == -1 else rec_status}]: {rec_message}')

            if "sender" in data or "status" in data:
                last_data_received = data
                if exit_on_zero:
                    if rec_status > 0:
                        break

    except KeyboardInterrupt:
        print("Forced Exit...")
        return False, last_data_received
    return True, last_data_received


def socket_connector(port: int, host: str, exit_lines: [str] = None) -> (bool, Optional[dict]):
    if host == "localhost":
        host = socket.gethostname()  # as both code is running on same pc

    try:
        client_socket = socket.socket()  # instantiate
        print(f"Connecting to {host}:{port}...")
        client_socket.connect((host, port))  # connect to the server
    except ConnectionRefusedError:
        print(f"Connection to {host}:{port} was refused")
        return False, ""
    print("Connected.")

    buf_res, last_data_received = read_socket_data_until(client_socket, exit_lines)

    client_socket.close()  # close the connection
    print("Connection Closed")
    return buf_res, last_data_received


if __name__ == '__main__':
    # Argument-parser
    parser = argparse.ArgumentParser(description='Script to upload configs to the controller')
    parser.add_argument('--connection_mode',
                        help='Use "bridge" to connect to bridge or "direct" to connect to chip directly',
                        type=str)
    parser.add_argument('--bridge_socket_port', help='Port of the Socket Server', type=int)
    parser.add_argument('--bridge_api_port', help='Port of the Socket Server', type=int)
    parser.add_argument('--bridge_addr', help='Address of the Socket Server', type=str)
    ARGS = parser.parse_args()

    if ARGS.connection_mode:
        connection_mode = ARGS.connection_mode
    else:
        connection_mode = CONNECTION_MODES[select_option(CONNECTION_MODES, "Connection Mode")]

    if connection_mode == "bridge":

        socket_client: socket = None

        if ARGS.bridge_addr:
            bridge_addr = ARGS.bridge_addr
        else:
            bridge_addr = input("Please enter server address: ")

        if ARGS.bridge_socket_port:
            socket_port = ARGS.bridge_socket_port
        else:
            try:
                socket_port = int(input("Please enter server socket port: "))
            except ValueError:
                print("Illegal port.")
                sys.exit(1)

        if ARGS.bridge_api_port:
            api_port = ARGS.bridge_api_port
        else:
            try:
                api_port = int(input("Please enter server API port: "))
            except ValueError:
                print("Illegal port.")
                sys.exit(1)

        print("Connecting to bridge...")
        status, _ = send_api_request(f"{bridge_addr}:{api_port}")
        if status == 200:
            print("Connected to API")
        else:
            print("API could not be reached")
            sys.exit(2)

        buf_bridge_addr = bridge_addr
        if bridge_addr == "localhost":
            buf_bridge_addr = socket.gethostname()

        try:
            socket_client = socket.socket()
            socket_client.connect((buf_bridge_addr, socket_port))  # connect to the server
        except ConnectionRefusedError:
            print(f"Connection to {buf_bridge_addr}:{socket_port} was refused")
            sys.exit(3)
        print("Connected to Bridge Socket")

        status, bridge_data = send_api_request(f"{bridge_addr}:{api_port}/info")
        if status != 200:
            print("Could not load information from the bridge.")
            sys.exit(4)

        print("Connected to bridge '{}'".format(bridge_data["bridge_name"]))
        print(" -> Running since: {}".format(bridge_data["running_since"]))
        print(" -> Software Branch: {}".format(bridge_data["software_branch"]))
        print(" -> Software Commit: {}".format(bridge_data["software_commit"]))
        print(" -> Clients: {}".format(bridge_data["client_count"]))
        print(" -> Connectors: {}".format(bridge_data["connector_count"]))
        print(" -> Gadgets: {}".format(bridge_data["gadget_count"]))

        bridge_clients: [dict] = []

        max_name_len = 0
        max_branch_name_len = 0

        status, client_data = send_api_request(f"{bridge_addr}:{api_port}/clients")

        if status != 200:
            print("Could not load clients from the bridge.")
            sys.exit(5)

        json_client_data = json.loads(client_data)

        for client_data in json_client_data["clients"]:
            try:
                buf_client = {"boot_mode": client_data["boot_mode"],
                              "name": client_data["name"],
                              "is_active": client_data["is_active"],
                              "sw_branch": client_data["sw_branch"] if client_data["sw_branch"] else "unknown",
                              "sw_version": client_data["sw_version"] if client_data["sw_version"] else "unknown",
                              "sw_uploaded": client_data["sw_uploaded"] if client_data["sw_uploaded"] else "unknown"}

                # determine the maximum lengths of name & branch for displaying them
                name_len = len(buf_client["name"])
                branch_len = len(buf_client["sw_branch"])

                if name_len > max_name_len:
                    max_name_len = name_len

                if branch_len > max_branch_name_len:
                    max_branch_name_len = branch_len

                bridge_clients.append(buf_client)
            except KeyError:
                print("A gadget could not be loaded")

        client_names: [str] = []

        print("Clients loaded:")
        for client_data in bridge_clients:
            client_names.append(client_data["name"])
            client_pattern = " -> {} | Commit: {} | Branch: {} | {}"
            print(client_pattern.format(client_data["name"] + " " * (max_name_len - len(client_data["name"])),
                                        client_data["sw_version"],
                                        client_data["sw_branch"] + " " * (max_branch_name_len - len(client_data["name"])),
                                        ("Active" if client_data["is_active"] else "Inactive")
                                        )
                  )

        task_option = select_option(BRIDGE_FUNCTIONS, "What to do")

        keep_running = True

        while keep_running:
            if task_option == 0:
                # Write software to chip
                selected_branch = select_option(DEFAULT_SW_BRANCH_NAMES, "Branch")
                selected_branch_name = ""
                if selected_branch == 0:
                    selected_branch_name = input("Enter branch name:")
                else:
                    selected_branch_name = DEFAULT_SW_BRANCH_NAMES[selected_branch]
                print(f"Writing software branch '{selected_branch_name}':")

                detected_serial_ports = read_serial_ports_from_bridge()
                sel_ser_port = 0
                sel_ser_port_str = ""
                if detected_serial_ports:
                    possible_serial_ports = ["default"] + detected_serial_ports
                    sel_ser_port_str = select_option(possible_serial_ports, "Serial Port for Upload")
                    sel_port_str = possible_serial_ports[sel_ser_port]

                serial_port_option = f'%serial_port={sel_ser_port_str}' if sel_ser_port else ''
                flash_path = f"/system/flash_software?branch_name={selected_branch_name}{serial_port_option}"

                status, resp_data = send_api_command(f"{bridge_addr}:{api_port}{flash_path}")
                if status != 200:
                    print(f"Software flashing could no be started:\n{resp_data}")
                    continue

                # Read lines from socket port
                success, last_data = read_socket_data_until(socket_client, True)

                if not success:
                    print("Unknown error or interruption while reading socket data")
                    continue

                if last_data["status"] == 0:
                    print("Flashing Software was successful")
                elif last_data["status"] != 0:
                    print("Flashing Software failed")
                else:
                    print("[Script Error] Problem in flashing status detection")

            elif task_option == 1:
                # Write config to chip
                selected_cip = client_names[select_option(client_names, "Chip")]
                print(f"Writing config to '{selected_cip}'...")
                pass

            elif task_option == 2:
                # restart client
                selected_cip = client_names[select_option(client_names, "Chip")]
                print(f"Restarting client '{selected_cip}'...")

    print("Quitting...")
