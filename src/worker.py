from socket import socket, AF_INET, SOCK_STREAM

import config
import conn


def start():
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect((config.get("server_ip"), config.get("server_port")))

    conn.send(sock, {"test": 1, "b": [1, 2, 3]})
    print(conn.recv(sock))
