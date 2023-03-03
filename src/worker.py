import time

from conn import request


def attempt_render(config):
    pass


def run_worker(config):
    """
    Run the worker loop.
    If the worker is idle, it will sleep for a bit before trying again.
    """
    print("Worker starting.")
    print("Testing ping...")
    resp = request(config, {"method": "ping"})
    assert resp["status"] == "ok"

    delay = 0
    while True:
        did_work = attempt_render(config)
        if did_work:
            delay = 0
        else:
            delay = min(delay + 1, 10)
        time.sleep(delay)
