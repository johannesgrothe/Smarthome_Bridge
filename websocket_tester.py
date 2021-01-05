import socket
import argparse


def client_program(port: int, host: str):
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


def manual_tester(port: int):
    host = socket.gethostname()  # as both code is running on same pc

    client_socket = socket.socket()  # instantiate
    client_socket.connect((host, port))  # connect to the server
    print("connected")

    message = input(" -> ")  # take input

    while message.lower().strip() != 'bye':
        client_socket.send(message.encode())  # send message
        data = client_socket.recv(1024).decode()  # receive response

        print('Received from server: ' + data)  # show in terminal

        message = input(" -> ")  # again take input

    client_socket.close()  # close the connection


if __name__ == '__main__':
    # Argument-parser
    parser = argparse.ArgumentParser(description='Script to upload configs to the controller')
    parser.add_argument('--socket_port', help='Port of the Socket Server', type=int)
    parser.add_argument('--socket_addr', help='Address of the Socket Server', type=str)
    ARGS = parser.parse_args()

    if ARGS.socket_port and ARGS.socket_addr:
        client_program(ARGS.socket_port, ARGS.socket_addr)
    else:
        print("No port/address Configured.")
