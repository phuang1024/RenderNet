import pickle
import random
import tarfile
import tempfile
import time
from pathlib import Path


class FileLock:
    """
    If file is present, means something is locked.
    Wait until file is deleted, then re-create it and continue.
    """

    def __init__(self, path):
        self.path = Path(path)

    def __enter__(self):
        while self.path.exists():
            time.sleep(0.01)
        self.path.touch()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.path.unlink()


class DataManager:
    """
    Manages current jobs in temporary directory.
    Used by server.

    File structure:
    - DataManager root
        - 0   # job 0
        - 1   # job 1
            - blend.tar.gz    # contains user's blend, textures, etc.
                - main.blend  # blend file to render.
                ...
            - status.pkl  # dictionary containing:
                - "done": List of frames done.
                - "pending": Map of frames being processed to time started.
                - "todo": List of frames not started.
                - "batch_size": Map of worker ID to batch_size. With each batch, this is changed
                    to make work time closer to `tgt_batch_time`.
            - done.txt   # if present, means no more "todo" frames.
            - lock.txt   # if present, some thread is processing.
            - renders/   # rendered images
                - 0.jpg
                ...
        ...
    """

    # Ideal max time a worker works for per batch (sec).
    # Smaller = less waiting on slower workers at the end.
    # Larger = less relative overhead.
    tgt_batch_time = 40
    max_batch_size = 100

    def __init__(self, root):
        self.root = root
        self.root.mkdir(exist_ok=True)

    def lock(self, job_id):
        """
        Return FileLock object for job_id.
        """
        return FileLock(self.root / job_id / "lock.txt")

    def create_job(self, blend: bytes, frames: list[int], is_tar: bool):
        """
        Creates new render job.
        :param blend: Bytes data of blend file.
        :param frames: Frames to render.
        :return: Job ID (string)
        """
        job_id = self.get_unique_id()
        job_path = self.root / job_id
        job_path.mkdir()

        # Save blend file
        if is_tar:
            (job_path / "blend.tar.gz").write_bytes(blend)
        else:
            with tempfile.NamedTemporaryFile("wb") as f, tarfile.open(job_path / "blend.tar.gz", "w:gz") as tar:
                f.write(blend)
                f.flush()
                tar.add(f.name, arcname="main.blend")

        # Write frame data.
        data = {
            "done": [],
            "pending": {},   # {frame: time_start, ...}
            "todo": sorted(list(frames)),
            "batch_size": {},
        }
        (job_path / "status.pkl").write_bytes(pickle.dumps(data))

        # Output renders directory.
        (job_path / "renders").mkdir()

        return job_id

    def get_work(self, worker_id):
        """
        Randomly chooses pending job to do.
        :return: (job_id, frame)
        """
        curr_jobs = list(self.get_pending_jobs())
        if not curr_jobs:
            return None, None

        job_id = random.choice(curr_jobs)
        job_path = self.root / job_id

        with self.lock(job_id):
            status = pickle.loads((job_path / "status.pkl").read_bytes())

            if worker_id not in status["batch_size"]:
                # Initialize worker batch_size
                status["batch_size"][worker_id] = 1

            # Update frames
            frames = status["todo"][:int(status["batch_size"][worker_id])]
            for frame in frames:
                status["todo"].remove(frame)
                status["pending"][frame] = time.time()

            (job_path / "status.pkl").write_bytes(pickle.dumps(status))

        return (job_id, frames)

    def save_render(self, worker_id, job_id, frame, img_data):
        job_path = self.root / job_id

        with self.lock(job_id):
            status = pickle.loads((job_path / "status.pkl").read_bytes())

            avg_time = (time.time() - status["pending"][frame]) / status["batch_size"][worker_id]
            nominal_bs = self.tgt_batch_time / avg_time
            diff = nominal_bs - status["batch_size"][worker_id]
            new_bs = status["batch_size"][worker_id] + diff*0.5
            new_bs = max(1, min(self.max_batch_size, new_bs))
            status["batch_size"][worker_id] = new_bs

            # Update frames
            status["pending"].pop(frame)
            status["done"].append(frame)

            # Save image
            (job_path / "renders" / f"{frame}.jpg").write_bytes(img_data)

            (job_path / "status.pkl").write_bytes(pickle.dumps(status))

    def get_unique_id(self):
        max_num = 0
        for f in self.root.iterdir():
            name = f.stem
            if name.isdigit():
                max_num = max(max_num, int(name)+1)
        return str(max_num)

    def get_pending_jobs(self):
        """
        Job IDs that have frames available to give to workers.
        """
        for jobdir in self.root.iterdir():
            done_txt = (jobdir / "done.txt")
            if not done_txt.exists():
                frames = pickle.loads((jobdir / "status.pkl").read_bytes())
                if len(frames["todo"]) > 0:
                    yield jobdir.name
                else:
                    # Mark as done, won't check next time.
                    (jobdir / "done.txt").touch()
