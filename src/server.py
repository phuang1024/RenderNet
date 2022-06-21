import os
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread

import config
import conn
from utils import get_tmp


class Job:
    """
    Something to render.
    """

    def __init__(self, path, frames):
        """
        :param path: Path containing this job's files e.g.
            /tmp/..server../1238349
        :param frames: Frames to render.
        """
        self.path = path
        self.frames = frames
        self.next = 0  # Next frame index to render.
        self.frames_dir = os.path.join(self.path, "frames")

        os.makedirs(self.frames_dir, exist_ok=True)

    def blend_path(self):
        return os.path.join(self.path, "blend.blend")

    def frame_path(self, frame):
        return os.path.join(self.frames_dir, f"{frame}.jpg")

    def next_job(self):
        """
        Returns next frame to render.
        """
        frame = self.frames[self.next]
        self.next += 1
        return frame

    @property
    def done(self):
        return self.next >= len(self.frames)


class Server:
    def __init__(self):
        self.jobs = []
        self.tmpdir = get_tmp()

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
            pass
