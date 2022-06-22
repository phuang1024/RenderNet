import os
import random
import time
from base64 import b64encode
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


class JobsLock:
    """
    Context manager that locks Server._jobs
    """

    def __init__(self, server):
        self.server = server

    def __enter__(self):
        while self.server._jobs_lock:
            time.sleep(0.001)
        self.server._jobs_lock = True
        return self.server._jobs

    def __exit__(self, *args):
        self.server._jobs_lock = False


class Server:
    def __init__(self):
        self._jobs = {}
        self._jobs_lock = False
        self.tmpdir = get_tmp("server")

        self.server = socket(AF_INET, SOCK_STREAM)
        self.server.bind((config.get("server_ip"), config.get("server_port")))

    def start(self):
        print("Starting server.")

        Thread(target=self.clean).start()

        self.server.listen()

        while True:
            sock, addr = self.server.accept()
            Thread(target=self.handle, args=(sock, addr)).start()

    def clean(self):
        """
        Background thread that cleans up.
        """
        # TODO for testing
        p = os.path.join(self.tmpdir, "123")
        os.makedirs(p, exist_ok=True)
        os.system(f"cp /tmp/default.blend {p}/blend.blend")
        self._jobs[123] = Job(p, list(range(100)))

        while True:
            time.sleep(1)

            with JobsLock(self) as jobs:
                # Clean done jobs.
                to_remove = []
                for key, job in jobs.items():
                    if job.done:
                        to_remove.append(key)
                for key in to_remove:
                    jobs.pop(key)

    def handle(self, sock, addr):
        print("Connection:", addr)

        data = conn.recv(sock)
        if "type" in data and "action" in data:
            if data["type"] == "worker":
                self.handle_worker(sock, data)
        else:
            conn.send(sock, "invalid")

    def handle_worker(self, sock, data):
        with JobsLock(self) as jobs:
            if data["action"] == "request_work":
                keys = list(jobs.keys())
                random.shuffle(keys)
    
                found = False
                for k in keys:
                    if not jobs[k].done:
                        found = True
                        break
    
                if found:
                    frame = jobs[k].next_job()
                    conn.send(sock, {"found": True, "id": k, "frame": frame})
                else:
                    conn.send(sock, {"found": False})

            elif data["action"] == "download":
                job_id = data["id"]
                if job_id in jobs:
                    with open(jobs[job_id].blend_path(), "rb") as f:
                        conn.send(sock, b64encode(f.read()).decode())
                else:
                    conn.send(sock, b"")
