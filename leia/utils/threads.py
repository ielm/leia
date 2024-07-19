from typing import Tuple

import json
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
