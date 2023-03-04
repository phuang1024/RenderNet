"""
Handles interrupt signals (Ctrl-C).
"""

import signal

_interrupted = False
_server = None

def _signal_handler(signum, frame):
    global _interrupted
    _interrupted = True

    print(f"Interrupted by signal {signum}; stopping soon.")

    if _server is not None:
        _server.stop()

def register(server=None):
    global _server
    _server = server

    signal.signal(signal.SIGINT, _signal_handler)

def interrupted():
    return _interrupted
