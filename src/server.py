import pickle
import random
from pathlib import Path
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread

from conn import *
from datamgr import DataManager

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
            path = self.manager.root / request["job_id"] / "status.pkl"
            if path.exists():
                data = pickle.loads(path.read_bytes())
                all_frames = sorted(set(data["done"] + list(data["pending"].keys()) + data["todo"]))
                response = {
                    "status": "ok",
                    "frames_done": data["done"],
                    "frames_requested": all_frames,
                }
            else:
                response = {
                    "status": "not_found"
                }
            send(conn, response)

        else:
            print(f"Invalid method from {addr}")
            send(conn, {"status": "invalid_request"})
