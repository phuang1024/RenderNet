import random
import shutil
import time
from pathlib import Path
from subprocess import run, DEVNULL

from conn import make_request

TMP_DIR = Path(f"/tmp/RenderFarmWorker{random.randint(0, 100000)}")
TMP_DIR.mkdir(exist_ok=True, parents=True)

BLENDER = shutil.which("blender")
assert BLENDER is not None, "Blender not found."


def ensure_blend(config, job_id):
    path = TMP_DIR / f"{job_id}.blend"
    if not path.exists():
        print(f"Downloading blend of job {job_id}...")

        resp = make_request(config, {"method": "download_blend", "job_id": job_id})
        if resp["status"] != "ok":
            raise Exception("Failed to download blend file.")
        with path.open("wb") as f:
            f.write(resp["data"])

    return path


def run_blender_render(file, frame):
    print(f"Rendering frame {frame}...")
    out_path = TMP_DIR / "render"
    proc = run([BLENDER, "-b", file, "-F", "JPEG", "-o", out_path, "-f", str(frame)],
        stdout=DEVNULL, stderr=DEVNULL)
    assert proc.returncode == 0, "Blender failed to render."
    out_path = TMP_DIR / f"render{frame:04d}.jpg"
    return out_path


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
    frame = resp["frame"]
    print(f"Got work: job_id={job_id}, frame={frame}")

    # Render
    blend_path = ensure_blend(config, job_id)
    out_path = run_blender_render(blend_path, frame)

    # Upload result
    print("Uploading result...")
    resp = make_request(config, {"method": "upload_render", "job_id": job_id, "frame": frame,
                                 "data": out_path.read_bytes()})

    print("Done.")
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

    delay = 0
    while True:
        did_work = attempt_render(config)
        if did_work:
            delay = 0
        else:
            delay = min(delay + 1, 10)
        time.sleep(delay)
