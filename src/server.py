import pickle
import random
import tarfile
import tempfile
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
        - request: {}
        - response: {status="ok"}
    - "download_blend":
        - request: {job_id=...}
        - response: {data=...}
    - "download_render":
        - request: {job_id=..., frame=...}
        - response: {data=...}
    - "get_work":
        - request: {}
        - response: {job_id=..., frames=[...]}
    - "upload_render":
        - request: {job_id=..., frame=..., data=...}
        - response: {status="ok"}
    - "create_job":
        - request: {blend=..., frames=[...], is_tar=...,}
            - is_tar: True if uploaded a tar archive; false if a single blend file.
        - response: {job_id=...}
    - "job_status":
        - request: {job_id=...}
        - response: {frames_done=..., frames_requested=...}
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

    def stop(self):
        """
        Stops the server.
        """
        self.sock.close()

    def handle_client(self, conn, addr):
        request = recv(conn)
        if not isinstance(request, dict) or "method" not in request:
            print(f"Invalid request from {addr}")
            return
        print(f"Request from {addr}; method={request['method']}")

        if request["method"] == "ping":
            send(conn, {"status": "ok"})

        elif request["method"] == "download_blend":
            path = self.manager.root / request["job_id"] / "blend.tar.gz"
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
            job_id, frames = self.manager.get_work()
            if job_id is None:
                send(conn, {
                    "status": "no_work",
                })
            else:
                send(conn, {
                    "status": "ok",
                    "job_id": job_id,
                    "frames": frames,
                })

        elif request["method"] == "upload_render":
            self.manager.save_render(request["job_id"], request["frame"], request["data"])
            send(conn, {"status": "ok"})

        elif request["method"] == "create_job":
            job_id = self.manager.create_job(
                request["blend"],
                request["frames"],
                request["is_tar"],
            )
            send(conn, {
                "status": "ok",
                "job_id": job_id,
            })

        elif request["method"] == "job_status":
            path = self.manager.root / request["job_id"] / "frames.pkl"
            if path.exists():
                data = pickle.loads(path.read_bytes())
                all_frames = set(data["done"] + list(data["pending"].keys()) + data["todo"])
                response = {
                    "status": "ok",
                    "frames_done": data["done"],
                    "frames_requested": sorted(list(all_frames)),
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
        - 0   # job 0
        - 1   # job 1
            - blend.tar.gz    # contains user's blend, textures, etc.
                - main.blend  # blend file to render.
                ...
            - frames.pkl
            - done.txt   # if present, means done.
            - lock.txt   # if present, thread is processing.
            - renders/   # rendered images
                - 0.jpg
                ...
        ...
    """

    # Worker renders x frames per request.
    chunk_size = 16

    def __init__(self, root):
        self.root = root
        self.root.mkdir(exist_ok=True)

    def create_job(self, blend: bytes, frames: list[int], is_tar: bool):
        """
        Creates new render job.
        :param blend: Bytes data of blend file.
        :param frames: Frames to render.
        :return: Job ID (string)
        """
        job_id = self.get_unique_id()
        path = self.root / job_id
        path.mkdir()

        # Save blend file
        if is_tar:
            (path / "blend.tar.gz").write_bytes(blend)
        else:
            with tempfile.NamedTemporaryFile("wb") as f, tarfile.open(path / "blend.tar.gz", "w:gz") as tar:
                f.write(blend)
                f.flush()
                tar.add(f.name, arcname="main.blend")

        # Write frame data.
        data = {
            "done": [],
            "pending": {},   # {frame: time_start, ...}
            "todo": sorted(list(frames)),
        }
        (path / "frames.pkl").write_bytes(pickle.dumps(data))

        # Output renders directory.
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

        # Update frames
        data = pickle.loads((path / "frames.pkl").read_bytes())
        frames = data["todo"][:self.chunk_size]
        for frame in frames:
            data["todo"].remove(frame)
            data["pending"][str(frame)] = time.time()
        (path / "frames.pkl").write_bytes(pickle.dumps(data))

        (path / "lock.txt").unlink()
        return (job_id, frames)

    def save_render(self, job_id, frame, img_data):
        path = self.root / job_id

        # Update frames
        data = pickle.loads((path / "frames.pkl").read_bytes())
        data["pending"].pop(str(frame))
        data["done"].append(frame)
        (path / "frames.pkl").write_bytes(pickle.dumps(data))

        # Save image
        (path / "renders" / f"{frame}.jpg").write_bytes(img_data)

    def get_unique_id(self):
        max_num = 0
        for f in self.root.iterdir():
            name = f.stem
            if name.isdigit():
                max_num = max(max_num, int(name)+1)
        return str(max_num)

    def get_pending_jobs(self):
        """
        Job IDs that have frames available to give to workers.
        """
        for jobdir in self.root.iterdir():
            done_txt = (jobdir / "done.txt")
            if not done_txt.exists():
                frames = pickle.loads((jobdir / "frames.pkl").read_bytes())
                if len(frames["todo"]) > 0:
                    yield jobdir.name
                else:
                    # Mark as done, won't check next time.
                    (jobdir / "done.txt").touch()
