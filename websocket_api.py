import asyncio
import socket
import threading


class WebsocketStreamingThread(threading.Thread):
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
                            print(f"Sending to socket clients: '{message_to_publish}'")
                        for client, address in self.__clients:
                            try:
                                client.sendall(message_to_publish.encode())
                            except ConnectionResetError:
                                print(print(f"Connection to '{address}' was lost"))
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


class WebsocketAPIClientThread(threading.Thread):
    __parent_object = None
    __client: socket
    __address = None
    __termination_requested: bool

    def __init__(self, parent, client: socket, address):
        super().__init__()
        print(f"Creating new client thread for {address}")
        self.__parent_object = parent
        self.__client = client
        self.__address = address
        self.__termination_requested = False

    def run(self):
        self.__client.send(str.encode(f'Connected to: {self.__parent_object.get_bridge_name()}'))
        try:
            while not self.__termination_requested:
                # if parent_object
                pass
        except KeyboardInterrupt:
            print("Forcefully quitting client thread")
            self.__client.close()
            print(f"Connection to '{self.__address}' was closed")
        except ConnectionResetError:
            print(print(f"Connection to '{self.__address}' was lost"))
        print("Thread is beeing stopped...")

    def terminate(self):
        self.__termination_requested = true


def run_websocket_api(bridge, port: int):
    """Starts the websocket API"""

    print(f"Starting Websocket API at port {port}")

    #
    # # get the hostname
    # host = socket.gethostname()
    #
    # server_socket = socket.socket()  # get instance
    # # look closely. The bind() function takes tuple as argument
    # server_socket.bind((host, port))  # bind host address and port together
    #
    # # configure how many client the server can listen simultaneously
    # server_socket.listen(2)
    # conn, address = server_socket.accept()  # accept new connection
    # print("Connection from: " + str(address))
    # while True:
    #     # receive data stream. it won't accept data packet greater than 1024 bytes
    #     data = conn.recv(1024).decode()
    #     if not data:
    #         # if data is not received break
    #         break
    #     print("from connected user: " + str(data))
    #     data = input(' -> ')
    #     conn.send(data.encode())  # send data to the client


    client_threads: [WebsocketAPIClientThread] = []

    streaming_thread = WebsocketStreamingThread(bridge)
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
                # new_client_thread = WebsocketAPIClientThread(bridge, new_client, str(address))
                # new_client_thread.start()
                # client_threads.append(new_client_thread)

    except KeyboardInterrupt:
        print("Forcefully quitting socket server")

    streaming_thread.terminate()
