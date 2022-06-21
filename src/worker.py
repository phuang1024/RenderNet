import os
import random
import time

import config
import conn
from utils import get_tmp


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

    except KeyboardInterrupt:
        print("Stopping worker.")
