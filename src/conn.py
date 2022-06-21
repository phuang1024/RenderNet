import json
import socket
import struct
from socket import socket, AF_INET, SOCK_STREAM
from tqdm import trange

import config


def chunk_send(sock, data, pbar=False):
    sock.send(data)
    return

def chunk_recv(sock, length):
    data = b""
    iters = 0
    while len(data) < length:
        data += sock.recv(length)
        iters += 1
        if iters >= 1e7:
            raise ValueError("Could not receive data (maybe broken pipe).")

    return data


def recv(sock):
    """
    Receive json object.
    """
    length = struct.unpack("<I", sock.recv(4))[0]
    return json.loads(chunk_recv(sock, length))

def send(sock, obj, pbar=False):
    """
    Send json object.
    """
    data = json.dumps(obj).encode()
    sock.send(struct.pack("<I", len(data)))
    chunk_send(sock, data, pbar)


def request(data):
    """
    Called by non-servers.
    Sends object to server, receives object and returns.
    """
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect((config.get("server_ip"), config.get("server_port")))
    send(sock, data)
    return recv(sock)
