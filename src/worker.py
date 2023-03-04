import time

from conn import make_request


def attempt_render(config):
    """
    Attempt to render a job.
    :return: True if a job was rendered, False otherwise.
    """
    resp = make_request(config, {"method": "get_work"})
    if resp["status"] != "ok":
        return False

    job_id = resp["job_id"]
    frame = resp["frame"]
    print(f"Got work: job_id={job_id}, frame={frame}")


def run_worker(config):
    """
    Run the worker loop.
    If the worker is idle, it will sleep for a bit before trying again.
    """
    print("Worker starting.")
    print("Testing ping...")
    resp = make_request(config, {"method": "ping"})
    assert resp["status"] == "ok"

    delay = 0
    while True:
        did_work = attempt_render(config)
        if did_work:
            delay = 0
        else:
            delay = min(delay + 1, 10)
        time.sleep(delay)
