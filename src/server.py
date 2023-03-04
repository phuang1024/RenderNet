import json
import random
import time
from pathlib import Path
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread

from conn import *

TMP_DIR = Path(f"/tmp/RenderFarmServer{random.randint(0, 100000)}")
TMP_DIR.mkdir(exist_ok=True, parents=True)


class Server:
    """
    All responses contain "status=..."
    If status == "ok", good request.
    Else, bad.

    Request methods:
    - "ping":
        - request: ()
        - response: (status="ok")
    - "download_blend":
        - request: (job_id=...)
        - response: (data=...)
    - "download_render":
        - request: (job_id=..., frame=...)
        - response: (data=...)
    - "get_work":
        - request: ()
        - response: (job_id=..., frame=...)
    - "upload_render":
        - request: (job_id=..., frame=..., data=...)
        - response: (status="ok")
    - "create_job":
        - request: (blend=..., frames=...(list))
        - response: (job_id=...)
    - "job_status":
        - request: (job_id=...)
        - response: (frames_done=...)
    """

    def __init__(self, ip, port):
        self.manager = DataManager(TMP_DIR / "jobs")

        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.bind((ip, port))

        print(f"Temporary directory: {TMP_DIR}")
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

        if request["method"] == "ping":
            send(conn, {"status": "ok"})

        elif request["method"] == "download_blend":
            path = self.manager.root / request["job_id"] / "blend.blend"
            if path.exists():
                response = {
                    "status": "ok",
                    "data": path.read_bytes(),
                }
            else:
                response = {
                    "status": "not_found"
                }
            send(conn, response)

        elif request["method"] == "download_render":
            path = self.manager.root / request["job_id"] / "renders" / f"{request['frame']}.jpg"
            if path.exists():
                response = {
                    "status": "ok",
                    "data": path.read_bytes(),
                }
            else:
                response = {
                    "status": "not_found"
                }
            send(conn, response)

        elif request["method"] == "get_work":
            job_id, frame = self.manager.get_work()
            if job_id is None:
                send(conn, {
                    "status": "no_work",
                })
            else:
                send(conn, {
                    "status": "ok",
                    "job_id": job_id,
                    "frame": frame,
                })

        elif request["method"] == "upload_render":
            self.manager.save_render(request["job_id"], request["frame"], request["data"])
            send(conn, {"status": "ok"})

        elif request["method"] == "create_job":
            job_id = self.manager.create_job(
                request["blend"],
                request["frames"],
            )
            send(conn, {
                "status": "ok",
                "job_id": job_id,
            })

        elif request["method"] == "job_status":
            path = self.manager.root / request["job_id"] / "frames.json"
            if path.exists():
                data = json.loads(path.read_text())
                response = {
                    "status": "ok",
                    "frames_done": data["done"],
                }
            else:
                response = {
                    "status": "not_found"
                }
            send(conn, response)

        else:
            print(f"Invalid method from {addr}")
            send(conn, {"status": "invalid_request"})


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
            - renders/   # rendered images
                - 0.jpg
                ...
        ...
    """

    def __init__(self, root):
        self.root = root
        self.root.mkdir(exist_ok=True)

    def create_job(self, blend: bytes, frames: list[int]):
        """
        Creates new render job.
        :param blend: Bytes data of blend file.
        :param frames: Frames to render.
        :return: Job ID (string)
        """
        job_id = self.get_unique_id()
        path = self.root / job_id
        path.mkdir()

        with (path / "blend.blend").open("wb") as f:
            f.write(blend)
        with (path / "frames.json").open("w") as f:
            data = {
                "done": [],
                "pending": [],
                "todo": sorted(list(frames)),
            }
            json.dump(data, f, indent=4)

        (path / "renders").mkdir()

        return job_id

    def get_work(self):
        """
        Randomly chooses pending job to do.
        :return: (job_id, frame)
        """
        curr_jobs = list(self.get_pending_jobs())
        if not curr_jobs:
            return None, None

        job_id = random.choice(curr_jobs)
        path = self.root / job_id

        # Wait for lock
        while (path / "lock.txt").exists():
            time.sleep(0.01)
        (path / "lock.txt").touch()

        # Update frames.json
        data = json.loads((path / "frames.json").read_text())
        frame = data["todo"][0]
        data["todo"].remove(frame)
        data["pending"].append(frame)
        (path / "frames.json").write_text(json.dumps(data, indent=4))

        (path / "lock.txt").unlink()
        return (job_id, frame)

    def save_render(self, job_id, frame, img_data):
        path = self.root / job_id

        # Update frames.json
        data = json.loads((path / "frames.json").read_text())
        data["pending"].remove(frame)
        data["done"].append(frame)
        (path / "frames.json").write_text(json.dumps(data, indent=4))

        # Save image
        (path / "renders" / f"{frame}.jpg").write_bytes(img_data)

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
                else:
                    yield job.name
