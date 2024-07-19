from dataclasses import dataclass
from leia.ontomem.lexicon import SynStruc
from leia.ontomem.memory import Memory
from leia.utils.str2py import import_class
from leia.utils.threads import multiprocess_read_json_file
from multiprocessing.pool import Pool
from typing import List, Union

import os


class TransformationsCatalogue(object):

    def __init__(self, memory: Memory, contents_dir: str, load_now: bool=True):
        self.memory = memory
        self.contents_dir = contents_dir
        self.cache = {}

        if load_now:
            self.load()

    def load(self):
        pool = Pool(4)
        files = os.listdir(self.contents_dir)

        contents = pool.starmap(multiprocess_read_json_file, map(lambda file: (self.contents_dir, file, "trans"), files))
        for c in contents:
            self.cache[c[0]] = Transformation(c[0], contents=c[1])

    def add_transformation(self, transformation: 'Transformation'):
        self.cache[transformation.name] = transformation

    def remove_transformation(self, transformation: Union['Transformation', str]):
        if isinstance(transformation, Transformation):
            transformation = transformation.name
        if transformation in self.cache:
            del self.cache[transformation]

    def transformations(self) -> List['Transformation']:
        return list(self.cache.values())

    def transformation(self, name: str) -> Union['Transformation', None]:
        if name in self.cache:
            return self.cache[name]
        return None


class Transformation(object):

    @dataclass
    class Variable(object):
        index: int
        pos: List[str]
        tags: List[str]

    def __init__(self, name: str, contents: dict=None):
        self.name = name
        self.example: str = None
        self.variables: List[Transformation.Variable] = []
        self.synstrucs: List[SynStruc] = []
        self.executable: TransformationExecutable = None

        if contents is not None:
            self._index(contents)

    def _index(self, contents: dict):
        self.example = contents["example"]
        self.variables = list(map(lambda var: Transformation.Variable(int(var[0]), var[1]["pos"], var[1]["tag"]), contents["pattern"]["vars"].items()))
        self.synstrucs = list(map(lambda syn: SynStruc(contents=syn), contents["pattern"]["syn-strucs"]))
        self.executable = import_class(contents["executable"])


class TransformationExecutable(object):

    def run(self):
        # TODO: Determine standard inputs (e.g., variable mappings, WMLexicon, etc.)
        # TODO: Determine which of those inputs should be at the __init__ level, rather than the run() level.
        # This method is meant to be overridden by any implementation of this class; this is an abstract.
        raise NotImplementedError