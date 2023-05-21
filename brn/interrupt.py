"""
Handles interrupt signals (Ctrl-C).
"""

import sys
import signal

_interrupted = False
_server = None
_num_interrupts = 0

def _signal_handler(signum, frame):
    global _interrupted, _num_interrupts
    _interrupted = True
    _num_interrupts += 1

    print(f"Interrupted by signal {signum}; stopping soon.")

    if _server is not None:
        _server.stop()

    if _num_interrupts >= 2:
        print("Interrupted twice; exiting immediately.")
        sys.exit(1)

def register(server=None):
    global _server
    _server = server

    signal.signal(signal.SIGINT, _signal_handler)

def interrupted():
    return _interrupted
