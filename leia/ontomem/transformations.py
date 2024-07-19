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

    def __init__(self, name: str, contents: dict=None):
        self.name = name
        self.example: str = None
        self.synstruc: TransformationSynStruc = None
        self.executable: TransformationExecutable = None

        if contents is not None:
            self._index(contents)

    def _index(self, contents: dict):
        self.example = contents["example"]
        self.synstruc = TransformationSynStruc(contents=contents["syn-struc"])
        self.executable = import_class(contents["executable"])


class TransformationSynStruc(object):

    @dataclass
    class DependencyElement(SynStruc.Element):
        type: str
        variable: Union[int, None]
        optional: bool
        governor: Union[int, None]
        dependent: Union[int, None]

        @classmethod
        def parse(cls, data: dict) -> 'SynStruc.DependencyElement':
            return TransformationSynStruc.DependencyElement(
                data["deptype"],
                data["var"] if "var" in data else None,
                data["opt"] if "opt" in data else False,
                data["governor"] if "governor" in data else None,
                data["dependent"] if "dependent" in data else None
            )

        def to_dict(self) -> dict:
            return {"type": "dependency", "deptype": self.type, "var": self.variable, "opt": self.optional, "gov": self.governor, "dep": self.dependent}

    @dataclass
    class Variable(object):
        index: int
        pos: List[str]
        tags: List[str]

    def __init__(self, contents: dict=None):
        self.variables = List[TransformationSynStruc.Variable]
        self.patterns = List[List[Union[TransformationSynStruc.DependencyElement, SynStruc.TokenElement, SynStruc.ConstituencyElement]]]

        if contents is not None:
            self._index(contents)

    def _index(self, contents: dict):
        self.variables = list(map(lambda var: TransformationSynStruc.Variable(int(var[0]), var[1]["pos"], var[1]["tag"]), contents["vars"].items()))

        element_map = {
            "token": SynStruc.TokenElement,
            "dependency": TransformationSynStruc.DependencyElement,
            "constituency": SynStruc.ConstituencyElement
        }

        self.patterns = list(map(lambda pattern: list(map(lambda element: element_map[element["type"]].parse(element), pattern)), contents["patterns"]))

    def __eq__(self, other):
        if isinstance(other, TransformationSynStruc):
            return self.variables == other.variables and self.patterns == other.patterns


class TransformationExecutable(object):

    def run(self):
        # TODO: Determine standard inputs (e.g., variable mappings, WMLexicon, etc.)
        # TODO: Determine which of those inputs should be at the __init__ level, rather than the run() level.
        # This method is meant to be overridden by any implementation of this class; this is an abstract.
        raise NotImplementedError