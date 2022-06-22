import os
import random
import shutil
import sys
import time
from base64 import b64decode, b64encode
from subprocess import Popen, DEVNULL, PIPE, STDOUT

import config
import conn
from utils import get_tmp

BLENDER = shutil.which("blender")
assert BLENDER is not None


def ensure_blend(tmpdir, job_id):
    path = os.path.join(tmpdir, f"{job_id}.blend")
    if not os.path.isfile(path):
        with open(path, "wb") as f:
            resp = conn.request({
                "type": "worker",
                "action": "download",
                "id": job_id,
            })
            f.write(b64decode(resp))


    return path


def render(tmpdir, blend, frame):
    args = [BLENDER, "--background", blend, "--render-output", os.path.join(tmpdir, "frame"),
        "--render-frame", str(frame)]
    p = Popen(args, stdin=DEVNULL, stdout=PIPE, stderr=STDOUT)
    p.wait()

    if p.returncode != 0:
        print("Blender render failed. Blender output:")
        sys.stdout.buffer.write(p.stdout.read())

    return os.path.join(tmpdir, f"frame{frame:04}.jpg")


def start():
    tmpdir = get_tmp("worker")
    try:
        while True:
            print("Requesting work.")
            resp = conn.request({
                "type": "worker",
                "action": "request_work",
                "accept": config.get("worker_accept"),
            })

            if resp["found"]:
                job_id = resp["id"]
                frame = resp["frame"]

                blend = ensure_blend(tmpdir, job_id)
                print(f"Rendering: job={job_id}, frame={frame};   ", end="", flush=True)
                output = render(tmpdir, blend, frame)
                print("Uploading;   ", end="", flush=True)
                with open(output, "rb") as f:
                    conn.request({
                        "type": "worker",
                        "action": "upload",
                        "id": job_id,
                        "frame": frame,
                        "data": b64encode(f.read()).decode(),
                    })
                print("Done")

            else:
                time.sleep(5)

    except KeyboardInterrupt:
        print("Stopping worker.")
