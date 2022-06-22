import os
import random


def get_tmp(name):
    """
    Returns /tmp/renderfarm_{name}_{rand}
    """
    rand = random.randint(0, 1e9)
    tmpdir = f"/tmp/renderfarm_{name}_{rand}"
    os.makedirs(tmpdir, exist_ok=True)
    return tmpdir
