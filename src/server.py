from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread

import config
import conn


class Server:
    def __init__(self):
        self.jobs = []

        self.server = socket(AF_INET, SOCK_STREAM)
        self.server.bind((config.get("server_ip"), config.get("server_port")))

    def start(self):
        print("Starting server.")

        self.server.listen()

        while True:
            sock, addr = self.server.accept()
            Thread(target=self.handle, args=(sock, addr)).start()

    def handle(self, sock, addr):
        print("Connection:", addr)

        data = conn.recv(sock)
        if "type" in data and "action" in data:
            if data["type"] == "worker":
                self.handle_worker(sock, data)
        else:
            conn.send(sock, "invalid")

    def handle_worker(self, sock, data):
        if data["action"] == "request_work":
            conn.send(sock, " " * int(1e8), True)
