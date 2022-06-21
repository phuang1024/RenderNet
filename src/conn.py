import json
import socket
import struct


def recv(sock):
    """
    Receive json object.
    """
    length = struct.unpack("<I", sock.recv(4))[0]
    return json.loads(sock.recv(length))


def send(sock, obj):
    """
    Send json object.
    """
    data = json.dumps(obj).encode()
    sock.send(struct.pack("<I", len(data)))
    sock.send(data)
