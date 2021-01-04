import asyncio
import socket


def client_program():
    host = socket.gethostname()  # as both code is running on same pc
    port = 5003  # socket server port number

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


def manual_tester():
    host = socket.gethostname()  # as both code is running on same pc
    port = 6200  # socket server port number

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
    client_program()
    # manual_tester()
