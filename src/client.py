import os
from base64 import b64decode, b64encode

import conn


def start(args):
    if args.action == "status":
        required = ("job_id",)
    elif args.action == "download":
        required = ("job_id", "output", "frames")
    elif args.action == "new":
        required = ("blend", "frames")
    for key in required:
        if getattr(args, key) is None:
            print(f"Argument --{key} required.")
            return

    if args.action == "status":
        pass

    elif args.action == "download":
        pass

    elif args.action == "new":
        pass
