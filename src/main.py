import argparse

import config
import worker
from server import Server


def check_config():
    data = config.load()
    for entry in config.CONFIG_ENTRIES:
        if entry not in data:
            raise ValueError(f"Config entry {entry} not found. See renderfarm config --help")


def main():
    parser = argparse.ArgumentParser(description="Local Blender render farm.")
    subps = parser.add_subparsers(title="subcommands", dest="subparser")

    clientp = subps.add_parser("client", help="Request render.")

    workerp = subps.add_parser("worker", help="Render for clients.")

    serverp = subps.add_parser("server", help="Manage all communication.")

    configp = subps.add_parser("config", help="Edit configuration.")
    configp.add_argument("entry", help="Which config entry to edit?",
        choices=config.CONFIG_ENTRIES)
    configp.add_argument("data", help="New config data.")

    args = parser.parse_args()

    config.init()

    if args.subparser == "config":
        entry = args.entry
        data = args.data
        if entry == "server_port":
            data = int(data)

        curr = config.load()
        curr[entry] = data
        config.dump(curr)

        return

    check_config()

    if args.subparser == "client":
        pass

    if args.subparser == "worker":
        worker.start()

    if args.subparser == "server":
        server = Server()
        server.start()


if __name__ == "__main__":
    main()
