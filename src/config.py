import json
import os

CONFIG_DIR = os.path.expanduser("~/.config/renderfarm")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

CONFIG_ENTRIES = (
    "server_ip",
    "server_port",
)


def init():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if not os.path.isfile(CONFIG_FILE):
        dump({})


def dump(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)
