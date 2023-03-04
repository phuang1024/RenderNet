from pathlib import Path

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


def run_client(config, args):
    blend_path = Path(args.blend)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"Creating job:")
    print(f"- Blend: {blend_path}")
    print(f"- Output directory: {outdir}")
    print(f"- Frames: ")
    frames = list(parse_frames(args.frames))

    print("Sending job to server.")
    response = make_request(config, {"method": "create_job", "blend": blend_path.read_bytes(), "frames": frames})
    assert response["status"] == "ok"
