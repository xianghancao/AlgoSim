
import os

def make_dirs(path):
    if not os.path.exists(path):
        if os.path.exists(os.path.split(path)[0]):
            os.mkdir(path)
        else:
            make_dirs(os.path.split(path)[0])
    return

