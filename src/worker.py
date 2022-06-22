import os
import random
import time
from base64 import b64decode

import config
import conn
from utils import get_tmp


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
                blend = ensure_blend(tmpdir, resp["id"])
                print(blend)
                break  # TODO remove
            else:
                time.sleep(5)

    except KeyboardInterrupt:
        print("Stopping worker.")
