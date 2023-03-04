import random
import shutil
import time
from pathlib import Path
from subprocess import run, DEVNULL

from conn import make_request

TMP_DIR = Path(f"/tmp/RenderFarmWorker{random.randint(0, 100000)}")
(TMP_DIR / "blends").mkdir(exist_ok=True, parents=True)
(TMP_DIR / "renders").mkdir(exist_ok=True, parents=True)

BLENDER = shutil.which("blender")
assert BLENDER is not None, "Blender not found."


def ensure_blend(config, job_id):
    path = TMP_DIR / "blends" / f"{job_id}.blend"
    if not path.exists():
        print(f"  Downloading blend of job {job_id}...")

        resp = make_request(config, {"method": "download_blend", "job_id": job_id})
        if resp["status"] != "ok":
            raise Exception("Failed to download blend file.")
        with path.open("wb") as f:
            f.write(resp["data"])

    return path


def run_blender_render(file, frames):
    print(f"  Running blender on {len(frames)} frames...")
    out_path = TMP_DIR / "renders" / "img"

    proc = run([BLENDER, "-b", file, "-F", "JPEG", "-o", out_path, "-f", ",".join(map(str, frames))],
        stdout=DEVNULL, stderr=DEVNULL)
    assert proc.returncode == 0, "Blender failed to render."


def attempt_render(config) -> bool:
    """
    Attempt to render a job.
    :return: True if a job was rendered, False otherwise.
    """
    # Request work
    resp = make_request(config, {"method": "get_work"})
    if resp["status"] != "ok":
        #print("No work.")
        return False
    job_id = resp["job_id"]
    frames = resp["frames"]
    print(f"Got work: job_id={job_id}, {len(frames)} frames.")

    # Render
    blend_path = ensure_blend(config, job_id)
    run_blender_render(blend_path, frames)

    # Upload result
    print("  Uploading results...")
    for frame in frames:
        curr_path = TMP_DIR / "renders" / f"img{frame:04d}.jpg"
        resp = make_request(config, {"method": "upload_render", "job_id": job_id, "frame": frame,
                "data": curr_path.read_bytes()})

    print("  Done.")
    return True


def run_worker(config):
    """
    Run the worker loop.
    If the worker is idle, it will sleep for a bit before trying again.
    """
    print("Worker starting.")
    print(f"Temporary directory: {TMP_DIR}")
    print("Testing ping...")
    resp = make_request(config, {"method": "ping"})
    assert resp["status"] == "ok"
    print("Waiting for work")

    delay = 0
    while True:
        did_work = attempt_render(config)
        if did_work:
            delay = 0
        else:
            delay = min(delay + 1, 10)
        time.sleep(delay)
