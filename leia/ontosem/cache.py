from leia.ontosem.analysis import Analysis
from leia.ontosem.config import OntoSemConfig
from typing import List, Union
from uuid import uuid4

import importlib
import json
import os


class OntoSemCache(object):

    def __init__(self, config: OntoSemConfig):
        self.config = config
        self.index_file_name = "_index.json"

    def _path(self) -> str:
        path = self.config.cache_path
        if path is None:
            path = "%s/../.cache" % importlib.import_module("leia").__path__[0]

        if not os.path.exists(path):
            os.mkdir(path)

        return path

    def _index(self) -> dict:
        path = self._path()
        filename = "%s/%s" % (path, self.index_file_name)

        if not os.path.exists(filename):
            with open(filename, "w") as file:
                json.dump({}, file)

        with open(filename, "r") as file:
            index = json.load(file)

        return index

    def cache(self, analysis: Analysis):
        index = self._index()
        path = self._path()

        filename = "%s/%s.json" % (path, uuid4())
        if analysis.text in index:
            filename = index[analysis.text]

        index[analysis.text] = filename

        with open(filename, "w") as file:
            json.dump(analysis.to_dict(), file)

        filename = "%s/%s" % (path, self.index_file_name)
        with open(filename, "w") as file:
            json.dump(index, file)

    def load(self, text: str, logs: List[dict] = None) -> Union[Analysis, None]:
        if logs is None:
            logs = []

        index = self._index()

        if text in index:
            filename = index[text]
            with open(filename, "r") as file:
                contents = json.load(file)
                analysis = Analysis.from_dict(contents)
                analysis.config._memory = self.config.memory()

                for log in analysis.logs:
                    log["cached"] = True

                analysis.logs.extend(logs)

                return analysis

        return None
