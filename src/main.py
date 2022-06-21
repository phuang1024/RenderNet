import argparse


def main():
    parser = argparse.ArgumentParser(description="Local Blender render farm.")
    subps = parser.add_subparsers(title="subcommands", dest="subparser")
    parser.add_argument("action", help="What to do?"
        choices=["client", "worker", "server", "config"], default="client")

    clientp = subps.add_parser("client", help="Request render.")

    workerp = subps.add_parser("worker", help="Render for clients.")

    serverp = subps.add_parser("server", help="Manage all communication.")

    configp = subps.add_parser("config", help="Edit configuration.")
    configp.add_argument("entry", help="Which config entry to edit?",
        choices=["server_ip", "server_port"])
    configp.add_argument("data", help="New config data.")

    args = parser.parse_args()

    if parser.action == "client":
        pass

    if parser.action == "worker":
        pass

    if parser.action == "server":
        pass

    if parser.action == "config":
        pass


if __name__ == "__main__":
    main()
