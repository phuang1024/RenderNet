import json
import time
from pathlib import Path
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread

from conn import *

TMP_DIR = Path("/tmp/RenderFarm/server")
TMP_DIR.mkdir(exist_ok=True)


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


class DataManager:
    """
    Manages current jobs in temporary directory.

    File structure:
    - DataManager root
        - 0   # (job0)
        - 1   # (job1)
            - blend.blend
            - frames.json
            - done.txt   # if present, means done.
            - lock.txt   # if present, thread is processing.
        ...
    """

    def __init__(self, root):
        self.root = root

    def create_job(self, blend: bytes, frames: list[int]):
        """
        Creates new render job.
        :param blend: Bytes data of blend file.
        :param frames: Frames to render.
        :return: Job ID (string)
        """
        job_id = self.get_unique_id()
        path = self.root / job_id

        with (path / "blend.blend").open("wb") as f:
            f.write(blend)
        with (path / "frames.json").open("w") as f:
            data = {
                "done": [],
                "pending": [],
                "todo": list(frames),
            }
            json.dump(data, f, indent=4)

        return job_id

    def get_work(self):
        """
        Randomly chooses pending job to do.
        :return: (job_id, frame)
        """
        curr_jobs = list(self.get_pending_jobs())
        job_id = random.choice(curr_jobs)
        path = self.root / job_id

        while (path / "lock.txt").exists():
            time.sleep(0.01)
        (path / "lock.txt").touch()

        with (path / "frames.json").open("r") as f:
            data = json.load(f)
        frame = random.choice(data["todo"])
        data["todo"].remove(frame)
        data["pending"].append(frame)
        with (path / "frames.json").open("w") as f:
            json.dump(data, f, indent=4)

        return (job_id, frame)

    def get_unique_id(self):
        max_num = 0
        for f in self.root.iterdir():
            name = f.name.stem
            if name.isdigit():
                max_num = max(max_num, int(name)+1)
        return str(max_num)

    def get_pending_jobs(self):
        for job in self.root.iterdir():
            if not (job / "done.txt").exists():
                with (job / "frames.json").open("r") as f:
                    frames = json.load(f)
                if len(frames["todo"]) == 0 and len(frames["pending"]) == 0:
                    (job / "done.txt").touch()
                yield job.name
