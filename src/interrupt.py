"""
Handles interrupt signals (Ctrl-C).
"""

import signal

_interrupted = False

def _signal_handler(signum, frame):
    global _interrupted
    _interrupted = True

    print(f"Interrupted by signal {signum}; stopping soon.")

def register():
    signal.signal(signal.SIGINT, _signal_handler)

def interrupted():
    return _interrupted
