from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread

from conn import *


class Server:
    def __init__(self, ip, port):
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.bind((ip, port))

        print(f"Binding to {ip}:{port}")

    def start(self):
        """
        Holds forever.
        """
        self.sock.listen()
        print(f"Server listening")

        while True:
            client, addr = self.sock.accept()
            Thread(target=self.handle_client, args=(client, addr)).start()

    def handle_client(self, conn, addr):
        request = recv(conn)
        if not isinstance(request, dict) or "method" not in request:
            print(f"Invalid request from {addr}")
            return
        print(f"Request from {addr}; method={request['method']}")

        match request["method"]:
            case "ping":
                send(conn, {"status": "ok"})
