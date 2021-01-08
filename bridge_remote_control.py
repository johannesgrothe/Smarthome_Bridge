import socket
import argparse
import sys
import requests
import json

CONNECTION_MODES = ["direct", "bridge"]
DIRECT_NETWORK_MODES = ["serial", "mqtt"]


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


def send_api_request(url: str) -> (int, str):
    if not url.startswith("http"):
        url = "http://" + url

    # print(f"Sending API request to '{url}'")
    response = requests.get(url)
    return response.status_code, response.content.decode()


def socket_connector(port: int, host: str):
    if host == "localhost":
        host = socket.gethostname()  # as both code is running on same pc

    try:
        client_socket = socket.socket()  # instantiate
        print(f"Connecting to {host}:{port}...")
        client_socket.connect((host, port))  # connect to the server
    except ConnectionRefusedError:
        print(f"Connection to {host}:{port} was refused")
        return
    print("Connected.")

    try:
        while True:
            # client_socket.send(message.encode())  # send message
            data = client_socket.recv(5000).decode()  # receive response

            print('-> ' + data)  # show in terminal

    except KeyboardInterrupt:
        print("Forced Exit...")
    client_socket.close()  # close the connection
    print("Connection Closed")


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

        json_bridge_data = json.loads(bridge_data)

        print("Connected to bridge '{}'".format(json_bridge_data["bridge_name"]))
        print(" -> Running since: {}".format(json_bridge_data["running_since"]))
        print(" -> Software Branch: {}".format(json_bridge_data["software_branch"]))
        print(" -> Software Commit: {}".format(json_bridge_data["software_commit"]))
        print(" -> Clients: {}".format(json_bridge_data["client_count"]))
        print(" -> Connectors: {}".format(json_bridge_data["connector_count"]))
        print(" -> Gadgets: {}".format(json_bridge_data["gadget_count"]))

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

        print("Clients loaded:")
        for client_data in bridge_clients:
            client_pattern = " -> {} | Commit: {} | Branch: {} | {}"
            print(client_pattern.format(client_data["name"] + " " * (max_name_len - len(client_data["name"])),
                                        client_data["sw_version"],
                                        client_data["sw_branch"] + " " * (max_branch_name_len - len(client_data["name"])),
                                        ("Active" if client_data["is_active"] else "Inactive")
                                        )
                  )
