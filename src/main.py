import argparse

import client
import config
import worker
from server import Server


def main():
    parser = argparse.ArgumentParser(description="Local Blender render farm.")
    subps = parser.add_subparsers(title="subcommands", dest="subparser")

    clientp = subps.add_parser("client", help="Request render.")
    clientp.add_argument("action", help="What to do?",
        choices=["status", "download", "new"])
    clientp.add_argument("-o", "--output", help="Output directory.")
    clientp.add_argument("-j", "--job_id", help="Render job ID.", type=int)
    clientp.add_argument("-b", "--blend", help="Path to blend file.")
    clientp.add_argument("-f", "--frames", help="Frames to render.")

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
        elif entry == "worker_accept":
            data = data.split(",")

        curr = config.load()
        curr[entry] = data
        config.dump(curr)

        return

    assert config.check(args.subparser)

    if args.subparser == "client":
        client.start(args)

    if args.subparser == "worker":
        worker.start()

    if args.subparser == "server":
        server = Server()
        server.start()


if __name__ == "__main__":
    main()
