import random
import shutil
import tarfile
import tempfile
import time
from pathlib import Path
from subprocess import run, DEVNULL

from .conn import make_request
from .interrupt import interrupted

TMP_DIR = Path(f"/tmp/RenderFarmWorker{random.randint(0, 100000)}")
(TMP_DIR / "blends").mkdir(exist_ok=True, parents=True)
(TMP_DIR / "renders").mkdir(exist_ok=True, parents=True)

BLENDER = shutil.which("blender")
assert BLENDER is not None, "Blender not found."


def ensure_blend(config, job_id):
    path = TMP_DIR / "blends" / f"{job_id}"
    if not path.exists():
        print(f"  Downloading blend.tar.gz of job {job_id}...")

        resp = make_request(config, {"method": "download_blend", "job_id": job_id})
        if resp["status"] != "ok":
            raise Exception("Failed to download blend file.")

        with tempfile.NamedTemporaryFile("wb") as tar:
            tar.write(resp["data"])
            with tarfile.open(tar.name) as tar:
                tar.extractall(path)

    return path / "main.blend"


def run_blender_render(file, frames):
    print(f"  Running blender on {len(frames)} frames...")
    out_path = TMP_DIR / "renders" / "img"

    proc = run(
        [BLENDER, "-b", file, "-F", "JPEG", "-o", out_path, "-f", ",".join(map(str, frames))],
        stdout=DEVNULL,
        stderr=DEVNULL,
        cwd=file.parent,
    )
    assert proc.returncode == 0, "Blender failed to render."


def attempt_render(config, worker_id) -> bool:
    """
    Attempt to render a job.
    :return: True if a job was rendered, False otherwise.
    """
    time_start = time.time()

    # Request work
    resp = make_request(config, {"method": "get_work", "worker_id": worker_id})
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
                "data": curr_path.read_bytes(), "worker_id": worker_id})

    time_elapse = time.time() - time_start
    sec_per_frame = time_elapse / len(frames)
    print(f"  Rendered {len(frames)} frames in {time_elapse:.2f} seconds ({sec_per_frame:.2f} sec/frame).")

    print("  Done.")
    return True


def run_worker(config):
    """
    Run the worker loop.
    If the worker is idle, it will sleep for a bit before trying again.
    """
    print("Worker starting.")
    print(f"Temporary directory: {TMP_DIR}")
    print("Initializing worker...")
    resp = make_request(config, {"method": "worker_init"})
    worker_id = resp["worker_id"]
    print(f"Worker ID is {worker_id}")
    print("Waiting for work")

    delay = 0
    while not interrupted():
        did_work = attempt_render(config, worker_id)
        if did_work:
            delay = 0
        else:
            delay = min(delay + 1, 10)
        time.sleep(delay)
