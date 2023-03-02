import struct

import bcon


def send(conn, obj):
    data = bcon.dumps(obj)
    conn.send(struct.pack("<I", len(data)))
    conn.send(data)

def recv(conn):
    length = struct.unpack("<I", conn.recv(4))[0]
    data = conn.recv(length)
    return bcon.loads(data)
