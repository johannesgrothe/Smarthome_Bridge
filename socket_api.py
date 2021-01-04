import asyncio
import socket
import threading


class SocketStreamingThread(threading.Thread):
    __clients: [(socket, str)]
    __termination_requested: bool
    __bridge = None
    __lock: threading.Lock

    def __init__(self, bridge):
        super().__init__()
        print("Streaming Thread Created")
        self.__bridge = bridge
        self.__clients = []
        self.__termination_requested = False
        self.__lock = threading.Lock()

    def add_client(self, client: socket, address: str):
        with self.__lock:
            self.__clients.append((client, address))
        print(f"Client '{address}' added to streaming thread")

    def run(self):
        try:
            while True:
                with self.__lock:
                    if self.__termination_requested:
                        break
                    message_to_publish: str = self.__bridge.get_streaming_message()
                    if message_to_publish:
                        if self.__clients:
                            print(f"[Socket publish]: '{message_to_publish}'")
                        iterator = 0
                        remove_clients: [int] = []
                        for client, address in self.__clients:
                            try:
                                client.sendall(message_to_publish.encode())
                            except (ConnectionResetError, BrokenPipeError):
                                print(f"Connection to '{address}' was lost")
                                # Save clients index for removal
                                remove_clients.append(iterator)
                            iterator += 1

                        # remove 'dead' clients
                        if remove_clients:
                            print("Removing stored client data")
                            remove_clients.reverse()
                            for client_index in remove_clients:
                                self.__clients.pop(client_index)

        except KeyboardInterrupt:
            print("Forcefully quitting client thread")
        with self.__lock:
            for client, address in self.__clients:
                try:
                    client.close()
                    print(f"Connection to '{address}' was closed")
                except Exception as e:
                    print(f"Error closing connection to '{address}'")

    def terminate(self):
        with self.__lock:
            self.__termination_requested = True


def run_socket_api(bridge, port: int):
    """Starts the socket API"""

    print(f"Starting Websocket API at port {port}")

    streaming_thread = SocketStreamingThread(bridge)
    streaming_thread.start()

    # get the hostname
    host = socket.gethostname()

    server_socket = socket.socket()  # get instance
    # look closely. The bind() function takes tuple as argument
    server_socket.bind((host, port))  # bind host address and port together

    # configure how many client the server can listen simultaneously
    server_socket.listen(5)
    print("Listening for clients...")

    try:
        while True:
            new_client, address = server_socket.accept()  # accept new connection
            if new_client:
                print("Connection from: " + str(address))
                streaming_thread.add_client(new_client, str(address))

    except KeyboardInterrupt:
        print("Forcefully quitting socket server")

    streaming_thread.terminate()
