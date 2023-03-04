import time
from pathlib import Path
from tqdm import tqdm

from conn import make_request


def parse_frames(frames: str):
    for section in frames.split(","):
        parts = list(map(int, section.split(":")))
        if len(parts) == 1:
            print(f"  - Frame {parts[0]}")
            yield parts[0]
        elif len(parts) == 2:
            print(f"  - Frames {parts[0]} to {parts[1]}")
            yield from range(parts[0], parts[1])
        elif len(parts) == 3:
            print(f"  - Frames {parts[0]} to {parts[1]} by {parts[2]}")
            yield from range(parts[0], parts[1], parts[2])


def create_job(config, args):
    blend_path = Path(args.blend)

    print(f"Creating job:")
    print(f"- Blend: {blend_path}")
    print(f"- Frames: ")
    frames = list(parse_frames(args.frames))

    print("Sending job to server.")
    response = make_request(config, {"method": "create_job", "blend": blend_path.read_bytes(), "frames": frames})
    assert response["status"] == "ok"
    job_id = response["job_id"]
    print(f"Job created: job_id={job_id}")
    print(f"Run `python main.py download {job_id} /path/to/output` to download the results.")


def download_results(config, args):
    job_id = args.job_id
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading results:")
    print(f"- Job ID: {args.job_id}")
    print(f"- Output directory: {outdir}")

    response = make_request(config, {"method": "job_status", "job_id": job_id})
    all_frames = response["frames_requested"]

    # Check which frames we already have
    pbar = tqdm(total=len(all_frames), desc="Waiting...")
    frames_done = set()
    for file in outdir.iterdir():
        if file.suffix == ".jpg":
            frames_done.add(int(file.stem))
            pbar.update(1)

    delay = 0
    while True:
        time.sleep(delay)
        response = make_request(config, {"method": "job_status", "job_id": job_id})
        if response["status"] != "ok":
            continue

        # Check if we got any new frames
        did_something = False
        for frame in response["frames_done"]:
            if frame not in frames_done:
                did_something = True

                # Download the frame
                response = make_request(config, {"method": "download_render", "job_id": job_id, "frame": frame})
                if response["status"] == "ok":
                    (outdir / f"{frame}.jpg").write_bytes(response["data"])
                else:
                    print(f"Failed to download frame {frame}")
                    continue

                frames_done.add(frame)
                pbar.set_description(f"Got frame {frame}")
                pbar.update(1)

        if len(frames_done) == len(all_frames):
            break

        if did_something:
            delay = 0
        else:
            delay = min(delay + 1, 10)

    pbar.close()
    print("Done.")
