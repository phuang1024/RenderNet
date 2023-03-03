import struct
from socket import socket, AF_INET, SOCK_STREAM

import bcon


def send(conn, obj):
    data = bcon.dumps(obj)
    conn.send(struct.pack("<I", len(data)))
    conn.send(data)

def recv(conn):
    length = struct.unpack("<I", conn.recv(4))[0]
    data = conn.recv(length)
    return bcon.loads(data)

def request(config, data):
    """
    Create connection, request, response.
    """
    conn = socket(AF_INET, SOCK_STREAM)
    conn.connect((config["ip"], config["port"]))
    send(conn, data)
    response = recv(conn)
    conn.close()
    return response
