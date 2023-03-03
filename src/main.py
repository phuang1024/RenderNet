import argparse
import json
import os

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
    parser.add_argument("mode", choices=["server", "client", "worker", "config"], default="client")
    args = parser.parse_args()

    if not os.path.isfile(CONFIG_PATH) or args.mode == "config":
        create_config()

    with open(CONFIG_PATH) as f:
        config = json.load(f)

    if args.mode == "server":
        server = Server(config["ip"], config["port"])
        server.start()
    elif args.mode == "worker":
        run_worker(config)


if __name__ == "__main__":
    main()
