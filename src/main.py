import argparse
import json
import os

import interrupt
from client import create_job, download_results
from server import Server
from worker import run_worker

ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(ROOT, "config.json")


def create_config():
    print("Creating config file.")
    data = {
        "ip": input("Server IP: "),
        "port": int(input("Server port: ")),
    }
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=4)


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="mode", required=True)
    subparsers.add_parser("server")
    subparsers.add_parser("worker")
    subparsers.add_parser("config")
    create_parser = subparsers.add_parser("create")
    create_parser.add_argument("blend", type=str)
    create_parser.add_argument("frames", type=str, help="Python slice format i.e. a:b:c,d:e, etc.")
    download_parser = subparsers.add_parser("download")
    download_parser.add_argument("job_id", type=str)
    download_parser.add_argument("outdir", type=str)
    args = parser.parse_args()

    if not os.path.isfile(CONFIG_PATH) or args.mode == "config":
        create_config()

    with open(CONFIG_PATH) as f:
        config = json.load(f)

    if args.mode == "server":
        server = Server(config["ip"], config["port"])
        interrupt.register(server)
        server.start()
    else:
        interrupt.register()
        if args.mode == "worker":
            run_worker(config)
        elif args.mode == "create":
            create_job(config, args)
        elif args.mode == "download":
            download_results(config, args)


if __name__ == "__main__":
    main()
