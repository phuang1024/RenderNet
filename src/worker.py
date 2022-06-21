import os
import random
import time

import config
import conn

_rand = random.randint(0, 1e9)
TMPDIR = os.path.join("/tmp", f"renderfarm_worker_{_rand}")
os.makedirs(TMPDIR, exist_ok=True)


def start():
    try:
        while True:
            print("Requesting work.")
            resp = conn.request({
                "type": "worker",
                "action": "request_work",
                "accept": config.get("worker_accept"),
            })
            print(len(resp))

            break

    except KeyboardInterrupt:
        print("Stopping worker.")
