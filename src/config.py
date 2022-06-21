import json
import os

CONFIG_DIR = os.path.expanduser("~/.config/renderfarm")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

CONFIG_ENTRIES = (
    "server_ip",
    "server_port",
    "worker_accept",
)


def init():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if not os.path.isfile(CONFIG_FILE):
        dump({})


def _check_real(entries):
    data = load()
    for entry in entries:
        if entry not in data:
            return False
    return True


def check(mode):
    """
    Make sure all config is present.

    :param mode: "server", "client", etc.
    """
    if mode == "worker":
        return _check_real(CONFIG_ENTRIES)
    else:
        return _check_real(("server_ip", "server_port"))


def dump(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def get(key):
    return load()[key]
