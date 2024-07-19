from multiprocessing import Pool
from typing import List, Tuple

import json
import os
import sys
import threading


class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self):
        super(StoppableThread, self).__init__()
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


def multiprocess_read_directory(directory: str, extension: str) -> List[Tuple[str, dict]]:
    # Reads all files with the extension in the directory, parsing them as JSON.
    # Attempts to perform a multiprocess / Pool.starmap to improve efficiency; if determined
    # that this will not be efficient, instead reads all files in the main process.

    # extension parameter should not include the "."
    extension_length = len(extension) + 1

    files = os.listdir(directory)
    names = map(lambda f: f[0:-extension_length], files)

    if attempt_multiprocess():
        pool = Pool(4)
        contents = pool.starmap(multiprocess_read_json_file, map(lambda file: (directory, file, extension), files))
        return contents

    results = []
    for name in names:
        file_name = "%s/%s.%s" % (directory, name, extension)
        with open(file_name, "r") as file:
            contents = json.load(file)
            results.append((name, contents))

    return results


def multiprocess_read_json_file(directory: str, file_name: str, extension: str) -> Tuple[str, dict]:
    # This is needed as Pool.starmap requires a function pointer.
    # This function is a simple wrapper around json.load, returning the file name (without extension) and the
    # dict contents.
    # It is used by Ontology.load() and Lexicon.load().

    lenextension = len(extension) + 1

    name = file_name[0:-lenextension]
    file_name = "%s/%s" % (directory, file_name)

    with open(file_name, "r") as file:
        contents = json.load(file)
        return name, contents


def attempt_multiprocess() -> bool:
    # Determines if multiprocessing will be an efficient task.

    # For now, the only evidence is if the PyCharm debugger is active, in which case multiprocessing is
    # extremely slow, and isn't worth using.
    return not "_pydev_bundle.pydev_log" in sys.modules.keys()